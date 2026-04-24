"""
Futu OpenD 數據饋送器
使用 futu-api SDK 正確連接 OpenD 獲取 NQ 100 數據
"""

import futu as ft
import psycopg2
from datetime import datetime
import time
import json

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'trading_db',
    'user': 'postgres',
    'password': 'PostgresqL'
}

class FutuOpenDFeed:
    """Futu OpenD 數據饋送器"""
    
    def __init__(self, host='127.0.0.1', port=11111):
        self.host = host
        self.port = port
        self.quote_ctx = None
        self.connected = False
        
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
    
    def subscribe_nq100(self):
        """訂閱 NQ 100 數據"""
        if not self.connected:
            print(f"[{datetime.now()}] ❌ 未連接，無法訂閱")
            return False
        
        try:
            # NQ 100 Mini Futures 代碼
            # 在 Futu 中，納斯達克100期貨通常是 MNQ 或 NQ
            # 根據市場不同，代碼可能不同
            # Futu 代碼格式: 市場.代碼
            # US. 美股, HK. 港股, SZ. 深圳, SH. 上海
            # NQ 100 指數在 Futu 中不可用，使用 QQQ 作為代理
            # QQQ (Invesco QQQ Trust) 追蹤 NQ 100 指數
            codes = ['US.QQQ']  # NQ 100 代理
            
            for code in codes:
                print(f"[{datetime.now()}] 嘗試訂閱: {code}")
                
                # 訂閱報價和逐筆
                ret, err = self.quote_ctx.subscribe(
                    code, 
                    [ft.SubType.QUOTE, ft.SubType.TICKER, ft.SubType.RT_DATA]
                )
                
                if ret == ft.RET_OK:
                    print(f"[{datetime.now()}] ✅ 成功訂閱: {code}")
                    return True
                else:
                    print(f"[{datetime.now()}] ⚠️ 訂閱 {code} 失敗: {err}")
            
            return False
            
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 訂閱異常: {e}")
            return False
    
    def get_snapshot(self):
        """獲取市場快照"""
        if not self.connected:
            return None
        
        try:
            # 嘗試獲取 NQ 100 快照
            codes = ['US.QQQ', 'US.SQQQ', 'US.TQQQ']
            
            for code in codes:
                ret, data = self.quote_ctx.get_market_snapshot([code])
                
                if ret == ft.RET_OK and not data.empty:
                    print(f"[{datetime.now()}] ✅ 獲取 {code} 快照成功")
                    return data
                
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 獲取快照失敗: {e}")
        
        return None
    
    def save_to_database(self, symbol, price, open_price=None, high_price=None, 
                        low_price=None, volume=None, change=None):
        """保存數據到數據庫"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO raw_market_data 
                (symbol, price, open_price, high_price, low_price, volume, 
                 change_value, timestamp, source, data_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (symbol, price, open_price, high_price, low_price, volume,
                  change, datetime.now(), 'futu_opend', 'tick'))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"[{datetime.now()}] 💾 已保存: {symbol} @ {price}")
            return True
            
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 數據庫錯誤: {e}")
            return False
    
    def run_polling(self, interval=5):
        """輪詢模式獲取數據"""
        print(f"[{datetime.now()}] 啟動輪詢模式 (間隔: {interval}秒)")
        
        try:
            while True:
                # 獲取快照
                snapshot = self.get_snapshot()
                
                if snapshot is not None and not snapshot.empty:
                    # 解析數據
                    row = snapshot.iloc[0]
                    
                    symbol = row.get('code', 'NQ100')
                    price = row.get('last_price') or row.get('price')
                    open_price = row.get('open_price')
                    high_price = row.get('high_price')
                    low_price = row.get('low_price')
                    volume = row.get('volume')
                    change = row.get('change')
                    
                    if price:
                        self.save_to_database(
                            symbol=symbol,
                            price=float(price),
                            open_price=float(open_price) if open_price else None,
                            high_price=float(high_price) if high_price else None,
                            low_price=float(low_price) if low_price else None,
                            volume=int(volume) if volume else None,
                            change=float(change) if change else None
                        )
                else:
                    print(f"[{datetime.now()}] ⚠️ 無法獲取快照")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"[{datetime.now()}] 停止輪詢")
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 輪詢異常: {e}")
    
    def close(self):
        """關閉連接"""
        if self.quote_ctx:
            self.quote_ctx.close()
            self.connected = False
            print(f"[{datetime.now()}] 已關閉連接")

def test_connection():
    """測試連接"""
    print("=" * 60)
    print("Futu OpenD 連接測試")
    print("=" * 60)
    
    feed = FutuOpenDFeed()
    
    # 連接
    if feed.connect():
        # 嘗試訂閱
        feed.subscribe_nq100()
        
        # 獲取一次快照
        snapshot = feed.get_snapshot()
        
        if snapshot is not None:
            print("\n快照數據:")
            print(snapshot.to_string())
        
        # 關閉
        feed.close()
        return True
    else:
        print("\n❌ 連接失敗，請檢查:")
        print("  1. OpenD 是否已啟動")
        print("  2. OpenD 是否已登入")
        print("  3. 端口 11111 是否正確")
        return False

def run_feed():
    """運行數據饋送"""
    print("=" * 60)
    print("Futu OpenD 數據饋送器")
    print("=" * 60)
    
    feed = FutuOpenDFeed()
    
    if feed.connect():
        feed.subscribe_nq100()
        feed.run_polling(interval=5)
    else:
        print("連接失敗，退出")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            test_connection()
        elif sys.argv[1] == 'run':
            run_feed()
        else:
            print("Usage: python futu_opend_feed.py [test|run]")
    else:
        test_connection()
