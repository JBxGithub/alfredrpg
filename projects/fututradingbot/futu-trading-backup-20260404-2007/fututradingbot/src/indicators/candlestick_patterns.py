"""
K線形態分析模組 - Candlestick Patterns Analysis Module
提供專業的K線形態識別功能
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class PatternType(Enum):
    """K線形態類型枚舉"""
    DOJI = "doji"
    HAMMER = "hammer"
    HANGING_MAN = "hanging_man"
    SHOOTING_STAR = "shooting_star"
    INVERTED_HAMMER = "inverted_hammer"
    MARUBOZU_BULLISH = "marubozu_bullish"
    MARUBOZU_BEARISH = "marubozu_bearish"
    ENGULFING_BULLISH = "engulfing_bullish"
    ENGULFING_BEARISH = "engulfing_bearish"
    HARAMI_BULLISH = "harami_bullish"
    HARAMI_BEARISH = "harami_bearish"
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"
    THREE_WHITE_SOLDIERS = "three_white_soldiers"
    THREE_BLACK_CROWS = "three_black_crows"
    NONE = "none"


class PatternStrength(Enum):
    """形態強度"""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class CandlestickPattern:
    """K線形態檢測結果"""
    pattern_type: PatternType
    strength: PatternStrength
    confidence: float
    position_score: float
    volume_score: float
    trend_score: float
    overall_score: float
    index: int
    description: str = ""
    
    def is_bullish(self) -> bool:
        bullish_patterns = [
            PatternType.HAMMER, PatternType.INVERTED_HAMMER,
            PatternType.MARUBOZU_BULLISH, PatternType.ENGULFING_BULLISH,
            PatternType.HARAMI_BULLISH, PatternType.MORNING_STAR,
            PatternType.THREE_WHITE_SOLDIERS
        ]
        return self.pattern_type in bullish_patterns
    
    def is_bearish(self) -> bool:
        bearish_patterns = [
            PatternType.HANGING_MAN, PatternType.SHOOTING_STAR,
            PatternType.MARUBOZU_BEARISH, PatternType.ENGULFING_BEARISH,
            PatternType.HARAMI_BEARISH, PatternType.EVENING_STAR,
            PatternType.THREE_BLACK_CROWS
        ]
        return self.pattern_type in bearish_patterns
    
    def is_reversal(self) -> bool:
        reversal_patterns = [
            PatternType.DOJI, PatternType.HAMMER, PatternType.HANGING_MAN,
            PatternType.SHOOTING_STAR, PatternType.INVERTED_HAMMER,
            PatternType.ENGULFING_BULLISH, PatternType.ENGULFING_BEARISH,
            PatternType.HARAMI_BULLISH, PatternType.HARAMI_BEARISH,
            PatternType.MORNING_STAR, PatternType.EVENING_STAR
        ]
        return self.pattern_type in reversal_patterns


class CandlestickAnalyzer:
    """K線形態分析器"""
    
    def __init__(
        self,
        doji_threshold: float = 0.01,
        hammer_shadow_ratio: float = 2.0,
        min_body_ratio: float = 0.1,
        marubozu_threshold: float = 0.05
    ):
        self.doji_threshold = doji_threshold
        self.hammer_shadow_ratio = hammer_shadow_ratio
        self.min_body_ratio = min_body_ratio
        self.marubozu_threshold = marubozu_threshold
    
    def analyze(self, df: pd.DataFrame) -> List[CandlestickPattern]:
        """分析整個DataFrame中的所有K線形態"""
        patterns = []
        for i in range(len(df)):
            pattern = self.detect_at_index(df, i)
            if pattern and pattern.pattern_type != PatternType.NONE:
                patterns.append(pattern)
        return patterns
    
    def detect_at_index(
        self, df: pd.DataFrame, idx: int, calculate_scores: bool = True
    ) -> Optional[CandlestickPattern]:
        """檢測指定索引位置的K線形態"""
        if idx < 0 or idx >= len(df):
            return None
        
        single_pattern = self._detect_single_candle(df, idx)
        double_pattern = self._detect_double_candle(df, idx) if idx >= 1 else None
        triple_pattern = self._detect_triple_candle(df, idx) if idx >= 2 else None
        
        best_pattern = triple_pattern or double_pattern or single_pattern
        
        if best_pattern is None:
            return CandlestickPattern(
                pattern_type=PatternType.NONE, strength=PatternStrength.WEAK,
                confidence=0.0, position_score=0.0, volume_score=0.0,
                trend_score=0.0, overall_score=0.0, index=idx, description="無明顯形態"
            )
        
        if calculate_scores:
            return self._calculate_pattern_strength(df, idx, best_pattern)
        return best_pattern
    
    def _detect_single_candle(self, df: pd.DataFrame, idx: int) -> Optional[CandlestickPattern]:
        """檢測單根K線形態"""
        open_p = df['open'].iloc[idx]
        high = df['high'].iloc[idx]
        low = df['low'].iloc[idx]
        close = df['close'].iloc[idx]
        
        body = abs(close - open_p)
        upper_shadow = high - max(open_p, close)
        lower_shadow = min(open_p, close) - low
        total_range = high - low
        
        if total_range == 0:
            return None
        
        body_ratio = body / total_range
        upper_ratio = upper_shadow / total_range
        lower_ratio = lower_shadow / total_range
        is_bullish = close > open_p
        
        if body_ratio <= self.doji_threshold:
            return CandlestickPattern(
                pattern_type=PatternType.DOJI, strength=PatternStrength.MODERATE,
                confidence=body_ratio / self.doji_threshold,
                position_score=0.5, volume_score=0.5, trend_score=0.5,
                overall_score=50.0, index=idx, description="十字星 - 市場猶豫不決"
            )
        
        if upper_ratio <= self.marubozu_threshold and lower_ratio <= self.marubozu_threshold:
            if is_bullish:
                return CandlestickPattern(
                    pattern_type=PatternType.MARUBOZU_BULLISH, strength=PatternStrength.STRONG,
                    confidence=1.0 - max(upper_ratio, lower_ratio) / self.marubozu_threshold,
                    position_score=0.7, volume_score=0.5, trend_score=0.8,
                    overall_score=75.0, index=idx, description="光頭光腳陽線 - 強勁看漲動能"
                )
            else:
                return CandlestickPattern(
                    pattern_type=PatternType.MARUBOZU_BEARISH, strength=PatternStrength.STRONG,
                    confidence=1.0 - max(upper_ratio, lower_ratio) / self.marubozu_threshold,
                    position_score=0.7, volume_score=0.5, trend_score=0.8,
                    overall_score=75.0, index=idx, description="光頭光腳陰線 - 強勁看跌動能"
                )
        
        if lower_ratio >= self.hammer_shadow_ratio * body_ratio and upper_ratio < 0.1:
            if is_bullish:
                return CandlestickPattern(
                    pattern_type=PatternType.HAMMER, strength=PatternStrength.MODERATE,
                    confidence=min(lower_ratio / (self.hammer_shadow_ratio * body_ratio), 1.0),
                    position_score=0.6, volume_score=0.5, trend_score=0.6,
                    overall_score=60.0, index=idx, description="錘子線 - 潛在看漲反轉"
                )
            else:
                return CandlestickPattern(
                    pattern_type=PatternType.HANGING_MAN, strength=PatternStrength.MODERATE,
                    confidence=min(lower_ratio / (self.hammer_shadow_ratio * body_ratio), 1.0),
                    position_score=0.6, volume_score=0.5, trend_score=0.6,
                    overall_score=60.0, index=idx, description="吊頸線 - 潛在看跌反轉"
                )
        
        if upper_ratio >= self.hammer_shadow_ratio * body_ratio and lower_ratio < 0.1:
            if not is_bullish:
                return CandlestickPattern(
                    pattern_type=PatternType.SHOOTING_STAR, strength=PatternStrength.MODERATE,
                    confidence=min(upper_ratio / (self.hammer_shadow_ratio * body_ratio), 1.0),
                    position_score=0.6, volume_score=0.5, trend_score=0.6,
                    overall_score=60.0, index=idx, description="射擊之星 - 潛在看跌反轉"
                )
            else:
                return CandlestickPattern(
                    pattern_type=PatternType.INVERTED_HAMMER, strength=PatternStrength.MODERATE,
                    confidence=min(upper_ratio / (self.hammer_shadow_ratio * body_ratio), 1.0),
                    position_score=0.6, volume_score=0.5, trend_score=0.6,
                    overall_score=60.0, index=idx, description="倒錘子 - 潛在看漲反轉"
                )
        return None
    
    def _detect_double_candle(self, df: pd.DataFrame, idx: int) -> Optional[CandlestickPattern]:
        """檢測雙根K線組合形態"""
        if idx < 1:
            return None
        
        open1, high1, low1, close1 = df['open'].iloc[idx-1], df['high'].iloc[idx-1], df['low'].iloc[idx-1], df['close'].iloc[idx-1]
        open2, high2, low2, close2 = df['open'].iloc[idx], df['high'].iloc[idx], df['low'].iloc[idx], df['close'].iloc[idx]
        body1, body2 = abs(close1 - open1), abs(close2 - open2)
        is_bullish1, is_bullish2 = close1 > open1, close2 > open2
        
        if is_bullish2 and not is_bullish1:
            if open2 < close1 and close2 > open1 and body2 > body1 * 1.2:
                return CandlestickPattern(
                    pattern_type=PatternType.ENGULFING_BULLISH, strength=PatternStrength.STRONG,
                    confidence=min(body2 / body1 / 1.5, 1.0),
                    position_score=0.75, volume_score=0.6, trend_score=0.7,
                    overall_score=80.0, index=idx, description="看漲吞沒 - 強勢反轉信號"
                )
        
        if not is_bullish2 and is_bullish1:
            if open2 > close1 and close2 < open1 and body2 > body1 * 1.2:
                return CandlestickPattern(
                    pattern_type=PatternType.ENGULFING_BEARISH, strength=PatternStrength.STRONG,
                    confidence=min(body2 / body1 / 1.5, 1.0),
                    position_score=0.75, volume_score=0.6, trend_score=0.7,
                    overall_score=80.0, index=idx, description="看跌吞沒 - 強勢反轉信號"
                )
        
        if body2 < body1 * 0.8:
            if is_bullish1 and not is_bullish2 and high2 < high1 and low2 > low1:
                return CandlestickPattern(
                    pattern_type=PatternType.HARAMI_BULLISH, strength=PatternStrength.MODERATE,
                    confidence=1.0 - body2 / body1,
                    position_score=0.65, volume_score=0.5, trend_score=0.6,
                    overall_score=65.0, index=idx, description="看漲孕育 - 潛在底部反轉"
                )
            if not is_bullish1 and is_bullish2 and high2 < high1 and low2 > low1:
                return CandlestickPattern(
                    pattern_type=PatternType.HARAMI_BEARISH, strength=PatternStrength.MODERATE,
                    confidence=1.0 - body2 / body1,
                    position_score=0.65, volume_score=0.5, trend_score=0.6,
                    overall_score=65.0, index=idx, description="看跌孕育 - 潛在頂部反轉"
                )
        return None
    
    def _detect_triple_candle(self, df: pd.DataFrame, idx: int) -> Optional[CandlestickPattern]:
        """檢測三根K線組合形態"""
        if idx < 2:
            return None
        
        opens = [df['open'].iloc[idx-i] for i in range(3)]
        closes = [df['close'].iloc[idx-i] for i in range(3)]
        bodies = [abs(closes[i] - opens[i]) for i in range(3)]
        is_bullish = [closes[i] > opens[i] for i in range(3)]
        
        if not is_bullish[2] and is_bullish[0]:
            if bodies[2] > bodies[1] * 2 and bodies[0] > bodies[1] * 2 and closes[0] > (opens[2] + closes[2]) / 2:
                return CandlestickPattern(
                    pattern_type=PatternType.MORNING_STAR, strength=PatternStrength.VERY_STRONG,
                    confidence=0.9, position_score=0.85, volume_score=0.7, trend_score=0.8,
                    overall_score=90.0, index=idx, description="晨星 - 強烈看漲反轉信號"
                )
        
        if is_bullish[2] and not is_bullish[0]:
            if bodies[2] > bodies[1] * 2 and bodies[0] > bodies[1] * 2 and closes[0] < (opens[2] + closes[2]) / 2:
                return CandlestickPattern(
                    pattern_type=PatternType.EVENING_STAR, strength=PatternStrength.VERY_STRONG,
                    confidence=0.9, position_score=0.85, volume_score=0.7, trend_score=0.8,
                    overall_score=90.0, index=idx, description="暮星 - 強烈看跌反轉信號"
                )
        
        if all(is_bullish) and closes[0] > closes[1] > closes[2] and opens[0] > opens[1] > opens[2]:
            return CandlestickPattern(
                pattern_type=PatternType.THREE_WHITE_SOLDIERS, strength=PatternStrength.STRONG,
                confidence=0.85, position_score=0.8, volume_score=0.7, trend_score=0.85,
                overall_score=85.0, index=idx, description="三白兵 - 強勁上升趨勢"
            )
        
        if not any(is_bullish) and closes[0] < closes[1] < closes[2] and opens[0] < opens[1] < opens[2]:
            return CandlestickPattern(
                pattern_type=PatternType.THREE_BLACK_CROWS, strength=PatternStrength.STRONG,
                confidence=0.85, position_score=0.8, volume_score=0.7, trend_score=0.85,
                overall_score=85.0, index=idx, description="三烏鴉 - 強勁下降趨勢"
            )
        return None
    
    def _calculate_pattern_strength(self, df: pd.DataFrame, idx: int, pattern: CandlestickPattern) -> CandlestickPattern:
        """計算形態的綜合強度評分"""
        position_score = self._calculate_position_score(df, idx, pattern)
        volume_score = self._calculate_volume_score(df, idx, pattern)
        trend_score = self._calculate_trend_score(df, idx, pattern)
        
        overall_score = (position_score * 0.4 + volume_score * 0.3 + trend_score * 0.3) * 100
        
        if overall_score >= 80:
            strength = PatternStrength.VERY_STRONG
        elif overall_score >= 65:
            strength = PatternStrength.STRONG
        elif overall_score >= 50:
            strength = PatternStrength.MODERATE
        else:
            strength = PatternStrength.WEAK
        
        return CandlestickPattern(
            pattern_type=pattern.pattern_type, strength=strength,
            confidence=pattern.confidence, position_score=position_score,
            volume_score=volume_score, trend_score=trend_score,
            overall_score=round(overall_score, 2), index=idx,
            description=pattern.description
        )
    
    def _calculate_position_score(self, df: pd.DataFrame, idx: int, pattern: CandlestickPattern) -> float:
        """計算位置評分"""
        if len(df) < 20 or idx < 5:
            return 0.5
        
        close = df['close'].iloc[idx]
        recent_high = df['high'].iloc[max(0, idx-20):idx+1].max()
        recent_low = df['low'].iloc[max(0, idx-20):idx+1].min()
        
        if recent_high == recent_low:
            return 0.5
        
        position_in_range = (close - recent_low) / (recent_high - recent_low)
        
        if pattern.is_bullish():
            if position_in_range < 0.3:
                return 0.9
            elif position_in_range < 0.5:
                return 0.7
            else:
                return 0.4
        elif pattern.is_bearish():
            if position_in_range > 0.7:
                return 0.9
            elif position_in_range > 0.5:
                return 0.7
            else:
                return 0.4
        return 0.5
    
    def _calculate_volume_score(self, df: pd.DataFrame, idx: int, pattern: CandlestickPattern) -> float:
        """計算成交量評分"""
        if 'volume' not in df.columns or idx < 5:
            return 0.5
        
        current_volume = df['volume'].iloc[idx]
        avg_volume = df['volume'].iloc[max(0, idx-5):idx].mean()
        
        if avg_volume == 0:
            return 0.5
        
        volume_ratio = current_volume / avg_volume
        
        if pattern.is_reversal():
            if volume_ratio > 2.0:
                return 0.9
            elif volume_ratio > 1.5:
                return 0.75
            elif volume_ratio > 1.0:
                return 0.6
            else:
                return 0.4
        else:
            if volume_ratio > 1.2:
                return 0.8
            else:
                return 0.6
    
    def _calculate_trend_score(self, df: pd.DataFrame, idx: int, pattern: CandlestickPattern) -> float:
        """計算趨勢評分"""
        if len(df) < 10 or idx < 5:
            return 0.5
        
        close = df['close'].iloc[idx]
        close_5 = df['close'].iloc[idx-5]
        close_10 = df['close'].iloc[idx-10]
        
        short_trend = (close - close_5) / close_5 if close_5 != 0 else 0
        medium_trend = (close - close_10) / close_10 if close_10 != 0 else 0
        
        if pattern.is_bullish():
            if short_trend < -0.05:
                return 0.85
            elif short_trend > 0 and medium_trend > 0:
                return 0.75
            else:
                return 0.6
        elif pattern.is_bearish():
            if short_trend > 0.05:
                return 0.85
            elif short_trend < 0 and medium_trend < 0:
                return 0.75
            else:
                return 0.6
        return 0.5
    
    def get_latest_signals(self, df: pd.DataFrame, min_score: float = 60.0, n: int = 5) -> List[CandlestickPattern]:
        """獲取最近的K線形態信號"""
        signals = []
        for i in range(max(0, len(df)-n), len(df)):
            pattern = self.detect_at_index(df, i)
            if pattern and pattern.overall_score >= min_score:
                signals.append(pattern)
        return signals
    
    def get_signal_summary(self, df: pd.DataFrame) -> Dict[str, any]:
        """獲取K線形態信號摘要"""
        patterns = self.analyze(df)
        if not patterns:
            return {'has_signal': False, 'latest_pattern': None, 'bullish_count': 0, 'bearish_count': 0, 'strongest_signal': None}
        
        bullish = [p for p in patterns if p.is_bullish()]
        bearish = [p for p in patterns if p.is_bearish()]
        strongest = max(patterns, key=lambda p: p.overall_score)
        
        return {
            'has_signal': True, 'latest_pattern': patterns[-1],
            'bullish_count': len(bullish), 'bearish_count': len(bearish),
            'strongest_signal': strongest, 'avg_score': np.mean([p.overall_score for p in patterns])
        }


def detect_doji(df: pd.DataFrame, idx: int = -1) -> bool:
    """檢測十字星"""
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, idx if idx >= 0 else len(df) + idx)
    return pattern.pattern_type == PatternType.DOJI if pattern else False


def detect_hammer(df: pd.DataFrame, idx: int = -1) -> bool:
    """檢測錘子線"""
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, idx if idx >= 0 else len(df) + idx)
    return pattern.pattern_type == PatternType.HAMMER if pattern else False


def detect_shooting_star(df: pd.DataFrame, idx: int = -1) -> bool:
    """檢測射擊之星"""
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, idx if idx >= 0 else len(df) + idx)
    return pattern.pattern_type == PatternType.SHOOTING_STAR if pattern else False


def detect_marubozu(df: pd.DataFrame, idx: int = -1) -> Optional[str]:
    """檢測光頭光腳"""
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, idx if idx >= 0 else len(df) + idx)
    if pattern.pattern_type == PatternType.MARUBOZU_BULLISH:
        return 'bullish'
    elif pattern.pattern_type == PatternType.MARUBOZU_BEARISH:
        return 'bearish'
    return None


def detect_engulfing(df: pd.DataFrame, idx: int = -1) -> Optional[str]:
    """檢測吞沒形態"""
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, idx if idx >= 0 else len(df) + idx)
    if pattern.pattern_type == PatternType.ENGULFING_BULLISH:
        return 'bullish'
    elif pattern.pattern_type == PatternType.ENGULFING_BEARISH:
        return 'bearish'
    return None


def detect_harami(df: pd.DataFrame, idx: int = -1) -> Optional[str]:
    """檢測孕育形態"""
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, idx if idx >= 0 else len(df) + idx)
    if pattern.pattern_type == PatternType.HARAMI_BULLISH:
        return 'bullish'
    elif pattern.pattern_type == PatternType.HARAMI_BEARISH:
        return 'bearish'
    return None


def detect_morning_star(df: pd.DataFrame, idx: int = -1) -> bool:
    """檢測晨星"""
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, idx if idx >= 0 else len(df) + idx)
    return pattern.pattern_type == PatternType.MORNING_STAR if pattern else False


def detect_evening_star(df: pd.DataFrame, idx: int = -1) -> bool:
    """檢測暮星"""
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, idx if idx >= 0 else len(df) + idx)
    return pattern.pattern_type == PatternType.EVENING_STAR if pattern else False


def calculate_pattern_strength(df: pd.DataFrame, idx: int = -1) -> float:
    """計算形態綜合評分"""
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, idx if idx >= 0 else len(df) + idx)
    return pattern.overall_score if pattern else 0.0
