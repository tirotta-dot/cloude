"""APEX-X: varianti aggressive per massimizzare il CAGR.

Domanda a cui risponde: "quanto si puo' spingere il rendimento e qual e'
il prezzo in rischio?". Ogni variante e' valutata su:
  - full period 2021-2026 (gonfiato dal bull 2021)
  - out-of-sample 2024-2026 (il numero su cui ragionare)
  - Monte Carlo p95 del drawdown sulla variante scelta
"""

import os
import sys
from dataclasses import replace

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from engine import compute_metrics  # noqa: E402
from portfolio import ApexParams, load_all, run_portfolio  # noqa: E402
from validate import FINAL, monte_carlo  # noqa: E402

HERE = os.path.dirname(__file__)
OOS_START = "2024-01-01"


def evaluate(data, p: ApexParams) -> dict:
    full = run_portfolio(data, p)
    d_oos = {s: df.loc["2023-06-01":] for s, df in data.items()}  # warmup indicatori
    oos = run_portfolio(d_oos, p)
    eq = oos.equity.loc[OOS_START:]
    m_oos = compute_metrics(eq / eq.iloc[0] * 10_000,
                            [t for t in oos.trades
                             if t.entry_date >= pd.Timestamp(OOS_START)], 10_000)
    f = full.metrics
    return {"full_CAGR%": f["cagr_pct"], "full_DD%": f["max_drawdown_pct"],
            "full_Calmar": f["calmar"], "full_PF": f["profit_factor"],
            "oos_CAGR%": m_oos["cagr_pct"], "oos_DD%": m_oos["max_drawdown_pct"],
            "oos_PF": m_oos["profit_factor"]}, full


VARIANTS = {
    "APEX base (riferimento)": FINAL,
    "A1 conc.: risk 15, cap 50, max 3 pos": replace(FINAL, risk_pct=15.0, max_frac=0.50, max_pos=3),
    "A2 rotazione top-2 momentum":          replace(FINAL, top_k=2),
    "A3 top-2 + risk 15, cap 60":           replace(FINAL, top_k=2, risk_pct=15.0, max_frac=0.60),
    "A4 leva 1.5x su base":                 replace(FINAL, leverage=1.5),
    "A5 leva 2x su base":                   replace(FINAL, leverage=2.0),
    "A6 top-1, cap 100, risk 20":           replace(FINAL, top_k=1, max_frac=1.0, risk_pct=20.0, max_pos=1),
    "A7 = A3 + leva 1.5x":                  replace(FINAL, top_k=2, risk_pct=15.0, max_frac=0.60, leverage=1.5),
}


# ── APEX-X: la configurazione aggressiva finale ────────────────────────────
# Rotazione momentum top-3 + rischio 15% + cap 50% + leva 2x + trailing 5xATR.
# Scelta su un plateau (i vicini r12-18 / c40-50 / tr4.5-5.5 / lev1.75-2
# danno full 93-125% e OOS 57-76%): non e' un picco isolato.
FINAL_X = replace(FINAL, top_k=3, risk_pct=15.0, max_frac=0.50,
                  leverage=2.0, trail_mult=5.0)


def main():
    data = load_all()
    pd.set_option("display.width", 220)
    rows, results = [], {}
    variants = {**VARIANTS, "APEX-X finale (top3 r15 c50 lev2 tr5)": FINAL_X}
    for name, p in variants.items():
        m, res = evaluate(data, p)
        rows.append({"variante": name, **m})
        results[name] = res
    tab = pd.DataFrame(rows)
    print(tab.to_string(index=False))
    tab.to_csv(os.path.join(HERE, "aggressive_results.csv"), index=False)

    print("\nStress APEX-X (funding leva e costi):")
    stress_rows = []
    for name, p in [("borrow 30%/anno", replace(FINAL_X, borrow_apr=30.0)),
                    ("borrow 50%/anno", replace(FINAL_X, borrow_apr=50.0)),
                    ("costi doppi", replace(FINAL_X, fee_pct=0.20, slippage_pct=0.10))]:
        m, _ = evaluate(data, p)
        stress_rows.append({"variante": name, **m})
    print(pd.DataFrame(stress_rows).to_string(index=False))

    print("\nMonte Carlo (2000 sim) sulle varianti chiave:")
    for name in ["APEX base (riferimento)", "A5 leva 2x su base",
                 "APEX-X finale (top3 r15 c50 lev2 tr5)"]:
        mc = monte_carlo(results[name].equity)
        print(f"  {name}: DD mediano {mc['dd_mediano']}%, p95 {mc['dd_p95']}%, "
              f"p99 {mc['dd_p99']}%, CAGR mediano {mc['cagr_mediano']}%")

    charts(data, results["APEX base (riferimento)"],
           results["APEX-X finale (top3 r15 c50 lev2 tr5)"])


def charts(data, res_base, res_x):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(os.path.join(HERE, "charts"), exist_ok=True)
    btc = data["BTCUSD"]["close"]
    btc_bh = btc / btc.iloc[0] * 10_000

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                             gridspec_kw={"height_ratios": [3, 1]})
    axes[0].plot(res_x.equity.index, res_x.equity, lw=1.7, color="#6a1b9a",
                 label="APEX-X aggressiva (CAGR 111%)")
    axes[0].plot(res_base.equity.index, res_base.equity, lw=1.5, color="#1565c0",
                 label="APEX base (CAGR 83%)")
    axes[0].plot(btc_bh.index, btc_bh, lw=1.1, color="#9e9e9e", label="Buy & Hold BTC")
    axes[0].set_yscale("log")
    axes[0].set_title("APEX vs APEX-X - equity (scala log) | 10.000$ iniziali, costi e funding inclusi")
    axes[0].legend(loc="upper left")
    axes[0].grid(alpha=0.3)
    for res, col, lab in [(res_x, "#6a1b9a", "APEX-X"), (res_base, "#1565c0", "APEX")]:
        dd = (res.equity / res.equity.cummax() - 1) * 100
        axes[1].plot(dd.index, dd, color=col, lw=1.0, label=lab)
    axes[1].set_title("Drawdown %")
    axes[1].legend(loc="lower left")
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "charts", "apexx_vs_apex.png"), dpi=130)
    print("\nGrafico salvato in backtest/charts/apexx_vs_apex.png")


if __name__ == "__main__":
    main()
