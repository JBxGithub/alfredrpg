"""
市場狀態檢測模組 - Market Regime Detection Module

使用 Hidden Markov Model (HMM) 和技術指標進行市場狀態識別
支持四種市場狀態：
- TRENDING_UP: 上升趨勢
- TRENDING_DOWN: 下降趨勢
- RANGING: 震盪整理
- HIGH_VOLATILITY: 高波動

整合市場情緒分析功能

作者: FutuTradingBot AI Research Team
版本: 1.1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path

from src.utils.logger import logger
from src.analysis.market_sentiment import (
    MarketSentimentAnalyzer, MarketSentimentAnalysis,
    SentimentIndicators, MarketSentiment
)


class MarketRegime(Enum):
    """市場狀態枚舉"""
    TRENDING_UP = "trending_up"           # 上升趨勢
    TRENDING_DOWN = "trending_down"       # 下降趨勢
    RANGING = "ranging"                    # 震盪整理
    HIGH_VOLATILITY = "high_volatility"    # 高波動
    UNKNOWN = "unknown"                    # 未知狀態


class VolatilityRegime(Enum):
    """波動率區間枚舉"""
    LOW = "low"              # 低波動 (< 0.8x 歷史平均)
    MEDIUM = "medium"        # 中波動 (0.8x - 1.2x)
    HIGH = "high"            # 高波動 (1.2x - 1.8x)
    EXTREME = "extreme"      # 極高波動 (> 1.8x)


@dataclass
class RegimeFeatures:
    """市場狀態特徵"""
    returns: float = 0.0           # 收益率
    volatility: float = 0.0        # 波動率
    volume_change: float = 0.0     # 成交量變化
    trend_strength: float = 0.0    # 趨勢強度 (0-100)
    adx: float = 0.0               # ADX值
    atr_ratio: float = 1.0         # ATR比率
    boll_bandwidth: float = 0.0    # 布林帶寬度
    price_momentum: float = 0.0    # 價格動能
    # 情緒指標
    fear_greed_index: float = 50.0 # 恐懼/貪婪指數
    sentiment_score: float = 0.0   # 情緒評分 (-1 到 1)
    
    def to_vector(self) -> np.ndarray:
        """轉換為特徵向量"""
        return np.array([
            self.returns,
            self.volatility,
            self.volume_change,
            self.trend_strength / 100,  # 標準化
            self.adx / 100,              # 標準化
            self.atr_ratio,
            self.boll_bandwidth,
            self.price_momentum,
            self.fear_greed_index / 100, # 標準化
            self.sentiment_score
        ])


@dataclass
class RegimeState:
    """市場狀態結果"""
    regime: MarketRegime
    volatility_regime: VolatilityRegime
    confidence: float = 0.0        # 置信度 (0-1)
    features: RegimeFeatures = field(default_factory=RegimeFeatures)
    timestamp: datetime = field(default_factory=datetime.now)
    duration: int = 0              # 當前狀態持續時間
    
    def is_trending(self) -> bool:
        """是否為趨勢市場"""
        return self.regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]
    
    def is_ranging(self) -> bool:
        """是否為震盪市場"""
        return self.regime == MarketRegime.RANGING
    
    def is_high_volatility(self) -> bool:
        """是否為高波動市場"""
        return self.regime == MarketRegime.HIGH_VOLATILITY


class HiddenMarkovModel:
    """
    簡化版隱馬爾可夫模型
    
    由於完整HMM實現需要額外依賴庫 (hmmlearn)，
    這裡提供一個基於規則的實現，可後續替換為真正的HMM
    """
    
    def __init__(self, n_states: int = 4):
        self.n_states = n_states
        self.state_names = [
            MarketRegime.TRENDING_UP,
            MarketRegime.TRENDING_DOWN,
            MarketRegime.RANGING,
            MarketRegime.HIGH_VOLATILITY
        ]
        
        # 轉移概率矩陣 (簡化版)
        self.transition_matrix = np.array([
            [0.6, 0.1, 0.2, 0.1],   # 從上升趨勢
            [0.1, 0.6, 0.2, 0.1],   # 從下降趨勢
            [0.25, 0.25, 0.4, 0.1], # 從震盪
            [0.2, 0.2, 0.2, 0.4]    # 從高波動
        ])
        
        self.current_state = MarketRegime.RANGING
        self.state_history: List[MarketRegime] = []
        
    def decode(self, features: RegimeFeatures) -> Tuple[MarketRegime, float]:
        """
        根據特徵推斷市場狀態
        
        Returns:
            (狀態, 置信度)
        """
        # 基於規則的狀態推斷
        scores = {}
        
        # 上升趨勢得分
        scores[MarketRegime.TRENDING_UP] = (
            (1 if features.returns > 0.001 else 0) * 0.2 +
            (features.trend_strength / 100) * 0.3 +
            (features.adx / 100) * 0.3 +
            (1 if features.price_momentum > 0 else 0) * 0.2
        )
        
        # 下降趨勢得分
        scores[MarketRegime.TRENDING_DOWN] = (
            (1 if features.returns < -0.001 else 0) * 0.2 +
            (features.trend_strength / 100) * 0.3 +
            (features.adx / 100) * 0.3 +
            (1 if features.price_momentum < 0 else 0) * 0.2
        )
        
        # 震盪得分
        scores[MarketRegime.RANGING] = (
            (1 if abs(features.returns) < 0.005 else 0) * 0.3 +
            (1 - features.trend_strength / 100) * 0.3 +
            (1 - features.adx / 50) * 0.2 +
            (1 - features.boll_bandwidth) * 0.2
        )
        
        # 高波動得分
        scores[MarketRegime.HIGH_VOLATILITY] = (
            min(features.volatility * 10, 1.0) * 0.4 +
            (1 if features.atr_ratio > 1.5 else features.atr_ratio / 1.5) * 0.4 +
            min(features.boll_bandwidth * 2, 1.0) * 0.2
        )
        
        # 應用轉移概率
        current_idx = self.state_names.index(self.current_state)
        for i, state in enumerate(self.state_names):
            scores[state] *= self.transition_matrix[current_idx][i]
        
        # 選擇得分最高的狀態
        best_state = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = scores[best_state] / total_score if total_score > 0 else 0
        
        return best_state, confidence
    
    def update_state(self, new_state: MarketRegime):
        """更新當前狀態"""
        self.state_history.append(self.current_state)
        self.current_state = new_state


class MarketRegimeDetector:
    """
    市場狀態檢測器
    
    結合技術指標、HMM和情緒分析進行市場狀態識別
    """
    
    def __init__(self, lookback_period: int = 20):
        """
        初始化檢測器
        
        Args:
            lookback_period: 回看週期
        """
        self.lookback_period = lookback_period
        self.hmm = HiddenMarkovModel()
        
        # 情緒分析器
        self.sentiment_analyzer = MarketSentimentAnalyzer()
        
        # 歷史數據緩存
        self.price_history: pd.DataFrame = pd.DataFrame()
        self.regime_history: List[RegimeState] = []
        self.sentiment_history: List[MarketSentimentAnalysis] = []
        
        # 歷史波動率基準
        self.historical_volatility: float = 0.0
        
        logger.info(f"市場狀態檢測器初始化完成 (回看週期: {lookback_period})")
    
    def fit(self, df: pd.DataFrame):
        """
        使用歷史數據訓練/校準模型
        
        Args:
            df: 歷史價格數據
        """
        if len(df) < self.lookback_period * 2:
            logger.warning("歷史數據不足，無法校準模型")
            return
        
        # 計算歷史波動率基準
        returns = df['close'].pct_change().dropna()
        self.historical_volatility = returns.std() * np.sqrt(252)
        
        logger.info(f"模型校準完成，歷史波動率: {self.historical_volatility:.2%}")
    
    def detect(self, df: pd.DataFrame) -> RegimeState:
        """
        檢測當前市場狀態
        
        Args:
            df: 價格數據 (至少包含 lookback_period 條數據)
            
        Returns:
            RegimeState: 市場狀態
        """
        if len(df) < self.lookback_period:
            logger.warning(f"數據不足，需要至少 {self.lookback_period} 條數據")
            return RegimeState(
                regime=MarketRegime.UNKNOWN,
                volatility_regime=VolatilityRegime.MEDIUM,
                confidence=0.0
            )
        
        # 計算特徵
        features = self._calculate_features(df)
        
        # HMM狀態解碼
        regime, confidence = self.hmm.decode(features)
        self.hmm.update_state(regime)
        
        # 檢測波動率區間
        vol_regime = self._detect_volatility_regime(features.atr_ratio)
        
        # 計算狀態持續時間
        duration = self._calculate_regime_duration(regime)
        
        # 創建狀態對象
        state = RegimeState(
            regime=regime,
            volatility_regime=vol_regime,
            confidence=confidence,
            features=features,
            timestamp=datetime.now(),
            duration=duration
        )
        
        self.regime_history.append(state)
        
        # 保持歷史記錄在合理範圍
        if len(self.regime_history) > 1000:
            self.regime_history = self.regime_history[-500:]
        
        return state
    
    def _calculate_features(self, df: pd.DataFrame) -> RegimeFeatures:
        """計算市場特徵 (整合情緒指標)"""
        features = RegimeFeatures()
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df.get('volume', pd.Series(0, index=df.index))
        
        # 計算收益率
        returns = close.pct_change().dropna()
        features.returns = returns.iloc[-1] if len(returns) > 0 else 0
        
        # 計算波動率 (年化)
        if len(returns) >= 10:
            features.volatility = returns.std() * np.sqrt(252)
        
        # 成交量變化
        if len(volume) >= 2 and volume.iloc[-2] > 0:
            features.volume_change = (volume.iloc[-1] - volume.iloc[-2]) / volume.iloc[-2]
        
        # 趨勢強度和ADX
        features.adx = self._calculate_adx(df, 14)
        features.trend_strength = self._calculate_trend_strength(df)
        
        # ATR比率
        atr = self._calculate_atr(df, 14)
        historical_atr = self._calculate_historical_atr(df, 60)
        features.atr_ratio = atr / historical_atr if historical_atr > 0 else 1.0
        
        # 布林帶寬度
        features.boll_bandwidth = self._calculate_boll_bandwidth(df)
        
        # 價格動能
        if len(close) >= 10:
            features.price_momentum = (close.iloc[-1] - close.iloc[-10]) / close.iloc[-10]
        
        # 整合情緒指標
        try:
            sentiment_analysis = self.sentiment_analyzer.analyze(df)
            self.sentiment_history.append(sentiment_analysis)
            
            features.fear_greed_index = sentiment_analysis.indicators.fear_greed_index
            
            # 轉換情緒為評分 (-1 到 1)
            sentiment_map = {
                MarketSentiment.EXTREME_FEAR: -0.8,
                MarketSentiment.FEAR: -0.4,
                MarketSentiment.NEUTRAL: 0.0,
                MarketSentiment.GREED: 0.4,
                MarketSentiment.EXTREME_GREED: 0.8
            }
            features.sentiment_score = sentiment_map.get(sentiment_analysis.sentiment, 0.0)
        except Exception as e:
            logger.warning(f"情緒分析失敗: {e}")
            features.fear_greed_index = 50.0
            features.sentiment_score = 0.0
        
        return features
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """計算ADX (平均趨向指數)"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # +DM and -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        plus_dm[plus_dm <= minus_dm] = 0
        minus_dm[minus_dm <= plus_dm] = 0
        
        # Smooth TR and DM
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * plus_dm.rolling(window=period).mean() / atr
        minus_di = 100 * minus_dm.rolling(window=period).mean() / atr
        
        # DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 25.0
    
    def _calculate_trend_strength(self, df: pd.DataFrame) -> float:
        """計算趨勢強度 (0-100)"""
        close = df['close']
        
        # 使用多個EMA的排列判斷趨勢
        ema_5 = close.ewm(span=5, adjust=False).mean()
        ema_10 = close.ewm(span=10, adjust=False).mean()
        ema_20 = close.ewm(span=20, adjust=False).mean()
        
        # 計算趨勢得分
        score = 50  # 中性
        
        # EMA排列
        if ema_5.iloc[-1] > ema_10.iloc[-1] > ema_20.iloc[-1]:
            score += 25
        elif ema_5.iloc[-1] < ema_10.iloc[-1] < ema_20.iloc[-1]:
            score -= 25
        
        # 價格相對於EMA的位置
        current_price = close.iloc[-1]
        if current_price > ema_5.iloc[-1]:
            score += 15
        else:
            score -= 15
        
        # 價格動量
        if len(close) >= 5:
            momentum = (current_price - close.iloc[-5]) / close.iloc[-5] * 100
            score += np.clip(momentum * 2, -20, 20)
        
        return np.clip(score, 0, 100)
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """計算ATR"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else 0.0
    
    def _calculate_historical_atr(self, df: pd.DataFrame, period: int = 60) -> float:
        """計算歷史ATR基準"""
        if len(df) < period:
            return self._calculate_atr(df, len(df) // 2)
        
        return self._calculate_atr(df, period)
    
    def _calculate_boll_bandwidth(self, df: pd.DataFrame, period: int = 20) -> float:
        """計算布林帶寬度"""
        close = df['close']
        
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        upper = middle + 2 * std
        lower = middle - 2 * std
        
        bandwidth = (upper - lower) / middle
        
        return bandwidth.iloc[-1] if not pd.isna(bandwidth.iloc[-1]) else 0.1
    
    def _detect_volatility_regime(self, atr_ratio: float) -> VolatilityRegime:
        """檢測波動率區間"""
        if atr_ratio < 0.8:
            return VolatilityRegime.LOW
        elif atr_ratio < 1.2:
            return VolatilityRegime.MEDIUM
        elif atr_ratio < 1.8:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.EXTREME
    
    def _calculate_regime_duration(self, current_regime: MarketRegime) -> int:
        """計算當前狀態持續時間"""
        duration = 1
        
        for state in reversed(self.regime_history):
            if state.regime == current_regime:
                duration += 1
            else:
                break
        
        return duration
    
    def get_regime_statistics(self, n_periods: int = 100) -> Dict[str, Any]:
        """
        獲取市場狀態統計
        
        Args:
            n_periods: 統計的歷史期數
            
        Returns:
            統計信息字典
        """
        if not self.regime_history:
            return {}
        
        recent_history = self.regime_history[-n_periods:]
        
        total = len(recent_history)
        if total == 0:
            return {}
        
        stats = {
            'total_periods': total,
            'current_regime': self.regime_history[-1].regime.value if self.regime_history else 'unknown',
            'current_confidence': self.regime_history[-1].confidence if self.regime_history else 0,
            'regime_distribution': {},
            'avg_duration': {}
        }
        
        # 計算各狀態分布
        for regime in MarketRegime:
            count = sum(1 for s in recent_history if s.regime == regime)
            stats['regime_distribution'][regime.value] = {
                'count': count,
                'percentage': count / total * 100
            }
        
        # 計算平均持續時間
        for regime in MarketRegime:
            durations = [s.duration for s in recent_history if s.regime == regime]
            if durations:
                stats['avg_duration'][regime.value] = np.mean(durations)
        
        return stats
    
    def predict_regime_change(self) -> Optional[MarketRegime]:
        """
        預測可能的狀態轉換
        
        Returns:
            預測的下一狀態或 None
        """
        if not self.regime_history:
            return None
        
        current = self.regime_history[-1]
        
        # 如果當前狀態持續時間過長，可能發生轉換
        if current.duration > 20:  # 閾值可調整
            # 基於轉移矩陣預測
            current_idx = self.hmm.state_names.index(current.regime)
            transition_probs = self.hmm.transition_matrix[current_idx]
            
            # 排除當前狀態，選擇概率最高的
            transition_probs[current_idx] = 0
            next_idx = np.argmax(transition_probs)
            
            if transition_probs[next_idx] > 0.3:  # 概率閾值
                return self.hmm.state_names[next_idx]
        
        return None
    
    def save_state(self, filepath: str):
        """保存檢測器狀態"""
        state = {
            'current_regime': self.hmm.current_state.value,
            'historical_volatility': self.historical_volatility,
            'regime_history': [
                {
                    'regime': s.regime.value,
                    'volatility_regime': s.volatility_regime.value,
                    'confidence': s.confidence,
                    'timestamp': s.timestamp.isoformat(),
                    'duration': s.duration
                }
                for s in self.regime_history[-100:]  # 只保存最近100條
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        logger.info(f"市場狀態檢測器狀態已保存: {filepath}")
    
    def load_state(self, filepath: str):
        """加載檢測器狀態"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            self.hmm.current_state = MarketRegime(state.get('current_regime', 'ranging'))
            self.historical_volatility = state.get('historical_volatility', 0.0)
            
            logger.info(f"市場狀態檢測器狀態已加載: {filepath}")
        except Exception as e:
            logger.error(f"加載狀態失敗: {e}")


