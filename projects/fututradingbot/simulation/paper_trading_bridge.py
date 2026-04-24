"""
模擬交易 Bridge - 獨立於實盤系統
用途: Z-Score 策略實測
特點: 模擬交易執行，不真實下單
"""

import asyncio
import json
import websockets
from datetime import datetime
from pathlib import Path
import sys
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
import pandas as pd
import numpy as np

# Setup logging
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.logger_config import setup_logger
logger = setup_logger("PaperBridge", "logs/paper_bridge.log")

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

# 導入策略
from src.strategies.zscore_strategy import ZScoreStrategy
from src.data.market_data import MarketDataManager

try:
    from src.api.futu_client import FutuAPIClient
    FUTU_AVAILABLE = True
except ImportError:
    logger.warning("Futu API not available, using mock data")
    FUTU_AVAILABLE = False


@dataclass
class PaperPosition:
    """模擬持倉"""
    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0
    direction: str = "long"
    entry_time: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def unrealized_pnl(self) -> float:
        if self.direction == "long":
            return (self.current_price - self.avg_cost) * self.quantity
        else:
            return (self.avg_cost - self.current_price) * self.quantity


@dataclass
class PaperTrade:
    """模擬交易記錄"""
    timestamp: str
    symbol: str
    action: str
    direction: str
    quantity: int
    price: float
    fee: float
    realized_pnl: float = 0.0
    reason: str = ""


@dataclass
class PaperAccount:
    """模擬賬戶"""
    initial_capital: float = 100000.0
    available_cash: float = 100000.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    
    @property
    def total_assets(self) -> float:
        return self.available_cash
    
    @property
    def win_rate(self) -> float:
        if self.total_trades > 0:
            return (self.winning_trades / self.total_trades) * 100
        return 0.0


