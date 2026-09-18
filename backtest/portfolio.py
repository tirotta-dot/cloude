"""Simulatore di portafoglio a capitale condiviso per la strategia APEX.

Differenza fondamentale rispetto a run.py: qui c'e' UN SOLO conto che opera
le 5 cripto contemporaneamente, come farebbe un trader reale:
  - sizing a rischio per trade sull'equity corrente del conto
  - cap di esposizione totale (niente leva: max 100% investito)
  - numero massimo di posizioni aperte
  - quando il capitale non basta per tutti i segnali, priorita' alle
    cripto con momentum piu' forte (ROC 90 giorni)

Esecuzione: segnali sulla chiusura, ordini all'apertura successiva,
stop intrabar con trailing aggiornato solo a fine barra (no lookahead).
"""

import os
import sys
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from engine import atr, compute_metrics, ema, load_csv, Trade  # noqa: E402

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
SYMBOLS = ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD", "XRPUSD"]


@dataclass
class ApexParams:
    ch_len: int = 30          # canale breakout (giorni)
    exit_len: int = 20        # EMA di uscita
    trail_mult: float = 4.0   # trailing stop in multipli di ATR(14)
    sl_pct: float = 12.0      # stop fisso di emergenza
    risk_pct: float = 10.0    # rischio per trade in % equity
    max_frac: float = 1.0     # frazione massima di equity per singola posizione
    max_pos: int = 5          # posizioni aperte massime
    use_btc_filter: bool = False   # le alt entrano solo se BTC > EMA200
    use_alignment: bool = False    # richiede anche EMA50 > EMA200
    fee_pct: float = 0.10
    slippage_pct: float = 0.05
    top_k: int | None = None       # entra solo nelle prime k coin per momentum 90g
    leverage: float = 1.0          # esposizione massima in multipli di equity
    borrow_apr: float = 12.0       # funding annuo sul notional aperto (perpetual)
    # ── feature sperimentali (testate in improvements.py) ──
    smart_exit: bool = False       # uscita EMA20 solo se il trade e' in perdita
    chandelier: bool = False       # trailing dal massimo close dall'ingresso
    require_mom_pos: bool = False  # entra solo con momentum 90g positivo
    breadth_scaling: bool = False  # rischio scalato sull'ampiezza del regime
    eq_curve_filter: bool = False  # rischio dimezzato se equity < EMA50(equity)
    pyramid: bool = False          # un add-on a meta' size su nuovo breakout
    vol_cap_pctile: float | None = None  # blocca ingressi se ATR% oltre il percentile
    # ── meta-strategia (APEX-S) ──
    mode_switch: bool = False      # commuta aggressivo/difensivo su ampiezza regime
    breadth_hi: float = 0.5        # soglia di ampiezza per la modalita' aggressiva
    def_risk: float = 8.0          # parametri della modalita' difensiva
    def_frac: float = 0.30
    def_topk: int = 3
    def_lev: float = 1.0
    vol_target: float | None = None  # vol annua target del portafoglio (es. 0.50)
    vol_floor: float = 0.3           # leva minima del vol-targeting (1.0 = taglia solo la leva)
    dd_brake: float | None = None    # stop ai nuovi ingressi se DD portafoglio oltre soglia (es. 0.20)
    cooldown: int = 0                # giorni di attesa prima di rientrare su una coin stoppata in perdita
    lock_trigger: float | None = None  # profitto (es. 0.5 = +50%) oltre cui il trailing si stringe
    lock_mult: float = 3.0             # multiplo ATR del trailing "stretto" post-trigger
    trade_only: tuple | None = None  # se impostato, opera solo questi simboli


def build_signals(df: pd.DataFrame, p: ApexParams, btc_regime: pd.Series | None,
                  is_btc: bool) -> dict:
    c = df["close"]
    # warmup: ewm di pandas parte dalla prima barra valida (salta i NaN),
    # quindi EMA200/ATR vanno mascherati finche' non hanno storia reale
    # sufficiente, altrimenti su una coin listata da poco il filtro di
    # regime "vale" gia' pochi giorni dopo il listing
    n_valid = c.notna().cumsum()
    e200 = ema(c, 200).where(n_valid >= 200)
    a = atr(df, 14).where(n_valid >= 14)
    hi = c.rolling(p.ch_len).max().shift(1)
    regime = (c > e200) & (ema(c, 50) > e200)
    entry = (c > hi) & (c > e200)
    if p.use_alignment:
        entry &= ema(c, 50) > e200
    if p.use_btc_filter and not is_btc and btc_regime is not None:
        entry &= btc_regime.reindex(df.index).fillna(False)
    if p.require_mom_pos:
        entry &= c.pct_change(90) > 0
    if p.vol_cap_pctile is not None:
        atrp = a / c
        thr = atrp.rolling(365, min_periods=100).quantile(p.vol_cap_pctile).shift(1)
        entry &= (atrp <= thr) | thr.isna()
    return {
        "entry": entry.fillna(False).to_numpy(),
        "exit": (c < ema(c, p.exit_len)).fillna(False).to_numpy(),
        "atr": a.to_numpy(),
        "mom": c.pct_change(90).fillna(-9.9).to_numpy(),  # priorita' ingressi
        "regime": regime.fillna(False).to_numpy(),
    }


