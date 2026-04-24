"""
交易監控器 - Trading Monitor

實時監控交易狀態，發送告警
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

try:
    from src.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """告警"""
    level: str  # 'info', 'warning', 'error', 'critical'
    message: str
    timestamp: datetime
    data: Dict[str, Any]


class TradingMonitor:
    """
    交易監控器
    
    監控：
    - 系統狀態
    - 交易表現
    - 風險指標
    - 異常情況
    """
    
    def __init__(self, check_interval: int = 30):
        """
        初始化
        
        Args:
            check_interval: 檢查間隔（秒）
        """
        self.check_interval = check_interval
        self.is_running = False
        self.alerts: List[Alert] = []
        self.metrics_history: List[Dict] = []
        self.alert_handlers: List[Callable] = []
        self._monitor_task = None
    
    def add_alert_handler(self, handler: Callable):
        """添加告警處理器"""
        self.alert_handlers.append(handler)
    
    async def start(self):
        """啟動監控"""
        self.is_running = True
        logger.info("🔍 交易監控器已啟動")
        
        while self.is_running:
            try:
                await self._check_system()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"監控循環錯誤: {e}")
                await asyncio.sleep(5)
    
    def stop(self):
        """停止監控"""
        self.is_running = False
        logger.info("監控器已停止")
    
    async def _check_system(self):
        """檢查系統狀態"""
        # TODO: 實現具體檢查邏輯
        pass
    
    def record_metrics(self, metrics: Dict[str, Any]):
        """記錄指標"""
        metrics['timestamp'] = datetime.now().isoformat()
        self.metrics_history.append(metrics)
        
        # 只保留最近 1000 條
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    def alert(self, level: str, message: str, data: Dict[str, Any] = None):
        """
        發送告警
        
        Args:
            level: 級別 ('info', 'warning', 'error', 'critical')
            message: 消息
            data: 附加數據
        """
        alert = Alert(
            level=level,
            message=message,
            timestamp=datetime.now(),
            data=data or {}
        )
        self.alerts.append(alert)
        
        # 輸出日誌
        log_func = getattr(logger, level, logger.info)
        log_func(f"[{level.upper()}] {message}")
        
        # 調用處理器
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"告警處理器錯誤: {e}")
    
    def get_recent_alerts(self, level: str = None, limit: int = 10) -> List[Alert]:
        """獲取最近告警"""
        alerts = self.alerts
        if level:
            alerts = [a for a in alerts if a.level == level]
        return alerts[-limit:]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """獲取指標摘要"""
        if not self.metrics_history:
            return {}
        
        recent = self.metrics_history[-10:]
        return {
            'total_records': len(self.metrics_history),
            'recent_avg': {
                k: sum(r.get(k, 0) for r in recent) / len(recent)
                for k in recent[0].keys() if k != 'timestamp'
            } if recent else {}
        }
