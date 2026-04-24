"""
信號增強器 - Signal Enhancer

ML預測結果整合、動態權重調整、模型性能監控

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from src.strategies.base import TradeSignal, SignalType
from src.ml.feature_engineering import FeatureEngineer
from src.ml.model_trainer import ModelTrainer, ModelMetrics
from src.utils.logger import logger


class SignalConfidence(Enum):
    """信號信心級別"""
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 1.0


@dataclass
class EnhancedSignal:
    """增強後的信號"""
    original_signal: TradeSignal
    ml_confidence: float
    enhanced_strength: float
    risk_adjusted_size: int
    expected_return: float
    win_probability: float
    recommendation: str  # 'proceed', 'caution', 'reject'
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelPerformance:
    """模型性能記錄"""
    timestamp: datetime
    accuracy: float
    precision: float
    recall: float
    predictions_count: int
    correct_predictions: int
    avg_confidence: float


class SignalEnhancer:
    """
    信號增強器
    
    使用機器學習模型增強原始交易信號
    """
    
    def __init__(
        self,
        model_trainer: Optional[ModelTrainer] = None,
        confidence_threshold: float = 0.6,
        min_win_probability: float = 0.55
    ):
        """
        初始化信號增強器
        
        Args:
            model_trainer: 模型訓練器
            confidence_threshold: 信心閾值
            min_win_probability: 最小勝率要求
        """
        self.model_trainer = model_trainer or ModelTrainer()
        self.feature_engineer = FeatureEngineer()
        self.confidence_threshold = confidence_threshold
        self.min_win_probability = min_win_probability
        
        # 性能監控
        self.performance_history: List[ModelPerformance] = []
        self.prediction_log: List[Dict[str, Any]] = []
        
        # 動態權重
        self.base_ml_weight: float = 0.5
        self.base_strategy_weight: float = 0.5
        self.adaptive_weights: bool = True
        
        logger.info(f"信號增強器初始化 | ML權重: {self.base_ml_weight}, 策略權重: {self.base_strategy_weight}")
    
    def enhance_signal(
        self,
        signal: TradeSignal,
        df: pd.DataFrame,
        market_context: Optional[Dict[str, Any]] = None
    ) -> EnhancedSignal:
        """
        增強交易信號
        
        Args:
            signal: 原始交易信號
            df: 市場數據
            market_context: 市場上下文
            
        Returns:
            EnhancedSignal: 增強後的信號
        """
        # 提取特徵
        features = self.feature_engineer.extract_features(df)
        latest_features = features.iloc[-1:]
        
        # ML預測
        ml_confidence = self._get_ml_confidence(latest_features)
        
        # 計算原始信號強度
        original_strength = self._calculate_signal_strength(signal)
        
        # 動態權重調整
        ml_weight, strategy_weight = self._calculate_dynamic_weights()
        
        # 計算增強後的強度
        enhanced_strength = (
            ml_confidence * ml_weight +
            original_strength * strategy_weight
        )
        
        # 計算勝率
        win_probability = self._estimate_win_probability(
            enhanced_strength, ml_confidence, market_context
        )
        
        # 計算預期收益
        expected_return = self._estimate_expected_return(
            signal, win_probability, enhanced_strength
        )
        
        # 風險調整倉位
        risk_adjusted_size = self._calculate_risk_adjusted_size(
            signal, enhanced_strength, win_probability
        )
        
        # 生成建議
        recommendation = self._generate_recommendation(
            enhanced_strength, win_probability, ml_confidence
        )
        
        enhanced = EnhancedSignal(
            original_signal=signal,
            ml_confidence=ml_confidence,
            enhanced_strength=enhanced_strength,
            risk_adjusted_size=risk_adjusted_size,
            expected_return=expected_return,
            win_probability=win_probability,
            recommendation=recommendation,
            metadata={
                'ml_weight': ml_weight,
                'strategy_weight': strategy_weight,
                'original_strength': original_strength,
                'market_context': market_context
            }
        )
        
        # 記錄預測
        self._log_prediction(enhanced)
        
        return enhanced
    
    def _get_ml_confidence(self, features: pd.DataFrame) -> float:
        """獲取ML模型信心度"""
        if self.model_trainer.model is None:
            return 0.5  # 默認中性
        
        try:
            # 獲取預測概率
            proba = self.model_trainer.predict_proba(features)
            
            # 取最高概率作為信心度
            confidence = np.max(proba)
            
            return float(confidence)
        except Exception as e:
            logger.debug(f"ML預測失敗: {e}")
            return 0.5
    
    def _calculate_signal_strength(self, signal: TradeSignal) -> float:
        """計算原始信號強度"""
        base_strength = 0.5
        
        # 根據信號類型調整
        if signal.signal == SignalType.BUY:
            base_strength = 0.7
        elif signal.signal == SignalType.SELL:
            base_strength = 0.3
        
        # 根據元數據調整
        if signal.metadata:
            if 'factor_score' in signal.metadata:
                # 因子分數歸一化到 0-1
                factor_score = signal.metadata['factor_score']
                base_strength = min(max((factor_score + 100) / 200, 0), 1)
            
            if 'confidence' in signal.metadata:
                base_strength = (base_strength + signal.metadata['confidence']) / 2
        
        return base_strength
    
    def _calculate_dynamic_weights(self) -> Tuple[float, float]:
        """計算動態權重"""
        if not self.adaptive_weights or not self.performance_history:
            return self.base_ml_weight, self.base_strategy_weight
        
        # 根據近期性能調整權重
        recent_performances = self.performance_history[-10:]
        
        if len(recent_performances) < 5:
            return self.base_ml_weight, self.base_strategy_weight
        
        # 計算ML模型近期準確率
        ml_accuracy = np.mean([p.accuracy for p in recent_performances])
        
        # 根據準確率調整權重
        if ml_accuracy > 0.65:
            ml_weight = min(self.base_ml_weight + 0.1, 0.7)
        elif ml_accuracy < 0.5:
            ml_weight = max(self.base_ml_weight - 0.1, 0.3)
        else:
            ml_weight = self.base_ml_weight
        
        strategy_weight = 1 - ml_weight
        
        return ml_weight, strategy_weight
    
    def _estimate_win_probability(
        self,
        enhanced_strength: float,
        ml_confidence: float,
        market_context: Optional[Dict[str, Any]]
    ) -> float:
        """估計勝率"""
        base_probability = enhanced_strength
        
        # 根據市場上下文調整
        if market_context:
            # 波動率調整
            volatility = market_context.get('volatility', 0.2)
            if volatility > 0.3:  # 高波動降低勝率預期
                base_probability *= 0.9
            
            # 趨勢調整
            trend = market_context.get('trend', 'neutral')
            if trend == 'strong_uptrend' and enhanced_strength > 0.6:
                base_probability *= 1.05
            elif trend == 'strong_downtrend' and enhanced_strength < 0.4:
                base_probability *= 1.05
        
        return min(max(base_probability, 0.1), 0.95)
    
    def _estimate_expected_return(
        self,
        signal: TradeSignal,
        win_probability: float,
        enhanced_strength: float
    ) -> float:
        """估計預期收益"""
        # 從信號元數據獲取目標收益
        target_return = 0.03  # 默認3%
        
        if signal.metadata:
            if 'take_profit' in signal.metadata and 'entry_price' in signal.metadata:
                tp = signal.metadata['take_profit']
                entry = signal.metadata['entry_price']
                target_return = (tp - entry) / entry
            elif 'expected_return' in signal.metadata:
                target_return = signal.metadata['expected_return']
        
        # 計算預期收益
        expected_win = win_probability * target_return
        expected_loss = (1 - win_probability) * 0.02  # 假設2%平均虧損
        
        return expected_win - expected_loss
    
    def _calculate_risk_adjusted_size(
        self,
        signal: TradeSignal,
        enhanced_strength: float,
        win_probability: float
    ) -> int:
        """計算風險調整後的倉位"""
        base_size = signal.qty
        
        # 根據信心度調整
        confidence_factor = enhanced_strength
        
        # 根據勝率調整
        win_rate_factor = win_probability
        
        # 綜合調整因子
        adjustment_factor = (confidence_factor + win_rate_factor) / 2
        
        # 限制調整範圍 (0.5x - 1.5x)
        adjustment_factor = max(0.5, min(adjustment_factor * 1.2, 1.5))
        
        adjusted_size = int(base_size * adjustment_factor)
        
        return max(adjusted_size, 0)
    
    def _generate_recommendation(
        self,
        enhanced_strength: float,
        win_probability: float,
        ml_confidence: float
    ) -> str:
        """生成交易建議"""
        # 綜合評分
        composite_score = (enhanced_strength + win_probability + ml_confidence) / 3
        
        if composite_score > 0.75 and win_probability > self.min_win_probability + 0.1:
            return 'proceed'
        elif composite_score > 0.5 and win_probability > self.min_win_probability:
            return 'caution'
        else:
            return 'reject'
    
    def _log_prediction(self, enhanced: EnhancedSignal):
        """記錄預測"""
        self.prediction_log.append({
            'timestamp': datetime.now().isoformat(),
            'code': enhanced.original_signal.code,
            'signal_type': enhanced.original_signal.signal.value,
            'ml_confidence': enhanced.ml_confidence,
            'enhanced_strength': enhanced.enhanced_strength,
            'win_probability': enhanced.win_probability,
            'recommendation': enhanced.recommendation
        })
        
        # 限制日誌大小
        if len(self.prediction_log) > 1000:
            self.prediction_log = self.prediction_log[-500:]
    
    def update_performance(
        self,
        predictions: List[Dict[str, Any]],
        actual_results: List[bool]
    ):
        """
        更新模型性能
        
        Args:
            predictions: 預測記錄
            actual_results: 實際結果 (True/False)
        """
        if len(predictions) != len(actual_results):
            logger.warning("預測數量和實際結果數量不匹配")
            return
        
        correct = sum(1 for pred, actual in zip(predictions, actual_results) if pred['correct'] == actual)
        total = len(predictions)
        
        accuracy = correct / total if total > 0 else 0
        avg_confidence = np.mean([p['ml_confidence'] for p in predictions])
        
        performance = ModelPerformance(
            timestamp=datetime.now(),
            accuracy=accuracy,
            precision=0,  # 簡化計算
            recall=0,
            predictions_count=total,
            correct_predictions=correct,
            avg_confidence=avg_confidence
        )
        
        self.performance_history.append(performance)
        
        # 限制歷史記錄大小
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-50:]
        
        logger.info(f"性能更新 | 準確率: {accuracy:.2%}, 平均信心: {avg_confidence:.2%}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        if not self.performance_history:
            return {'status': 'no_data'}
        
        recent = self.performance_history[-10:]
        
        return {
            'recent_accuracy': np.mean([p.accuracy for p in recent]),
            'recent_avg_confidence': np.mean([p.avg_confidence for p in recent]),
            'total_predictions': sum(p.predictions_count for p in self.performance_history),
            'ml_weight': self.base_ml_weight,
            'strategy_weight': self.base_strategy_weight,
            'adaptive_enabled': self.adaptive_weights
        }
    
    def set_weights(self, ml_weight: float, strategy_weight: float):
        """設置權重"""
        self.base_ml_weight = ml_weight
        self.base_strategy_weight = strategy_weight
        self.adaptive_weights = False  # 手動設置時禁用自適應
        
        logger.info(f"權重已設置 | ML: {ml_weight}, 策略: {strategy_weight}")
    
    def enable_adaptive_weights(self, enable: bool = True):
        """啟用/禁用自適應權重"""
        self.adaptive_weights = enable
        logger.info(f"自適應權重: {'啟用' if enable else '禁用'}")


class SignalFilter:
    """
    信號過濾器
    
    基於ML預測過濾低質量信號
    """
    
    def __init__(
        self,
        enhancer: SignalEnhancer,
        min_confidence: float = 0.6,
        min_win_probability: float = 0.55
    ):
        self.enhancer = enhancer
        self.min_confidence = min_confidence
        self.min_win_probability = min_win_probability
        self.filtered_count: int = 0
        self.passed_count: int = 0
    
    def filter_signal(
        self,
        signal: TradeSignal,
        df: pd.DataFrame
    ) -> Optional[TradeSignal]:
        """
        過濾信號
        
        Args:
            signal: 原始信號
            df: 市場數據
            
        Returns:
            過濾後的信號或None
        """
        enhanced = self.enhancer.enhance_signal(signal, df)
        
        if enhanced.recommendation == 'reject':
            self.filtered_count += 1
            logger.debug(f"信號被過濾: {signal.code} | 信心: {enhanced.ml_confidence:.2%}")
            return None
        
        if enhanced.win_probability < self.min_win_probability:
            self.filtered_count += 1
            logger.debug(f"信號被過濾: {signal.code} | 勝率: {enhanced.win_probability:.2%}")
            return None
        
        self.passed_count += 1
        
        # 更新原始信號
        signal.qty = enhanced.risk_adjusted_size
        signal.metadata = signal.metadata or {}
        signal.metadata['enhanced'] = True
        signal.metadata['ml_confidence'] = enhanced.ml_confidence
        signal.metadata['win_probability'] = enhanced.win_probability
        
        return signal
    
    def get_filter_stats(self) -> Dict[str, int]:
        """獲取過濾統計"""
        return {
            'filtered': self.filtered_count,
            'passed': self.passed_count,
            'total': self.filtered_count + self.passed_count,
            'pass_rate': self.passed_count / (self.filtered_count + self.passed_count) if (self.filtered_count + self.passed_count) > 0 else 0
        }


# 便捷函數
def enhance_signal(
    signal: TradeSignal,
    df: pd.DataFrame,
    model_trainer: Optional[ModelTrainer] = None
) -> EnhancedSignal:
    """便捷函數：增強信號"""
    enhancer = SignalEnhancer(model_trainer)
    return enhancer.enhance_signal(signal, df)
