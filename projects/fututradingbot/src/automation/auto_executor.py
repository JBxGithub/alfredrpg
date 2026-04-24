"""
自動執行器 - Auto Executor

自動執行止損、止盈、倉位調整
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

try:
    from src.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class ActionType(Enum):
    """操作類型"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    REDUCE_POSITION = "reduce_position"
    CLOSE_ALL = "close_all"
    ALERT = "alert"


@dataclass
class ExecutionRule:
    """執行規則"""
    action: ActionType
    condition: str
    params: Dict[str, Any]
    enabled: bool = True


class AutoExecutor:
    """
    自動執行器
    
    自動執行：
    - 止損出場
    - 止盈出場
    - 倉位調整
    - 緊急平倉
    """
    
    def __init__(self):
        self.rules: list = []
        self.is_running = False
        self.execution_history: list = []
        self.callbacks: Dict[ActionType, Callable] = {}
    
    def register_callback(self, action: ActionType, callback: Callable):
        """
        註冊操作回調
        
        Args:
            action: 操作類型
            callback: 回調函數
        """
        self.callbacks[action] = callback
        logger.info(f"已註冊回調: {action.value}")
    
    def add_rule(self, rule: ExecutionRule):
        """添加執行規則"""
        self.rules.append(rule)
        logger.info(f"添加規則: {rule.action.value} - {rule.condition}")
    
    async def check_and_execute(self, context: Dict[str, Any]):
        """
        檢查條件並執行
        
        Args:
            context: 當前市場和帳戶狀態
        """
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if self._evaluate_condition(rule.condition, context):
                await self._execute_action(rule.action, rule.params, context)
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        評估條件
        
        支持的條件：
        - loss_pct > X: 虧損百分比超過 X
        - profit_pct > X: 盈利百分比超過 X
        - drawdown > X: 回撤超過 X
        - time_after_entry > X: 持倉時間超過 X 分鐘
        """
        try:
            # 簡單條件解析
            if 'loss_pct' in condition:
                threshold = float(condition.split('>')[1].strip())
                current_loss = context.get('unrealized_pnl_pct', 0)
                return current_loss < -threshold
            
            elif 'profit_pct' in condition:
                threshold = float(condition.split('>')[1].strip())
                current_profit = context.get('unrealized_pnl_pct', 0)
                return current_profit > threshold
            
            elif 'drawdown' in condition:
                threshold = float(condition.split('>')[1].strip())
                current_dd = context.get('drawdown', 0)
                return current_dd > threshold
            
            return False
            
        except Exception as e:
            logger.error(f"條件評估失敗: {e}")
            return False
    
    async def _execute_action(self, action: ActionType, params: Dict[str, Any], 
                              context: Dict[str, Any]):
        """執行操作"""
        logger.warning(f"🚨 自動執行: {action.value}")
        
        # 記錄執行
        self.execution_history.append({
            'action': action.value,
            'params': params,
            'context': context,
            'timestamp': datetime.now().isoformat()
        })
        
        # 調用回調
        if action in self.callbacks:
            try:
                await self.callbacks[action](params, context)
                logger.info(f"✅ 執行成功: {action.value}")
            except Exception as e:
                logger.error(f"❌ 執行失敗: {action.value} - {e}")
        else:
            logger.warning(f"未找到回調: {action.value}")
    
    def get_execution_history(self) -> list:
        """獲取執行歷史"""
        return self.execution_history


# 導入 datetime
from datetime import datetime
