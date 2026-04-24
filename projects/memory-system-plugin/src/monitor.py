"""
Session Monitor Module - 記憶系統插件
負責監控 Context 使用率，實現預警和自動觸發機制

Author: ClawTeam - Monitor
Date: 2026-04-07
"""

import json
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path
import threading
import queue

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContextStatus(Enum):
    """Context 使用狀態"""
    NORMAL = "normal"           # 正常 (< 70%)
    WARNING = "warning"         # 預警 (70% - 80%)
    CRITICAL = "critical"       # 危險 (>= 80%)
    UNKNOWN = "unknown"         # 未知


@dataclass
class ContextMetrics:
    """Context 使用指標"""
    session_id: str
    timestamp: datetime
    tokens_used: int
    tokens_total: int
    tokens_remaining: int
    usage_percentage: float
    status: ContextStatus
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "tokens_used": self.tokens_used,
            "tokens_total": self.tokens_total,
            "tokens_remaining": self.tokens_remaining,
            "usage_percentage": round(self.usage_percentage, 2),
            "status": self.status.value
        }


@dataclass
class AlertConfig:
    """預警配置"""
    warning_threshold: float = 70.0      # 70% 預警
    critical_threshold: float = 80.0     # 80% 自動觸發
    check_interval: int = 300            # 每 5 分鐘檢測一次
    max_history_size: int = 1000         # 最大歷史記錄數
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SessionState:
    """Session 狀態"""
    session_id: str
    created_at: datetime
    last_activity: datetime
    context_metrics: Optional[ContextMetrics] = None
    alert_count: int = 0
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "context_metrics": self.context_metrics.to_dict() if self.context_metrics else None,
            "alert_count": self.alert_count,
            "is_active": self.is_active
        }


