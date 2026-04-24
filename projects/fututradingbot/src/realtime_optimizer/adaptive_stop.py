"""
自適應止損管理器 - Adaptive Stop Manager

根據市場波動和表現動態調整止損/止盈
"""

import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from src.utils.logger import logger


class StopType(Enum):
    """止損類型"""
    FIXED = "fixed"           # 固定百分比
    ATR_BASED = "atr"         # ATR 基於
    VOLATILITY = "volatility" # 波動率基於
    TRAILING = "trailing"     # 追踪止損


@dataclass
class StopLevel:
    """止損水平"""
    entry_price: float
    current_stop: float
    current_target: float
    stop_type: StopType
    atr_value: Optional[float] = None


class AdaptiveStopManager:
    """
    自適應止損管理器
    
    功能：
    - 根據 ATR 動態調整止損
    - 追踪止損 (Trailing Stop)
    - 根據勝率調整止盈距離
    """
    
    def __init__(
        self,
        base_stop_pct: float = 0.02,
        base_target_pct: float = 0.04,
        atr_multiplier: float = 2.0,
        trailing_activation: float = 0.02
    ):
        """
        初始化
        
        Args:
            base_stop_pct: 基礎止損百分比
            base_target_pct: 基礎止盈百分比
            atr_multiplier: ATR 乘數
            trailing_activation: 追踪止損激活閾值
        """
        self.base_stop_pct = base_stop_pct
        self.base_target_pct = base_target_pct
        self.atr_multiplier = atr_multiplier
        self.trailing_activation = trailing_activation
        
        self.positions: Dict[str, StopLevel] = {}
        self.adjustment_history: List[Dict] = []
    
    def add_position(
        self,
        position_id: str,
        entry_price: float,
        direction: str,  # 'long' or 'short'
        atr: Optional[float] = None,
        stop_type: StopType = StopType.FIXED
    ) -> StopLevel:
        """
        添加持倉並計算止損/止盈
        
        Args:
            position_id: 持倉 ID
            entry_price: 入場價
            direction: 方向
            atr: ATR 值
            stop_type: 止損類型
            
        Returns:
            StopLevel: 止損水平
        """
        if stop_type == StopType.ATR_BASED and atr:
            stop_distance = atr * self.atr_multiplier
            target_distance = atr * self.atr_multiplier * 2
        else:
            stop_distance = entry_price * self.base_stop_pct
            target_distance = entry_price * self.base_target_pct
        
        if direction == 'long':
            stop_price = entry_price - stop_distance
            target_price = entry_price + target_distance
        else:  # short
            stop_price = entry_price + stop_distance
            target_price = entry_price - target_distance
        
        level = StopLevel(
            entry_price=entry_price,
            current_stop=stop_price,
            current_target=target_price,
            stop_type=stop_type,
            atr_value=atr
        )
        
        self.positions[position_id] = level
        
        logger.info(
            f"添加持倉 {position_id}: 止損=${level.current_stop:.2f}, "
            f"止盈=${level.current_target:.2f}"
        )
        
        return level
    
    def update_trailing_stop(
        self,
        position_id: str,
        current_price: float,
        direction: str
    ) -> Optional[float]:
        """
        更新追踪止損
        
        Args:
            position_id: 持倉 ID
            current_price: 當前價格
            direction: 方向
            
        Returns:
            新的止損價或 None
        """
        if position_id not in self.positions:
            return None
        
        level = self.positions[position_id]
        
        # 計算盈利百分比
        if direction == 'long':
            profit_pct = (current_price - level.entry_price) / level.entry_price
            
            # 如果盈利超過激活閾值，啟動追踪止損
            if profit_pct > self.trailing_activation:
                # 追踪止損設置在最高價下方 base_stop_pct
                new_stop = current_price * (1 - self.base_stop_pct)
                
                # 只上移，不下移
                if new_stop > level.current_stop:
                    old_stop = level.current_stop
                    level.current_stop = new_stop
                    
                    logger.info(
                        f"追踪止損上移 {position_id}: ${old_stop:.2f} -> ${new_stop:.2f}"
                    )
                    
                    self.adjustment_history.append({
                        'position_id': position_id,
                        'old_stop': old_stop,
                        'new_stop': new_stop,
                        'current_price': current_price,
                        'profit_pct': profit_pct
                    })
                    
                    return new_stop
        
        else:  # short
            profit_pct = (level.entry_price - current_price) / level.entry_price
            
            if profit_pct > self.trailing_activation:
                new_stop = current_price * (1 + self.base_stop_pct)
                
                if new_stop < level.current_stop:
                    old_stop = level.current_stop
                    level.current_stop = new_stop
                    
                    logger.info(
                        f"追踪止損下移 {position_id}: ${old_stop:.2f} -> ${new_stop:.2f}"
                    )
                    
                    return new_stop
        
        return None
    
    def adjust_for_win_rate(self, win_rate: float):
        """
        根據勝率調整止損/止盈距離
        
        Args:
            win_rate: 當前勝率
        """
        if win_rate > 0.6:
            # 勝率高，可以放寬止損，提高止盈
            self.base_stop_pct = min(0.03, self.base_stop_pct * 1.1)
            self.base_target_pct = min(0.08, self.base_target_pct * 1.1)
            logger.info(f"勝率良好 ({win_rate:.1%}), 放寬止損/止盈")
            
        elif win_rate < 0.4:
            # 勝率低，收緊止損，降低止盈期望
            self.base_stop_pct = max(0.01, self.base_stop_pct * 0.9)
            self.base_target_pct = max(0.02, self.base_target_pct * 0.9)
            logger.info(f"勝率偏低 ({win_rate:.1%}), 收緊止損/止盈")
    
    def check_stop_triggered(
        self,
        position_id: str,
        current_price: float,
        direction: str
    ) -> Optional[str]:
        """
        檢查是否觸發止損/止盈
        
        Returns:
            'stop_loss', 'take_profit', or None
        """
        if position_id not in self.positions:
            return None
        
        level = self.positions[position_id]
        
        if direction == 'long':
            if current_price <= level.current_stop:
                return 'stop_loss'
            elif current_price >= level.current_target:
                return 'take_profit'
        else:  # short
            if current_price >= level.current_stop:
                return 'stop_loss'
            elif current_price <= level.current_target:
                return 'take_profit'
        
        return None
    
    def remove_position(self, position_id: str):
        """移除持倉"""
        if position_id in self.positions:
            del self.positions[position_id]
            logger.info(f"移除持倉 {position_id}")
    
    def get_position_stops(self, position_id: str) -> Optional[StopLevel]:
        """獲取持倉止損信息"""
        return self.positions.get(position_id)
