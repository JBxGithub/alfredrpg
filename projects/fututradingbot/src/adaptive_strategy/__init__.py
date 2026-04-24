"""
自適應策略切換系統 - Adaptive Strategy Switcher

功能：
- 監測市場狀態（趨勢/震盪/高波動）
- 自動切換最適合的策略
- 策略權重動態調整
- 多策略組合優化

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

from .market_regime_detector import MarketRegimeDetector, MarketRegime, RegimeMetrics
from .strategy_selector import StrategySelector, StrategyScore
from .strategy_orchestrator import StrategyOrchestrator, StrategyAllocation
from .multi_strategy_engine import MultiStrategyEngine, EngineConfig

__all__ = [
    'MarketRegimeDetector',
    'MarketRegime',
    'RegimeMetrics',
    'StrategySelector',
    'StrategyScore',
    'StrategyOrchestrator',
    'StrategyAllocation',
    'MultiStrategyEngine',
    'EngineConfig'
]