class PaperTradingBridge:
    """模擬交易 Bridge - 獨立於實盤系統"""
    
    # Z-Score 策略參數（固定測試參數）
    CONFIG = {
        'period': 60,
        'upper_threshold': 1.6,
        'lower_threshold': -1.6,
        'exit_threshold': 0.5,
        'position_pct': 0.50,
        'commission_rate': 0.001,
    }
    
    def __init__(self, host: str = "127.0.0.1", port: int = 11111):
        self.host = host
        self.port = port
        self.symbol = "TQQQ"
        self.futu_code = "US.TQQQ"
        
        # 數據存儲
        self.price_data = {'price': 0.0, 'volume': 0, 'timestamp': None}
        self.price_history: List[dict] = []
        self.current_zscore: float = 0.0
        self.current_rsi: float = 50.0
        
        # 模擬交易數據
        self.account = PaperAccount()
        self.position: Optional[PaperPosition] = None
        self.trades: List[PaperTrade] = []
        
        # WebSocket 客戶端
        self.clients: set = set()
        self.running = False
        
        # Futu client
        self.futu_client = None
        
        # 策略
        self.strategy = ZScoreStrategy(
            period=self.CONFIG['period'],
            upper_threshold=self.CONFIG['upper_threshold'],
            lower_threshold=self.CONFIG['lower_threshold'],
            exit_threshold=self.CONFIG['exit_threshold'],
            position_pct=self.CONFIG['position_pct']
        )
        
        # 數據管理器
        self.md = MarketDataManager()
        
        # 數據目錄
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info(f"PaperTradingBridge initialized (Z-Score: {self.CONFIG['upper_threshold']})")
    
    async def start(self):
        """啟動模擬交易 Bridge"""
        logger.info("=" * 60)
        logger.info("PAPER TRADING BRIDGE Starting...")
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"WebSocket: ws://127.0.0.1:8766")
        logger.info(f"Initial Capital: ${self.account.initial_capital:,.2f}")
        logger.info("=" * 60)
        
        self.running = True
        
        if FUTU_AVAILABLE:
            await self.connect_futu()
        
        # 啟動 WebSocket 服務器 (Port 8766 - 與實盤 8765 不同)
        server = await websockets.serve(
            self.handle_client,
            "127.0.0.1",
            8766
        )
        
        data_task = asyncio.create_task(self.data_collection_loop())
        signal_task = asyncio.create_task(self.trading_loop())
        
        logger.info("Paper Trading Bridge is running!")
        await asyncio.gather(server.wait_closed(), data_task, signal_task)
    
    async def connect_futu(self):
        """連接富途 API"""
        try:
            self.futu_client = FutuAPIClient(host=self.host, port=self.port)
            if self.futu_client.connect_quote():
                logger.info(f"Connected to Futu OpenD at {self.host}:{self.port}")
                quote_client = self.futu_client.get_quote_client()
                if quote_client:
                    ret, data = quote_client.subscribe([self.futu_code], ["QUOTE"])
                    if ret == 0:
                        logger.info(f"Subscribed to {self.futu_code}")
        except Exception as e:
            logger.error(f"Futu connection error: {e}")
            self.futu_client = None
    
    async def handle_client(self, websocket):
        """處理 Dashboard WebSocket 連接"""
        self.clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Paper Dashboard client {client_id} connected. Total: {len(self.clients)}")
        
        try:
            await self.send_to_client(websocket, {
                "type": "initial",
                "data": self.get_dashboard_data()
            })
            
            async for message in websocket:
                try:
                    msg = json.loads(message)
                    await self.handle_message(websocket, msg)
                except json.JSONDecodeError:
                    pass
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
    
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
    
    async def send_to_client(self, websocket, message: dict):
        """發送消息到指定客戶端"""
        try:
            await websocket.send(json.dumps(message))
        except Exception:
            pass
    
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
        for client in disconnected:
            self.clients.discard(client)
    
    async def data_collection_loop(self):
        """數據收集循環"""
        while self.running:
            try:
                if FUTU_AVAILABLE and self.futu_client:
                    await self.fetch_real_data()
                else:
                    await self.fetch_mock_data()
                
                await self.broadcast({
                    "type": "data_update",
                    "data": self.get_dashboard_data()
                })
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Data collection error: {e}")
                await asyncio.sleep(5)
    
    async def fetch_real_data(self):
        """從富途 API 獲取真實數據"""
        try:
            quote_client = self.futu_client.get_quote_client()
            if not quote_client:
                return
            ret, data = quote_client.get_stock_quote([self.futu_code])
            if ret == 0 and not data.empty:
                for _, row in data.iterrows():
                    price = float(row.get("last_price", 0))
                    volume = int(row.get("volume", 0))
                    self.price_data = {
                        'price': price,
                        'volume': volume,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.price_history.append({
                        'close': price,
                        'volume': volume,
                        'timestamp': datetime.now().isoformat()
                    })
                    if len(self.price_history) > 100:
                        self.price_history = self.price_history[-100:]
                    self.calculate_indicators()
        except Exception as e:
            logger.warning(f"Failed to fetch real data: {e}")
    
    async def fetch_mock_data(self):
        """獲取模擬數據"""
        import random
        base_price = 70.5
        if len(self.price_history) > 0:
            last_price = self.price_history[-1]['close']
        else:
            last_price = base_price
        change_pct = random.uniform(-0.005, 0.005)
        new_price = last_price * (1 + change_pct)
        volume = random.randint(1000000, 2000000)
        self.price_data = {
            'price': new_price,
            'volume': volume,
            'timestamp': datetime.now().isoformat()
        }
        self.price_history.append({
            'close': new_price,
            'volume': volume,
            'timestamp': datetime.now().isoformat()
        })
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
        self.calculate_indicators()
    
    def calculate_indicators(self):
        """計算技術指標"""
        if len(self.price_history) < self.CONFIG['period']:
            return
        try:
            df = pd.DataFrame(self.price_history)
            prices = df['close'].values
            lookback = self.CONFIG['period']
            recent_prices = prices[-lookback:]
            mean_price = np.mean(recent_prices[:-1])
            std_price = np.std(recent_prices[:-1])
            current_price = prices[-1]
            if std_price > 0:
                self.current_zscore = (current_price - mean_price) / std_price
            else:
                self.current_zscore = 0.0
        except Exception as e:
            logger.warning(f"Indicator calculation error: {e}")
    
    async def trading_loop(self):
        """交易信號循環"""
        logger.info("Starting paper trading loop...")
        while self.running:
            try:
                signal = self.check_signal()
                if signal and signal.get('signal') != 0:
                    await self.execute_paper_trade(signal)
                    await self.broadcast({
                        "type": "trade",
                        "data": self.get_dashboard_data()
                    })
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(10)
    
    def check_signal(self) -> Optional[dict]:
        """檢查交易信號"""
        if len(self.price_history) < self.CONFIG['period']:
            return None
        try:
            df = pd.DataFrame(self.price_history)
            signal_data = self.strategy.generate_signal(df)
            return signal_data
        except Exception as e:
            logger.error(f"Signal check error: {e}")
            return None
    
    async def execute_paper_trade(self, signal: dict):
        """執行模擬交易"""
        try:
            signal_type = signal.get('signal_text', '')
            price = self.price_data['price']
            
            if signal_type == '做多' and self.position is None:
                # 開多倉
                cash_to_use = self.account.available_cash * self.CONFIG['position_pct']
                quantity = int(cash_to_use / price)
                if quantity > 0:
                    cost = price * quantity
                    fee = cost * self.CONFIG['commission_rate']
                    total_cost = cost + fee
                    
                    self.position = PaperPosition(
                        symbol=self.symbol,
                        quantity=quantity,
                        avg_cost=price,
                        current_price=price,
                        direction="long"
                    )
                    self.account.available_cash -= total_cost
                    
                    trade = PaperTrade(
                        timestamp=datetime.now().isoformat(),
                        symbol=self.symbol,
                        action="BUY",
                        direction="long",
                        quantity=quantity,
                        price=price,
                        fee=fee,
                        reason=f"Z-Score: {signal.get('zscore', 0):.2f}"
                    )
                    self.trades.append(trade)
                    logger.info(f"[PAPER] BUY {quantity} {self.symbol} @ ${price:.2f}")
                    
            elif signal_type == '做空' and self.position is None:
                # 開空倉
                cash_to_use = self.account.available_cash * self.CONFIG['position_pct']
                quantity = int(cash_to_use / price)
                if quantity > 0:
                    proceeds = price * quantity
                    fee = proceeds * self.CONFIG['commission_rate']
                    
                    self.position = PaperPosition(
                        symbol=self.symbol,
                        quantity=quantity,
                        avg_cost=price,
                        current_price=price,
                        direction="short"
                    )
                    self.account.available_cash += (proceeds - fee)
                    
                    trade = PaperTrade(
                        timestamp=datetime.now().isoformat(),
                        symbol=self.symbol,
                        action="SELL",
                        direction="short",
                        quantity=quantity,
                        price=price,
                        fee=fee,
                        reason=f"Z-Score: {signal.get('zscore', 0):.2f}"
                    )
                    self.trades.append(trade)
                    logger.info(f"[PAPER] SHORT {quantity} {self.symbol} @ ${price:.2f}")
                    
            elif signal_type == '平倉/觀望' and self.position is not None:
                # 平倉
                position = self.position
                quantity = position.quantity
                
                if position.direction == "long":
                    proceeds = price * quantity
                    fee = proceeds * self.CONFIG['commission_rate']
                    net_proceeds = proceeds - fee
                    realized_pnl = (price - position.avg_cost) * quantity - fee
                    self.account.available_cash += net_proceeds
                else:  # short
                    cost = price * quantity
                    fee = cost * self.CONFIG['commission_rate']
                    realized_pnl = (position.avg_cost - price) * quantity - fee
                    self.account.available_cash -= (cost + fee)
                
                self.account.total_trades += 1
                if realized_pnl > 0:
                    self.account.winning_trades += 1
                else:
                    self.account.losing_trades += 1
                self.account.total_pnl += realized_pnl
                
                trade = PaperTrade(
                    timestamp=datetime.now().isoformat(),
                    symbol=self.symbol,
                    action="SELL" if position.direction == "long" else "BUY",
                    direction=position.direction,
                    quantity=quantity,
                    price=price,
                    fee=fee,
                    realized_pnl=realized_pnl,
                    reason="Z-Score回歸"
                )
                self.trades.append(trade)
                logger.info(f"[PAPER] CLOSE {position.direction} {quantity} {self.symbol} @ ${price:.2f}, PnL: ${realized_pnl:+.2f}")
                
                self.position = None
                
        except Exception as e:
            logger.error(f"Paper trade execution error: {e}")
    
    def get_dashboard_data(self) -> dict:
        """獲取 Dashboard 數據"""
        position_data = None
        if self.position:
            self.position.current_price = self.price_data['price']
            position_data = {
                "symbol": self.position.symbol,
                "quantity": self.position.quantity,
                "avg_cost": round(self.position.avg_cost, 2),
                "current_price": round(self.position.current_price, 2),
                "unrealized_pnl": round(self.position.unrealized_pnl, 2),
                "unrealized_pnl_pct": round(self.position.unrealized_pnl_pct, 2),
                "direction": self.position.direction
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "TQQQ": {
                "price": round(self.price_data['price'], 2),
                "zscore": round(self.current_zscore, 2),
                "volume": self.price_data['volume']
            },
            "account": {
                "initial_capital": self.account.initial_capital,
                "available_cash": round(self.account.available_cash, 2),
                "total_assets": round(self.account.total_assets, 2),
                "total_pnl": round(self.account.total_pnl, 2),
                "win_rate": round(self.account.win_rate, 2),
                "total_trades": self.account.total_trades
            },
            "position": position_data,
            "trades": [{
                "timestamp": t.timestamp,
                "symbol": t.symbol,
                "action": t.action,
                "quantity": t.quantity,
                "price": t.price,
                "realized_pnl": t.realized_pnl
            } for t in self.trades[-10:]],
            "strategy": {
                "running": True,
                "name": "Z-Score Paper Trading",
                "threshold": self.CONFIG['upper_threshold']
            }
        }
    
    def stop(self):
        """停止 Bridge"""
        self.running = False
        if self.futu_client:
            self.futu_client.disconnect_all()
        logger.info("PaperTradingBridge stopped")


async def main():
    """主函數"""
    bridge = PaperTradingBridge()
    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested...")
    finally:
        bridge.stop()


if __name__ == "__main__":
    asyncio.run(main())
