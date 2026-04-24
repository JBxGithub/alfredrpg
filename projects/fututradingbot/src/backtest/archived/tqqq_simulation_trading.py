"""
TQQQ 單邊多空策略模擬交易
TQQQ Long/Short Strategy Simulation Trading

連接Realtime Bridge進行模擬交易測試
"""

import sys
import time
import json
import asyncio
import websockets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

import pandas as pd
import numpy as np
import yfinance as yf

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


@dataclass
class Position:
    """持倉數據"""
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    shares: int
    entry_time: datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    def to_dict(self):
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'shares': self.shares,
            'entry_time': self.entry_time.isoformat(),
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_pct': self.unrealized_pnl_pct
        }


@dataclass
class TradeSignal:
    """交易信號"""
    timestamp: datetime
    signal_type: str  # 'buy', 'sell', 'close'
    symbol: str
    price: float
    reason: str
    confidence: float
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'signal_type': self.signal_type,
            'symbol': self.symbol,
            'price': self.price,
            'reason': self.reason,
            'confidence': self.confidence
        }


class TQQQStrategy:
    """TQQQ單邊多空策略"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = {
            'entry_zscore': 2.0,
            'exit_zscore': 0.5,
            'stop_loss_zscore': 3.5,
            'position_pct': 0.50,
            'lookback_period': 60,
            'rsi_period': 14,
            'rsi_overbought': 65.0,
            'rsi_oversold': 35.0,
            'volume_ma_period': 20,
            'take_profit_pct': 0.05,
            'stop_loss_pct': 0.03,
            'time_stop_days': 3
        }
        if config:
            self.config.update(config)
        
        self.price_history = pd.DataFrame()
        print(f"✅ TQQQ策略初始化完成")
        print(f"   進場Z-Score: ±{self.config['entry_zscore']}")
        print(f"   出場Z-Score: ±{self.config['exit_zscore']}")
        print(f"   倉位比例: {self.config['position_pct']*100}%")
    
    def update_price(self, timestamp, open_price, high, low, close, volume):
        """更新價格數據"""
        new_row = pd.DataFrame([{
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }])
        
        if self.price_history.empty:
            self.price_history = new_row
        else:
            self.price_history = pd.concat([self.price_history, new_row], ignore_index=True)
        
        # 保持數據在合理範圍內
        if len(self.price_history) > 500:
            self.price_history = self.price_history.tail(300)
        
        self.price_history['timestamp'] = pd.to_datetime(self.price_history['timestamp'])
        self.price_history = self.price_history.set_index('timestamp')
    
    def calculate_indicators(self) -> pd.DataFrame:
        """計算技術指標"""
        df = self.price_history.copy()
        
        # 計算Z-Score
        df['price_ma'] = df['close'].rolling(window=self.config['lookback_period']).mean()
        df['price_std'] = df['close'].rolling(window=self.config['lookback_period']).std()
        df['zscore'] = (df['close'] - df['price_ma']) / df['price_std']
        
        # 計算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config['rsi_period']).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 計算成交量均線
        df['volume_ma'] = df['volume'].rolling(window=self.config['volume_ma_period']).mean()
        
        return df
    
    def check_market_state(self) -> str:
        """檢查市場狀態"""
        if len(self.price_history) < 200:
            return 'sideways'
        
        current_price = self.price_history['close'].iloc[-1]
        ma200 = self.price_history['close'].rolling(window=200).mean().iloc[-1]
        
        if current_price > ma200 * 1.05:
            return 'bull'
        elif current_price < ma200 * 0.95:
            return 'bear'
        else:
            return 'sideways'
    
    def generate_signal(self) -> Optional[TradeSignal]:
        """生成交易信號"""
        if len(self.price_history) < self.config['lookback_period'] + 20:
            return None
        
        df = self.calculate_indicators()
        current = df.iloc[-1]
        
        if pd.isna(current['zscore']) or pd.isna(current['rsi']):
            return None
        
        market_state = self.check_market_state()
        zscore = current['zscore']
        rsi = current['rsi']
        volume = current['volume']
        volume_ma = current['volume_ma']
        current_price = current['close']
        timestamp = df.index[-1]
        
        # 做多條件
        if zscore < -self.config['entry_zscore']:
            if rsi < self.config['rsi_oversold']:
                if volume > volume_ma * 0.8:
                    if market_state in ['bull', 'sideways']:
                        return TradeSignal(
                            timestamp=timestamp,
                            signal_type='buy',
                            symbol='TQQQ',
                            price=current_price,
                            reason=f"Z-Score({zscore:.2f})超賣+RSI({rsi:.1f})低+{market_state}市",
                            confidence=min(abs(zscore) / 3, 0.95)
                        )
        
        # 做空條件
        if zscore > self.config['entry_zscore']:
            if rsi > self.config['rsi_overbought']:
                if volume > volume_ma * 0.8:
                    if market_state in ['bear', 'sideways']:
                        return TradeSignal(
                            timestamp=timestamp,
                            signal_type='sell',
                            symbol='TQQQ',
                            price=current_price,
                            reason=f"Z-Score({zscore:.2f})超買+RSI({rsi:.1f})高+{market_state}市",
                            confidence=min(abs(zscore) / 3, 0.95)
                        )
        
        return None
    
    def check_exit(self, position: Position) -> tuple[bool, str]:
        """檢查是否應該平倉"""
        if len(self.price_history) < self.config['lookback_period']:
            return False, ""
        
        df = self.calculate_indicators()
        current = df.iloc[-1]
        
        entry_price = position.entry_price
        current_price = current['close']
        direction = position.direction
        
        # 計算盈虧
        if direction == 'long':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        zscore = current['zscore']
        
        # 止盈檢查
        if pnl_pct >= self.config['take_profit_pct']:
            return True, f"止盈({pnl_pct*100:.2f}%)"
        
        # 止損檢查
        if pnl_pct <= -self.config['stop_loss_pct']:
            return True, f"止損({pnl_pct*100:.2f}%)"
        
        # Z-Score止損
        if direction == 'long' and zscore > self.config['stop_loss_zscore']:
            return True, f"Z-Score止損({zscore:.2f})"
        if direction == 'short' and zscore < -self.config['stop_loss_zscore']:
            return True, f"Z-Score止損({zscore:.2f})"
        
        # Z-Score回歸止盈
        if abs(zscore) < self.config['exit_zscore']:
            return True, f"Z-Score回歸({zscore:.2f})"
        
        # 時間止損
        days_held = (datetime.now() - position.entry_time).days
        if days_held >= self.config['time_stop_days']:
            return True, f"時間止損({days_held}天)"
        
        return False, ""
    
    def get_position_size(self, capital: float, current_price: float) -> int:
        """計算倉位大小"""
        position_value = capital * self.config['position_pct']
        shares = int(position_value / current_price)
        return max(shares, 1)


class TQQQSimulationTrader:
    """TQQQ模擬交易器"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position: Optional[Position] = None
        self.trades: list = []
        self.signals: list = []
        self.equity_history: list = []
        
        self.strategy = TQQQStrategy()
        self.websocket = None
        self.running = False
        
        # 統計
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'max_drawdown': 0.0,
            'peak_equity': initial_capital
        }
        
        print(f"\n{'='*70}")
        print("TQQQ 單邊多空策略模擬交易系統")
        print(f"{'='*70}")
        print(f"初始資金: ${initial_capital:,.2f}")
        print(f"Realtime Bridge: ws://127.0.0.1:8765")
        print(f"{'='*70}\n")
    
    async def connect(self):
        """連接Realtime Bridge"""
        uri = "ws://127.0.0.1:8765"
        print(f"🔗 正在連接 Realtime Bridge ({uri})...")
        
        try:
            self.websocket = await websockets.connect(uri)
            print("✅ 已連接 Realtime Bridge")
            return True
        except Exception as e:
            print(f"❌ 連接失敗: {e}")
            print("⚠️  將使用Yahoo Finance模擬數據模式")
            return False
    
    async def run_simulation(self):
        """運行模擬交易"""
        connected = await self.connect()
        
        if connected:
            await self.run_websocket_mode()
        else:
            await self.run_mock_mode()
    
    async def run_websocket_mode(self):
        """WebSocket模式 - 從Realtime Bridge接收數據"""
        print("\n📡 WebSocket模式啟動")
        print("等待實時數據...\n")
        
        self.running = True
        
        try:
            async for message in self.websocket:
                if not self.running:
                    break
                
                try:
                    data = json.loads(message)
                    await self.process_market_data(data)
                except json.JSONDecodeError:
                    print(f"無效的消息格式: {message}")
                
                await asyncio.sleep(0.1)
                
        except websockets.exceptions.ConnectionClosed:
            print("\n⚠️  WebSocket連接已關閉")
            print("切換到模擬數據模式...")
            await self.run_mock_mode()
    
    async def run_mock_mode(self):
        """模擬數據模式 - 從Yahoo Finance獲取數據"""
        print("\n📊 模擬數據模式啟動")
        print("從Yahoo Finance獲取TQQQ數據...\n")
        
        # 獲取歷史數據
        ticker = yf.Ticker("TQQQ")
        hist = ticker.history(period="5d", interval="1m")
        
        if hist.empty:
            print("❌ 無法獲取數據")
            return
        
        print(f"✅ 獲取到 {len(hist)} 條歷史數據")
        print(f"   期間: {hist.index[0]} ~ {hist.index[-1]}\n")
        
        # 模擬實時數據流
        for idx, (timestamp, row) in enumerate(hist.iterrows()):
            data = {
                'symbol': 'TQQQ',
                'timestamp': timestamp.isoformat(),
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': int(row['Volume'])
            }
            
            await self.process_market_data(data)
            
            # 模擬實時延遲
            await asyncio.sleep(0.05)
            
            # 每100條數據打印一次狀態
            if idx % 100 == 0 and idx > 0:
                self.print_status()
        
        # 最終報告
        self.print_final_report()
    
    async def process_market_data(self, data: Dict[str, Any]):
        """處理市場數據"""
        symbol = data.get('symbol', 'TQQQ')
        timestamp = data.get('timestamp')
        open_price = data.get('open', 0)
        high = data.get('high', 0)
        low = data.get('low', 0)
        close = data.get('close', 0)
        volume = data.get('volume', 0)
        
        # 更新策略數據
        self.strategy.update_price(timestamp, open_price, high, low, close, volume)
        
        # 檢查平倉條件
        if self.position:
            should_exit, exit_reason = self.strategy.check_exit(self.position)
            
            if should_exit:
                await self.close_position(close, exit_reason)
        
        # 檢查開倉條件
        if not self.position:
            signal = self.strategy.generate_signal()
            
            if signal:
                await self.open_position(signal)
                self.signals.append(signal)
        
        # 更新持倉盈虧
        if self.position:
            self.update_position_pnl(close)
        
        # 記錄權益
        self.record_equity()
    
    async def open_position(self, signal: TradeSignal):
        """開倉"""
        direction = 'long' if signal.signal_type == 'buy' else 'short'
        shares = self.strategy.get_position_size(self.cash, signal.price)
        
        if shares <= 0:
            return
        
        # 計算成本
        trade_value = signal.price * shares
        commission = trade_value * 0.001  # 0.1% 佣金
        total_cost = trade_value + commission
        
        if total_cost > self.cash:
            return
        
        # 扣除現金
        self.cash -= total_cost
        
        # 創建持倉
        self.position = Position(
            symbol=signal.symbol,
            direction=direction,
            entry_price=signal.price,
            shares=shares,
            entry_time=datetime.now(),
            current_price=signal.price
        )
        
        emoji = "📈" if direction == 'long' else "📉"
        print(f"{emoji} 開倉 [{direction.upper()}] {signal.timestamp}")
        print(f"   價格: ${signal.price:.2f} | 股數: {shares}")
        print(f"   原因: {signal.reason}")
        print(f"   信心度: {signal.confidence:.2%}")
        print()
    
    async def close_position(self, current_price: float, reason: str):
        """平倉"""
        if not self.position:
            return
        
        position = self.position
        
        # 計算盈虧
        if position.direction == 'long':
            pnl = (current_price - position.entry_price) * position.shares
            pnl_pct = (current_price - position.entry_price) / position.entry_price
        else:  # short
            pnl = (position.entry_price - current_price) * position.shares
            pnl_pct = (position.entry_price - current_price) / position.entry_price
        
        # 扣除佣金
        commission = current_price * position.shares * 0.001
        pnl -= commission
        
        # 回收資金
        trade_value = current_price * position.shares
        self.cash += trade_value - commission
        
        # 記錄交易
        trade = {
            'entry_time': position.entry_time.isoformat(),
            'exit_time': datetime.now().isoformat(),
            'direction': position.direction,
            'entry_price': position.entry_price,
            'exit_price': current_price,
            'shares': position.shares,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': reason
        }
        self.trades.append(trade)
        
        # 更新統計
        self.stats['total_trades'] += 1
        self.stats['total_pnl'] += pnl
        if pnl > 0:
            self.stats['winning_trades'] += 1
        else:
            self.stats['losing_trades'] += 1
        
        emoji = "✅" if pnl > 0 else "❌"
        print(f"{emoji} 平倉 [{position.direction.upper()}] {datetime.now().isoformat()}")
        print(f"   出場價: ${current_price:.2f}")
        print(f"   盈虧: ${pnl:,.2f} ({pnl_pct*100:+.2f}%)")
        print(f"   原因: {reason}")
        print()
        
        # 清空持倉
        self.position = None
    
    def update_position_pnl(self, current_price: float):
        """更新持倉盈虧"""
        if not self.position:
            return
        
        position = self.position
        position.current_price = current_price
        
        if position.direction == 'long':
            position.unrealized_pnl = (current_price - position.entry_price) * position.shares
            position.unrealized_pnl_pct = (current_price - position.entry_price) / position.entry_price
        else:
            position.unrealized_pnl = (position.entry_price - current_price) * position.shares
            position.unrealized_pnl_pct = (position.entry_price - current_price) / position.entry_price
    
    def record_equity(self):
        """記錄權益"""
        position_value = 0
        if self.position:
            position_value = self.position.current_price * self.position.shares
        
        total_equity = self.cash + position_value
        
        # 更新最大回撤
        if total_equity > self.stats['peak_equity']:
            self.stats['peak_equity'] = total_equity
        
        drawdown = (self.stats['peak_equity'] - total_equity) / self.stats['peak_equity']
        if drawdown > self.stats['max_drawdown']:
            self.stats['max_drawdown'] = drawdown
        
        self.equity_history.append({
            'timestamp': datetime.now().isoformat(),
            'cash': self.cash,
            'position_value': position_value,
            'total_equity': total_equity
        })
    
    def print_status(self):
        """打印當前狀態"""
        print(f"\n{'='*70}")
        print(f"當前狀態 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        print(f"現金: ${self.cash:,.2f}")
        
        if self.position:
            pos = self.position
            print(f"\n持倉:")
            print(f"  方向: {pos.direction.upper()}")
            print(f"  進場價: ${pos.entry_price:.2f}")
            print(f"  當前價: ${pos.current_price:.2f}")
            print(f"  股數: {pos.shares}")
            print(f"  未實現盈虧: ${pos.unrealized_pnl:,.2f} ({pos.unrealized_pnl_pct*100:+.2f}%)")
        else:
            print(f"\n持倉: 無")
        
        total_equity = self.cash + (self.position.current_price * self.position.shares if self.position else 0)
        pnl_pct = (total_equity - self.initial_capital) / self.initial_capital * 100
        print(f"\n總權益: ${total_equity:,.2f} ({pnl_pct:+.2f}%)")
        print(f"交易次數: {self.stats['total_trades']}")
        print(f"{'='*70}\n")
    
    def print_final_report(self):
        """打印最終報告"""
        print(f"\n{'='*70}")
        print("模擬交易最終報告")
        print(f"{'='*70}")
        
        total_equity = self.cash + (self.position.current_price * self.position.shares if self.position else 0)
        total_return = total_equity - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100
        
        print(f"\n資金統計:")
        print(f"  初始資金: ${self.initial_capital:,.2f}")
        print(f"  最終資金: ${total_equity:,.2f}")
        print(f"  總回報: ${total_return:,.2f} ({total_return_pct:+.2f}%)")
        
        print(f"\n交易統計:")
        print(f"  總交易次數: {self.stats['total_trades']}")
        if self.stats['total_trades'] > 0:
            win_rate = (self.stats['winning_trades'] / self.stats['total_trades']) * 100
            print(f"  勝率: {win_rate:.2f}%")
            print(f"  盈利交易: {self.stats['winning_trades']}")
            print(f"  虧損交易: {self.stats['losing_trades']}")
        print(f"  最大回撤: {self.stats['max_drawdown']*100:.2f}%")
        
        if self.trades:
            print(f"\n逐筆交易記錄:")
            for i, trade in enumerate(self.trades, 1):
                emoji = "✅" if trade['pnl'] > 0 else "❌"
                print(f"  {emoji} #{i}: {trade['direction'].upper()} ${trade['pnl']:,.2f} ({trade['pnl_pct']*100:+.2f}%) - {trade['exit_reason']}")
        
        print(f"\n{'='*70}")
        
        # 保存結果
        self.save_results()
    
    def save_results(self):
        """保存結果到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = Path('C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot/reports')
        report_dir.mkdir(exist_ok=True)
        
        result = {
            'timestamp': timestamp,
            'initial_capital': self.initial_capital,
            'final_equity': self.cash + (self.position.current_price * self.position.shares if self.position else 0),
            'stats': self.stats,
            'trades': self.trades,
            'signals': [s.to_dict() for s in self.signals],
            'equity_history': self.equity_history[-100:]  # 最後100條
        }
        
        # 保存JSON
        json_file = report_dir / f'simulation_result_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n📄 結果已保存: {json_file}")


async def main():
    """主函數"""
    trader = TQQQSimulationTrader(initial_capital=100000.0)
    
    try:
        await trader.run_simulation()
    except KeyboardInterrupt:
        print("\n\n⚠️  用戶中斷")
        trader.print_final_report()


if __name__ == '__main__':
    asyncio.run(main())
