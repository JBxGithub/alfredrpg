"""
策略模組
Strategy Module

提供交易策略實現:
- BaseStrategy: 策略基類
- TrendStrategy: 趨勢跟蹤策略
- StrategyConfigManager: 策略配置管理
- BacktestEngine: 回測引擎
"""

from src.strategies.base import (
    BaseStrategy,
    StrategyManager,
    TradeSignal,
    SignalType
)

from src.strategies.trend_strategy import (
    TrendStrategy,
    TrendState,
    PositionState,
    TrendAnalysis,
    EntryCondition,
    ExitCondition,
    PositionSizing
)

from src.strategies.strategy_config import (
    StrategyConfigManager,
    TrendStrategyConfig,
    RiskManagementConfig,
    BacktestConfig,
    get_config_manager
)

from src.strategies.backtest import (
    BacktestEngine,
    BacktestResult,
    BacktestOrder,
    BacktestPosition,
    BacktestTrade,
    WalkForwardAnalysis
)

__all__ = [
    # 基類
    'BaseStrategy',
    'StrategyManager',
    'TradeSignal',
    'SignalType',
    
    # 趨勢策略
    'TrendStrategy',
    'TrendState',
    'PositionState',
    'TrendAnalysis',
    'EntryCondition',
    'ExitCondition',
    'PositionSizing',
    
    # 配置管理
    'StrategyConfigManager',
    'TrendStrategyConfig',
    'RiskManagementConfig',
    'BacktestConfig',
    'get_config_manager',
    
    # 回測
    'BacktestEngine',
    'BacktestResult',
    'BacktestOrder',
    'BacktestPosition',
    'BacktestTrade',
    'WalkForwardAnalysis'
]
