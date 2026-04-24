"""
Futu OpenD Data Feed
直接連接 Futu OpenD WebSocket，獲取 NQ 100 (MNQ) 實時數據
"""

import websocket
import json
import psycopg2
from datetime import datetime
import time
import threading

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'trading_db',
    'user': 'postgres',
    'password': 'PostgresqL'
}

# Futu OpenD configuration
FUTU_WS_URL = "ws://127.0.0.1:11111"

class FutuDataFeed:
    def __init__(self):
        self.ws = None
        self.connected = False
        self.reconnect_interval = 5
        self.heartbeat_interval = 30
        
    def connect(self):
        """Connect to Futu OpenD WebSocket"""
        try:
            self.ws = websocket.WebSocketApp(
                FUTU_WS_URL,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            # Start connection in a separate thread
            wst = threading.Thread(target=self.ws.run_forever)
            wst.daemon = True
            wst.start()
            
            print(f"[{datetime.now()}] Connecting to Futu OpenD at {FUTU_WS_URL}...")
            
        except Exception as e:
            print(f"[{datetime.now()}] Connection error: {e}")
            self.schedule_reconnect()
    
    def on_open(self, ws):
        """Handle connection open"""
        self.connected = True
        print(f"[{datetime.now()}] Connected to Futu OpenD")
        
        # Subscribe to MNQ (NQ 100 Mini Futures)
        subscribe_msg = {
            "cmd": "subscribe",
            "symbols": ["MNQ"],
            "data_types": ["quote", "tick"]
        }
        ws.send(json.dumps(subscribe_msg))
        print(f"[{datetime.now()}] Subscribed to MNQ")
        
        # Start heartbeat
        self.start_heartbeat()
    
    def on_message(self, ws, message):
        """Handle incoming message"""
        try:
            data = json.loads(message)
            self.process_data(data)
        except json.JSONDecodeError as e:
            print(f"[{datetime.now()}] JSON decode error: {e}")
        except Exception as e:
            print(f"[{datetime.now()}] Message processing error: {e}")
    
    def on_error(self, ws, error):
        """Handle error"""
        print(f"[{datetime.now()}] WebSocket error: {error}")
        self.connected = False
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle connection close"""
        self.connected = False
        print(f"[{datetime.now()}] Connection closed: {close_status_code} - {close_msg}")
        self.schedule_reconnect()
    
    def process_data(self, data):
        """Process and store market data"""
        try:
            # Check if this is a quote message
            if data.get('type') == 'quote' or data.get('cmd') == 'quote':
                symbol = data.get('symbol', '')
                
                # Only process MNQ
                if 'MNQ' in symbol:
                    parsed = {
                        'symbol': 'MNQ',
                        'price': data.get('last') or data.get('price') or data.get('cur_price'),
                        'open_price': data.get('open'),
                        'high_price': data.get('high'),
                        'low_price': data.get('low'),
                        'volume': data.get('volume') or data.get('vol'),
                        'turnover': data.get('turnover'),
                        'open_interest': data.get('open_interest') or data.get('oi'),
                        'bid_price': data.get('bid1') or data.get('bid_price'),
                        'ask_price': data.get('ask1') or data.get('ask_price'),
                        'bid_volume': data.get('bid_vol1') or data.get('bid_volume'),
                        'ask_volume': data.get('ask_vol1') or data.get('ask_volume'),
                        'timestamp': datetime.now(),
                        'source': 'futu_opend',
                        'data_type': 'tick',
                        'metadata': json.dumps({
                            'raw_data': data
                        })
                    }
                    
                    self.save_to_database(parsed)
                    print(f"[{datetime.now()}] MNQ Price: {parsed['price']}")
                    
        except Exception as e:
            print(f"[{datetime.now()}] Data processing error: {e}")
    
    def save_to_database(self, data):
        """Save data to PostgreSQL"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO raw_market_data 
                (symbol, price, open_price, high_price, low_price, volume, turnover, 
                 open_interest, bid_price, ask_price, bid_volume, ask_volume, 
                 timestamp, source, data_type, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['symbol'], data['price'], data['open_price'], data['high_price'],
                data['low_price'], data['volume'], data['turnover'], data['open_interest'],
                data['bid_price'], data['ask_price'], data['bid_volume'], data['ask_volume'],
                data['timestamp'], data['source'], data['data_type'], data['metadata']
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"[{datetime.now()}] Database error: {e}")
    
    def start_heartbeat(self):
        """Send periodic heartbeat"""
        def heartbeat():
            while self.connected:
                time.sleep(self.heartbeat_interval)
                if self.connected and self.ws:
                    try:
                        self.ws.send(json.dumps({"cmd": "heartbeat"}))
                    except Exception as e:
                        print(f"[{datetime.now()}] Heartbeat error: {e}")
        
        hb_thread = threading.Thread(target=heartbeat)
        hb_thread.daemon = True
        hb_thread.start()
    
    def schedule_reconnect(self):
        """Schedule reconnection"""
        print(f"[{datetime.now()}] Reconnecting in {self.reconnect_interval} seconds...")
        time.sleep(self.reconnect_interval)
        self.connect()
    
    def run(self):
        """Main loop"""
        print(f"[{datetime.now()}] Starting Futu Data Feed...")
        self.connect()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"[{datetime.now()}] Shutting down...")
            if self.ws:
                self.ws.close()

if __name__ == "__main__":
    feed = FutuDataFeed()
    feed.run()
