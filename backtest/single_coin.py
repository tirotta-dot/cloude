"""Backtest APEX-V2 in modalita' single-coin (equivalente al Pine su un
singolo chart TradingView): una sola posizione, BTC usato solo come filtro
di regime. Classifica le 10 coin, genera i grafici delle migliori 5 e i
file Pine pronti con i settaggi impostati.
"""

import os
import sys
from dataclasses import replace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from portfolio import load_universe, run_portfolio  # noqa: E402
from report import APEX_V2, SYMBOLS_X2  # noqa: E402

HERE = os.path.dirname(__file__)
CHARTS = os.path.join(HERE, "charts", "single")
READY = os.path.join(HERE, "..", "pinescript", "ready")

# Config single-chart: identica al Pine (niente rotazione ne' vol-target,
# che sono meccaniche di portafoglio non replicabili su un solo chart)
V2_SINGLE = replace(APEX_V2, top_k=None, max_pos=1, vol_target=None)


def run_coin(coin: str):
    syms = ["BTCUSD"] if coin == "BTCUSD" else ["BTCUSD", coin]
    data = load_universe(syms)
    p = V2_SINGLE if coin == "BTCUSD" else replace(V2_SINGLE, trade_only=(coin,))
    res = run_portfolio(data, p)
    return res, data[coin]


def chart(coin: str, res, px: pd.DataFrame, rank: int):
    os.makedirs(CHARTS, exist_ok=True)
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1]})
    axes[0].plot(px.index, px["close"], lw=0.9, color="#607d8b", label=coin)
    buys = [(t.entry_date, t.entry_px) for t in res.trades]
    sells_w = [(t.exit_date, t.exit_px) for t in res.trades if t.ret_pct > 0]
    sells_l = [(t.exit_date, t.exit_px) for t in res.trades if t.ret_pct <= 0]
    if buys:
        axes[0].scatter(*zip(*buys), marker="^", color="#2e7d32", s=60,
                        zorder=5, label="Ingresso")
    if sells_w:
        axes[0].scatter(*zip(*sells_w), marker="v", color="#1565c0", s=60,
                        zorder=5, label="Uscita in profitto")
    if sells_l:
        axes[0].scatter(*zip(*sells_l), marker="v", color="#c62828", s=60,
                        zorder=5, label="Uscita in perdita")
    axes[0].set_yscale("log")
    m = res.metrics
    axes[0].set_title(f"#{rank} APEX-V2 su {coin} | CAGR {m['cagr_pct']}% · "
                      f"MaxDD {m['max_drawdown_pct']}% · PF {m['profit_factor']} · "
                      f"{m['n_trades']} trade · win {m['win_rate_pct']}%")
    axes[0].legend(loc="upper left")
    axes[0].grid(alpha=0.3)
    axes[1].plot(res.equity.index, res.equity, lw=1.4, color="#6a1b9a",
                 label="Equity (10.000$ iniziali)")
    axes[1].set_yscale("log")
    axes[1].legend(loc="upper left")
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(CHARTS, f"{rank:02d}_{coin}.png")
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def make_pine(coin: str, m: dict, rank: int):
    """Genera il file Pine con i settaggi V2 gia' impostati come default."""
    os.makedirs(READY, exist_ok=True)
    src = open(os.path.join(HERE, "..", "pinescript", "apex_trend_strategy.pine")).read()
    tkr = coin.replace("USD", "USDT")
    hdr = (f"//@version=5\n"
           f"// ════════════════════════════════════════════════════════════════\n"
           f"//  APEX-V2 PRONTA PER {coin.replace('USD','')} - settaggi gia' impostati\n"
           f"//  1. Apri il grafico BINANCE:{tkr} (o equivalente), timeframe 1D\n"
           f"//  2. Incolla questo script nel Pine Editor -> Aggiungi al grafico\n"
           f"//  Backtest 2021->giu 2026 (#{rank} su 10 coin): CAGR {m['cagr_pct']}% |\n"
           f"//  MaxDD {m['max_drawdown_pct']}% | PF {m['profit_factor']} | "
           f"{m['n_trades']} trade | win rate {m['win_rate_pct']}%\n"
           f"//  Preset FUTURES (leva 2): per SPOT metti Leva=1 (rendimento ~meta',\n"
           f"//  stesso profilo). Il funding dei perpetual non e' simulato.\n"
           f"// ════════════════════════════════════════════════════════════════\n")
    body = src.split("strategy(", 1)[1]
    body = "strategy(" + body
    body = body.replace('strategy("APEX Trend Strategy v2 [Daily]"',
                        f'strategy("APEX-V2 {coin.replace("USD","")} [Daily]"')
    # default single-chart V2: canale 20, trailing 5, rischio 15, cap 50, leva 2
    body = body.replace('input.int(30,    "Canale breakout (gg)"',
                        'input.int(20,    "Canale breakout (gg)"')
    body = body.replace('input.float(4.0, "Trailing ATR x"',
                        'input.float(5.0, "Trailing ATR x"')
    body = body.replace('input.float(10.0,"Rischio per trade % equity"',
                        'input.float(15.0,"Rischio per trade % equity"')
    body = body.replace('input.float(30.0,"Cap posizione % equity"',
                        'input.float(50.0,"Cap posizione % equity"')
    body = body.replace('input.float(1.0, "Leva (1 = spot)"',
                        'input.float(2.0, "Leva (1 = spot)"')
    path = os.path.join(READY, f"APEX_V2_{coin.replace('USD','')}.pine")
    open(path, "w").write(hdr + body)
    return path


def main():
    pd.set_option("display.width", 220)
    rows, results = [], {}
    for coin in SYMBOLS_X2:
        res, px = run_coin(coin)
        results[coin] = (res, px)
        m = res.metrics
        rows.append({"coin": coin, "CAGR%": m["cagr_pct"], "tot%": m["total_return_pct"],
                     "MaxDD%": m["max_drawdown_pct"], "PF": m["profit_factor"],
                     "trades": m["n_trades"], "win%": m["win_rate_pct"],
                     "Calmar": m["calmar"], "Sharpe": m["sharpe"]})
    tab = pd.DataFrame(rows).sort_values("CAGR%", ascending=False).reset_index(drop=True)
    print(tab.to_string(index=False))
    tab.to_csv(os.path.join(HERE, "single_coin_ranking.csv"), index=False)

    top5 = tab.head(5)["coin"].tolist()
    print("\nTOP 5:", top5)
    for rank, coin in enumerate(top5, 1):
        res, px = results[coin]
        cp = chart(coin, res, px, rank)
        pp = make_pine(coin, res.metrics, rank)
        print(f"  #{rank} {coin}: {cp} | {pp}")


if __name__ == "__main__":
    main()
