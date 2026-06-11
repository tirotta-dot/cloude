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


def build_signals(df: pd.DataFrame, p: ApexParams, btc_regime: pd.Series | None,
                  is_btc: bool) -> dict:
    c = df["close"]
    e200 = ema(c, 200)
    hi = c.rolling(p.ch_len).max().shift(1)
    entry = (c > hi) & (c > e200)
    if p.use_alignment:
        entry &= ema(c, 50) > e200
    if p.use_btc_filter and not is_btc and btc_regime is not None:
        entry &= btc_regime.reindex(df.index).fillna(False)
    return {
        "entry": entry.fillna(False).to_numpy(),
        "exit": (c < ema(c, p.exit_len)).fillna(False).to_numpy(),
        "atr": atr(df, 14).to_numpy(),
        "mom": c.pct_change(90).fillna(-9.9).to_numpy(),  # priorita' ingressi
    }


@dataclass
class PortfolioResult:
    equity: pd.Series = field(repr=False, default=None)
    trades: list = field(repr=False, default_factory=list)
    metrics: dict = field(default_factory=dict)
    exposure: pd.Series = field(repr=False, default=None)


def run_portfolio(data: dict[str, pd.DataFrame], p: ApexParams,
                  initial: float = 10_000) -> PortfolioResult:
    dates = data[SYMBOLS[0]].index
    for s in SYMBOLS:
        assert len(data[s].index) == len(dates), f"{s}: indice non allineato"

    arr = {s: {k: data[s][k].to_numpy() for k in ["open", "high", "low", "close"]}
           for s in SYMBOLS}
    btc_c = data["BTCUSD"]["close"]
    btc_regime = btc_c > ema(btc_c, 200)
    sig = {s: build_signals(data[s], p, btc_regime, s == "BTCUSD") for s in SYMBOLS}

    cost = (p.fee_pct + p.slippage_pct) / 100
    cash = initial
    pos = {s: None for s in SYMBOLS}   # dict: qty, entry_px, stop, trail, entry_i
    pend_in = {s: False for s in SYMBOLS}
    pend_out = {s: False for s in SYMBOLS}
    trades: list[tuple] = []
    equity = np.empty(len(dates))
    exposure = np.empty(len(dates))

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
        trades.append(Trade(dates[ps["entry_i"]], dates[i], ps["entry_px"],
                            fill, f"long:{s}", ret, reason))
        pos[s] = None

    for i in range(len(dates)):
        # 1) uscite da segnale, eseguite all'apertura
        for s in SYMBOLS:
            if pend_out[s] and pos[s]:
                close_pos(s, i, arr[s]["open"][i], "signal")
            pend_out[s] = False

        # 2) ingressi all'apertura: priorita' al momentum piu' forte
        eq_now = mark_equity(i, "open")
        candidates = [s for s in SYMBOLS if pend_in[s] and pos[s] is None]
        candidates.sort(key=lambda s: sig[s]["mom"][i], reverse=True)
        for s in candidates:
            pend_in[s] = False
            n_open = sum(1 for ps in pos.values() if ps)
            if n_open >= p.max_pos or cash <= 1:
                continue
            o = arr[s]["open"][i]
            a = sig[s]["atr"][i]
            if np.isnan(a) or o <= 0:
                continue
            stop_dist_pct = p.trail_mult * a / o * 100
            frac = min(p.max_frac, p.risk_pct / max(stop_dist_pct, 1e-9))
            invested = min(cash, frac * eq_now)
            if invested < eq_now * 0.01:
                continue
            fill = o * (1 + cost)
            pos[s] = {"qty": invested / fill, "entry_px": fill, "entry_i": i,
                      "stop": fill * (1 - p.sl_pct / 100), "trail": -np.inf}
            cash -= invested

        # 3) stop intrabar (trailing aggiornato solo fino a ieri: no lookahead)
        for s in SYMBOLS:
            ps = pos[s]
            if ps and i > ps["entry_i"]:
                eff = max(ps["stop"], ps["trail"]) if np.isfinite(ps["trail"]) else ps["stop"]
                if arr[s]["low"][i] <= eff:
                    close_pos(s, i, min(arr[s]["open"][i], eff), "stop")

        # 4) aggiorna trailing con la chiusura odierna
        for s in SYMBOLS:
            ps = pos[s]
            if ps and not np.isnan(sig[s]["atr"][i]):
                lvl = arr[s]["close"][i] - p.trail_mult * sig[s]["atr"][i]
                ps["trail"] = max(ps["trail"], lvl)

        # 5) segnali di fine giornata per domani
        for s in SYMBOLS:
            if pos[s] is None and sig[s]["entry"][i]:
                pend_in[s] = True
            if pos[s] is not None and sig[s]["exit"][i]:
                pend_out[s] = True

        equity[i] = mark_equity(i, "close")
        exposure[i] = (equity[i] - cash) / equity[i] if equity[i] > 0 else 0

    # liquidazione finale per il calcolo dei rendimenti
    last = len(dates) - 1
    for s in SYMBOLS:
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
