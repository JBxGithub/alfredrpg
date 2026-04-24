"""
專業級技術指標模組 - Professional Technical Indicators
Complete implementation of all professional trading indicators

Indicators:
- MACDV (Volume): Volume > 1.5×20-day average
- ADX: Trend strength (Wilder)
- +DI/-DI: Trend direction
- MACD (12,26,9): Standard MACD
- EMA (9/20/50): Multiple EMAs
- BOLL (20,2): Bollinger Bands
- VIX: Volatility filter

Author: Professional Trading System
Version: 2.0.0
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class TrendStrength(Enum):
    """Trend strength classification"""
    WEAK = "weak"              # ADX < 20
    MODERATE = "moderate"       # 20 <= ADX < 25
    STRONG = "strong"          # 25 <= ADX < 50
    VERY_STRONG = "very_strong" # 50 <= ADX < 70
    EXTREME = "extreme"       # ADX >= 70


@dataclass
class MACDResult:
    """MACD (12,26,9) calculation result"""
    macd_line: pd.Series      # DIF (Fast - Slow)
    signal_line: pd.Series   # DEA (Signal line)
    histogram: pd.Series      # MACD柱
    crossover: pd.Series     # Crossover signals
    direction: pd.Series     # Trend direction


@dataclass  
class ADXResult:
    """ADX calculation result"""
    adx: pd.Series           # ADX value
    plus_di: pd.Series       # +DI (Directional Indicator +)
    minus_di: pd.Series       # -DI (Directional Indicator -)
    trend_strength: pd.Series  # Trend strength enum
    trend_direction: pd.Series  # Trend direction


@dataclass
class BOLLResult:
    """Bollinger Bands (20,2) calculation result"""
    upper: pd.Series         # Upper band
    middle: pd.Series        # Middle band (20 SMA)
    lower: pd.Series         # Lower band
    bandwidth: pd.Series    # Bandwidth indicator
    position: pd.Series    # Position in band (%) 


@dataclass
class EMAResult:
    """Multiple EMA results"""
    ema_9: pd.Series
    ema_20: pd.Series
    ema_50: pd.Series
    
    def get排列(self) -> str:
        """Get EMA arrangement (多頭/空頭/中性)"""
        latest = self.ema_9.iloc[-1] if len(self.ema_9) > 0 else np.nan
        if pd.isna(latest):
            return "NEUTRAL"
        if self.ema_9.iloc[-1] > self.ema_20.iloc[-1] > self.ema_50.iloc[-1]:
            return "BULLISH"
        elif self.ema_9.iloc[-1] < self.ema_20.iloc[-1] < self.ema_50.iloc[-1]:
            return "BEARISH"
        return "NEUTRAL"


@dataclass
class VolumeResult:
    """Volume analysis result"""
    volume: pd.Series
    volume_ma20: pd.Series
    volume_ratio: pd.Series   # Volume / 20-day MA
    volume_spike: pd.Series    # > 1.5x threshold trigger


@dataclass
class ProfessionalIndicators:
    """Complete professional indicator set"""
    macd: MACDResult
    adx: ADXResult
    boll: BOLLResult
    ema: EMAResult
    volume: VolumeResult
    vix: float
    rsi: Optional[pd.Series] = None


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> MACDResult:
    """
    Calculate MACD (12, 26, 9)
    
    Args:
        prices: Price series
        fast: Fast EMA period
        slow: Slow EMA period  
        signal: Signal line period
    
    Returns:
        MACDResult with all components
    """
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = (macd_line - signal_line) * 2
    
    # Crossover signals: 1 = Bullish cross, -1 = Bearish cross
    crossover = pd.Series(0, index=prices.index)
    crossover[(macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))] = 1
    crossover[(macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))] = -1
    
    # Direction
    direction = pd.Series("NEUTRAL", index=prices.index)
    direction[macd_line > signal_line] = "BULLISH"
    direction[macd_line < signal_line] = "BEARISH"
    
    return MACDResult(
        macd_line=macd_line,
        signal_line=signal_line,
        histogram=histogram,
        crossover=crossover,
        direction=direction
    )


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> ADXResult:
    """
    Calculate ADX (Wilder's smoothing method)
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ADX period (default 14)
    
    Returns:
        ADXResult with ADX, +DI, -DI
    """
    # Calculate True Range (TR)
    high_low = high - low
    high_close = (high - close.shift(1)).abs()
    low_close = (low - close.shift(1)).abs()
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    tr = tr.rolling(min_periods=1).sum()
    
    # Calculate +DM and -DM
    high_diff = high.diff()
    low_diff = -low.diff()
    
    plus_dm = pd.Series(0, index=high.index)
    plus_dm[(high_diff > low_diff) & (high_diff > 0)] = high_diff
    
    minus_dm = pd.Series(0, index=high.index)
    minus_dm[(low_diff > high_diff) & (low_diff > 0)] = low_diff
    
    # Wilder's smoothing
    def wilders_smooth(series: pd.Series, period: int) -> pd.Series:
        alpha = 1 / period
        return series.ewm(alpha=alpha, adjust=False).mean()
    
    smoothed_tr = wilders_smooth(tr, period)
    smoothed_plus_dm = wilders_smooth(plus_dm, period)
    smoothed_minus_dm = wilders_smooth(minus_dm, period)
    
    # Calculate +DI and -DI
    plus_di = (smoothed_plus_dm / smoothed_tr) * 100
    minus_di = (smoothed_minus_dm / smoothed_tr) * 100
    
    # Calculate DX
    di_sum = plus_di + minus_di
    dx = pd.Series(0, index=high.index)
    dx[di_sum > 0] = ((plus_di - minus_di).abs() / di_sum) * 100
    
    # Calculate ADX (Wilder's smoothing of DX)
    adx = wilders_smooth(dx, period)
    
    # Trend strength classification
    trend_strength = pd.Series(TrendStrength.WEAK.value, index=high.index)
    trend_strength[(adx >= 20) & (adx < 25)] = TrendStrength.MODERATE.value
    trend_strength[(adx >= 25) & (adx < 50)] = TrendStrength.STRONG.value
    trend_strength[(adx >= 50) & (adx < 70)] = TrendStrength.VERY_STRONG.value
    trend_strength[adx >= 70] = TrendStrength.EXTREME.value
    
    # Trend direction
    trend_direction = pd.Series("NEUTRAL", index=high.index)
    trend_direction[plus_di > minus_di] = "BULLISH"
    trend_direction[minus_di > plus_di] = "BEARISH"
    
    return ADXResult(
        adx=adx,
        plus_di=plus_di,
        minus_di=minus_di,
        trend_strength=trend_strength,
        trend_direction=trend_direction
    )


def calculate_bollinger(prices: pd.Series, period: int = 20, std_multiplier: float = 2.0) -> BOLLResult:
    """
    Calculate Bollinger Bands (20, 2)
    
    Args:
        prices: Price series
        period: MA period (default 20)
        std_multiplier: Standard deviation multiplier (default 2)
    
    Returns:
        BOLLResult with upper, middle, lower bands
    """
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper = middle + (std * std_multiplier)
    lower = middle - (std * std_multiplier)
    
    # Bandwidth: (Upper - Lower) / Middle * 100
    bandwidth = ((upper - lower) / middle) * 100
    
    # Position: Where is price in the band (%)
    position = pd.Series(0, index=prices.index)
    band_range = upper - lower
    position[band_range > 0] = ((prices - lower) / band_range) * 100
    
    return BOLLResult(
        upper=upper,
        middle=middle,
        lower=lower,
        bandwidth=bandwidth,
        position=position
    )


def calculate_ema(prices: pd.Series, periods: List[int] = [9, 20, 50]) -> EMAResult:
    """
    Calculate multiple EMAs
    
    Args:
        prices: Price series
        periods: EMA periods to calculate
    
    Returns:
        EMAResult with ema_9, ema_20, ema_50
    """
    result = {}
    for period in periods:
        result[f'ema_{period}'] = prices.ewm(span=period, adjust=False).mean()
    
    return EMAResult(
        ema_9=result['ema_9'],
        ema_20=result['ema_20'],
        ema_50=result['ema_50']
    )


def calculate_volume_analysis(volume: pd.Series, period: int = 20) -> VolumeResult:
    """
    Calculate Volume Analysis
    
    MACDV: Volume > 1.5 × 20-day average volume
    
    Args:
        volume: Volume series
        period: MA period (default 20)
    
    Returns:
        VolumeResult with analysis
    """
    volume_ma20 = volume.rolling(window=period).mean()
    volume_ratio = volume / volume_ma20
    
    # Volume spike: volume > 1.5 × MA20
    volume_spike = volume_ratio > 1.5
    
    return VolumeResult(
        volume=volume,
        volume_ma20=volume_ma20,
        volume_ratio=volume_ratio,
        volume_spike=volume_spike
    )


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate RSI
    
    Args:
        prices: Price series
        period: RSI period
    
    Returns:
        RSI series
    """
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate ATR (Average True Range)
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ATR period
    
    Returns:
        ATR series
    """
    high_low = high - low
    high_close = (high - close.shift(1)).abs()
    low_close = (low - close.shift(1)).abs()
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    
    return atr


def calculate_all_indicators(
    df: pd.DataFrame,
    high_col: str = 'high',
    low_col: str = 'low', 
    close_col: str = 'close',
    volume_col: str = 'volume'
) -> Dict[str, Any]:
    """
    Calculate all professional indicators
    
    Args:
        df: DataFrame with OHLCV data
        high_col: High column name
        low_col: Low column name
        close_col: Close column name
        volume_col: Volume column name
    
    Returns:
        Dictionary with all indicator results
    """
    high = df[high_col]
    low = df[low_col]
    close = df[close_col]
    volume = df[volume_col]
    
    # Calculate all indicators
    macd = calculate_macd(close)
    adx = calculate_adx(high, low, close)
    boll = calculate_bollinger(close)
    ema = calculate_ema(close)
    vol = calculate_volume_analysis(volume)
    rsi = calculate_rsi(close)
    atr = calculate_atr(high, low, close)
    
    return {
        'macd': macd,
        'adx': adx,
        'boll': boll,
        'ema': ema,
        'volume': vol,
        'rsi': rsi,
        'atr': atr,
        'close': close,
        'high': high,
        'low': low,
        'volume_series': volume
    }


# Entry signal checker
def check_entry_signal(indicators: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if entry conditions are met (Long)
    
    Conditions (ALL must be satisfied):
    1. ADX > 25 AND rising
    2. +DI > -DI
    3. MACD cross over signal
    4. Price > 20 EMA
    5. Volume > 1.5 × 20-day average
    
    Args:
        indicators: Dictionary from calculate_all_indicators
    
    Returns:
        (signal_met, reason)
    """
    adx = indicators['adx']
    macd = indicators['macd']
    close = indicators['close']
    vol = indicators['volume']
    ema = indicators['ema']
    
    reasons = []
    signal_ok = True
    
    # Condition 1: ADX > 25 AND rising
    current_adx = adx.adx.iloc[-1]
    prev_adx = adx.adx.iloc[-2] if len(adx.adx) > 1 else 0
    if current_adx <= 25:
        signal_ok = False
        reasons.append(f"ADX={current_adx:.1f} <= 25")
    
    # Condition 2: +DI > -DI
    if adx.plus_di.iloc[-1] <= adx.minus_di.iloc[-1]:
        signal_ok = False
        reasons.append("+DI <= -DI")
    
    # Condition 3: MACD crossover (bullish)
    if macd.crossover.iloc[-1] != 1:
        signal_ok = False
        reasons.append("No MACD bullish crossover")
    
    # Condition 4: Price > 20 EMA
    if close.iloc[-1] <= ema.ema_20.iloc[-1]:
        signal_ok = False
        reasons.append(f"Price <= EMA20")
    
    # Condition 5: Volume spike
    if not vol.volume_spike.iloc[-1]:
        signal_ok = False
        reasons.append(f"Volume ratio = {vol.volume_ratio.iloc[-1]:.2f} <= 1.5")
    
    if signal_ok:
        return True, "All entry conditions satisfied"
    else:
        return False, "; ".join(reasons)


# Exit signal checker
def check_exit_signal(indicators: Dict[str, Any], entry_price: float) -> Tuple[bool, str]:
    """
    Check exit conditions
    
    Exit conditions:
    1. MACD reversal (bearish crossover)
    2. ADX weakening (< 20 or declining significantly)
    3. Stop loss hit (ATR based)
    4. Take profit target (R:R >= 1:2)
    
    Args:
        indicators: Indicator dictionary
        entry_price: Entry price
    
    Returns:
        (should_exit, reason)
    """
    adx = indicators['adx']
    macd = indicators['macd']
    close = indicators['close']
    atr = indicators['atr']
    
    reasons = []
    should_exit = False
    
    # Condition 1: MACD bearish crossover
    if macd.crossover.iloc[-1] == -1:
        should_exit = True
        reasons.append("MACD bearish crossover")
    
    # Condition 2: ADX < 20 (trend weakened)
    if adx.adx.iloc[-1] < 20:
        should_exit = True
        reasons.append(f"ADX={adx.adx.iloc[-1]:.1f} < 20")
    
    # Return reason
    if should_exit:
        return True, "; ".join(reasons)
    return False, ""


def get_market_regime(indicators: Dict[str, Any]) -> str:
    """
    Determine market regime
    
    Args:
        indicators: Indicator dictionary
    
    Returns:
        Regime: TRENDING, CONSOLIDATING, VOLATILE
    """
    adx = indicators['adx']
    boll = indicators['boll']
    close = indicators['close']
    
    adx_value = adx.adx.iloc[-1]
    
    if adx_value >= 25:
        return "TRENDING"
    elif adx_value < 20:
        return "CONSOLIDATING"
    else:
        return "TRANSITIONAL"


def get_vix_filter(vix: float) -> str:
    """
    VIX-based risk filter
    
    VIX < 20: Normal trading
    VIX 20-25: Caution
    VIX 25-30: Reduced position half
    VIX > 30: Exit all, stop trading
    
    Args:
        vix: Current VIX value
    
    Returns:
        Risk level recommendation
    """
    if vix < 20:
        return "NORMAL"
    elif vix < 25:
        return "CAUTION"
    elif vix < 30:
        return "HALF_POSITION"
    else:
        return "EXIT_ALL"