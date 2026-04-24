"""
TQQQ 2022年度回測腳本（放寬版）
回測期間: 2022-01-01 至 2022-12-31
策略參數（放寬版）:
- Z-Score: ±1.5
- RSI: < 35 / > 65
- MACD: 金叉/死叉
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
class BacktestTrade:
    """回測交易記錄"""
    entry_date: datetime
    exit_date: Optional[datetime]
    direction: str  # 'long' or 'short'
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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'start_date': str(self.start_date),
            'end_date': str(self.end_date),
            'initial_capital': float(self.initial_capital),
            'final_capital': float(self.final_capital),
            'total_return_pct': float(self.total_return_pct),
            'total_trades': int(self.total_trades),
            'winning_trades': int(self.winning_trades),
            'losing_trades': int(self.losing_trades),
            'win_rate': float(self.win_rate),
            'avg_profit': float(self.avg_profit),
            'avg_loss': float(self.avg_loss),
            'profit_factor': float(self.profit_factor),
            'max_drawdown_pct': float(self.max_drawdown_pct),
            'sharpe_ratio': float(self.sharpe_ratio),
            'volatility': float(self.volatility)
        }


class TQQQRelaxedStrategy:
    """TQQQ放寬版策略（2022回測專用）"""
    
    def __init__(self):
        # 放寬版策略參數
        self.entry_zscore = 1.5      # Z-Score閾值: ±1.5
        self.exit_zscore = 0.5       # 出場Z分數
        self.stop_loss_zscore = 3.5  # 止損Z分數
        self.position_pct = 0.50     # 單筆倉位50%
        self.lookback_period = 60    # Z-Score計算週期
        self.rsi_period = 14         # RSI週期
        self.rsi_overbought = 65.0   # RSI超買閾值: > 65
        self.rsi_oversold = 35.0     # RSI超賣閾值: < 35
        self.volume_ma_period = 20   # 成交量均線週期
        self.take_profit_pct = 0.05  # 止盈5%
        self.stop_loss_pct = 0.03    # 止損3%
        self.time_stop_days = 3      # 時間止損3天
        
        print(f"放寬版策略初始化: Z-Score±{self.entry_zscore}, RSI({self.rsi_oversold}/{self.rsi_overbought})")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
        df = data.copy()
        
        # 計算Z-Score
        df['price_ma'] = df['close'].rolling(window=self.lookback_period).mean()
        df['price_std'] = df['close'].rolling(window=self.lookback_period).std()
        df['zscore'] = (df['close'] - df['price_ma']) / df['price_std']
        
        # 計算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 計算成交量均線
        df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period).mean()
        
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
        """生成交易信號"""
        if len(data) < self.lookback_period + 20:
            return None
        
        # 計算指標
        df = self.calculate_indicators(data)
        current = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else current
        
        # 檢查數據有效性
        if pd.isna(current['zscore']) or pd.isna(current['rsi']) or pd.isna(current['macd_hist']):
            return None
        
        market_state = self.check_market_state(data)
        
        zscore = current['zscore']
        rsi = current['rsi']
        macd_hist = current['macd_hist']
        prev_macd_hist = prev['macd_hist']
        volume = current['volume']
        volume_ma = current['volume_ma']
        
        # 做多條件檢查（放寬版）
        # 1. Z-Score < -1.5
        # 2. RSI < 35
        # 3. MACD 金叉 (prev < 0 and current >= 0)
        # 4. 市場狀態：牛市或震盪
        if zscore < -self.entry_zscore:
            if rsi < self.rsi_oversold:
                if prev_macd_hist < 0 and macd_hist >= 0:  # MACD金叉
                    if volume > volume_ma * 0.8:  # 成交量確認
                        if market_state in ['bull', 'sideways']:
                            return {
                                'signal_type': 'buy',
                                'symbol': 'TQQQ',
                                'price': current['close'],
                                'confidence': min(abs(zscore) / 3, 0.95),
                                'reason': f"Z-Score({zscore:.2f})超賣+RSI({rsi:.1f})低+MACD金叉+{market_state}市"
                            }
        
        # 做空條件檢查（放寬版）
        # 1. Z-Score > 1.5
        # 2. RSI > 65
        # 3. MACD 死叉 (prev > 0 and current <= 0)
        # 4. 市場狀態：熊市或震盪
        if zscore > self.entry_zscore:
            if rsi > self.rsi_overbought:
                if prev_macd_hist > 0 and macd_hist <= 0:  # MACD死叉
                    if volume > volume_ma * 0.8:  # 成交量確認
                        if market_state in ['bear', 'sideways']:
                            return {
                                'signal_type': 'sell',
                                'symbol': 'TQQQ',
                                'price': current['close'],
                                'confidence': min(abs(zscore) / 3, 0.95),
                                'reason': f"Z-Score({zscore:.2f})超買+RSI({rsi:.1f})高+MACD死叉+{market_state}市"
                            }
        
        return None
    
    def check_exit(self, position: Dict[str, Any], current_data: pd.DataFrame):
        """檢查是否應該平倉"""
        if len(current_data) < self.lookback_period:
            return False, ""
        
        # 計算當前指標
        df = self.calculate_indicators(current_data)
        current = df.iloc[-1]
        
        entry_price = position['entry_price']
        current_price = current['close']
        entry_time = position['entry_time']
        direction = position['direction']
        
        # 計算盈虧
        if direction == 'long':
            pnl_pct = (current_price - entry_price) / entry_price
        else:  # short
            pnl_pct = (entry_price - current_price) / entry_price
        
        zscore = current['zscore']
        
        # 止盈檢查
        if pnl_pct >= self.take_profit_pct:
            return True, f"止盈({pnl_pct*100:.2f}%)"
        
        # 止損檢查
        if pnl_pct <= -self.stop_loss_pct:
            return True, f"止損({pnl_pct*100:.2f}%)"
        
        # Z-Score止損（策略失效）
        if direction == 'long' and zscore > self.stop_loss_zscore:
            return True, f"Z-Score止損({zscore:.2f})"
        if direction == 'short' and zscore < -self.stop_loss_zscore:
            return True, f"Z-Score止損({zscore:.2f})"
        
        # Z-Score回歸止盈
        if abs(zscore) < self.exit_zscore:
            return True, f"Z-Score回歸({zscore:.2f})"
        
        # 時間止損檢查
        if isinstance(entry_time, str):
            entry_time = datetime.fromisoformat(entry_time)
        
        days_held = (current_data.index[-1] - entry_time).days
        if days_held >= self.time_stop_days:
            return True, f"時間止損({days_held}天)"
        
        return False, ""
    
    def get_position_size(self, capital: float, current_price: float) -> int:
        """計算倉位大小"""
        position_value = capital * self.position_pct
        shares = int(position_value / current_price)
        return max(shares, 1)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            'name': 'TQQQ Relaxed Strategy (放寬版)',
            'version': '1.0.0',
            'entry_zscore': self.entry_zscore,
            'exit_zscore': self.exit_zscore,
            'stop_loss_zscore': self.stop_loss_zscore,
            'position_pct': self.position_pct,
            'take_profit_pct': self.take_profit_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'time_stop_days': self.time_stop_days,
            'rsi_overbought': self.rsi_overbought,
            'rsi_oversold': self.rsi_oversold,
            'lookback_period': self.lookback_period,
            'volume_ma_period': self.volume_ma_period
        }


class TQQQBacktestEngine:
    """TQQQ回測引擎"""
    
    def __init__(
        self,
        strategy: TQQQRelaxedStrategy,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.001
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        self.cash = initial_capital
        self.position = None  # 單一倉位
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[Dict] = []
    
    def fetch_data(self, symbol: str = 'TQQQ', period: str = '5y') -> pd.DataFrame:
        """從Yahoo Finance獲取數據"""
        print(f"📊 正在獲取 {symbol} 歷史數據...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        # 標準化列名
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # 處理索引
        df = df.reset_index()
        
        # 找到日期列
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
        
        # 準備數據
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
            current_price = df['close'].iloc[i]
            
            # 檢查平倉條件
            if self.position:
                should_exit, exit_reason = self.strategy.check_exit(self.position, current_data)
                
                if should_exit:
                    self._close_position(current_date, current_price, exit_reason)
            
            # 檢查開倉條件（無持倉時）
            if not self.position:
                signal = self.strategy.generate_signal(current_data)
                
                if signal:
                    self._open_position(signal, current_date, current_data)
            
            # 記錄權益曲線
            self._record_equity(current_date, current_price)
        
        # 回測結束，平倉所有持倉
        if self.position:
            self._close_position(df.index[-1], df['close'].iloc[-1], "回測結束平倉")
        
        return self._generate_result(df)
    
    def _open_position(self, signal, timestamp: datetime, data: pd.DataFrame):
        """開倉"""
        current_price = data['close'].iloc[-1]
        
        # 考慮滑點
        signal_type = signal.get('signal_type', '').lower()
        
        if signal_type == 'buy':
            executed_price = current_price * (1 + self.slippage)
            direction = 'long'
        else:
            executed_price = current_price * (1 - self.slippage)
            direction = 'short'
        
        # 計算倉位大小
        shares = self.strategy.get_position_size(self.cash, executed_price)
        
        if shares <= 0:
            return
        
        # 計算成本
        trade_value = executed_price * shares
        commission = trade_value * self.commission_rate
        total_cost = trade_value + commission
        
        if total_cost > self.cash:
            return
        
        # 扣除現金
        self.cash -= total_cost
        
        # 創建倉位
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
        
        # 考慮滑點
        if self.position['direction'] == 'long':
            executed_price = current_price * (1 - self.slippage)
        else:
            executed_price = current_price * (1 + self.slippage)
        
        # 計算盈虧
        entry_price = self.position['entry_price']
        shares = self.position['shares']
        
        if self.position['direction'] == 'long':
            pnl = (executed_price - entry_price) * shares
            pnl_pct = (executed_price - entry_price) / entry_price
        else:  # short
            pnl = (entry_price - executed_price) * shares
            pnl_pct = (entry_price - executed_price) / entry_price
        
        # 扣除佣金
        commission = executed_price * shares * self.commission_rate
        pnl -= commission
        
        # 回收資金
        trade_value = executed_price * shares
        self.cash += trade_value - commission
        
        # 記錄交易
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
        
        # 清空倉位
        self.position = None
    
    def _record_equity(self, timestamp: datetime, current_price: float):
        """記錄權益曲線"""
        position_value = 0
        if self.position:
            if self.position['direction'] == 'long':
                position_value = current_price * self.position['shares']
            else:  # short
                # 簡化計算
                position_value = self.position['entry_price'] * self.position['shares']
        
        total_equity = self.cash + position_value
        self.equity_curve.append({
            'timestamp': timestamp,
            'cash': self.cash,
            'position_value': position_value,
            'total_equity': total_equity
        })
    
    def _generate_result(self, df: pd.DataFrame) -> BacktestResult:
        """生成回測結果"""
        
        # 創建權益曲線DataFrame
        equity_df = pd.DataFrame(self.equity_curve)
        if not equity_df.empty:
            equity_df.set_index('timestamp', inplace=True)
        
        # 計算績效指標
        initial_capital = self.initial_capital
        final_capital = self.cash
        total_return_pct = ((final_capital - initial_capital) / initial_capital) * 100
        
        # 交易統計
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
        
        # 計算最大回撤
        if not equity_df.empty:
            equity_df['peak'] = equity_df['total_equity'].cummax()
            equity_df['drawdown'] = equity_df['total_equity'] - equity_df['peak']
            equity_df['drawdown_pct'] = (equity_df['drawdown'] / equity_df['peak']) * 100
            max_drawdown_pct = equity_df['drawdown_pct'].min()
            
            # 計算夏普比率
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


def run_backtest():
    """執行2022年度回測（放寬版）"""
    
    print("="*70)
    print("TQQQ Long/Short Strategy - 2022年度回測（放寬版）")
    print("="*70)
    print("回測期間: 2022-01-01 至 2022-12-31")
    print("策略參數:")
    print("  - Z-Score: ±1.5")
    print("  - RSI: < 35 / > 65")
    print("  - MACD: 金叉/死叉")
    print("="*70)
    
    # 創建策略
    strategy = TQQQRelaxedStrategy()
    
    # 創建回測引擎
    engine = TQQQBacktestEngine(
        strategy=strategy,
        initial_capital=100000.0,
        commission_rate=0.001,
        slippage=0.001
    )
    
    # 獲取數據
    data = engine.fetch_data('TQQQ', period='5y')
    
    # 執行回測（2022年度）
    result = engine.run(
        data,
        start_date='2022-01-01',
        end_date='2022-12-31'
    )
    
    # 輸出結果
    print("\n" + "="*70)
    print("回測結果")
    print("="*70)
    print(f"回測期間: {result.start_date} ~ {result.end_date}")
    print(f"初始資金: ${result.initial_capital:,.2f}")
    print(f"最終資金: ${result.final_capital:,.2f}")
    print(f"總回報: {result.total_return_pct:.2f}%")
    print(f"總交易次數: {result.total_trades}")
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


def save_results(result: BacktestResult, strategy: TQQQRelaxedStrategy):
    """保存回測結果"""
    
    report_dir = 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot/reports'
    
    # 確保目錄存在
    os.makedirs(report_dir, exist_ok=True)
    
    # 保存JSON結果（符合要求的命名格式）
    json_file = f'{report_dir}/backtest_2022_relaxed.json'
    result_dict = {
        'summary': result.to_dict(),
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
    
    print(f"\n📊 JSON結果已保存: {json_file}")
    
    # 保存摘要報告
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'{report_dir}/backtest_2022_relaxed_report_{timestamp}.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("TQQQ Long/Short Strategy - 2022年度回測報告（放寬版）\n")
        f.write("="*70 + "\n\n")
        
        # 策略配置
        f.write("策略配置:\n")
        f.write("-"*70 + "\n")
        for key, value in strategy.get_strategy_info().items():
            f.write(f"  {key}: {value}\n")
        f.write("\n")
        
        # 回測結果
        f.write("回測結果:\n")
        f.write("-"*70 + "\n")
        f.write(f"回測期間: {result.start_date} ~ {result.end_date}\n")
        f.write(f"初始資金: ${result.initial_capital:,.2f}\n")
        f.write(f"最終資金: ${result.final_capital:,.2f}\n")
        f.write(f"總回報: {result.total_return_pct:.2f}%\n")
        f.write(f"總交易次數: {result.total_trades}\n")
        f.write(f"勝率: {result.win_rate:.2f}%\n")
        f.write(f"平均盈利: ${result.avg_profit:,.2f}\n")
        f.write(f"平均虧損: ${result.avg_loss:,.2f}\n")
        f.write(f"盈虧比: {result.profit_factor:.2f}\n")
        f.write(f"最大回撤: {result.max_drawdown_pct:.2f}%\n")
        f.write(f"夏普比率: {result.sharpe_ratio:.2f}\n")
        f.write(f"波動率: {result.volatility:.2f}%\n")
        f.write("\n")
        
        # 逐筆交易記錄
        f.write("逐筆交易記錄:\n")
        f.write("-"*70 + "\n")
        for i, trade in enumerate(result.trades, 1):
            f.write(f"\n交易 #{i}:\n")
            f.write(f"  方向: {trade.direction.upper()}\n")
            f.write(f"  進場: {trade.entry_date} @ ${trade.entry_price:.2f}\n")
            f.write(f"  出場: {trade.exit_date} @ ${trade.exit_price:.2f}\n")
            f.write(f"  股數: {trade.shares}\n")
            f.write(f"  盈虧: ${trade.pnl:,.2f} ({trade.pnl_pct*100:+.2f}%)\n")
            f.write(f"  出場原因: {trade.exit_reason}\n")
    
    print(f"📄 報告已保存: {report_file}")
    
    # 保存權益曲線
    if not result.equity_curve.empty:
        equity_file = f'{report_dir}/equity_curve_2022_relaxed_{timestamp}.csv'
        result.equity_curve.to_csv(equity_file)
        print(f"📈 權益曲線已保存: {equity_file}")


if __name__ == '__main__':
    result = run_backtest()
