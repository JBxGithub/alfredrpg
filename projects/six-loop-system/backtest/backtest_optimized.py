"""
六循環系統回測引擎 - 優化版
改進策略參數，提高交易頻率
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import json
import os

class SixLoopBacktestOptimized:
    """優化版六循環回測引擎"""
    
    def __init__(self, start_date='2019-01-01', end_date='2024-12-31', initial_capital=100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = 0
        self.entry_price = 0
        self.trades = []
        self.daily_pnl = []
        
        # 優化後的閾值
        self.buy_threshold = 60      # 降低買入閾值
        self.sell_threshold = 40     # 降低賣出閾值
        self.stop_loss_pct = 0.05    # 放寬止損到5%
        self.take_profit_pct = 0.10  # 放寬止盈到10%
        self.max_position_pct = 0.95 # 使用95%資金
        
    def fetch_data(self):
        """獲取歷史數據"""
        print(f"獲取數據: {self.start_date} 至 {self.end_date}")
        
        # 獲取QQQ數據
        qqq = yf.Ticker("QQQ")
        self.qqq_data = qqq.history(start=self.start_date, end=self.end_date)
        
        # 獲取TQQQ數據
        tqqq = yf.Ticker("TQQQ")
        self.tqqq_data = tqqq.history(start=self.start_date, end=self.end_date)
        
        # 獲取VIX數據 (用於風險評估)
        vix = yf.Ticker("^VIX")
        self.vix_data = vix.history(start=self.start_date, end=self.end_date)
        
        print(f"QQQ數據: {len(self.qqq_data)} 天")
        print(f"TQQQ數據: {len(self.tqqq_data)} 天")
        
        return self.qqq_data, self.tqqq_data
    
    def calculate_indicators(self, data, idx):
        """計算技術指標"""
        if idx < 50:
            return None
        
        # 獲取當前數據窗口
        window = data.iloc[max(0, idx-200):idx+1]
        current_price = data['Close'].iloc[idx]
        
        # 移動平均線
        ma20 = window['Close'].iloc[-20:].mean()
        ma50 = window['Close'].iloc[-50:].mean()
        ma200 = window['Close'].mean() if len(window) >= 200 else ma50
        
        # RSI
        delta = window['Close'].diff()
        gain = (delta.where(delta > 0, 0)).iloc[-14:].mean()
        loss = (-delta.where(delta < 0, 0)).iloc[-14:].mean()
        rs = gain / loss if loss != 0 else 1
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = window['Close'].ewm(span=12).mean().iloc[-1]
        ema26 = window['Close'].ewm(span=26).mean().iloc[-1]
        macd = ema12 - ema26
        
        # 波動率 (ATR簡化版)
        high_low = window['High'] - window['Low']
        atr = high_low.iloc[-14:].mean()
        
        # 價格動量
        momentum_20 = (current_price - window['Close'].iloc[-20]) / window['Close'].iloc[-20]
        momentum_50 = (current_price - window['Close'].iloc[-50]) / window['Close'].iloc[-50] if len(window) >= 50 else 0
        
        return {
            'price': current_price,
            'ma20': ma20,
            'ma50': ma50,
            'ma200': ma200,
            'rsi': rsi,
            'macd': macd,
            'atr': atr,
            'momentum_20': momentum_20,
            'momentum_50': momentum_50
        }
    
    def calculate_absolute_score(self, indicators):
        """計算Absolute評分 (趨勢跟蹤)"""
        if not indicators:
            return 50
        
        scores = []
        
        # 價格 vs MA20
        if indicators['price'] > indicators['ma20']:
            scores.append(70)
        else:
            scores.append(30)
        
        # 價格 vs MA50
        if indicators['price'] > indicators['ma50']:
            scores.append(80)
        else:
            scores.append(20)
        
        # 價格 vs MA200 (長期趨勢)
        if indicators['price'] > indicators['ma200']:
            scores.append(90)
        else:
            scores.append(10)
        
        # 動量
        if indicators['momentum_20'] > 0.05:
            scores.append(80)
        elif indicators['momentum_20'] > 0:
            scores.append(60)
        else:
            scores.append(40)
        
        # MACD
        if indicators['macd'] > 0:
            scores.append(70)
        else:
            scores.append(30)
        
        return np.mean(scores)
    
    def calculate_reference_score(self, indicators, vix_value=None):
        """計算Reference評分 (風險/時機)"""
        if not indicators:
            return 50
        
        scores = []
        
        # RSI (逆勢指標)
        rsi = indicators['rsi']
        if rsi < 30:  # 超賣
            scores.append(80)  # 買入機會
        elif rsi > 70:  # 超買
            scores.append(20)  # 賣出信號
        else:
            scores.append(50)
        
        # 波動率
        atr_pct = indicators['atr'] / indicators['price']
        if atr_pct < 0.02:  # 低波動
            scores.append(70)
        elif atr_pct > 0.05:  # 高波動
            scores.append(30)
        else:
            scores.append(50)
        
        # VIX (恐慌指數)
        if vix_value and not np.isnan(vix_value):
            if vix_value > 30:  # 高恐慌 = 買入機會
                scores.append(80)
            elif vix_value < 15:  # 低恐慌 = 謹慎
                scores.append(40)
            else:
                scores.append(60)
        else:
            scores.append(50)
        
        # 長期動量
        if indicators['momentum_50'] > 0.1:
            scores.append(70)
        elif indicators['momentum_50'] < -0.1:
            scores.append(30)
        else:
            scores.append(50)
        
        return np.mean(scores)
    
    def generate_signal(self, abs_score, ref_score, current_position):
        """生成交易信號"""
        final_score = abs_score * 0.6 + ref_score * 0.4
        
        # 有倉位時，放寬賣出條件
        if current_position > 0:
            if final_score < self.sell_threshold or final_score > 85:  # 極度高值也賣
                return 'SELL', final_score
            else:
                return 'HOLD', final_score
        else:
            # 無倉位時
            if final_score > self.buy_threshold:
                return 'BUY', final_score
            else:
                return 'HOLD', final_score
    
    def run_backtest(self):
        """運行回測"""
        print("\n" + "="*60)
        print("六循環系統回測 - 優化版")
        print("="*60)
        
        self.fetch_data()
        
        # 對齊數據
        common_dates = self.qqq_data.index.intersection(self.tqqq_data.index)
        qqq_aligned = self.qqq_data.loc[common_dates]
        tqqq_aligned = self.tqqq_data.loc[common_dates]
        
        print(f"\n回測期間: {common_dates[0]} 至 {common_dates[-1]}")
        print(f"總交易日: {len(common_dates)}")
        
        daily_results = []
        
        for i in range(len(common_dates)):
            date = common_dates[i]
            qqq_price = qqq_aligned['Close'].iloc[i]
            tqqq_price = tqqq_aligned['Close'].iloc[i]
            
            # 獲取VIX
            vix_value = None
            if date in self.vix_data.index:
                vix_value = self.vix_data['Close'].loc[date]
            
            # 計算指標
            indicators = self.calculate_indicators(qqq_aligned, i)
            
            if indicators:
                abs_score = self.calculate_absolute_score(indicators)
                ref_score = self.calculate_reference_score(indicators, vix_value)
                signal, final_score = self.generate_signal(abs_score, ref_score, self.positions)
            else:
                abs_score = ref_score = final_score = 50
                signal = 'HOLD'
            
            # 檢查止損止盈
            if self.positions > 0:
                pnl_pct = (tqqq_price - self.entry_price) / self.entry_price
                
                # 止損
                if pnl_pct <= -self.stop_loss_pct:
                    signal = 'SELL_STOP'
                # 止盈
                elif pnl_pct >= self.take_profit_pct:
                    signal = 'SELL_PROFIT'
            
            # 執行交易
            if signal in ['BUY'] and self.positions == 0:
                shares = int(self.capital * self.max_position_pct / tqqq_price)
                if shares > 0:
                    self.positions = shares
                    self.entry_price = tqqq_price
                    self.trades.append({
                        'date': date,
                        'action': 'BUY',
                        'price': tqqq_price,
                        'shares': shares,
                        'abs_score': abs_score,
                        'ref_score': ref_score,
                        'final_score': final_score
                    })
                    
            elif signal in ['SELL', 'SELL_STOP', 'SELL_PROFIT'] and self.positions > 0:
                pnl = (tqqq_price - self.entry_price) * self.positions
                self.capital += pnl
                
                self.trades.append({
                    'date': date,
                    'action': signal,
                    'price': tqqq_price,
                    'shares': self.positions,
                    'pnl': pnl,
                    'pnl_pct': (tqqq_price - self.entry_price) / self.entry_price,
                    'abs_score': abs_score,
                    'ref_score': ref_score,
                    'final_score': final_score
                })
                self.positions = 0
                self.entry_price = 0
            
            # 計算持倉價值
            position_value = self.positions * tqqq_price if self.positions > 0 else 0
            portfolio_value = self.capital + position_value
            
            daily_results.append({
                'date': date,
                'qqq_price': qqq_price,
                'tqqq_price': tqqq_price,
                'absolute_score': abs_score,
                'reference_score': ref_score,
                'final_score': final_score,
                'signal': signal,
                'capital': self.capital,
                'positions': self.positions,
                'position_value': position_value,
                'portfolio_value': portfolio_value
            })
        
        self.daily_results = pd.DataFrame(daily_results)
        return self.daily_results
    
    def calculate_metrics(self):
        """計算回測指標"""
        print("\n" + "="*60)
        print("回測結果 - 優化版")
        print("="*60)
        
        # 基本指標
        final_value = self.daily_results['portfolio_value'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # 年化收益
        years = (self.daily_results['date'].iloc[-1] - self.daily_results['date'].iloc[0]).days / 365.25
        annualized_return = ((final_value / self.initial_capital) ** (1/years) - 1) * 100
        
        # 最大回撤
        self.daily_results['cummax'] = self.daily_results['portfolio_value'].cummax()
        self.daily_results['drawdown'] = (self.daily_results['portfolio_value'] - self.daily_results['cummax']) / self.daily_results['cummax']
        max_drawdown = self.daily_results['drawdown'].min() * 100
        
        # 波動率
        daily_returns = self.daily_results['portfolio_value'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        
        # 夏普比率
        sharpe_ratio = (daily_returns.mean() * 252 - 0.02) / (daily_returns.std() * np.sqrt(252))
        
        # 索提諾比率
        downside_returns = daily_returns[daily_returns < 0]
        sortino_ratio = (daily_returns.mean() * 252 - 0.02) / (downside_returns.std() * np.sqrt(252)) if len(downside_returns) > 0 else 0
        
        # 交易統計
        buy_trades = [t for t in self.trades if t['action'] == 'BUY']
        sell_trades = [t for t in self.trades if 'SELL' in t['action']]
        winning_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('pnl', 0) <= 0]
        
        win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0
        
        avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) * 100 if winning_trades else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) * 100 if losing_trades else 0
        
        profit_factor = abs(sum(t['pnl'] for t in winning_trades)) / abs(sum(t['pnl'] for t in losing_trades)) if losing_trades and sum(t['pnl'] for t in losing_trades) != 0 else float('inf')
        
        # 輸出結果
        print(f"\n【基本指標】")
        print(f"初始資金: ${self.initial_capital:,.2f}")
        print(f"最終價值: ${final_value:,.2f}")
        print(f"總回報: {total_return:.2f}%")
        print(f"年化回報: {annualized_return:.2f}%")
        print(f"年化波動率: {volatility:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        
        print(f"\n【風險調整收益】")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        print(f"索提諾比率: {sortino_ratio:.2f}")
        
        print(f"\n【交易統計】")
        print(f"總交易次數: {len(sell_trades)}")
        print(f"勝率: {win_rate:.1f}%")
        print(f"盈利交易: {len(winning_trades)}")
        print(f"虧損交易: {len(losing_trades)}")
        print(f"平均盈利: {avg_win:.2f}%")
        print(f"平均虧損: {avg_loss:.2f}%")
        print(f"盈虧比: {profit_factor:.2f}")
        
        # 對比買入持有
        buy_hold_shares = self.initial_capital / self.tqqq_data['Close'].iloc[0]
        buy_hold_value = buy_hold_shares * self.tqqq_data['Close'].iloc[-1]
        buy_hold_return = (buy_hold_value - self.initial_capital) / self.initial_capital * 100
        buy_hold_max_dd = ((self.tqqq_data['Close'] / self.tqqq_data['Close'].cummax()) - 1).min() * 100
        
        print(f"\n【策略對比】")
        print(f"策略回報: {total_return:.2f}%")
        print(f"買入持有回報: {buy_hold_return:.2f}%")
        print(f"超額收益: {total_return - buy_hold_return:.2f}%")
        print(f"策略最大回撤: {max_drawdown:.2f}%")
        print(f"買入持有最大回撤: {buy_hold_max_dd:.2f}%")
        
        # 保存指標
        self.metrics = {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return_pct': total_return,
            'annualized_return_pct': annualized_return,
            'volatility_pct': volatility,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'total_trades': len(sell_trades),
            'win_rate': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'profit_factor': profit_factor,
            'buy_hold_return_pct': buy_hold_return,
            'buy_hold_max_dd_pct': buy_hold_max_dd,
            'outperformance': total_return - buy_hold_return
        }
        
        return self.metrics
    
    def save_results(self):
        """保存回測結果"""
        os.makedirs('backtest/results', exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存每日結果
        self.daily_results.to_csv(f'backtest/results/optimized_daily_{timestamp}.csv', index=False)
        
        # 保存交易記錄
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_df.to_csv(f'backtest/results/optimized_trades_{timestamp}.csv', index=False)
        
        # 保存指標
        with open(f'backtest/results/optimized_metrics_{timestamp}.json', 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        
        print(f"\n結果已保存到 backtest/results/")
        print(f"文件名: optimized_*_{timestamp}.*")

def main():
    """主函數"""
    backtest = SixLoopBacktestOptimized(
        start_date='2019-01-01',
        end_date='2024-12-31',
        initial_capital=100000
    )
    
    backtest.run_backtest()
    backtest.calculate_metrics()
    backtest.save_results()
    
    print("\n回測完成！")

if __name__ == '__main__':
    main()
