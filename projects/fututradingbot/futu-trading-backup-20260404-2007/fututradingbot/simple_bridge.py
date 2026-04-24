# 簡化版 Realtime Bridge - 專注穩定性
# 只獲取基本數據，確保 Dashboard 能正常顯示

import asyncio
import json
import os
import websockets
from datetime import datetime
from pathlib import Path
import sys
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.api.futu_client import FutuAPIClient, FutuTradeClient, Market, TrdEnv, SubType
    FUTU_AVAILABLE = True
except ImportError:
    logger.warning("Futu API not available")
    FUTU_AVAILABLE = False


@dataclass
class PriceData:
    """價格數據"""
    symbol: str
    price: float = 0.0
    change: float = 0.0
    change_pct: float = 0.0
    volume: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AccountInfo:
    """賬戶信息"""
    total_assets: float = 100000.0
    available_cash: float = 100000.0
    daily_pnl: float = 0.0


class SimpleRealtimeBridge:
    """簡化版實時數據橋接器"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        self.host = host
        self.port = port
        self.symbol = "TQQQ"
        self.futu_code = "US.TQQQ"
        
        # Data storage
        self.price_data = PriceData(symbol=self.symbol)
        self.account = AccountInfo()
        self.positions: Dict = {}
        self.trades: List = []
        
        # WebSocket clients
        self.clients: set = set()
        self.running = False
        
        # Futu clients
        self.futu_client = None
        self.futu_trade_client = None
        
        logger.info(f"SimpleRealtimeBridge initialized for {self.symbol}")
    
    async def start(self):
        """啟動橋接器"""
        logger.info("=" * 60)
        logger.info("Simple Realtime Bridge Starting...")
        logger.info("=" * 60)
        
        self.running = True
        
        # Connect to Futu API
        if FUTU_AVAILABLE:
            await self.connect_futu()
        
        # Start WebSocket server
        server = await websockets.serve(
            self.handle_client,
            "127.0.0.1", 8765
        )
        
        # Start data collection
        data_task = asyncio.create_task(self.data_collection_loop())
        
        logger.info("Bridge is running!")
        await asyncio.gather(server.wait_closed(), data_task)
    
    async def connect_futu(self):
        """連接富途API"""
        try:
            # Connect quote client
            self.futu_client = FutuAPIClient(host=self.host, port=self.port)
            if self.futu_client.connect_quote():
                logger.info(f"Connected to Futu OpenD at {self.host}:{self.port}")
                
                # Subscribe to TQQQ
                quote_client = self.futu_client.get_quote_client()
                if quote_client:
                    ret, data = quote_client.subscribe([self.futu_code], [SubType.QUOTE])
                    if ret == 0:
                        logger.info(f"Subscribed to {self.futu_code}")
                    else:
                        logger.warning(f"Subscribe failed: {data}")
            
            # Connect trade client
            self.futu_trade_client = FutuTradeClient(
                host=self.host, port=self.port, market=Market.US
            )
            if self.futu_trade_client.connect():
                logger.info("Trade client connected")
                
                # Unlock trade
                password = os.getenv("TRADE_PASSWORD", "011087")
                if self.futu_trade_client.unlock_trade(password):
                    logger.info("Trade interface unlocked")
                
                # Get initial account data
                await self.update_account_data()
                
        except Exception as e:
            logger.error(f"Futu connection error: {e}")
    
    async def update_account_data(self):
        """更新帳戶數據"""
        if not self.futu_trade_client:
            return
        
        try:
            # Query account
            ret_code, account_data = self.futu_trade_client.accinfo_query(TrdEnv.REAL)
            
            if ret_code == 0 and account_data is not None:
                # Parse DataFrame
                if hasattr(account_data, 'to_dict'):
                    data_list = account_data.to_dict('records')
                    if len(data_list) > 0:
                        data = data_list[0]
                        
                        # Update account
                        if 'total_assets' in data:
                            self.account.total_assets = float(data['total_assets'])
                        if 'available_cash' in data or 'cash' in data:
                            self.account.available_cash = float(data.get('available_cash', data.get('cash', 0)))
                        
                        logger.info(f"Account: Total=${self.account.total_assets:.2f}, Cash=${self.account.available_cash:.2f}")
            
            # Query positions
            ret_code, positions = self.futu_trade_client.position_list_query(TrdEnv.REAL)
            
            if ret_code == 0 and positions is not None:
                if hasattr(positions, 'to_dict'):
                    pos_list = positions.to_dict('records')
                    self.positions = {}
                    
                    for pos in pos_list:
                        symbol = pos.get('code', '').replace('US.', '')
                        if symbol:
                            self.positions[symbol] = {
                                'symbol': symbol,
                                'quantity': int(pos.get('qty', 0)),
                                'avg_cost': float(pos.get('cost_price', 0)),
                                'current_price': float(pos.get('nominal_price', 0)),
                                'unrealized_pnl': float(pos.get('pl_val', 0))
                            }
                    
                    logger.info(f"Positions: {len(self.positions)} positions")
            
        except Exception as e:
            logger.warning(f"Failed to update account: {e}")
    
    async def fetch_price_data(self):
        """獲取價格數據"""
        if not self.futu_client:
            return
        
        try:
            quote_client = self.futu_client.get_quote_client()
            if not quote_client:
                return
            
            # Get stock quote
            ret, data = quote_client.get_stock_quote([self.futu_code])
            
            if ret == 0 and data is not None and not data.empty:
                for _, row in data.iterrows():
                    code = row.get("code", "")
                    symbol = code.replace("US.", "") if code.startswith("US.") else code
                    
                    if symbol == self.symbol:
                        price = float(row.get("last_price", 0))
                        volume = int(row.get("volume", 0))
                        
                        # Calculate change
                        prev_close = float(row.get("prev_close_price", price))
                        change = price - prev_close
                        change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                        
                        # Update price data
                        self.price_data.price = price
                        self.price_data.volume = volume
                        self.price_data.change = change
                        self.price_data.change_pct = change_pct
                        self.price_data.timestamp = datetime.now().isoformat()
                        
                        logger.debug(f"Price update: {symbol} ${price:.2f} ({change_pct:+.2f}%)")
                        
        except Exception as e:
            logger.warning(f"Failed to fetch price: {e}")
    
    async def data_collection_loop(self):
        """數據收集循環"""
        logger.info("Starting data collection...")
        counter = 0
        
        while self.running:
            try:
                # Fetch price data
                await self.fetch_price_data()
                
                # Update account data every 30 seconds
                counter += 1
                if counter >= 15:
                    await self.update_account_data()
                    counter = 0
                
                # Broadcast to clients
                await self.broadcast_data()
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Data collection error: {e}")
                await asyncio.sleep(5)
    
    async def broadcast_data(self):
        """廣播數據到所有客戶端"""
        if not self.clients:
            return
        
        data = {
            "type": "data_update",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "TQQQ": {
                    "price": self.price_data.price,
                    "change": round(self.price_data.change, 2),
                    "change_pct": round(self.price_data.change_pct, 2),
                    "volume": self.price_data.volume
                },
                "account": {
                    "total_assets": round(self.account.total_assets, 2),
                    "available_cash": round(self.account.available_cash, 2),
                    "daily_pnl": round(self.account.daily_pnl, 2)
                },
                "positions": list(self.positions.values()),
                "trades": self.trades[-10:]
            }
        }
        
        message = json.dumps(data)
        disconnected = []
        
        for client in self.clients:
            try:
                await client.send(message)
            except Exception:
                disconnected.append(client)
        
        for client in disconnected:
            self.clients.discard(client)
    
    async def handle_client(self, websocket):
        """處理客戶端連接"""
        self.clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected. Total: {len(self.clients)}")
        
        try:
            # Send initial data
            await self.broadcast_data()
            
            # Keep connection alive
            async for message in websocket:
                try:
                    msg = json.loads(message)
                    if msg.get("action") == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    pass
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client {client_id} disconnected. Total: {len(self.clients)}")


async def main():
    bridge = SimpleRealtimeBridge()
    await bridge.start()


if __name__ == "__main__":
    asyncio.run(main())
