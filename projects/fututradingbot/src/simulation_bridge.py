"""
Real Simulation Bridge - 真實模擬交易數據橋接

連接配對交易策略引擎至 Dashboard
提供實時模擬交易數據
"""

import asyncio
import json
import websockets
from datetime import datetime
from pathlib import Path
import sys

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategies.pairs_trading import PairsTradingStrategy, PairsTradingConfig
from futu import OpenQuoteContext, KLType, SubType
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SimulationBridge:
    """模擬交易數據橋接器"""
    
    def __init__(self, symbols: list = None):
        self.symbols = symbols or ["TQQQ", "SQQQ"]
        self.strategy = PairsTradingStrategy({
            'entry_zscore': 2.0,
            'exit_zscore': 0.5,
            'position_pct': 0.1
        })
        self.quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
        self.running = False
        self.positions = {}
        self.trades = []
        self.account = {
            "cash": 100000.0,
            "equity": 100000.0,
            "daily_pnl": 0.0
        }
        
    async def start(self):
        """啟動橋接"""
        logger.info("=" * 50)
        logger.info("Simulation Bridge Started")
        logger.info(f"Symbols: {self.symbols}")
        logger.info("=" * 50)
        
        self.running = True
        
        # Start WebSocket server for Dashboard
        server = await websockets.serve(
            self.handle_dashboard,
            "127.0.0.1",
            8765
        )
        
        # Start trading loop
        trading_task = asyncio.create_task(self.trading_loop())
        
        logger.info("Bridge running on ws://127.0.0.1:8765")
        await asyncio.gather(server.wait_closed(), trading_task)
        
    async def handle_dashboard(self, websocket, path):
        """處理 Dashboard 連接"""
        logger.info("Dashboard connected")
        
        try:
            while self.running:
                # Send current data
                data = self.get_dashboard_data()
                await websocket.send(json.dumps(data))
                await asyncio.sleep(1)  # Update every second
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Dashboard disconnected")
            
    async def trading_loop(self):
        """交易主循環"""
        logger.info("Starting trading loop...")
        
        while self.running:
            try:
                # Get market data
                tqqq_data = await self.get_market_data("TQQQ")
                sqqq_data = await self.get_market_data("SQQQ")
                
                if tqqq_data and sqqq_data:
                    # Generate trading signal
                    signal = self.strategy.generate_signal(
                        tqqq_data, sqqq_data
                    )
                    
                    # Update price data for strategy
                self.strategy.update_price_data("TQQQ", [tqqq_data["price"]])
                self.strategy.update_price_data("SQQQ", [sqqq_data["price"]])
                
                # Generate signal
                signal = self.strategy.on_bar("TQQQ_SQQQ_pair")
                
                if signal:
                    await self.execute_signal(signal)
                        
                # Log status every 30 seconds
                await self.log_status()
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(10)
                
    async def get_market_data(self, symbol: str):
        """獲取市場數據"""
        try:
            # Subscribe to real-time data
            ret, data = self.quote_ctx.subscribe([f"US.{symbol}"], [SubType.QUOTE])
            if ret != 0:
                logger.warning(f"Subscribe {symbol} failed: {data}")
                return None
                
            # Get quote
            ret, data = self.quote_ctx.get_stock_quote([f"US.{symbol}"])
            if ret != 0 or data.empty:
                logger.warning(f"Get quote {symbol} failed: {data}")
                return None
                
            row = data.iloc[0]
            return {
                "symbol": symbol,
                "price": float(row.get("last_price", 0)),
                "open": float(row.get("open_price", 0)),
                "high": float(row.get("high_price", 0)),
                "low": float(row.get("low_price", 0)),
                "volume": int(row.get("volume", 0)),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Failed to get {symbol} data: {e}")
            return None
            
    async def execute_signal(self, signal: dict):
        """執行交易信號"""
        logger.info(f"Executing signal: {signal}")
        
        trade = {
            "timestamp": datetime.now().isoformat(),
            "symbol": signal["symbol"],
            "action": signal["action"],
            "quantity": signal["quantity"],
            "price": signal["price"],
            "reason": signal["reason"]
        }
        
        self.trades.append(trade)
        
        # Update positions
        if signal["action"] == "BUY":
            self.positions[signal["symbol"]] = {
                "quantity": signal["quantity"],
                "avg_cost": signal["price"]
            }
            self.account["cash"] -= signal["price"] * signal["quantity"]
        elif signal["action"] == "SELL":
            if signal["symbol"] in self.positions:
                del self.positions[signal["symbol"]]
            self.account["cash"] += signal["price"] * signal["quantity"]
            
        # Save to log
        await self.save_trade_log(trade)
        
    async def log_status(self):
        """記錄狀態"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "account": self.account,
            "positions": self.positions,
            "trade_count": len(self.trades)
        }
        logger.info(f"Status: {status}")
        
    async def save_trade_log(self, trade: dict):
        """保存交易記錄"""
        log_file = Path("logs/simulation_trades.jsonl")
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, "a") as f:
            f.write(json.dumps(trade) + "\n")
            
    def get_dashboard_data(self) -> dict:
        """獲取 Dashboard 數據"""
        return {
            "timestamp": datetime.now().isoformat(),
            "account": self.account,
            "positions": self.positions,
            "trades": self.trades[-10:],  # Last 10 trades
            "trade_count": len(self.trades),
            "status": "running"
        }
        
    def stop(self):
        """停止橋接"""
        self.running = False
        logger.info("Bridge stopped")


async def main():
    """主函數"""
    bridge = SimulationBridge(symbols=["TQQQ", "SQQQ"])
    
    try:
        await bridge.start()
    except KeyboardInterrupt:
        bridge.stop()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
