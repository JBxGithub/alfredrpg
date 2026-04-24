"""
告警管理器 - WhatsApp 異常通知
"""

import json
import os
from datetime import datetime

# WhatsApp 配置
WHATSAPP_TARGET = "+85263931048"

class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alert_log = 'logs/alerts.json'
        os.makedirs('logs', exist_ok=True)
        self.alert_history = self._load_alert_history()
    
    def _load_alert_history(self):
        """加載告警歷史"""
        if os.path.exists(self.alert_log):
            try:
                with open(self.alert_log, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'alerts': [], 'last_alert': None}
        return {'alerts': [], 'last_alert': None}
    
    def _save_alert_history(self):
        """保存告警歷史"""
        with open(self.alert_log, 'w', encoding='utf-8') as f:
            json.dump(self.alert_history, f, indent=2, ensure_ascii=False)
    
    def send_alert(self, level, title, message, details=None):
        """
        發送告警
        
        Args:
            level: 級別 (info, warning, error, critical)
            title: 標題
            message: 消息內容
            details: 詳細信息
        """
        alert = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'title': title,
            'message': message,
            'details': details or {}
        }
        
        # 記錄到歷史
        self.alert_history['alerts'].append(alert)
        self.alert_history['last_alert'] = alert['timestamp']
        self._save_alert_history()
        
        # 打印告警 (實際使用時會發送 WhatsApp)
        emoji_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'critical': '🚨'
        }
        
        emoji = emoji_map.get(level, '🔔')
        print(f"\n{emoji} [{level.upper()}] {title}")
        print(f"   {message}")
        if details:
            print(f"   詳情: {details}")
        print(f"   時間: {alert['timestamp']}")
        print(f"   目標: WhatsApp {WHATSAPP_TARGET}")
        
        return alert
    
    def check_system_health(self):
        """檢查系統健康狀態並發送告警"""
        import psycopg2
        import socket
        import requests
        
        alerts = []
        
        # Check Futu OpenD
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('127.0.0.1', 11111))
            sock.close()
            
            if result != 0:
                alerts.append(self.send_alert(
                    'error',
                    'Futu OpenD 連接失敗',
                    '無法連接到 Futu OpenD (端口 11111)',
                    {'port': 11111, 'error_code': result}
                ))
        except Exception as e:
            alerts.append(self.send_alert(
                'error',
                'Futu OpenD 檢查異常',
                str(e)
            ))
        
        # Check PostgreSQL
        try:
            conn = psycopg2.connect(
                host='localhost', port=5432, database='trading_db',
                user='postgres', password='PostgresqL'
            )
            cursor = conn.cursor()
            
            # Check latest data
            cursor.execute('''
                SELECT MAX(timestamp) 
                FROM raw_market_data 
                WHERE source = 'futu_opend'
            ''')
            result = cursor.fetchone()
            
            if result and result[0]:
                from datetime import datetime, timezone
                latest = result[0]
                now = datetime.now(timezone.utc)
                if latest.tzinfo is None:
                    latest = latest.replace(tzinfo=timezone.utc)
                
                diff_minutes = (now - latest).total_seconds() / 60
                
                if diff_minutes > 10:
                    alerts.append(self.send_alert(
                        'warning',
                        'Futu 數據滯後',
                        f'最新數據 {diff_minutes:.1f} 分鐘前',
                        {'last_update': str(latest), 'lag_minutes': diff_minutes}
                    ))
            else:
                alerts.append(self.send_alert(
                    'error',
                    '無 Futu 數據',
                    '數據庫中沒有 Futu 數據'
                ))
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            alerts.append(self.send_alert(
                'critical',
                'PostgreSQL 連接失敗',
                str(e)
            ))
        
        # Check Node-RED
        try:
            response = requests.get('http://localhost:1880/flows', timeout=5)
            if response.status_code != 200:
                alerts.append(self.send_alert(
                    'error',
                    'Node-RED 異常',
                    f'HTTP {response.status_code}'
                ))
        except Exception as e:
            alerts.append(self.send_alert(
                'error',
                'Node-RED 連接失敗',
                str(e)
            ))
        
        if not alerts:
            print("✅ 系統健康檢查通過，無異常")
        
        return alerts

def main():
    """測試告警管理器"""
    manager = AlertManager()
    
    print("=" * 60)
    print("告警管理器測試")
    print("=" * 60)
    
    # Test alerts
    manager.send_alert('info', '測試通知', '這是一個測試通知')
    manager.send_alert('warning', '測試警告', '這是一個測試警告')
    
    print("\n" + "=" * 60)
    print("系統健康檢查")
    print("=" * 60)
    
    # Check system health
    alerts = manager.check_system_health()
    
    print(f"\n檢查完成，發現 {len(alerts)} 個告警")

if __name__ == '__main__':
    main()
