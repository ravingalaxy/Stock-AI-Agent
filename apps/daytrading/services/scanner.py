"""Skill 1: Trader Scanner — NSE/BSE stock screening.

Screens for momentum, volume spikes, breakouts, volatility.
Uses deterministic scoring (no LLM).
"""

import logging
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

from apps.market.models import Stock
from apps.daytrading.models import ScanResult
from .market_data import get_quote, get_intraday_candles, get_daily_history, normalize_symbol
from .market_calendar import is_market_open, now_ist, is_trading_day
from .indicators import calculate_intraday_indicators, calculate_opening_range

logger = logging.getLogger(__name__)

DEFAULT_SCAN_UNIVERSE = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK",
    "LT", "AXISBANK", "BAJFINANCE", "MARUTI", "TITAN",
    "SUNPHARMA", "TATAMOTORS", "NTPC", "POWERGRID", "M&M",
    "ASIANPAINT", "ULTRACEMCO", "WIPRO", "NESTLEIND", "HCLTECH",
    "ADANIENT", "ADANIPORTS", "JSWSTEEL", "TATASTEEL", "ONGC",
    "COALINDIA", "BPCL", "GRASIM", "TECHM", "DRREDDY",
    "CIPLA", "HEROMOTOCO", "APOLLOHOSP", "EICHERMOT", "DIVISLAB",
    "TATACONSUM", "BAJAJFINSV", "INDUSINDBK", "BRITANNIA", "SBILIFE",
    "HINDALCO", "HDFCLIFE", "UPL", "LTIM", "SHRIRAMFIN",
]


def scan_momentum(universe=None, exchange="NSE"):
    """Scan for momentum stocks — high relative volume + price movement."""
    universe = universe or DEFAULT_SCAN_UNIVERSE
    results = []
    for sym in universe:
        try:
            df = get_intraday_candles(sym, interval="5m", period="5d", exchange=exchange)
            if df is None or len(df) < 20:
                continue
            df = calculate_intraday_indicators(df)
            latest = df.iloc[-1]
            score = 0.0

            avg_vol = df["Volume"].rolling(20).mean().iloc[-1]
            vol_ratio = latest["Volume"] / avg_vol if avg_vol > 0 else 0
            score += min(30, vol_ratio * 10)

            day_open = df.iloc[0]["Open"]
            change_pct = (latest["Close"] - day_open) / day_open * 100 if day_open > 0 else 0
            score += min(25, abs(change_pct) * 5)

            rsi = latest.get("RSI_9", 50)
            if pd.notna(rsi) and 55 < rsi < 75:
                score += 20
            elif pd.notna(rsi) and 40 < rsi < 55:
                score += 10

            if pd.notna(latest.get("VWAP")) and latest["Close"] > latest["VWAP"]:
                score += 15

            if pd.notna(latest.get("EMA_9")) and pd.notna(latest.get("EMA_20")):
                if latest["EMA_9"] > latest["EMA_20"]:
                    score += 10

            if score >= 30:
                results.append({
                    "symbol": normalize_symbol(sym, exchange), "clean_symbol": sym,
                    "scan_type": "MOMENTUM", "score": round(score, 1),
                    "price": float(latest["Close"]), "volume": int(latest["Volume"]),
                    "volume_ratio": round(vol_ratio, 2),
                    "change_pct": round(change_pct, 2),
                    "rsi": round(float(rsi), 1) if pd.notna(rsi) else None,
                })
        except Exception as e:
            logger.warning(f"Scan failed for {sym}: {e}")
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def scan_breakouts(universe=None, exchange="NSE"):
    """Scan for breakout setups."""
    universe = universe or DEFAULT_SCAN_UNIVERSE
    results = []
    for sym in universe:
        try:
            df = get_daily_history(sym, period="3mo", exchange=exchange)
            if df is None or len(df) < 20:
                continue
            latest = df.iloc[-1]
            high_20d = df["High"].tail(20).max()
            avg_vol = df["Volume"].tail(20).mean()
            score = 0.0

            if latest["Close"] >= high_20d * 0.98:
                score += 40
            if latest["Volume"] > avg_vol * 1.5:
                score += 25

            range_20d = df["High"].tail(20).max() - df["Low"].tail(20).min()
            range_10d = df["High"].tail(10).max() - df["Low"].tail(10).min()
            if range_20d > 0 and range_10d / range_20d < 0.5:
                score += 20

            delta = df["Close"].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean().iloc[-1]
            loss_val = (-delta.where(delta < 0, 0)).rolling(14).mean().iloc[-1]
            rsi = 100 - (100 / (1 + gain / loss_val)) if loss_val > 0 else 50
            if 50 < rsi < 70:
                score += 15

            if score >= 40:
                results.append({
                    "symbol": normalize_symbol(sym, exchange), "clean_symbol": sym,
                    "scan_type": "BREAKOUT", "score": round(score, 1),
                    "price": float(latest["Close"]), "volume": int(latest["Volume"]),
                    "volume_ratio": round(latest["Volume"] / avg_vol, 2) if avg_vol > 0 else 0,
                    "change_pct": round((latest["Close"] - df["Close"].iloc[-2]) / df["Close"].iloc[-2] * 100, 2),
                    "rsi": round(rsi, 1),
                })
        except Exception as e:
            logger.warning(f"Breakout scan failed for {sym}: {e}")
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def scan_volume_spikes(universe=None, exchange="NSE"):
    """Scan for unusual volume activity."""
    universe = universe or DEFAULT_SCAN_UNIVERSE
    results = []
    for sym in universe:
        try:
            df = get_daily_history(sym, period="2mo", exchange=exchange)
            if df is None or len(df) < 20:
                continue
            latest = df.iloc[-1]
            avg_vol = df["Volume"].tail(20).mean()
            vol_ratio = latest["Volume"] / avg_vol if avg_vol > 0 else 0
            if vol_ratio >= 2.0:
                change_pct = (latest["Close"] - df["Close"].iloc[-2]) / df["Close"].iloc[-2] * 100
                score = min(100, vol_ratio * 15 + abs(change_pct) * 5)
                results.append({
                    "symbol": normalize_symbol(sym, exchange), "clean_symbol": sym,
                    "scan_type": "VOLUME_SPIKE", "score": round(score, 1),
                    "price": float(latest["Close"]), "volume": int(latest["Volume"]),
                    "volume_ratio": round(vol_ratio, 2), "change_pct": round(change_pct, 2),
                })
        except Exception as e:
            logger.warning(f"Volume scan failed for {sym}: {e}")
    results.sort(key=lambda x: x.get("volume_ratio", 0), reverse=True)
    return results


def run_full_scan(universe=None, exchange="NSE"):
    """Run all scanners and persist results."""
    results = {
        "momentum": scan_momentum(universe, exchange),
        "breakouts": scan_breakouts(universe, exchange),
        "volume_spikes": scan_volume_spikes(universe, exchange),
        "timestamp": now_ist().isoformat(),
        "market_open": is_market_open(),
    }
    for scan_type, hits in results.items():
        if scan_type in ("timestamp", "market_open"):
            continue
        for hit in hits[:20]:
            try:
                ScanResult.objects.update_or_create(
                    symbol=hit["symbol"], scan_type=hit["scan_type"],
                    scanned_at__date=now_ist().date(),
                    defaults={
                        "score": hit["score"], "price": hit.get("price"),
                        "volume": hit.get("volume"), "volume_ratio": hit.get("volume_ratio"),
                        "change_pct": hit.get("change_pct"), "rsi": hit.get("rsi"),
                        "details": hit.get("details", {}), "scanned_at": now_ist(),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to persist scan result: {e}")
    return results