class MultiTimeframeRegimeDetector:
    """
    多時間框架市場狀態檢測器
    
    同時監控多個時間框架的市場狀態
    """
    
    def __init__(self, timeframes: List[str] = None):
        """
        初始化
        
        Args:
            timeframes: 時間框架列表，如 ['15m', '1h', '1d']
        """
        self.timeframes = timeframes or ['15m', '1h', '1d']
        self.detectors: Dict[str, MarketRegimeDetector] = {
            tf: MarketRegimeDetector() for tf in self.timeframes
        }
        
        logger.info(f"多時間框架檢測器初始化: {timeframes}")
    
    def detect_all(self, data: Dict[str, pd.DataFrame]) -> Dict[str, RegimeState]:
        """
        檢測所有時間框架的市場狀態
        
        Args:
            data: 各時間框架的數據 {timeframe: df}
            
        Returns:
            各時間框架的市場狀態
        """
        results = {}
        
        for tf, df in data.items():
            if tf in self.detectors:
                results[tf] = self.detectors[tf].detect(df)
        
        return results
    
    def get_aligned_regime(self, data: Dict[str, pd.DataFrame]) -> Optional[MarketRegime]:
        """
        獲取多時間框架一致的市場狀態
        
        Returns:
            如果所有時間框架狀態一致，返回該狀態；否則返回 None
        """
        states = self.detect_all(data)
        
        if not states:
            return None
        
        regimes = [s.regime for s in states.values()]
        
        # 檢查是否全部一致
        if len(set(regimes)) == 1:
            return regimes[0]
        
        # 檢查是否為趨勢方向一致
        trending_up_count = sum(1 for r in regimes if r == MarketRegime.TRENDING_UP)
        trending_down_count = sum(1 for r in regimes if r == MarketRegime.TRENDING_DOWN)
        
        if trending_up_count == len(regimes):
            return MarketRegime.TRENDING_UP
        if trending_down_count == len(regimes):
            return MarketRegime.TRENDING_DOWN
        
        return None
    
    def get_regime_consensus(self, data: Dict[str, pd.DataFrame]) -> Tuple[MarketRegime, float]:
        """
        獲取市場狀態共識（投票機制）
        
        Returns:
            (共識狀態, 置信度)
        """
        states = self.detect_all(data)
        
        if not states:
            return MarketRegime.UNKNOWN, 0.0
        
        # 計算各狀態的加權得分
        weights = {'15m': 0.2, '1h': 0.3, '1d': 0.5}  # 長期框架權重更高
        scores = {regime: 0.0 for regime in MarketRegime}
        
        for tf, state in states.items():
            weight = weights.get(tf, 0.25)
            scores[state.regime] += weight * state.confidence
        
        # 選擇得分最高的狀態
        best_regime = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = scores[best_regime] / total_score if total_score > 0 else 0
        
        return best_regime, confidence


