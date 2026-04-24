"""
六循環系統監控腳本
用於 Cron Job 自動監控系統健康狀態
"""

import sys
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/private skills/node-red-automation')

import psycopg2
from datetime import datetime, timedelta, timezone
import requests
import json

# Configuration
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

class SixLoopMonitor:
    """六循環系統監控器"""
    
    def __init__(self):
        self.checks = []
        self.errors = []
        
    def check_database(self):
        """檢查數據庫連接"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Check latest data
            cursor.execute("""
                SELECT symbol, price, timestamp, source 
                FROM raw_market_data 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if result:
                symbol, price, timestamp, source = result
                # Handle timezone-aware datetime
                now = datetime.now(timezone.utc)
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                time_diff = now - timestamp
                
                if time_diff < timedelta(minutes=5):
                    self.checks.append(f"✅ 數據庫: 最新數據 {time_diff.seconds}秒前 ({symbol} @ {price})")
                else:
                    self.errors.append(f"⚠️ 數據庫: 數據滯後 {time_diff.seconds}秒")
            else:
                self.errors.append("❌ 數據庫: 無數據")
            
            # Check counts by source
            cursor.execute("""
                SELECT source, COUNT(*) 
                FROM raw_market_data 
                WHERE timestamp > NOW() - INTERVAL '1 hour'
                GROUP BY source
            """)
            counts = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            self.errors.append(f"❌ 數據庫錯誤: {e}")
            return False
    
    def check_node_red(self):
        """檢查 Node-RED 狀態"""
        try:
            response = requests.get(f"{NODE_RED_URL}/flows", timeout=5)
            if response.status_code == 200:
                flows = response.json()
                flow_count = len([f for f in flows if f.get('type') == 'tab'])
                self.checks.append(f"✅ Node-RED: {flow_count} 個 Flows 運行中")
                return True
            else:
                self.errors.append(f"⚠️ Node-RED: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.errors.append(f"❌ Node-RED: 無法連接 ({e})")
            return False
    
    def check_futu(self):
        """檢查 Futu OpenD 狀態"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((FUTU_HOST, FUTU_PORT))
            sock.close()
            
            if result == 0:
                self.checks.append(f"✅ Futu OpenD: 端口 {FUTU_PORT} 開啟")
                return True
            else:
                self.errors.append(f"❌ Futu OpenD: 端口 {FUTU_PORT} 關閉")
                return False
        except Exception as e:
            self.errors.append(f"❌ Futu OpenD: 檢查失敗 ({e})")
            return False
    
    def generate_report(self):
        """生成監控報告"""
        report = []
        report.append("=" * 60)
        report.append("六循環系統監控報告")
        report.append(f"時間: {datetime.now()}")
        report.append("=" * 60)
        
        if self.checks:
            report.append("\n✅ 正常項目:")
            for check in self.checks:
                report.append(f"  {check}")
        
        if self.errors:
            report.append("\n⚠️ 異常項目:")
            for error in self.errors:
                report.append(f"  {error}")
        
        if not self.errors:
            report.append("\n🎉 所有系統正常運作!")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def run(self):
        """運行所有檢查"""
        self.check_database()
        self.check_node_red()
        self.check_futu()
        
        report = self.generate_report()
        print(report)
        
        # Save to file
        with open(f"logs/monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", 'w') as f:
            f.write(report)
        
        return len(self.errors) == 0

def main():
    """主函數"""
    import os
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    monitor = SixLoopMonitor()
    success = monitor.run()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
