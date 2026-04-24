"""
監控系統 - Monitoring System

提供實時監控、警報和日誌審計功能：
- 實時監控面板：盈虧、風險度、策略狀態
- 警報機制：風控觸發、異常交易、系統錯誤
- 日誌與審計：操作記錄、風控事件、性能指標
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import threading
import queue

from src.utils.logger import logger


class AlertType(Enum):
    """警報類型"""
    RISK_WARNING = "risk_warning"
    RISK_CRITICAL = "risk_critical"
    TRADE_ANOMALY = "trade_anomaly"
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CONNECTION_LOST = "connection_lost"
    MARGIN_CALL = "margin_call"


class AlertChannel(Enum):
    """警報通道"""
    CONSOLE = "console"
    FILE = "file"
    WEBSOCKET = "websocket"
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class Alert:
    """警報對象"""
    alert_type: AlertType
    title: str
    message: str
    level: str  # info, warning, error, critical
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "alert_type": self.alert_type.value,
            "title": self.title,
            "message": self.message,
            "level": self.level,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }


@dataclass
class MetricPoint:
    """指標數據點"""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class SystemStatus:
    """系統狀態"""
    timestamp: datetime
    is_running: bool
    uptime_seconds: float
    
    # 連接狀態
    quote_connected: bool = False
    trade_connected: Dict[str, bool] = field(default_factory=dict)
    
    # 策略狀態
    strategy_status: Dict[str, Any] = field(default_factory=dict)
    
    # 性能指標
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    
    # 交易統計
    total_trades_today: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    
    # 盈虧
    daily_pnl: float = 0.0
    total_pnl: float = 0.0


class AlertManager:
    """
    警報管理器
    
    負責發送和管理各類警報通知
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化警報管理器
        
        Args:
            config: 警報配置
        """
        self.config = config or {}
        self.alerts: List[Alert] = []
        self.alert_handlers: Dict[AlertChannel, List[Callable]] = {
            AlertChannel.CONSOLE: [],
            AlertChannel.FILE: [],
            AlertChannel.WEBSOCKET: [],
            AlertChannel.TELEGRAM: [],
            AlertChannel.EMAIL: [],
            AlertChannel.WEBHOOK: []
        }
        self._alert_queue: queue.Queue = queue.Queue()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        
        # 警報去重（防止重複發送）
        self._recent_alerts: Dict[str, datetime] = {}
        self._dedup_window = timedelta(minutes=5)
        
        # 設置默認處理器
        self._setup_default_handlers()
        
        logger.info("警報管理器初始化完成")
    
    def _setup_default_handlers(self):
        """設置默認警報處理器"""
        # 控制台輸出
        self.register_handler(AlertChannel.CONSOLE, self._console_handler)
        
        # 文件記錄
        self.register_handler(AlertChannel.FILE, self._file_handler)
    
    def register_handler(self, channel: AlertChannel, handler: Callable[[Alert], None]):
        """
        註冊警報處理器
        
        Args:
            channel: 警報通道
            handler: 處理函數
        """
        self.alert_handlers[channel].append(handler)
    
    def start(self):
        """啟動警報管理器"""
        self._running = True
        self._worker_thread = threading.Thread(target=self._alert_worker, daemon=True)
        self._worker_thread.start()
        logger.info("警報管理器已啟動")
    
    def stop(self):
        """停止警報管理器"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        logger.info("警報管理器已停止")
    
    def _alert_worker(self):
        """警報處理工作線程"""
        while self._running:
            try:
                alert = self._alert_queue.get(timeout=1)
                self._process_alert(alert)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"處理警報時出錯: {e}")
    
    def _process_alert(self, alert: Alert):
        """處理警報"""
        # 保存警報
        self.alerts.append(alert)
        
        # 限制警報數量
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
        
        # 發送到各個通道
        for channel, handlers in self.alert_handlers.items():
            if self._should_send_to_channel(alert, channel):
                for handler in handlers:
                    try:
                        handler(alert)
                    except Exception as e:
                        logger.error(f"警報處理器出錯: {e}")
    
    def _should_send_to_channel(self, alert: Alert, channel: AlertChannel) -> bool:
        """檢查是否應該發送到指定通道"""
        # 根據警報級別和通道配置決定
        level_config = self.config.get("levels", {})
        
        if alert.level == "critical":
            return True
        elif alert.level == "error":
            return channel in [AlertChannel.CONSOLE, AlertChannel.FILE, AlertChannel.TELEGRAM]
        elif alert.level == "warning":
            return channel in [AlertChannel.CONSOLE, AlertChannel.FILE]
        
        return channel == AlertChannel.CONSOLE
    
    def send_alert(self, alert_type: AlertType, title: str, message: str, 
                   level: str = "info", data: Optional[Dict[str, Any]] = None):
        """
        發送警報
        
        Args:
            alert_type: 警報類型
            title: 標題
            message: 消息內容
            level: 級別 (info, warning, error, critical)
            data: 附加數據
        """
        # 檢查去重
        dedup_key = f"{alert_type.value}:{title}"
        now = datetime.now()
        
        if dedup_key in self._recent_alerts:
            last_sent = self._recent_alerts[dedup_key]
            if now - last_sent < self._dedup_window:
                return  # 跳過重複警報
        
        self._recent_alerts[dedup_key] = now
        
        # 創建警報
        alert = Alert(
            alert_type=alert_type,
            title=title,
            message=message,
            level=level,
            timestamp=now,
            data=data or {}
        )
        
        # 加入隊列
        self._alert_queue.put(alert)
    
    def _console_handler(self, alert: Alert):
        """控制台警報處理器"""
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        emoji = emoji_map.get(alert.level, "📢")
        log_message = f"{emoji} [{alert.level.upper()}] {alert.title}: {alert.message}"
        
        if alert.level == "critical":
            logger.critical(log_message)
        elif alert.level == "error":
            logger.error(log_message)
        elif alert.level == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def _file_handler(self, alert: Alert):
        """文件警報處理器"""
        try:
            log_dir = Path("./logs/alerts")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.jsonl"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(alert.to_dict(), ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"寫入警報日誌失敗: {e}")
    
    def acknowledge_alert(self, alert_index: int, acknowledged_by: str):
        """
        確認警報
        
        Args:
            alert_index: 警報索引
            acknowledged_by: 確認人
        """
        if 0 <= alert_index < len(self.alerts):
            alert = self.alerts[alert_index]
            alert.acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            logger.info(f"警報已確認: {alert.title} (by {acknowledged_by})")
    
    def get_unacknowledged_alerts(self) -> List[Alert]:
        """獲取未確認的警報"""
        return [a for a in self.alerts if not a.acknowledged]
    
    def get_alerts_by_type(self, alert_type: AlertType) -> List[Alert]:
        """獲取指定類型的警報"""
        return [a for a in self.alerts if a.alert_type == alert_type]
    
    def clear_old_alerts(self, days: int = 7):
        """清除舊警報"""
        cutoff = datetime.now() - timedelta(days=days)
        self.alerts = [a for a in self.alerts if a.timestamp > cutoff]


