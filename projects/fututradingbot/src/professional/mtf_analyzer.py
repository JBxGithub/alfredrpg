"""
多時間框架分析模組 - Multi-Time Frame Analyzer (MTF)

MTF Architecture:
- Monthly (月线): Final trend filter - NEVER trade against monthly trend
- Weekly (周线): ADX > 20 + price above/below 20 EMA
- Daily (日线): All conditions met before entry

Author: Professional Trading System
Version: 2.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from src.professional.indicators import (
    calculate_adx, calculate_ema, calculate_all_indicators,
    calculate_macd, calculate_bollinger
)


class MTFTrend(Enum):
    """Multi-Time Frame Trend"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class MTFSignal(Enum):
    """MTF Entry Signal"""
    STRONG_BUY = "strong_buy"      # All 3 timeframes aligned
    BUY = "buy"                   # Weekly + Daily aligned
    NEUTRAL = "neutral"           # No clear direction
    SELL = "sell"                # Against trend
    STRONG_SELL = "strong_sell"  # All 3 timeframes bearish


@dataclass
class TimeFrameAnalysis:
    """Single timeframe analysis result"""
    timeframe: str           # monthly/weekly/daily
    trend: MTFTrend          # trend direction
    adx: float               # ADX value
    adx_strength: str        # weak/moderate/strong/very_strong/extreme
    price_above_ema20: bool  # price position relative to EMA20
    ema_arrangement: str    # bullish/bearish/neutral
    is_trending: bool        # ADX > 20
    is_consolidating: bool    # ADX < 20
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timeframe': self.timeframe,
            'trend': self.trend.value,
            'adx': self.adx,
            'adx_strength': self.adx_strength,
            'price_above_ema20': self.price_above_ema20,
            'ema_arrangement': self.ema_arrangement,
            'is_trending': self.is_trending,
            'is_consolidating': self.is_consolidating
        }


@dataclass
class MTFResult:
    """Multi-Time Frame Analysis Result"""
    monthly: Optional[TimeFrameAnalysis]
    weekly: Optional[TimeFrameAnalysis]
    daily: Optional[TimeFrameAnalysis]
    signal: MTFSignal
    entry_allowed: bool
    reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'signal': self.signal.value,
            'entry_allowed': self.entry_allowed,
            'reason': self.reason
        }
        if self.monthly:
            result['monthly'] = self.monthly.to_dict()
        if self.weekly:
            result['weekly'] = self.weekly.to_dict()
        if self.daily:
            result['daily'] = self.daily.to_dict()
        return result