# 便捷函數
def detect_market_regime(df: pd.DataFrame, lookback: int = 20) -> RegimeState:
    """
    快速檢測市場狀態
    
    Args:
        df: 價格數據
        lookback: 回看週期
        
    Returns:
        市場狀態
    """
    detector = MarketRegimeDetector(lookback_period=lookback)
    return detector.detect(df)


def get_volatility_adjustment(regime: VolatilityRegime) -> Dict[str, float]:
    """
    獲取波動率調整係數
    
    Args:
        regime: 波動率區間
        
    Returns:
        調整係數字典
    """
    adjustments = {
        VolatilityRegime.LOW: {
            'position_scale': 1.5,
            'stop_loss_mult': 1.5,
            'take_profit_mult': 3.0,
            'max_positions': 1.5
        },
        VolatilityRegime.MEDIUM: {
            'position_scale': 1.0,
            'stop_loss_mult': 1.0,
            'take_profit_mult': 2.0,
            'max_positions': 1.0
        },
        VolatilityRegime.HIGH: {
            'position_scale': 0.5,
            'stop_loss_mult': 0.7,
            'take_profit_mult': 1.5,
            'max_positions': 0.6
        },
        VolatilityRegime.EXTREME: {
            'position_scale': 0.0,
            'stop_loss_mult': 0.5,
            'take_profit_mult': 1.0,
            'max_positions': 0.0
        }
    }
    
    return adjustments.get(regime, adjustments[VolatilityRegime.MEDIUM])
