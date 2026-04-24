"""
TQQQ 2024年度回測腳本（放寬版）
回測期間: 2024-01-01 至 2024-12-31
策略參數（放寬版）

## 策略參數（放寬版）
- entry_zscore: 1.5
- exit_zscore: 0.5
- position_pct: 0.50
- take_profit_pct: 0.05
- stop_loss_pct: 0.03
- time_stop_days: 3
- rsi_overbought: 65.0
- rsi_oversold: 35.0

## 進場條件
- 做多: Z-Score < -1.5 + MACD金叉 + RSI < 35
- 做空: Z-Score > 1.5 + MACD死叉 + RSI > 65
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import yfinance as yf
import warnings
import sys
import os

# 添加項目路徑
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot')

warnings.filterwarnings('ignore')


@dataclass
class TQQQStrategyConfig:
    """TQQQ策略配置 - 放寬版"""
    entry_zscore: float = 1.5
    exit_zscore: float = 0.5
    stop_loss_zscore: float = 3.5
    position_pct: float = 0.50
    max_positions: int = 2
    lookback_period: int = 60
    rsi_period: int = 14
    rsi_overbought: float = 65.0  # 放寬版: 65
    rsi_oversold: float = 35.0    # 放寬版: 35
    volume_ma_period: int = 20
    take_profit_pct: float = 0.05
    stop_loss_pct: float = 0.03
    time_stop_days: int = 3
    require_market_state: bool = True


class TQQQBacktestStrategy:
    """TQQQ回測專用策略 - 放寬版（含MACD條件）"""
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'entry_zscore': 1.5,
            'exit_zscore': 0.5,
            'stop_loss_zscore': 3.5,
            'position_pct': 0.50,
            'max_positions': 2,
            'lookback_period': 60,
            'rsi_period': 14,
            'rsi_overbought': 65.0,  # 放寬版
            'rsi_oversold': 35.0,    # 放寬版
            'volume_ma_period': 20,
            'take_profit_pct': 0.05,
            'stop_loss_pct': 0.03,
            'time_stop_days': 3,
            'require_market_state': True
        }
        
        if config:
            default_config.update(config)
        
        self.config = TQQQStrategyConfig(**default_config)
        self.current_positions = []
        
        print(f"🎯 TQQQ策略初始化（放寬版）")
        print(f"   倉位: {self.config.position_pct*100}%")
        print(f"   Z-Score進場: ±{self.config.entry_zscore}")
        print(f"   Z-Score出場: ±{self.config.exit_zscore}")
        print(f"   RSI超買/超賣: {self.config.rsi_overbought}/{self.config.rsi_oversold}")
        print(f"   止盈/止損: {self.config.take_profit_pct*100}%/{self.config.stop_loss_pct*100}%")
        print(f"   時間止損: {self.config.time_stop_days}天")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
        df = data.copy()
        
        # 計算Z-Score
        df['price_ma'] = df['close'].rolling(window=self.config.lookback_period).mean()
        df['price_std'] = df['close'].rolling(window=self.config.lookback_period).std()
        df['zscore'] = (df['close'] - df['price_ma']) / df['price_std']
        
        # 計算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.config.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.config.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 計算成交量均線
        df['volume_ma'] = df['volume'].rolling(window=self.config.volume_ma_period).mean()
        
        # 計算MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def check_market_state(self, data: pd.DataFrame) -> str:
        """檢查市場狀態"""
        if len(data) < 200:
            return 'sideways'
        
        current_price = data['close'].iloc[-1]
        ma200 = data['close'].rolling(window=200).mean().iloc[-1]
        
        if current_price > ma200 * 1.05:
            return 'bull'
        elif current_price < ma200 * 0.95:
            return 'bear'
        else:
            return 'sideways'
    
    def generate_signal(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        生成交易信號（放寬版）
        
        進場條件:
        - 做多: Z-Score < -1.5 + MACD金叉 + RSI < 35
        - 做空: Z-Score > 1.5 + MACD死叉 + RSI > 65
        """
        if len(data) < self.config.lookback_period + 26:
            return None
        
        df = self.calculate_indicators(data)
        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else current
        
        if pd.isna(current['zscore']) or pd.isna(current['rsi']) or pd.isna(current['macd_hist']):
            return None
        
        market_state = self.check_market_state(data)
        
        zscore = current['zscore']
        rsi = current['rsi']
        macd_hist = current['macd_hist']
        prev_macd_hist = prev['macd_hist']
        
        # 做多條件檢查（放寬版）
        # 1. Z-Score < -1.5
        # 2. RSI < 35
        # 3. MACD 金叉 (macd_hist 由負轉正)
        if zscore < -self.config.entry_zscore:
            if rsi < self.config.rsi_oversold:  # RSI < 35
                if prev_macd_hist < 0 and macd_hist >= 0:  # MACD金叉
                    if market_state in ['bull', 'sideways']:
                        return {
                            'signal_type': 'buy',
                            'symbol': 'TQQQ',
                            'price': current['close'],
                            'confidence': min(abs(zscore) / 3, 0.95),
                            'reason': f"Z-Score({zscore:.2f})+RSI({rsi:.1f})+MACD金叉+{market_state}市",
                            'metadata': {
                                'zscore': zscore,
                                'rsi': rsi,
                                'macd_hist': macd_hist,
                                'market_state': market_state
                            }
                        }
        
        # 做空條件檢查（放寬版）
        # 1. Z-Score > 1.5
        # 2. RSI > 65
        # 3. MACD 死叉 (macd_hist 由正轉負)
        if zscore > self.config.entry_zscore:
            if rsi > self.config.rsi_overbought:  # RSI > 65
                if prev_macd_hist > 0 and macd_hist <= 0:  # MACD死叉
                    if market_state in ['bear', 'sideways']:
                        return {
                            'signal_type': 'sell',
                            'symbol': 'TQQQ',
                            'price': current['close'],
                            'confidence': min(abs(zscore) / 3, 0.95),
                            'reason': f"Z-Score({zscore:.2f})+RSI({rsi:.1f})+MACD死叉+{market_state}市",
                            'metadata': {
                                'zscore': zscore,
                                'rsi': rsi,
                                'macd_hist': macd_hist,
                                'market_state': market_state
                            }
                        }
        
        return None
    
    def check_exit(self, position: Dict[str, Any], current_data: pd.DataFrame, current_date: datetime = None):
        """檢查是否應該平倉"""
        if len(current_data) < self.config.lookback_period:
            return False, ""
        
        df = self.calculate_indicators(current_data)
        current = df.iloc[-1]
        
        entry_price = position['entry_price']
        current_price = current['close']
        entry_time = position['entry_time']
        direction = position['direction']
        
        if direction == 'long':
            pnl_pct = (current_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - current_price) / entry_price
        
        zscore = current['zscore']
        
        # 止盈檢查
        if pnl_pct >= self.config.take_profit_pct:
            return True, f"止盈({pnl_pct*100:.2f}%)"
        
        # 止損檢查
        if pnl_pct <= -self.config.stop_loss_pct:
            return True, f"止損({pnl_pct*100:.2f}%)"
        
        # Z-Score止損
        if direction == 'long' and zscore > self.config.stop_loss_zscore:
            return True, f"Z-Score止損({zscore:.2f})"
        if direction == 'short' and zscore < -self.config.stop_loss_zscore:
            return True, f"Z-Score止損({zscore:.2f})"
        
        # Z-Score回歸止盈
        if abs(zscore) < self.config.exit_zscore:
            return True, f"Z-Score回歸({zscore:.2f})"
        
        # 時間止損
        if isinstance(entry_time, str):
            entry_time = datetime.fromisoformat(entry_time)
        
        if current_date is None:
            current_date = current_data.index[-1]
            if isinstance(current_date, pd.Timestamp):
                current_date = current_date.to_pydatetime()
        
        days_held = (current_date - entry_time).days
        if days_held >= self.config.time_stop_days:
            return True, f"時間止損({days_held}天)"
        
        return False, ""
    
    def get_position_size(self, capital: float, current_price: float) -> int:
        """計算倉位大小"""
        position_value = capital * self.config.position_pct
        shares = int(position_value / current_price)
        return max(shares, 1)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            'name': 'TQQQ Long/Short Strategy (放寬版)',
            'version': '3.0.0-relaxed',
            'entry_zscore': self.config.entry_zscore,
            'exit_zscore': self.config.exit_zscore,
            'position_pct': self.config.position_pct,
            'take_profit_pct': self.config.take_profit_pct,
            'stop_loss_pct': self.config.stop_loss_pct,
            'time_stop_days': self.config.time_stop_days,
            'rsi_overbought': self.config.rsi_overbought,
            'rsi_oversold': self.config.rsi_oversold,
            'lookback_period': self.config.lookback_period,
            'entry_conditions': {
                'long': 'Z-Score < -1.5 + MACD金叉 + RSI < 35',
                'short': 'Z-Score > 1.5 + MACD死叉 + RSI > 65'
            }
        }


