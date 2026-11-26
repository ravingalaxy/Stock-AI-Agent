"""Technical indicator engine for intraday trading.

Extends existing src.analysis.indicators with intraday-specific: VWAP, Opening Range,
pre-market levels, intraday momentum.
Uses deterministic Python/pandas only — no LLM.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

from src.utils.helpers import safe_divide


def calculate_vwap(df):
    """Calculate Volume-Weighted Average Price."""
    if df is None or df.empty or "Volume" not in df.columns:
        return pd.Series(dtype=float)
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    cum_tp_vol = (typical_price * df["Volume"]).cumsum()
    cum_vol = df["Volume"].cumsum()
    return cum_tp_vol / cum_vol.replace(0, np.nan)


def calculate_opening_range(df, minutes=15):
    """Calculate Opening Range (first N minutes). NSE opens at 09:15 IST."""
    if df is None or df.empty:
        return None
    first_ts = df.index[0]
    cutoff = first_ts + pd.Timedelta(minutes=minutes)
    or_data = df[df.index < cutoff]
    if or_data.empty:
        return None
    or_high = float(or_data["High"].max())
    or_low = float(or_data["Low"].min())
    or_mid = (or_high + or_low) / 2
    or_range = or_high - or_low
    return {
        "or_high": or_high, "or_low": or_low, "or_mid": or_mid,
        "or_range": or_range,
        "or_range_pct": safe_divide(or_range, or_mid) * 100 if or_mid else 0,
        "minutes": minutes,
    }


def calculate_intraday_indicators(df):
    """Add intraday-specific indicators to candle DataFrame."""
    if df is None or df.empty:
        return df
    df = df.copy()
    df["VWAP"] = calculate_vwap(df)

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(9).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(9).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI_9"] = 100 - (100 / (1 + rs))

    df["EMA_9"] = df["Close"].ewm(span=9).mean()
    df["EMA_20"] = df["Close"].ewm(span=20).mean()

    tr = pd.DataFrame({
        "hl": df["High"] - df["Low"],
        "hc": abs(df["High"] - df["Close"].shift(1)),
        "lc": abs(df["Low"] - df["Close"].shift(1)),
    }).max(axis=1)
    df["ATR_5"] = tr.rolling(5).mean()
    df["Cum_Volume"] = df["Volume"].cumsum()
    df["Price_vs_VWAP"] = df["Close"] - df["VWAP"]
    return df


def detect_intraday_setups(df, or_data=None):
    """Detect intraday trading setups."""
    setups = []
    if df is None or len(df) < 10:
        return setups
    latest = df.iloc[-1]

    if or_data:
        if latest["Close"] > or_data["or_high"]:
            setups.append({
                "type": "ORB_BREAKOUT_LONG",
                "description": f"Price broke above Opening Range High {or_data['or_high']:.2f}",
                "strength": "STRONG" if latest["Volume"] > df["Volume"].mean() * 1.5 else "MODERATE",
            })
        elif latest["Close"] < or_data["or_low"]:
            setups.append({
                "type": "ORB_BREAKOUT_SHORT",
                "description": f"Price broke below Opening Range Low {or_data['or_low']:.2f}",
                "strength": "STRONG" if latest["Volume"] > df["Volume"].mean() * 1.5 else "MODERATE",
            })

    if "VWAP" in df.columns and pd.notna(latest.get("VWAP")):
        vwap = latest["VWAP"]
        if abs(latest["Close"] - vwap) / vwap < 0.002 and latest["Close"] > vwap:
            setups.append({"type": "VWAP_BOUNCE_LONG", "description": f"Price bouncing off VWAP {vwap:.2f}", "strength": "MODERATE"})

    if len(df) >= 4:
        last3 = df.iloc[-3:]
        if all(last3["Close"] > last3["Open"]) and all(last3["Volume"].diff().dropna() > 0):
            setups.append({"type": "MOMENTUM_BURST", "description": "3 consecutive up candles with increasing volume", "strength": "STRONG"})

    if "Volume" in df.columns:
        avg_vol = df["Volume"].rolling(20).mean().iloc[-1] if len(df) >= 20 else df["Volume"].mean()
        if latest["Volume"] > avg_vol * 3:
            setups.append({"type": "VOLUME_SPIKE", "description": f"Volume {latest['Volume']/avg_vol:.1f}x average", "strength": "STRONG"})

    return setups


def calculate_support_resistance(df, num_levels=3):
    """Calculate support/resistance levels from pivot points."""
    if df is None or len(df) < 5:
        return {"support": [], "resistance": []}
    latest = df.iloc[-1]
    h, l, c = float(latest["High"]), float(latest["Low"]), float(latest["Close"])
    pivot = (h + l + c) / 3
    return {
        "pivot": round(pivot, 2),
        "resistance": [round(2 * pivot - l, 2), round(pivot + (h - l), 2), round(h + 2 * (pivot - l), 2)],
        "support": [round(2 * pivot - h, 2), round(pivot - (h - l), 2), round(l - 2 * (h - pivot), 2)],
    }
