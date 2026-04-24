"""
TQQQ策略2025年度回測（最終版）
回測期間: 2025-01-01 至 2025-12-31 (全年)
策略參數: 框架A最終版

## 策略參數（最終版）
- entry_zscore: 2.0
- exit_zscore: 0.5
- position_pct: 0.50
- take_profit_pct: 0.05
- stop_loss_pct: 0.03
- time_stop_days: 3
- rsi_overbought: 70.0
- rsi_oversold: 30.0

## 進場條件
- 做多: Z-Score < -2.0 + MACD金叉 + RSI < 30
- 做空: Z-Score > 2.0 + MACD死叉 + RSI > 70
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
import sys


class TQQQBacktest2025Final:
    """TQQQ 2025年度回測引擎（最終版）"""
    
    def __init__(
        self,
        entry_zscore: float = 2.0,
        exit_zscore: float = 0.5,
        position_pct: float = 0.50,
        take_profit_pct: float = 0.05,
        stop_loss_pct: float = 0.03,
        time_stop_days: int = 3,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.001
    ):
        self.config = {
            'entry_zscore': entry_zscore,
            'exit_zscore': exit_zscore,
            'position_pct': position_pct,
            'take_profit_pct': take_profit_pct,
            'stop_loss_pct': stop_loss_pct,
            'time_stop_days': time_stop_days,
            'rsi_overbought': rsi_overbought,
            'rsi_oversold': rsi_oversold,
            'lookback_period': 60,
            'rsi_period': 14,
            'volume_ma_period': 20,
            'stop_loss_zscore': 3.5
        }
        
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        self.cash = initial_capital
        self.position = None
        self.trades = []
        self.equity_curve = []
        
    def fetch_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """獲取TQQQ歷史數據"""
        print(f"正在獲取TQQQ數據: {start_date} 至 {end_date}")
        
        # 為了計算60日Z-Score，需要額外獲取60天前的數據
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        extended_start = (start_dt - timedelta(days=90)).strftime('%Y-%m-%d')
        
        ticker = yf.Ticker("TQQQ")
        df = ticker.history(start=extended_start, end=end_date, interval='1d')
        
        if df.empty:
            raise ValueError("無法獲取TQQQ數據")
        
        # 移除時區信息
        df.index = df.index.tz_localize(None)
        
        df.reset_index(inplace=True)
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
        
        if 'date' in df.columns:
            df.rename(columns={'date': 'timestamp'}, inplace=True)
        if 'datetime' in df.columns:
            df.rename(columns={'datetime': 'timestamp'}, inplace=True)
            
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        print(f"獲取到 {len(df)} 條數據")
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標 - 包含MACD"""
        # Z-Score
        lookback = self.config['lookback_period']
        df['price_ma'] = df['close'].rolling(window=lookback).mean()
        df['price_std'] = df['close'].rolling(window=lookback).std()
        df['zscore'] = (df['close'] - df['price_ma']) / df['price_std']
        
        # RSI
        rsi_period = self.config['rsi_period']
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Volume MA
        df['volume_ma'] = df['volume'].rolling(window=self.config['volume_ma_period']).mean()
        
        # 200日均線（市場狀態判斷）
        df['ma200'] = df['close'].rolling(window=200).mean()
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def get_market_state(self, df: pd.DataFrame, current_idx: int) -> str:
        """判斷市場狀態"""
        if current_idx < 200:
            return 'sideways'
        
        current_price = df['close'].iloc[current_idx]
        ma200 = df['ma200'].iloc[current_idx]
        
        if current_price > ma200 * 1.05:
            return 'bull'
        elif current_price < ma200 * 0.95:
            return 'bear'
        else:
            return 'sideways'
    
    def check_entry_signal(self, df: pd.DataFrame, idx: int) -> tuple:
        """
        檢查進場信號（最終版）
        
        做多: Z-Score < -2.0 + MACD金叉 + RSI < 30
        做空: Z-Score > 2.0 + MACD死叉 + RSI > 70
        
        返回: (signal_type, reason) 或 (None, "")
        """
        if idx < 1:
            return None, ""
            
        row = df.iloc[idx]
        prev_row = df.iloc[idx - 1]
        
        if pd.isna(row['zscore']) or pd.isna(row['rsi']) or pd.isna(row['macd_hist']):
            return None, ""
        
        zscore = row['zscore']
        rsi = row['rsi']
        macd_hist = row['macd_hist']
        prev_macd_hist = prev_row['macd_hist']
        volume = row['volume']
        volume_ma = row['volume_ma']
        
        market_state = self.get_market_state(df, idx)
        
        # 做多條件: Z-Score < -2.0 + MACD金叉 + RSI < 30
        if zscore < -self.config['entry_zscore']:
            if rsi < self.config['rsi_oversold']:  # RSI < 30
                if prev_macd_hist < 0 and macd_hist >= 0:  # MACD金叉
                    if volume > volume_ma * 0.8:
                        if market_state in ['bull', 'sideways']:
                            return 'long', f"Z-Score({zscore:.2f})+RSI({rsi:.1f})+MACD金叉+{market_state}市"
        
        # 做空條件: Z-Score > 2.0 + MACD死叉 + RSI > 70
        if zscore > self.config['entry_zscore']:
            if rsi > self.config['rsi_overbought']:  # RSI > 70
                if prev_macd_hist > 0 and macd_hist <= 0:  # MACD死叉
                    if volume > volume_ma * 0.8:
                        if market_state in ['bear', 'sideways']:
                            return 'short', f"Z-Score({zscore:.2f})+RSI({rsi:.1f})+MACD死叉+{market_state}市"
        
        return None, ""
    
    def check_exit_signal(self, df: pd.DataFrame, idx: int, position: dict) -> tuple:
        """
        檢查出場信號（最終版）
        
        止盈: 5%
        止損: 3%
        Z-Score回歸: ±0.5
        時間止損: 3天
        
        返回: (should_exit, reason)
        """
        row = df.iloc[idx]
        current_price = row['close']
        zscore = row['zscore']
        
        entry_price = position['entry_price']
        direction = position['direction']
        entry_time = position['entry_time']
        
        # 計算盈虧
        if direction == 'long':
            pnl_pct = (current_price - entry_price) / entry_price
        else:  # short
            pnl_pct = (entry_price - current_price) / entry_price
        
        # 止盈檢查 (5%)
        if pnl_pct >= self.config['take_profit_pct']:
            return True, f"止盈({pnl_pct*100:.2f}%)"
        
        # 止損檢查 (3%)
        if pnl_pct <= -self.config['stop_loss_pct']:
            return True, f"止損({pnl_pct*100:.2f}%)"
        
        # Z-Score止損 (3.5)
        if direction == 'long' and zscore > self.config['stop_loss_zscore']:
            return True, f"Z-Score止損({zscore:.2f})"
        if direction == 'short' and zscore < -self.config['stop_loss_zscore']:
            return True, f"Z-Score止損({zscore:.2f})"
        
        # Z-Score回歸止盈 (0.5)
        if abs(zscore) < self.config['exit_zscore']:
            return True, f"Z-Score回歸({zscore:.2f})"
        
        # 時間止損 (3天)
        current_time = df.index[idx]
        days_held = (current_time - entry_time).days
        if days_held >= self.config['time_stop_days']:
            return True, f"時間止損({days_held}天)"
        
        return False, ""
    
    def run_backtest(self, df: pd.DataFrame, start_date: str, end_date: str) -> dict:
        """執行回測"""
        print(f"\n開始回測: {start_date} 至 {end_date}")
        print(f"策略參數: entry_zscore={self.config['entry_zscore']}, exit_zscore={self.config['exit_zscore']}")
        print(f"止盈: {self.config['take_profit_pct']*100}%, 止損: {self.config['stop_loss_pct']*100}%")
        print(f"RSI超買: {self.config['rsi_overbought']}, RSI超賣: {self.config['rsi_oversold']}")
        
        # 計算指標
        df = self.calculate_indicators(df)
        
        # 過濾回測期間
        start_dt = pd.Timestamp(start_date)
        end_dt = pd.Timestamp(end_date)
        df = df[(df.index >= start_dt) & (df.index <= end_dt)]
        
        if len(df) == 0:
            raise ValueError("回測期間無數據")
        
        print(f"回測數據點: {len(df)} 天")
        
        # 重置狀態
        self.cash = self.initial_capital
        self.position = None
        self.trades = []
        self.equity_curve = []
        
        # 逐日回測
        for i in range(len(df)):
            current_time = df.index[i]
            current_price = df['close'].iloc[i]
            
            # 記錄權益
            position_value = 0
            if self.position:
                if self.position['direction'] == 'long':
                    position_value = current_price * self.position['qty']
                else:  # short
                    entry_value = self.position['entry_price'] * self.position['qty']
                    current_value = current_price * self.position['qty']
                    pnl = entry_value - current_value
                    position_value = entry_value + pnl
            
            total_equity = self.cash + position_value
            self.equity_curve.append({
                'timestamp': current_time.strftime('%Y-%m-%d'),
                'cash': self.cash,
                'position_value': position_value,
                'total_equity': total_equity,
                'close': current_price
            })
            
            # 檢查出場
            if self.position:
                should_exit, exit_reason = self.check_exit_signal(df, i, self.position)
                if should_exit:
                    exit_price = current_price * (1 - self.slippage) if self.position['direction'] == 'long' else current_price * (1 + self.slippage)
                    
                    if self.position['direction'] == 'long':
                        proceeds = exit_price * self.position['qty']
                        cost = self.position['entry_price'] * self.position['qty']
                        pnl = proceeds - cost
                        pnl_pct = pnl / cost
                        self.cash += proceeds
                    else:  # short
                        cover_cost = exit_price * self.position['qty']
                        entry_value = self.position['entry_price'] * self.position['qty']
                        pnl = entry_value - cover_cost
                        pnl_pct = pnl / entry_value
                        self.cash += (entry_value + pnl)
                    
                    commission = exit_price * self.position['qty'] * self.commission_rate
                    self.cash -= commission
                    
                    self.trades.append({
                        'entry_time': self.position['entry_time'].strftime('%Y-%m-%d'),
                        'exit_time': current_time.strftime('%Y-%m-%d'),
                        'direction': self.position['direction'],
                        'entry_price': self.position['entry_price'],
                        'exit_price': exit_price,
                        'qty': self.position['qty'],
                        'pnl': pnl,
                        'pnl_pct': pnl_pct * 100,
                        'exit_reason': exit_reason
                    })
                    
                    print(f"  [{current_time.strftime('%Y-%m-%d')}] 平倉: {self.position['direction']} | PnL: ${pnl:.2f} ({pnl_pct*100:.2f}%) | 原因: {exit_reason}")
                    self.position = None
            
            # 檢查進場
            if not self.position:
                signal_type, reason = self.check_entry_signal(df, i)
                if signal_type:
                    entry_price = df['close'].iloc[i] * (1 + self.slippage) if signal_type == 'long' else df['close'].iloc[i] * (1 - self.slippage)
                    
                    position_value = self.cash * self.config['position_pct']
                    qty = int(position_value / entry_price)
                    
                    if qty > 0:
                        total_cost = entry_price * qty
                        commission = total_cost * self.commission_rate
                        
                        if signal_type == 'long':
                            if total_cost + commission <= self.cash:
                                self.cash -= (total_cost + commission)
                                self.position = {
                                    'entry_price': entry_price,
                                    'qty': qty,
                                    'direction': 'long',
                                    'entry_time': current_time
                                }
                                print(f"  [{current_time.strftime('%Y-%m-%d')}] 做多: {qty}股 @ ${entry_price:.2f} | 原因: {reason}")
                        else:  # short
                            margin_required = total_cost * 0.5
                            if margin_required + commission <= self.cash:
                                self.cash -= commission
                                self.position = {
                                    'entry_price': entry_price,
                                    'qty': qty,
                                    'direction': 'short',
                                    'entry_time': current_time
                                }
                                print(f"  [{current_time.strftime('%Y-%m-%d')}] 做空: {qty}股 @ ${entry_price:.2f} | 原因: {reason}")
        
        # 回測結束，平倉
        if self.position:
            final_price = df['close'].iloc[-1]
            exit_price = final_price * (1 - self.slippage) if self.position['direction'] == 'long' else final_price * (1 + self.slippage)
            
            if self.position['direction'] == 'long':
                proceeds = exit_price * self.position['qty']
                cost = self.position['entry_price'] * self.position['qty']
                pnl = proceeds - cost
                self.cash += proceeds
            else:
                cover_cost = exit_price * self.position['qty']
                entry_value = self.position['entry_price'] * self.position['qty']
                pnl = entry_value - cover_cost
                self.cash += (entry_value + pnl)
            
            commission = exit_price * self.position['qty'] * self.commission_rate
            self.cash -= commission
            
            self.trades.append({
                'entry_time': self.position['entry_time'].strftime('%Y-%m-%d'),
                'exit_time': df.index[-1].strftime('%Y-%m-%d'),
                'direction': self.position['direction'],
                'entry_price': self.position['entry_price'],
                'exit_price': exit_price,
                'qty': self.position['qty'],
                'pnl': pnl,
                'pnl_pct': (pnl / (self.position['entry_price'] * self.position['qty'])) * 100,
                'exit_reason': '回測結束平倉'
            })
            print(f"  [回測結束] 強制平倉: {self.position['direction']} | PnL: ${pnl:.2f}")
        
        return self.generate_report(df)
    
    def generate_report(self, df: pd.DataFrame) -> dict:
        """生成回測報告"""
        equity_df = pd.DataFrame(self.equity_curve)
        
        initial_capital = self.initial_capital
        final_capital = equity_df['total_equity'].iloc[-1]
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        # 計算勝率
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 計算最大回撤
        equity_df['peak'] = equity_df['total_equity'].cummax()
        equity_df['drawdown'] = equity_df['total_equity'] - equity_df['peak']
        equity_df['drawdown_pct'] = (equity_df['drawdown'] / equity_df['peak']) * 100
        max_drawdown = equity_df['drawdown'].min()
        max_drawdown_pct = equity_df['drawdown_pct'].min()
        
        # 計算夏普比率
        equity_df['returns'] = equity_df['total_equity'].pct_change().dropna()
        risk_free_rate = 0.02
        if equity_df['returns'].std() > 0:
            excess_returns = equity_df['returns'] - risk_free_rate / 252
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / equity_df['returns'].std()
        else:
            sharpe_ratio = 0
        
        # 盈虧統計
        profits = [t['pnl'] for t in self.trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in self.trades if t['pnl'] <= 0]
        avg_profit = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # Profit Factor
        total_profit = sum(profits) if profits else 0
        total_loss = abs(sum(losses)) if losses else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        report = {
            'backtest_period': {
                'start': df.index[0].strftime('%Y-%m-%d'),
                'end': df.index[-1].strftime('%Y-%m-%d')
            },
            'strategy_config': self.config,
            'initial_capital': initial_capital,
            'final_capital': round(final_capital, 2),
            'total_return': round(total_return, 2),
            'total_return_pct': round(total_return_pct, 2),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'avg_profit': round(avg_profit, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_drawdown, 2),
            'max_drawdown_pct': round(max_drawdown_pct, 2),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
        
        return report


def main():
    """主函數"""
    print("="*70)
    print("TQQQ策略2025年度回測（最終版）")
    print("="*70)
    
    # 回測期間: 2025年全年
    start_date = '2025-01-01'
    end_date = '2026-01-01'
    
    # 策略參數（最終版）
    config = {
        'entry_zscore': 2.0,
        'exit_zscore': 0.5,
        'position_pct': 0.50,
        'take_profit_pct': 0.05,
        'stop_loss_pct': 0.03,
        'time_stop_days': 3,
        'rsi_overbought': 70.0,
        'rsi_oversold': 30.0,
        'initial_capital': 100000.0
    }
    
    # 創建回測引擎
    backtest = TQQQBacktest2025Final(**config)
    
    # 獲取數據
    df = backtest.fetch_data(start_date, end_date)
    
    # 執行回測
    report = backtest.run_backtest(df, start_date, end_date)
    
    # 打印結果
    print("\n" + "="*70)
    print("回測結果摘要")
    print("="*70)
    print(f"回測期間: {report['backtest_period']['start']} 至 {report['backtest_period']['end']}")
    print(f"初始資金: ${report['initial_capital']:,.2f}")
    print(f"最終資金: ${report['final_capital']:,.2f}")
    print(f"總回報: ${report['total_return']:,.2f} ({report['total_return_pct']:.2f}%)")
    print(f"交易次數: {report['total_trades']}")
    print(f"勝率: {report['win_rate']:.2f}% ({report['winning_trades']}勝/{report['losing_trades']}負)")
    print(f"平均盈利: ${report['avg_profit']:.2f}")
    print(f"平均虧損: ${report['avg_loss']:.2f}")
    print(f"盈虧比: {report['profit_factor']:.2f}")
    print(f"最大回撤: {report['max_drawdown_pct']:.2f}%")
    print(f"夏普比率: {report['sharpe_ratio']:.2f}")
    print("="*70)
    
    # 保存報告
    output_dir = 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot/reports'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f"{output_dir}/backtest_2025_final.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n報告已保存: {output_file}")
    
    return report


if __name__ == '__main__':
    main()