@dataclass
class PortfolioResult:
    equity: pd.Series = field(repr=False, default=None)
    trades: list = field(repr=False, default_factory=list)
    metrics: dict = field(default_factory=dict)
    exposure: pd.Series = field(repr=False, default=None)


def run_portfolio(data: dict[str, pd.DataFrame], p: ApexParams,
                  initial: float = 10_000) -> PortfolioResult:
    syms = list(data.keys())
    dates = data[syms[0]].index
    for s in syms:
        assert len(data[s].index) == len(dates), f"{s}: indice non allineato"

    arr = {s: {k: data[s][k].to_numpy() for k in ["open", "high", "low", "close"]}
           for s in syms}
    btc_c = data["BTCUSD"]["close"]
    # stesso warmup di build_signals: la EMA200 del filtro BTC deve avere
    # 200 barre reali prima di dichiarare il regime valido
    btc_regime = (btc_c > ema(btc_c, 200)) & (btc_c.notna().cumsum() >= 200)
    sig = {s: build_signals(data[s], p, btc_regime, s == "BTCUSD") for s in syms}

    cost = (p.fee_pct + p.slippage_pct) / 100
    cash = initial
    pos = {s: None for s in syms}   # dict: qty, entry_px, stop, trail, entry_i, hh, adds
    pend_in = {s: False for s in syms}
    pend_out = {s: False for s in syms}
    pend_add = {s: False for s in syms}
    trades: list[tuple] = []
    equity = np.empty(len(dates))
    exposure = np.empty(len(dates))
    eq_ema = initial          # EMA50 dell'equity (protezione equity-curve)
    eq_prev = initial
    eq_peak = initial         # massimo storico dell'equity (per il freno DD)
    last_loss_i = {s: -10**9 for s in syms}  # ultima uscita in perdita per coin
    EQ_ALPHA = 2 / 51

    def mark_equity(i: int, price_key: str) -> float:
        val = cash
        for s, ps in pos.items():
            if ps:
                val += ps["qty"] * arr[s][price_key][i]
        return val

    def close_pos(s: str, i: int, raw_px: float, reason: str):
        nonlocal cash
        ps = pos[s]
        fill = raw_px * (1 - cost)
        cash += ps["qty"] * fill
        ret = (fill - ps["entry_px"]) / ps["entry_px"] * 100
        if ret <= 0:
            last_loss_i[s] = i
        trades.append(Trade(dates[ps["entry_i"]], dates[i], ps["entry_px"],
                            fill, f"long:{s}", ret, reason,
                            ps["qty"] * (fill - ps["entry_px"])))
        pos[s] = None

    def entry_frac(s: str, i: int, eq_now: float, risk: float, cap: float) -> float:
        """Frazione di equity da investire, con tutte le scale di rischio."""
        o = arr[s]["open"][i]
        a = sig[s]["atr"][i - 1] if i > 0 else np.nan  # ATR di ieri: no lookahead
        if np.isnan(a) or o <= 0:
            return 0.0
        stop_dist_pct = p.trail_mult * a / o * 100
        if p.breadth_scaling and i > 0:
            breadth = np.mean([sig[x]["regime"][i - 1] for x in syms])
            risk *= max(0.4, breadth)
        frac = min(cap, risk / max(stop_dist_pct, 1e-9))
        if p.eq_curve_filter and eq_prev < eq_ema:
            frac *= 0.5   # il sistema stesso e' in drawdown: de-risk
        return frac

    for i in range(len(dates)):
        # 1) uscite da segnale, eseguite all'apertura
        for s in syms:
            if pend_out[s] and pos[s]:
                close_pos(s, i, arr[s]["open"][i], "signal")
            pend_out[s] = False

        # 2) ingressi all'apertura: priorita' al momentum piu' forte
        eq_now = mark_equity(i, "open")

        # ── selezione modalita' giornaliera (APEX-S) ────────────────
        # Usa solo informazioni della barra precedente: nessun lookahead.
        risk_today, cap_today = p.risk_pct, p.max_frac
        topk_today, lev_today = p.top_k, p.leverage
        entries_on = True
        if p.mode_switch and i > 0:
            btc_on = sig["BTCUSD"]["regime"][i - 1]
            breadth = float(np.mean([sig[x]["regime"][i - 1] for x in syms]))
            if not btc_on:
                entries_on = False          # mercato in bear: niente nuovi rischi
            elif breadth < p.breadth_hi:    # regime fragile: modalita' difensiva
                risk_today, cap_today = p.def_risk, p.def_frac
                topk_today, lev_today = p.def_topk, p.def_lev
        # freno DD: il portafoglio e' sotto del X% dal massimo degli ultimi
        # 90 giorni -> niente nuovi rischi finche' non si risale. Il picco
        # rolling (non storico) evita il lock-out permanente dopo un grande
        # bull: il riferimento "invecchia" e il sistema puo' ripartire.
        if p.dd_brake is not None and i > 0:
            roll_peak = float(np.max(equity[max(0, i - 90):i]))
            if eq_prev < roll_peak * (1 - p.dd_brake):
                entries_on = False
        # vol-targeting: la leva disponibile scala sull'inverso della
        # volatilita' realizzata del portafoglio (30 gg, annualizzata)
        if p.vol_target is not None and i > 31:
            eq_win = equity[i - 31:i]
            rets = np.diff(eq_win) / eq_win[:-1]
            rv = float(np.std(rets)) * np.sqrt(365)
            if rv > 1e-6:
                lev_today = min(lev_today, max(p.vol_floor, p.vol_target / rv))

        candidates = [s for s in syms if pend_in[s] and pos[s] is None
                      and i - last_loss_i[s] > p.cooldown] if entries_on else []
        # momentum di IERI: la decisione per l'open di oggi non puo' usare
        # il close odierno (no lookahead, come breadth/ATR/regime sopra)
        candidates.sort(key=lambda s: sig[s]["mom"][max(i - 1, 0)], reverse=True)
        # rotazione: solo le prime k coin per momentum sono eleggibili
        if topk_today is not None:
            rank = sorted(syms, key=lambda s: sig[s]["mom"][max(i - 1, 0)], reverse=True)
            allowed = set(rank[:topk_today])
            candidates = [s for s in candidates if s in allowed]
        for s in candidates:
            n_open = sum(1 for ps in pos.values() if ps)
            if n_open >= p.max_pos or eq_now <= 0:
                continue
            frac = entry_frac(s, i, eq_now, risk_today, cap_today)
            if frac <= 0:
                continue
            o = arr[s]["open"][i]
            # potere d'acquisto: con leva 1 e' il cash; con leva >1 si puo'
            # andare a cash negativo fino a leverage * equity di esposizione
            invested_now = eq_now - cash
            buying_power = lev_today * eq_now - invested_now
            invested = min(frac * eq_now, buying_power)
            if lev_today <= 1.0:
                invested = min(invested, cash)
            if invested < eq_now * 0.01:
                continue
            fill = o * (1 + cost)
            pos[s] = {"qty": invested / fill, "entry_px": fill, "entry_i": i,
                      "stop": fill * (1 - p.sl_pct / 100), "trail": -np.inf,
                      "hh": -np.inf, "adds": 0}
            cash -= invested
        # il segnale vale solo per l'apertura successiva alla chiusura che lo
        # ha generato: i pendenti non eseguiti (top-k, cooldown, blocco
        # ingressi) decadono e si riarmano solo se l'entry e' ancora vera
        for s in syms:
            pend_in[s] = False

        # 2b) piramidazione: un solo add-on a meta' size su nuovo breakout
        for s in syms:
            if pend_add[s] and pos[s]:
                ps = pos[s]
                frac = entry_frac(s, i, eq_now, risk_today, cap_today) * 0.5
                invested_now = eq_now - cash
                buying_power = lev_today * eq_now - invested_now
                invested = min(frac * eq_now, buying_power)
                if lev_today <= 1.0:
                    invested = min(invested, cash)
                if invested >= eq_now * 0.01:
                    fill = arr[s]["open"][i] * (1 + cost)
                    new_qty = invested / fill
                    tot = ps["qty"] + new_qty
                    ps["entry_px"] = (ps["entry_px"] * ps["qty"] + fill * new_qty) / tot
                    ps["qty"] = tot
                    ps["adds"] += 1
                    cash -= invested
            pend_add[s] = False

        # 3) stop intrabar (trailing aggiornato solo fino a ieri: no lookahead);
        #    lo stop fisso e' attivo anche sulla barra di ingresso
        for s in syms:
            ps = pos[s]
            if ps and i == ps["entry_i"] and arr[s]["low"][i] <= ps["stop"]:
                close_pos(s, i, ps["stop"], "stop")
            elif ps and i > ps["entry_i"]:
                eff = max(ps["stop"], ps["trail"]) if np.isfinite(ps["trail"]) else ps["stop"]
                if arr[s]["low"][i] <= eff:
                    close_pos(s, i, min(arr[s]["open"][i], eff), "stop")

        # 4) aggiorna trailing con la chiusura odierna
        #    (chandelier: dal massimo close dall'ingresso, non dal close odierno)
        for s in syms:
            ps = pos[s]
            if ps and not np.isnan(sig[s]["atr"][i]):
                ps["hh"] = max(ps["hh"], arr[s]["close"][i])
                base = ps["hh"] if p.chandelier else arr[s]["close"][i]
                mult = p.trail_mult
                # profit-lock: oltre il trigger di profitto il trailing si
                # stringe -> restituisce meno dai top parabolici
                if (p.lock_trigger is not None
                        and ps["hh"] / ps["entry_px"] - 1 > p.lock_trigger):
                    mult = p.lock_mult
                lvl = base - mult * sig[s]["atr"][i]
                ps["trail"] = max(ps["trail"], lvl)

        # 5) segnali di fine giornata per domani
        for s in syms:
            ps = pos[s]
            if ps is None and sig[s]["entry"][i]:
                if p.trade_only is None or s in p.trade_only:
                    pend_in[s] = True
            if ps is not None and sig[s]["exit"][i]:
                # smart exit: l'uscita EMA20 scatta solo se il trade e' in
                # perdita; i vincitori restano gestiti dal solo trailing
                if not p.smart_exit or arr[s]["close"][i] < ps["entry_px"]:
                    pend_out[s] = True
            if (p.pyramid and ps is not None and sig[s]["entry"][i]
                    and ps["adds"] == 0 and i > ps["entry_i"]
                    and arr[s]["close"][i] > ps["entry_px"] * 1.05):
                pend_add[s] = True

        # funding perpetual: si paga sull'INTERO notional delle posizioni
        # aperte, ogni giorno in posizione (la venue di riferimento sono i
        # futures: il solo interesse sul cash negativo sottostimerebbe)
        notional = sum(ps["qty"] * arr[s]["close"][i] for s, ps in pos.items() if ps)
        if notional > 0:
            cash -= notional * p.borrow_apr / 100 / 365
        equity[i] = mark_equity(i, "close")
        exposure[i] = (equity[i] - cash) / equity[i] if equity[i] > 0 else 0
        eq_prev = equity[i]
        eq_peak = max(eq_peak, equity[i])
        eq_ema = eq_ema + EQ_ALPHA * (equity[i] - eq_ema)
        if equity[i] <= 0:  # conto azzerato: liquidazione forzata, fine
            for s in syms:
                if pos[s]:
                    close_pos(s, i, arr[s]["close"][i], "margin_call")
            cash = 0.0
            equity[i:] = 0.0
            exposure[i:] = 0.0
            break

    # liquidazione finale per il calcolo dei rendimenti
    last = len(dates) - 1
    for s in syms:
        if pos[s]:
            close_pos(s, last, arr[s]["close"][last], "end_of_data")
    equity[last] = cash

    eq = pd.Series(equity, index=dates)
    res = PortfolioResult(equity=eq, trades=trades,
                          exposure=pd.Series(exposure, index=dates))
    res.metrics = compute_metrics(eq, trades, initial)
    res.metrics["avg_exposure_pct"] = round(float(np.mean(exposure)) * 100, 1)
    return res


def load_all() -> dict[str, pd.DataFrame]:
    return {s: load_csv(os.path.join(DATA, f"{s}.csv")) for s in SYMBOLS}


SYMBOLS_10 = SYMBOLS + ["ADAUSD", "DOGEUSD", "LINKUSD", "AVAXUSD", "DOTUSD"]


def load_universe(symbols=None) -> dict[str, pd.DataFrame]:
    """Carica un universo arbitrario di coin (default: le 5 originali).

    Le coin con storico piu' corto (es. DOT su FMP parte da giu 2021)
    vengono riallineate al calendario di BTC con NaN iniziali: gli
    indicatori restano NaN e bloccano gli ingressi finche' non c'e'
    storia sufficiente, come per una coin listata piu' tardi.
    """
    symbols = symbols or SYMBOLS
    data = {s: load_csv(os.path.join(DATA, f"{s}.csv")) for s in symbols}
    idx = data["BTCUSD"].index
    return {s: df.reindex(idx) for s, df in data.items()}
