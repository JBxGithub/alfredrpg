"""
實時策略優化器

功能：
- 實時監控交易表現
- 自動調整策略參數
- 動態倉位管理
- 自適應止損/止盈

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

from .performance_tracker import PerformanceTracker, PerformanceMetrics, TradeRecord
from .parameter_adjuster import ParameterAdjuster
from .adaptive_stop import AdaptiveStopManager, StopLevel
from .strategy_evolver import StrategyEvolver, StrategyGene

__all__ = [
    'PerformanceTracker',
    'PerformanceMetrics',
    'TradeRecord',
    'ParameterAdjuster',
    'AdaptiveStopManager',
    'StopLevel',
    'StrategyEvolver',
    'StrategyGene'
]
