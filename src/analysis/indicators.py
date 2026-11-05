"""Technical Indicators Calculation Engine using pandas and ta library."""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import date, datetime

from src.utils.logger import logger
from src.utils.helpers import safe_divide


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate comprehensive technical indicators on price DataFrame.
    
    Args:
        df: DataFrame with columns ['Open', 'High', 'Low', 'Close', 'Volume'] and DatetimeIndex
        
    Returns:
        DataFrame with added indicator columns.
    """
    if df is None or df.empty or len(df) < 50:
        logger.warning("Insufficient data for indicator calculation")
        return df
        
    df = df.copy()
    
    # Ensure required columns
    required = ["Open", "High", "Low", "Close", "Volume"]
    for col in required:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return df
            
    # Moving Averages
    df["SMA_20"] = df["Close"].rolling(20).mean()
    df["SMA_50"] = df["Close"].rolling(50).mean()
    df["SMA_200"] = df["Close"].rolling(200).mean()
    df["EMA_12"] = df["Close"].ewm(span=12).mean()
    df["EMA_26"] = df["Close"].ewm(span=26).mean()
    df["EMA_50"] = df["Close"].ewm(span=50).mean()
    
    # RSI
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = safe_divide(gain, loss)
    df["RSI_14"] = 100 - (100 / (1 + rs))
    
    # MACD
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["MACD_Signal"] = df["MACD"].ewm(span=9).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]
    
    # Bollinger Bands
    df["BB_Middle"] = df["Close"].rolling(20).mean()
    bb_std = df["Close"].rolling(20).std()
    df["BB_Upper"] = df["BB_Middle"] + (2 * bb_std)
    df["BB_Lower"] = df["BB_Middle"] - (2 * bb_std)
    df["BB_Width"] = safe_divide(df["BB_Upper"] - df["BB_Lower"], df["BB_Middle"]) * 100
    df["BB_Position"] = safe_divide(df["Close"] - df["BB_Lower"], df["BB_Upper"] - df["BB_Lower"])
    
    # Average True Range (ATR)
    df["TR"] = np.maximum(
        df["High"] - df["Low"],
        np.maximum(
            abs(df["High"] - df["Close"].shift(1)),
            abs(df["Low"] - df["Close"].shift(1))
        )
    )
    df["ATR_14"] = df["TR"].rolling(14).mean()
    df["ATR_Pct"] = safe_divide(df["ATR_14"], df["Close"]) * 100
    
    # Volume Indicators
    df["Volume_SMA_20"] = df["Volume"].rolling(20).mean()
    df["Volume_Ratio"] = safe_divide(df["Volume"], df["Volume_SMA_20"])
    df["OBV"] = (np.sign(df["Close"].diff()) * df["Volume"]).fillna(0).cumsum()
    
    # 52-Week High/Low
    df["High_52W"] = df["High"].rolling(252).max()
    df["Low_52W"] = df["Low"].rolling(252).min()
    df["Dist_From_52W_High"] = safe_divide(df["High_52W"] - df["Close"], df["High_52W"]) * 100
    df["Dist_From_52W_Low"] = safe_divide(df["Close"] - df["Low_52W"], df["Low_52W"]) * 100
    df["Position_In_52W_Range"] = safe_divide(df["Close"] - df["Low_52W"], df["High_52W"] - df["Low_52W"]) * 100
    
    # Volatility
    df["Daily_Return"] = df["Close"].pct_change()
    df["Volatility_20"] = df["Daily_Return"].rolling(20).std() * np.sqrt(252) * 100  # Annualized %
    df["Volatility_60"] = df["Daily_Return"].rolling(60).std() * np.sqrt(252) * 100
    
    # Drawdown
    df["Rolling_Max"] = df["Close"].cummax()
    df["Drawdown"] = safe_divide(df["Close"] - df["Rolling_Max"], df["Rolling_Max"]) * 100
    df["Max_Drawdown_252"] = df["Drawdown"].rolling(252).min()
    
    # Relative Strength vs Benchmark (would need benchmark data passed in)
    # Placeholder - calculated in technical agent with benchmark
    
    return df


def get_latest_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Extract latest indicator values from DataFrame."""
    if df is None or df.empty:
        return {}
        
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    indicators = {}
    indicator_cols = [
        "SMA_20", "SMA_50", "SMA_200", "EMA_12", "EMA_26", "EMA_50",
        "RSI_14", "MACD", "MACD_Signal", "MACD_Hist",
        "BB_Upper", "BB_Middle", "BB_Lower", "BB_Width", "BB_Position",
        "ATR_14", "ATR_Pct",
        "Volume_SMA_20", "Volume_Ratio", "OBV",
        "High_52W", "Low_52W", "Dist_From_52W_High", "Dist_From_52W_Low", "Position_In_52W_Range",
        "Volatility_20", "Volatility_60", "Drawdown", "Max_Drawdown_252"
    ]
    
    for col in indicator_cols:
        if col in df.columns:
            val = latest.get(col)
            indicators[col] = float(val) if pd.notna(val) else None
            
    # Trend Signals
    indicators["trend_sma"] = "Bullish" if indicators.get("SMA_50", 0) > indicators.get("SMA_200", 0) else "Bearish"
    indicators["price_vs_sma50"] = "Above" if latest["Close"] > indicators.get("SMA_50", 0) else "Below"
    indicators["price_vs_sma200"] = "Above" if latest["Close"] > indicators.get("SMA_200", 0) else "Below"
    indicators["macd_signal"] = "Bullish" if indicators.get("MACD_Hist", 0) > 0 else "Bearish"
    indicators["rsi_zone"] = "Overbought" if indicators.get("RSI_14", 50) > 70 else ("Oversold" if indicators.get("RSI_14", 50) < 30 else "Neutral")
    
    # Momentum
    if len(df) >= 20:
        indicators["momentum_20d"] = safe_divide(latest["Close"] - df["Close"].iloc[-21], df["Close"].iloc[-21]) * 100
    if len(df) >= 60:
        indicators["momentum_60d"] = safe_divide(latest["Close"] - df["Close"].iloc[-61], df["Close"].iloc[-61]) * 100
    if len(df) >= 252:
        indicators["momentum_252d"] = safe_divide(latest["Close"] - df["Close"].iloc[-253], df["Close"].iloc[-253]) * 100
        
    return indicators


