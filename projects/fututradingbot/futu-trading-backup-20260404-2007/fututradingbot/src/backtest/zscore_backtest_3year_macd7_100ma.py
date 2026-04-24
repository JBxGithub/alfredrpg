"""
Z-Score 策略回測 - 3年，閾值 1.65，MACD (7,14,7)，100日MA
回測期間: 2023-01-01 至 2026-01-01
策略: Z-Score Mean Reversion，閾值 upper=1.65, lower=-1.65
技術指標: MACD (7,14,7)，100日MA
初始資金: $100,000
倉位: 50%
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
import sys

# 添加項目路徑
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot')


class ZScoreBacktestStrategyV2:
    """
    Z-Score Mean Reversion 策略 V2
    - MACD: (7,14,7)
    - MA: 100日
    - 閾值: upper=1.65, lower=-1.65
    """
    
    def __init__(
        self,
        entry_zscore_upper: float = 1.65,     # 做空閾值
        entry_zscore_lower: float = -1.65,    # 做多閾值
        exit_zscore: float = 0.5,
        position_pct: float = 0.50,          # 50%倉位
        take_profit_pct: float = 0.05,       # 止盈5%
        stop_loss_pct: float = 0.03,         # 止損3%
        time_stop_days: int = 7,
        rsi_overbought: float = 70.0,
        rsi_oversold: float = 30.0,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.001
    ):
        self.config = {
            'entry_zscore_upper': entry_zscore_upper,
            'entry_zscore_lower': entry_zscore_lower,
            'exit_zscore': exit_zscore,
            'position_pct': position_pct,
            'take_profit_pct': take_profit_pct,
            'stop_loss_pct': stop_loss_pct,
            'time_stop_days': time_stop_days,
            'rsi_overbought': rsi_overbought,
            'rsi_oversold': rsi_oversold,
            'zscore_lookback': 60,
            'rsi_period': 14,
            'volume_ma_period': 20,
            'stop_loss_zscore': 3.5,
            'ma_period': 100  # 100日MA
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
        print(f"📊 正在獲取TQQQ數據: {start_date} 至 {end_date}")
        
        # 為了計算60日Z-Score和100日MA，需要額外獲取數據
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        extended_start = (start_dt - timedelta(days=150)).strftime('%Y-%m-%d')
        
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
        
        print(f"✅ 獲取到 {len(df)} 條數據")
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
        # Z-Score (60日)
        lookback = self.config['zscore_lookback']
        df['price_ma'] = df['close'].rolling(window=lookback).mean()
        df['price_std'] = df['close'].rolling(window=lookback).std()
        df['zscore'] = (df['close'] - df['price_ma']) / df['price_std']
        
        # RSI (14日)
        rsi_period = self.config['rsi_period']
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Volume MA (20日)
        df['volume_ma'] = df['volume'].rolling(window=self.config['volume_ma_period']).mean()

        # 100日移動平均線（市場狀態判斷）
        df['ma100'] = df['close'].rolling(window=self.config['ma_period']).mean()

        # MACD (7,14,7)
        exp1 = df['close'].ewm(span=7, adjust=False).mean()
        exp2 = df['close'].ewm(span=14, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=7, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def check_entry_signal(self, df: pd.DataFrame, idx: int) -> tuple:
        """
        檢查進場信號
        
        做多條件: Z-Score < -1.65 + RSI < 30 + 成交量確認
        做空條件: Z-Score > 1.65 + RSI > 70 + 成交量確認
        
        Returns: (signal_type, reason) 或 (None, "")
        """
        if idx < 1:
            return None, ""
            
        row = df.iloc[idx]
        
        if pd.isna(row['zscore']) or pd.isna(row['rsi']):
            return None, ""
        
        zscore = row['zscore']
        rsi = row['rsi']
        volume = row['volume']
        volume_ma = row['volume_ma']

        upper_threshold = self.config['entry_zscore_upper']
        lower_threshold = self.config['entry_zscore_lower']

        # 做多條件: Z-Score < -1.65 + RSI < 30 + 成交量確認
        if zscore < lower_threshold:
            if rsi < self.config['rsi_oversold']:
                if volume > volume_ma * 0.5:
                    return 'long', f"Z-Score({zscore:.2f})<{lower_threshold}+RSI({rsi:.1f})<30+量增"

        # 做空條件: Z-Score > 1.65 + RSI > 70 + 成交量確認
        if zscore > upper_threshold:
            if rsi > self.config['rsi_overbought']:
                if volume > volume_ma * 0.5:
                    return 'short', f"Z-Score({zscore:.2f})>{upper_threshold}+RSI({rsi:.1f})>70+量增"
        
        return None, ""
    
    def check_exit_signal(self, df: pd.DataFrame, idx: int, position: dict) -> tuple:
        """
        檢查出場信號
        
        止盈: 5%
        止損: 3%
        Z-Score回歸: ±0.5
        時間止損: 7天
        
        Returns: (should_exit, reason)
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
        
        # Z-Score回歸檢查 (±0.5)
        if abs(zscore) < self.config['exit_zscore']:
            return True, f"Z-Score回歸({zscore:.2f})"
        
        # 時間止損檢查
        current_time = df.index[idx]
        days_held = (current_time - entry_time).days
        if days_held >= self.config['time_stop_days']:
            return True, f"時間止損({days_held}天)"
        
        return False, ""
    
    def run_backtest(self, df: pd.DataFrame, start_date: str, end_date: str) -> dict:
        """執行回測"""
        print(f"\n🚀 開始回測...")
        print(f"   期間: {start_date} 至 {end_date}")
        print(f"   初始資金: ${self.initial_capital:,.2f}")
        
        # 計算指標
        df = self.calculate_indicators(df)
        
        # 過濾回測期間
        df = df[df.index >= start_date]
        df = df[df.index <= end_date]
        
        print(f"   回測數據點: {len(df)}")
        
        # 逐日回測
        for i in range(len(df)):
            current_time = df.index[i]
            
            # 檢查平倉條件
            if self.position:
                should_exit, exit_reason = self.check_exit_signal(df, i, self.position)
                
                if should_exit:
                    self._close_position(df, i, exit_reason)
            
            # 檢查開倉條件（無持倉時）
            if not self.position:
                signal_type, reason = self.check_entry_signal(df, i)
                
                if signal_type:
                    self._open_position(df, i, signal_type, reason)
            
            # 記錄權益曲線
            self._record_equity(df, i)
        
        # 回測結束，平倉所有持倉
        if self.position:
            self._close_position(df, len(df)-1, "回測結束平倉")
        
        return self._generate_report(df)
    
    def _open_position(self, df: pd.DataFrame, idx: int, direction: str, reason: str):
        """開倉"""
        current_price = df.iloc[idx]['close']
        current_time = df.index[idx]
        
        # 考慮滑點
        if direction == 'long':
            executed_price = current_price * (1 + self.slippage)
        else:
            executed_price = current_price * (1 - self.slippage)
        
        # 計算倉位大小（基於初始資本的50%）
        position_value = self.initial_capital * self.config['position_pct']
        shares = int(position_value / executed_price)
        
        if shares < 1:
            return
        
        # 計算成本
        cost = shares * executed_price
        commission = cost * self.commission_rate
        total_cost = cost + commission
        
        if total_cost > self.cash:
            return
        
        # 更新資金
        self.cash -= total_cost
        
        # 記錄持倉
        self.position = {
            'direction': direction,
            'entry_price': executed_price,
            'shares': shares,
            'entry_time': current_time,
            'entry_reason': reason,
            'commission': commission
        }
        
        print(f"📈 開倉 [{direction.upper()}] {current_time.strftime('%Y-%m-%d')}: "
              f"價格=${executed_price:.2f}, 股數={shares}, 原因={reason}")
    
    def _close_position(self, df: pd.DataFrame, idx: int, reason: str):
        """平倉"""
        if not self.position:
            return
        
        current_price = df.iloc[idx]['close']
        current_time = df.index[idx]
        
        # 考慮滑點
        if self.position['direction'] == 'long':
            executed_price = current_price * (1 - self.slippage)
        else:
            executed_price = current_price * (1 + self.slippage)
        
        shares = self.position['shares']
        entry_price = self.position['entry_price']
        direction = self.position['direction']
        entry_time = self.position['entry_time']
        entry_commission = self.position['commission']
        
        # 計算收益
        if direction == 'long':
            pnl = (executed_price - entry_price) * shares
        else:
            pnl = (entry_price - executed_price) * shares
        
        # 扣除手續費
        exit_commission = shares * executed_price * self.commission_rate
        total_commission = entry_commission + exit_commission
        pnl -= total_commission
        
        pnl_pct = pnl / (entry_price * shares) * 100
        
        # 更新資金
        proceeds = shares * executed_price - exit_commission
        self.cash += proceeds
        
        # 記錄交易
        days_held = (current_time - entry_time).days
        trade = {
            'entry_time': entry_time,
            'exit_time': current_time,
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': executed_price,
            'shares': shares,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': reason,
            'days_held': days_held
        }
        self.trades.append(trade)
        
        emoji = "✅" if pnl > 0 else "❌"
        print(f"{emoji} 平倉 [{direction.upper()}] {current_time.strftime('%Y-%m-%d')}: "
              f"價格=${executed_price:.2f}, 盈虧=${pnl:.2f}({pnl_pct:.2f}%), "
              f"原因={reason}, 持倉={days_held}天")
        
        # 清空持倉
        self.position = None
    
    def _record_equity(self, df: pd.DataFrame, idx: int):
        """記錄權益曲線"""
        current_time = df.index[idx]
        current_price = df.iloc[idx]['close']
        
        # 計算總權益
        if self.position:
            position_value = self.position['shares'] * current_price
            total_equity = self.cash + position_value
        else:
            total_equity = self.cash
        
        self.equity_curve.append({
            'timestamp': current_time,
            'equity': total_equity,
            'cash': self.cash,
            'position_value': position_value if self.position else 0
        })
    
    def _generate_report(self, df: pd.DataFrame) -> dict:
        """生成回測報告"""
        # 計算統計數據
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        
        long_trades = [t for t in self.trades if t['direction'] == 'long']
        short_trades = [t for t in self.trades if t['direction'] == 'short']
        
        winning_long = [t for t in long_trades if t['pnl'] > 0]
        winning_short = [t for t in short_trades if t['pnl'] > 0]
        
        # 計算指標
        total_return = self.cash - self.initial_capital
        total_return_pct = (total_return / self.initial_capital) * 100
        
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        long_win_rate = (len(winning_long) / len(long_trades) * 100) if long_trades else 0
        short_win_rate = (len(winning_short) / len(short_trades) * 100) if short_trades else 0
        
        avg_profit = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        profit_factor = (sum(t['pnl'] for t in winning_trades) / abs(sum(t['pnl'] for t in losing_trades))) if losing_trades and sum(t['pnl'] for t in losing_trades) != 0 else float('inf')
        
        # 計算最大回撤
        equity_df = pd.DataFrame(self.equity_curve)
        if not equity_df.empty:
            equity_df['peak'] = equity_df['equity'].cummax()
            equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
            max_drawdown_pct = equity_df['drawdown'].min()
        else:
            max_drawdown_pct = 0
        
        # 計算夏普比率
        if len(equity_df) > 1:
            equity_df['returns'] = equity_df['equity'].pct_change().dropna()
            volatility = equity_df['returns'].std() * np.sqrt(252) * 100
            sharpe_ratio = (total_return_pct / 100) / (volatility / 100) if volatility != 0 else 0
        else:
            volatility = 0
            sharpe_ratio = 0
        
        report = {
            'strategy_name': 'Z-Score Mean Reversion V2 (MACD 7,14,7 + 100MA)',
            'backtest_period': {
                'start': str(df.index[0]),
                'end': str(df.index[-1])
            },
            'strategy_config': self.config,
            'initial_capital': self.initial_capital,
            'final_capital': self.cash,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'long_trades': len(long_trades),
            'short_trades': len(short_trades),
            'long_win_rate': long_win_rate,
            'short_win_rate': short_win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'volatility': volatility,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
        
        return report


def main():
    """主函數 - 3年回測"""
    print("="*70)
    print("Z-Score 策略回測 - 3年（MACD 7,14,7 + 100日MA）")
    print("="*70)

    # 回測期間: 2023-2026年
    start_date = '2023-01-01'
    end_date = '2026-01-01'

    # 策略參數
    config = {
        'entry_zscore_upper': 1.65,      # 做空閾值
        'entry_zscore_lower': -1.65,     # 做多閾值
        'exit_zscore': 0.5,
        'position_pct': 0.50,           # 50%倉位
        'take_profit_pct': 0.05,        # 止盈5%
        'stop_loss_pct': 0.03,          # 止損3%
        'time_stop_days': 7,            # 時間止損7天
        'rsi_overbought': 70.0,         # RSI超買70
        'rsi_oversold': 30.0,           # RSI超賣30
        'initial_capital': 100000.0
    }

    # 創建回測引擎
    backtest = ZScoreBacktestStrategyV2(**config)

    # 獲取數據
    df = backtest.fetch_data(start_date, end_date)

    # 執行回測
    report = backtest.run_backtest(df, start_date, end_date)

    # 打印結果
    print("\n" + "="*70)
    print("📊 3年回測結果摘要（MACD 7,14,7 + 100日MA）")
    print("="*70)
    print(f"📅 回測期間: {report['backtest_period']['start'][:10]} 至 {report['backtest_period']['end'][:10]}")
    print(f"📋 策略名稱: {report['strategy_name']}")
    print(f"🎯 Z-Score閾值: upper={report['strategy_config']['entry_zscore_upper']}, lower={report['strategy_config']['entry_zscore_lower']}")
    print(f"📈 RSI閾值: 超買={report['strategy_config']['rsi_overbought']}, 超賣={report['strategy_config']['rsi_oversold']}")
    print(f"⏱️  時間止損: {report['strategy_config']['time_stop_days']}天")
    print(f"💰 倉位: {report['strategy_config']['position_pct']*100}%")
    print(f"📊 初始資金: ${report['initial_capital']:,.2f}")
    print(f"📊 最終資金: ${report['final_capital']:,.2f}")
    print(f"💵 總回報: ${report['total_return']:,.2f} ({report['total_return_pct']:+.2f}%)")
    print(f"🔄 交易次數: {report['total_trades']}")
    print(f"✅ 勝率: {report['win_rate']:.2f}% ({report['winning_trades']}勝/{report['losing_trades']}負)")
    print(f"📈 做多交易: {report['long_trades']}次 (勝率: {report['long_win_rate']:.2f}%)")
    print(f"📉 做空交易: {report['short_trades']}次 (勝率: {report['short_win_rate']:.2f}%)")
    print(f"💚 平均盈利: ${report['avg_profit']:.2f}")
    print(f"❤️  平均虧損: ${report['avg_loss']:.2f}")
    print(f"⚖️  盈虧比: {report['profit_factor']:.2f}")
    print(f"📉 最大回撤: {report['max_drawdown_pct']:.2f}%")
    print(f"🎯 夏普比率: {report['sharpe_ratio']:.2f}")
    print("="*70)

    # 保存報告
    output_dir = 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot/reports'
    os.makedirs(output_dir, exist_ok=True)

    # 轉換為可序列化的格式
    report_serializable = {
        'strategy_name': report['strategy_name'],
        'backtest_period': report['backtest_period'],
        'strategy_config': report['strategy_config'],
        'initial_capital': report['initial_capital'],
        'final_capital': report['final_capital'],
        'total_return': report['total_return'],
        'total_return_pct': report['total_return_pct'],
        'total_trades': report['total_trades'],
        'winning_trades': report['winning_trades'],
        'losing_trades': report['losing_trades'],
        'win_rate': report['win_rate'],
        'long_trades': report['long_trades'],
        'short_trades': report['short_trades'],
        'long_win_rate': report['long_win_rate'],
        'short_win_rate': report['short_win_rate'],
        'avg_profit': report['avg_profit'],
        'avg_loss': report['avg_loss'],
        'profit_factor': report['profit_factor'],
        'max_drawdown_pct': report['max_drawdown_pct'],
        'sharpe_ratio': report['sharpe_ratio'],
        'volatility': report['volatility'],
        'trades': [
            {
                'entry_time': str(t['entry_time']),
                'exit_time': str(t['exit_time']),
                'direction': t['direction'],
                'entry_price': t['entry_price'],
                'exit_price': t['exit_price'],
                'shares': t['shares'],
                'pnl': t['pnl'],
                'pnl_pct': t['pnl_pct'],
                'exit_reason': t['exit_reason'],
                'days_held': t['days_held']
            }
            for t in report['trades']
        ],
        'equity_curve': [
            {
                'timestamp': str(e['timestamp']),
                'equity': e['equity'],
                'cash': e['cash'],
                'position_value': e['position_value']
            }
            for e in report['equity_curve']
        ]
    }

    output_file = f"{output_dir}/zscore_backtest_3year_macd7_100ma.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report_serializable, f, indent=2, ensure_ascii=False)

    print(f"\n💾 報告已保存: {output_file}")

    return report


if __name__ == '__main__':
    main()
