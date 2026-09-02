"""Test di sanita' del motore di backtest su dati sintetici.

Verificano le proprieta' che proteggono dai bug piu' costosi:
esecuzione ritardata (no lookahead), stop e take profit sulla barra di
ingresso, trailing senza lookahead, applicazione dei costi, e per il
portafoglio: ranking momentum senza lookahead e decadimento dei segnali
pendenti bloccati.
Esecuzione: python3 backtest/test_engine.py
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from engine import FEE_PCT, SLIPPAGE_PCT, StrategySignals, run_backtest  # noqa: E402
from portfolio import ApexParams, run_portfolio  # noqa: E402

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
    """Il check di oggi deve usare il trailing calcolato fino a IERI.

    Ingresso a barra 2 (open 100). Barra 2: close 120 -> trail 116.
    Barra 3 (discriminante): low 117 resta sopra il trail di ieri (116)
    ma sotto quello che userebbe il close odierno (121.5 - 4 = 117.5):
    NESSUNA uscita. Barra 4: low 108 buca il trail 117.5 aggiornato a
    fine barra 3 -> stop a 117.5.
    """
    df = make_df([100, 100, 100, 120, 118],
                 [100, 100, 121, 122, 118],
                 [100, 100, 99, 117, 108],
                 [100, 100, 120, 121.5, 110])
    # ATR costante artificiale: serie fornita a mano (trail = close - 4)
    a = pd.Series(2.0, index=df.index)
    s = sig(df, entry_idx=[1], trail_atr_mult=2.0)
    s.atr_series = a
    res = run_backtest(df, s, "T", "t")
    assert len(res.trades) == 1, res.trades
    t = res.trades[0]
    # un motore con lookahead uscirebbe gia' a barra 3 (117 <= 117.5)
    assert t.reason == "stop" and t.exit_date == df.index[4], (t.reason, t.exit_date)
    assert abs(t.exit_px - 117.5 * (1 - COST)) < 1e-9, t.exit_px
    print("ok  trailing_no_lookahead")


def test_take_profit_fill():
    """Il TP deve riempirsi quando l'high lo tocca dopo l'ingresso."""
    df = make_df([100, 100, 100, 100, 100],
                 [100, 100, 100, 108, 100],
                 [100, 100, 100, 100, 100],
                 [100, 100, 100, 104, 100])
    res = run_backtest(df, sig(df, entry_idx=[1], tp_pct=5.0), "T", "t")
    t = res.trades[0]
    tp = 100 * (1 + COST) * 1.05
    assert t.reason == "take_profit" and t.exit_date == df.index[3], (t.reason, t.exit_date)
    assert abs(t.exit_px - tp * (1 - COST)) < 1e-9, t.exit_px
    print("ok  take_profit_fill")


def test_take_profit_on_entry_bar():
    """TP toccato nel giorno stesso dell'ingresso: il fill deve avvenire
    (simmetrico allo stop); se la barra tocca entrambi vince lo stop."""
    df = make_df([100, 100, 100, 100],
                 [100, 100, 110, 100],
                 [100, 100, 99, 100],
                 [100, 100, 103, 100])
    res = run_backtest(df, sig(df, entry_idx=[1], tp_pct=5.0), "T", "t")
    t = res.trades[0]
    tp = 100 * (1 + COST) * 1.05
    assert t.reason == "take_profit" and t.exit_date == df.index[2], (t.reason, t.exit_date)
    assert abs(t.exit_px - tp * (1 - COST)) < 1e-9, t.exit_px
    # barra di ingresso che tocca sia stop sia TP: priorita' conservativa
    df2 = make_df([100, 100, 100, 100],
                  [100, 100, 110, 100],
                  [100, 100, 94, 100],
                  [100, 100, 103, 100])
    res2 = run_backtest(df2, sig(df2, entry_idx=[1], sl_pct=5.0, tp_pct=5.0), "T", "t")
    assert res2.trades[0].reason == "stop", res2.trades[0].reason
    print("ok  take_profit_on_entry_bar")


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


# ── Test del portafoglio (run_portfolio) ────────────────────────────────────

def make_trend_df(closes):
    """OHLC sintetico da una serie di chiusure: open = close di ieri."""
    closes = np.asarray(closes, dtype=float)
    opens = np.concatenate([[closes[0]], closes[:-1]])
    highs = np.maximum(opens, closes) * 1.001
    lows = np.minimum(opens, closes) * 0.999
    return make_df(opens, highs, lows, closes)


def test_portfolio_ranking_no_lookahead():
    """Cambiare il close di OGGI non deve cambiare gli ingressi di OGGI:
    il ranking momentum del top-k usa solo dati fino a ieri."""
    n, t_mod = 260, 230
    btc = 100 * 1.004 ** np.arange(n)      # momentum sempre maggiore
    alt = 100 * 1.003 ** np.arange(n)
    p = ApexParams(top_k=1, max_frac=0.30)
    res_a = run_portfolio({"BTCUSD": make_trend_df(btc),
                           "ALTUSD": make_trend_df(alt)}, p)
    alt_mod = alt.copy()
    alt_mod[t_mod] *= 1.5   # pompa il close di oggi: mom[oggi] di ALT > BTC
    res_b = run_portfolio({"BTCUSD": make_trend_df(btc),
                           "ALTUSD": make_trend_df(alt_mod)}, p)
    cutoff = make_trend_df(btc).index[t_mod]
    ent_a = {(t.side, t.entry_date) for t in res_a.trades if t.entry_date <= cutoff}
    ent_b = {(t.side, t.entry_date) for t in res_b.trades if t.entry_date <= cutoff}
    # con lookahead ALT scavalcherebbe BTC nel rank ed entrerebbe oggi stesso
    assert ent_a == ent_b, ent_a ^ ent_b
    print("ok  portfolio_ranking_no_lookahead")


def test_portfolio_pending_cleanup():
    """Un segnale bloccato (qui: dal cooldown) deve decadere, non restare
    in coda ed essere eseguito settimane dopo a condizioni non piu' vere."""
    n = 245
    t = np.arange(206)
    closes = np.empty(n)
    closes[:206] = 100 * 1.004 ** t              # uptrend: ingresso ~barra 200
    closes[206] = closes[205] * 0.55             # crollo -> stop in perdita
    closes[207:] = closes[206] * 0.999 ** np.arange(n - 207)  # sotto EMA200
    closes[218] = closes[:206].max() * 1.06      # breakout di UN solo giorno
    p = ApexParams(cooldown=15, trail_mult=8.0)
    res = run_portfolio({"BTCUSD": make_trend_df(closes)}, p)
    # il segnale della barra 218 e' bloccato dal cooldown alla barra 219:
    # non deve essere eseguito al suo scadere (entry ormai falsa da giorni)
    assert len(res.trades) == 1, [(t.entry_date, t.reason) for t in res.trades]
    assert res.trades[0].pnl_cash <= 0  # e' l'uscita in perdita che arma il cooldown
    print("ok  portfolio_pending_cleanup")


if __name__ == "__main__":
    test_no_lookahead_entry()
    test_stop_on_entry_bar()
    test_trailing_no_lookahead()
    test_take_profit_fill()
    test_take_profit_on_entry_bar()
    test_costs_applied_both_sides()
    test_risk_sizing_caps_loss()
    test_portfolio_ranking_no_lookahead()
    test_portfolio_pending_cleanup()
    print("\nTutti i test passati.")
