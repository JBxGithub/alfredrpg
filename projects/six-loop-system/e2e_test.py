"""
端到端測試 - 六循環系統
測試完整交易流程
"""

import sys
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/private skills/node-red-automation')

import psycopg2
import requests
import socket
from datetime import datetime, timezone
import json

# Test configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'trading_db',
    'user': 'postgres',
    'password': 'PostgresqL'
}

NODE_RED_URL = "http://localhost:1880"
FUTU_HOST = "127.0.0.1"
FUTU_PORT = 11111

class E2ETester:
    """端到端測試器"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test(self, name, test_func):
        """執行單個測試"""
        print(f"\n🧪 測試: {name}")
        try:
            result = test_func()
            if result:
                print(f"   ✅ 通過")
                self.passed += 1
                self.results.append((name, True, None))
            else:
                print(f"   ❌ 失敗")
                self.failed += 1
                self.results.append((name, False, "返回 False"))
        except Exception as e:
            print(f"   ❌ 異常: {e}")
            self.failed += 1
            self.results.append((name, False, str(e)))
    
    def test_database_connection(self):
        """測試數據庫連接"""
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] == 1
    
    def test_futu_data_flow(self):
        """測試 Futu 數據流"""
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check for today's Futu data
        cursor.execute('''
            SELECT COUNT(*), MAX(timestamp)
            FROM raw_market_data
            WHERE source = 'futu_opend'
            AND timestamp > CURRENT_DATE
        ''')
        count, latest = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if count == 0:
            return False
        
        # Check if data is recent (within 10 minutes)
        if latest:
            now = datetime.now(timezone.utc)
            if latest.tzinfo is None:
                latest = latest.replace(tzinfo=timezone.utc)
            diff_minutes = (now - latest).total_seconds() / 60
            return diff_minutes < 10
        
        return False
    
    def test_node_red_flows(self):
        """測試 Node-RED Flows"""
        try:
            response = requests.get(f"{NODE_RED_URL}/flows", timeout=5)
            if response.status_code != 200:
                return False
            
            flows = response.json()
            flow_count = len([f for f in flows if f.get('type') == 'tab'])
            return flow_count >= 4  # Should have at least 4 flows
        except:
            return False
    
    def test_futu_opend_connection(self):
        """測試 Futu OpenD 連接"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((FUTU_HOST, FUTU_PORT))
            sock.close()
            return result == 0
        except:
            return False
    
    def test_data_quality(self):
        """測試數據質量"""
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check QQQ data quality
        cursor.execute('''
            SELECT 
                COUNT(*) as count,
                AVG(price) as avg_price,
                MIN(price) as min_price,
                MAX(price) as max_price
            FROM raw_market_data
            WHERE symbol IN ('US.QQQ', 'QQQ')
            AND timestamp > CURRENT_DATE
        ''')
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        count, avg_price, min_price, max_price = result
        
        # Should have data and reasonable price range for QQQ
        if count == 0:
            return False
        
        # QQQ should be between 500-800
        if avg_price and (avg_price < 500 or avg_price > 800):
            return False
        
        return True
    
    def test_risk_management_data(self):
        """測試風險管理數據"""
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check if we can calculate daily stats
        cursor.execute('''
            SELECT 
                symbol,
                COUNT(*) as count,
                MAX(price) as high,
                MIN(price) as low,
                AVG(price) as avg
            FROM raw_market_data
            WHERE timestamp > CURRENT_DATE
            GROUP BY symbol
            ORDER BY COUNT(*) DESC
            LIMIT 5
        ''')
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Should have at least some data for risk calculations
        return len(results) > 0
    
    def test_backup_data_sources(self):
        """測試備份數據源"""
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT source
            FROM raw_market_data
            WHERE timestamp > CURRENT_DATE - INTERVAL '1 day'
        ''')
        
        sources = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        # Should have multiple data sources
        return len(sources) >= 2
    
    def generate_report(self):
        """生成測試報告"""
        print("\n" + "=" * 60)
        print("端到端測試報告")
        print("=" * 60)
        print(f"測試時間: {datetime.now()}")
        print(f"總測試數: {len(self.results)}")
        print(f"通過: {self.passed} ✅")
        print(f"失敗: {self.failed} ❌")
        print(f"通過率: {self.passed/len(self.results)*100:.1f}%" if self.results else "N/A")
        
        if self.failed > 0:
            print("\n失敗項目:")
            for name, passed, error in self.results:
                if not passed:
                    print(f"  ❌ {name}: {error}")
        
        print("=" * 60)
        
        # Save report
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'total': len(self.results),
            'passed': self.passed,
            'failed': self.failed,
            'results': [
                {'name': name, 'passed': passed, 'error': error}
                for name, passed, error in self.results
            ]
        }
        
        with open(f"logs/e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return self.failed == 0

def main():
    """運行端到端測試"""
    print("=" * 60)
    print("六循環系統 - 端到端測試")
    print("=" * 60)
    
    tester = E2ETester()
    
    # Run tests
    tester.test("數據庫連接", tester.test_database_connection)
    tester.test("Futu OpenD 連接", tester.test_futu_opend_connection)
    tester.test("Futu 數據流", tester.test_futu_data_flow)
    tester.test("Node-RED Flows", tester.test_node_red_flows)
    tester.test("數據質量", tester.test_data_quality)
    tester.test("風險管理數據", tester.test_risk_management_data)
    tester.test("備份數據源", tester.test_backup_data_sources)
    
    # Generate report
    all_passed = tester.generate_report()
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
