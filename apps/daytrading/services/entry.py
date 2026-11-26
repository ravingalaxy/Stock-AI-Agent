"""Skill 3: Trader Entry — Explainable intraday entry signals.

Configurable strategies: ORB, VWAP Bounce, Momentum, Breakout, Bull Flag.
Deterministic signal generation (no LLM for signals).
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List

import pandas as pd

from apps.daytrading.models import DayTradePlan
from .market_data import get_intraday_candles, get_quote, normalize_symbol
from .market_calendar import is_market_open, now_ist, minutes_to_close
from .indicators import (
    calculate_intraday_indicators, calculate_opening_range,
    detect_intraday_setups, calculate_support_resistance,
)

logger = logging.getLogger(__name__)


def generate_entry_signal(symbol, exchange="NSE", strategy="ORB"):
    """Generate an intraday entry signal for a symbol.

    Returns a dict with entry recommendation or None if no signal.
    """
    sym = normalize_symbol(symbol, exchange)

    # Fetch intraday data
    df = get_intraday_candles(symbol, interval="5m", period="1d", exchange=exchange)
    if df is None or len(df) < 5:
        return {"signal": False, "reason": "Insufficient intraday data"}

    df = calculate_intraday_indicators(df)
    or_data = calculate_opening_range(df, minutes=15)
    latest = df.iloc[-1]
    setups = detect_intraday_setups(df, or_data)
    sr = calculate_support_resistance(df)

    if not setups:
        return {"signal": False, "reason": "No actionable setup detected", "symbol": sym}

    # Pick best setup matching requested strategy
    matched = None
    for s in setups:
        if strategy == "ORB" and s["type"].startswith("ORB"):
            matched = s
            break
        elif strategy == "VWAP_BOUNCE" and s["type"] == "VWAP_BOUNCE_LONG":
            matched = s
            break
        elif strategy == "MOMENTUM" and s["type"] == "MOMENTUM_BURST":
            matched = s
            break
        elif strategy == "BREAKOUT" and s["type"] == "VOLUME_SPIKE":
            matched = s
            break

    if not matched:
        matched = setups[0]  # best available

    direction = "LONG" if "LONG" in matched["type"] or "BURST" in matched["type"] or "SPIKE" in matched["type"] else "SHORT"
    entry_price = float(latest["Close"])

    # Calculate stop-loss and targets
    atr = float(latest.get("ATR_5", 0)) if pd.notna(latest.get("ATR_5")) else entry_price * 0.01
    if direction == "LONG":
        stop_loss = entry_price - (1.5 * atr)
        target_1 = entry_price + (2 * atr)
        target_2 = entry_price + (3 * atr)
    else:
        stop_loss = entry_price + (1.5 * atr)
        target_1 = entry_price - (2 * atr)
        target_2 = entry_price - (3 * atr)

    risk = abs(entry_price - stop_loss)
    reward = abs(target_1 - entry_price)
    rr = reward / risk if risk > 0 else 0

    return {
        "signal": True,
        "symbol": sym,
        "clean_symbol": symbol.replace(".NS", "").replace(".BO", ""),
        "exchange": exchange,
        "direction": direction,
        "strategy": matched["type"],
        "entry_price": round(entry_price, 2),
        "stop_loss": round(stop_loss, 2),
        "target_1": round(target_1, 2),
        "target_2": round(target_2, 2),
        "risk_reward": round(rr, 2),
        "atr": round(atr, 2),
        "strength": matched["strength"],
        "description": matched["description"],
        "vwap": round(float(latest.get("VWAP", 0)), 2) if pd.notna(latest.get("VWAP")) else None,
        "rsi": round(float(latest.get("RSI_9", 0)), 1) if pd.notna(latest.get("RSI_9")) else None,
        "support_resistance": sr,
        "or_data": or_data,
        "minutes_to_close": minutes_to_close(),
        "market_open": is_market_open(),
        "all_setups": setups,
    }


def create_trade_plan(signal_data):
    """Create a DayTradePlan from an entry signal."""
    if not signal_data or not signal_data.get("signal"):
        return None

    plan = DayTradePlan.objects.create(
        symbol=signal_data["symbol"],
        exchange=signal_data.get("exchange", "NSE"),
        strategy=signal_data.get("strategy", "ORB")[:20],
        direction=signal_data["direction"],
        status="PENDING",
        entry_price=Decimal(str(signal_data["entry_price"])),
        entry_trigger=signal_data.get("description", ""),
        stop_loss=Decimal(str(signal_data["stop_loss"])),
        target_1=Decimal(str(signal_data["target_1"])),
        target_2=Decimal(str(signal_data.get("target_2", signal_data["target_1"]))),
        risk_reward_ratio=Decimal(str(signal_data.get("risk_reward", 0))),
        scanner_score=signal_data.get("score"),
        rationale=signal_data.get("description", ""),
        indicators_snapshot={
            "vwap": signal_data.get("vwap"),
            "rsi": signal_data.get("rsi"),
            "atr": signal_data.get("atr"),
            "or_data": signal_data.get("or_data"),
        },
    )
    return plan


def get_active_plans(symbol=None):
    """Get active trade plans."""
    qs = DayTradePlan.objects.filter(status__in=["PENDING", "ACTIVE"])
    if symbol:
        qs = qs.filter(symbol__icontains=symbol)
    return list(qs.values())
