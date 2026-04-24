"""
整合風控與監控的交易引擎

將 RiskManager 和 Monitor 整合到交易流程中
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from src.utils.logger import logger
from src.risk.risk_manager import RiskManager, Position
from src.monitoring.monitor import Monitor
from src.config.settings import Settings


class RiskAwareTradingEngine:
    """
    帶風控意識的交易引擎
    
    整合風險管理和監控系統到交易流程中
    """
    
    def __init__(self, settings: Settings):
        """
        初始化交易引擎
        
        Args:
            settings: 配置對象
        """
        self.settings = settings
        
        # 初始化風險管理器
        risk_config_path = None
        if hasattr(settings, 'trading') and hasattr(settings.trading, 'risk_management'):
            risk_config_path = settings.trading.risk_management.get('config_path')
        
        self.risk_manager = RiskManager(risk_config_path)
        
        # 初始化監控系統
        monitor_config = {}
        if hasattr(settings, 'monitoring'):
            monitor_config = {
                "metrics_retention_hours": settings.monitoring.get('metrics', {}).get('retention_hours', 24),
                "audit_log_dir": settings.monitoring.get('audit', {}).get('log_dir', './logs/audit'),
                "alerts": settings.monitoring.get('alerts', {})
            }
        
        self.monitor = Monitor(monitor_config)
        
        # 交易統計
        self._total_trades = 0
        self._successful_trades = 0
        self._failed_trades = 0
        self._total_pnl = 0.0
        
        logger.info("風控交易引擎初始化完成")
    
    def start(self):
        """啟動引擎"""
        self.monitor.start()
        self.monitor.audit.log("trading_engine_start", "system")
        logger.info("風控交易引擎已啟動")
    
    def stop(self):
        """停止引擎"""
        self.monitor.stop()
        logger.info("風控交易引擎已停止")
    
    def update_account_info(self, total_capital: float, 
                           margin_used: float = 0.0, 
                           margin_available: float = 0.0):
        """
        更新賬戶信息
        
        Args:
            total_capital: 總資金
            margin_used: 已用保證金
            margin_available: 可用保證金
        """
        self.risk_manager.update_capital(total_capital, margin_used, margin_available)
        
        # 檢查資金風險
        daily_pnl = self.risk_manager.daily_stats.get('daily_pnl', 0)
        risk_events = self.risk_manager.check_capital_risk(daily_pnl)
        
        # 發送風險警報
        for event in risk_events:
            self.monitor.send_risk_alert(
                event.event_type.value,
                event.message,
                event.level.value,
                event.details
            )
    
    def update_positions(self, positions_data: List[Dict[str, Any]]):
        """
        更新持倉信息
        
        Args:
            positions_data: 持倉數據列表
        """
        positions = []
        for data in positions_data:
            position = Position(
                symbol=data['symbol'],
                quantity=data['quantity'],
                avg_price=data['avg_price'],
                market_price=data['market_price'],
                sector=data.get('sector')
            )
            positions.append(position)
        
        self.risk_manager.update_positions(positions)
        
        # 檢查是否有風險事件並發送警報
        summary = self.risk_manager.get_risk_summary()
        for event_data in summary.get('recent_events', []):
            if event_data['level'] in ['high', 'critical']:
                self.monitor.send_risk_alert(
                    event_data['type'],
                    event_data['message'],
                    event_data['level'],
                    event_data.get('details', {})
                )
    
    def check_trade(self, symbol: str, quantity: int, price: float, 
                    side: str) -> tuple[bool, Optional[str]]:
        """
        檢查交易是否允許
        
        Args:
            symbol: 股票代碼
            quantity: 數量
            price: 價格
            side: 方向 (BUY/SELL)
            
        Returns:
            (是否允許, 拒絕原因)
        """
        can_trade, event = self.risk_manager.check_trade_risk(symbol, quantity, price, side)
        
        if not can_trade:
            # 發送風控警報
            self.monitor.send_risk_alert(
                event.event_type.value,
                event.message,
                event.level.value,
                event.details
            )
            
            # 記錄審計日誌
            self.monitor.audit.log(
                action="trade_rejected",
                user="risk_manager",
                details={
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price,
                    "side": side,
                    "reason": event.message
                },
                result="rejected"
            )
            
            return False, event.message
        
        return True, None
    
    def record_trade(self, symbol: str, quantity: int, price: float, 
                     side: str, order_id: str, result: str = "success",
                     pnl: float = 0.0):
        """
        記錄交易
        
        Args:
            symbol: 股票代碼
            quantity: 數量
            price: 價格
            side: 方向
            order_id: 訂單ID
            result: 結果
            pnl: 盈虧
        """
        # 記錄到風險管理器
        self.risk_manager.record_trade(symbol, quantity, price, side)
        
        # 記錄到監控系統
        self.monitor.record_trade(symbol, side, quantity, price, order_id, result)
        
        # 更新統計
        self._total_trades += 1
        if result == "success":
            self._successful_trades += 1
        else:
            self._failed_trades += 1
        
        self._total_pnl += pnl
        
        # 更新監控面板
        self.monitor.update_trading_stats(
            daily_pnl=self.risk_manager.daily_stats.get('daily_pnl', 0) + pnl,
            total_pnl=self._total_pnl,
            total_trades=self._total_trades,
            successful=self._successful_trades,
            failed=self._failed_trades
        )
        
        # 檢查價格異常
        price_event = self.risk_manager._check_price_anomaly(symbol, price)
        if price_event and price_event.level.value in ['high', 'critical']:
            self.monitor.send_risk_alert(
                price_event.event_type.value,
                price_event.message,
                price_event.level.value,
                price_event.details
            )
    
    def update_connection_status(self, quote_connected: bool, 
                                  trade_connected: Dict[str, bool]):
        """更新連接狀態"""
        self.monitor.update_connection_status(quote_connected, trade_connected)
    
    def update_strategy_status(self, strategy_name: str, status: Dict[str, Any]):
        """更新策略狀態"""
        self.monitor.update_strategy_status(strategy_name, status)
    
    def get_status(self) -> Dict[str, Any]:
        """獲取引擎狀態"""
        risk_summary = self.risk_manager.get_risk_summary()
        dashboard = self.monitor.get_dashboard_data()
        health = self.monitor.get_system_health()
        
        return {
            "trading_enabled": risk_summary['trading_enabled'],
            "risk_summary": risk_summary,
            "system_status": dashboard['system_status'],
            "trading_stats": dashboard['trading_stats'],
            "health": health,
            "unacknowledged_alerts": len(self.monitor.alert_manager.get_unacknowledged_alerts())
        }
    
    def get_risk_report(self) -> Dict[str, Any]:
        """獲取風險報告"""
        return self.risk_manager.get_risk_summary()
    
    def acknowledge_alert(self, alert_index: int, user: str):
        """確認警報"""
        self.monitor.alert_manager.acknowledge_alert(alert_index, user)
    
    def reset_daily_stats(self):
        """重置每日統計"""
        self.risk_manager.reset_daily_stats()
        logger.info("每日統計已重置")
