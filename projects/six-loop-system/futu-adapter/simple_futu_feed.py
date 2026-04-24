"""
Simple Futu Data Feed - 使用 Futu API 直接獲取數據
"""

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

def save_market_data(symbol, price, open_price=None, high_price=None, low_price=None, 
                     volume=None, source='manual'):
    """Save market data to database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO raw_market_data 
            (symbol, price, open_price, high_price, low_price, volume, timestamp, source, data_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (symbol, price, open_price, high_price, low_price, volume, 
              datetime.now(), source, 'tick'))
        
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[{datetime.now()}] Saved: {symbol} @ {price}")
        return True
        
    except Exception as e:
        print(f"[{datetime.now()}] Database error: {e}")
        return False

def simulate_feed():
    """Simulate data feed for testing"""
    print(f"[{datetime.now()}] Starting simulated data feed...")
    
    # Base price for MNQ
    base_price = 19800.0
    
    try:
        while True:
            # Simulate small price movements
            import random
            change = random.uniform(-5, 5)
            price = base_price + change
            
            save_market_data(
                symbol='MNQ',
                price=round(price, 2),
                open_price=round(base_price, 2),
                high_price=round(price + 10, 2),
                low_price=round(price - 10, 2),
                volume=random.randint(1000, 5000),
                source='simulated'
            )
            
            time.sleep(5)  # Every 5 seconds
            
    except KeyboardInterrupt:
        print(f"[{datetime.now()}] Stopping feed...")

def check_database():
    """Check current database status"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), MAX(timestamp) FROM raw_market_data;")
        result = cursor.fetchone()
        print(f"Database: {result[0]} records, latest: {result[1]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Database check error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'simulate':
        simulate_feed()
    else:
        check_database()
        print("Usage: python simple_futu_feed.py simulate")
