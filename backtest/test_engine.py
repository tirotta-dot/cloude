"""Test di sanita' del motore di backtest su dati sintetici.

Verificano le proprieta' che proteggono dai bug piu' costosi:
esecuzione ritardata (no lookahead), stop sulla barra di ingresso,
trailing monotono, applicazione dei costi.
Esecuzione: python3 backtest/test_engine.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from engine import FEE_PCT, SLIPPAGE_PCT, StrategySignals, run_backtest  # noqa: E402

COST = (FEE_PCT + SLIPPAGE_PCT) / 100


def make_df(opens, highs, lows, closes):
    idx = pd.date_range("2024-01-01", periods=len(opens), freq="D")
    return pd.DataFrame({"open": opens, "high": highs, "low": lows,
                         "close": closes, "volume": 1.0}, index=idx)


def sig(df, entry_idx=(), exit_idx=(), **kw):
    e = pd.Series(False, index=df.index)
    x = pd.Series(False, index=df.index)
    for i in entry_idx:
        e.iloc[i] = True
    for i in exit_idx:
        x.iloc[i] = True
    return StrategySignals(entry=e, exit=x, **kw)


def test_no_lookahead_entry():
    """Il segnale alla barra 1 deve eseguire all'open della barra 2."""
    df = make_df([100, 100, 110, 110], [100, 100, 110, 110],
                 [100, 100, 110, 110], [100, 100, 110, 110])
    res = run_backtest(df, sig(df, entry_idx=[1]), "T", "t")
    t = res.trades[0]
    assert abs(t.entry_px - 110 * (1 + COST)) < 1e-9, t.entry_px
    print("ok  no_lookahead_entry")


def test_stop_on_entry_bar():
    """Crollo nel giorno di ingresso: lo stop fisso deve scattare subito."""
    df = make_df([100, 100, 100, 100], [100, 100, 101, 100],
                 [100, 100, 80, 100], [100, 100, 81, 100])
    res = run_backtest(df, sig(df, entry_idx=[1], sl_pct=5.0), "T", "t")
    t = res.trades[0]
    assert t.reason == "stop" and t.exit_date == df.index[2]
    expected_stop = 100 * (1 + COST) * 0.95
    assert abs(t.exit_px - expected_stop * (1 - COST)) < 1e-6
    print("ok  stop_on_entry_bar")


def test_trailing_no_lookahead():
    """Il trailing della barra corrente non deve usare la chiusura odierna.

    Barra 2: sale molto (trail salirebbe). Barra 3: scende sotto il trail
    di barra 2 ma sopra quello di barra 1 -> nessuna uscita se il trail
    fosse aggiornato correttamente solo a fine barra precedente.
    """
    df = make_df([100, 100, 100, 120, 109],
                 [100, 100, 121, 121, 115],
                 [100, 100, 99, 110, 108],
                 [100, 100, 120, 120, 110])
    # ATR costante artificiale: serie fornita a mano
    a = pd.Series(2.0, index=df.index)
    s = sig(df, entry_idx=[1], trail_atr_mult=2.0)
    s.atr_series = a
    res = run_backtest(df, s, "T", "t")
    # trail dopo barra 2 (close 120): 116. Barra 3 low 110 <= 116 -> stop a 116
    # ma con il trail di barra 2 valutato su barra 3, non su barra 2 stessa.
    t = res.trades[0]
    assert t.reason == "stop" and t.exit_date == df.index[3], (t.reason, t.exit_date)
    assert abs(t.exit_px - 116 * (1 - COST)) < 1e-9, t.exit_px
    print("ok  trailing_no_lookahead")


def test_costs_applied_both_sides():
    df = make_df([100] * 5, [100] * 5, [100] * 5, [100] * 5)
    res = run_backtest(df, sig(df, entry_idx=[1], exit_idx=[2]), "T", "t")
    t = res.trades[0]
    expected = ((1 - COST) / (1 + COST) - 1) * 100
    assert abs(t.ret_pct - expected) < 1e-9
    print("ok  costs_applied_both_sides")


def test_risk_sizing_caps_loss():
    """Con risk_pct, la perdita sull'equity deve essere ~risk quando lo stop
    trailing scatta alla distanza prevista."""
    n = 10
    df = make_df([100] * n, [100] * n, [100] * n, [100] * n)
    df.iloc[5] = [100, 100, 60, 60, 1.0]      # crollo: low 60
    df.iloc[6:] = [[60, 60, 60, 60, 1.0]] * (n - 6)
    a = pd.Series(2.5, index=df.index)   # stop dist = 4*2.5 = 10 -> 10%
    s = sig(df, entry_idx=[1], trail_atr_mult=4.0)
    s.atr_series = a
    s.risk_pct = 2.0   # frazione = 2/10 = 20% dell'equity
    res = run_backtest(df, s, "T", "t")
    eq_loss_pct = (res.equity.iloc[-1] / 10_000 - 1) * 100
    # perdita attesa ~ -2% (20% di equity che perde ~10%) + costi
    assert -2.7 < eq_loss_pct < -1.8, eq_loss_pct
    print("ok  risk_sizing_caps_loss")


if __name__ == "__main__":
    test_no_lookahead_entry()
    test_stop_on_entry_bar()
    test_trailing_no_lookahead()
    test_costs_applied_both_sides()
    test_risk_sizing_caps_loss()
    print("\nTutti i test passati.")
