"""
獎勵計算器 - Reward Calculator

計算強化學習的獎勵函數
"""

import numpy as np
from typing import Dict, Any, List
from dataclasses import dataclass

from src.utils.logger import logger


@dataclass
class RewardComponents:
    """獎勵組件"""
    pnl_reward: float          # 盈虧獎勵
    risk_penalty: float        # 風險懲罰
    consistency_bonus: float   # 一致性獎勵
    drawdown_penalty: float    # 回撤懲罰
    total_reward: float


class RewardCalculator:
    """
    獎勵計算器
    
    設計原則：
    1. 鼓勵盈利
    2. 懲罰過度風險
    3. 獎勵一致性
    4. 懲罰大回撤
    """
    
    def __init__(
        self,
        pnl_weight: float = 1.0,
        risk_weight: float = 0.5,
        consistency_weight: float = 0.3,
        drawdown_weight: float = 0.8,
        sharpe_weight: float = 0.4
    ):
        """
        初始化
        
        Args:
            pnl_weight: 盈虧權重
            risk_weight: 風險權重
            consistency_weight: 一致性權重
            drawdown_weight: 回撤權重
            sharpe_weight: 夏普比率權重
        """
        self.pnl_weight = pnl_weight
        self.risk_weight = risk_weight
        self.consistency_weight = consistency_weight
        self.drawdown_weight = drawdown_weight
        self.sharpe_weight = sharpe_weight
        
        # 歷史記錄
        self.returns_history: List[float] = []
        self.max_drawdown = 0.0
        self.peak_value = 0.0
    
    def calculate(
        self,
        current_value: float,
        previous_value: float,
        position: int,
        step: int,
        info: Dict[str, Any] = None
    ) -> RewardComponents:
        """
        計算獎勵
        
        Args:
            current_value: 當前組合價值
            previous_value: 上一步價值
            position: 當前持倉
            step: 步數
            info: 附加信息
            
        Returns:
            RewardComponents: 獎勵組件
        """
        # 1. 盈虧獎勵
        pnl = (current_value - previous_value) / previous_value
        pnl_reward = np.tanh(pnl * 10) * self.pnl_weight  # 使用 tanh 壓縮
        
        # 2. 風險懲罰 (持倉時間過長)
        risk_penalty = 0.0
        if position != 0:
            holding_period = info.get('holding_period', 0) if info else 0
            if holding_period > 20:  # 持倉超過 20 步
                risk_penalty = -0.01 * self.risk_weight
        
        # 3. 一致性獎勵
        self.returns_history.append(pnl)
        if len(self.returns_history) > 10:
            self.returns_history.pop(0)
        
        consistency_bonus = 0.0
        if len(self.returns_history) >= 5:
            # 獎勵穩定的正收益
            recent_returns = self.returns_history[-5:]
            if all(r > 0 for r in recent_returns):
                consistency_bonus = 0.05 * self.consistency_weight
        
        # 4. 回撤懲罰
        if current_value > self.peak_value:
            self.peak_value = current_value
        
        drawdown = (self.peak_value - current_value) / self.peak_value if self.peak_value > 0 else 0
        self.max_drawdown = max(self.max_drawdown, drawdown)
        
        drawdown_penalty = 0.0
        if drawdown > 0.05:  # 回撤超過 5%
            drawdown_penalty = -drawdown * 2 * self.drawdown_weight
        
        # 5. 夏普比率獎勵 (長期)
        sharpe_bonus = 0.0
        if len(self.returns_history) >= 20:
            sharpe = self._calculate_sharpe()
            if sharpe > 1.0:
                sharpe_bonus = 0.1 * self.sharpe_weight
        
        # 總獎勵
        total = pnl_reward + risk_penalty + consistency_bonus + drawdown_penalty + sharpe_bonus
        
        return RewardComponents(
            pnl_reward=pnl_reward,
            risk_penalty=risk_penalty,
            consistency_bonus=consistency_bonus,
            drawdown_penalty=drawdown_penalty,
            total_reward=total
        )
    
    def _calculate_sharpe(self) -> float:
        """計算夏普比率"""
        if len(self.returns_history) < 2:
            return 0.0
        
        returns = np.array(self.returns_history)
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        # 假設無風險利率為 0
        return mean_return / std_return * np.sqrt(252)  # 年化
    
    def reset(self):
        """重置計算器"""
        self.returns_history = []
        self.max_drawdown = 0.0
        self.peak_value = 0.0
    
    def get_statistics(self) -> Dict[str, float]:
        """獲取統計信息"""
        return {
            'max_drawdown': self.max_drawdown,
            'avg_return': np.mean(self.returns_history) if self.returns_history else 0,
            'return_std': np.std(self.returns_history) if self.returns_history else 0,
            'sharpe_ratio': self._calculate_sharpe()
        }
