import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.utils.logger import logger


@dataclass
class TechnicalIndicatorsOld:
    """Classic technical indicators for stock analysis."""
    # Trend indicators
    trend_sma: str = "Neutral"
    trend_ema: str = "Neutral"
    trend_macd: str = "Neutral"
    trend_adx: str = "Neutral"

    # Momentum indicators
    rsi_14: float = 50.0
    rsi_14_trigger: str = "Neutral"
    momentum_20d: float = 0.0
    momentum_60d: float = 0.0
    momentum_252d: float = 0.0
    stoch_k: float = 50.0
    stoch_d: float = 50.0
    vol_price_ratio: float = 1.0

    # Volatility
    atr_14: float = 0.0
    bb_upper: float = 0.0
    bb_middle: float = 0.0
    bb_lower: float = 0.0
    bb_width: float = 0.0
    bb_position: float = 50.0

    # Volume analysis
    volume_avg_20: float = 0.0
    volume_ratio: float = 1.0
    obv: float = 0.0

    # Support/Resistance
    current_price: float = 0.0
    support_20: float = 0.0
    resistance_20: float = 0.0
    support_50: float = 0.0
    resistance_50: float = 0.0
    pivot_point: float = 0.0
    s1: float = 0.0
    r1: float = 0.0

    # Price action
    price_vs_sma20: str = "Neutral"
    price_vs_sma50: str = "Neutral"
    price_vs_sma200: str = "Neutral"
    candle_body_pct: float = 0.0
    upper_shadow_pct: float = 0.0
    lower_shadow_pct: float = 0.0


