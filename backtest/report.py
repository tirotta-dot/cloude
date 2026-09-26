"""Report finale APEX-X2: metriche, walk-forward ancorato a 3 finestre,
Monte Carlo, rendimenti mensili e grafici. Genera backtest/APEX_X2_report.md.
"""

import os
import sys
from dataclasses import replace

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from engine import compute_metrics, period_returns  # noqa: E402
from portfolio import ApexParams, load_universe, run_portfolio  # noqa: E402
from validate import monte_carlo  # noqa: E402

HERE = os.path.dirname(__file__)

# ── APEX-X2: configurazione finale (vedi improvements.py) ──────────────────
# Universo 10 coin, rotazione top-5, canale 20gg, vol-cap 85°, chandelier,
# protezione equity-curve. Definita qui per import da altri moduli.
SYMBOLS_X2 = ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD", "XRPUSD",
              "ADAUSD", "DOGEUSD", "LINKUSD", "AVAXUSD", "DOTUSD"]
APEX_X2 = ApexParams(use_btc_filter=True, use_alignment=True,
                     ch_len=20, exit_len=20, trail_mult=5.0,
                     risk_pct=15.0, max_frac=0.50, max_pos=6,
                     top_k=5, leverage=2.0,
                     vol_cap_pctile=0.85, chandelier=True, eq_curve_filter=True)

# APEX-V "all-weather": X2 + vol-targeting 60% annuo applicato SOLO alla
# leva (floor 1x). Risultato: nessuna finestra walk-forward negativa
# (2023 +198%, 2024 +53%, 2025-26 0.0%) e DD piu' basso, al prezzo di
# meno upside negli anni esplosivi. Validata anche sul test freddo
# cross-sezionale (5 coin mai usate per il tuning: PF 2.4).
APEX_V = replace(APEX_X2, vol_target=0.60, vol_floor=1.0)

# APEX-V2: V + le due cure chirurgiche trovate diagnosticando l'episodio di
# max drawdown (emorragia lenta set 2021 -> ott 2023):
#  - cooldown 15g dopo un'uscita in perdita (stop al tritacarne nel chop:
#    AVAX veniva stoppata 5 volte a -12% in due mesi)
#  - profit-lock: oltre +50% il trailing si stringe a 3xATR (restituisce
#    meno dai top parabolici tipo SOL +308%)
# Risultato: CAGR 128% (da 112), DD -33.9% (da -36.6), worst WF DD -22.3%
# (da -34.8), WF 2025-26 +14.9% (da 0). Confermata sul test freddo.
APEX_V2 = replace(APEX_V, cooldown=15, lock_trigger=0.5, lock_mult=3.0)


def anchored_walk_forward(data, p: ApexParams):
    """3 finestre out-of-sample consecutive con parametri sempre congelati:
    la config non viene mai ri-ottimizzata sui dati che poi la giudicano."""
    folds = [("2023", "2022-01-01", "2023-01-01", "2024-01-01"),
             ("2024", "2023-01-01", "2024-01-01", "2025-01-01"),
             ("2025-26", "2024-01-01", "2025-01-01", "2026-12-31")]
    rows = []
    for name, warm, start, end in folds:
        d = {s: df.loc[warm:end] for s, df in data.items()}
        res = run_portfolio(d, p)
        eq = res.equity.loc[start:]
        m = compute_metrics(eq / eq.iloc[0] * 10_000,
                            [t for t in res.trades
                             if t.entry_date >= pd.Timestamp(start)], 10_000)
        rows.append({"finestra OOS": name, "CAGR%": m["cagr_pct"],
                     "MaxDD%": m["max_drawdown_pct"], "PF": m["profit_factor"],
                     "trades": m["n_trades"], "win%": m["win_rate_pct"]})
    return pd.DataFrame(rows)


def monthly_table(eq: pd.Series) -> pd.DataFrame:
    m = period_returns(eq, "ME")
    tab = pd.DataFrame({"anno": m.index.year, "mese": m.index.month, "ret": m.values})
    piv = tab.pivot(index="anno", columns="mese", values="ret").round(1)
    piv.columns = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago",
                   "Set", "Ott", "Nov", "Dic"][:len(piv.columns)]
    return piv


def charts(res, data):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    eq = res.equity
    btc = data["BTCUSD"]["close"]
    btc_bh = btc / btc.iloc[0] * 10_000

    fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=True,
                             gridspec_kw={"height_ratios": [3, 1, 1]})
    axes[0].plot(eq.index, eq, lw=1.7, color="#6a1b9a", label="APEX-X2 (10 coin)")
    axes[0].plot(btc_bh.index, btc_bh, lw=1.1, color="#9e9e9e", label="Buy & Hold BTC")
    axes[0].set_yscale("log")
    axes[0].set_title("APEX-X2 - equity (log) | 10.000$ iniziali, costi e funding inclusi")
    axes[0].legend(loc="upper left")
    axes[0].grid(alpha=0.3)
    dd = (eq / eq.cummax() - 1) * 100
    axes[1].fill_between(dd.index, dd, 0, color="#c62828", alpha=0.75)
    axes[1].set_title("Drawdown %")
    axes[1].grid(alpha=0.3)
    roll = eq.pct_change(365).dropna() * 100
    axes[2].plot(roll.index, roll, color="#1565c0", lw=1.2)
    axes[2].axhline(0, color="black", lw=0.6)
    axes[2].axhline(100, color="green", lw=0.6, ls="--")
    axes[2].set_title("Rendimento rolling 12 mesi % (linea verde = +100%)")
    axes[2].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "charts", "apex_x2_report.png"), dpi=130)
    print("Grafico: backtest/charts/apex_x2_report.png")


def main():
    pd.set_option("display.width", 220)
    data = load_universe(SYMBOLS_X2)
    res = run_portfolio(data, APEX_X2)
    m = res.metrics

    yearly = period_returns(res.equity, "YE")
    wf = anchored_walk_forward(data, APEX_X2)
    mc = monte_carlo(res.equity)
    piv = monthly_table(res.equity)

    tr = pd.DataFrame([{"symbol": t.side.split(":")[1], "entry": t.entry_date.date(),
                        "exit": t.exit_date.date(), "ret_pct": round(t.ret_pct, 2),
                        "reason": t.reason} for t in res.trades])
    tr.to_csv(os.path.join(HERE, "trades_x2.csv"), index=False)

    lines = ["# APEX-X2 - report finale", "",
             f"Universo: {', '.join(SYMBOLS_X2)} | rotazione top-{APEX_X2.top_k} momentum, "
             f"max {APEX_X2.max_pos} posizioni, canale {APEX_X2.ch_len}gg, leva {APEX_X2.leverage}x", "",
             "## Metriche full period (2021 → giu 2026)", "",
             pd.DataFrame([m]).to_string(index=False), "",
             "## Rendimenti per anno", "",
             pd.DataFrame({"anno": [d.year for d in yearly.index],
                           "rendimento%": yearly.round(1).values}).to_string(index=False), "",
             "## Walk-forward ancorato (parametri congelati)", "",
             wf.to_string(index=False), "",
             "## Monte Carlo (2000 block-bootstrap)", "",
             pd.DataFrame([mc]).to_string(index=False), "",
             "## Tabella mensile (%)", "",
             piv.to_string(), "",
             f"Trade totali: {m['n_trades']} (~{m['n_trades'] / 5.44:.0f}/anno) | "
             f"lista completa in trades_x2.csv", ""]
    with open(os.path.join(HERE, "APEX_X2_report.md"), "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines[:20]))
    charts(res, data)


if __name__ == "__main__":
    main()
