"""
市場狀態檢測器 - Market Regime Detector

檢測當前市場狀態：趨勢、震盪、高波動
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from src.utils.logger import logger


class MarketRegime(Enum):
    """市場狀態"""
    TRENDING_UP = "trending_up"      # 上升趨勢
    TRENDING_DOWN = "trending_down"  # 下降趨勢
    RANGING = "ranging"              # 震盪
    HIGH_VOLATILITY = "high_volatility"  # 高波動
    LOW_VOLATILITY = "low_volatility"    # 低波動
    UNKNOWN = "unknown"              # 未知


@dataclass
class RegimeMetrics:
    """狀態指標"""
    regime: MarketRegime
    confidence: float
    trend_strength: float
    volatility: float
    adx: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'regime': self.regime.value,
            'confidence': self.confidence,
            'trend_strength': self.trend_strength,
            'volatility': self.volatility,
            'adx': self.adx,
            'timestamp': self.timestamp.isoformat()
        }


class MarketRegimeDetector:
    """
    市場狀態檢測器
    
    使用技術指標判斷市場狀態：
    - ADX: 趨勢強度
    - ATR: 波動率
    - RSI: 超買超賣
    - 布林帶寬度: 波動區間
    """
    
    def __init__(
        self,
        adx_period: int = 14,
        adx_threshold: float = 25.0,
        volatility_threshold: float = 0.02,
        lookback_period: int = 20
    ):
        """
        初始化
        
        Args:
            adx_period: ADX 計算週期
            adx_threshold: 趨勢強度閾值
            volatility_threshold: 波動率閾值
            lookback_period: 回看週期
        """
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.volatility_threshold = volatility_threshold
        self.lookback_period = lookback_period
        
        self.current_regime = MarketRegime.UNKNOWN
        self.regime_history: List[RegimeMetrics] = []
        self.confidence_threshold = 0.6
    
    def detect(self, data: pd.DataFrame) -> RegimeMetrics:
        """
        檢測當前市場狀態
        
        Args:
            data: OHLCV 數據
            
        Returns:
            RegimeMetrics: 狀態指標
        """
        if len(data) < self.lookback_period:
            return RegimeMetrics(
                regime=MarketRegime.UNKNOWN,
                confidence=0.0,
                trend_strength=0.0,
                volatility=0.0,
                adx=0.0,
                timestamp=datetime.now()
            )
        
        # 計算技術指標
        adx = self._calculate_adx(data)
        volatility = self._calculate_volatility(data)
        trend_direction = self._detect_trend_direction(data)
        
        # 判斷狀態
        regime, confidence = self._classify_regime(adx, volatility, trend_direction)
        
        metrics = RegimeMetrics(
            regime=regime,
            confidence=confidence,
            trend_strength=adx,
            volatility=volatility,
            adx=adx,
            timestamp=datetime.now()
        )
        
        self.current_regime = regime
        self.regime_history.append(metrics)
        
        # 只保留最近 100 條記錄
        if len(self.regime_history) > 100:
            self.regime_history = self.regime_history[-100:]
        
        logger.info(f"市場狀態: {regime.value} (信心度: {confidence:.2%})")
        
        return metrics
    
    def _calculate_adx(self, data: pd.DataFrame) -> float:
        """計算 ADX (平均趨向指數)"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # +DM 和 -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        plus_dm[plus_dm <= minus_dm] = 0
        minus_dm[minus_dm <= plus_dm] = 0
        
        # 平滑
        atr = tr.rolling(window=self.adx_period).mean()
        plus_di = 100 * plus_dm.rolling(window=self.adx_period).mean() / atr
        minus_di = 100 * minus_dm.rolling(window=self.adx_period).mean() / atr
        
        # DX 和 ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=self.adx_period).mean()
        
        return adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0.0
    
    def _calculate_volatility(self, data: pd.DataFrame) -> float:
        """計算波動率 (ATR/價格)"""
        high = data['high']
        low = data['low']
        close = data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=14).mean()
        volatility = atr.iloc[-1] / close.iloc[-1] if close.iloc[-1] != 0 else 0
        
        return volatility
    
    def _detect_trend_direction(self, data: pd.DataFrame) -> str:
        """檢測趨勢方向"""
        close = data['close']
        
        # 使用簡單移動平均
        sma_short = close.rolling(window=10).mean()
        sma_long = close.rolling(window=30).mean()
        
        if sma_short.iloc[-1] > sma_long.iloc[-1]:
            return 'up'
        elif sma_short.iloc[-1] < sma_long.iloc[-1]:
            return 'down'
        return 'neutral'
    
    def _classify_regime(
        self,
        adx: float,
        volatility: float,
        trend_direction: str
    ) -> tuple:
        """
        分類市場狀態
        
        Returns:
            (MarketRegime, confidence)
        """
        # 高波動檢測
        if volatility > self.volatility_threshold * 2:
            confidence = min(1.0, volatility / (self.volatility_threshold * 3))
            return MarketRegime.HIGH_VOLATILITY, confidence
        
        # 低波動檢測
        if volatility < self.volatility_threshold * 0.3:
            confidence = 1.0 - (volatility / (self.volatility_threshold * 0.3))
            return MarketRegime.LOW_VOLATILITY, confidence
        
        # 趨勢檢測
        if adx > self.adx_threshold:
            confidence = min(1.0, adx / 50)
            if trend_direction == 'up':
                return MarketRegime.TRENDING_UP, confidence
            elif trend_direction == 'down':
                return MarketRegime.TRENDING_DOWN, confidence
        
        # 震盪檢測
        confidence = 1.0 - (adx / self.adx_threshold) if adx < self.adx_threshold else 0.0
        return MarketRegime.RANGING, max(0.0, min(1.0, confidence))
    
    def get_regime_distribution(self, lookback: int = 20) -> Dict[str, float]:
        """
        獲取最近狀態分佈
        
        Args:
            lookback: 回看週期
            
        Returns:
            各狀態出現比例
        """
        if not self.regime_history:
            return {}
        
        recent = self.regime_history[-lookback:]
        total = len(recent)
        
        distribution = {}
        for regime in MarketRegime:
            count = sum(1 for r in recent if r.regime == regime)
            distribution[regime.value] = count / total if total > 0 else 0
        
        return distribution
    
    def is_regime_stable(self, min_periods: int = 5) -> bool:
        """
        檢查狀態是否穩定
        
        Args:
            min_periods: 最小穩定週期
            
        Returns:
            是否穩定
        """
        if len(self.regime_history) < min_periods:
            return False
        
        recent = self.regime_history[-min_periods:]
        regimes = [r.regime for r in recent]
        
        # 檢查是否所有都是同一狀態
        return len(set(regimes)) == 1
