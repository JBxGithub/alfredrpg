"""
強化學習智能體 - RL Agent

使用 Deep Q-Network (DQN) 進行學習
"""

import numpy as np
import random
from typing import List, Tuple, Dict, Any
from collections import deque
from dataclasses import dataclass

from src.utils.logger import logger


@dataclass
class Experience:
    """經驗回放"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class DQNNetwork:
    """
    簡化版 DQN 網絡
    
    實際使用時可替換為 TensorFlow/PyTorch
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 64
    ):
        """
        初始化
        
        Args:
            state_dim: 狀態維度
            action_dim: 動作維度
            hidden_dim: 隱藏層維度
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # 簡化版：使用隨機權重（實際應使用神經網絡）
        self.weights1 = np.random.randn(state_dim, hidden_dim) * 0.1
        self.bias1 = np.zeros(hidden_dim)
        self.weights2 = np.random.randn(hidden_dim, action_dim) * 0.1
        self.bias2 = np.zeros(action_dim)
    
    def forward(self, state: np.ndarray) -> np.ndarray:
        """
        前向傳播
        
        Args:
            state: 狀態
            
        Returns:
            Q 值
        """
        # 隱藏層
        hidden = np.maximum(0, np.dot(state, self.weights1) + self.bias1)
        # 輸出層
        output = np.dot(hidden, self.weights2) + self.bias2
        return output
    
    def get_action(self, state: np.ndarray) -> int:
        """獲取最佳動作"""
        q_values = self.forward(state)
        return int(np.argmax(q_values))


class RLAgent:
    """
    強化學習智能體
    
    使用 DQN 算法學習最優交易策略
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int = 4,  # HOLD, BUY, SELL, CLOSE
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
        memory_size: int = 10000,
        batch_size: int = 32
    ):
        """
        初始化
        
        Args:
            state_dim: 狀態維度
            action_dim: 動作維度
            learning_rate: 學習率
            gamma: 折扣因子
            epsilon: 探索率
            epsilon_decay: 探索衰減
            epsilon_min: 最小探索率
            memory_size: 經驗回放大小
            batch_size: 批次大小
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.batch_size = batch_size
        
        # 網絡
        self.policy_net = DQNNetwork(state_dim, action_dim)
        self.target_net = DQNNetwork(state_dim, action_dim)
        
        # 經驗回放
        self.memory: deque = deque(maxlen=memory_size)
        
        # 訓練統計
        self.training_step = 0
        self.losses: List[float] = []
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        選擇動作 (ε-貪婪)
        
        Args:
            state: 當前狀態
            training: 是否訓練模式
            
        Returns:
            動作索引
        """
        if training and random.random() < self.epsilon:
            # 探索：隨機選擇
            return random.randrange(self.action_dim)
        else:
            # 利用：選擇最佳動作
            return self.policy_net.get_action(state)
    
    def store_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """
        存儲經驗
        
        Args:
            state: 當前狀態
            action: 動作
            reward: 獎勵
            next_state: 下一狀態
            done: 是否結束
        """
        exp = Experience(state, action, reward, next_state, done)
        self.memory.append(exp)
    
    def train(self) -> float:
        """
        訓練一步
        
        Returns:
            loss: 損失值
        """
        if len(self.memory) < self.batch_size:
            return 0.0
        
        # 採樣批次
        batch = random.sample(self.memory, self.batch_size)
        
        # 簡化版訓練（實際應使用梯度下降）
        loss = self._simplified_train(batch)
        
        # 衰減探索率
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        # 更新目標網絡
        if self.training_step % 100 == 0:
            self._update_target_network()
        
        self.training_step += 1
        self.losses.append(loss)
        
        return loss
    
    def _simplified_train(self, batch: List[Experience]) -> float:
        """
        簡化版訓練
        
        實際應使用反向傳播優化網絡權重
        """
        total_loss = 0.0
        
        for exp in batch:
            # 當前 Q 值
            current_q = self.policy_net.forward(exp.state)[exp.action]
            
            # 目標 Q 值
            if exp.done:
                target_q = exp.reward
            else:
                next_q = self.target_net.forward(exp.next_state)
                target_q = exp.reward + self.gamma * np.max(next_q)
            
            # 計算損失
            loss = (current_q - target_q) ** 2
            total_loss += loss
        
        return total_loss / len(batch)
    
    def _update_target_network(self):
        """更新目標網絡"""
        # 簡化版：直接複製（實際應使用軟更新）
        self.target_net = self.policy_net
        logger.debug("目標網絡已更新")
    
    def get_action_distribution(self, state: np.ndarray) -> Dict[int, float]:
        """
        獲取動作分佈
        
        Args:
            state: 狀態
            
        Returns:
            各動作概率
        """
        q_values = self.policy_net.forward(state)
        
        # Softmax
        exp_q = np.exp(q_values - np.max(q_values))
        probs = exp_q / exp_q.sum()
        
        return {i: probs[i] for i in range(self.action_dim)}
    
    def save(self, filepath: str):
        """保存模型"""
        import pickle
        
        state = {
            'policy_weights': {
                'w1': self.policy_net.weights1,
                'b1': self.policy_net.bias1,
                'w2': self.policy_net.weights2,
                'b2': self.policy_net.bias2,
            },
            'epsilon': self.epsilon,
            'training_step': self.training_step
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(state, f)
        
        logger.info(f"模型已保存: {filepath}")
    
    def load(self, filepath: str):
        """加載模型"""
        import pickle
        
        with open(filepath, 'rb') as f:
            state = pickle.load(f)
        
        self.policy_net.weights1 = state['policy_weights']['w1']
        self.policy_net.bias1 = state['policy_weights']['b1']
        self.policy_net.weights2 = state['policy_weights']['w2']
        self.policy_net.bias2 = state['policy_weights']['b2']
        
        self.epsilon = state['epsilon']
        self.training_step = state['training_step']
        
        self._update_target_network()
        
        logger.info(f"模型已加載: {filepath}")
