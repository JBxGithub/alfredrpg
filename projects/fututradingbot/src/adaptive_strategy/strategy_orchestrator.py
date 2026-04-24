"""
策略編排器 - Strategy Orchestrator

協調多個策略的運行和權重分配
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from src.utils.logger import logger
from src.adaptive_strategy.market_regime_detector import MarketRegimeDetector, MarketRegime
from src.adaptive_strategy.strategy_selector import StrategySelector, StrategyScore


@dataclass
class StrategyAllocation:
    """策略配置"""
    strategy_name: str
    weight: float           # 權重 (0-1)
    active: bool            # 是否激活
    params: Dict[str, Any]  # 策略參數


class StrategyOrchestrator:
    """
    策略編排器
    
    負責：
    - 管理多策略組合
    - 動態調整策略權重
    - 協調策略切換
    """
    
    def __init__(
        self,
        max_strategies: int = 3,
        rebalance_threshold: float = 0.1
    ):
        """
        初始化
        
        Args:
            max_strategies: 最大同時運行策略數
            rebalance_threshold: 再平衡閾值
        """
        self.max_strategies = max_strategies
        self.rebalance_threshold = rebalance_threshold
        
        # 策略配置
        self.allocations: Dict[str, StrategyAllocation] = {}
        
        # 檢測器和選擇器
        self.regime_detector = MarketRegimeDetector()
        self.strategy_selector = StrategySelector()
        
        # 狀態
        self.is_running = False
        self.check_interval = 60  # 秒
        self._monitor_task = None
    
    def add_strategy(
        self,
        strategy_name: str,
        initial_weight: float = 0.0,
        params: Dict[str, Any] = None
    ):
        """
        添加策略到組合
        
        Args:
            strategy_name: 策略名稱
            initial_weight: 初始權重
            params: 策略參數
        """
        self.allocations[strategy_name] = StrategyAllocation(
            strategy_name=strategy_name,
            weight=initial_weight,
            active=initial_weight > 0,
            params=params or {}
        )
        logger.info(f"添加策略到組合: {strategy_name} (權重: {initial_weight:.2%})")
    
    async def start(self):
        """啟動編排器"""
        self.is_running = True
        logger.info("策略編排器已啟動")
        
        # 啟動監控循環
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    def stop(self):
        """停止編排器"""
        self.is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
        logger.info("策略編排器已停止")
    
    async def _monitor_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                # 檢測市場狀態
                # TODO: 整合實際數據
                # regime = self.regime_detector.detect(data)
                
                # 檢查是否需要再平衡
                await self._check_rebalance()
                
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"監控循環錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _check_rebalance(self):
        """檢查是否需要再平衡"""
        # TODO: 實現再平衡邏輯
        pass
    
    def update_weights(
        self,
        new_weights: Dict[str, float],
        reason: str = ""
    ):
        """
        更新策略權重
        
        Args:
            new_weights: 新權重配置
            reason: 更新原因
        """
        # 正規化權重
        total = sum(new_weights.values())
        if total == 0:
            logger.warning("所有權重為0，不更新")
            return
        
        normalized = {k: v / total for k, v in new_weights.items()}
        
        # 應用新權重
        for name, weight in normalized.items():
            if name in self.allocations:
                old_weight = self.allocations[name].weight
                self.allocations[name].weight = weight
                self.allocations[name].active = weight > 0.01
                
                if abs(weight - old_weight) > 0.05:
                    logger.info(
                        f"權重調整: {name} {old_weight:.2%} -> {weight:.2%}"
                    )
        
        if reason:
            logger.info(f"權重更新原因: {reason}")
    
    def get_active_strategies(self) -> List[StrategyAllocation]:
        """獲取激活的策略"""
        return [
            alloc for alloc in self.allocations.values()
            if alloc.active and alloc.weight > 0
        ]
    
    def get_portfolio_weights(self) -> Dict[str, float]:
        """獲取組合權重"""
        return {
            name: alloc.weight
            for name, alloc in self.allocations.items()
        }
    
    def calculate_composite_signal(
        self,
        strategy_signals: Dict[str, float]
    ) -> float:
        """
        計算綜合信號
        
        Args:
            strategy_signals: 各策略信號 (-1 到 1)
            
        Returns:
            綜合信號
        """
        composite = 0.0
        total_weight = 0.0
        
        for name, signal in strategy_signals.items():
            if name in self.allocations:
                weight = self.allocations[name].weight
                composite += signal * weight
                total_weight += weight
        
        if total_weight > 0:
            composite /= total_weight
        
        return np.clip(composite, -1, 1)
    
    def get_allocation_summary(self) -> Dict[str, Any]:
        """獲取配置摘要"""
        active = self.get_active_strategies()
        
        return {
            'total_strategies': len(self.allocations),
            'active_strategies': len(active),
            'allocations': [
                {
                    'name': alloc.strategy_name,
                    'weight': alloc.weight,
                    'active': alloc.active
                }
                for alloc in self.allocations.values()
            ],
            'timestamp': datetime.now().isoformat()
        }
