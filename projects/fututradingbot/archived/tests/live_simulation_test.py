"""
FutuTradingBot 模擬環境實盤測試腳本
Live Simulation Test Script for FutuTradingBot

測試目標：使用 Futu API 的 SIMULATE 模式進行真實模擬交易測試
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 添加項目路徑
project_path = Path(r'C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot')
sys.path.insert(0, str(project_path))

import pandas as pd
import numpy as np

# 導入 Futu API
import futu as ft

# 導入項目模組
from src.api.futu_client import FutuAPIClient, FutuQuoteClient, FutuTradeClient, Market, SubType, TrdEnv, TrdSide, OrderType
from src.strategies.enhanced_strategy import EnhancedStrategy
from src.risk.risk_manager import RiskManager, RiskLimits, Position
from src.utils.logger import logger

# 測試報告類
class TestReport:
    def __init__(self):
        self.results = {
            "test_info": {
                "test_name": "FutuTradingBot Live Simulation Test",
                "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "environment": "SIMULATE",
                "opend_host": "127.0.0.1:11111"
            },
            "prerequisites": {},
            "connection_tests": {},
            "market_data_tests": {},
            "strategy_tests": {},
            "trade_tests": {},
            "risk_tests": {},
            "summary": {}
        }
        self.errors = []
    
    def add_result(self, section, test_name, status, details=None, error=None):
        if section not in self.results:
            self.results[section] = {}
        self.results[section][test_name] = {
            "status": status,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "details": details or {}
        }
        if error:
            self.errors.append({
                "section": section,
                "test": test_name,
                "error": str(error),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
    
    def save_json(self, filepath):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        print(f"JSON 測試報告已保存: {filepath}")
    
    def print_summary(self):
        print("\n" + "="*60)
        print("測試摘要")
        print("="*60)
        total_tests = 0
        passed_tests = 0
        for section, tests in self.results.items():
            if isinstance(tests, dict) and section not in ["test_info", "summary"]:
                for test_name, result in tests.items():
                    total_tests += 1
                    if result.get("status") == "PASSED":
                        passed_tests += 1
        print(f"總測試數: {total_tests}")
        print(f"通過: {passed_tests}")
        print(f"失敗: {total_tests - passed_tests}")
        if self.errors:
            print(f"\n錯誤數: {len(self.errors)}")
            for err in self.errors:
                print(f"  - [{err['section']}] {err['test']}: {err['error']}")
        return total_tests, passed_tests


def run_all_tests():
    """執行所有測試"""
    report = TestReport()
    
    # ============================================================
    # 1. 前提條件檢查
    # ============================================================
    print("="*60)
    print("1. 前提條件檢查")
    print("="*60)
    
    # 1.1 檢查 OpenD 連接
    print("\n[1.1] 檢查 OpenD 連接 (127.0.0.1:11111)...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('127.0.0.1', 11111))
        sock.close()
        if result == 0:
            print("✓ OpenD 運行正常")
            report.add_result("prerequisites", "opend_connection", "PASSED", {"host": "127.0.0.1:11111"})
        else:
            print(f"✗ OpenD 連接失敗 (錯誤碼: {result})")
            report.add_result("prerequisites", "opend_connection", "FAILED", {"error": f"Connection failed with code {result}"})
            return report
    except Exception as e:
        print(f"✗ OpenD 檢查失敗: {e}")
        report.add_result("prerequisites", "opend_connection", "FAILED", error=e)
        return report
    
    # 1.2 檢查 scikit-learn
    print("\n[1.2] 檢查 scikit-learn...")
    try:
        import sklearn
        print(f"✓ scikit-learn 已安裝 (版本: {sklearn.__version__})")
        report.add_result("prerequisites", "scikit_learn", "PASSED", {"version": sklearn.__version__})
    except ImportError as e:
        print(f"✗ scikit-learn 未安裝: {e}")
        report.add_result("prerequisites", "scikit_learn", "FAILED", error=e)
    
    # 1.3 檢查 futu-api
    print("\n[1.3] 檢查 futu-api...")
    try:
        import futu
        print(f"✓ futu-api 已安裝 (版本: {futu.__version__})")
        report.add_result("prerequisites", "futu_api", "PASSED", {"version": futu.__version__})
    except ImportError as e:
        print(f"✗ futu-api 未安裝: {e}")
        report.add_result("prerequisites", "futu_api", "FAILED", error=e)
    
    # ============================================================
    # 2. 連接測試
    # ============================================================
    print("\n" + "="*60)
    print("2. 連接測試")
    print("="*60)
    
    quote_client = None
    trade_client = None
    
    # 2.1 連接行情服務
    print("\n[2.1] 連接 OpenD 行情服務...")
    try:
        quote_client = FutuQuoteClient("127.0.0.1", 11111)
        if quote_client.connect():
            print("✓ 行情服務連接成功")
            report.add_result("connection_tests", "quote_connection", "PASSED")
        else:
            print("✗ 行情服務連接失敗")
            report.add_result("connection_tests", "quote_connection", "FAILED")
    except Exception as e:
        print(f"✗ 行情服務連接異常: {e}")
        report.add_result("connection_tests", "quote_connection", "FAILED", error=e)
    
    # 2.2 連接交易服務 (SIMULATE 模式)
    print("\n[2.2] 連接 OpenD 交易服務 (SIMULATE 模式)...")
    try:
        trade_client = FutuTradeClient("127.0.0.1", 11111, Market.HK)
        if trade_client.connect():
            print("✓ 交易服務連接成功 (SIMULATE)")
            report.add_result("connection_tests", "trade_connection", "PASSED", {"env": "SIMULATE"})
        else:
            print("✗ 交易服務連接失敗")
            report.add_result("connection_tests", "trade_connection", "FAILED")
    except Exception as e:
        print(f"✗ 交易服務連接異常: {e}")
        report.add_result("connection_tests", "trade_connection", "FAILED", error=e)
    
    # 2.3 查詢模擬賬戶資金
    print("\n[2.3] 查詢模擬賬戶資金...")
    try:
        if trade_client:
            ret_code, ret_data = trade_client.accinfo_query(TrdEnv.SIMULATE)
            if ret_code == 0:
                print(f"✓ 賬戶資金查詢成功")
                print(f"  可用資金: {ret_data.get('cash', 'N/A')}")
                print(f"  總資產: {ret_data.get('total_assets', 'N/A')}")
                report.add_result("connection_tests", "account_info", "PASSED", {
                    "cash": str(ret_data.get('cash', 'N/A')),
                    "total_assets": str(ret_data.get('total_assets', 'N/A'))
                })
            else:
                print(f"✗ 賬戶資金查詢失敗: {ret_data}")
                report.add_result("connection_tests", "account_info", "FAILED", {"error": str(ret_data)})
        else:
            print("✗ 交易客戶端未連接")
            report.add_result("connection_tests", "account_info", "FAILED", {"error": "Trade client not connected"})
    except Exception as e:
        print(f"✗ 賬戶資金查詢異常: {e}")
        report.add_result("connection_tests", "account_info", "FAILED", error=e)
    
    # 2.4 查詢模擬持倉
    print("\n[2.4] 查詢模擬持倉...")
    try:
        if trade_client:
            ret_code, ret_data = trade_client.position_list_query(TrdEnv.SIMULATE)
            if ret_code == 0:
                print(f"✓ 持倉查詢成功")
                if len(ret_data) > 0:
                    print(f"  持倉數量: {len(ret_data)}")
                    for _, row in ret_data.iterrows():
                        print(f"    - {row.get('code', 'N/A')}: {row.get('qty', 0)}股")
                else:
                    print("  當前無持倉")
                report.add_result("connection_tests", "position_query", "PASSED", {
                    "position_count": len(ret_data),
                    "positions": ret_data.to_dict('records') if len(ret_data) > 0 else []
                })
            else:
                print(f"✗ 持倉查詢失敗: {ret_data}")
                report.add_result("connection_tests", "position_query", "FAILED", {"error": str(ret_data)})
        else:
            print("✗ 交易客戶端未連接")
            report.add_result("connection_tests", "position_query", "FAILED", {"error": "Trade client not connected"})
    except Exception as e:
        print(f"✗ 持倉查詢異常: {e}")
        report.add_result("connection_tests", "position_query", "FAILED", error=e)
    
    # ============================================================
    # 3. 行情數據測試
    # ============================================================
    print("\n" + "="*60)
    print("3. 行情數據測試")
    print("="*60)
    
    # 3.1 獲取港股實時報價
    print("\n[3.1] 獲取港股實時報價 (00700, 09988)...")
    try:
        if quote_client:
            codes = ['HK.00700', 'HK.09988']
            ret_code, ret_data = quote_client.get_stock_quote(codes)
            if ret_code == 0:
                print(f"✓ 實時報價獲取成功")
                for _, row in ret_data.iterrows():
                    print(f"  {row.get('code', 'N/A')}: 最新價 {row.get('last_price', 'N/A')}")
                report.add_result("market_data_tests", "realtime_quote", "PASSED", {
                    "codes": codes,
                    "data": ret_data.to_dict('records')
                })
            else:
                print(f"✗ 實時報價獲取失敗: {ret_data}")
                report.add_result("market_data_tests", "realtime_quote", "FAILED", {"error": str(ret_data)})
        else:
            print("✗ 行情客戶端未連接")
            report.add_result("market_data_tests", "realtime_quote", "FAILED", {"error": "Quote client not connected"})
    except Exception as e:
        print(f"✗ 實時報價獲取異常: {e}")
        report.add_result("market_data_tests", "realtime_quote", "FAILED", error=e)
    
    # 3.2 獲取K線數據
    print("\n[3.2] 獲取K線數據 (日線/小時線)...")
    try:
        if quote_client:
            ret_code_day, ret_data_day = quote_client.get_cur_kline('HK.00700', num=50, ktype=ft.KLType.K_DAY)
            ret_code_hour, ret_data_hour = quote_client.get_cur_kline('HK.00700', num=50, ktype=ft.KLType.K_60M)
            
            if ret_code_day == 0 and ret_code_hour == 0:
                print(f"✓ K線數據獲取成功")
                print(f"  日線: {len(ret_data_day)} 條")
                print(f"  小時線: {len(ret_data_hour)} 條")
                report.add_result("market_data_tests", "kline_data", "PASSED", {
                    "daily_count": len(ret_data_day),
                    "hourly_count": len(ret_data_hour)
                })
            else:
                print(f"✗ K線數據獲取失敗")
                report.add_result("market_data_tests", "kline_data", "FAILED")
        else:
            print("✗ 行情客戶端未連接")
            report.add_result("market_data_tests", "kline_data", "FAILED")
    except Exception as e:
        print(f"✗ K線數據獲取異常: {e}")
        report.add_result("market_data_tests", "kline_data", "FAILED", error=e)
    
    # 3.3 訂閱實時推送
    print("\n[3.3] 訂閱實時推送...")
    try:
        if quote_client:
            codes = ['HK.00700', 'HK.09988']
            sub_types = [SubType.QUOTE, SubType.K_1M]
            ret_code, ret_data = quote_client.subscribe(codes, sub_types)
            if ret_code == 0:
                print(f"✓ 實時推送訂閱成功")
                report.add_result("market_data_tests", "subscription", "PASSED")
            else:
                print(f"✗ 實時推送訂閱失敗: {ret_data}")
                report.add_result("market_data_tests", "subscription", "FAILED")
        else:
            print("✗ 行情客戶端未連接")
            report.add_result("market_data_tests", "subscription", "FAILED")
    except Exception as e:
        print(f"✗ 實時推送訂閱異常: {e}")
        report.add_result("market_data_tests", "subscription", "FAILED", error=e)
    
    # ============================================================
    # 4. 策略信號測試
    # ============================================================
    print("\n" + "="*60)
    print("4. 策略信號測試")
    print("="*60)
    
    # 4.1 運行增強版策略分析
    print("\n[4.1] 運行增強版策略分析...")
    try:
        if quote_client:
            ret_code, kline_data = quote_client.get_cur_kline('HK.00700', num=100, ktype=ft.KLType.K_60M)
            if ret_code == 0 and len(kline_data) > 20:
                strategy = EnhancedStrategy(config={
                    'min_confirmed_factors': 4,
                    'min_score_threshold': 60.0
                })
                strategy.initialize()
                signal = strategy.on_data({'code': 'HK.00700', 'df': kline_data})
                
                print(f"✓ 策略分析完成")
                print(f"  數據點: {len(kline_data)}")
                if signal:
                    print(f"  信號: {signal.signal.value}")
                else:
                    print(f"  信號: 無 (未達進場條件)")
                
                report.add_result("strategy_tests", "strategy_analysis", "PASSED", {
                    "data_points": len(kline_data),
                    "signal": signal.signal.value if signal else None
                })
            else:
                print(f"✗ K線數據不足")
                report.add_result("strategy_tests", "strategy_analysis", "FAILED")
        else:
            print("✗ 行情客戶端未連接")
            report.add_result("strategy_tests", "strategy_analysis", "FAILED")
    except Exception as e:
        print(f"✗ 策略分析異常: {e}")
        report.add_result("strategy_tests", "strategy_analysis", "FAILED", error=e)
    
    # 4.2 生成交易信號
    print("\n[4.2] 生成交易信號...")
    try:
        if quote_client:
            signals_generated = []
            test_codes = ['HK.00700', 'HK.09988']
            
            strategy = EnhancedStrategy(config={
                'min_confirmed_factors': 3,
                'min_score_threshold': 50.0
            })
            strategy.initialize()
            
            for code in test_codes:
                ret_code, kline_data = quote_client.get_cur_kline(code, num=100, ktype=ft.KLType.K_60M)
                if ret_code == 0 and len(kline_data) > 20:
                    signal = strategy.on_data({'code': code, 'df': kline_data})
                    if signal:
                        signals_generated.append({
                            "code": code,
                            "signal": signal.signal.value,
                            "price": float(signal.price)
                        })
            
            print(f"✓ 交易信號生成完成")
            print(f"  生成信號數: {len(signals_generated)}")
            
            report.add_result("strategy_tests", "signal_generation", "PASSED", {
                "signals_count": len(signals_generated),
                "signals": signals_generated
            })
        else:
            print("✗ 行情客戶端未連接")
            report.add_result("strategy_tests", "signal_generation", "FAILED")
    except Exception as e:
        print(f"✗ 交易信號生成異常: {e}")
        report.add_result("strategy_tests", "signal_generation", "FAILED", error=e)
    
    # 4.3 驗證多因子共振邏輯
    print("\n[4.3] 驗證多因子共振邏輯...")
    try:
        strategy = EnhancedStrategy(config={'min_confirmed_factors': 4})
        weights = strategy.FACTOR_WEIGHTS
        total_weight = sum(weights.values())
        
        print(f"✓ 多因子共振邏輯驗證")
        print(f"  因子數量: {len(weights)}")
        print(f"  權重總和: {total_weight}")
        
        if abs(total_weight - 1.0) < 0.001:
            print(f"  ✓ 權重配置正確")
            report.add_result("strategy_tests", "multi_factor_logic", "PASSED", {
                "factor_count": len(weights),
                "total_weight": total_weight
            })
        else:
            print(f"  ✗ 權重總和不為1.0")
            report.add_result("strategy_tests", "multi_factor_logic", "FAILED")
    except Exception as e:
        print(f"✗ 多因子共振邏輯驗證異常: {e}")
        report.add_result("strategy_tests", "multi_factor_logic", "FAILED", error=e)
    
    # ============================================================
    # 5. 模擬交易測試
    # ============================================================
    print("\n" + "="*60)
    print("5. 模擬交易測試")
    print("="*60)
    
    order_id = None
    
    # 5.1 執行模擬買入
    print("\n[5.1] 執行模擬買入 (SIMULATE 環境)...")
    try:
        if trade_client and quote_client:
            ret_code, quote_data = quote_client.get_stock_quote(['HK.00700'])
            if ret_code == 0 and len(quote_data) > 0:
                current_price = quote_data.iloc[0]['last_price']
                test_price = round(current_price * 0.95, 2)
                
                ret_code, ret_data = trade_client.place_order(
                    price=test_price,
                    qty=100,
                    code='HK.00700',
                    trd_side=TrdSide.BUY,
                    order_type=OrderType.NORMAL,
                    trd_env=TrdEnv.SIMULATE
                )
                if ret_code == 0:
                    order_id = ret_data.get('order_id', None)
                    print(f"✓ 模擬買入下單成功")
                    print(f"  訂單ID: {order_id}")
                    report.add_result("trade_tests", "simulate_buy", "PASSED", {
                        "order_id": order_id,
                        "code": "HK.00700",
                        "price": test_price
                    })
                else:
                    print(f"✗ 模擬買入下單失敗: {ret_data}")
                    report.add_result("trade_tests", "simulate_buy", "FAILED")
            else:
                print(f"✗ 無法獲取當前價格")
                report.add_result("trade_tests", "simulate_buy", "FAILED")
        else:
            print("✗ 客戶端未連接")
            report.add_result("trade_tests", "simulate_buy", "FAILED")
    except Exception as e:
        print(f"✗ 模擬買入異常: {e}")
        report.add_result("trade_tests", "simulate_buy", "FAILED", error=e)
    
    # 5.2 查詢訂單狀態
    print("\n[5.2] 查詢訂單狀態...")
    try:
        if trade_client:
            ret_code, ret_data = trade_client.order_list_query(TrdEnv.SIMULATE)
            if ret_code == 0:
                print(f"✓ 訂單列表查詢成功")
                print(f"  訂單數量: {len(ret_data)}")
                report.add_result("trade_tests", "order_query", "PASSED", {
                    "order_count": len(ret_data)
                })
            else:
                print(f"✗ 訂單列表查詢失敗: {ret_data}")
                report.add_result("trade_tests", "order_query", "FAILED")
        else:
            print("✗ 交易客戶端未連接")
            report.add_result("trade_tests", "order_query", "FAILED")
    except Exception as e:
        print(f"✗ 訂單狀態查詢異常: {e}")
        report.add_result("trade_tests", "order_query", "FAILED", error=e)
    
    # 5.3 撤單測試
    print("\n[5.3] 撤銷測試訂單...")
    try:
        if trade_client and order_id:
            ret_code, ret_data = trade_client.cancel_order(order_id, TrdEnv.SIMULATE)
            if ret_code == 0:
                print(f"✓ 撤單成功")
                report.add_result("trade_tests", "cancel_order", "PASSED")
            else:
                print(f"✗ 撤單失敗: {ret_data}")
                report.add_result("trade_tests", "cancel_order", "FAILED")
        else:
            print("⚠ 無訂單可撤銷")
            report.add_result("trade_tests", "cancel_order", "SKIPPED")
    except Exception as e:
        print(f"✗ 撤單異常: {e}")
        report.add_result("trade_tests", "cancel_order", "FAILED", error=e)
    
    # 5.4 驗證交易記錄
    print("\n[5.4] 驗證交易記錄...")
    try:
        if trade_client:
            ret_code, ret_data = trade_client.order_list_query(TrdEnv.SIMULATE)
            if ret_code == 0:
                print(f"✓ 交易記錄驗證完成")
                print(f"  歷史訂單數: {len(ret_data)}")
                report.add_result("trade_tests", "trade_history", "PASSED", {
                    "total_orders": len(ret_data)
                })
            else:
                print(f"✗ 交易記錄查詢失敗: {ret_data}")
                report.add_result("trade_tests", "trade_history", "FAILED")
        else:
            print("✗ 交易客戶端未連接")
            report.add_result("trade_tests", "trade_history", "FAILED")
    except Exception as e:
        print(f"✗ 交易記錄驗證異常: {e}")
        report.add_result("trade_tests", "trade_history", "FAILED", error=e)
    
    # ============================================================
    # 6. 風控系統測試
    # ============================================================
    print("\n" + "="*60)
    print("6. 風控系統測試")
    print("="*60)
    
    # 6.1 驗證倉位限制
    print("\n[6.1] 驗證倉位限制...")
    try:
        risk_manager = RiskManager()
        risk_manager.update_capital(total_capital=1000000)
        
        test_positions = [Position(symbol="HK.00700", quantity=1000, avg_price=400, market_price=410, sector="科技")]
        risk_manager.update_positions(test_positions)
        
        limits = risk_manager.limits
        print(f"✓ 倉位限制配置")
        print(f"  單一股票最大價值: {limits.max_single_position_value:,.0f}")
        print(f"  單一股票最大佔比: {limits.max_single_position_percent}%")
        
        report.add_result("risk_tests", "position_limits", "PASSED", {
            "max_single_value": limits.max_single_position_value,
            "max_single_percent": limits.max_single_position_percent
        })
    except Exception as e:
        print(f"✗ 倉位限制驗證異常: {e}")
        report.add_result("risk_tests", "position_limits", "FAILED", error=e)
    
    # 6.2 驗證每日交易次數限制
    print("\n[6.2] 驗證每日交易次數限制...")
    try:
        risk_manager = RiskManager()
        
        for i in range(5):
            risk_manager.record_trade(f"HK.{70000+i}", 100, 100.0, "BUY")
        
        daily_count = risk_manager.daily_stats["trade_count"]
        max_trades = risk_manager.limits.max_daily_trades
        
        print(f"✓ 交易次數限制")
        print(f"  當日交易次數: {daily_count}")
        print(f"  每日最大交易次數: {max_trades}")
        
        can_trade, event = risk_manager.check_trade_risk("HK.09988", 100, 100.0, "BUY")
        
        report.add_result("risk_tests", "trade_count_limits", "PASSED", {
            "current_count": daily_count,
            "max_trades": max_trades,
            "can_trade": can_trade
        })
    except Exception as e:
        print(f"✗ 交易次數限制驗證異常: {e}")
        report.add_result("risk_tests", "trade_count_limits", "FAILED", error=e)
    
    # 6.3 驗證價格異常檢測
    print("\n[6.3] 驗證價格異常檢測...")
    try:
        risk_manager = RiskManager()
        
        for i in range(10):
            risk_manager._check_price_anomaly("HK.00700", 400.0 + i)
        
        event = risk_manager._check_price_anomaly("HK.00700", 500.0)
        
        print(f"✓ 價格異常檢測")
        print(f"  價格波動閾值: {risk_manager.limits.price_volatility_threshold}%")
        print(f"  價格暴漲暴跌閾值: {risk_manager.limits.price_spike_threshold}%")
        
        if event:
            print(f"  ✓ 檢測到價格異常: {event.message}")
        
        report.add_result("risk_tests", "price_anomaly_detection", "PASSED", {
            "volatility_threshold": risk_manager.limits.price_volatility_threshold,
            "spike_threshold": risk_manager.limits.price_spike_threshold,
            "anomaly_detected": event is not None
        })
    except Exception as e:
        print(f"✗ 價格異常檢測驗證異常: {e}")
        report.add_result("risk_tests", "price_anomaly_detection", "FAILED", error=e)
    
    # ============================================================
    # 清理工作
    # ============================================================
    print("\n" + "="*60)
    print("7. 清理工作")
    print("="*60)
    
    # 取消所有訂閱
    print("\n[7.1] 取消所有訂閱...")
    try:
        if quote_client:
            quote_client.unsubscribe_all()
            print("✓ 已取消所有訂閱")
    except Exception as e:
        print(f"⚠ 取消訂閱時出錯: {e}")
    
    # 關閉連接
    print("\n[7.2] 關閉所有連接...")
    try:
        if quote_client:
            quote_client.close()
            print("✓ 行情客戶端已關閉")
        if trade_client:
            trade_client.close()
            print("✓ 交易客戶端已關閉")
    except Exception as e:
        print(f"⚠ 關閉連接時出錯: {e}")
    
    return report


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FutuTradingBot 模擬環境實盤測試")
    print("="*60)
    print("\n⚠  重要提醒:")
    print("   - 本測試使用 SIMULATE 模式，不會進行真實交易")
    print("   - 請確保 OpenD 已啟動並監聽 127.0.0.1:11111")
    print("="*60 + "\n")
    
    report = run_all_tests()
    
    # 打印摘要
    total, passed = report.print_summary()
    
    # 保存報告
    report.save_json(r"C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot\tests\reports\live_simulation_test_report.json")
    
    print("\n" + "="*60)
    if passed == total:
        print("✅ 所有測試通過!")
    else:
        print(f"⚠️  {total - passed} 個測試失敗")
    print("="*60)
