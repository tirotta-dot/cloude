"""APEX-F (Fast): variante ad alta frequenza + generatore preset 4H.

Due obiettivi:
 1. Daily FAST (validato): canale breakout corto, niente cooldown/vol-cap,
    uscite rapide -> molti piu' trade su dati reali 2021-2026.
 2. Preset 4H pronti per TradingView: stessa logica V2, ma destinata a
    girare su grafico a 4 ore (NON backtestabile qui: manca lo storico
    intraday -> FMP intraday a pagamento, exchange fuori allowlist).

Genera: classifica single-coin FAST, 5 grafici (densita' trade visibile),
5 file Pine 4H pronti.
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
CHARTS = os.path.join(HERE, "charts", "fast")
READY4H = os.path.join(HERE, "..", "pinescript", "ready_4h")

# Single-chart FAST: 1 posizione, BTC solo regime, parametri reattivi
APEX_F = replace(APEX_V2, top_k=None, max_pos=1, vol_target=None,
                 ch_len=7, exit_len=10, cooldown=0, vol_cap_pctile=None)


def run_coin(coin, p_base):
    syms = ["BTCUSD"] if coin == "BTCUSD" else ["BTCUSD", coin]
    data = load_universe(syms)
    p = p_base if coin == "BTCUSD" else replace(p_base, trade_only=(coin,))
    return run_portfolio(data, p), data[coin]


def chart(coin, res, px, rank):
    os.makedirs(CHARTS, exist_ok=True)
    fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                           gridspec_kw={"height_ratios": [2, 1]})
    ax[0].plot(px.index, px["close"], lw=0.8, color="#607d8b", label=coin)
    b = [(t.entry_date, t.entry_px) for t in res.trades]
    sw = [(t.exit_date, t.exit_px) for t in res.trades if t.ret_pct > 0]
    sl = [(t.exit_date, t.exit_px) for t in res.trades if t.ret_pct <= 0]
    if b:
        ax[0].scatter(*zip(*b), marker="^", color="#2e7d32", s=34, zorder=5, label="Ingressi")
    if sw:
        ax[0].scatter(*zip(*sw), marker="v", color="#1565c0", s=34, zorder=5, label="Uscite +")
    if sl:
        ax[0].scatter(*zip(*sl), marker="v", color="#c62828", s=34, zorder=5, label="Uscite -")
    ax[0].set_yscale("log")
    m = res.metrics
    ax[0].set_title(f"#{rank} APEX-F (FAST, daily) su {coin} | {m['n_trades']} trade "
                    f"(~{m['n_trades']/5.44:.0f}/anno) · CAGR {m['cagr_pct']}% · "
                    f"DD {m['max_drawdown_pct']}% · PF {m['profit_factor']}")
    ax[0].legend(loc="upper left", fontsize=8)
    ax[0].grid(alpha=0.3)
    ax[1].plot(res.equity.index, res.equity, lw=1.3, color="#6a1b9a", label="Equity 10.000$")
    ax[1].set_yscale("log")
    ax[1].legend(loc="upper left")
    ax[1].grid(alpha=0.3)
    fig.tight_layout()
    path = os.path.join(CHARTS, f"{rank:02d}_{coin}_FAST.png")
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def make_pine_4h(coin, rank):
    """Preset 4H: V2 standard, ma con header che istruisce TF 4h."""
    os.makedirs(READY4H, exist_ok=True)
    src = open(os.path.join(HERE, "..", "pinescript", "apex_trend_strategy.pine")).read()
    tkr = coin.replace("USD", "USDT")
    hdr = (f"//@version=5\n"
           f"// ════════════════════════════════════════════════════════════════\n"
           f"//  APEX-V2 4H PRONTA PER {coin.replace('USD','')} - timeframe 4 ORE\n"
           f"//  >>> IMPOSTA IL GRAFICO SU 4h (4 ore) <<<  poi incolla e aggiungi.\n"
           f"//  Grafico: BINANCE:{tkr}  |  Timeframe: 4H\n"
           f"//\n"
           f"//  Perche' piu' trade: i periodi sono in BARRE, non in giorni. Su 4h\n"
           f"//  una barra = 4 ore, quindi EMA200/canale20 reagiscono ~6x piu'\n"
           f"//  in fretta che sul daily -> molti piu' ingressi.\n"
           f"//  NB: questo preset NON e' backtestato sullo storico intraday\n"
           f"//  (non disponibile in questo ambiente). Verifica nel backtester\n"
           f"//  di TradingView prima di operare. Preset FUTURES leva 2; per\n"
           f"//  spot metti Leva=1.\n"
           f"// ════════════════════════════════════════════════════════════════\n")
    body = "strategy(" + src.split("strategy(", 1)[1]
    body = body.replace('strategy("APEX Trend Strategy v2 [Daily]"',
                        f'strategy("APEX-V2 4H {coin.replace("USD","")}"')
    # default 4H: canale 20, trailing 5, rischio 15, cap 50, leva 2 (come V2)
    body = body.replace('input.int(30,    "Canale breakout (gg)"',
                        'input.int(20,    "Canale breakout (barre)"')
    body = body.replace('input.float(4.0, "Trailing ATR x"', 'input.float(5.0, "Trailing ATR x"')
    body = body.replace('input.float(10.0,"Rischio per trade % equity"',
                        'input.float(15.0,"Rischio per trade % equity"')
    body = body.replace('input.float(30.0,"Cap posizione % equity"',
                        'input.float(50.0,"Cap posizione % equity"')
    body = body.replace('input.float(1.0, "Leva (1 = spot)"', 'input.float(2.0, "Leva (1 = spot)"')
    path = os.path.join(READY4H, f"APEX_V2_4H_{coin.replace('USD','')}.pine")
    open(path, "w").write(hdr + body)
    return path


def main():
    pd.set_option("display.width", 220)
    rows, results = [], {}
    for coin in SYMBOLS_X2:
        res, px = run_coin(coin, APEX_F)
        results[coin] = (res, px)
        m = res.metrics
        rows.append({"coin": coin, "trades": m["n_trades"],
                     "tr/anno": round(m["n_trades"] / 5.44, 1), "CAGR%": m["cagr_pct"],
                     "tot%": m["total_return_pct"], "MaxDD%": m["max_drawdown_pct"],
                     "PF": m["profit_factor"], "win%": m["win_rate_pct"], "Calmar": m["calmar"]})
    tab = pd.DataFrame(rows).sort_values("CAGR%", ascending=False).reset_index(drop=True)
    print("CLASSIFICA APEX-F (FAST, daily):")
    print(tab.to_string(index=False))
    tab.to_csv(os.path.join(HERE, "fast_ranking.csv"), index=False)

    top5 = tab.head(5)["coin"].tolist()
    print("\nTOP 5 FAST:", top5)
    for rank, coin in enumerate(top5, 1):
        res, px = results[coin]
        print(f"  #{rank} {coin}: {chart(coin, res, px, rank)} | {make_pine_4h(coin, rank)}")


if __name__ == "__main__":
    main()
