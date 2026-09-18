"""Checkpoint out-of-sample "vero": il sistema congelato APEX-V2 (e X2/V per
confronto) misurato sulla finestra successiva all'ultimo tuning.

Il README (sez. APEX-V) avverte che il vero out-of-sample del vol-targeting
inizia dopo l'ultima scelta di design (dati fino al 2026-06-09). Questo script
rende il checkpoint ripetibile: estesi i CSV con nuove barre, misura la
performance della finestra OOS_START -> fine dati senza toccare i parametri.

Uso: python3 backtest/checkpoint_oos.py   -> backtest/oos_checkpoint.md + chart
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from engine import compute_metrics  # noqa: E402
from portfolio import load_universe, run_portfolio  # noqa: E402
from report import APEX_V2, APEX_V, APEX_X2, SYMBOLS_X2  # noqa: E402

HERE = os.path.dirname(__file__)

# Ultima barra vista da qualunque decisione di design/tuning del repo.
FROZEN_END = "2026-06-09"
OOS_START = "2026-06-10"


def window_stats(eq: pd.Series, trades, start: str):
    """Metriche della sola finestra OOS: equity normalizzata al suo inizio,
    trade con ingresso dentro la finestra (le posizioni gia' aperte
    contribuiscono comunque all'equity, che e' la misura onesta)."""
    win = eq.loc[start:]
    if len(win) < 2:
        return None
    ret = (win.iloc[-1] / win.iloc[0] - 1) * 100
    dd = ((win / win.cummax()) - 1).min() * 100
    t_in = [t for t in trades if t.entry_date >= pd.Timestamp(start)]
    wins = [t for t in t_in if t.ret_pct > 0]
    closed = [t for t in t_in if t.exit_date is not None]
    return {
        "dal": str(win.index[0].date()), "al": str(win.index[-1].date()),
        "giorni": len(win),
        "rendimento_pct": round(ret, 2),
        "maxdd_pct": round(dd, 2),
        "trade_aperti_in_finestra": len(t_in),
        "trade_chiusi": len(closed),
        "win_rate_pct": round(100 * len(wins) / len(t_in), 1) if t_in else None,
    }


def main():
    pd.set_option("display.width", 220)
    data = load_universe(SYMBOLS_X2)
    last_bar = max(df.index[-1] for df in data.values())

    lines = ["# Checkpoint out-of-sample (sistema congelato)", "",
             f"Parametri congelati al {FROZEN_END}; finestra OOS: {OOS_START} -> "
             f"{last_bar.date()}. Nessun parametro ri-ottimizzato.", ""]

    rows_full, rows_oos = [], []
    for name, params in [("APEX-V2 (consigliata)", APEX_V2),
                         ("APEX-V", APEX_V),
                         ("APEX-X2", APEX_X2)]:
        res = run_portfolio(data, params)
        m = res.metrics
        rows_full.append({"sistema": name, "CAGR%": m["cagr_pct"],
                          "MaxDD%": m["max_drawdown_pct"],
                          "PF": m["profit_factor"], "trades": m["n_trades"]})
        w = window_stats(res.equity, res.trades, OOS_START)
        w = {"sistema": name, **(w or {})}
        rows_oos.append(w)
        if name.startswith("APEX-V2"):
            eq_oos = res.equity.loc[OOS_START:]

    lines += ["## Full period (riferimento, dati estesi)", "",
              pd.DataFrame(rows_full).to_string(index=False), "",
              "## Finestra out-of-sample vera (mai vista da nessuna scelta)", "",
              pd.DataFrame(rows_oos).to_string(index=False), ""]

    # BTC buy&hold nella stessa finestra, per contesto di regime
    btc = data["BTCUSD"]["close"].loc[OOS_START:]
    lines += [f"Contesto: BTC nella finestra {btc.iloc[0]:.0f} -> {btc.iloc[-1]:.0f} "
              f"({(btc.iloc[-1] / btc.iloc[0] - 1) * 100:+.1f}%).", ""]

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(eq_oos.index, eq_oos / eq_oos.iloc[0] * 100, lw=1.6,
            color="#1565c0", label="APEX-V2 (congelata)")
    ax.plot(btc.index, btc / btc.iloc[0] * 100, lw=1.1, color="#9e9e9e",
            label="Buy & Hold BTC")
    ax.axhline(100, color="black", lw=0.6)
    ax.set_title(f"Finestra out-of-sample {OOS_START} -> {last_bar.date()} (base 100)")
    ax.legend(loc="best")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "charts", "oos_checkpoint.png"), dpi=130)

    out = os.path.join(HERE, "oos_checkpoint.md")
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    print(f"Report: {out} | grafico: backtest/charts/oos_checkpoint.png")


if __name__ == "__main__":
    main()