def analyze_single_timeframe(
    df: pd.DataFrame,
    timeframe: str,
    adx_period: int = 14
) -> TimeFrameAnalysis:
    """
    Analyze a single timeframe
    
    Args:
        df: DataFrame with OHLCV data
        timeframe: monthly/weekly/daily
        adx_period: ADX period
    
    Returns:
        TimeFrameAnalysis result
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate ADX
    adx_result = calculate_adx(high, low, close, adx_period)
    adx_value = adx_result.adx.iloc[-1]
    
    # Trend strength
    if adx_value < 20:
        adx_strength = "weak"
    elif adx_value < 25:
        adx_strength = "moderate"
    elif adx_value < 50:
        adx_strength = "strong"
    elif adx_value < 70:
        adx_strength = "very_strong"
    else:
        adx_strength = "extreme"
    
    # Trend direction (+DI vs -DI)
    if adx_result.plus_di.iloc[-1] > adx_result.minus_di.iloc[-1]:
        trend = MTFTrend.BULLISH
    elif adx_result.minus_di.iloc[-1] > adx_result.plus_di.iloc[-1]:
        trend = MTFTrend.BEARISH
    else:
        trend = MTFTrend.NEUTRAL
    
    # EMA analysis
    ema_result = calculate_ema(close)
    current_price = close.iloc[-1]
    ema20 = ema_result.ema_20.iloc[-1]
    
    # Price above EMA20
    price_above_ema20 = current_price > ema20
    
    # EMA arrangement
    ema_arrangement = ema_result.get排列()
    
    # Is trending/ consolidating
    is_trending = adx_value > 20
    is_consolidating = adx_value < 20
    
    return TimeFrameAnalysis(
        timeframe=timeframe,
        trend=trend,
        adx=adx_value,
        adx_strength=adx_strength,
        price_above_ema20=price_above_ema20,
        ema_arrangement=ema_arrangement,
        is_trending=is_trending,
        is_consolidating=is_consolidating
    )


def analyze_monthly(df: pd.DataFrame) -> TimeFrameAnalysis:
    """Analyze monthly timeframe"""
    return analyze_single_timeframe(df, "monthly")


def analyze_weekly(df: pd.DataFrame) -> TimeFrameAnalysis:
    """Analyze weekly timeframe"""
    return analyze_single_timeframe(df, "weekly")


def analyze_daily(df: pd.DataFrame) -> TimeFrameAnalysis:
    """Analyze daily timeframe"""
    return analyze_single_timeframe(df, "daily")


def combine_mtf(
    monthly: Optional[TimeFrameAnalysis],
    weekly: Optional[TimeFrameAnalysis],
    daily: Optional[TimeFrameAnalysis]
) -> MTFResult:
    """
    Combine MTF analysis into final signal
    
    MTF Entry Logic:
    1. Monthly: Final trend filter - NEVER trade against monthly
    2. Weekly: ADX > 20 + price at same side of 20 EMA
    3. Daily: All conditions met before entry
    
    Args:
        monthly: Monthly analysis
        weekly: Weekly analysis  
        daily: Daily analysis
    
    Returns:
        MTFResult with signal and entry decision
    """
    reasons = []
    entry_allowed = False
    signal = MTFSignal.NEUTRAL
    
    # Cannot analyze without daily
    if daily is None:
        return MTFResult(
            monthly=monthly,
            weekly=weekly,
            daily=daily,
            signal=MTFSignal.NEUTRAL,
            entry_allowed=False,
            reason="No daily data"
        )
    
    # Check monthly (filter only)
    monthly_trend_bullish = False
    if monthly:
        monthly_trend_bullish = monthly.trend == MTFTrend.BULLISH
        reasons.append(f"Monthly: {monthly.trend.value}")
    
    # Check weekly
    weekly_ok = False
    if weekly:
        weekly_trending = weekly.adx > 20
        weekly_price_ok = weekly.price_above_ema20
        reasons.append(f"Weekly: ADX={weekly.adx:.1f}, price_{'above' if weekly_price_ok else 'below'}_EMA20")
        
        if weekly_trending and weekly_price_ok:
            weekly_ok = True
    
    # Check daily (all conditions)
    daily_ok = False
    if daily:
        daily_trending = daily.adx > 25  # Stronger requirement for daily
        daily_bullish = daily.trend == MTFTrend.BULLISH
        daily_price_ok = daily.price_above_ema20
        reasons.append(f"Daily: ADX={daily.adx:.1f}, {daily.trend.value}, price_{'above' if daily_price_ok else 'below'}_EMA20")
        
        if daily_trending and daily_bullish and daily_price_ok:
            daily_ok = True
    
    # Combine signals
    if monthly and not monthly_trend_bullish:
        # Monthly is bearish - cannot go long
        signal = MTFSignal.SELL
        reasons.append("BLOCKED: Monthly trend is bearish")
    elif weekly_ok and daily_ok and monthly_trend_bullish:
        # All aligned
        signal = MTFSignal.STRONG_BUY
        entry_allowed = True
        reasons.append("APPROVED: All timeframes aligned")
    elif daily_ok:
        # Daily OK but weekly might be weak
        signal = MTFSignal.BUY
        entry_allowed = True
        reasons.append("APPROVED: Daily conditions met")
    else:
        signal = MTFSignal.NEUTRAL
        entry_allowed = False
        if not daily_ok:
            reasons.append("BLOCKED: Daily conditions not met")
        if not weekly_ok:
            reasons.append("BLOCKED: Weekly trend weak")
    
    return MTFResult(
        monthly=monthly,
        weekly=weekly,
        daily=daily,
        signal=signal,
        entry_allowed=entry_allowed,
        reason="; ".join(reasons)
    )


def analyze_mtf(
    df_daily: pd.DataFrame,
    df_weekly: Optional[pd.DataFrame] = None,
    df_monthly: Optional[pd.DataFrame] = None
) -> MTFResult:
    """
    Complete MTF analysis
    
    Args:
        df_daily: Daily OHLCV data
        df_weekly: Weekly OHLCV data (optional)
        df_monthly: Monthly OHLCV data (optional)
    
    Returns:
        MTFResult
    """
    # Analyze daily (required)
    daily_analysis = None
    if df_daily is not None and len(df_daily) > 30:
        daily_analysis = analyze_daily(df_daily)
    
    # Analyze weekly (if data available)
    weekly_analysis = None
    if df_weekly is not None and len(df_weekly) > 20:
        weekly_analysis = analyze_weekly(df_weekly)
    
    # Analyze monthly (if data available)
    monthly_analysis = None
    if df_monthly is not None and len(df_monthly) > 10:
        monthly_analysis = analyze_monthly(df_monthly)
    
    # Combine
    return combine_mtf(monthly_analysis, weekly_analysis, daily_analysis)


# Quick entry check
def check_mtf_entry(df_daily: pd.DataFrame, df_weekly: Optional[pd.DataFrame] = None) -> Tuple[bool, str]:
    """
    Quick MTF entry check
    
    Simplified version for quick decision
    
    Args:
        df_daily: Daily data
        df_weekly: Weekly data
    
    Returns:
        (entry_allowed, reason)
    """
    daily = analyze_daily(df_daily)
    
    weekly = None
    if df_weekly is not None and len(df_weekly) > 20:
        weekly = analyze_weekly(df_weekly)
    
    result = combine_mtf(None, weekly, daily)
    
    return result.entry_allowed, result.reason


# Weekly-Daily alignment check
def check_weekly_daily_alignment(
    df_weekly: pd.DataFrame,
    df_daily: pd.DataFrame
) -> Tuple[bool, str]:
    """
    Check if weekly and daily are aligned
    
    Args:
        df_weekly: Weekly data
        df_daily: Daily data
    
    Returns:
        (aligned, reason)
    """
    weekly = analyze_weekly(df_weekly)
    daily = analyze_daily(df_daily)
    
    aligned = (
        weekly.trend == daily.trend and
        weekly.adx > 20 and
        weekly.price_above_ema20 == daily.price_above_ema20
    )
    
    if aligned:
        return True, f"Weekly/Daily aligned ({weekly.trend.value})"
    else:
        return False, f"Weekly/Daily misaligned"


# Get monthly trend (for filtering)
def get_monthly_trend(df_monthly: pd.DataFrame) -> MTFTrend:
    """
    Get monthly trend direction
    
    Args:
        df_monthly: Monthly data
    
    Returns:
        MTFTrend: BULLISH, BEARISH, or NEUTRAL
    """
    if df_monthly is None or len(df_monthly) < 10:
        return MTFTrend.UNKNOWN
    
    monthly = analyze_monthly(df_monthly)
    return monthly.trend


# VIX integration with MTF
def get_mtf_with_vix(
    mtf_result: MTFResult,
    vix: float
) -> Dict[str, Any]:
    """
    Apply VIX filter to MTF signal
    
    VIX < 20: Normal trading
    VIX 20-25: Caution
    VIX 25-30: Reduce position by half
    VIX > 30: Exit all, stop trading
    
    Args:
        mtf_result: MTF analysis result
        vix: Current VIX value
    
    Returns:
        Modified result with VIX filter applied
    """
    result = mtf_result.to_dict()
    
    if vix < 20:
        result['vix_filter'] = 'NORMAL'
        result['risk_level'] = 'LOW'
    elif vix < 25:
        result['vix_filter'] = 'CAUTION'
        result['risk_level'] = 'MEDIUM'
    elif vix < 30:
        result['vix_filter'] = 'HALF_POSITION'
        result['risk_level'] = 'HIGH'
        result['entry_allowed'] = mtf_result.entry_allowed and False  # Force review
    else:
        result['vix_filter'] = 'EXIT_ALL'
        result['risk_level'] = 'EXTREME'
        result['entry_allowed'] = False
        result['reason'] = f"VIX={vix:.1f} > 30 - Extreme risk, exit all"
    
    result['vix'] = vix
    return result