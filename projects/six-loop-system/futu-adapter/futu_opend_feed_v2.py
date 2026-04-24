"""
Futu OpenD 數據饋送器 v2
修復數據寫入問題，確保 QQQ 數據正確寫入數據庫
"""

import futu as ft
import psycopg2
from datetime import datetime, timezone
import time
import sys

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'trading_db',
    'user': 'postgres',
    'password': 'PostgresqL'
}

class FutuOpenDFeedV2:
    """Futu OpenD 數據饋送器 v2 - 修復版"""
    
    def __init__(self, host='127.0.0.1', port=11111):
        self.host = host
        self.port = port
        self.quote_ctx = None
        self.connected = False
        self.data_count = 0
        
    def connect(self):
        """連接到 OpenD"""
        try:
            print(f"[{datetime.now()}] 連接到 Futu OpenD ({self.host}:{self.port})...")
            
            # 創建行情上下文
            self.quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)
            
            # 啟動異步接收
            self.quote_ctx.start()
            
            self.connected = True
            print(f"[{datetime.now()}] ✅ 已連接到 OpenD")
            return True
            
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 連接失敗: {e}")
            self.connected = False
            return False
    
    def get_qqq_data(self):
        """獲取 QQQ 數據"""
        if not self.connected:
            print(f"[{datetime.now()}] ❌ 未連接")
            return None
        
        try:
            # 直接獲取 QQQ 快照
            ret, data = self.quote_ctx.get_market_snapshot(['US.QQQ'])
            
            if ret == ft.RET_OK and not data.empty:
                row = data.iloc[0]
                
                # 提取數據
                result = {
                    'symbol': 'QQQ',  # 統一使用 QQQ
                    'price': float(row.get('last_price', 0)),
                    'open_price': float(row.get('open_price', 0)) if row.get('open_price') else None,
                    'high_price': float(row.get('high_price', 0)) if row.get('high_price') else None,
                    'low_price': float(row.get('low_price', 0)) if row.get('low_price') else None,
                    'volume': int(row.get('volume', 0)) if row.get('volume') else None,
                    'change_value': float(row.get('change_val', 0)) if row.get('change_val') else None,
                    'change_percent': float(row.get('change_rate', 0)) if row.get('change_rate') else None,
                    'timestamp': datetime.now(timezone.utc),
                    'source': 'futu_opend',
                    'data_type': 'tick'
                }
                
                print(f"[{datetime.now()}] ✅ 獲取 QQQ: {result['price']}")
                return result
            else:
                print(f"[{datetime.now()}] ⚠️ 無法獲取 QQQ: ret={ret}")
                return None
                
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 獲取失敗: {e}")
            return None
    
    def save_to_database(self, data):
        """保存數據到數據庫 - 修復版"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # 使用正確的列名
            cursor.execute("""
                INSERT INTO raw_market_data 
                (symbol, price, open_price, high_price, low_price, volume, 
                 change_value, change_percent, timestamp, source, data_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['symbol'],
                data['price'],
                data['open_price'],
                data['high_price'],
                data['low_price'],
                data['volume'],
                data['change_value'],
                data['change_percent'],
                data['timestamp'],
                data['source'],
                data['data_type']
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            self.data_count += 1
            print(f"[{datetime.now()}] 💾 已保存 #{self.data_count}: {data['symbol']} @ {data['price']}")
            return True
            
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 數據庫錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self, interval=5):
        """運行數據饋送"""
        print(f"[{datetime.now()}] 啟動 Futu OpenD 數據饋送器 v2")
        print(f"[{datetime.now()}] 數據源: QQQ (代理 NQ 100)")
        print(f"[{datetime.now()}] 輪詢間隔: {interval}秒")
        print("=" * 60)
        
        if not self.connect():
            print("連接失敗，退出")
            return False
        
        try:
            while True:
                # 獲取數據
                data = self.get_qqq_data()
                
                if data:
                    # 保存到數據庫
                    saved = self.save_to_database(data)
                    if not saved:
                        print(f"[{datetime.now()}] ⚠️ 保存失敗，繼續嘗試...")
                else:
                    print(f"[{datetime.now()}] ⚠️ 無法獲取數據")
                
                # 等待下一次輪詢
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] 停止饋送器")
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 運行錯誤: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()
        
        return True
    
    def close(self):
        """關閉連接"""
        if self.quote_ctx:
            self.quote_ctx.close()
            self.connected = False
            print(f"[{datetime.now()}] 已關閉連接")
            print(f"[{datetime.now()}] 總共保存: {self.data_count} 條記錄")

def test_once():
    """測試一次數據獲取和保存"""
    print("=" * 60)
    print("Futu OpenD 數據流測試")
    print("=" * 60)
    
    feed = FutuOpenDFeedV2()
    
    if feed.connect():
        # 獲取數據
        data = feed.get_qqq_data()
        
        if data:
            print(f"\n獲取到的數據:")
            for key, value in data.items():
                print(f"  {key}: {value}")
            
            # 保存數據
            print(f"\n保存數據...")
            saved = feed.save_to_database(data)
            
            if saved:
                print(f"✅ 測試成功！數據已保存到數據庫")
            else:
                print(f"❌ 測試失敗！無法保存數據")
        else:
            print(f"❌ 無法獲取數據")
        
        feed.close()
    else:
        print(f"❌ 連接失敗")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_once()
    else:
        feed = FutuOpenDFeedV2()
        feed.run(interval=5)