class MetricsCollector:
    """
    指標收集器
    
    收集和存儲系統性能指標
    """
    
    def __init__(self, retention_hours: int = 24):
        """
        初始化指標收集器
        
        Args:
            retention_hours: 指標保留時間（小時）
        """
        self.metrics: Dict[str, List[MetricPoint]] = {}
        self.retention_hours = retention_hours
        self._lock = threading.Lock()
        
        logger.info("指標收集器初始化完成")
    
    def record(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        記錄指標
        
        Args:
            name: 指標名稱
            value: 指標值
            labels: 標籤
        """
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = []
            
            point = MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.now(),
                labels=labels or {}
            )
            
            self.metrics[name].append(point)
            
            # 清理舊數據
            self._cleanup_old_data(name)
    
    def _cleanup_old_data(self, name: str):
        """清理舊數據"""
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        self.metrics[name] = [
            m for m in self.metrics[name] 
            if m.timestamp > cutoff
        ]
    
    def get_metric(self, name: str, duration_minutes: int = 60) -> List[MetricPoint]:
        """
        獲取指標數據
        
        Args:
            name: 指標名稱
            duration_minutes: 時間範圍（分鐘）
            
        Returns:
            指標數據點列表
        """
        cutoff = datetime.now() - timedelta(minutes=duration_minutes)
        
        with self._lock:
            if name not in self.metrics:
                return []
            
            return [m for m in self.metrics[name] if m.timestamp > cutoff]
    
    def get_metric_names(self) -> List[str]:
        """獲取所有指標名稱"""
        return list(self.metrics.keys())
    
    def get_latest(self, name: str) -> Optional[MetricPoint]:
        """獲取最新指標值"""
        with self._lock:
            if name not in self.metrics or not self.metrics[name]:
                return None
            return self.metrics[name][-1]
    
    def get_average(self, name: str, duration_minutes: int = 60) -> Optional[float]:
        """獲取平均值"""
        points = self.get_metric(name, duration_minutes)
        if not points:
            return None
        return sum(p.value for p in points) / len(points)
    
    def get_statistics(self, name: str, duration_minutes: int = 60) -> Dict[str, float]:
        """獲取統計信息"""
        points = self.get_metric(name, duration_minutes)
        
        if not points:
            return {}
        
        values = [p.value for p in points]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1]
        }


class AuditLogger:
    """
    審計日誌器
    
    記錄所有重要操作和事件
    """
    
    def __init__(self, log_dir: str = "./logs/audit"):
        """
        初始化審計日誌器
        
        Args:
            log_dir: 日誌目錄
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._current_date = datetime.now().date()
        self._log_file: Optional[Path] = None
        self._lock = threading.Lock()
        
        self._rotate_log_file()
        
        logger.info("審計日誌器初始化完成")
    
    def _rotate_log_file(self):
        """輪換日誌文件"""
        self._current_date = datetime.now().date()
        self._log_file = self.log_dir / f"audit_{self._current_date.strftime('%Y%m%d')}.jsonl"
    
    def log(self, action: str, user: str = "system", 
            details: Optional[Dict[str, Any]] = None, 
            result: str = "success"):
        """
        記錄審計日誌
        
        Args:
            action: 操作名稱
            user: 用戶
            details: 詳細信息
            result: 結果
        """
        # 檢查是否需要輪換日誌文件
        if datetime.now().date() != self._current_date:
            self._rotate_log_file()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user": user,
            "details": details or {},
            "result": result
        }
        
        with self._lock:
            try:
                with open(self._log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            except Exception as e:
                logger.error(f"寫入審計日誌失敗: {e}")
    
    def log_trade(self, symbol: str, side: str, quantity: int, 
                  price: float, order_id: str, result: str = "success"):
        """記錄交易操作"""
        self.log(
            action="trade",
            user="trading_bot",
            details={
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "order_id": order_id
            },
            result=result
        )
    
    def log_risk_event(self, event_type: str, message: str, 
                       level: str, details: Optional[Dict[str, Any]] = None):
        """記錄風控事件"""
        self.log(
            action="risk_event",
            user="risk_manager",
            details={
                "event_type": event_type,
                "message": message,
                "level": level,
                "extra": details or {}
            }
        )
    
    def log_config_change(self, changed_by: str, changes: Dict[str, Any]):
        """記錄配置變更"""
        self.log(
            action="config_change",
            user=changed_by,
            details=changes
        )
    
    def query_logs(self, start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   action: Optional[str] = None,
                   user: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        查詢日誌
        
        Args:
            start_time: 開始時間
            end_time: 結束時間
            action: 操作類型過濾
            user: 用戶過濾
            limit: 返回數量限制
            
        Returns:
            日誌條目列表
        """
        results = []
        
        # 獲取需要查詢的日誌文件
        log_files = sorted(self.log_dir.glob("audit_*.jsonl"), reverse=True)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry_time = datetime.fromisoformat(entry["timestamp"])
                            
                            # 時間過濾
                            if start_time and entry_time < start_time:
                                continue
                            if end_time and entry_time > end_time:
                                continue
                            
                            # 操作類型過濾
                            if action and entry["action"] != action:
                                continue
                            
                            # 用戶過濾
                            if user and entry["user"] != user:
                                continue
                            
                            results.append(entry)
                            
                            if len(results) >= limit:
                                return results
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error(f"讀取日誌文件失敗: {e}")
        
        return results


class Monitor:
    """
    監控器主類
    
    整合警報管理、指標收集和審計日誌功能
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化監控器
        
        Args:
            config: 監控配置
        """
        self.config = config or {}
        
        # 初始化組件
        self.alert_manager = AlertManager(self.config.get("alerts"))
        self.metrics = MetricsCollector(
            retention_hours=self.config.get("metrics_retention_hours", 24)
        )
        self.audit = AuditLogger(
            log_dir=self.config.get("audit_log_dir", "./logs/audit")
        )
        
        # 系統狀態
        self.system_status = SystemStatus(
            timestamp=datetime.now(),
            is_running=False,
            uptime_seconds=0.0
        )
        self._start_time: Optional[datetime] = None
        
        # 監控線程
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        logger.info("監控系統初始化完成")
    
    def start(self):
        """啟動監控系統"""
        self._start_time = datetime.now()
        self.system_status.is_running = True
        
        self.alert_manager.start()
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        self.audit.log("monitor_start", "system")
        logger.info("監控系統已啟動")
    
    def stop(self):
        """停止監控系統"""
        self._monitoring = False
        self.system_status.is_running = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        self.alert_manager.stop()
        
        self.audit.log("monitor_stop", "system")
        logger.info("監控系統已停止")
    
    def _monitor_loop(self):
        """監控循環"""
        while self._monitoring:
            try:
                # 更新系統狀態
                self._update_system_status()
                
                # 收集性能指標
                self._collect_performance_metrics()
                
                # 休眠
                time.sleep(10)  # 每10秒更新一次
                
            except Exception as e:
                logger.error(f"監控循環出錯: {e}")
                time.sleep(5)
    
    def _update_system_status(self):
        """更新系統狀態"""
        if self._start_time:
            uptime = (datetime.now() - self._start_time).total_seconds()
            self.system_status.uptime_seconds = uptime
        
        self.system_status.timestamp = datetime.now()
    
    def _collect_performance_metrics(self):
        """收集性能指標"""
        try:
            import psutil
            
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.record("cpu_percent", cpu_percent)
            self.system_status.cpu_percent = cpu_percent
            
            # 內存使用率
            memory = psutil.virtual_memory()
            self.metrics.record("memory_percent", memory.percent)
            self.system_status.memory_percent = memory.percent
            
            # 檢查性能警報
            if cpu_percent > 90:
                self.alert_manager.send_alert(
                    AlertType.PERFORMANCE_DEGRADATION,
                    "CPU使用率過高",
                    f"CPU使用率達到 {cpu_percent}%",
                    "warning",
                    {"cpu_percent": cpu_percent}
                )
            
            if memory.percent > 90:
                self.alert_manager.send_alert(
                    AlertType.PERFORMANCE_DEGRADATION,
                    "內存使用率過高",
                    f"內存使用率達到 {memory.percent}%",
                    "warning",
                    {"memory_percent": memory.percent}
                )
                
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"收集性能指標失敗: {e}")
    
    def update_connection_status(self, quote_connected: bool, 
                                  trade_connected: Dict[str, bool]):
        """更新連接狀態"""
        self.system_status.quote_connected = quote_connected
        self.system_status.trade_connected = trade_connected
        
        # 檢查連接斷開警報
        if not quote_connected:
            self.alert_manager.send_alert(
                AlertType.CONNECTION_LOST,
                "行情連接斷開",
                "無法連接到行情服務器",
                "error"
            )
    
    def update_strategy_status(self, strategy_name: str, status: Dict[str, Any]):
        """更新策略狀態"""
        self.system_status.strategy_status[strategy_name] = {
            **status,
            "last_update": datetime.now().isoformat()
        }
    
    def update_trading_stats(self, daily_pnl: float, total_pnl: float,
                             total_trades: int, successful: int, failed: int):
        """更新交易統計"""
        self.system_status.daily_pnl = daily_pnl
        self.system_status.total_pnl = total_pnl
        self.system_status.total_trades_today = total_trades
        self.system_status.successful_trades = successful
        self.system_status.failed_trades = failed
        
        # 記錄指標
        self.metrics.record("daily_pnl", daily_pnl)
        self.metrics.record("total_trades", total_trades)
    
    def record_trade(self, symbol: str, side: str, quantity: int, 
                     price: float, order_id: str, result: str = "success"):
        """記錄交易"""
        self.audit.log_trade(symbol, side, quantity, price, order_id, result)
        
        # 更新統計
        self.system_status.total_trades_today += 1
        if result == "success":
            self.system_status.successful_trades += 1
        else:
            self.system_status.failed_trades += 1
    
    def send_risk_alert(self, event_type: str, message: str, 
                        level: str, data: Optional[Dict[str, Any]] = None):
        """發送風控警報"""
        alert_type_map = {
            "critical": AlertType.RISK_CRITICAL,
            "error": AlertType.RISK_WARNING,
            "warning": AlertType.RISK_WARNING,
            "info": AlertType.RISK_WARNING
        }
        
        alert_type = alert_type_map.get(level, AlertType.RISK_WARNING)
        
        self.alert_manager.send_alert(
            alert_type,
            f"風控警報: {event_type}",
            message,
            level,
            data
        )
        
        # 記錄審計日誌
        self.audit.log_risk_event(event_type, message, level, data)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """獲取監控面板數據"""
        return {
            "system_status": {
                "is_running": self.system_status.is_running,
                "uptime_seconds": self.system_status.uptime_seconds,
                "quote_connected": self.system_status.quote_connected,
                "trade_connected": self.system_status.trade_connected,
                "cpu_percent": self.system_status.cpu_percent,
                "memory_percent": self.system_status.memory_percent
            },
            "trading_stats": {
                "daily_pnl": self.system_status.daily_pnl,
                "total_pnl": self.system_status.total_pnl,
                "total_trades_today": self.system_status.total_trades_today,
                "successful_trades": self.system_status.successful_trades,
                "failed_trades": self.system_status.failed_trades
            },
            "strategy_status": self.system_status.strategy_status,
            "recent_alerts": [
                a.to_dict() for a in self.alert_manager.alerts[-10:]
            ],
            "unacknowledged_alerts": len(self.alert_manager.get_unacknowledged_alerts()),
            "metrics": {
                name: self.metrics.get_statistics(name, 60)
                for name in self.metrics.get_metric_names()
            }
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """獲取系統健康狀態"""
        issues = []
        
        if not self.system_status.quote_connected:
            issues.append({"level": "error", "message": "行情連接斷開"})
        
        for market, connected in self.system_status.trade_connected.items():
            if not connected:
                issues.append({"level": "error", "message": f"{market} 交易連接斷開"})
        
        if self.system_status.cpu_percent > 80:
            issues.append({"level": "warning", "message": f"CPU使用率過高: {self.system_status.cpu_percent}%"})
        
        if self.system_status.memory_percent > 80:
            issues.append({"level": "warning", "message": f"內存使用率過高: {self.system_status.memory_percent}%"})
        
        unacknowledged = len(self.alert_manager.get_unacknowledged_alerts())
        if unacknowledged > 0:
            issues.append({"level": "info", "message": f"有 {unacknowledged} 個未確認警報"})
        
        return {
            "healthy": len([i for i in issues if i["level"] == "error"]) == 0,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }
