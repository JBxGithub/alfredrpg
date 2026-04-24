"""
Survival Trader - 實盤交易系統 (生死存亡模式)
帳戶: 6896 (REAL環境)
每日盈利目標: $50+
每日最大虧損: $100
交易時間: 週一至五 21:30-04:00

這是最高優先級任務，持續運作直到手動停止。
"""

import asyncio
import json
import os
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

# Setup paths
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_DIR / 'logs' / 'survival_trader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SurvivalTrader")

# Import Futu API
try:
    from src.api.futu_client import FutuAPIClient, FutuTradeClient, Market, TrdEnv, TrdSide, OrderType
    import futu as ft
    FUTU_AVAILABLE = True
except ImportError as e:
    logger.error(f"Futu API not available: {e}")
    FUTU_AVAILABLE = False

# Account Configuration
ACCOUNT_ID = 281756477706540632  # 6896 account
TRADE_PASSWORD = "011087"  # Trading password

# Trading Parameters
DAILY_PROFIT_TARGET = 50.0  # $50 daily profit target
DAILY_MAX_LOSS = 100.0  # $100 daily max loss
TRADING_START_TIME = time(21, 30)  # 21:30
TRADING_END_TIME = time(4, 0)  # 04:00

# Strategy Parameters (Z-Score Mean Reversion)
CONFIG = {
    'symbol': 'TQQQ',
    'futu_code': 'US.TQQQ',
    'entry_zscore': 1.65,
    'exit_zscore': 0.5,
    'stop_loss_zscore': 3.5,
    'position_pct': 0.50,  # 50% of available cash
    'lookback_period': 60,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    'take_profit_pct': 0.05,  # 5%
    'stop_loss_pct': 0.03,  # 3%
    'time_stop_days': 7,
}


@dataclass
class AccountStatus:
    """帳戶狀態"""
    total_assets: float = 0.0
    available_cash: float = 0.0
    daily_pnl: float = 0.0
    daily_pnl_pct: float = 0.0
    unrealized_pnl: float = 0.0
    timestamp: str = ""
    
    def to_dict(self):
        return {
            'total_assets': round(self.total_assets, 2),
            'available_cash': round(self.available_cash, 2),
            'daily_pnl': round(self.daily_pnl, 2),
            'daily_pnl_pct': round(self.daily_pnl_pct, 2),
            'unrealized_pnl': round(self.unrealized_pnl, 2),
            'timestamp': self.timestamp
        }


@dataclass
class Position:
    """持倉信息"""
    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    direction: str = "long"  # 'long' or 'short'
    entry_time: str = ""