@dataclass
class BacktestTrade:
    """回測交易記錄"""
    entry_date: datetime
    exit_date: Optional[datetime]
    direction: str
    entry_price: float
    exit_price: Optional[float]
    shares: int
    pnl: float
    pnl_pct: float
    exit_reason: str


@dataclass
class BacktestResult:
    """回測結果"""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    max_drawdown_pct: float
    sharpe_ratio: float
    volatility: float
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)


class TQQQBacktestEngine:
    """TQQQ回測引擎"""
    
    def __init__(
        self,
        strategy: TQQQBacktestStrategy,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.001
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        self.cash = initial_capital
        self.position = None
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[Dict] = []
        
    def fetch_data(self, symbol: str = 'TQQQ', period: str = '2y') -> pd.DataFrame:
        """從Yahoo Finance獲取數據"""
        print(f"📊 正在獲取 {symbol} 歷史數據...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        df = df.reset_index()
        
        date_col = None
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                date_col = col
                break
        
        if date_col:
            df = df.rename(columns={date_col: 'timestamp'})
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        
        print(f"✅ 獲取數據成功: {len(df)} 條記錄")
        print(f"   期間: {df.index[0]} ~ {df.index[-1]}")
        return df
    
    def run(
        self,
        data: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> BacktestResult:
        """執行回測"""
        
        df = data.copy()
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
        
        df = df.sort_index()
        
        print(f"\n🚀 開始回測...")
        print(f"   期間: {df.index[0]} ~ {df.index[-1]}")
        print(f"   初始資金: ${self.initial_capital:,.2f}")
        print(f"   數據點數: {len(df)}")
        
        # 逐日回測
        for i in range(len(df)):
            current_date = df.index[i]
            current_data = df.iloc[:i+1].copy()
            
            # 檢查平倉條件
            if self.position:
                should_exit, exit_reason = self.strategy.check_exit(self.position, current_data, current_date)
                
                if should_exit:
                    self._close_position(current_date, current_data['close'].iloc[-1], exit_reason)
            
            # 檢查開倉條件
            if not self.position:
                signal = self.strategy.generate_signal(current_data)
                
                if signal:
                    self._open_position(signal, current_date, current_data)
            
            # 記錄權益曲線
            self._record_equity(current_date, current_data['close'].iloc[-1])
        
        # 回測結束，平倉
        if self.position:
            self._close_position(df.index[-1], df['close'].iloc[-1], "回測結束平倉")
        
        return self._generate_result(df)
    
    def _open_position(self, signal, timestamp: datetime, data: pd.DataFrame):
        """開倉"""
        current_price = data['close'].iloc[-1]
        
        signal_value = signal.get('signal_type', '').lower()
        
        if signal_value == 'buy':
            executed_price = current_price * (1 + self.slippage)
            direction = 'long'
        else:
            executed_price = current_price * (1 - self.slippage)
            direction = 'short'
        
        shares = self.strategy.get_position_size(self.cash, executed_price)
        
        if shares <= 0:
            return
        
        trade_value = executed_price * shares
        commission = trade_value * self.commission_rate
        total_cost = trade_value + commission
        
        if total_cost > self.cash:
            return
        
        self.cash -= total_cost
        
        self.position = {
            'entry_time': timestamp,
            'entry_price': executed_price,
            'shares': shares,
            'direction': direction,
            'commission': commission
        }
        
        print(f"   📈 開倉 [{direction.upper()}] {timestamp.strftime('%Y-%m-%d')} @ ${executed_price:.2f} x {shares}股")
    
    def _close_position(self, timestamp: datetime, current_price: float, reason: str):
        """平倉"""
        if not self.position:
            return
        
        if self.position['direction'] == 'long':
            executed_price = current_price * (1 - self.slippage)
        else:
            executed_price = current_price * (1 + self.slippage)
        
        entry_price = self.position['entry_price']
        shares = self.position['shares']
        
        if self.position['direction'] == 'long':
            pnl = (executed_price - entry_price) * shares
            pnl_pct = (executed_price - entry_price) / entry_price
        else:
            pnl = (entry_price - executed_price) * shares
            pnl_pct = (entry_price - executed_price) / entry_price
        
        commission = executed_price * shares * self.commission_rate
        pnl -= commission
        
        trade_value = executed_price * shares
        self.cash += trade_value - commission
        
        trade = BacktestTrade(
            entry_date=self.position['entry_time'],
            exit_date=timestamp,
            direction=self.position['direction'],
            entry_price=entry_price,
            exit_price=executed_price,
            shares=shares,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason=reason
        )
        self.trades.append(trade)
        
        emoji = "✅" if pnl > 0 else "❌"
        print(f"   {emoji} 平倉 [{self.position['direction'].upper()}] {timestamp.strftime('%Y-%m-%d')} @ ${executed_price:.2f} | P&L: ${pnl:,.2f} ({pnl_pct*100:+.2f}%) | {reason}")
        
        self.position = None
    
    def _record_equity(self, timestamp: datetime, current_price: float):
        """記錄權益曲線"""
        position_value = 0
        if self.position:
            position_value = self.position['shares'] * current_price
            self.position['current_value'] = position_value
        
        total_equity = self.cash + position_value
        self.equity_curve.append({
            'timestamp': timestamp,
            'cash': self.cash,
            'position_value': position_value,
            'total_equity': total_equity
        })
    
    def _generate_result(self, df: pd.DataFrame) -> BacktestResult:
        """生成回測結果"""
        
        equity_df = pd.DataFrame(self.equity_curve)
        if not equity_df.empty:
            equity_df.set_index('timestamp', inplace=True)
        
        initial_capital = self.initial_capital
        final_capital = self.cash
        total_return_pct = ((final_capital - initial_capital) / initial_capital) * 100
        
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        losing_trades = len([t for t in self.trades if t.pnl <= 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        profits = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl <= 0]
        avg_profit = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 0
        total_profit = sum(profits)
        total_loss = abs(sum(losses))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        if not equity_df.empty:
            equity_df['peak'] = equity_df['total_equity'].cummax()
            equity_df['drawdown'] = equity_df['total_equity'] - equity_df['peak']
            equity_df['drawdown_pct'] = (equity_df['drawdown'] / equity_df['peak']) * 100
            max_drawdown_pct = equity_df['drawdown_pct'].min()
            
            equity_df['returns'] = equity_df['total_equity'].pct_change().dropna()
            if equity_df['returns'].std() > 0:
                risk_free_rate = 0.02
                excess_returns = equity_df['returns'] - risk_free_rate / 252
                sharpe_ratio = np.sqrt(252) * excess_returns.mean() / equity_df['returns'].std()
                volatility = equity_df['returns'].std() * np.sqrt(252) * 100
            else:
                sharpe_ratio = 0
                volatility = 0
        else:
            max_drawdown_pct = 0
            sharpe_ratio = 0
            volatility = 0
        
        return BacktestResult(
            start_date=df.index[0],
            end_date=df.index[-1],
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return_pct=total_return_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
            trades=self.trades,
            equity_curve=equity_df
        )


def run_backtest_2024_relaxed():
    """執行2024年度回測（放寬版）"""
    
    print("="*70)
    print("TQQQ Long/Short Strategy - 2024年度回測（放寬版）")
    print("="*70)
    
    # 策略配置（放寬版）
    config = {
        'entry_zscore': 1.5,
        'exit_zscore': 0.5,
        'position_pct': 0.50,
        'take_profit_pct': 0.05,
        'stop_loss_pct': 0.03,
        'time_stop_days': 3,
        'rsi_overbought': 65.0,  # 放寬版
        'rsi_oversold': 35.0,    # 放寬版
        'stop_loss_zscore': 3.5,
        'lookback_period': 60,
        'rsi_period': 14,
        'require_market_state': True
    }
    
    # 創建策略
    strategy = TQQQBacktestStrategy(config)
    
    # 創建回測引擎
    engine = TQQQBacktestEngine(
        strategy=strategy,
        initial_capital=100000.0,
        commission_rate=0.001,
        slippage=0.001
    )
    
    # 獲取數據 - 使用更長的期間確保覆蓋2024全年
    data = engine.fetch_data('TQQQ', period='3y')
    
    # 執行回測 - 2024全年
    result = engine.run(
        data,
        start_date='2024-01-01',
        end_date='2024-12-31'
    )
    
    # 輸出結果
    print("\n" + "="*70)
    print("📊 回測結果")
    print("="*70)
    print(f"回測期間: {result.start_date} ~ {result.end_date}")
    print(f"初始資金: ${result.initial_capital:,.2f}")
    print(f"最終資金: ${result.final_capital:,.2f}")
    print(f"總回報: {result.total_return_pct:.2f}%")
    print(f"總交易次數: {result.total_trades}")
    print(f"盈利交易: {result.winning_trades}")
    print(f"虧損交易: {result.losing_trades}")
    print(f"勝率: {result.win_rate:.2f}%")
    print(f"平均盈利: ${result.avg_profit:,.2f}")
    print(f"平均虧損: ${result.avg_loss:,.2f}")
    print(f"盈虧比: {result.profit_factor:.2f}")
    print(f"最大回撤: {result.max_drawdown_pct:.2f}%")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"波動率: {result.volatility:.2f}%")
    print("="*70)
    
    # 保存結果
    save_results(result, strategy)
    
    return result


def save_results(result: BacktestResult, strategy: TQQQBacktestStrategy):
    """保存回測結果"""
    
    report_dir = 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot/reports'
    os.makedirs(report_dir, exist_ok=True)
    
    # 保存JSON結果 - 使用指定文件名
    json_file = f'{report_dir}/backtest_2024_relaxed.json'
    
    result_dict = {
        'summary': {
            'start_date': str(result.start_date),
            'end_date': str(result.end_date),
            'initial_capital': float(result.initial_capital),
            'final_capital': float(result.final_capital),
            'total_return_pct': float(result.total_return_pct),
            'total_trades': int(result.total_trades),
            'winning_trades': int(result.winning_trades),
            'losing_trades': int(result.losing_trades),
            'win_rate': float(result.win_rate),
            'avg_profit': float(result.avg_profit),
            'avg_loss': float(result.avg_loss),
            'profit_factor': float(result.profit_factor),
            'max_drawdown_pct': float(result.max_drawdown_pct),
            'sharpe_ratio': float(result.sharpe_ratio),
            'volatility': float(result.volatility)
        },
        'strategy_config': strategy.get_strategy_info(),
        'trades': [
            {
                'entry_date': str(t.entry_date),
                'exit_date': str(t.exit_date),
                'direction': t.direction,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'shares': t.shares,
                'pnl': t.pnl,
                'pnl_pct': t.pnl_pct,
                'exit_reason': t.exit_reason
            }
            for t in result.trades
        ]
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, default=str)
    
    print(f"\n💾 結果已保存: {json_file}")
    
    # 保存權益曲線
    if not result.equity_curve.empty:
        equity_file = f'{report_dir}/equity_curve_2024_relaxed.csv'
        result.equity_curve.to_csv(equity_file)
        print(f"📈 權益曲線已保存: {equity_file}")


if __name__ == '__main__':
    result = run_backtest_2024_relaxed()
