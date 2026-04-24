"""
強化學習模組 - Reinforcement Learning

功能：
- 使用 RL 自動學習最優參數
- 持續從交易結果學習
- 自動探索新策略組合

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

from .trading_environment import TradingEnvironment, Action, State
from .rl_agent import RLAgent, Experience
from .reward_calculator import RewardCalculator, RewardComponents
from .rl_trainer import RLTrainer, TrainingConfig, TrainingMetrics

__all__ = [
    'TradingEnvironment',
    'Action',
    'State',
    'RLAgent',
    'Experience',
    'RewardCalculator',
    'RewardComponents',
    'RLTrainer',
    'TrainingConfig',
    'TrainingMetrics'
]
