"""
備份數據饋送器
當 Futu OpenD 數據流失敗時，從 investing.com 獲取 NQ 100 數據
使用 alfred-browser 技能
"""

import sys
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/private skills/alfred-browser')

import psycopg2
from datetime import datetime
import time
import json
import requests

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'trading_db',
    'user': 'postgres',
    'password': 'PostgresqL'
}

def save_market_data(symbol, price, open_price=None, high_price=None, low_price=None,
                     change_value=None, change_percent=None, volume=None, source='backup'):
    """保存市場數據到數據庫"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO raw_market_data
            (symbol, price, open_price, high_price, low_price, change_value, change_percent, volume, timestamp, source, data_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (symbol, price, open_price, high_price, low_price, change_value, change_percent, volume,
              datetime.now(), source, 'tick'))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[{datetime.now()}] Saved: {symbol} @ {price} (source: {source})")
        return True
        
    except Exception as e:
        print(f"[{datetime.now()}] Database error: {e}")
        return False

def fetch_from_investing():
    """從 investing.com API 獲取 NQ 100 數據 (.NDX)"""
    try:
        # investing.com API endpoint for NQ 100 (Nasdaq 100 Index)
        # ID 20 是 NQ 100 指數
        url = "https://api.investing.com/api/marketdata/v1/data/index/20"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.investing.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data:
                market_data = data['data']
                
                parsed = {
                    'symbol': 'NQ100',
                    'price': float(market_data.get('last', 0)),
                    'open_price': float(market_data.get('open', 0)),
                    'high_price': float(market_data.get('high', 0)),
                    'low_price': float(market_data.get('low', 0)),
                    'change_value': float(market_data.get('change', 0)),
                    'change_percent': float(market_data.get('change_percent', 0)),
                    'volume': int(market_data.get('volume', 0)) if market_data.get('volume') else None,
                    'source': 'investing_com'
                }
                
                return parsed
        else:
            print(f"[{datetime.now()}] investing.com API error: {response.status_code}")
            
    except Exception as e:
        print(f"[{datetime.now()}] Fetch error: {e}")
    
    return None

def fetch_from_yahoo():
    """從 Yahoo Finance 獲取 NQ 100 數據 (備用)"""
    try:
        # Yahoo Finance API for NQ=F (Nasdaq 100 Futures)
        url = "https://query1.finance.yahoo.com/v8/finance/chart/NQ=F?interval=1m&range=1d"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']
                
                # Get latest price
                timestamps = result.get('timestamp', [])
                closes = result['indicators']['quote'][0].get('close', [])
                opens = result['indicators']['quote'][0].get('open', [])
                highs = result['indicators']['quote'][0].get('high', [])
                lows = result['indicators']['quote'][0].get('low', [])
                volumes = result['indicators']['quote'][0].get('volume', [])
                
                if closes and len(closes) > 0:
                    latest_idx = -1
                    parsed = {
                        'symbol': 'NQ100',
                        'price': closes[latest_idx] if closes[latest_idx] else meta.get('regularMarketPrice'),
                        'open_price': opens[latest_idx] if opens and opens[latest_idx] else meta.get('regularMarketOpen'),
                        'high_price': highs[latest_idx] if highs and highs[latest_idx] else meta.get('regularMarketDayHigh'),
                        'low_price': lows[latest_idx] if lows and lows[latest_idx] else meta.get('regularMarketDayLow'),
                        'change_value': None,
                        'change_percent': None,
                        'volume': volumes[latest_idx] if volumes and volumes[latest_idx] else None,
                        'source': 'yahoo_finance'
                    }
                    
                    return parsed
        else:
            print(f"[{datetime.now()}] Yahoo Finance API error: {response.status_code}")
            
    except Exception as e:
        print(f"[{datetime.now()}] Yahoo fetch error: {e}")
    
    return None

def run_backup_feed():
    """運行備份數據饋送"""
    print(f"[{datetime.now()}] 啟動備份數據饋送器...")
    print(f"[{datetime.now()}] 數據源順序: investing.com -> Yahoo Finance")
    
    try:
        while True:
            # 嘗試從 investing.com 獲取
            data = fetch_from_investing()
            
            # 如果失敗，嘗試 Yahoo Finance
            if not data:
                print(f"[{datetime.now()}] investing.com 失敗，嘗試 Yahoo Finance...")
                data = fetch_from_yahoo()
            
            if data:
                save_market_data(
                    symbol=data['symbol'],
                    price=data['price'],
                    open_price=data['open_price'],
                    high_price=data['high_price'],
                    low_price=data['low_price'],
                    change_value=data['change_value'],
                    change_percent=data['change_percent'],
                    volume=data['volume'],
                    source=data['source']
                )
            else:
                print(f"[{datetime.now()}] 無法從任何數據源獲取數據")
            
            # 每 30 秒獲取一次
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"[{datetime.now()}] 停止備份饋送器...")

def check_futu_data_status():
    """檢查 Futu 數據流狀態"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 檢查最近 5 分鐘的 Futu 數據
        cursor.execute("""
            SELECT COUNT(*), MAX(timestamp) 
            FROM raw_market_data 
            WHERE source = 'futu_opend' 
            AND timestamp > NOW() - INTERVAL '5 minutes'
        """)
        
        result = cursor.fetchone()
        count = result[0]
        latest = result[1]
        
        cursor.close()
        conn.close()
        
        if count == 0:
            print(f"[{datetime.now()}] ⚠️ Futu 數據流異常: 最近 5 分鐘無數據")
            return False
        else:
            print(f"[{datetime.now()}] ✅ Futu 數據流正常: {count} 條記錄，最新: {latest}")
            return True
            
    except Exception as e:
        print(f"[{datetime.now()}] 檢查錯誤: {e}")
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'check':
            check_futu_data_status()
        elif sys.argv[1] == 'run':
            run_backup_feed()
        else:
            print("Usage: python backup_data_feed.py [check|run]")
    else:
        # 默認檢查 Futu 狀態
        check_futu_data_status()
