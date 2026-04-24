"""
風險管理與監控系統測試
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime, date

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.risk.risk_manager import (
    RiskManager, RiskLimits, RiskEvent, 
    RiskLevel, RiskEventType, Position
)
from src.monitoring.monitor import (
    Monitor, AlertManager, MetricsCollector, 
    AuditLogger, Alert, AlertType
)


class TestRiskManager(unittest.TestCase):
    """測試風險管理器"""
    
    def setUp(self):
        """測試前設置"""
        self.risk_manager = RiskManager()
        self.risk_manager.update_capital(1000000, 0, 500000)
    
    def test_position_limits(self):
        """測試倉位限制"""
        # 創建超過限制的持倉
        positions = [
            Position(
                symbol="TEST",
                quantity=10000,
                avg_price=100.0,
                market_price=150.0,
                sector="科技"
            )
        ]
        
        self.risk_manager.update_positions(positions)
        
        # 檢查是否產生風險事件
        summary = self.risk_manager.get_risk_summary()
        self.assertTrue(len(summary['recent_events']) > 0)
    
    def test_trade_risk_check(self):
        """測試交易風險檢查"""
        # 正常交易
        can_trade, event = self.risk_manager.check_trade_risk("00700", 100, 400.0, "BUY")
        self.assertTrue(can_trade)
        self.assertIsNone(event)
        
        # 超過單筆金額限制
        can_trade, event = self.risk_manager.check_trade_risk("00700", 10000, 100.0, "BUY")
        self.assertFalse(can_trade)
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, RiskEventType.ORDER_SIZE_EXCEEDED)
    
    def test_daily_trade_limit(self):
        """測試每日交易次數限制"""
        # 模擬達到交易次數上限
        self.risk_manager.daily_stats["trade_count"] = 20
        
        can_trade, event = self.risk_manager.check_trade_risk("00700", 100, 400.0, "BUY")
        self.assertFalse(can_trade)
        self.assertEqual(event.event_type, RiskEventType.DAILY_TRADE_LIMIT_EXCEEDED)
    
    def test_capital_risk_drawdown(self):
        """測試回撤控制"""
        # 設置峰值資金
        self.risk_manager.peak_capital = 1000000
        self.risk_manager.current_capital = 850000  # 15% 回撤
        
        events = self.risk_manager.check_capital_risk(0)
        
        # 應該觸發回撤警告
        drawdown_events = [e for e in events if e.event_type == RiskEventType.DRAWDOWN_LIMIT_EXCEEDED]
        self.assertTrue(len(drawdown_events) > 0)
        
        # 交易應該被禁用
        self.assertFalse(self.risk_manager.is_trading_enabled())
    
    def test_daily_loss_limit(self):
        """測試每日虧損限制"""
        events = self.risk_manager.check_capital_risk(-60000)  # 超過 50000 限制
        
        loss_events = [e for e in events if e.event_type == RiskEventType.DAILY_LOSS_LIMIT_EXCEEDED]
        self.assertTrue(len(loss_events) > 0)
        self.assertEqual(loss_events[0].level, RiskLevel.CRITICAL)


class TestAlertManager(unittest.TestCase):
    """測試警報管理器"""
    
    def setUp(self):
        """測試前設置"""
        self.alert_manager = AlertManager()
    
    def test_send_alert(self):
        """測試發送警報"""
        self.alert_manager.send_alert(
            AlertType.RISK_WARNING,
            "測試警報",
            "這是一個測試警報",
            "warning"
        )
        
        self.assertEqual(len(self.alert_manager.alerts), 1)
        self.assertEqual(self.alert_manager.alerts[0].title, "測試警報")
    
    def test_alert_deduplication(self):
        """測試警報去重"""
        # 發送相同警報多次
        for _ in range(3):
            self.alert_manager.send_alert(
                AlertType.RISK_WARNING,
                "重複警報",
                "這個警報應該被去重",
                "warning"
            )
        
        # 應該只有一個警報（在短時間內）
        self.assertEqual(len(self.alert_manager.alerts), 1)
    
    def test_acknowledge_alert(self):
        """測試確認警報"""
        self.alert_manager.send_alert(
            AlertType.RISK_WARNING,
            "待確認警報",
            "請確認此警報",
            "warning"
        )
        
        # 確認警報
        self.alert_manager.acknowledge_alert(0, "test_user")
        
        self.assertTrue(self.alert_manager.alerts[0].acknowledged)
        self.assertEqual(self.alert_manager.alerts[0].acknowledged_by, "test_user")


class TestMetricsCollector(unittest.TestCase):
    """測試指標收集器"""
    
    def setUp(self):
        """測試前設置"""
        self.metrics = MetricsCollector()
    
    def test_record_and_get(self):
        """測試記錄和獲取指標"""
        # 記錄一些指標
        for i in range(10):
            self.metrics.record("test_metric", float(i))
        
        # 獲取指標
        points = self.metrics.get_metric("test_metric")
        self.assertEqual(len(points), 10)
        
        # 檢查最新值
        latest = self.metrics.get_latest("test_metric")
        self.assertEqual(latest.value, 9.0)
    
    def test_statistics(self):
        """測試統計功能"""
        # 記錄測試數據
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for v in values:
            self.metrics.record("stat_test", v)
        
        stats = self.metrics.get_statistics("stat_test")
        
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["min"], 10.0)
        self.assertEqual(stats["max"], 50.0)
        self.assertEqual(stats["avg"], 30.0)


class TestAuditLogger(unittest.TestCase):
    """測試審計日誌器"""
    
    def setUp(self):
        """測試前設置"""
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.audit = AuditLogger(log_dir=self.temp_dir)
    
    def test_log_action(self):
        """測試記錄操作"""
        self.audit.log("test_action", "test_user", {"key": "value"}, "success")
        
        # 查詢日誌
        logs = self.audit.query_logs(action="test_action")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], "test_action")
        self.assertEqual(logs[0]["user"], "test_user")
    
    def test_log_trade(self):
        """測試記錄交易"""
        self.audit.log_trade("00700", "BUY", 100, 420.0, "ORD123", "success")
        
        logs = self.audit.query_logs(action="trade")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["details"]["symbol"], "00700")


class TestIntegration(unittest.TestCase):
    """整合測試"""
    
    def test_risk_monitor_integration(self):
        """測試風控與監控整合"""
        risk_manager = RiskManager()
        monitor = Monitor()
        
        # 設置資金
        risk_manager.update_capital(1000000, 0, 500000)
        
        # 檢查風險並發送警報
        can_trade, event = risk_manager.check_trade_risk("TEST", 10000, 1000.0, "BUY")
        
        if not can_trade:
            # 通過監控系統發送警報
            monitor.alert_manager.send_alert(
                AlertType.RISK_WARNING,
                "風控警報",
                event.message,
                event.level.value,
                event.details
            )
            
            # 記錄審計日誌
            monitor.audit.log_risk_event(
                event.event_type.value,
                event.message,
                event.level.value,
                event.details
            )
        
        # 驗證
        self.assertFalse(can_trade)
        self.assertEqual(len(monitor.alert_manager.alerts), 1)


if __name__ == "__main__":
    unittest.main()
