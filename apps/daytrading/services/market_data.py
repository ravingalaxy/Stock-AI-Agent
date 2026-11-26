"""Provider-independent Indian market data service.

Uses yfinance for NSE/BSE. Validates timestamps, handles missing candles.
Clearly labels real-time vs delayed vs historical data.
Never fabricates data.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import pandas as pd
import numpy as np
import yfinance as yf

from .market_calendar import IST, is_trading_day, is_market_open, now_ist

logger = logging.getLogger(__name__)

EXCHANGE_SUFFIX = {"NSE": ".NS", "BSE": ".BO"}


def normalize_symbol(symbol, exchange="NSE"):
    """Ensure symbol has correct exchange suffix."""
    symbol = symbol.strip().upper()
    suffix = EXCHANGE_SUFFIX.get(exchange, ".NS")
    if not symbol.endswith((".NS", ".BO")):
        symbol = symbol + suffix
    return symbol


def clean_symbol(symbol):
    """Remove exchange suffix for display."""
    return symbol.replace(".NS", "").replace(".BO", "")


def get_quote(symbol, exchange="NSE"):
    """Fetch current quote. Data may be 15-min delayed (yfinance free tier)."""
    sym = normalize_symbol(symbol, exchange)
    try:
        ticker = yf.Ticker(sym)
        hist = ticker.history(period="2d")
        if hist.empty:
            return None
        last = hist.iloc[-1]
        prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else last["Close"]
        change = last["Close"] - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        return {
            "symbol": sym, "clean_symbol": clean_symbol(sym), "exchange": exchange,
            "price": float(last["Close"]), "open": float(last["Open"]),
            "high": float(last["High"]), "low": float(last["Low"]),
            "close": float(last["Close"]), "volume": int(last["Volume"]),
            "prev_close": float(prev_close), "change": float(change),
            "change_pct": float(change_pct), "data_type": "DELAYED",
            "timestamp": datetime.now(IST).isoformat(),
        }
    except Exception as e:
        logger.error(f"Quote fetch failed for {sym}: {e}")
        return None


def get_intraday_candles(symbol, interval="5m", period="1d", exchange="NSE"):
    """Fetch intraday OHLCV candles."""
    sym = normalize_symbol(symbol, exchange)
    try:
        df = yf.download(sym, period=period, interval=interval, progress=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC").tz_convert(IST)
        else:
            df.index = df.index.tz_convert(IST)
        df = df[df["Volume"] > 0].copy()
        df = df[~df.index.duplicated(keep="first")]
        df = df.sort_index()
        return df
    except Exception as e:
        logger.error(f"Intraday fetch failed for {sym} {interval}: {e}")
        return None


def get_daily_history(symbol, period="1y", exchange="NSE"):
    """Fetch daily OHLCV history."""
    sym = normalize_symbol(symbol, exchange)
    try:
        df = yf.download(sym, period=period, interval="1d", progress=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df[~df.index.duplicated(keep="first")]
        df = df.sort_index()
        return df
    except Exception as e:
        logger.error(f"Daily history fetch failed for {sym}: {e}")
        return None


def get_multiple_quotes(symbols, exchange="NSE"):
    """Fetch quotes for multiple symbols."""
    results = []
    for sym in symbols:
        q = get_quote(sym, exchange)
        if q:
            results.append(q)
    return results


def get_index_data(index_symbol="^NSEI"):
    """Fetch Nifty / Sensex index data."""
    try:
        ticker = yf.Ticker(index_symbol)
        hist = ticker.history(period="2d")
        if hist.empty:
            return None
        last = hist.iloc[-1]
        prev = hist["Close"].iloc[-2] if len(hist) > 1 else last["Close"]
        change = last["Close"] - prev
        return {
            "symbol": index_symbol, "value": float(last["Close"]),
            "change": float(change),
            "change_pct": float(change / prev * 100) if prev else 0,
            "data_type": "DELAYED",
        }
    except Exception as e:
        logger.error(f"Index fetch failed for {index_symbol}: {e}")
        return None


def validate_candle_data(df):
    """Validate candle data quality."""
    if df is None or df.empty:
        return {"valid": False, "error": "No data"}
    issues = []
    if len(df) > 1:
        time_diffs = df.index.to_series().diff().dropna()
        median_diff = time_diffs.median()
        gaps = time_diffs[time_diffs > median_diff * 3]
        if len(gaps) > 0:
            issues.append(f"{len(gaps)} time gaps detected")
    for col in ["Open", "High", "Low", "Close"]:
        if col in df.columns and (df[col] <= 0).any():
            issues.append(f"Invalid {col} prices detected")
    return {
        "valid": len(issues) == 0, "rows": len(df),
        "date_range": f"{df.index[0]} to {df.index[-1]}", "issues": issues,
    }
