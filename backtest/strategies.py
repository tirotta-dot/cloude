"""Strategie: repliche dei bot Coinrule + candidate ottimizzate.

Ogni funzione riceve il DataFrame OHLCV giornaliero e restituisce
StrategySignals. La logica rispecchia 1:1 i file Pine Script del repo.
"""

import pandas as pd

from engine import StrategySignals, atr, bollinger, ema, rsi, sma


# ── Repliche Coinrule ───────────────────────────────────────────────────────

def bb_rsi_short(df: pd.DataFrame) -> StrategySignals:
    """Bollinger Bands and RSI Short Selling (mean reversion short)."""
    basis, upper, _ = bollinger(df["close"], 20, 2.0)
    r = rsi(df["close"], 14)
    entry = (df["close"] > upper) & (r > 70)
    exit_ = (df["close"] < basis) | (r < 50)
    return StrategySignals(entry=entry, exit=exit_, side="short", sl_pct=4.0)


def range_trading(df: pd.DataFrame) -> StrategySignals:
    """Solana Range Trading: compra banda inferiore, vendi banda superiore."""
    _, upper, lower = bollinger(df["close"], 20, 2.0)
    r = rsi(df["close"], 14)
    entry = (df["close"] < lower) & (r < 35)
    exit_ = df["close"] > upper
    return StrategySignals(entry=entry, exit=exit_, sl_pct=5.0)


def ma_crossing(df: pd.DataFrame) -> StrategySignals:
    """Maximized Moving Average Crossing: EMA 9/21."""
    fast, slow = ema(df["close"], 9), ema(df["close"], 21)
    cross_up = (fast > slow) & (fast.shift(1) <= slow.shift(1))
    cross_dn = (fast < slow) & (fast.shift(1) >= slow.shift(1))
    return StrategySignals(entry=cross_up, exit=cross_dn, sl_pct=6.0)


def scalp_on_trend(df: pd.DataFrame) -> StrategySignals:
    """Maximized Scalping On Trend: pullback RSI in uptrend, TP/SL stretti."""
    fast, slow = ema(df["close"], 20), ema(df["close"], 50)
    r = rsi(df["close"], 14)
    entry = (fast > slow) & (df["close"] > slow) & (r < 45)
    exit_ = pd.Series(False, index=df.index)
    return StrategySignals(entry=entry, exit=exit_, tp_pct=2.0, sl_pct=1.5)


def buy_sl_tp(df: pd.DataFrame) -> StrategySignals:
    """Buy + Stop Loss And Take Profit: cross sopra EMA20, TP 6% / SL 3%."""
    e = ema(df["close"], 20)
    entry = (df["close"] > e) & (df["close"].shift(1) <= e.shift(1))
    exit_ = pd.Series(False, index=df.index)
    return StrategySignals(entry=entry, exit=exit_, tp_pct=6.0, sl_pct=3.0)


def flash_crash(df: pd.DataFrame) -> StrategySignals:
    """Buy The Uptrend Flash Crash: -8% in 3 barre vicino al trend rialzista."""
    e = ema(df["close"], 100)
    drop = (df["close"].shift(3) - df["close"]) / df["close"].shift(3) * 100
    entry = (drop >= 8.0) & (df["close"] > e * 0.95)
    exit_ = pd.Series(False, index=df.index)
    return StrategySignals(entry=entry, exit=exit_, tp_pct=6.0, sl_pct=5.0)


def rebalance_trend(df: pd.DataFrame) -> StrategySignals:
    """Rebalance Trend Following: investito sopra SMA200 con SMA50>SMA200."""
    mid, long_ = sma(df["close"], 50), sma(df["close"], 200)
    entry = (df["close"] > long_) & (mid > long_)
    exit_ = df["close"] < mid
    return StrategySignals(entry=entry, exit=exit_)


# ── Candidate ottimizzate (long-only, daily) ────────────────────────────────

def trend_pullback(df: pd.DataFrame, rsi_buy=45, rsi_sell=70,
                   trail_mult=3.5, sl_pct=10.0) -> StrategySignals:
    """Compra il pullback dentro un uptrend strutturale.

    Filtro di regime: close > EMA200. Entrata: RSI(14) sotto soglia
    (sconto temporaneo). Uscita: RSI ipercomprato, rottura del regime,
    trailing stop ATR o stop fisso di emergenza.
    """
    e200 = ema(df["close"], 200)
    r = rsi(df["close"], 14)
    a = atr(df, 14)
    entry = (df["close"] > e200) & (r < rsi_buy)
    exit_ = (r > rsi_sell) | (df["close"] < e200)
    return StrategySignals(entry=entry, exit=exit_, sl_pct=sl_pct,
                           trail_atr_mult=trail_mult, atr_series=a)


def donchian_trend(df: pd.DataFrame, ch_len=20, trail_mult=4.0) -> StrategySignals:
    """Breakout Donchian con filtro EMA200 e trailing ATR."""
    e200 = ema(df["close"], 200)
    hi = df["close"].rolling(ch_len).max().shift(1)
    a = atr(df, 14)
    entry = (df["close"] > hi) & (df["close"] > e200)
    exit_ = df["close"] < ema(df["close"], 20)
    return StrategySignals(entry=entry, exit=exit_, trail_atr_mult=trail_mult,
                           atr_series=a, sl_pct=12.0)


def apex(df: pd.DataFrame, ch_len=30, trail_mult=4.0, exit_len=20,
         sl_pct=12.0, risk_pct=10.0) -> StrategySignals:
    """APEX Trend: breakout Donchian in regime rialzista + sizing a rischio.

    Configurazione finale scelta dallo sweep (backtest/tune.py) perche'
    su un plateau robusto, non un picco isolato:
      - Regime: close > EMA200 (si opera solo in uptrend strutturale)
      - Entrata: chiusura sopra il massimo di chiusura dei 30 gg precedenti
      - Uscite: chiusura sotto EMA20, trailing 4xATR(14), stop fisso 12%
      - Sizing: si investe solo la frazione di equity per cui lo stop
        trailing costa ~10%% dell'equity (riduce molto il drawdown)
    """
    e200 = ema(df["close"], 200)
    a = atr(df, 14)
    hi = df["close"].rolling(ch_len).max().shift(1)
    entry = (df["close"] > hi) & (df["close"] > e200)
    exit_ = df["close"] < ema(df["close"], exit_len)
    return StrategySignals(entry=entry, exit=exit_, sl_pct=sl_pct,
                           trail_atr_mult=trail_mult, atr_series=a,
                           risk_pct=risk_pct)


COINRULE = {
    "BB+RSI Short": bb_rsi_short,
    "Range Trading": range_trading,
    "MA Crossing": ma_crossing,
    "Scalping On Trend": scalp_on_trend,
    "Buy + SL/TP": buy_sl_tp,
    "Flash Crash": flash_crash,
    "Rebalance Trend": rebalance_trend,
}

CANDIDATES = {
    "Trend Pullback": trend_pullback,
    "Donchian Trend": donchian_trend,
    "APEX Trend (finale)": apex,
}
