"""
多策略引擎 - Multi Strategy Engine

整合所有自適應策略功能的主引擎
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from src.utils.logger import logger
from src.adaptive_strategy.market_regime_detector import MarketRegimeDetector, RegimeMetrics
from src.adaptive_strategy.strategy_selector import StrategySelector, StrategyScore
from src.adaptive_strategy.strategy_orchestrator import StrategyOrchestrator


@dataclass
class EngineConfig:
    """引擎配置"""
    enable_regime_detection: bool = True
    enable_strategy_selection: bool = True
    enable_weight_optimization: bool = True
    check_interval: int = 60
    min_regime_confidence: float = 0.6


class MultiStrategyEngine:
    """
    多策略引擎
    
    Phase 2 核心組件：
    - 市場狀態自動檢測
    - 策略自動選擇和切換
    - 多策略權重優化
    - 綜合信號生成
    """
    
    def __init__(self, config: EngineConfig = None):
        """
        初始化
        
        Args:
            config: 引擎配置
        """
        self.config = config or EngineConfig()
        
        # 核心組件
        self.regime_detector = MarketRegimeDetector()
        self.strategy_selector = StrategySelector()
        self.orchestrator = StrategyOrchestrator()
        
        # 狀態
        self.is_running = False
        self.current_regime: Optional[RegimeMetrics] = None
        self.current_strategy: Optional[str] = None
        self._main_loop_task = None
        
        # 數據緩存
        self.data_buffer: pd.DataFrame = None
        self.buffer_size = 100
    
    async def start(self):
        """啟動引擎"""
        self.is_running = True
        logger.info("🚀 多策略引擎已啟動")
        
        # 啟動編排器
        await self.orchestrator.start()
        
        # 啟動主循環
        self._main_loop_task = asyncio.create_task(self._main_loop())
    
    def stop(self):
        """停止引擎"""
        self.is_running = False
        self.orchestrator.stop()
        
        if self._main_loop_task:
            self._main_loop_task.cancel()
        
        logger.info("🛑 多策略引擎已停止")
    
    async def _main_loop(self):
        """主循環"""
        logger.info("🔄 主循環已啟動")
        
        while self.is_running:
            try:
                # 1. 更新市場數據
                await self._update_market_data()
                
                # 2. 檢測市場狀態
                if self.config.enable_regime_detection:
                    await self._detect_regime()
                
                # 3. 選擇最佳策略
                if self.config.enable_strategy_selection:
                    await self._select_strategy()
                
                # 4. 優化策略權重
                if self.config.enable_weight_optimization:
                    await self._optimize_weights()
                
                # 5. 生成綜合信號
                signal = await self._generate_signal()
                
                await asyncio.sleep(self.config.check_interval)
                
            except Exception as e:
                logger.error(f"主循環錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _update_market_data(self):
        """更新市場數據"""
        # TODO: 整合實際數據源
        pass
    
    async def _detect_regime(self):
        """檢測市場狀態"""
        if self.data_buffer is None or len(self.data_buffer) < 30:
            return
        
        regime = self.regime_detector.detect(self.data_buffer)
        self.current_regime = regime
        
        if regime.confidence >= self.config.min_regime_confidence:
            logger.info(
                f"📊 市場狀態: {regime.regime.value} "
                f"(信心度: {regime.confidence:.2%})"
            )
    
    async def _select_strategy(self):
        """選擇策略"""
        if self.current_regime is None:
            return
        
        # 檢查是否應該切換
        if not self.strategy_selector.should_switch_strategy(
            self.current_regime.regime
        ):
            return
        
        # 選擇最佳策略
        best = self.strategy_selector.select_strategy(self.current_regime)
        
        if best and best.strategy_name != self.current_strategy:
            self.current_strategy = best.strategy_name
            logger.info(
                f"🔄 策略切換: -> {best.strategy_name} "
                f"(評分: {best.score:.3f})"
            )
    
    async def _optimize_weights(self):
        """優化策略權重"""
        # TODO: 實現權重優化算法
        pass
    
    async def _generate_signal(self) -> float:
        """生成綜合信號"""
        # TODO: 整合各策略信號
        return 0.0
    
    def on_market_data(self, data: pd.DataFrame):
        """
        接收市場數據
        
        Args:
            data: 新數據
        """
        if self.data_buffer is None:
            self.data_buffer = data
        else:
            self.data_buffer = pd.concat([self.data_buffer, data])
        
        # 保持緩存大小
        if len(self.data_buffer) > self.buffer_size:
            self.data_buffer = self.data_buffer.iloc[-self.buffer_size:]
    
    def get_engine_status(self) -> Dict[str, Any]:
        """獲取引擎狀態"""
        return {
            'is_running': self.is_running,
            'current_regime': self.current_regime.to_dict() if self.current_regime else None,
            'current_strategy': self.current_strategy,
            'orchestrator': self.orchestrator.get_allocation_summary(),
            'config': {
                'enable_regime_detection': self.config.enable_regime_detection,
                'enable_strategy_selection': self.config.enable_strategy_selection,
                'enable_weight_optimization': self.config.enable_weight_optimization,
            }
        }
    
    def register_strategy(
        self,
        strategy_name: str,
        regime_fit: Dict[Any, float],
        initial_weight: float = 0.0
    ):
        """
        註冊策略
        
        Args:
            strategy_name: 策略名稱
            regime_fit: 狀態適配
            initial_weight: 初始權重
        """
        # 註冊到選擇器
        self.strategy_selector.register_strategy(strategy_name, regime_fit)
        
        # 添加到編排器
        self.orchestrator.add_strategy(strategy_name, initial_weight)
        
        logger.info(f"✅ 策略已註冊: {strategy_name}")
