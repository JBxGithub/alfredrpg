"""
參數調整器 - Parameter Adjuster

根據表現自動調整策略參數
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import numpy as np

from src.utils.logger import logger
from src.realtime_optimizer.performance_tracker import PerformanceTracker, PerformanceMetrics


@dataclass
class AdjustmentRule:
    """調整規則"""
    name: str
    condition: str  # 條件描述
    parameter: str  # 要調整的參數
    adjustment: float  # 調整幅度 (例如 0.9 = 減少10%)
    min_value: float  # 最小值
    max_value: float  # 最大值


class ParameterAdjuster:
    """
    參數調整器
    
    根據實時表現自動調整：
    - 倉位大小
    - 止損位
    - 止盈位
    - 策略閾值
    """
    
    def __init__(self):
        self.current_params: Dict[str, Any] = {}
        self.adjustment_history: list = []
        self.base_params: Dict[str, Any] = {}
        
        # 預設調整規則
        self.rules = [
            AdjustmentRule(
                name='降低倉位（低勝率）',
                condition='recent_win_rate < 0.4',
                parameter='position_size',
                adjustment=0.8,  # 減少20%
                min_value=0.01,
                max_value=1.0
            ),
            AdjustmentRule(
                name='降低倉位（高回撤）',
                condition='max_drawdown > 0.10',
                parameter='position_size',
                adjustment=0.7,
                min_value=0.01,
                max_value=1.0
            ),
            AdjustmentRule(
                name='收緊止損',
                condition='avg_loss < -avg_profit * 1.5',
                parameter='stop_loss_pct',
                adjustment=0.85,
                min_value=0.005,
                max_value=0.10
            ),
            AdjustmentRule(
                name='放寬止損',
                condition='frequent_stop_loss',
                parameter='stop_loss_pct',
                adjustment=1.15,
                min_value=0.005,
                max_value=0.10
            ),
            AdjustmentRule(
                name='提高止盈',
                condition='win_rate > 0.6 and profit_factor > 2',
                parameter='take_profit_pct',
                adjustment=1.1,
                min_value=0.01,
                max_value=0.20
            )
        ]
    
    def initialize(self, base_params: Dict[str, Any]):
        """
        初始化參數
        
        Args:
            base_params: 基礎參數配置
        """
        self.base_params = base_params.copy()
        self.current_params = base_params.copy()
        logger.info(f"參數調整器已初始化: {list(base_params.keys())}")
    
    def adjust(self, tracker: PerformanceTracker) -> Dict[str, Any]:
        """
        根據表現調整參數
        
        Args:
            tracker: 表現追踪器
            
        Returns:
            調整後的參數
        """
        metrics = tracker.get_metrics()
        suggestions = tracker.get_adjustment_suggestions()
        
        adjustments_made = []
        
        # 根據建議調整
        if suggestions['reduce_position_size']:
            new_size = self._adjust_parameter(
                'position_size', 0.8,
                self.rules[0].min_value, self.rules[0].max_value
            )
            adjustments_made.append(f"倉位調整: {self.current_params.get('position_size', 'N/A')} -> {new_size}")
        
        if suggestions['tighten_stop_loss']:
            new_sl = self._adjust_parameter(
                'stop_loss_pct', 0.85,
                self.rules[2].min_value, self.rules[2].max_value
            )
            adjustments_made.append(f"止損收緊: {self.current_params.get('stop_loss_pct', 'N/A')} -> {new_sl}")
        
        if suggestions['widen_stop_loss']:
            new_sl = self._adjust_parameter(
                'stop_loss_pct', 1.15,
                self.rules[3].min_value, self.rules[3].max_value
            )
            adjustments_made.append(f"止損放寬: {self.current_params.get('stop_loss_pct', 'N/A')} -> {new_sl}")
        
        # 根據表現指標調整
        if metrics.win_rate > 0.6 and metrics.profit_factor > 2:
            # 表現良好，可以稍微提高倉位
            new_size = self._adjust_parameter(
                'position_size', 1.05,
                0.01, 1.0
            )
            adjustments_made.append(f"表現良好，倉位提升: {new_size}")
        
        # 記錄調整
        if adjustments_made:
            self.adjustment_history.append({
                'timestamp': datetime.now().isoformat(),
                'adjustments': adjustments_made,
                'params': self.current_params.copy()
            })
            logger.info(f"參數調整完成: {adjustments_made}")
        
        return self.current_params
    
    def _adjust_parameter(self, param_name: str, factor: float, 
                          min_val: float, max_val: float) -> float:
        """
        調整單個參數
        
        Args:
            param_name: 參數名稱
            factor: 調整因子
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            調整後的值
        """
        current = self.current_params.get(param_name, self.base_params.get(param_name, 0.1))
        new_value = current * factor
        new_value = np.clip(new_value, min_val, max_val)
        self.current_params[param_name] = new_value
        return new_value
    
    def reset_to_base(self):
        """重置為基礎參數"""
        self.current_params = self.base_params.copy()
        logger.info("參數已重置為基礎值")
    
    def get_current_params(self) -> Dict[str, Any]:
        """獲取當前參數"""
        return self.current_params.copy()
    
    def get_adjustment_history(self) -> list:
        """獲取調整歷史"""
        return self.adjustment_history


# 導入 datetime 用於記錄時間
from datetime import datetime
