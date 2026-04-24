"""
Realtime Bridge - 實時數據橋接器 (最終版 2026-03-29)

連接富途API獲取TQQQ實時價格
計算Z-Score、RSI、成交量MA
生成交易信號並通過WebSocket廣播到Dashboard

策略參數（Z-Score Mean Reversion）：
- Z-Score 進場閾值: ±1.65
- RSI 超買/超賣: 70/30
- 成交量過濾: > 20日均量 × 50%
- 止盈/止損: 5%/3%
- 時間止損: 7天
"""

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
import statistics
import pandas as pd
import numpy as np

# Real account configuration for SQQQ position
REAL_ACCOUNT_ID = 281756477706540632  # Account with SQQQ position
REAL_ACCOUNT_CURRENCY = "HKD"

# Setup logging
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from src.utils.logger_config import setup_logger
    logger = setup_logger("RealtimeBridge", "logs/realtime_bridge.log")
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 載入 TQQQ 策略（包含完整 Z-Score 邏輯 + RSI/MACD/止盈止損）
try:
    from src.strategies.tqqq_long_short import TQQQLongShortStrategy, TQQQStrategyConfig
    TQQQ_STRATEGY_AVAILABLE = True
    logger.info("TQQQ Long/Short strategy loaded for live trading")
except ImportError as e:
    logger.warning(f"TQQQ strategy not available: {e}")
    TQQQ_STRATEGY_AVAILABLE = False

try:
    from src.api.futu_client import FutuAPIClient, Market, SubType
    from futu import SubType as FutuSubType
    import futu as ft
    FUTU_AVAILABLE = True
except ImportError:
    logger.warning("Futu API not available, using mock data")
    FUTU_AVAILABLE = False


@dataclass
class PriceData:
    """價格數據"""
    symbol: str
    price: float = 0.0
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    volume: int = 0
    change: float = 0.0
    change_pct: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def update(self, price: float, volume: int = 0):
        """更新價格"""
        if self.price > 0:
            self.change = price - self.price
            self.change_pct = (self.change / self.price) * 100
        self.price = price
        if volume > 0:
            self.volume = volume
        self.timestamp = datetime.now().isoformat()


@dataclass
class TradingSignal:
    """交易信號"""
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0-100
    reason: str
    z_score: float = 0.0
    rsi: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AccountInfo:
    """賬戶信息"""
    total_assets: float = 100000.0
    available_cash: float = 100000.0
    daily_pnl: float = 0.0
    daily_pnl_pct: float = 0.0
    total_unrealized_pnl: float = 0.0


@dataclass
class Position:
    """持倉信息"""
    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    direction: str = "long"  # 'long' or 'short'
    entry_time: str = field(default_factory=lambda: datetime.now().isoformat())


