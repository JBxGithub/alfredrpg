"""
RL 訓練器 - RL Trainer

訓練強化學習智能體
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd

from src.utils.logger import logger
from src.reinforcement_learning.trading_environment import TradingEnvironment, Action
from src.reinforcement_learning.rl_agent import RLAgent
from src.reinforcement_learning.reward_calculator import RewardCalculator


@dataclass
class TrainingConfig:
    """訓練配置"""
    episodes: int = 1000
    max_steps: int = 252  # 一年交易日
    learning_rate: float = 0.001
    batch_size: int = 32
    save_interval: int = 100
    eval_interval: int = 50


@dataclass
class TrainingMetrics:
    """訓練指標"""
    episode: int
    total_reward: float
    final_value: float
    trades_count: int
    sharpe_ratio: float
    max_drawdown: float
    epsilon: float


class RLTrainer:
    """
    強化學習訓練器
    
    負責：
    - 訓練循環管理
    - 評估和驗證
    - 模型保存和加載
    """
    
    def __init__(
        self,
        env: TradingEnvironment,
        agent: RLAgent,
        config: TrainingConfig = None
    ):
        """
        初始化
        
        Args:
            env: 交易環境
            agent: RL 智能體
            config: 訓練配置
        """
        self.env = env
        self.agent = agent
        self.config = config or TrainingConfig()
        
        self.reward_calc = RewardCalculator()
        self.metrics_history: List[TrainingMetrics] = []
        self.best_performance = -float('inf')
        
        self.is_training = False
    
    async def train(self) -> List[TrainingMetrics]:
        """
        訓練主循環
        
        Returns:
            訓練歷史
        """
        self.is_training = True
        logger.info(f"🚀 開始訓練: {self.config.episodes} episodes")
        
        for episode in range(self.config.episodes):
            if not self.is_training:
                break
            
            # 運行一個 episode
            metrics = await self._run_episode(episode)
            self.metrics_history.append(metrics)
            
            # 記錄進度
            if episode % 10 == 0:
                logger.info(
                    f"Episode {episode}: "
                    f"Reward={metrics.total_reward:.3f}, "
                    f"Value=${metrics.final_value:,.2f}, "
                    f"Trades={metrics.trades_count}"
                )
            
            # 評估
            if episode % self.config.eval_interval == 0 and episode > 0:
                await self._evaluate(episode)
            
            # 保存最佳模型
            if metrics.final_value > self.best_performance:
                self.best_performance = metrics.final_value
                if episode % self.config.save_interval == 0:
                    self._save_model(f"best_model_ep{episode}.pkl")
        
        logger.info("✅ 訓練完成")
        self.is_training = False
        
        return self.metrics_history
    
    async def _run_episode(self, episode: int) -> TrainingMetrics:
        """
        運行一個訓練 episode
        
        Args:
            episode: Episode 編號
            
        Returns:
            TrainingMetrics: 訓練指標
        """
        # 重置環境和計算器
        state = self.env.reset()
        self.reward_calc.reset()
        
        total_reward = 0.0
        step = 0
        
        while step < self.config.max_steps:
            # 選擇動作
            action_idx = self.agent.select_action(state, training=True)
            action = Action(action_idx)
            
            # 執行動作
            next_state, env_reward, done, info = self.env.step(action)
            
            # 計算獎勵
            reward_components = self.reward_calc.calculate(
                current_value=info['portfolio_value'],
                previous_value=self.env.portfolio_value - env_reward * self.env.initial_capital,
                position=info['position'],
                step=step,
                info=info
            )
            
            # 存儲經驗
            self.agent.store_experience(
                state=state,
                action=action_idx,
                reward=reward_components.total_reward,
                next_state=next_state,
                done=done
            )
            
            # 訓練
            if step % 4 == 0:  # 每 4 步訓練一次
                self.agent.train()
            
            total_reward += reward_components.total_reward
            state = next_state
            step += 1
            
            if done:
                break
        
        # 獲取表現
        perf = self.env.get_performance()
        reward_stats = self.reward_calc.get_statistics()
        
        return TrainingMetrics(
            episode=episode,
            total_reward=total_reward,
            final_value=perf['final_value'],
            trades_count=perf['trades_count'],
            sharpe_ratio=reward_stats['sharpe_ratio'],
            max_drawdown=reward_stats.get('max_drawdown', 0),
            epsilon=self.agent.epsilon
        )
    
    async def _evaluate(self, episode: int):
        """
        評估當前模型
        
        Args:
            episode: 當前 episode
        """
        logger.info(f"🔍 Episode {episode}: 評估模型...")
        
        # 運行幾個測試 episode（無探索）
        test_rewards = []
        for _ in range(5):
            state = self.env.reset()
            episode_reward = 0
            
            for _ in range(self.config.max_steps):
                action_idx = self.agent.select_action(state, training=False)
                state, reward, done, _ = self.env.step(Action(action_idx))
                episode_reward += reward
                
                if done:
                    break
            
            test_rewards.append(episode_reward)
        
        avg_reward = np.mean(test_rewards)
        logger.info(f"   平均測試獎勵: {avg_reward:.3f}")
    
    def _save_model(self, filename: str):
        """保存模型"""
        import os
        save_dir = "models/rl"
        os.makedirs(save_dir, exist_ok=True)
        
        filepath = f"{save_dir}/{filename}"
        self.agent.save(filepath)
        logger.info(f"💾 模型已保存: {filepath}")
    
    def stop(self):
        """停止訓練"""
        self.is_training = False
        logger.info("🛑 訓練已停止")
    
    def get_training_summary(self) -> Dict[str, Any]:
        """獲取訓練摘要"""
        if not self.metrics_history:
            return {}
        
        recent = self.metrics_history[-10:]
        
        return {
            'total_episodes': len(self.metrics_history),
            'avg_final_value': np.mean([m.final_value for m in recent]),
            'avg_reward': np.mean([m.total_reward for m in recent]),
            'avg_trades': np.mean([m.trades_count for m in recent]),
            'best_performance': self.best_performance,
            'current_epsilon': self.agent.epsilon
        }