def calculate_relative_strength(stock_df: pd.DataFrame, benchmark_df: pd.DataFrame) -> Dict[str, float]:
    """Calculate relative strength vs benchmark (e.g., Nifty 50)."""
    if stock_df is None or benchmark_df is None:
        return {}
        
    # Align dates
    common_dates = stock_df.index.intersection(benchmark_df.index)
    if len(common_dates) < 20:
        return {}
        
    stock_aligned = stock_df.loc[common_dates]["Close"]
    bench_aligned = benchmark_df.loc[common_dates]["Close"]
    
    # Calculate relative strength (RS) = Stock Performance / Benchmark Performance
    periods = [20, 60, 120, 252]
    rs = {}
    
    for p in periods:
        if len(stock_aligned) >= p + 1:
            stock_ret = safe_divide(stock_aligned.iloc[-1] - stock_aligned.iloc[-p-1], stock_aligned.iloc[-p-1])
            bench_ret = safe_divide(bench_aligned.iloc[-1] - bench_aligned.iloc[-p-1], bench_aligned.iloc[-p-1])
            if bench_ret != 0:
                rs[f"RS_{p}d"] = (1 + stock_ret) / (1 + bench_ret) - 1
                
    return rs


def detect_chart_patterns(df: pd.DataFrame) -> List[str]:
    """Detect basic chart patterns (simplified)."""
    patterns = []
    if df is None or len(df) < 50:
        return patterns
        
    latest = df.iloc[-1]
    
    # Golden Cross / Death Cross
    if "SMA_50" in df.columns and "SMA_200" in df.columns:
        sma50_prev = df["SMA_50"].iloc[-2]
        sma200_prev = df["SMA_200"].iloc[-2]
        sma50_curr = latest["SMA_50"]
        sma200_curr = latest["SMA_200"]
        
        if pd.notna(sma50_prev) and pd.notna(sma200_prev):
            if sma50_prev <= sma200_prev and sma50_curr > sma200_curr:
                patterns.append("Golden Cross (SMA50 crossed above SMA200)")
            elif sma50_prev >= sma200_prev and sma50_curr < sma200_curr:
                patterns.append("Death Cross (SMA50 crossed below SMA200)")
                
    # Breakout patterns
    if "High_52W" in df.columns:
        if latest["Close"] > latest["High_52W"] * 0.98:
            patterns.append("Near 52-Week High")
        if latest["Close"] < latest["Low_52W"] * 1.02:
            patterns.append("Near 52-Week Low")
            
    # Volume spike
    if "Volume_Ratio" in df.columns and latest["Volume_Ratio"] > 2:
        patterns.append("High Volume Spike (>2x Average)")
        
    # Bollinger Band squeeze
    if "BB_Width" in df.columns:
        bb_width_avg = df["BB_Width"].rolling(20).mean().iloc[-1]
        if pd.notna(bb_width_avg) and latest["BB_Width"] < bb_width_avg * 0.5:
            patterns.append("Bollinger Band Squeeze (Low Volatility)")
            
    return patterns