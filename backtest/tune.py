"""Sweep dei parametri della strategia Donchian+risk sizing.

Obiettivo: trovare una configurazione robusta (non il singolo massimo)
con buon CAGR medio e drawdown contenuto su tutte e 5 le cripto.
"""

import os
import sys
from itertools import product

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from engine import StrategySignals, atr, ema, load_csv, run_backtest  # noqa: E402

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
SYMBOLS = ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD", "XRPUSD"]


def make_strategy(df, ch_len, trail_mult, exit_len, risk_pct):
    e200 = ema(df["close"], 200)
    hi = df["close"].rolling(ch_len).max().shift(1)
    a = atr(df, 14)
    entry = (df["close"] > hi) & (df["close"] > e200)
    exit_ = df["close"] < ema(df["close"], exit_len)
    return StrategySignals(entry=entry, exit=exit_, trail_atr_mult=trail_mult,
                           atr_series=a, sl_pct=12.0, risk_pct=risk_pct)


def main():
    data = {s: load_csv(os.path.join(DATA, f"{s}.csv")) for s in SYMBOLS}
    rows = []
    grid = product([20, 30, 40, 55],      # ch_len
                   [3.0, 4.0, 5.0],       # trail_mult
                   [20, 30],              # exit ema
                   [1.5, 2.0, 3.0, None]) # risk_pct (None = 100% equity)
    for ch, tr, ex, rk in grid:
        ms = [run_backtest(d, make_strategy(d, ch, tr, ex, rk), s, "x").metrics
              for s, d in data.items()]
        rows.append({
            "ch_len": ch, "trail": tr, "exit_ema": ex, "risk": rk if rk else 100,
            "avg_cagr": round(np.mean([m["cagr_pct"] for m in ms]), 1),
            "min_cagr": round(min(m["cagr_pct"] for m in ms), 1),
            "avg_dd": round(np.mean([m["max_drawdown_pct"] for m in ms]), 1),
            "worst_dd": round(min(m["max_drawdown_pct"] for m in ms), 1),
            "avg_sharpe": round(np.mean([m["sharpe"] for m in ms]), 2),
        })
    out = pd.DataFrame(rows)
    # ranking: massimizza CAGR penalizzando il drawdown peggiore (MAR-like)
    out["score"] = out["avg_cagr"] / out["worst_dd"].abs().clip(lower=1)
    out = out.sort_values("score", ascending=False)
    out.to_csv(os.path.join(HERE, "sweep_results.csv"), index=False)
    print(out.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
