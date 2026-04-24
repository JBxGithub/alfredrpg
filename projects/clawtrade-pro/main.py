"""
ClawTrade Pro - 通用股票交易系統主程序
"""

import os
import sys
import yaml
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# 添加技能路徑（已更新到 private skills）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'private skills', 'clawtrade-pro', 'trading-core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'private skills', 'clawtrade-pro', 'engine'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'private skills', 'clawtrade-pro', 'risk'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'private skills', 'clawtrade-pro', 'automation', 'heartbeat'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'private skills', 'clawtrade-pro', 'automation', 'cron_jobs'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'private skills', 'clawtrade-pro', 'strategies'))

from trading_core import FutuClient, DataSync
from engine import StrategyEngine, TradeSignal, SignalType
from risk_manager import RiskManager
from heartbeat import HeartbeatMonitor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClawTradePro:
    """ClawTrade Pro 主系統"""
    
    def __init__(self, config_path: str = "config/trading.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # 初始化組件
        self.futu = FutuClient()
        self.strategy_engine = StrategyEngine("config/strategies.yaml")
        self.risk_manager = RiskManager()
        self.data_sync = DataSync()
        self.heartbeat = HeartbeatMonitor()
        
        self.running = False
        self.positions = {}
        
    def _load_config(self) -> Dict:
        """加載配置"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def initialize(self) -> bool:
        """初始化系統"""
        logger.info("🚀 Initializing ClawTrade Pro...")
        
        # 1. 連接 Futu
        if not self.futu.connect():
            logger.error("❌ Failed to connect to Futu")
            return False
        logger.info("✅ Futu connected")
        
        # 2. 加載策略配置
        self.strategy_engine.load_config()
        symbols = self.strategy_engine.get_registered_symbols()
        logger.info(f"✅ Loaded {len(symbols)} strategies: {symbols}")
        
        # 3. 獲取初始持倉
        self._update_positions()
        
        logger.info("✅ ClawTrade Pro initialized successfully")
        return True
    
    def _update_positions(self):
        """更新持倉信息"""
        positions = self.futu.get_positions()
        if positions:
            self.positions = {p.symbol: p for p in positions}
            logger.info(f"📋 Current positions: {len(positions)}")
            for p in positions:
                logger.info(f"  {p.symbol}: {p.quantity} @ ${p.avg_price:.2f}")
    
    def process_signal(self, signal: TradeSignal) -> bool:
        """處理交易信號"""
        if signal.signal == SignalType.HOLD:
            return False
        
        symbol = signal.symbol
        logger.info(f"📡 Signal received: {signal.signal.value} {symbol} @ ${signal.price:.2f}")
        logger.info(f"   Reason: {signal.reason}")
        logger.info(f"   Confidence: {signal.confidence:.2%}")
        
        # 1. 風險檢查
        account = self.futu.get_account_info()
        if not account:
            logger.error("❌ Failed to get account info")
            return False
        
        # 構建訂單
        if signal.signal in [SignalType.BUY, SignalType.SELL]:
            # 計算倉位大小
            strategy = self.strategy_engine._strategies.get(symbol)
            if strategy and hasattr(strategy, 'calculate_position_size'):
                quantity = strategy.calculate_position_size(account.total_assets, signal.price)
            else:
                quantity = int((account.total_assets * 0.5) / signal.price)
            
            order = {
                'symbol': symbol,
                'side': 'BUY' if signal.signal == SignalType.BUY else 'SELL',
                'quantity': quantity,
                'price': signal.price
            }
            
            # 風險檢查
            current_positions = [
                {'symbol': p.symbol, 'market_value': p.market_value}
                for p in self.positions.values()
            ]
            
            risk_check = self.risk_manager.check_order(order, 
                                                       {'total_assets': account.total_assets, 'cash': account.cash},
                                                       current_positions)
            
            if not risk_check.passed:
                logger.warning(f"🚫 Risk check failed: {risk_check.message}")
                return False
            
            logger.info(f"✅ Risk check passed: {risk_check.message}")
            
            # 執行交易 (模擬模式)
            logger.info(f"📝 Would execute: {order['side']} {order['quantity']} {symbol} @ ${signal.price:.2f}")
            
            # 設置止損止盈
            if hasattr(strategy, 'stop_loss') and hasattr(strategy, 'take_profit'):
                self.risk_manager.set_stop_orders(
                    f"{symbol}_{datetime.now().timestamp()}",
                    symbol, signal.price, order['side']
                )
        
        elif signal.signal == SignalType.CLOSE:
            # 平倉
            if symbol in self.positions:
                pos = self.positions[symbol]
                side = 'SELL' if pos.quantity > 0 else 'BUY'
                logger.info(f"📝 Would close: {side} {abs(pos.quantity)} {symbol}")
        
        return True
    
    def scan_signals(self) -> List[TradeSignal]:
        """掃描所有股票的信號"""
        signals = []
        
        for symbol in self.strategy_engine.get_registered_symbols():
            try:
                # 獲取歷史數據
                import pandas as pd
                klines = self.futu.get_klines(symbol, period="DAY", count=100)
                
                if klines:
                    df = pd.DataFrame(klines)
                    df['symbol'] = symbol
                    
                    # 獲取當前持倉
                    current_position = None
                    if symbol in self.positions:
                        pos = self.positions[symbol]
                        current_position = {
                            'symbol': symbol,
                            'side': 'LONG' if pos.quantity > 0 else 'SHORT',
                            'entry_price': pos.avg_price,
                            'entry_time': datetime.now(),  # 應從數據庫獲取
                            'quantity': abs(pos.quantity)
                        }
                    
                    # 生成信號
                    signal = self.strategy_engine.generate_signal(symbol, df, current_position)
                    if signal and signal.signal != SignalType.HOLD:
                        signals.append(signal)
                        
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
        
        return signals
    
    def run_once(self):
        """運行一次掃描"""
        logger.info("🔍 Scanning for trading signals...")
        
        # 更新持倉
        self._update_positions()
        
        # 掃描信號
        signals = self.scan_signals()
        
        if signals:
            logger.info(f"🚨 Found {len(signals)} active signals")
            for signal in signals:
                self.process_signal(signal)
        else:
            logger.info("✅ No signals found")
        
        # 檢查持倉風險
        self._check_position_risks()
    
    def _check_position_risks(self):
        """檢查持倉風險"""
        if not self.positions:
            return
        
        from risk_manager import Position
        
        pos_objects = []
        for p in self.positions.values():
            pos_objects.append(Position(
                symbol=p.symbol,
                side='LONG' if p.quantity > 0 else 'SHORT',
                quantity=abs(p.quantity),
                entry_price=p.avg_price,
                current_price=p.market_price,
                market_value=p.market_value,
                unrealized_pnl=p.unrealized_pnl,
                pnl_pct=p.pnl_pct,
                entry_time=datetime.now()
            ))
        
        alerts = self.risk_manager.check_positions(pos_objects)
        for alert in alerts:
            logger.warning(f"🚨 RISK ALERT: {alert.message}")
    
    def run(self, interval: int = 60):
        """持續運行"""
        import time
        
        self.running = True
        logger.info(f"🔄 Starting ClawTrade Pro (interval: {interval}s)")
        
        try:
            while self.running:
                self.run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("🛑 Stopping ClawTrade Pro...")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """關閉系統"""
        self.running = False
        self.futu.disconnect()
        logger.info("✅ ClawTrade Pro shutdown complete")
    
    def get_status(self) -> Dict:
        """獲取系統狀態"""
        account = self.futu.get_account_info()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'connected': self.futu.is_connected(),
            'account': {
                'total_assets': account.total_assets if account else 0,
                'cash': account.cash if account else 0,
                'market_value': account.market_value if account else 0
            },
            'positions': len(self.positions),
            'strategies': len(self.strategy_engine.get_registered_symbols())
        }


def main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(description='ClawTrade Pro')
    parser.add_argument('--action', choices=['run', 'scan', 'status', 'test'],
                       default='run', help='Action to perform')
    parser.add_argument('--interval', type=int, default=60,
                       help='Scan interval in seconds')
    parser.add_argument('--symbol', help='Test specific symbol')
    
    args = parser.parse_args()
    
    system = ClawTradePro()
    
    if args.action == 'run':
        if system.initialize():
            system.run(args.interval)
    
    elif args.action == 'scan':
        if system.initialize():
            system.run_once()
            system.shutdown()
    
    elif args.action == 'status':
        if system.initialize():
            status = system.get_status()
            print("\n📊 System Status:")
            print(f"  Connected: {status['connected']}")
            print(f"  Total Assets: ${status['account']['total_assets']:,.2f}")
            print(f"  Cash: ${status['account']['cash']:,.2f}")
            print(f"  Positions: {status['positions']}")
            print(f"  Strategies: {status['strategies']}")
            system.shutdown()
    
    elif args.action == 'test':
        if not args.symbol:
            print("Please specify --symbol")
            return
        
        if system.initialize():
            # 測試特定股票
            import pandas as pd
            klines = system.futu.get_klines(args.symbol, count=100)
            if klines:
                df = pd.DataFrame(klines)
                signal = system.strategy_engine.generate_signal(args.symbol, df)
                if signal:
                    print(f"\n📡 Signal for {args.symbol}:")
                    print(f"  Action: {signal.signal.value}")
                    print(f"  Price: ${signal.price:.2f}")
                    print(f"  Confidence: {signal.confidence:.2%}")
                    print(f"  Reason: {signal.reason}")
                    print(f"  Params: {signal.params}")
            system.shutdown()


if __name__ == "__main__":
    main()