class SurvivalTrader:
    """生存交易器 - 實盤交易系統"""
    
    def __init__(self):
        self.running = False
        self.quote_client: Optional[FutuAPIClient] = None
        self.trade_client: Optional[FutuTradeClient] = None
        self.account_unlocked = False
        
        # Data storage
        self.account = AccountStatus()
        self.positions: Dict[str, Position] = {}
        self.price_history: List[dict] = []
        self.trades_today: List[dict] = []
        
        # Indicators
        self.current_zscore = 0.0
        self.current_rsi = 50.0
        self.current_price = 0.0
        
        # Status tracking
        self.last_status_report = datetime.now()
        self.status_report_interval = 300  # 5 minutes
        
        logger.info("=" * 60)
        logger.info("🚀 SURVIVAL TRADER INITIALIZED")
        logger.info(f"Account: {ACCOUNT_ID} (REAL)")
        logger.info(f"Daily Profit Target: ${DAILY_PROFIT_TARGET}")
        logger.info(f"Daily Max Loss: ${DAILY_MAX_LOSS}")
        logger.info("=" * 60)
    
    async def start(self):
        """啟動交易系統"""
        logger.info("\n🔥 STARTING SURVIVAL TRADER - THIS IS A LIVE SYSTEM 🔥\n")
        
        if not FUTU_AVAILABLE:
            logger.error("❌ Futu API not available. Cannot start trading.")
            return
        
        self.running = True
        
        # Connect to Futu
        await self.connect_futu()
        
        # Main trading loop
        await self.trading_loop()
    
    async def connect_futu(self):
        """連接富途API"""
        try:
            # Connect quote client
            self.quote_client = FutuAPIClient(host="127.0.0.1", port=11111)
            if self.quote_client.connect_quote():
                logger.info("✅ Connected to Futu OpenD (Quote)")
                
                # Subscribe to TQQQ
                quote = self.quote_client.get_quote_client()
                if quote:
                    ret, data = quote.subscribe([CONFIG['futu_code']], [ft.SubType.QUOTE])
                    if ret == 0:
                        logger.info(f"✅ Subscribed to {CONFIG['symbol']}")
                    else:
                        logger.warning(f"⚠️ Subscribe warning: {data}")
            else:
                logger.error("❌ Failed to connect to Futu OpenD")
                return
            
            # Connect trade client
            self.trade_client = FutuTradeClient(
                host="127.0.0.1",
                port=11111,
                market=Market.US
            )
            
            if self.trade_client.connect():
                logger.info("✅ Connected to Futu OpenD (Trade)")
                
                # Unlock trade
                if self.trade_client.unlock_trade(TRADE_PASSWORD):
                    logger.info("✅ Trade interface unlocked")
                    self.account_unlocked = True
                else:
                    logger.warning("⚠️ Failed to unlock trade interface")
            else:
                logger.error("❌ Failed to connect trade client")
                
        except Exception as e:
            logger.error(f"❌ Connection error: {e}")
    
    async def trading_loop(self):
        """主交易循環"""
        logger.info("\n📊 Entering trading loop...")
        
        iteration = 0
        while self.running:
            try:
                iteration += 1
                now = datetime.now()
                
                # Check if in trading hours (21:30 - 04:00 next day)
                current_time = now.time()
                is_trading_hours = (
                    (current_time >= TRADING_START_TIME) or 
                    (current_time <= TRADING_END_TIME)
                )
                
                if not is_trading_hours:
                    logger.info(f"⏰ Outside trading hours ({current_time}). Waiting...")
                    await asyncio.sleep(60)
                    continue
                
                # Update account status
                await self.update_account_status()
                
                # Fetch market data
                await self.fetch_market_data()
                
                # Calculate indicators
                self.calculate_indicators()
                
                # Check risk limits
                if await self.check_risk_limits():
                    logger.warning("🛑 Risk limit reached! Stopping trading.")
                    break
                
                # Generate and execute signals
                signal = self.generate_signal()
                if signal and signal['action'] != 'HOLD':
                    await self.execute_trade(signal)
                
                # Report status every 5 minutes
                if (now - self.last_status_report).seconds >= self.status_report_interval:
                    await self.report_status()
                    self.last_status_report = now
                
                # Sleep before next iteration
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"❌ Trading loop error: {e}")
                await asyncio.sleep(30)
    
    async def update_account_status(self):
        """更新帳戶狀態"""
        if not self.trade_client:
            return
        
        try:
            # Query account info
            ret_code, acc_data = self.trade_client.accinfo_query(
                trd_env=TrdEnv.REAL,
                acc_id=ACCOUNT_ID
            )
            
            if ret_code == 0 and acc_data is not None and len(acc_data) > 0:
                # Handle DataFrame
                if hasattr(acc_data, 'to_dict'):
                    account_list = acc_data.to_dict('records')
                    if len(account_list) > 0:
                        data = account_list[0]
                elif isinstance(acc_data, list) and len(acc_data) > 0:
                    data = acc_data[0]
                elif isinstance(acc_data, dict):
                    data = acc_data
                else:
                    data = {}
                
                if isinstance(data, dict):
                    self.account.total_assets = float(data.get('total_assets', 0) or data.get('totalAsset', 0) or 0)
                    self.account.available_cash = float(data.get('available_cash', 0) or data.get('availableCash', 0) or data.get('cash', 0) or 0)
                    self.account.daily_pnl = float(data.get('daily_pnl', 0) or data.get('pl', 0) or 0)
                    self.account.timestamp = datetime.now().isoformat()
                    
                    if self.account.total_assets > 0:
                        self.account.daily_pnl_pct = (self.account.daily_pnl / self.account.total_assets) * 100
            
            # Query positions
            ret_code, pos_data = self.trade_client.position_list_query(
                trd_env=TrdEnv.REAL,
                acc_id=ACCOUNT_ID
            )
            
            if ret_code == 0 and pos_data is not None and len(pos_data) > 0:
                self.positions = {}
                
                if hasattr(pos_data, 'to_dict'):
                    positions_list = pos_data.to_dict('records')
                elif isinstance(pos_data, list):
                    positions_list = pos_data
                else:
                    positions_list = []
                
                total_unrealized = 0.0
                for pos in positions_list:
                    if isinstance(pos, dict):
                        symbol = pos.get('code', '').replace('US.', '')
                        if symbol:
                            qty = int(pos.get('qty', 0))
                            current_price = float(pos.get('nominal_price', 0))
                            unrealized = float(pos.get('pl_val', 0))
                            total_unrealized += unrealized
                            
                            self.positions[symbol] = Position(
                                symbol=symbol,
                                quantity=qty,
                                avg_cost=float(pos.get('cost_price', 0)),
                                current_price=current_price,
                                unrealized_pnl=unrealized,
                                direction='long' if pos.get('position_side') == 'LONG' else 'short',
                                entry_time=pos.get('create_time', '')
                            )
                
                self.account.unrealized_pnl = total_unrealized
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to update account: {e}")
    
    async def fetch_market_data(self):
        """獲取市場數據"""
        if not self.quote_client:
            return
        
        try:
            quote = self.quote_client.get_quote_client()
            if not quote:
                return
            
            ret, data = quote.get_stock_quote([CONFIG['futu_code']])
            
            if ret == 0 and data is not None and not data.empty:
                for _, row in data.iterrows():
                    price = float(row.get('last_price', 0))
                    volume = int(row.get('volume', 0))
                    high = float(row.get('high_price', 0))
                    low = float(row.get('low_price', 0))
                    open_price = float(row.get('open_price', 0))
                    
                    self.current_price = price
                    
                    # Add to history
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
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch market data: {e}")
    
    def calculate_indicators(self):
        """計算技術指標"""
        if len(self.price_history) < CONFIG['lookback_period']:
            return
        
        try:
            import numpy as np
            
            prices = [p['close'] for p in self.price_history]
            lookback = CONFIG['lookback_period']
            
            # Calculate Z-Score
            if len(prices) >= lookback:
                recent_prices = prices[-lookback:]
                mean_price = np.mean(recent_prices[:-1])
                std_price = np.std(recent_prices[:-1])
                current_price = prices[-1]
                
                if std_price > 0:
                    self.current_zscore = (current_price - mean_price) / std_price
            
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
                    
        except Exception as e:
            logger.warning(f"⚠️ Indicator calculation error: {e}")
    
    async def check_risk_limits(self) -> bool:
        """檢查風險限制，返回True如果達到限制"""
        # Check daily loss limit
        if self.account.daily_pnl <= -DAILY_MAX_LOSS:
            logger.error(f"🛑 DAILY LOSS LIMIT REACHED: ${self.account.daily_pnl:.2f}")
            return True
        
        # Check daily profit target (optional - can continue trading)
        if self.account.daily_pnl >= DAILY_PROFIT_TARGET:
            logger.info(f"🎯 DAILY PROFIT TARGET REACHED: ${self.account.daily_pnl:.2f}")
            # Don't stop, just log
        
        return False
    
    def generate_signal(self) -> Optional[dict]:
        """生成交易信號"""
        if len(self.price_history) < CONFIG['lookback_period']:
            return None
        
        symbol = CONFIG['symbol']
        zscore = self.current_zscore
        rsi = self.current_rsi
        
        # Check if we have position
        has_position = symbol in self.positions and self.positions[symbol].quantity > 0
        
        # Entry signals
        if not has_position:
            # Long entry
            if zscore < -CONFIG['entry_zscore'] and rsi < CONFIG['rsi_oversold']:
                return {
                    'action': 'BUY',
                    'symbol': symbol,
                    'reason': f'Z-Score({zscore:.2f}) oversold + RSI({rsi:.1f}) low',
                    'zscore': zscore,
                    'rsi': rsi
                }
            
            # Short entry
            if zscore > CONFIG['entry_zscore'] and rsi > CONFIG['rsi_overbought']:
                return {
                    'action': 'SELL',
                    'symbol': symbol,
                    'reason': f'Z-Score({zscore:.2f}) overbought + RSI({rsi:.1f}) high',
                    'zscore': zscore,
                    'rsi': rsi
                }
        
        # Exit signals
        if has_position:
            position = self.positions[symbol]
            entry_price = position.avg_cost
            current_price = self.current_price
            
            # Calculate P&L
            if position.direction == 'long':
                pnl_pct = (current_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current_price) / entry_price
            
            # Take profit
            if pnl_pct >= CONFIG['take_profit_pct']:
                return {
                    'action': 'SELL' if position.direction == 'long' else 'BUY',
                    'symbol': symbol,
                    'reason': f'Take profit ({pnl_pct*100:.2f}%)',
                    'zscore': zscore,
                    'rsi': rsi
                }
            
            # Stop loss
            if pnl_pct <= -CONFIG['stop_loss_pct']:
                return {
                    'action': 'SELL' if position.direction == 'long' else 'BUY',
                    'symbol': symbol,
                    'reason': f'Stop loss ({pnl_pct*100:.2f}%)',
                    'zscore': zscore,
                    'rsi': rsi
                }
            
            # Z-Score exit
            if abs(zscore) < CONFIG['exit_zscore']:
                return {
                    'action': 'SELL' if position.direction == 'long' else 'BUY',
                    'symbol': symbol,
                    'reason': f'Z-Score reversion ({zscore:.2f})',
                    'zscore': zscore,
                    'rsi': rsi
                }
        
        return {'action': 'HOLD', 'symbol': symbol, 'reason': 'No signal', 'zscore': zscore, 'rsi': rsi}
    
    async def execute_trade(self, signal: dict):
        """執行交易"""
        if not self.trade_client or not self.account_unlocked:
            logger.warning("⚠️ Trade client not ready")
            return
        
        try:
            symbol = signal['symbol']
            action = signal['action']
            price = self.current_price
            
            if price <= 0:
                logger.warning(f"⚠️ Invalid price: {price}")
                return
            
            # Calculate quantity (50% of available cash)
            cash_to_use = self.account.available_cash * CONFIG['position_pct']
            quantity = int(cash_to_use / price)
            
            if quantity <= 0:
                logger.warning(f"⚠️ Insufficient cash. Available: ${self.account.available_cash:.2f}")
                return
            
            # Determine trade side
            if action == 'BUY':
                trd_side = TrdSide.BUY
            elif action == 'SELL':
                trd_side = TrdSide.SELL
            else:
                return
            
            # Place order
            logger.info(f"📝 PLACING ORDER: {action} {quantity} {symbol} @ ${price:.2f}")
            logger.info(f"   Reason: {signal['reason']}")
            
            ret_code, order_data = self.trade_client.place_order(
                price=price,
                qty=quantity,
                code=CONFIG['futu_code'],
                trd_side=trd_side,
                order_type=OrderType.NORMAL,
                trd_env=TrdEnv.REAL,
                acc_id=ACCOUNT_ID
            )
            
            if ret_code == 0:
                logger.info(f"✅ ORDER PLACED SUCCESSFULLY: {action} {quantity} {symbol}")
                
                # Record trade
                trade = {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'action': action,
                    'quantity': quantity,
                    'price': price,
                    'reason': signal['reason'],
                    'zscore': signal['zscore'],
                    'rsi': signal['rsi']
                }
                self.trades_today.append(trade)
                
                # Save trade to file
                self.save_trade(trade)
            else:
                logger.error(f"❌ ORDER FAILED: {order_data}")
                
        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
    
    def save_trade(self, trade: dict):
        """保存交易記錄"""
        try:
            trades_file = PROJECT_DIR / 'logs' / f'trades_{datetime.now().strftime("%Y%m%d")}.json'
            
            trades = []
            if trades_file.exists():
                with open(trades_file, 'r') as f:
                    trades = json.load(f)
            
            trades.append(trade)
            
            with open(trades_file, 'w') as f:
                json.dump(trades, f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to save trade: {e}")
    
    async def report_status(self):
        """報告狀態 (每5分鐘)"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 STATUS REPORT")
        logger.info("=" * 60)
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Account: {ACCOUNT_ID} (REAL)")
        logger.info("-" * 60)
        logger.info("💰 ACCOUNT:")
        logger.info(f"   Total Assets: ${self.account.total_assets:,.2f}")
        logger.info(f"   Available Cash: ${self.account.available_cash:,.2f}")
        logger.info(f"   Daily P&L: ${self.account.daily_pnl:+.2f} ({self.account.daily_pnl_pct:+.2f}%)")
        logger.info(f"   Unrealized P&L: ${self.account.unrealized_pnl:+.2f}")
        logger.info("-" * 60)
        logger.info("📈 MARKET:")
        logger.info(f"   Symbol: {CONFIG['symbol']}")
        logger.info(f"   Price: ${self.current_price:.2f}")
        logger.info(f"   Z-Score: {self.current_zscore:.2f}")
        logger.info(f"   RSI: {self.current_rsi:.1f}")
        logger.info("-" * 60)
        logger.info("📋 POSITIONS:")
        if self.positions:
            for symbol, pos in self.positions.items():
                logger.info(f"   {symbol}: {pos.quantity} @ ${pos.avg_cost:.2f} ({pos.direction})")
                logger.info(f"      Unrealized: ${pos.unrealized_pnl:+.2f}")
        else:
            logger.info("   No open positions")
        logger.info("-" * 60)
        logger.info(f"📝 Trades Today: {len(self.trades_today)}")
        logger.info("=" * 60 + "\n")
        
        # Also save status to file
        self.save_status()
    
    def save_status(self):
        """保存狀態到文件"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'account': self.account.to_dict(),
                'positions': {k: asdict(v) for k, v in self.positions.items()},
                'market': {
                    'symbol': CONFIG['symbol'],
                    'price': self.current_price,
                    'zscore': self.current_zscore,
                    'rsi': self.current_rsi
                },
                'trades_count': len(self.trades_today)
            }
            
            status_file = PROJECT_DIR / 'logs' / 'survival_status.json'
            with open(status_file, 'w') as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to save status: {e}")
    
    def stop(self):
        """停止交易系統"""
        logger.info("\n🛑 STOPPING SURVIVAL TRADER...")
        self.running = False
        
        if self.quote_client:
            self.quote_client.disconnect_all()
        
        if self.trade_client:
            # Close all positions before stopping
            logger.info("⚠️ Please manually close any open positions!")
        
        logger.info("✅ Survival Trader stopped")


async def main():
    """主函數"""
    trader = SurvivalTrader()
    
    try:
        await trader.start()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Keyboard interrupt received")
    finally:
        trader.stop()


if __name__ == "__main__":
    asyncio.run(main())