class AdvancedTechnicalAnalyzer:
    """Advanced technical analysis engine."""

    def __init__(self, df: pd.DataFrame):
        """
        Args:
            df: DataFrame with Open, High, Low, Close, Volume columns
        """
        self.df = df.copy()
        self.df['Close'] = pd.to_numeric(self.df['Close'], errors='coerce')
        self.df['Volume'] = pd.to_numeric(self.df['Volume'], errors='coerce')
        self.df.dropna(subset=['Close'], inplace=True)

    def calculate_all_advanced_indicators(self) -> TechnicalIndicatorsOld:
        """Calculate all advanced technical indicators."""
        indicators = TechnicalIndicatorsOld(
            current_price=self.df['Close'].iloc[-1],
            volume_avg_20=self.df['Volume'].rolling(20).mean().iloc[-1] if len(self.df) >= 20 else 0
        )

        # 1. RSI (14)
        indicators.rsi_14 = self._calculate_rsi(14)
        indicators.rsi_14_trigger = self._get_rsi_signal(indicators.rsi_14)

        # 2. MACD (12, 26, 9) with signals
        macd_line, signal_line, hist = self._calculate_macd()
        indicators.trend_macd = self._get_macd_signal(hist[-1])
        indicators.momentum_20d = indicators.rsi_14  # Simplified

        # 3. Bollinger Bands (20, 2)
        upper, middle, lower, width, position = self._calculate_bollinger_bands(20, 2)
        indicators.bb_upper = upper
        indicators.bb_middle = middle
        indicators.bb_lower = lower
        indicators.bb_width = width
        indicators.bb_position = position
        indicators.price_vs_sma20 = self._get_price_vs_ma_signal("SMA20", 20)
        indicators.price_vs_sma50 = self._get_price_vs_ma_signal("SMA50", 50)
        indicators.price_vs_sma200 = self._get_price_vs_ma_signal("SMA200", 200)

        # 4. Moving Averages
        indicators.trend_sma = self._calculate_sma_signal(50)
        indicators.trend_ema = self._calculate_ema_signal(200)

        # 5. Stochastic Oscillator (14, 3, 3)
        stoch_k, stoch_d = self._calculate_stochastic(14, 3, 3)
        indicators.stoch_k = stoch_k
        indicators.stoch_d = stoch_d

        # 6. Volume ratio
        indicators.volume_ratio = self.df['Volume'].iloc[-1] / indicators.volume_avg_20 if indicators.volume_avg_20 > 0 else 1.0

        # 7. ATR (14) for volatility
        indicators.atr_14 = self._calculate_atr(14)

        # 8. Pivot Points for Support/Resistance
        pivot_info = self._calculate_pivot_points()
        indicators.pivot_point, indicators.s1, indicators.r1 = pivot_info

        # 9. Volume analysis - OBV
        indicators.obv = self._calculate_obv()

        # 10. Candlestick pattern analysis
        candel_pattern = self._analyze_candlestick_pattern()
        indicators.trend_sma = candel_pattern

        return indicators

    def _calculate_rsi(self, period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        delta = self.df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if len(rsi) > 0 else 50.0

    def _get_rsi_signal(self, rsi: float) -> str:
        """Get RSI trading signal."""
        if rsi > 70:
            return "Overbought"
        elif rsi < 30:
            return "Oversold"
        elif 45 <= rsi <= 55:
            return "Neutral"
        else:
            return "Strength"

    def _calculate_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD and signal line."""
        ema_fast = self.df['Close'].ewm(span=fast).mean()
        ema_slow = self.df['Close'].ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), histogram.iloc[-1]

    def _get_macd_signal(self, hist_value: float) -> str:
        """Get MACD histogram signal."""
        if hist_value > 0:
            return "Bullish"
        elif hist_value < 0:
            return "Bearish"
        else:
            return "Neutral"

    def _calculate_bollinger_bands(self, period: int = 20, std_dev: float = 2) -> Tuple[float, float, float, float, float]:
        """Calculate Bollinger Bands."""
        sma = self.df['Close'].rolling(window=period).mean()
        std = self.df['Close'].rolling(window=period).std()
        upper = sma + (std * std_dev)
        middle = sma
        lower = sma - (std * std_dev)
        current_price = self.df['Close'].iloc[-1]
        width = ((upper - lower) / middle * 100) if middle > 0 else 0
        position = ((current_price - lower) / (upper - lower) * 100) if (upper - lower) > 0 else 50
        return float(upper.iloc[-1]), float(middle.iloc[-1]), float(lower.iloc[-1]), float(width), float(position)

    def _get_price_vs_ma_signal(self, ma_name: str, period: int) -> str:
        """Calculate signal based on current price relative to MA."""
        if len(self.df) < period:
            return "Neutral"
        sma = self.df['Close'].rolling(window=period).mean()
        current_price = self.df['Close'].iloc[-1]
        sma_val = sma.iloc[-1]
        if pd.isna(sma_val):
            return "Neutral"
        return "Above" if current_price >= sma_val else "Below"

    def _calculate_sma_signal(self, period: int) -> str:
        """Calculate SMA trend signal."""
        sma = self.df['Close'].rolling(window=period).mean()
        current_price = self.df['Close'].iloc[-1]
        sma_value = sma.iloc[-1]
        if period == 50:
            if current_price > sma_value:
                return "Bullish"
            else:
                return "Bearish"
        else:
            return "Neutral"

    def _calculate_ema_signal(self, period: int) -> str:
        """Calculate EMA trend signal."""
        ema = self.df['Close'].ewm(span=period, adjust=False).mean()
        current_price = self.df['Close'].iloc[-1]
        ema_value = ema.iloc[-1]
        if current_price > ema_value:
            return "Bullish"
        else:
            return "Bearish"

    def _calculate_stochastic(self, k_period: int = 14, d_period: int = 3, smooth: int = 3) -> Tuple[float, float]:
        """Calculate Stochastic Oscillator."""
        low_14 = self.df['Low'].rolling(window=k_period).min()
        high_14 = self.df['High'].rolling(window=k_period).max()

        k = ((self.df['Close'] - low_14) / (high_14 - low_14)) * 100
        d = k.rolling(window=d_period).mean()
        smoothed_k = d.rolling(window=smooth).mean()

        return float(smoothed_k.iloc[-1]), float(d.iloc[-1])

    def _calculate_atr(self, period: int = 14) -> float:
        """Average True Range."""
        high_low = self.df['High'] - self.df['Low']
        high_close = np.abs(self.df['High'] - self.df['Close'].shift())
        low_close = np.abs(self.df['Low'] - self.df['Close'].shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return float(atr.iloc[-1]) if len(atr) > 0 else 0.0

    def _calculate_pivot_points(self) -> Tuple[float, float, float]:
        """Calculate Pivot Points (R1, S1, Pivot)."""
        high = self.df['High'].iloc[-1]
        low = self.df['Low'].iloc[-1]
        close = self.df['Close'].iloc[-1]

        pivot = (high + low + close) / 3
        r1 = (pivot * 2) - low
        s1 = (pivot * 2) - high

        return float(pivot), float(s1), float(r1)

    def _calculate_obv(self) -> float:
        """On Balance Volume."""
        price_diff = self.df['Close'].diff()
        obv = (price_diff.where(price_diff > 0, 0).cumsum()).where(price_diff < 0, 0).sum()
        return obv

    def _analyze_candlestick_pattern(self) -> str:
        """Candlestick pattern analysis (simplified)."""
        # Simple Last 3 candles analysis
        last_candles = self.df.tail(3)
        current_candle = last_candles.iloc[-1]
        prev_candle = last_candles.iloc[-2]

        body_ratio = abs(current_candle['Close'] - current_candle['Open']) / current_candle['High']
        prev_body_ratio = abs(prev_candle['Close'] - prev_candle['Open']) / prev_candle['High']

        # If body ratio is small and current is above previous close -> Spinning Top
        if body_ratio < 0.3 and current_candle['Close'] > prev_candle['Close']:
            return "Bullish Disturbance"

        return "Neutral"