class ContextMonitor:
    """
    Context 使用率監控器
    
    功能：
    1. 實時檢測 Context 使用率
    2. 70% 發送預警通知
    3. 80% 自動觸發 Session 切換流程
    4. 記錄歷史數據供分析
    """
    
    # OpenClaw 預設 Context 限制
    DEFAULT_CONTEXT_LIMIT = 256000  # 256k tokens
    
    def __init__(
        self,
        session_id: str,
        config: Optional[AlertConfig] = None,
        data_dir: Optional[Path] = None
    ):
        self.session_id = session_id
        self.config = config or AlertConfig()
        self.data_dir = data_dir or Path("./data/monitor")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 狀態追蹤
        self.state = SessionState(
            session_id=session_id,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        # 歷史記錄
        self.metrics_history: List[ContextMetrics] = []
        self.max_history = self.config.max_history_size
        
        # 回調函數
        self._warning_callbacks: List[Callable[[ContextMetrics], None]] = []
        self._critical_callbacks: List[Callable[[ContextMetrics], None]] = []
        self._normal_callbacks: List[Callable[[ContextMetrics], None]] = []
        
        # 監控線程
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._alert_triggered = {
            ContextStatus.WARNING: False,
            ContextStatus.CRITICAL: False
        }
        
        logger.info(f"ContextMonitor initialized for session: {session_id}")
    
    def register_callback(
        self,
        status: ContextStatus,
        callback: Callable[[ContextMetrics], None]
    ) -> None:
        """
        註冊狀態變化回調函數
        
        Args:
            status: 觸發回調的狀態
            callback: 回調函數，接收 ContextMetrics 參數
        """
        if status == ContextStatus.WARNING:
            self._warning_callbacks.append(callback)
        elif status == ContextStatus.CRITICAL:
            self._critical_callbacks.append(callback)
        elif status == ContextStatus.NORMAL:
            self._normal_callbacks.append(callback)
        
        logger.debug(f"Registered callback for status: {status.value}")
    
    def calculate_usage(
        self,
        tokens_used: int,
        tokens_total: Optional[int] = None
    ) -> ContextMetrics:
        """
        計算 Context 使用率
        
        Args:
            tokens_used: 已使用的 tokens
            tokens_total: 總 tokens 限制（預設 256k）
        
        Returns:
            ContextMetrics 指標對象
        """
        tokens_total = tokens_total or self.DEFAULT_CONTEXT_LIMIT
        tokens_remaining = tokens_total - tokens_used
        usage_percentage = (tokens_used / tokens_total) * 100
        
        # 確定狀態
        if usage_percentage >= self.config.critical_threshold:
            status = ContextStatus.CRITICAL
        elif usage_percentage >= self.config.warning_threshold:
            status = ContextStatus.WARNING
        else:
            status = ContextStatus.NORMAL
        
        metrics = ContextMetrics(
            session_id=self.session_id,
            timestamp=datetime.now(),
            tokens_used=tokens_used,
            tokens_total=tokens_total,
            tokens_remaining=tokens_remaining,
            usage_percentage=usage_percentage,
            status=status
        )
        
        # 更新狀態
        self.state.context_metrics = metrics
        self.state.last_activity = datetime.now()
        
        # 添加到歷史
        self._add_to_history(metrics)
        
        return metrics
    
    def _add_to_history(self, metrics: ContextMetrics) -> None:
        """添加指標到歷史記錄"""
        self.metrics_history.append(metrics)
        
        # 限制歷史記錄大小
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
    
    def check_and_alert(self, tokens_used: int) -> ContextMetrics:
        """
        檢查使用率並觸發相應警報
        
        Args:
            tokens_used: 當前已使用的 tokens
        
        Returns:
            ContextMetrics 指標對象
        """
        metrics = self.calculate_usage(tokens_used)
        
        # 根據狀態觸發回調
        if metrics.status == ContextStatus.CRITICAL:
            if not self._alert_triggered[ContextStatus.CRITICAL]:
                self._trigger_critical_alert(metrics)
                self._alert_triggered[ContextStatus.CRITICAL] = True
                self.state.alert_count += 1
        
        elif metrics.status == ContextStatus.WARNING:
            if not self._alert_triggered[ContextStatus.WARNING]:
                self._trigger_warning_alert(metrics)
                self._alert_triggered[ContextStatus.WARNING] = True
                self.state.alert_count += 1
        
        elif metrics.status == ContextStatus.NORMAL:
            # 重置警報狀態
            self._alert_triggered = {
                ContextStatus.WARNING: False,
                ContextStatus.CRITICAL: False
            }
            self._trigger_normal_callback(metrics)
        
        return metrics
    
    def _trigger_warning_alert(self, metrics: ContextMetrics) -> None:
        """觸發預警警報"""
        logger.warning(
            f"⚠️ Context 使用率預警: {metrics.usage_percentage:.1f}% "
            f"({metrics.tokens_used:,}/{metrics.tokens_total:,} tokens)"
        )
        
        for callback in self._warning_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Warning callback error: {e}")
    
    def _trigger_critical_alert(self, metrics: ContextMetrics) -> None:
        """觸發危險警報（自動觸發機制）"""
        logger.error(
            f"🚨 Context 使用率危險: {metrics.usage_percentage:.1f}% "
            f"({metrics.tokens_used:,}/{metrics.tokens_total:,} tokens)\n"
            f"自動觸發 Session 切換流程！"
        )
        
        for callback in self._critical_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Critical callback error: {e}")
    
    def _trigger_normal_callback(self, metrics: ContextMetrics) -> None:
        """觸發正常狀態回調"""
        for callback in self._normal_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Normal callback error: {e}")
    
    def start_monitoring(self, get_tokens_func: Callable[[], int]) -> None:
        """
        啟動後台監控線程
        
        Args:
            get_tokens_func: 獲取當前 tokens 使用量的函數
        """
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("Monitoring already running")
            return
        
        self._stop_event.clear()
        
        def monitor_loop():
            logger.info(f"Started monitoring thread for session: {self.session_id}")
            
            while not self._stop_event.is_set():
                try:
                    tokens_used = get_tokens_func()
                    self.check_and_alert(tokens_used)
                    
                    # 保存狀態
                    self.save_state()
                    
                except Exception as e:
                    logger.error(f"Monitor loop error: {e}")
                
                # 等待下一次檢測
                self._stop_event.wait(self.config.check_interval)
            
            logger.info(f"Stopped monitoring thread for session: {self.session_id}")
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """停止後台監控線程"""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.state.is_active = False
        self.save_state()
        logger.info("Monitoring stopped")
    
    def save_state(self) -> None:
        """保存當前狀態到文件"""
        state_file = self.data_dir / f"{self.session_id}_state.json"
        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def load_state(self) -> Optional[SessionState]:
        """從文件加載狀態"""
        state_file = self.data_dir / f"{self.session_id}_state.json"
        if not state_file.exists():
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.state = SessionState(
                session_id=data["session_id"],
                created_at=datetime.fromisoformat(data["created_at"]),
                last_activity=datetime.fromisoformat(data["last_activity"]),
                alert_count=data.get("alert_count", 0),
                is_active=data.get("is_active", True)
            )
            
            if data.get("context_metrics"):
                metrics_data = data["context_metrics"]
                self.state.context_metrics = ContextMetrics(
                    session_id=metrics_data["session_id"],
                    timestamp=datetime.fromisoformat(metrics_data["timestamp"]),
                    tokens_used=metrics_data["tokens_used"],
                    tokens_total=metrics_data["tokens_total"],
                    tokens_remaining=metrics_data["tokens_remaining"],
                    usage_percentage=metrics_data["usage_percentage"],
                    status=ContextStatus(metrics_data["status"])
                )
            
            return self.state
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    def get_usage_trend(self, minutes: int = 60) -> Dict[str, Any]:
        """
        獲取使用率趨勢
        
        Args:
            minutes: 分析過去多少分鐘的數據
        
        Returns:
            趨勢分析結果
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {
                "period_minutes": minutes,
                "data_points": 0,
                "trend": "unknown",
                "avg_usage": 0,
                "max_usage": 0,
                "min_usage": 0
            }
        
        usages = [m.usage_percentage for m in recent_metrics]
        
        # 計算趨勢
        if len(usages) >= 2:
            first_half = sum(usages[:len(usages)//2]) / (len(usages)//2)
            second_half = sum(usages[len(usages)//2:]) / (len(usages) - len(usages)//2)
            
            if second_half > first_half * 1.05:
                trend = "increasing"
            elif second_half < first_half * 0.95:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "unknown"
        
        return {
            "period_minutes": minutes,
            "data_points": len(recent_metrics),
            "trend": trend,
            "avg_usage": round(sum(usages) / len(usages), 2),
            "max_usage": round(max(usages), 2),
            "min_usage": round(min(usages), 2),
            "current_usage": round(usages[-1], 2)
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """生成監控報告"""
        return {
            "session_id": self.session_id,
            "report_time": datetime.now().isoformat(),
            "session_state": self.state.to_dict(),
            "config": self.config.to_dict(),
            "current_metrics": self.state.context_metrics.to_dict() if self.state.context_metrics else None,
            "usage_trend_1h": self.get_usage_trend(60),
            "usage_trend_24h": self.get_usage_trend(1440),
            "total_alerts": self.state.alert_count,
            "recommendation": self._generate_recommendation()
        }
    
    def _generate_recommendation(self) -> str:
        """生成建議"""
        if not self.state.context_metrics:
            return "無法生成建議：沒有可用數據"
        
        usage = self.state.context_metrics.usage_percentage
        
        if usage >= 80:
            return (
                "🚨 強烈建議立即開啟新 Session！\n"
                "Context 使用率已達危險水平，繼續使用可能導致:\n"
                "- 響應質量下降\n"
                "- 重要上下文丟失\n"
                "- 系統錯誤\n\n"
                "請執行：保存當前摘要 → 開新 Session → 加載記憶"
            )
        elif usage >= 70:
            return (
                "⚠️ 建議準備開啟新 Session\n"
                "Context 使用率已達預警水平，建議:\n"
                "- 完成當前任務\n"
                "- 準備 Session 摘要\n"
                "- 計劃在 75% 前切換 Session"
            )
        elif usage >= 60:
            return (
                "ℹ️ Context 使用率正常偏高\n"
                "建議注意對話長度，避免一次性發送大量內容。"
            )
        else:
            return "✅ Context 使用率健康，繼續保持。"


class SessionMonitorAPI:
    """
    Session 監控 API
    
    提供 RESTful 風格的接口供外部調用
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("./data/monitor")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._monitors: Dict[str, ContextMonitor] = {}
    
    def create_monitor(
        self,
        session_id: str,
        config: Optional[AlertConfig] = None
    ) -> ContextMonitor:
        """創建新的監控器"""
        if session_id in self._monitors:
            logger.warning(f"Monitor for {session_id} already exists, returning existing")
            return self._monitors[session_id]
        
        monitor = ContextMonitor(session_id, config, self.data_dir)
        self._monitors[session_id] = monitor
        
        logger.info(f"Created monitor for session: {session_id}")
        return monitor
    
    def get_monitor(self, session_id: str) -> Optional[ContextMonitor]:
        """獲取監控器"""
        return self._monitors.get(session_id)
    
    def remove_monitor(self, session_id: str) -> bool:
        """移除監控器"""
        if session_id in self._monitors:
            self._monitors[session_id].stop_monitoring()
            del self._monitors[session_id]
            logger.info(f"Removed monitor for session: {session_id}")
            return True
        return False
    
    def get_all_monitors(self) -> Dict[str, ContextMonitor]:
        """獲取所有監控器"""
        return self._monitors.copy()
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取 Session 狀態
        
        API 端點: GET /api/session/{session_id}/status
        """
        monitor = self.get_monitor(session_id)
        if not monitor:
            return None
        
        return {
            "session_id": session_id,
            "is_active": monitor.state.is_active,
            "created_at": monitor.state.created_at.isoformat(),
            "last_activity": monitor.state.last_activity.isoformat(),
            "alert_count": monitor.state.alert_count,
            "current_metrics": monitor.state.context_metrics.to_dict() if monitor.state.context_metrics else None
        }
    
    def update_context_usage(
        self,
        session_id: str,
        tokens_used: int
    ) -> Optional[ContextMetrics]:
        """
        更新 Context 使用量
        
        API 端點: POST /api/session/{session_id}/context
        """
        monitor = self.get_monitor(session_id)
        if not monitor:
            return None
        
        return monitor.check_and_alert(tokens_used)
    
    def get_usage_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取使用報告
        
        API 端點: GET /api/session/{session_id}/report
        """
        monitor = self.get_monitor(session_id)
        if not monitor:
            return None
        
        return monitor.generate_report()
    
    def get_all_sessions_status(self) -> List[Dict[str, Any]]:
        """
        獲取所有 Session 狀態
        
        API 端點: GET /api/sessions
        """
        return [
            self.get_session_status(sid)
            for sid in self._monitors.keys()
        ]
    
    def register_alert_handler(
        self,
        session_id: str,
        status: str,
        handler: Callable[[ContextMetrics], None]
    ) -> bool:
        """
        註冊警報處理器
        
        API 端點: POST /api/session/{session_id}/handlers
        """
        monitor = self.get_monitor(session_id)
        if not monitor:
            return False
        
        try:
            status_enum = ContextStatus(status)
            monitor.register_callback(status_enum, handler)
            return True
        except ValueError:
            logger.error(f"Invalid status: {status}")
            return False
    
    def shutdown_all(self) -> None:
        """關閉所有監控器"""
        for monitor in self._monitors.values():
            monitor.stop_monitoring()
        self._monitors.clear()
        logger.info("All monitors shutdown")


# 預設警報處理器
def default_warning_handler(metrics: ContextMetrics) -> None:
    """預設預警處理器"""
    print(f"\n{'='*60}")
    print(f"⚠️  Context 使用率預警")
    print(f"{'='*60}")
    print(f"Session ID: {metrics.session_id}")
    print(f"使用率: {metrics.usage_percentage:.1f}%")
    print(f"已使用: {metrics.tokens_used:,} / {metrics.tokens_total:,} tokens")
    print(f"剩餘: {metrics.tokens_remaining:,} tokens")
    print(f"{'='*60}\n")


def default_critical_handler(metrics: ContextMetrics) -> None:
    """預設危險處理器"""
    print(f"\n{'='*60}")
    print(f"🚨  Context 使用率危險 - 自動觸發機制啟動")
    print(f"{'='*60}")
    print(f"Session ID: {metrics.session_id}")
    print(f"使用率: {metrics.usage_percentage:.1f}%")
    print(f"已使用: {metrics.tokens_used:,} / {metrics.tokens_total:,} tokens")
    print(f"剩餘: {metrics.tokens_remaining:,} tokens")
    print(f"\n⚡ 建議操作:")
    print(f"   1. 立即生成 Session 摘要")
    print(f"   2. 保存到向量數據庫")
    print(f"   3. 開啟新 Session")
    print(f"   4. 加載記憶上下文")
    print(f"{'='*60}\n")


# 便捷函數
def create_monitor(
    session_id: str,
    warning_threshold: float = 70.0,
    critical_threshold: float = 80.0,
    auto_handlers: bool = True
) -> ContextMonitor:
    """
    快速創建監控器
    
    Args:
        session_id: Session ID
        warning_threshold: 預警閾值（預設 70%）
        critical_threshold: 危險閾值（預設 80%）
        auto_handlers: 是否自動註冊預設處理器
    
    Returns:
        ContextMonitor 實例
    """
    config = AlertConfig(
        warning_threshold=warning_threshold,
        critical_threshold=critical_threshold
    )
    
    monitor = ContextMonitor(session_id, config)
    
    if auto_handlers:
        monitor.register_callback(ContextStatus.WARNING, default_warning_handler)
        monitor.register_callback(ContextStatus.CRITICAL, default_critical_handler)
    
    return monitor


# 示例用法
if __name__ == "__main__":
    # 創建監控器
    monitor = create_monitor("test_session_001")
    
    # 模擬 Context 使用情況
    test_cases = [
        150000,  # ~58% - 正常
        180000,  # ~70% - 預警
        191000,  # ~75% - 預警（已觸發過）
        210000,  # ~82% - 危險，自動觸發
    ]
    
    print("="*60)
    print("Session Monitor 測試")
    print("="*60)
    
    for tokens in test_cases:
        print(f"\n模擬 tokens 使用: {tokens:,}")
        metrics = monitor.check_and_alert(tokens)
        print(f"狀態: {metrics.status.value}")
        print(f"使用率: {metrics.usage_percentage:.1f}%")
        time.sleep(0.5)
    
    # 生成報告
    print("\n" + "="*60)
    print("監控報告")
    print("="*60)
    report = monitor.generate_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
