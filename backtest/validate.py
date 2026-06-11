"""Suite di validazione professionale per APEX (portafoglio reale).

1. Esperimenti sui filtri (regime BTC, allineamento EMA, concentrazione)
2. Walk-forward: ottimizzazione in-sample 2021-2023, verifica out-of-sample
   2024-2026 con parametri CONGELATI
3. Monte Carlo block-bootstrap sui rendimenti giornalieri (distribuzione DD)
4. Stress test: costi raddoppiati, rimozione dei trade migliori
"""

import os
import sys
from dataclasses import replace
from itertools import product

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from engine import compute_metrics  # noqa: E402
from portfolio import ApexParams, load_all, run_portfolio  # noqa: E402

HERE = os.path.dirname(__file__)
RNG = np.random.default_rng(42)


def brief(name: str, m: dict) -> dict:
    return {"config": name, "CAGR%": m["cagr_pct"], "MaxDD%": m["max_drawdown_pct"],
            "Sharpe": m["sharpe"], "Sortino": m["sortino"], "Calmar": m["calmar"],
            "trades": m["n_trades"], "win%": m["win_rate_pct"],
            "PF": m["profit_factor"], "exp%": m.get("avg_exposure_pct", "-")}


def experiments(data) -> pd.DataFrame:
    configs = {
        "E0 base (nessun filtro)":        ApexParams(),
        "E1 + filtro regime BTC":         ApexParams(use_btc_filter=True),
        "E2 + allineamento EMA50>200":    ApexParams(use_alignment=True),
        "E3 = E1 + E2":                   ApexParams(use_btc_filter=True, use_alignment=True),
        "E4 = E3, max 3 posizioni":       ApexParams(use_btc_filter=True, use_alignment=True, max_pos=3),
        "E5 = E3, rischio 12%":           ApexParams(use_btc_filter=True, use_alignment=True, risk_pct=12.0),
        "E6 = E3, rischio 8%":            ApexParams(use_btc_filter=True, use_alignment=True, risk_pct=8.0),
    }
    rows = [brief(n, run_portfolio(data, p).metrics) for n, p in configs.items()]
    return pd.DataFrame(rows)


def walk_forward(data, base: ApexParams):
    """Ottimizza su 2021-2023 (in-sample), congela, verifica su 2024-2026."""
    is_end = "2023-12-31"
    d_is = {s: df.loc[:is_end] for s, df in data.items()}
    d_oos = {s: df.loc["2023-06-01":] for s, df in data.items()}  # warmup EMA200
    oos_start = "2024-01-01"

    grid = list(product([20, 30, 40, 55], [3.0, 4.0, 5.0], [20, 30]))
    rows = []
    for ch, tr, ex in grid:
        p = replace(base, ch_len=ch, trail_mult=tr, exit_len=ex)
        m = run_portfolio(d_is, p).metrics
        score = m["cagr_pct"] / max(abs(m["max_drawdown_pct"]), 1)
        rows.append({"ch": ch, "trail": tr, "exit": ex, "is_cagr": m["cagr_pct"],
                     "is_dd": m["max_drawdown_pct"], "score": round(score, 3)})
    tab = pd.DataFrame(rows).sort_values("score", ascending=False)

    best = tab.iloc[0]
    p_best = replace(base, ch_len=int(best.ch), trail_mult=float(best.trail),
                     exit_len=int(best.exit))
    res_oos = run_portfolio(d_oos, p_best)
    eq_oos = res_oos.equity.loc[oos_start:]
    m_oos = compute_metrics(eq_oos / eq_oos.iloc[0] * 10_000, [
        t for t in res_oos.trades if t.entry_date >= pd.Timestamp(oos_start)], 10_000)

    # confronto: anche la config "deployata" (base) valutata OOS
    res_base_oos = run_portfolio(d_oos, base)
    eqb = res_base_oos.equity.loc[oos_start:]
    m_base_oos = compute_metrics(eqb / eqb.iloc[0] * 10_000, [
        t for t in res_base_oos.trades if t.entry_date >= pd.Timestamp(oos_start)], 10_000)
    return tab, p_best, m_oos, m_base_oos


def monte_carlo(eq: pd.Series, n_sims=2000, block=20):
    """Block bootstrap dei rendimenti giornalieri -> distribuzione di MaxDD."""
    rets = eq.pct_change().dropna().to_numpy()
    n = len(rets)
    dds, finals = [], []
    for _ in range(n_sims):
        idx = RNG.integers(0, n - block, size=n // block + 1)
        sim = np.concatenate([rets[j:j + block] for j in idx])[:n]
        curve = np.cumprod(1 + sim)
        peak = np.maximum.accumulate(curve)
        dds.append(((curve / peak) - 1).min() * 100)
        finals.append((curve[-1] ** (365 / n) - 1) * 100)
    dds, finals = np.array(dds), np.array(finals)
    return {
        "dd_mediano": round(float(np.median(dds)), 1),
        "dd_p95": round(float(np.percentile(dds, 5)), 1),   # 95° percentile peggiore
        "dd_p99": round(float(np.percentile(dds, 1)), 1),
        "cagr_mediano": round(float(np.median(finals)), 1),
        "prob_anno_negativo_pct": round(float((finals < 0).mean() * 100), 1),
    }


def stress(data, p: ApexParams):
    rows = []
    res = run_portfolio(data, p)
    rows.append(brief("costi standard (0.15%/lato)", res.metrics))
    rows.append(brief("costi DOPPI (0.30%/lato)",
                      run_portfolio(data, replace(p, fee_pct=0.20, slippage_pct=0.10)).metrics))
    # rimozione dei 5 trade migliori: l'edge sopravvive senza i fuoriclasse?
    no_best = sorted(res.trades, key=lambda t: t.ret_pct, reverse=True)[5:]
    eq_proxy = res.equity  # equity reale; ricalcolo solo le metriche dei trade
    m = compute_metrics(eq_proxy, no_best, 10_000)
    rows.append({"config": "senza i 5 trade migliori (solo stat. trade)",
                 "CAGR%": "-", "MaxDD%": "-", "Sharpe": "-", "Sortino": "-",
                 "Calmar": "-", "trades": m["n_trades"], "win%": m["win_rate_pct"],
                 "PF": m["profit_factor"], "exp%": "-"})
    return pd.DataFrame(rows), res


# configurazione finale "deployata" (scelta su un plateau robusto, vedi README)
FINAL = ApexParams(use_btc_filter=True, use_alignment=True,
                   risk_pct=10.0, max_frac=0.30)


def main():
    data = load_all()
    pd.set_option("display.width", 200)
    out = []

    def log(*args):
        line = " ".join(str(a) for a in args)
        print(line)
        out.append(line)

    log("=" * 80, "\nESPERIMENTI FILTRI (portafoglio reale, capitale condiviso)\n", "=" * 80)
    exp = experiments(data)
    log(exp.to_string(index=False))
    exp.to_csv(os.path.join(HERE, "experiments.csv"), index=False)

    log("\n", "=" * 80, "\nWALK-FORWARD: ottimizzato 2021-2023, congelato, verificato 2024-2026\n", "=" * 80)
    tab, p_best, m_oos_best, m_oos_final = walk_forward(data, FINAL)
    log("Top 5 configurazioni in-sample (2021-2023):")
    log(tab.head(5).to_string(index=False))
    log(f"\nMigliore in-sample: ch={p_best.ch_len} trail={p_best.trail_mult} exit={p_best.exit_len}")
    log("Out-of-sample 2024-2026 (parametri congelati dalla migliore IS):")
    log(pd.DataFrame([brief("best IS -> OOS", m_oos_best)]).to_string(index=False))
    log("Out-of-sample 2024-2026 della config FINALE (30/4.0/20):")
    log(pd.DataFrame([brief("finale -> OOS", m_oos_final)]).to_string(index=False))

    log("\n", "=" * 80, "\nMONTE CARLO block-bootstrap (2000 simulazioni, blocchi 20gg)\n", "=" * 80)
    res_final = run_portfolio(data, FINAL)
    mc = monte_carlo(res_final.equity)
    log(pd.DataFrame([mc]).to_string(index=False))

    log("\n", "=" * 80, "\nSTRESS TEST\n", "=" * 80)
    st, _ = stress(data, FINAL)
    log(st.to_string(index=False))

    log("\n", "=" * 80, "\nCONFIG FINALE - dettaglio\n", "=" * 80)
    log(pd.DataFrame([brief("APEX finale", res_final.metrics)]).to_string(index=False))
    yearly = (res_final.equity.resample("YE").last() /
              res_final.equity.resample("YE").first() - 1) * 100
    log("\nRendimenti per anno:")
    log(pd.DataFrame({"anno": [d.year for d in yearly.index],
                      "rendimento%": yearly.round(1).values}).to_string(index=False))

    # contributo per cripto
    tr = pd.DataFrame([{"symbol": t.side.split(":")[1], "ret_pct": t.ret_pct,
                        "reason": t.reason} for t in res_final.trades])
    contrib = tr.groupby("symbol").agg(trades=("ret_pct", "size"),
                                       win_rate=("ret_pct", lambda x: round((x > 0).mean() * 100, 1)),
                                       avg_ret=("ret_pct", lambda x: round(x.mean(), 2)))
    log("\nContributo per cripto:")
    log(contrib.to_string())

    # esporta trade list e report
    pd.DataFrame([{"symbol": t.side.split(":")[1], "entry": t.entry_date.date(),
                   "exit": t.exit_date.date(), "entry_px": round(t.entry_px, 4),
                   "exit_px": round(t.exit_px, 4), "ret_pct": round(t.ret_pct, 2),
                   "reason": t.reason} for t in res_final.trades]
                 ).to_csv(os.path.join(HERE, "trades_final.csv"), index=False)
    with open(os.path.join(HERE, "validation_report.txt"), "w") as f:
        f.write("\n".join(out))

    charts(data, res_final)


def charts(data, res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(os.path.join(HERE, "charts"), exist_ok=True)
    eq = res.equity
    btc = data["BTCUSD"]["close"]
    btc_bh = btc / btc.iloc[0] * 10_000

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True,
                             gridspec_kw={"height_ratios": [3, 1]})
    axes[0].plot(eq.index, eq, label="APEX portafoglio 5 cripto", lw=1.6, color="#1565c0")
    axes[0].plot(btc_bh.index, btc_bh, label="Buy & Hold BTC", lw=1.2, color="#9e9e9e")
    axes[0].set_yscale("log")
    axes[0].set_title("APEX Trend - equity (scala log) | 10.000$ iniziali, costi inclusi")
    axes[0].legend(loc="upper left")
    axes[0].grid(alpha=0.3)
    dd = (eq / eq.cummax() - 1) * 100
    dd_bh = (btc_bh / btc_bh.cummax() - 1) * 100
    axes[1].fill_between(dd.index, dd, 0, color="#c62828", alpha=0.7, label="APEX")
    axes[1].plot(dd_bh.index, dd_bh, color="#9e9e9e", lw=0.8, label="B&H BTC")
    axes[1].set_title("Drawdown %")
    axes[1].legend(loc="lower left")
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "charts", "equity_drawdown.png"), dpi=130)

    fig2, ax = plt.subplots(figsize=(10, 5))
    yearly = (eq.resample("YE").last() / eq.resample("YE").first() - 1) * 100
    years = [d.year for d in yearly.index]
    colors = ["#2e7d32" if v >= 0 else "#c62828" for v in yearly.values]
    ax.bar([str(y) for y in years], yearly.values, color=colors)
    for x, v in zip(range(len(years)), yearly.values):
        ax.text(x, v + (2 if v >= 0 else -5), f"{v:.0f}%", ha="center", fontsize=10)
    ax.set_title("APEX Trend - rendimento per anno (%)")
    ax.grid(alpha=0.3, axis="y")
    fig2.tight_layout()
    fig2.savefig(os.path.join(HERE, "charts", "yearly_returns.png"), dpi=130)
    print("\nGrafici salvati in backtest/charts/")


if __name__ == "__main__":
    main()
