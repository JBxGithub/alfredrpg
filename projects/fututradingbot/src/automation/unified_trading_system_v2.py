"""
統一交易系統 V2 - Unified Trading System V2

整合 Phase 1 + 2 + 3 的完整自動化交易系統
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from src.utils.logger import logger

# Phase 1 組件
from src.automation.deployment_manager import DeploymentManager, DeploymentConfig
from src.automation.risk_checker import RiskChecker
from src.automation.auto_executor import AutoExecutor
from src.automation.monitor import TradingMonitor
from src.realtime_optimizer.performance_tracker import PerformanceTracker
from src.realtime_optimizer.parameter_adjuster import ParameterAdjuster

# Phase 2 組件
from src.adaptive_strategy import (
    MultiStrategyEngine, EngineConfig,
    MarketRegime, StrategySelector
)

# Phase 3 組件
from src.reinforcement_learning import (
    TradingEnvironment, RLAgent, RLTrainer, TrainingConfig
)


@dataclass
class UnifiedConfigV2:
    """統一配置 V2"""
    # Phase 1 配置
    strategy_name: str = "AdaptiveMultiStrategy"
    symbols: List[str] = None
    initial_capital: float = 100000.0
    paper_trading: bool = True
    
    # Phase 2 配置
    enable_adaptive_strategy: bool = True
    max_strategies: int = 3
    
    # Phase 3 配置
    enable_rl_optimization: bool = True
    rl_training_episodes: int = 100
    
    # 通用配置
    auto_adjust_params: bool = True
    auto_stop_loss: bool = True
    auto_take_profit: bool = True
    enable_monitoring: bool = True
    check_interval: int = 60
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ['TQQQ']


class UnifiedTradingSystemV2:
    """
    統一交易系統 V2
    
    整合三大階段功能：
    - Phase 1: 自動化部署 + 實時優化
    - Phase 2: 自適應策略切換
    - Phase 3: 強化學習優化
    """
    
    def __init__(self):
        """初始化"""
        # Phase 1 組件
        self.deployment = DeploymentManager()
        self.risk_checker = RiskChecker()
        self.executor = AutoExecutor()
        self.monitor = TradingMonitor()
        self.tracker = PerformanceTracker()
        self.adjuster = ParameterAdjuster()
        
        # Phase 2 組件
        self.strategy_engine: Optional[MultiStrategyEngine] = None
        
        # Phase 3 組件
        self.rl_agent: Optional[RLAgent] = None
        self.rl_trainer: Optional[RLTrainer] = None
        
        # 配置
        self.config: Optional[UnifiedConfigV2] = None
        self.is_running = False
        self._main_task = None
        
        logger.info("🚀 UnifiedTradingSystemV2 初始化完成")
    
    async def start(self, config: UnifiedConfigV2) -> bool:
        """
        啟動系統
        
        Args:
            config: 統一配置
            
        Returns:
            bool: 是否成功啟動
        """
        self.config = config
        logger.info("=" * 70)
        logger.info("🚀 啟動 UnifiedTradingSystemV2")
        logger.info("=" * 70)
        
        # Phase 1: 部署
        logger.info("\n【Phase 1】啟動自動化基礎...")
        deploy_config = DeploymentConfig(
            strategy_name=config.strategy_name,
            symbols=config.symbols,
            initial_capital=config.initial_capital,
            paper_trading=config.paper_trading,
            auto_stop_loss=config.auto_stop_loss,
            auto_take_profit=config.auto_take_profit
        )
        
        if not await self.deployment.deploy(deploy_config):
            logger.error("❌ Phase 1 部署失敗")
            return False
        
        self.tracker.start()
        self.adjuster.initialize({
            'position_size': 0.02,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        })
        logger.info("✅ Phase 1 完成")
        
        # Phase 2: 自適應策略
        if config.enable_adaptive_strategy:
            logger.info("\n【Phase 2】啟動自適應策略...")
            await self._init_phase2()
            logger.info("✅ Phase 2 完成")
        
        # Phase 3: 強化學習
        if config.enable_rl_optimization:
            logger.info("\n【Phase 3】初始化強化學習...")
            await self._init_phase3()
            logger.info("✅ Phase 3 完成")
        
        # 啟動主循環
        self.is_running = True
        self._main_task = asyncio.create_task(self._main_loop())
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ 所有階段啟動完成！")
        logger.info("=" * 70)
        logger.info(f"交易模式: {'模擬' if config.paper_trading else '實盤'}")
        logger.info(f"自適應策略: {'啟用' if config.enable_adaptive_strategy else '禁用'}")
        logger.info(f"強化學習: {'啟用' if config.enable_rl_optimization else '禁用'}")
        
        return True
    
    async def _init_phase2(self):
        """初始化 Phase 2"""
        engine_config = EngineConfig(
            enable_regime_detection=True,
            enable_strategy_selection=True,
            check_interval=self.config.check_interval
        )
        
        self.strategy_engine = MultiStrategyEngine(engine_config)
        
        # 註冊預設策略
        from src.adaptive_strategy import MarketRegime
        self.strategy_engine.register_strategy(
            'TQQQ_Momentum',
            {
                MarketRegime.TRENDING_UP: 0.9,
                MarketRegime.TRENDING_DOWN: 0.7,
                MarketRegime.RANGING: 0.4
            },
            0.5
        )
        
        self.strategy_engine.register_strategy(
            'MeanReversion',
            {
                MarketRegime.RANGING: 0.9,
                MarketRegime.LOW_VOLATILITY: 0.8
            },
            0.3
        )
        
        await self.strategy_engine.start()
    
    async def _init_phase3(self):
        """初始化 Phase 3"""
        # 創建簡化環境（實際應連接真實數據）
        dummy_data = pd.DataFrame({
            'open': [100] * 100,
            'high': [101] * 100,
            'low': [99] * 100,
            'close': [100] * 100,
            'volume': [1000] * 100
        })
        
        env = TradingEnvironment(dummy_data, self.config.initial_capital)
        self.rl_agent = RLAgent(state_dim=6, action_dim=4)
        
        trainer_config = TrainingConfig(
            episodes=self.config.rl_training_episodes,
            max_steps=50
        )
        
        self.rl_trainer = RLTrainer(env, self.rl_agent, trainer_config)
    
    async def _main_loop(self):
        """主循環"""
        logger.info("🔄 主循環已啟動")
        
        while self.is_running:
            try:
                # Phase 1: 實時優化
                if self.config.auto_adjust_params:
                    if self.tracker.should_adjust_strategy():
                        new_params = self.adjuster.adjust(self.tracker)
                        logger.info(f"參數自動調整: {new_params}")
                
                # Phase 2: 策略切換
                if self.strategy_engine and self.config.enable_adaptive_strategy:
                    # 策略引擎在背景運行
                    pass
                
                # Phase 3: RL 訓練
                if self.rl_trainer and self.config.enable_rl_optimization:
                    # RL 訓練在背景進行
                    pass
                
                # 記錄狀態
                self._log_status()
                
                await asyncio.sleep(self.config.check_interval)
                
            except Exception as e:
                logger.error(f"主循環錯誤: {e}")
                await asyncio.sleep(5)
    
    def _log_status(self):
        """記錄系統狀態"""
        status = self.get_status()
        logger.debug(f"系統狀態: {status}")
    
    async def stop(self):
        """停止系統"""
        logger.info("🛑 正在停止系統...")
        self.is_running = False
        
        if self.strategy_engine:
            self.strategy_engine.stop()
        
        if self.rl_trainer:
            self.rl_trainer.stop()
        
        await self.deployment.stop()
        self.monitor.stop()
        
        logger.info("✅ 系統已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'is_running': self.is_running,
            'phase1': {
                'deployment_status': self.deployment.get_status(),
                'performance': self.tracker.get_trade_summary()
            },
            'phase2': self.strategy_engine.get_engine_status() if self.strategy_engine else None,
            'phase3': self.rl_trainer.get_training_summary() if self.rl_trainer else None
        }


# 使用示例
async def main():
    """主函數示例"""
    system = UnifiedTradingSystemV2()
    
    config = UnifiedConfigV2(
        strategy_name="FullAutoV2",
        symbols=["TQQQ"],
        initial_capital=100000,
        paper_trading=True,
        enable_adaptive_strategy=True,
        enable_rl_optimization=True
    )
    
    if await system.start(config):
        print("\n✅ 系統運作中，按 Ctrl+C 停止")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await system.stop()
    else:
        print("❌ 啟動失敗")


if __name__ == '__main__':
    asyncio.run(main())
