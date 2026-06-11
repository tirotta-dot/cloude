"""Motore di backtest event-driven per dati OHLCV giornalieri.

Convenzioni:
- I segnali sono calcolati sulla chiusura della barra t.
- L'esecuzione avviene all'apertura della barra t+1 (niente lookahead).
- Stop loss / take profit / trailing stop sono valutati intrabar
  usando high/low della barra corrente, con gestione dei gap.
- Commissioni e slippage applicati a ogni lato dell'operazione.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

FEE_PCT = 0.10       # commissione taker per lato (Binance/Coinrule tipica)
SLIPPAGE_PCT = 0.05  # slippage stimato per lato


# ── Indicatori ──────────────────────────────────────────────────────────────

def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    delta = s.diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    # RMA (media di Wilder), come ta.rsi di TradingView
    roll_up = up.ewm(alpha=1 / n, adjust=False).mean()
    roll_down = down.ewm(alpha=1 / n, adjust=False).mean()
    rs = roll_up / roll_down
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    prev_c = c.shift(1)
    tr = pd.concat([h - l, (h - prev_c).abs(), (l - prev_c).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def bollinger(s: pd.Series, n: int = 20, mult: float = 2.0):
    basis = sma(s, n)
    dev = mult * s.rolling(n).std(ddof=0)
    return basis, basis + dev, basis - dev


# ── Definizione strategia ───────────────────────────────────────────────────

@dataclass
class StrategySignals:
    """Output di una strategia: segnali e regole di uscita.

    entry/exit sono Series booleane allineate al DataFrame (valutate a fine
    barra). I parametri di rischio sono percentuali sul prezzo di ingresso;
    trail_atr_mult usa l'ATR della barra di ingresso aggiornato barra per barra.
    """
    entry: pd.Series
    exit: pd.Series
    side: str = "long"               # "long" o "short"
    sl_pct: float | None = None
    tp_pct: float | None = None
    trail_atr_mult: float | None = None
    atr_series: pd.Series | None = None
    risk_pct: float | None = None  # rischio per trade in % equity (sizing ATR); None = 100% equity


@dataclass
class Trade:
    entry_date: object
    exit_date: object
    entry_px: float
    exit_px: float
    side: str
    ret_pct: float
    reason: str


@dataclass
class Result:
    symbol: str
    strategy: str
    equity: pd.Series = field(repr=False, default=None)
    trades: list = field(repr=False, default_factory=list)
    metrics: dict = field(default_factory=dict)


def _apply_costs(px: float, side: str, is_entry: bool) -> float:
    cost = (FEE_PCT + SLIPPAGE_PCT) / 100
    buying = (side == "long") == is_entry
    return px * (1 + cost) if buying else px * (1 - cost)


def run_backtest(df: pd.DataFrame, sig: StrategySignals, symbol: str,
                 name: str, initial_capital: float = 10_000) -> Result:
    o = df["open"].to_numpy()
    h = df["high"].to_numpy()
    l = df["low"].to_numpy()
    c = df["close"].to_numpy()
    dates = df.index
    entry_sig = sig.entry.fillna(False).to_numpy()
    exit_sig = sig.exit.fillna(False).to_numpy()
    atr_arr = sig.atr_series.to_numpy() if sig.atr_series is not None else None
    is_long = sig.side == "long"

    cash = initial_capital
    qty = 0.0
    entry_px = stop_px = tp_px = np.nan
    trail_px = -np.inf if is_long else np.inf
    entry_i = -1
    pending_entry = pending_exit = False
    trades: list[Trade] = []
    equity = np.empty(len(df))

    def close_position(i: int, raw_px: float, reason: str):
        nonlocal cash, qty, entry_i
        fill = _apply_costs(raw_px, sig.side, is_entry=False)
        if is_long:
            cash = cash + qty * fill
            ret = (fill - entry_px) / entry_px * 100
        else:
            # short: pnl in cash sul nozionale
            cash = cash + qty * (entry_px - fill)
            ret = (entry_px - fill) / entry_px * 100
        trades.append(Trade(dates[entry_i], dates[i], entry_px, fill, sig.side, ret, reason))
        qty = 0.0
        entry_i = -1

    for i in range(len(df)):
        # 1) esegue ordini decisi alla chiusura della barra precedente
        if pending_exit and qty != 0:
            close_position(i, o[i], "signal")
            pending_exit = False
        if pending_entry and qty == 0:
            fill = _apply_costs(o[i], sig.side, is_entry=True)
            # frazione di equity da investire: con risk_pct attivo la size e'
            # tale che la distanza dello stop costi ~risk_pct% dell'equity
            frac = 1.0
            if sig.risk_pct is not None:
                stop_dist_pct = None
                if sig.trail_atr_mult is not None and atr_arr is not None and not np.isnan(atr_arr[i]):
                    stop_dist_pct = sig.trail_atr_mult * atr_arr[i] / o[i] * 100
                elif sig.sl_pct is not None:
                    stop_dist_pct = sig.sl_pct
                if stop_dist_pct and stop_dist_pct > 0:
                    frac = min(1.0, sig.risk_pct / stop_dist_pct)
            invested = cash * frac
            if is_long:
                qty = invested / fill
                cash -= invested
            else:
                qty = invested / fill  # nozionale
            entry_px = fill
            entry_i = i
            stop_px = np.nan
            if sig.sl_pct is not None:
                stop_px = entry_px * (1 - sig.sl_pct / 100) if is_long else entry_px * (1 + sig.sl_pct / 100)
            tp_px = np.nan
            if sig.tp_pct is not None:
                tp_px = entry_px * (1 + sig.tp_pct / 100) if is_long else entry_px * (1 - sig.tp_pct / 100)
            trail_px = -np.inf if is_long else np.inf
            pending_entry = False

        # 2) gestione intrabar di SL/TP/trailing sulla barra corrente.
        #    Il trailing usato qui e' quello calcolato fino alla barra
        #    precedente: viene aggiornato solo dopo il controllo (no lookahead).
        if qty != 0 and i > entry_i:
            candidates = []
            if not np.isnan(stop_px):
                candidates.append(stop_px)
            if np.isfinite(trail_px):
                candidates.append(trail_px)
            eff_stop = (max(candidates) if is_long else min(candidates)) if candidates else None
            if is_long:
                if eff_stop is not None and l[i] <= eff_stop:
                    close_position(i, min(o[i], eff_stop), "stop")
                elif not np.isnan(tp_px) and h[i] >= tp_px:
                    close_position(i, max(o[i], tp_px), "take_profit")
            else:
                if eff_stop is not None and h[i] >= eff_stop:
                    close_position(i, max(o[i], eff_stop), "stop")
                elif not np.isnan(tp_px) and l[i] <= tp_px:
                    close_position(i, min(o[i], tp_px), "take_profit")

        # aggiorna il trailing stop con la chiusura della barra corrente
        if qty != 0 and sig.trail_atr_mult is not None and atr_arr is not None and not np.isnan(atr_arr[i]):
            lvl = (c[i] - sig.trail_atr_mult * atr_arr[i]) if is_long else (c[i] + sig.trail_atr_mult * atr_arr[i])
            trail_px = max(trail_px, lvl) if is_long else min(trail_px, lvl)

        # 3) registra i segnali per la prossima barra
        if qty == 0 and entry_sig[i]:
            pending_entry = True
        if qty != 0 and exit_sig[i]:
            pending_exit = True

        # 4) equity mark-to-market
        if qty != 0:
            equity[i] = (cash + qty * c[i]) if is_long else cash + qty * (entry_px - c[i])
        else:
            equity[i] = cash

    # chiude l'eventuale posizione residua all'ultima barra
    if qty != 0:
        close_position(len(df) - 1, c[-1], "end_of_data")
        equity[-1] = cash

    eq = pd.Series(equity, index=dates)
    res = Result(symbol=symbol, strategy=name, equity=eq, trades=trades)
    res.metrics = compute_metrics(eq, trades, initial_capital)
    return res


def compute_metrics(eq: pd.Series, trades: list, initial: float) -> dict:
    total_ret = (eq.iloc[-1] / initial - 1) * 100
    n_years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1e-9)
    cagr = ((eq.iloc[-1] / initial) ** (1 / n_years) - 1) * 100 if eq.iloc[-1] > 0 else -100.0
    peak = eq.cummax()
    dd = (eq / peak - 1) * 100
    max_dd = dd.min()
    daily_ret = eq.pct_change().dropna()
    sharpe = (daily_ret.mean() / daily_ret.std() * np.sqrt(365)) if daily_ret.std() > 0 else 0.0
    downside = daily_ret[daily_ret < 0].std()
    sortino = (daily_ret.mean() / downside * np.sqrt(365)) if downside and downside > 0 else 0.0
    calmar = cagr / abs(max_dd) if max_dd < 0 else float("inf")
    wins = [t for t in trades if t.ret_pct > 0]
    losses = [t for t in trades if t.ret_pct <= 0]
    gross_win = sum(t.ret_pct for t in wins)
    gross_loss = -sum(t.ret_pct for t in losses)
    # massima serie di perdite consecutive
    max_consec = streak = 0
    for t in trades:
        streak = streak + 1 if t.ret_pct <= 0 else 0
        max_consec = max(max_consec, streak)
    return {
        "total_return_pct": round(total_ret, 2),
        "cagr_pct": round(cagr, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "sharpe": round(float(sharpe), 2),
        "sortino": round(float(sortino), 2),
        "calmar": round(float(calmar), 2),
        "n_trades": len(trades),
        "win_rate_pct": round(len(wins) / len(trades) * 100, 1) if trades else 0.0,
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "avg_trade_pct": round(np.mean([t.ret_pct for t in trades]), 2) if trades else 0.0,
        "max_consec_losses": max_consec,
    }


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    return df[["open", "high", "low", "close", "volume"]].astype(float)
