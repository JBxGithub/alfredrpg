"""
六循環系統回測引擎
使用5年歷史數據測試策略表現
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import json
import os

class SixLoopBacktest:
    """六循環系統回測引擎"""
    
    def __init__(self, start_date='2019-01-01', end_date='2024-12-31', initial_capital=100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = 0
        self.trades = []
        self.daily_pnl = []
        
        # 策略參數
        self.absolute_weights = {
            'nq200ma': 0.30,
            'nq50ma': 0.30,
            'nq20ema50ema': 0.20,
            'mtf': 0.10,
            'market_phase': 0.10
        }
        
        self.reference_weights = {
            'components_breadth': 0.20,
            'components_risk': 0.10,
            'technical_rsi': 0.15,
            'technical_atr': 0.10,
            'technical_zscore': 0.10,
            'technical_macd': 0.05,
            'technical_divergence': 0.05,
            'money_flow_futures': 0.15,
            'money_flow_etf': 0.10
        }
        
        # 風險參數
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.03
        self.max_position = 1000
        self.max_daily_loss = 500
        
    def fetch_data(self):
        """獲取歷史數據"""
        print(f"獲取數據: {self.start_date} 至 {self.end_date}")
        
        # 獲取QQQ數據 (作為NQ 100代理)
        qqq = yf.Ticker("QQQ")
        self.qqq_data = qqq.history(start=self.start_date, end=self.end_date)
        
        # 獲取TQQQ數據 (交易標的)
        tqqq = yf.Ticker("TQQQ")
        self.tqqq_data = tqqq.history(start=self.start_date, end=self.end_date)
        
        print(f"QQQ數據: {len(self.qqq_data)} 天")
        print(f"TQQQ數據: {len(self.tqqq_data)} 天")
        
        return self.qqq_data, self.tqqq_data
    
    def calculate_absolute_score(self, data, idx):
        """計算Absolute評分"""
        if idx < 200:
            return 50  # 數據不足，中性評分
        
        scores = {}
        current_price = data['Close'].iloc[idx]
        
        # 200MA
        ma200 = data['Close'].iloc[idx-200:idx].mean()
        scores['nq200ma'] = 100 if current_price > ma200 else 0
        
        # 50MA
        ma50 = data['Close'].iloc[idx-50:idx].mean()
        scores['nq50ma'] = 100 if current_price > ma50 else 0
        
        # 20EMA vs 50EMA
        ema20 = data['Close'].iloc[idx-20:idx].ewm(span=20).mean().iloc[-1]
        ema50 = data['Close'].iloc[idx-50:idx].ewm(span=50).mean().iloc[-1]
        scores['nq20ema50ema'] = 100 if ema20 > ema50 else 0
        
        # MTF (簡化版: 使用價格動量)
        momentum = (current_price - data['Close'].iloc[idx-20]) / data['Close'].iloc[idx-20]
        scores['mtf'] = min(100, max(0, 50 + momentum * 500))
        
        # Market Phase (簡化版)
        if current_price > ma50 > ma200:
            scores['market_phase'] = 100  # 上升趨勢
        elif current_price < ma50 < ma200:
            scores['market_phase'] = 0    # 下降趨勢
        else:
            scores['market_phase'] = 50   # 震盪
        
        # 加權計算
        absolute_score = sum(scores[k] * self.absolute_weights[k] for k in scores)
        return absolute_score
    
    def calculate_reference_score(self, data, idx):
        """計算Reference評分"""
        if idx < 20:
            return 50
        
        scores = {}
        
        # RSI (簡化計算)
        delta = data['Close'].iloc[idx-14:idx].diff()
        gain = (delta.where(delta > 0, 0)).mean()
        loss = (-delta.where(delta < 0, 0)).mean()
        rs = gain / loss if loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        scores['technical_rsi'] = rsi
        
        # ATR (簡化)
        high_low = data['High'].iloc[idx-14:idx] - data['Low'].iloc[idx-14:idx]
        atr = high_low.mean()
        current_atr = high_low.iloc[-1]
        scores['technical_atr'] = 100 if current_atr < atr else 50
        
        # Z-Score
        mean_price = data['Close'].iloc[idx-20:idx].mean()
        std_price = data['Close'].iloc[idx-20:idx].std()
        zscore = (data['Close'].iloc[idx] - mean_price) / std_price if std_price != 0 else 0
        scores['technical_zscore'] = min(100, max(0, 50 + zscore * 25))
        
        # 其他指標簡化
        scores['components_breadth'] = 70  # 假設成分股廣度良好
        scores['components_risk'] = 80     # 假設風險較低
        scores['technical_macd'] = 60
        scores['technical_divergence'] = 50
        scores['money_flow_futures'] = 65
        scores['money_flow_etf'] = 70
        
        # 加權計算
        reference_score = sum(scores[k] * self.reference_weights[k] for k in scores)
        return reference_score
    
    def generate_signal(self, absolute_score, reference_score):
        """生成交易信號"""
        final_score = absolute_score * 0.6 + reference_score * 0.4
        
        if final_score >= 70:
            return 'BUY', final_score
        elif final_score <= 30:
            return 'SELL', final_score
        else:
            return 'HOLD', final_score
    
    def run_backtest(self):
        """運行回測"""
        print("\n" + "="*60)
        print("六循環系統回測")
        print("="*60)
        
        # 獲取數據
        self.fetch_data()
        
        # 對齊數據
        common_dates = self.qqq_data.index.intersection(self.tqqq_data.index)
        qqq_aligned = self.qqq_data.loc[common_dates]
        tqqq_aligned = self.tqqq_data.loc[common_dates]
        
        print(f"\n回測期間: {common_dates[0]} 至 {common_dates[-1]}")
        print(f"總交易日: {len(common_dates)}")
        
        # 回測循環
        daily_results = []
        
        for i in range(len(common_dates)):
            date = common_dates[i]
            qqq_price = qqq_aligned['Close'].iloc[i]
            tqqq_price = tqqq_aligned['Close'].iloc[i]
            
            # 計算評分
            abs_score = self.calculate_absolute_score(qqq_aligned, i)
            ref_score = self.calculate_reference_score(qqq_aligned, i)
            signal, final_score = self.generate_signal(abs_score, ref_score)
            
            # 執行交易邏輯
            if signal == 'BUY' and self.positions == 0:
                # 計算可買入股數
                shares = min(self.max_position, int(self.capital * 0.95 / tqqq_price))
                if shares > 0:
                    self.positions = shares
                    entry_price = tqqq_price
                    self.trades.append({
                        'date': date,
                        'action': 'BUY',
                        'price': tqqq_price,
                        'shares': shares,
                        'signal_score': final_score
                    })
                    
            elif signal == 'SELL' and self.positions > 0:
                # 檢查止損止盈
                entry_trade = [t for t in self.trades if t['action'] == 'BUY'][-1]
                entry_price = entry_trade['price']
                pnl_pct = (tqqq_price - entry_price) / entry_price
                
                # 止盈止損檢查
                if pnl_pct <= -self.stop_loss_pct or pnl_pct >= self.take_profit_pct or signal == 'SELL':
                    pnl = (tqqq_price - entry_price) * self.positions
                    self.capital += pnl
                    self.trades.append({
                        'date': date,
                        'action': 'SELL',
                        'price': tqqq_price,
                        'shares': self.positions,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'signal_score': final_score
                    })
                    self.positions = 0
            
            # 記錄每日狀態
            portfolio_value = self.capital + (self.positions * tqqq_price if self.positions > 0 else 0)
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
                'portfolio_value': portfolio_value
            })
        
        self.daily_results = pd.DataFrame(daily_results)
        return self.daily_results
    
    def calculate_metrics(self):
        """計算回測指標"""
        print("\n" + "="*60)
        print("回測結果")
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
        
        # 夏普比率 (簡化版，假設無風險利率2%)
        daily_returns = self.daily_results['portfolio_value'].pct_change().dropna()
        sharpe_ratio = (daily_returns.mean() * 252 - 0.02) / (daily_returns.std() * np.sqrt(252))
        
        # 交易統計
        buy_trades = [t for t in self.trades if t['action'] == 'BUY']
        sell_trades = [t for t in self.trades if t['action'] == 'SELL']
        winning_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('pnl', 0) <= 0]
        
        win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0
        
        # 輸出結果
        print(f"\n初始資金: ${self.initial_capital:,.2f}")
        print(f"最終價值: ${final_value:,.2f}")
        print(f"總回報: {total_return:.2f}%")
        print(f"年化回報: {annualized_return:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        print(f"\n交易次數:")
        print(f"  買入: {len(buy_trades)}")
        print(f"  賣出: {len(sell_trades)}")
        print(f"  勝率: {win_rate:.1f}%")
        print(f"  盈利交易: {len(winning_trades)}")
        print(f"  虧損交易: {len(losing_trades)}")
        
        # 對比買入持有
        buy_hold_shares = self.initial_capital / self.tqqq_data['Close'].iloc[0]
        buy_hold_value = buy_hold_shares * self.tqqq_data['Close'].iloc[-1]
        buy_hold_return = (buy_hold_value - self.initial_capital) / self.initial_capital * 100
        
        print(f"\n對比買入持有策略:")
        print(f"  買入持有回報: {buy_hold_return:.2f}%")
        print(f"  策略超額收益: {total_return - buy_hold_return:.2f}%")
        
        # 保存結果
        self.metrics = {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return_pct': total_return,
            'annualized_return_pct': annualized_return,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': len(sell_trades),
            'win_rate': win_rate,
            'buy_hold_return_pct': buy_hold_return,
            'outperformance': total_return - buy_hold_return
        }
        
        return self.metrics
    
    def save_results(self):
        """保存回測結果"""
        os.makedirs('backtest/results', exist_ok=True)
        
        # 保存每日結果
        self.daily_results.to_csv(f'backtest/results/daily_results_{self.start_date}_{self.end_date}.csv')
        
        # 保存交易記錄
        trades_df = pd.DataFrame(self.trades)
        trades_df.to_csv(f'backtest/results/trades_{self.start_date}_{self.end_date}.csv')
        
        # 保存指標
        with open(f'backtest/results/metrics_{self.start_date}_{self.end_date}.json', 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        print(f"\n結果已保存到 backtest/results/")

def main():
    """主函數"""
    # 5年回測
    backtest = SixLoopBacktest(
        start_date='2019-01-01',
        end_date='2024-12-31',
        initial_capital=100000
    )
    
    # 運行回測
    backtest.run_backtest()
    
    # 計算指標
    backtest.calculate_metrics()
    
    # 保存結果
    backtest.save_results()
    
    print("\n回測完成！")

if __name__ == '__main__':
    main()
