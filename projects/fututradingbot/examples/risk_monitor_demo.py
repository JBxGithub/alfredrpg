"""
風控與監控系統使用示例

展示如何整合 RiskManager 和 Monitor 到交易機器人中
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.risk.risk_manager import RiskManager, RiskLimits, Position
from src.monitoring.monitor import Monitor
from src.utils.logger import logger, setup_logger


def demo_risk_management():
    """演示風險管理功能"""
    print("\n" + "="*60)
    print("風險管理系統演示")
    print("="*60)
    
    # 初始化風險管理器
    risk_manager = RiskManager("./config/risk_config.json")
    
    # 設置資金狀況
    risk_manager.update_capital(
        total_capital=1000000,
        margin_used=100000,
        margin_available=400000
    )
    
    # 模擬持倉
    positions = [
        Position(
            symbol="00700",
            quantity=100,
            avg_price=400.0,
            market_price=420.0,
            sector="科技"
        ),
        Position(
            symbol="09988",
            quantity=200,
            avg_price=80.0,
            market_price=85.0,
            sector="科技"
        ),
        Position(
            symbol="00005",
            quantity=1000,
            avg_price=60.0,
            market_price=62.0,
            sector="金融"
        )
    ]
    
    # 更新持倉並檢查風險
    risk_manager.update_positions(positions)
    
    # 檢查交易風險
    print("\n1. 檢查交易風險:")
    can_trade, event = risk_manager.check_trade_risk("00700", 500, 420.0, "BUY")
    print(f"   是否可以買入 500股 00700 @ 420.0: {can_trade}")
    if event:
        print(f"   風險事件: {event.message}")
    
    # 檢查大額交易
    can_trade, event = risk_manager.check_trade_risk("02318", 2000, 100.0, "BUY")
    print(f"\n   是否可以買入 2000股 02318 @ 100.0: {can_trade}")
    if event:
        print(f"   風險事件: {event.message}")
    
    # 檢查資金風險
    print("\n2. 檢查資金風險:")
    risk_events = risk_manager.check_capital_risk(daily_pnl=-30000)
    print(f"   當日虧損 -30,000 的風險事件數: {len(risk_events)}")
    for event in risk_events:
        print(f"   - {event.level.value}: {event.message}")
    
    # 獲取風險摘要
    print("\n3. 風險摘要:")
    summary = risk_manager.get_risk_summary()
    print(f"   總資金: {summary['total_capital']:,.2f}")
    print(f"   持倉總值: {summary['total_position_value']:,.2f}")
    print(f"   當日盈虧: {summary['daily_pnl']:,.2f}")
    print(f"   回撤: {summary['drawdown_percent']:.2f}%")
    print(f"   保證金使用率: {summary['margin_ratio']:.2f}%")
    print(f"   交易啟用狀態: {summary['trading_enabled']}")
    
    # 記錄交易
    risk_manager.record_trade("00700", 100, 420.0, "BUY")
    print(f"\n4. 記錄交易後:")
    print(f"   今日交易次數: {risk_manager.daily_stats['trade_count']}")
    
    return risk_manager


def demo_monitoring():
    """演示監控系統功能"""
    print("\n" + "="*60)
    print("監控系統演示")
    print("="*60)
    
    # 初始化監控器
    monitor = Monitor({
        "metrics_retention_hours": 24,
        "audit_log_dir": "./logs/audit"
    })
    
    # 啟動監控
    monitor.start()
    
    # 更新連接狀態
    monitor.update_connection_status(
        quote_connected=True,
        trade_connected={"HK": True, "US": True}
    )
    
    # 更新策略狀態
    monitor.update_strategy_status("ma_crossover", {
        "status": "running",
        "last_signal": "BUY",
        "signal_time": datetime.now().isoformat()
    })
    
    # 更新交易統計
    monitor.update_trading_stats(
        daily_pnl=15000.0,
        total_pnl=125000.0,
        total_trades=10,
        successful=8,
        failed=2
    )
    
    # 記錄交易
    monitor.record_trade("00700", "BUY", 100, 420.0, "ORD123456", "success")
    
    # 發送風控警報
    monitor.send_risk_alert(
        event_type="POSITION_LIMIT_EXCEEDED",
        message="00700 倉位超過限制",
        level="warning",
        data={"symbol": "00700", "current": 120000, "limit": 100000}
    )
    
    # 獲取監控面板數據
    print("\n1. 監控面板數據:")
    dashboard = monitor.get_dashboard_data()
    
    print(f"   系統運行中: {dashboard['system_status']['is_running']}")
    print(f"   行情連接: {dashboard['system_status']['quote_connected']}")
    print(f"   交易連接: {dashboard['system_status']['trade_connected']}")
    print(f"   當日盈虧: {dashboard['trading_stats']['daily_pnl']:,.2f}")
    print(f"   今日交易: {dashboard['trading_stats']['total_trades_today']}")
    print(f"   未確認警報: {dashboard['unacknowledged_alerts']}")
    
    # 獲取系統健康狀態
    print("\n2. 系統健康狀態:")
    health = monitor.get_system_health()
    print(f"   健康狀態: {'良好' if health['healthy'] else '有問題'}")
    if health['issues']:
        for issue in health['issues']:
            print(f"   - [{issue['level']}] {issue['message']}")
    
    # 查詢審計日誌
    print("\n3. 最近審計日誌:")
    logs = monitor.audit.query_logs(limit=5)
    for log in logs:
        print(f"   [{log['timestamp']}] {log['action']} by {log['user']}")
    
    # 停止監控
    monitor.stop()
    print("\n監控系統已停止")
    
    return monitor


def demo_integration():
    """演示風控與監控整合使用"""
    print("\n" + "="*60)
    print("風控與監控整合演示")
    print("="*60)
    
    # 初始化
    risk_manager = RiskManager("./config/risk_config.json")
    monitor = Monitor()
    
    monitor.start()
    
    # 設置初始狀態
    risk_manager.update_capital(1000000, 0, 500000)
    monitor.update_capital = lambda *args: risk_manager.update_capital(*args)
    
    print("\n1. 模擬正常交易流程:")
    
    # 檢查交易風險
    symbol, quantity, price = "00700", 100, 420.0
    can_trade, event = risk_manager.check_trade_risk(symbol, quantity, price, "BUY")
    
    if can_trade:
        print(f"   ✓ 允許買入 {symbol} {quantity}股 @ {price}")
        risk_manager.record_trade(symbol, quantity, price, "BUY")
        monitor.record_trade(symbol, "BUY", quantity, price, "ORD001", "success")
    else:
        print(f"   ✗ 拒絕交易: {event.message}")
        monitor.send_risk_alert(
            event.event_type.value,
            event.message,
            event.level.value,
            event.details
        )
    
    print("\n2. 模擬風控觸發:")
    
    # 嘗試大額交易
    symbol, quantity, price = "02318", 5000, 100.0
    can_trade, event = risk_manager.check_trade_risk(symbol, quantity, price, "BUY")
    
    if can_trade:
        print(f"   ✓ 允許買入 {symbol} {quantity}股 @ {price}")
    else:
        print(f"   ✗ 拒絕交易: {event.message}")
        monitor.send_risk_alert(
            event.event_type.value,
            event.message,
            event.level.value,
            event.details
        )
    
    print("\n3. 模擬回撤控制:")
    
    # 更新資金（模擬虧損）
    risk_manager.update_capital(850000, 0, 500000)  # 虧損 15%
    events = risk_manager.check_capital_risk(daily_pnl=-150000)
    
    for event in events:
        print(f"   ! {event.level.value.upper()}: {event.message}")
        monitor.send_risk_alert(
            event.event_type.value,
            event.message,
            event.level.value,
            event.details
        )
    
    print(f"\n   交易狀態: {'啟用' if risk_manager.is_trading_enabled() else '已禁用'}")
    
    # 獲取綜合報告
    print("\n4. 綜合風控報告:")
    risk_summary = risk_manager.get_risk_summary()
    dashboard = monitor.get_dashboard_data()
    
    print(f"   當前資金: {risk_summary['total_capital']:,.2f}")
    print(f"   峰值資金: {risk_summary['peak_capital']:,.2f}")
    print(f"   當前回撤: {risk_summary['drawdown_percent']:.2f}%")
    print(f"   今日交易: {risk_summary['daily_trade_count']}")
    print(f"   系統運行時間: {dashboard['system_status']['uptime_seconds']:.0f}秒")
    
    monitor.stop()


if __name__ == "__main__":
    # 設置日誌
    setup_logger(None)
    
    # 運行演示
    try:
        demo_risk_management()
        demo_monitoring()
        demo_integration()
        
        print("\n" + "="*60)
        print("所有演示完成！")
        print("="*60)
        
    except Exception as e:
        logger.exception(f"演示出錯: {e}")
        raise
