"""Banco di prova dei miglioramenti: ogni feature viene accesa da sola
su APEX-X e tenuta solo se migliora il quadro full + out-of-sample.
Poi le vincenti vengono combinate e ri-validate.
"""

import os
import sys
from dataclasses import replace

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from aggressive import FINAL_X, evaluate  # noqa: E402
from portfolio import SYMBOLS_10, load_universe  # noqa: E402

HERE = os.path.dirname(__file__)

FEATURES = {
    "F1 smart exit (EMA solo se in perdita)": {"smart_exit": True},
    "F2 chandelier trailing":                 {"chandelier": True},
    "F3 momentum positivo richiesto":         {"require_mom_pos": True},
    "F4 rischio scalato su ampiezza regime":  {"breadth_scaling": True},
    "F5 protezione equity-curve":             {"eq_curve_filter": True},
    "F6 piramidazione (1 add-on)":            {"pyramid": True},
    "F7 cap volatilita' (90° pctile)":        {"vol_cap_pctile": 0.90},
}


def table(data, configs: dict) -> pd.DataFrame:
    rows = []
    for name, kw in configs.items():
        p = replace(FINAL_X, **kw) if isinstance(kw, dict) else kw
        m, _ = evaluate(data, p)
        rows.append({"config": name, **m})
    return pd.DataFrame(rows)


def main():
    pd.set_option("display.width", 220)
    data5 = load_universe()

    print("=" * 100, "\nFEATURE singole su APEX-X (universo 5 coin)\n", "=" * 100)
    base = table(data5, {"APEX-X baseline": {}})
    feats = table(data5, FEATURES)
    out = pd.concat([base, feats])
    print(out.to_string(index=False))
    out.to_csv(os.path.join(HERE, "improvements_features.csv"), index=False)


if __name__ == "__main__":
    main()
