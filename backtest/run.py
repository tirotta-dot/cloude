"""Esegue tutti i backtest su 5 cripto e genera backtest/results.md."""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from engine import load_csv, run_backtest  # noqa: E402
from strategies import CANDIDATES, COINRULE  # noqa: E402

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
SYMBOLS = ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD", "XRPUSD"]


def fmt_table(rows: list[dict], cols: list[str]) -> str:
    head = "| " + " | ".join(cols) + " |"
    sep = "|" + "|".join(["---"] * len(cols)) + "|"
    body = ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    return "\n".join([head, sep] + body)


def main():
    data = {s: load_csv(os.path.join(DATA, f"{s}.csv")) for s in SYMBOLS}
    all_strats = {**COINRULE, **CANDIDATES}

    rows = []
    equities = {}
    for strat_name, fn in all_strats.items():
        for sym, df in data.items():
            res = run_backtest(df, fn(df), sym, strat_name)
            m = res.metrics
            rows.append({"strategy": strat_name, "symbol": sym, **m})
            equities[(strat_name, sym)] = res.equity

    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(HERE, "results_full.csv"), index=False)

    # report markdown
    cols = ["symbol", "total_return_pct", "cagr_pct", "max_drawdown_pct",
            "sharpe", "n_trades", "win_rate_pct", "profit_factor"]
    lines = ["# Risultati backtest (daily, 2021 → ago 2026)", "",
             "Commissioni 0.10% + slippage 0.05% per lato. Esecuzione "
             "all'apertura della barra successiva al segnale. Capitale "
             "iniziale 10.000 USD; 100% reinvestito a ogni trade per le "
             "repliche Coinrule, sizing a rischio (~10% dell'equity per "
             "trade) per APEX Trend (finale).", ""]

    buyhold = []
    for sym, df in data.items():
        bh_ret = (df["close"].iloc[-1] / df["open"].iloc[0] - 1) * 100
        peak = df["close"].cummax()
        bh_dd = ((df["close"] / peak - 1) * 100).min()
        buyhold.append({"symbol": sym, "buy_hold_return_pct": round(bh_ret, 1),
                        "buy_hold_max_dd_pct": round(bh_dd, 1)})
    lines += ["## Benchmark Buy & Hold", "",
              fmt_table(buyhold, ["symbol", "buy_hold_return_pct", "buy_hold_max_dd_pct"]), ""]

    for strat_name in all_strats:
        sub = out[out["strategy"] == strat_name].to_dict("records")
        avg_cagr = np.mean([r["cagr_pct"] for r in sub])
        avg_dd = np.mean([r["max_drawdown_pct"] for r in sub])
        lines += [f"## {strat_name}", "",
                  fmt_table(sub, cols), "",
                  f"**Media 5 cripto: CAGR {avg_cagr:.1f}% | MaxDD {avg_dd:.1f}%**", ""]

    # ── Portafoglio APEX: capitale diviso sulle 5 cripto, equal weight ──
    apex_name = "APEX Trend (finale)"
    eqs = pd.concat([equities[(apex_name, s)] / 10_000 for s in SYMBOLS], axis=1)
    port = eqs.mean(axis=1) * 10_000
    from engine import compute_metrics, period_returns
    pm = compute_metrics(port, [], 10_000)
    yearly = period_returns(port, "YE")
    ytab = [{"anno": d.year, "rendimento_pct": round(v, 1)} for d, v in yearly.items()]
    lines += ["## Portafoglio APEX (capitale diviso sulle 5 cripto)", "",
              fmt_table([{"symbol": "PORTAFOGLIO", **{k: pm[k] for k in
                          ["total_return_pct", "cagr_pct", "max_drawdown_pct", "sharpe"]}}],
                        ["symbol", "total_return_pct", "cagr_pct", "max_drawdown_pct", "sharpe"]), "",
              "### Rendimento per anno", "", fmt_table(ytab, ["anno", "rendimento_pct"]), ""]

    with open(os.path.join(HERE, "results.md"), "w") as f:
        f.write("\n".join(lines))

    # riepilogo a video
    summary = out.groupby("strategy")[["cagr_pct", "max_drawdown_pct", "sharpe", "win_rate_pct"]].mean().round(1)
    print(summary.sort_values("cagr_pct", ascending=False).to_string())


if __name__ == "__main__":
    main()
