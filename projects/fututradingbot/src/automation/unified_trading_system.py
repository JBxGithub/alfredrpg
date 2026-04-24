"""
統一交易系統 - Unified Trading System

整合實盤部署自動化 + 實時策略調整
"""

import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass

try:
    from src.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
from src.automation.deployment_manager import DeploymentManager, DeploymentConfig, DeploymentStatus
from src.automation.auto_executor import AutoExecutor, ActionType
from src.automation.monitor import TradingMonitor
from src.realtime_optimizer.performance_tracker import PerformanceTracker
from src.realtime_optimizer.parameter_adjuster import ParameterAdjuster


@dataclass
class UnifiedConfig:
    """統一配置"""
    # 部署配置
    strategy_name: str
    symbols: list
    initial_capital: float
    paper_trading: bool = True
    
    # 風險配置
    risk_per_trade: float = 0.02
    max_daily_loss: float = 0.05
    max_drawdown: float = 0.10
    
    # 自動化配置
    auto_adjust_params: bool = True
    auto_stop_loss: bool = True
    auto_take_profit: bool = True
    
    # 監控配置
    enable_monitoring: bool = True
    check_interval: int = 30


class UnifiedTradingSystem:
    """
    統一交易系統
    
    整合：
    1. 一鍵部署實盤/模擬交易
    2. 實時表現追踪
    3. 自動參數調整
    4. 自動止損/止盈
    5. 實時監控告警
    """
    
    def __init__(self):
        # 部署模組
        self.deployment = DeploymentManager()
        self.executor = AutoExecutor()
        self.monitor = TradingMonitor()
        
        # 實時優化模組
        self.tracker = PerformanceTracker()
        self.adjuster = ParameterAdjuster()
        
        # 狀態
        self.config: Optional[UnifiedConfig] = None
        self.is_running = False
        self._main_loop_task = None
    
    async def start(self, config: UnifiedConfig) -> bool:
        """
        啟動統一交易系統
        
        Args:
            config: 統一配置
            
        Returns:
            bool: 是否成功啟動
        """
        self.config = config
        logger.info("🚀 啟動統一交易系統")
        logger.info(f"策略: {config.strategy_name}")
        logger.info(f"模式: {'模擬交易' if config.paper_trading else '實盤交易'}")
        
        # Step 1: 部署
        deploy_config = DeploymentConfig(
            strategy_name=config.strategy_name,
            symbols=config.symbols,
            initial_capital=config.initial_capital,
            risk_per_trade=config.risk_per_trade,
            max_daily_loss=config.max_daily_loss,
            max_drawdown=config.max_drawdown,
            auto_stop_loss=config.auto_stop_loss,
            auto_take_profit=config.auto_take_profit,
            paper_trading=config.paper_trading
        )
        
        if not await self.deployment.deploy(deploy_config):
            logger.error("部署失敗")
            return False
        
        # Step 2: 初始化優化器
        self.tracker.start()
        self.adjuster.initialize({
            'position_size': config.risk_per_trade,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04
        })
        
        # Step 3: 設置自動執行規則
        if config.auto_stop_loss:
            self.executor.add_rule({
                'action': ActionType.STOP_LOSS,
                'condition': 'loss_pct > 0.02',
                'params': {'reason': 'auto_stop_loss'},
                'enabled': True
            })
        
        if config.auto_take_profit:
            self.executor.add_rule({
                'action': ActionType.TAKE_PROFIT,
                'condition': 'profit_pct > 0.04',
                'params': {'reason': 'auto_take_profit'},
                'enabled': True
            })
        
        # Step 4: 啟動監控
        if config.enable_monitoring:
            self._main_loop_task = asyncio.create_task(self._main_loop())
        
        self.is_running = True
        logger.info("✅ 統一交易系統已啟動")
        return True
    
    async def _main_loop(self):
        """主循環"""
        logger.info("🔄 主循環已啟動")
        
        while self.is_running and self.deployment.status == DeploymentStatus.RUNNING:
            try:
                # 1. 檢查是否需要調整參數
                if self.config.auto_adjust_params:
                    if self.tracker.should_adjust_strategy():
                        logger.info("檢測到需要調整策略")
                        new_params = self.adjuster.adjust(self.tracker)
                        logger.info(f"參數已調整: {new_params}")
                
                # 2. 檢查自動執行規則
                context = self._build_context()
                await self.executor.check_and_execute(context)
                
                # 3. 記錄指標
                metrics = self.tracker.get_trade_summary()
                self.monitor.record_metrics(metrics)
                
                # 4. 檢查風險限制
                await self._check_risk_limits()
                
                await asyncio.sleep(self.config.check_interval if self.config else 30)
                
            except Exception as e:
                logger.error(f"主循環錯誤: {e}")
                await asyncio.sleep(5)
    
    def _build_context(self) -> Dict[str, Any]:
        """構建當前上下文"""
        metrics = self.tracker.get_metrics()
        return {
            'unrealized_pnl_pct': 0,  # TODO: 從持倉計算
            'drawdown': metrics.max_drawdown,
            'win_rate': metrics.win_rate,
            'total_pnl': metrics.total_pnl
        }
    
    async def _check_risk_limits(self):
        """檢查風險限制"""
        metrics = self.tracker.get_metrics()
        
        # 日虧損限制
        if metrics.total_pnl_pct < -self.config.max_daily_loss:
            self.monitor.alert(
                'critical',
                f"日虧損超過限制: {metrics.total_pnl_pct:.2%}",
                {'action': 'pause_trading'}
            )
            await self.deployment.pause()
        
        # 最大回撤限制
        if metrics.max_drawdown > self.config.max_drawdown:
            self.monitor.alert(
                'critical',
                f"最大回撤超過限制: {metrics.max_drawdown:.2%}",
                {'action': 'stop_trading'}
            )
            await self.stop()
    
    async def stop(self):
        """停止系統"""
        logger.info("🛑 正在停止統一交易系統...")
        self.is_running = False
        
        if self._main_loop_task:
            self._main_loop_task.cancel()
        
        await self.deployment.stop()
        self.monitor.stop()
        
        logger.info("✅ 統一交易系統已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'is_running': self.is_running,
            'deployment': self.deployment.get_status(),
            'performance': self.tracker.get_trade_summary(),
            'current_params': self.adjuster.get_current_params(),
            'alerts': len(self.monitor.alerts)
        }


# 使用示例
async def main():
    """主函數示例"""
    system = UnifiedTradingSystem()
    
    config = UnifiedConfig(
        strategy_name='TQQQ_Momentum',
        symbols=['TQQQ'],
        initial_capital=100000,
        paper_trading=True,  # 先用模擬交易測試
        auto_adjust_params=True,
        auto_stop_loss=True,
        auto_take_profit=True
    )
    
    if await system.start(config):
        print("系統已啟動，按 Ctrl+C 停止")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await system.stop()
    else:
        print("啟動失敗")


if __name__ == '__main__':
    asyncio.run(main())