class RealtimeBridge:
    """實時數據橋接器 - 框架A適配版"""
    
    # Z-Score 策略配置（與模擬系統一致，閾值 1.6）
    CONFIG = {
        'entry_zscore': 1.6,  # 回測選定閾值
        'exit_zscore': 0.5,
        'position_pct': 0.50,
        'lookback_period': 60,
    }
    
    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        self.host = host
        self.port = port
        # 只追蹤TQQQ
        self.symbol = "TQQQ"
        self.futu_code = "US.TQQQ"
        
        # Data storage
        self.price_data: PriceData = PriceData(symbol=self.symbol)
        self.price_history: List[dict] = []  # Store OHLCV data for indicators
        self.signals: List[TradingSignal] = []
        self.positions: Dict[str, Position] = {}
        self.account = AccountInfo()
        self.trades: List[dict] = []
        
        # Technical indicators
        self.current_zscore: float = 0.0
        self.current_rsi: float = 50.0
        self.current_volume_ma: float = 0.0
        
        # WebSocket clients
        self.clients: set = set()
        self.running = False
        
        # Futu client
        self.futu_client: Optional[FutuAPIClient] = None
        self.futu_trade_client = None
        self.account_unlocked = False
        
        # Strategy instance - 使用 TQQQ 策略邏輯（包含完整 Z-Score + RSI + 止盈止損）
        self.strategy_config = None
        if TQQQ_STRATEGY_AVAILABLE:
            try:
                # 使用 TQQQ 策略配置（Z-Score 閾值已調整為 1.6）
                self.strategy_config = {
                    'entry_zscore': 1.6,  # 回測優化閾值
                    'exit_zscore': 0.5,
                    'stop_loss_zscore': 3.5,
                    'position_pct': 0.50,
                    'lookback_period': 60,
                    'rsi_period': 14,
                    'rsi_overbought': 65.0,
                    'rsi_oversold': 35.0,
                    'take_profit_pct': 0.05,
                    'stop_loss_pct': 0.03,
                    'time_stop_days': 3
                }
                logger.info("✅ TQQQ Strategy config loaded (Z-Score threshold: 1.6)")
            except Exception as e:
                logger.error(f"❌ Failed to load strategy config: {e}")
                self.strategy_config = None
        
        logger.info(f"RealtimeBridge initialized for {self.symbol} (TQQQ Strategy v2.0)")
    
    async def start(self):
        """啟動橋接器"""
        logger.info("=" * 60)
        logger.info("Realtime Bridge Starting... (Framework A)")
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"WebSocket Server: ws://127.0.0.1:8765")
        logger.info("=" * 60)
        
        self.running = True
        
        # Connect to Futu API
        if FUTU_AVAILABLE:
            await self.connect_futu()
        
        # Start WebSocket server
        server = await websockets.serve(
            self.handle_client,
            "127.0.0.1",
            8765
        )
        
        # Start data collection loop
        data_task = asyncio.create_task(self.data_collection_loop())
        
        # Start signal calculation loop
        signal_task = asyncio.create_task(self.signal_calculation_loop())
        
        logger.info("Bridge is running!")
        await asyncio.gather(server.wait_closed(), data_task, signal_task)
    
    async def connect_futu(self):
        """連接富途API"""
        try:
            self.futu_client = FutuAPIClient(host=self.host, port=self.port)
            if self.futu_client.connect_quote():
                logger.info(f"Connected to Futu OpenD at {self.host}:{self.port}")
                
                # Subscribe to TQQQ quote
                quote_client = self.futu_client.get_quote_client()
                if quote_client:
                    ret, data = quote_client.subscribe(
                        [self.futu_code],
                        [SubType.QUOTE]
                    )
                    if ret == 0:
                        logger.info(f"Subscribed to {self.futu_code}")
                    else:
                        logger.warning(f"Subscribe failed: {data}")
                
                # Fetch historical data for indicator calculation
                await self.fetch_historical_data()
                
                # Connect trade client for account info
                await self.connect_trade_client()
            else:
                logger.error("Failed to connect to Futu OpenD")
        except Exception as e:
            logger.error(f"Futu connection error: {e}")
            self.futu_client = None
    
    async def fetch_historical_data(self):
        """獲取歷史K線數據用於計算指標"""
        try:
            quote_client = self.futu_client.get_quote_client()
            if not quote_client:
                logger.warning("Quote client not available for historical data")
                return
            
            logger.info(f"Fetching historical data for {self.symbol}...")
            
            # Subscribe to K-line data first
            ret_sub, _ = quote_client.subscribe([self.futu_code], [SubType.K_DAY])
            if ret_sub != 0:
                logger.warning(f"Failed to subscribe to K-line data: {ret_sub}")
                return
            
            # Get 100 days of daily K-lines
            ret, data = quote_client.get_cur_kline(self.futu_code, num=100, ktype=ft.KLType.K_DAY)
            
            if ret == 0 and data is not None and not data.empty:
                # Convert to price_history format
                self.price_history = []
                for _, row in data.iterrows():
                    self.price_history.append({
                        'close': float(row.get('close', 0)),
                        'high': float(row.get('high', 0)),
                        'low': float(row.get('low', 0)),
                        'open': float(row.get('open', 0)),
                        'volume': int(row.get('volume', 0)),
                        'timestamp': row.get('time_key', datetime.now().isoformat())
                    })
                
                logger.info(f"✅ Loaded {len(self.price_history)} historical data points")
                
                # Calculate initial indicators
                self.calculate_indicators()
                logger.info(f"Initial indicators - Z-Score: {self.current_zscore:.2f}, RSI: {self.current_rsi:.1f}")
            else:
                logger.warning(f"Failed to fetch historical data: ret={ret}")
                
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
    
    async def connect_trade_client(self):
        """連接交易客戶端並獲取帳戶信息"""
        try:
            from src.api.futu_client import FutuTradeClient, Market, TrdEnv
            
            self.futu_trade_client = FutuTradeClient(
                host=self.host, 
                port=self.port, 
                market=Market.US
            )
            
            if self.futu_trade_client.connect():
                logger.info("US Trade client connected")
                
                # Try to unlock trade with password
                trade_password = os.getenv("TRADE_PASSWORD", "011087")  # Account 24026693
                # Real account ID for SQQQ position: 281756477706540632
                if self.futu_trade_client.unlock_trade(trade_password):
                    logger.info("✅ Trade interface unlocked")
                    self.account_unlocked = True
                else:
                    logger.warning("⚠️ Failed to unlock trade interface - will try to fetch account anyway")
                
                # Try to get account info
                await self.update_account_from_futu()
            else:
                logger.warning("Failed to connect US trade client")
        except Exception as e:
            logger.warning(f"Trade client connection error: {e}")
            self.futu_trade_client = None
    
    async def update_account_from_futu(self):
        """從富途API更新真實帳戶數據、持倉和訂單"""
        if not self.futu_trade_client:
            return
        
        try:
            from src.api.futu_client import TrdEnv
            
            # ========== 1. 查詢帳戶資金 ==========
            # 使用正確的真實賬戶 ID (281756477706540632) 查詢
            ret_code, ret_data = self.futu_trade_client.accinfo_query(
                trd_env=TrdEnv.REAL,
                acc_id=REAL_ACCOUNT_ID
            )
            account_env = "REAL"
            
            # 如果真實賬戶為空，使用模擬賬戶
            if ret_code != 0 or ret_data is None or len(ret_data) == 0:
                ret_code, ret_data = self.futu_trade_client.accinfo_query(TrdEnv.SIMULATE)
                account_env = "SIMULATE"
            
            if ret_code == 0 and ret_data is not None and len(ret_data) > 0:
                # Handle DataFrame format from Futu API
                if hasattr(ret_data, 'to_dict'):
                    # Convert DataFrame to dict
                    account_list = ret_data.to_dict('records')
                    if len(account_list) > 0:
                        account_data = account_list[0]
                    else:
                        account_data = {}
                elif isinstance(ret_data, list) and len(ret_data) > 0:
                    account_data = ret_data[0]
                elif isinstance(ret_data, dict):
                    account_data = ret_data
                else:
                    account_data = {}
                
                # Log raw data for debugging
                logger.debug(f"Raw account data: {account_data}")
                
                # Update account info with various possible field names
                if isinstance(account_data, dict):
                    # Total assets - try multiple field names
                    total_assets = (account_data.get('total_assets') or 
                                  account_data.get('totalAsset') or 
                                  account_data.get('asset') or
                                  account_data.get('market_value') or
                                  account_data.get('marketValue'))
                    if total_assets:
                        self.account.total_assets = float(total_assets)
                        logger.debug(f"Updated total_assets: {self.account.total_assets}")
                    
                    # Available cash
                    available_cash = (account_data.get('available_cash') or 
                                    account_data.get('availableCash') or 
                                    account_data.get('cash') or 
                                    account_data.get('buying_power') or
                                    account_data.get('buyingPower') or
                                    account_data.get('max_power_short'))
                    if available_cash:
                        self.account.available_cash = float(available_cash)
                        logger.debug(f"Updated available_cash: {self.account.available_cash}")
                    
                    # Daily P&L
                    daily_pnl = (account_data.get('daily_pnl') or 
                               account_data.get('dailyPnL') or 
                               account_data.get('pl') or
                               account_data.get('today_profit_loss'))
                    if daily_pnl:
                        self.account.daily_pnl = float(daily_pnl)
                    
                    logger.info(f"✅ Account updated from Futu ({account_env}): Total=${self.account.total_assets:.2f}, Cash=${self.account.available_cash:.2f}")
            else:
                logger.warning(f"Could not fetch account info: ret_code={ret_code}, data={ret_data}")
            
            # ========== 2. 查詢持倉列表 ==========
            total_position_value = 0.0
            if account_env == "REAL":
                ret_code, positions_data = self.futu_trade_client.position_list_query(
                    trd_env=TrdEnv.REAL,
                    acc_id=REAL_ACCOUNT_ID
                )
            else:
                ret_code, positions_data = self.futu_trade_client.position_list_query(TrdEnv.SIMULATE)
            
            if ret_code == 0 and positions_data is not None and len(positions_data) > 0:
                # Clear existing positions and update with real data
                self.positions = {}
                
                # Handle DataFrame format
                if hasattr(positions_data, 'to_dict'):
                    positions_list = positions_data.to_dict('records')
                elif isinstance(positions_data, list):
                    positions_list = positions_data
                else:
                    positions_list = []
                
                for pos in positions_list:
                    if isinstance(pos, dict):
                        symbol = pos.get('code', '').replace('US.', '')
                        if symbol:
                            qty = int(pos.get('qty', 0))
                            current_price = float(pos.get('nominal_price', 0))
                            position_value = qty * current_price
                            total_position_value += position_value
                            
                            self.positions[symbol] = Position(
                                symbol=symbol,
                                quantity=qty,
                                avg_cost=float(pos.get('cost_price', 0)),
                                current_price=current_price,
                                unrealized_pnl=float(pos.get('pl_val', 0)),
                                direction='long' if pos.get('position_side') == 'LONG' else 'short'
                            )
                
                logger.info(f"✅ Positions updated: {len(self.positions)} positions, Total Value: ${total_position_value:.2f}")
                for sym, pos in self.positions.items():
                    logger.info(f"   {sym}: {pos.quantity} @ ${pos.current_price:.2f}, P&L: ${pos.unrealized_pnl:.2f}")
                
                # Recalculate total assets: cash + position value
                self.account.total_assets = self.account.available_cash + total_position_value
            else:
                logger.debug(f"No positions found or query failed: ret_code={ret_code}")
            
            # ========== 3. 查詢今日訂單 ==========
            if account_env == "REAL":
                ret_code, orders_data = self.futu_trade_client.order_list_query(
                    trd_env=TrdEnv.REAL,
                    acc_id=REAL_ACCOUNT_ID
                )
            else:
                ret_code, orders_data = self.futu_trade_client.order_list_query(TrdEnv.SIMULATE)
            
            if ret_code == 0 and orders_data is not None and len(orders_data) > 0:
                # Handle DataFrame format
                if hasattr(orders_data, 'to_dict'):
                    orders_list = orders_data.to_dict('records')
                elif isinstance(orders_data, list):
                    orders_list = orders_data
                else:
                    orders_list = []
                
                # Update today's trades
                self.trades = []
                for order in orders_list:
                    if isinstance(order, dict):
                        # Only include today's orders
                        order_time = order.get('create_time', '')
                        if isinstance(order_time, str) and datetime.now().strftime('%Y-%m-%d') in order_time:
                            self.trades.append({
                                'timestamp': order_time,
                                'symbol': order.get('code', '').replace('US.', ''),
                                'action': order.get('trd_side', ''),
                                'quantity': int(order.get('qty', 0)),
                                'price': float(order.get('price', 0)),
                                'status': order.get('order_status', '')
                            })
                
                logger.info(f"✅ Today's trades updated: {len(self.trades)} orders")
            else:
                logger.debug(f"No orders found or query failed: ret_code={ret_code}")
                
        except Exception as e:
            logger.warning(f"Failed to update account from Futu: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
    
    async def handle_client(self, websocket):
        """處理Dashboard WebSocket連接"""
        self.clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Dashboard client {client_id} connected. Total clients: {len(self.clients)}")
        
        try:
            # Send initial data
            await self.send_to_client(websocket, {
                "type": "initial",
                "data": self.get_dashboard_data()
            })
            
            # Keep connection alive and handle messages
            async for message in websocket:
                try:
                    msg = json.loads(message)
                    await self.handle_message(websocket, msg)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client {client_id}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected normally")
        except Exception as e:
            logger.error(f"Client {client_id} error: {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client {client_id} removed. Total clients: {len(self.clients)}")
    
    async def handle_message(self, websocket, message: dict):
        """處理客戶端消息"""
        action = message.get("action")
        
        if action == "ping":
            await self.send_to_client(websocket, {"type": "pong"})
        elif action == "get_data":
            await self.send_to_client(websocket, {
                "type": "data_update",
                "data": self.get_dashboard_data()
            })
        elif action == "toggle_strategy":
            enabled = message.get("enabled", False)
            logger.info(f"Strategy toggle: {enabled}")
            await self.broadcast({
                "type": "strategy_update",
                "data": {"running": enabled, "name": "TQQQ Long/Short Strategy (框架A)"}
            })
    
    async def send_to_client(self, websocket, message: dict):
        """發送消息到指定客戶端"""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send to client: {e}")
    
    async def broadcast(self, message: dict):
        """廣播消息到所有客戶端"""
        if not self.clients:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for client in self.clients:
            try:
                await client.send(message_json)
            except Exception:
                disconnected.append(client)
        
        # Remove disconnected clients
        for client in disconnected:
            self.clients.discard(client)
    
    async def data_collection_loop(self):
        """數據收集循環"""
        logger.info("Starting data collection loop...")
        
        account_update_counter = 0
        
        while self.running:
            try:
                if FUTU_AVAILABLE and self.futu_client:
                    await self.fetch_real_data()
                    
                    # Update account info every 30 seconds (every 15 iterations)
                    account_update_counter += 1
                    if account_update_counter >= 15:
                        await self.update_account_from_futu()
                        account_update_counter = 0
                else:
                    await self.fetch_mock_data()
                
                # Broadcast price update with full data
                dashboard_data = self.get_dashboard_data()
                await self.broadcast({
                    "type": "data_update",
                    "data": dashboard_data
                })
                
                await asyncio.sleep(2)  # Update every 2 seconds
                
            except Exception as e:
                logger.error(f"Data collection error: {e}")
                await asyncio.sleep(5)
    
    async def fetch_real_data(self):
        """從富途API獲取真實數據"""
        try:
            quote_client = self.futu_client.get_quote_client()
            if not quote_client:
                logger.warning("Quote client not available")
                return
            
            ret, data = quote_client.get_stock_quote([self.futu_code])
            
            logger.debug(f"Fetch quote result: ret={ret}, data_empty={data.empty if data is not None else 'N/A'}")
            
            if ret == 0 and data is not None and not data.empty:
                for _, row in data.iterrows():
                    code = row.get("code", "")
                    symbol = code.replace("US.", "") if code.startswith("US.") else code
                    
                    if symbol == self.symbol:
                        price = float(row.get("last_price", 0))
                        volume = int(row.get("volume", 0))
                        open_price = float(row.get("open_price", 0))
                        high = float(row.get("high_price", 0))
                        low = float(row.get("low_price", 0))
                        
                        # Update price data
                        self.price_data.update(price, volume)
                        self.price_data.open = open_price
                        self.price_data.high = high
                        self.price_data.low = low
                        
                        # Add to history for indicator calculation
                        self.price_history.append({
                            'close': price,
                            'high': high,
                            'low': low,
                            'open': open_price,
                            'volume': volume,
                            'timestamp': datetime.now().isoformat()
                        })
                        
                        # Keep only last 100 data points
                        if len(self.price_history) > 100:
                            self.price_history = self.price_history[-100:]
                        
                        # Calculate indicators
                        self.calculate_indicators()
                        
                        logger.debug(f"{symbol}: ${price:.2f} ({self.price_data.change_pct:+.2f}%) Z-Score: {self.current_zscore:.2f} RSI: {self.current_rsi:.1f}")
                        
        except Exception as e:
            logger.warning(f"Failed to fetch real data: {e}")
    
    async def fetch_mock_data(self):
        """獲取模擬數據（當Futu API不可用時）"""
        import random
        
        base_price = 70.5
        
        # Simulate small price movement
        if len(self.price_history) > 0:
            last_price = self.price_history[-1]['close']
        else:
            last_price = base_price
        
        change_pct = random.uniform(-0.005, 0.005)
        new_price = last_price * (1 + change_pct)
        volume = random.randint(1000000, 2000000)
        
        self.price_data.update(new_price, volume)
        self.price_data.open = base_price * 0.99
        self.price_data.high = max(new_price, base_price * 1.01)
        self.price_data.low = min(new_price, base_price * 0.99)
        
        # Add to history
        self.price_history.append({
            'close': new_price,
            'high': self.price_data.high,
            'low': self.price_data.low,
            'open': self.price_data.open,
            'volume': volume,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
        
        # Calculate indicators
        self.calculate_indicators()
    
    def calculate_indicators(self):
        """計算技術指標 (Z-Score, RSI, Volume MA)"""
        if len(self.price_history) < self.CONFIG['lookback_period']:
            return
        
        try:
            # Create DataFrame
            df = pd.DataFrame(self.price_history)
            
            # Calculate Z-Score
            lookback = self.CONFIG['lookback_period']
            prices = df['close'].values
            
            if len(prices) >= lookback:
                recent_prices = prices[-lookback:]
                mean_price = np.mean(recent_prices[:-1])  # Exclude current
                std_price = np.std(recent_prices[:-1])
                current_price = prices[-1]
                
                if std_price > 0:
                    self.current_zscore = (current_price - mean_price) / std_price
                else:
                    self.current_zscore = 0.0
            
            # Calculate RSI
            rsi_period = 14
            if len(prices) >= rsi_period + 1:
                deltas = np.diff(prices[-rsi_period-1:])
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                
                avg_gain = np.mean(gains)
                avg_loss = np.mean(losses)
                
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    self.current_rsi = 100 - (100 / (1 + rs))
                else:
                    self.current_rsi = 100.0
            
            # Calculate Volume MA
            volumes = df['volume'].values
            if len(volumes) >= 20:
                self.current_volume_ma = np.mean(volumes[-20:])
            
        except Exception as e:
            logger.warning(f"Indicator calculation error: {e}")
    
    async def signal_calculation_loop(self):
        """信號計算循環"""
        logger.info("Starting signal calculation loop...")
        
        while self.running:
            try:
                signal = self.calculate_signal()
                
                if signal and signal.signal_type != "HOLD":
                    self.signals.append(signal)
                    if len(self.signals) > 50:
                        self.signals = self.signals[-50:]
                    
                    logger.info(f"Signal generated: {signal.symbol} {signal.signal_type} (z-score: {signal.z_score:.2f}, rsi: {signal.rsi:.1f})")
                    
                    # Execute trade with 50% cash position
                    await self.execute_trade(signal)
                    
                    # Broadcast signal with full dashboard update
                    await self.broadcast({
                        "type": "signal",
                        "data": asdict(signal)
                    })
                    # Also send full data update
                    await self.broadcast({
                        "type": "data_update",
                        "data": self.get_dashboard_data()
                    })
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Signal calculation error: {e}")
                await asyncio.sleep(10)
    
    def calculate_signal(self) -> Optional[TradingSignal]:
        """計算交易信號（使用 TQQQ Strategy 邏輯，包含完整 Z-Score + RSI + 止盈止損）"""
        if len(self.price_history) < self.CONFIG['lookback_period']:
            return None
        
        try:
            # 使用 TQQQ Strategy 邏輯（包含 RSI、MACD、市場狀態判斷）
            if TQQQ_STRATEGY_AVAILABLE and self.strategy_config:
                df = pd.DataFrame(self.price_history)
                current = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else current
                
                zscore = current.get('zscore', self.current_zscore)
                rsi = current.get('rsi', self.current_rsi)
                
                # 計算 MACD
                exp1 = df['close'].ewm(span=12, adjust=False).mean()
                exp2 = df['close'].ewm(span=26, adjust=False).mean()
                macd = exp1 - exp2
                macd_signal = macd.ewm(span=9, adjust=False).mean()
                macd_hist = macd - macd_signal
                
                current_macd_hist = macd_hist.iloc[-1]
                prev_macd_hist = macd_hist.iloc[-2] if len(macd_hist) > 1 else current_macd_hist
                
                # 市場狀態判斷（200日均線）
                if len(df) >= 200:
                    ma200 = df['close'].rolling(window=200).mean().iloc[-1]
                    current_price = current['close']
                    if current_price > ma200 * 1.05:
                        market_state = 'bull'
                    elif current_price < ma200 * 0.95:
                        market_state = 'bear'
                    else:
                        market_state = 'sideways'
                else:
                    market_state = 'sideways'
                
                # 做多條件（分層過濾）
                if zscore < -self.strategy_config['entry_zscore']:
                    rsi_condition = rsi < self.strategy_config['rsi_oversold']
                    macd_condition = prev_macd_hist < 0 and current_macd_hist >= 0
                    
                    if rsi_condition or macd_condition:
                        if market_state in ['bull', 'sideways']:
                            confirm_indicators = []
                            if rsi_condition:
                                confirm_indicators.append(f"RSI({rsi:.1f})")
                            if macd_condition:
                                confirm_indicators.append("MACD金叉")
                            
                            return TradingSignal(
                                symbol=self.symbol,
                                signal_type="BUY",
                                confidence=min(abs(zscore) / 3 * 100, 95),
                                reason=f"Z-Score({zscore:.2f})+{'/'.join(confirm_indicators)}+{market_state}市",
                                z_score=zscore,
                                rsi=rsi
                            )
                
                # 做空條件（分層過濾）
                if zscore > self.strategy_config['entry_zscore']:
                    rsi_condition = rsi > self.strategy_config['rsi_overbought']
                    macd_condition = prev_macd_hist > 0 and current_macd_hist <= 0
                    
                    if rsi_condition or macd_condition:
                        if market_state in ['bear', 'sideways']:
                            confirm_indicators = []
                            if rsi_condition:
                                confirm_indicators.append(f"RSI({rsi:.1f})")
                            if macd_condition:
                                confirm_indicators.append("MACD死叉")
                            
                            return TradingSignal(
                                symbol=self.symbol,
                                signal_type="SELL",
                                confidence=min(abs(zscore) / 3 * 100, 95),
                                reason=f"Z-Score({zscore:.2f})+{'/'.join(confirm_indicators)}+{market_state}市",
                                z_score=zscore,
                                rsi=rsi
                            )
                
                # 檢查出場條件（止盈止損、時間止損）
                if self.symbol in self.positions and self.positions[self.symbol].quantity > 0:
                    position = self.positions[self.symbol]
                    entry_price = position.avg_cost
                    current_price = current['close']
                    direction = position.direction
                    
                    # 計算盈虧
                    if direction == 'long':
                        pnl_pct = (current_price - entry_price) / entry_price
                    else:
                        pnl_pct = (entry_price - current_price) / entry_price
                    
                    # 止盈檢查
                    if pnl_pct >= self.strategy_config['take_profit_pct']:
                        return TradingSignal(
                            symbol=self.symbol,
                            signal_type="SELL" if direction == "long" else "BUY",
                            confidence=90,
                            reason=f"止盈({pnl_pct*100:.2f}%)",
                            z_score=zscore,
                            rsi=rsi
                        )
                    
                    # 止損檢查
                    if pnl_pct <= -self.strategy_config['stop_loss_pct']:
                        return TradingSignal(
                            symbol=self.symbol,
                            signal_type="SELL" if direction == "long" else "BUY",
                            confidence=90,
                            reason=f"止損({pnl_pct*100:.2f}%)",
                            z_score=zscore,
                            rsi=rsi
                        )
                    
                    # Z-Score止損
                    if direction == 'long' and zscore > self.strategy_config['stop_loss_zscore']:
                        return TradingSignal(
                            symbol=self.symbol,
                            signal_type="SELL",
                            confidence=90,
                            reason=f"Z-Score止損({zscore:.2f})",
                            z_score=zscore,
                            rsi=rsi
                        )
                    if direction == 'short' and zscore < -self.strategy_config['stop_loss_zscore']:
                        return TradingSignal(
                            symbol=self.symbol,
                            signal_type="BUY",
                            confidence=90,
                            reason=f"Z-Score止損({zscore:.2f})",
                            z_score=zscore,
                            rsi=rsi
                        )
                    
                    # Z-Score回歸止盈
                    if abs(zscore) < self.strategy_config['exit_zscore']:
                        return TradingSignal(
                            symbol=self.symbol,
                            signal_type="SELL" if direction == "long" else "BUY",
                            confidence=80,
                            reason=f"Z-Score回歸({zscore:.2f})",
                            z_score=zscore,
                            rsi=rsi
                        )
                
                # 無信號
                return TradingSignal(
                    symbol=self.symbol,
                    signal_type="HOLD",
                    confidence=50,
                    reason=f"Z-Score({zscore:.2f})觀望",
                    z_score=zscore,
                    rsi=rsi
                )
            else:
                # Fallback: 使用簡化邏輯
                zscore = self.current_zscore
                rsi = self.current_rsi
                
                if zscore < -1.6 and rsi < 35:
                    return TradingSignal(
                        symbol=self.symbol,
                        signal_type="BUY",
                        confidence=min(abs(zscore) / 3 * 100, 95),
                        reason=f"Z-Score({zscore:.2f})超賣+RSI({rsi:.1f})低",
                        z_score=zscore,
                        rsi=rsi
                    )
                elif zscore > 1.6 and rsi > 65:
                    return TradingSignal(
                        symbol=self.symbol,
                        signal_type="SELL",
                        confidence=min(abs(zscore) / 3 * 100, 95),
                        reason=f"Z-Score({zscore:.2f})超買+RSI({rsi:.1f})高",
                        z_score=zscore,
                        rsi=rsi
                    )
                elif abs(zscore) < 0.5:
                    if self.symbol in self.positions and self.positions[self.symbol].quantity > 0:
                        position = self.positions[self.symbol]
                        return TradingSignal(
                            symbol=self.symbol,
                            signal_type="SELL" if position.direction == "long" else "BUY",
                            confidence=70,
                            reason=f"Z-Score回歸({zscore:.2f})-平倉",
                            z_score=zscore,
                            rsi=rsi
                        )
                    return TradingSignal(
                        symbol=self.symbol,
                        signal_type="HOLD",
                        confidence=50,
                        reason=f"Z-Score({zscore:.2f})正常區間",
                        z_score=zscore,
                        rsi=rsi
                    )
                else:
                    return TradingSignal(
                        symbol=self.symbol,
                        signal_type="HOLD",
                        confidence=50,
                        reason=f"Z-Score({zscore:.2f})觀望",
                        z_score=zscore,
                        rsi=rsi
                    )
        except Exception as e:
            logger.error(f"Signal calculation error: {e}")
            return None
    
    def get_dashboard_data(self) -> dict:
        """獲取Dashboard數據 - 框架A格式"""
        # Update positions with current prices
        for symbol, position in self.positions.items():
            if symbol == self.symbol:
                position.current_price = self.price_data.price
                position.unrealized_pnl = (position.current_price - position.avg_cost) * position.quantity
                if position.avg_cost > 0:
                    position.unrealized_pnl_pct = ((position.current_price / position.avg_cost) - 1) * 100
        
        # Calculate total unrealized PnL
        total_unrealized = sum(p.unrealized_pnl for p in self.positions.values())
        self.account.total_unrealized_pnl = total_unrealized
        
        # Format positions for dashboard
        positions_list = []
        for symbol, pos in self.positions.items():
            if pos.quantity > 0:
                positions_list.append({
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "avg_cost": round(pos.avg_cost, 2),
                    "current_price": round(pos.current_price, 2),
                    "unrealized_pnl": round(pos.unrealized_pnl, 2),
                    "unrealized_pnl_pct": round(pos.unrealized_pnl_pct, 2),
                    "direction": pos.direction
                })
        
        # Format TQQQ data with indicators
        tqqq_data = {
            "price": round(self.price_data.price, 2),
            "change": round(self.price_data.change, 2),
            "change_pct": round(self.price_data.change_pct, 2),
            "volume": self.price_data.volume,
            "high": round(self.price_data.high, 2),
            "low": round(self.price_data.low, 2),
            "zscore": round(self.current_zscore, 2),
            "rsi": round(self.current_rsi, 1),
            "volume_ma": round(self.current_volume_ma, 0)
        }
        
        # Current signal
        current_signal = None
        if self.signals:
            last_signal = self.signals[-1]
            current_signal = {
                "type": last_signal.signal_type,
                "confidence": round(last_signal.confidence / 100, 2),
                "reason": last_signal.reason,
                "z_score": round(last_signal.z_score, 2),
                "rsi": round(last_signal.rsi, 1)
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "TQQQ": tqqq_data,
            "signal": current_signal,
            "account": {
                "total_assets": round(self.account.total_assets, 2),
                "available_cash": round(self.account.available_cash, 2),
                "daily_pnl": round(self.account.daily_pnl, 2),
                "daily_pnl_pct": round(self.account.daily_pnl_pct, 2),
                "total_unrealized_pnl": round(total_unrealized, 2)
            },
            "position": positions_list[0] if positions_list else None,
            "positions": positions_list,
            "signals": [asdict(s) for s in self.signals[-10:]],
            "today_trades": self.trades[-20:],
            "strategy": {
                "running": True,
                "name": "TQQQ Long/Short Strategy (框架A)",
                "last_update": datetime.now().isoformat(),
                "config": self.CONFIG
            }
        }
    
    async def execute_trade(self, signal: TradingSignal):
        """執行交易 - 使用50%可用現金"""
        try:
            symbol = signal.symbol
            price = self.price_data.price
            
            if price <= 0:
                logger.warning(f"Invalid price for {symbol}: {price}")
                return
            
            # Calculate position size - use 50% of available cash
            cash_to_use = self.account.available_cash * self.CONFIG['position_pct']
            quantity = int(cash_to_use / price)
            
            if quantity <= 0:
                logger.warning(f"Insufficient cash to execute trade. Cash: ${self.account.available_cash:.2f}, Price: ${price:.2f}")
                return
            
            if signal.signal_type == "BUY":
                # Check if already have long position
                if symbol in self.positions and self.positions[symbol].quantity > 0 and self.positions[symbol].direction == "long":
                    logger.info(f"Already have long position in {symbol}, skipping BUY")
                    return
                
                # Execute buy (long)
                cost = price * quantity
                fee = cost * 0.001  # 0.1% commission
                total_cost = cost + fee
                
                if total_cost > self.account.available_cash:
                    logger.warning(f"Insufficient cash for BUY. Need: ${total_cost:.2f}, Have: ${self.account.available_cash:.2f}")
                    return
                
                # Update position
                if symbol not in self.positions:
                    self.positions[symbol] = Position(symbol=symbol)
                
                position = self.positions[symbol]
                position.quantity = quantity
                position.avg_cost = price
                position.current_price = price
                position.direction = "long"
                position.entry_time = datetime.now().isoformat()
                
                # Update account
                self.account.available_cash -= total_cost
                self.account.total_assets = self.account.available_cash + (price * quantity)
                
                # Record trade
                trade = {
                    "timestamp": datetime.now().isoformat(),
                    "symbol": symbol,
                    "action": "BUY",
                    "direction": "long",
                    "quantity": quantity,
                    "price": round(price, 2),
                    "fee": round(fee, 2),
                    "total_cost": round(total_cost, 2),
                    "reason": signal.reason
                }
                self.trades.append(trade)
                
                logger.info(f"✅ BUY (Long) {quantity} {symbol} @ ${price:.2f} (50% cash = ${cash_to_use:.2f})")
                
            elif signal.signal_type == "SELL":
                # Check if have position to sell
                if symbol not in self.positions or self.positions[symbol].quantity <= 0:
                    # Open short position if no long position
                    if signal.z_score > self.CONFIG['entry_zscore']:
                        # Execute short sell
                        proceeds = price * quantity
                        fee = proceeds * 0.001
                        net_proceeds = proceeds - fee
                        
                        # Update position (short)
                        if symbol not in self.positions:
                            self.positions[symbol] = Position(symbol=symbol)
                        
                        position = self.positions[symbol]
                        position.quantity = quantity
                        position.avg_cost = price
                        position.current_price = price
                        position.direction = "short"
                        position.entry_time = datetime.now().isoformat()
                        
                        # Update account
                        self.account.available_cash += net_proceeds
                        
                        # Record trade
                        trade = {
                            "timestamp": datetime.now().isoformat(),
                            "symbol": symbol,
                            "action": "SELL",
                            "direction": "short",
                            "quantity": quantity,
                            "price": round(price, 2),
                            "fee": round(fee, 2),
                            "net_proceeds": round(net_proceeds, 2),
                            "reason": signal.reason
                        }
                        self.trades.append(trade)
                        
                        logger.info(f"✅ SELL (Short) {quantity} {symbol} @ ${price:.2f}")
                    return
                
                # Close existing position
                position = self.positions[symbol]
                quantity = position.quantity
                
                # Calculate proceeds
                proceeds = price * quantity
                fee = proceeds * 0.001
                net_proceeds = proceeds - fee
                
                # Calculate P&L
                if position.direction == "long":
                    cost_basis = position.avg_cost * quantity
                    realized_pnl = proceeds - cost_basis - fee
                else:  # short
                    cost_basis = position.avg_cost * quantity
                    realized_pnl = cost_basis - proceeds - fee
                
                # Update account
                self.account.available_cash += net_proceeds
                self.account.daily_pnl += realized_pnl
                self.account.total_assets = self.account.available_cash
                
                # Record trade
                trade = {
                    "timestamp": datetime.now().isoformat(),
                    "symbol": symbol,
                    "action": "SELL",
                    "direction": position.direction,
                    "quantity": quantity,
                    "price": round(price, 2),
                    "fee": round(fee, 2),
                    "net_proceeds": round(net_proceeds, 2),
                    "realized_pnl": round(realized_pnl, 2),
                    "reason": signal.reason
                }
                self.trades.append(trade)
                
                # Clear position
                del self.positions[symbol]
                
                logger.info(f"✅ CLOSE {position.direction} {quantity} {symbol} @ ${price:.2f}, P&L: ${realized_pnl:+.2f}")
            
            # Broadcast update
            await self.broadcast({
                "type": "trade_update",
                "data": self.get_dashboard_data()
            })
            
        except Exception as e:
            logger.error(f"Trade execution error: {e}")
    
    def stop(self):
        """停止橋接器"""
        self.running = False
        if self.futu_client:
            self.futu_client.disconnect_all()
        logger.info("RealtimeBridge stopped")


async def main():
    """主函數"""
    bridge = RealtimeBridge()
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
    finally:
        bridge.stop()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
