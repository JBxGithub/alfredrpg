"""
交易環境 - Trading Environment

強化學習的環境模擬
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from src.utils.logger import logger


class Action(Enum):
    """交易動作"""
    HOLD = 0
    BUY = 1
    SELL = 2
    CLOSE = 3


@dataclass
class State:
    """環境狀態"""
    price: float
    position: int  # -1, 0, 1
    pnl: float
    features: np.ndarray


class TradingEnvironment:
    """
    交易環境
    
    強化學習的交互環境：
    - 接收動作 (Action)
    - 返回新狀態 (State)
    - 計算獎勵 (Reward)
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        initial_capital: float = 100000.0,
        commission: float = 0.001,
        max_position: int = 1
    ):
        """
        初始化
        
        Args:
            data: 歷史數據
            initial_capital: 初始資金
            commission: 手續費率
            max_position: 最大持倉
        """
        self.data = data.reset_index(drop=True)
        self.initial_capital = initial_capital
        self.commission = commission
        self.max_position = max_position
        
        # 狀態
        self.current_step = 0
        self.position = 0
        self.cash = initial_capital
        self.portfolio_value = initial_capital
        self.trades: List[Dict] = []
        
        # 特徵數量
        self.feature_dim = self._calculate_feature_dim()
    
    def reset(self) -> np.ndarray:
        """
        重置環境
        
        Returns:
            初始狀態
        """
        self.current_step = 0
        self.position = 0
        self.cash = self.initial_capital
        self.portfolio_value = self.initial_capital
        self.trades = []
        
        return self._get_observation()
    
    def step(self, action: Action) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        執行一步
        
        Args:
            action: 動作
            
        Returns:
            (observation, reward, done, info)
        """
        # 執行動作
        reward = self._execute_action(action)
        
        # 前進一步
        self.current_step += 1
        done = self.current_step >= len(self.data) - 1
        
        # 獲取新狀態
        obs = self._get_observation()
        
        # 附加信息
        info = {
            'step': self.current_step,
            'position': self.position,
            'portfolio_value': self.portfolio_value,
            'cash': self.cash,
            'trades_count': len(self.trades)
        }
        
        return obs, reward, done, info
    
    def _execute_action(self, action: Action) -> float:
        """
        執行動作
        
        Returns:
            reward: 即時獎勵
        """
        current_price = self.data['close'].iloc[self.current_step]
        old_value = self.portfolio_value
        
        if action == Action.BUY and self.position < self.max_position:
            # 買入
            shares = self.cash * (1 - self.commission) / current_price
            self.cash = 0
            self.position += 1
            
            self.trades.append({
                'step': self.current_step,
                'action': 'buy',
                'price': current_price,
                'shares': shares
            })
            
        elif action == Action.SELL and self.position > -self.max_position:
            # 賣出 (做空)
            shares = self.initial_capital / current_price
            self.position -= 1
            
            self.trades.append({
                'step': self.current_step,
                'action': 'sell',
                'price': current_price,
                'shares': shares
            })
            
        elif action == Action.CLOSE and self.position != 0:
            # 平倉
            if self.position > 0:
                # 平多倉
                shares = sum(t['shares'] for t in self.trades if t['action'] == 'buy')
                self.cash = shares * current_price * (1 - self.commission)
            else:
                # 平空倉
                self.cash = self.initial_capital
            
            self.position = 0
            
            self.trades.append({
                'step': self.current_step,
                'action': 'close',
                'price': current_price
            })
        
        # 更新組合價值
        self._update_portfolio_value(current_price)
        
        # 計算獎勵 (組合價值變化)
        reward = (self.portfolio_value - old_value) / old_value
        
        return reward
    
    def _update_portfolio_value(self, current_price: float):
        """更新組合價值"""
        position_value = 0
        
        if self.position > 0:
            # 多倉
            shares = sum(t['shares'] for t in self.trades if t['action'] == 'buy')
            position_value = shares * current_price
        elif self.position < 0:
            # 空倉
            entry_price = self.trades[-1]['price'] if self.trades else current_price
            position_value = self.initial_capital + (entry_price - current_price) * \
                           (self.initial_capital / entry_price)
        
        self.portfolio_value = self.cash + position_value
    
    def _get_observation(self) -> np.ndarray:
        """
        獲取觀測狀態
        
        Returns:
            狀態向量
        """
        if self.current_step >= len(self.data):
            return np.zeros(self.feature_dim)
        
        row = self.data.iloc[self.current_step]
        
        # 構建特徵
        features = [
            row['open'] / row['close'] - 1,  # 開盤相對收盤
            row['high'] / row['close'] - 1,  # 最高相對收盤
            row['low'] / row['close'] - 1,   # 最低相對收盤
            row['volume'] / self.data['volume'].rolling(20).mean().iloc[self.current_step] - 1,
            self.position / self.max_position,  # 正規化持倉
            self.portfolio_value / self.initial_capital - 1,  # 累計收益
        ]
        
        # 添加技術指標 (如果有)
        for col in ['sma_10', 'sma_30', 'rsi', 'macd']:
            if col in row:
                features.append(row[col])
        
        return np.array(features, dtype=np.float32)
    
    def _calculate_feature_dim(self) -> int:
        """計算特徵維度"""
        # 基礎特徵 + 技術指標
        base_features = 6
        tech_features = sum(1 for col in ['sma_10', 'sma_30', 'rsi', 'macd'] 
                          if col in self.data.columns)
        return base_features + tech_features
    
    def get_performance(self) -> Dict[str, float]:
        """獲取交易表現"""
        total_return = (self.portfolio_value - self.initial_capital) / self.initial_capital
        
        # 計算夏普比率 (簡化版)
        if len(self.trades) > 1:
            returns = []
            for i in range(1, len(self.trades)):
                if self.trades[i]['action'] in ['close', 'sell']:
                    pnl = (self.trades[i]['price'] - self.trades[i-1]['price']) / \
                          self.trades[i-1]['price']
                    returns.append(pnl)
            
            sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252) if returns else 0
        else:
            sharpe = 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe,
            'trades_count': len(self.trades),
            'final_value': self.portfolio_value
        }
