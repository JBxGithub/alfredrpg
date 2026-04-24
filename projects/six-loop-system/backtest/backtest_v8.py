"""
六循環系統回測引擎 - V8 放寬止盈版
實現靚仔要求:
1. 日間止損: QQQ 入場價 -3%
2. 高位回落止損: 從持倉高位回落 -3%
3. 止盈: TQQQ +15% (放寬)
4. 7天評估: 牛市續持(>60)，熊市觀望
5. 冷卻期: 止損後1日先再買入
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import json
import os

class SixLoopBacktestV8:
    """六循環回測 V8 - 放寬止盈版"""
    
    def __init__(self, start_date='2019-01-01', end_date='2024-12-31', initial_capital=100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = 0
        self.entry_price = 0
        self.entry_qqq_price = 0
        self.highest_qqq_price = 0
        self.entry_date = None
        self.holding_days = 0
        self.cooldown_days = 0
        self.trades = []
        
        # V8: 放寬止盈到 15%
        self.qqq_stop_loss = 0.03           # 日間止損: QQQ -3%
        self.qqq_trailing_stop = 0.03       # 高位回落止損: -3%
        self.take_profit_pct = 0.15         # 止盈: TQQQ +15% (放寬！)
        self.reeval_days = 7                # 7天重新評估
        self.cooldown_period = 1            # 1天冷卻期
        self.max_position_pct = 0.95
        
        # 交易成本
        self.commission_rate = 0.001
        self.slippage = 0.001
        
    def fetch_data(self):
        """獲取歷史數據"""
        print(f"獲取數據: {self.start_date} 至 {self.end_date}")
        
        qqq = yf.Ticker("QQQ")
        self.qqq_data = qqq.history(start=self.start_date, end=self.end_date)
        
        tqqq = yf.Ticker("TQQQ")
        self.tqqq_data = tqqq.history(start=self.start_date, end=self.end_date)
        
        print(f"QQQ數據: {len(self.qqq_data)} 天")
        print(f"TQQQ數據: {len(self.tqqq_data)} 天")
        
        return self.qqq_data, self.tqqq_data
    
    def calculate_indicators(self, data, idx):
        """計算技術指標"""
        if idx < 50:
            return None
        
        window = data.iloc[max(0, idx-200):idx+1]
        current_price = data['Close'].iloc[idx]
        
        ma20 = window['Close'].iloc[-20:].mean()
        ma50 = window['Close'].iloc[-50:].mean()
        ma200 = window['Close'].mean() if len(window) >= 200 else ma50
        
        delta = window['Close'].diff()
        gain = (delta.where(delta > 0, 0)).iloc[-14:].mean()
        loss = (-delta.where(delta < 0, 0)).iloc[-14:].mean()
        rs = gain / loss if loss != 0 else 1
        rsi = 100 - (100 / (1 + rs))
        
        ema12 = window['Close'].ewm(span=12).mean().iloc[-1]
        ema26 = window['Close'].ewm(span=26).mean().iloc[-1]
        macd = ema12 - ema26
        
        momentum_20 = (current_price - window['Close'].iloc[-20]) / window['Close'].iloc[-20]
        
        return {
            'price': current_price,
            'ma20': ma20,
            'ma50': ma50,
            'ma200': ma200,
            'rsi': rsi,
            'macd': macd,
            'momentum_20': momentum_20
        }
    
    def calculate_absolute_score(self, indicators):
        """計算Absolute評分"""
        if not indicators:
            return 50
        
        scores = []
        scores.append(70 if indicators['price'] > indicators['ma20'] else 30)
        scores.append(80 if indicators['price'] > indicators['ma50'] else 20)
        scores.append(90 if indicators['price'] > indicators['ma200'] else 10)
        
        if indicators['momentum_20'] > 0.05:
            scores.append(80)
        elif indicators['momentum_20'] > 0:
            scores.append(60)
        else:
            scores.append(40)
        
        scores.append(70 if indicators['macd'] > 0 else 30)
        
        return np.mean(scores)
    
    def calculate_reference_score(self, indicators):
        """計算Reference評分"""
        if not indicators:
            return 50
        
        scores = []
        rsi = indicators['rsi']
        if rsi < 30:
            scores.append(80)
        elif rsi > 70:
            scores.append(20)
        else:
            scores.append(50)
        
        scores.extend([70, 60, 50, 55])
        
        return np.mean(scores)
    
    def run_backtest(self):
        """運行回測"""
        print("\n" + "="*60)
        print("六循環系統回測 - V8 (放寬止盈版)")
        print("="*60)
        print(f"日間止損: QQQ 入場價 -3%")
        print(f"高位回落止損: 從持倉高位回落 -3%")
        print(f"止盈: TQQQ +15% (放寬！)")
        print(f"7天評估: 牛市續持(>60)")
        print(f"冷卻期: 止損後{self.cooldown_period}日先再買入")
        print(f"交易成本: 手續費 {self.commission_rate*100}% + 滑點 {self.slippage*100}%")
        
        self.fetch_data()
        
        common_dates = self.qqq_data.index.intersection(self.tqqq_data.index)
        qqq_aligned = self.qqq_data.loc[common_dates]
        tqqq_aligned = self.tqqq_data.loc[common_dates]
        
        print(f"\n回測期間: {common_dates[0]} 至 {common_dates[-1]}")
        print(f"總交易日: {len(common_dates)}")
        
        daily_results = []
        total_commission = 0
        
        for i in range(len(common_dates)):
            date = common_dates[i]
            qqq_price = qqq_aligned['Close'].iloc[i]
            tqqq_price = tqqq_aligned['Close'].iloc[i]
            
            indicators = self.calculate_indicators(qqq_aligned, i)
            
            if indicators:
                abs_score = self.calculate_absolute_score(indicators)
                ref_score = self.calculate_reference_score(indicators)
            else:
                abs_score = ref_score = 50
            
            signal = 'HOLD'
            final_score = abs_score * 0.6 + ref_score * 0.4
            stop_reason = None
            
            # 更新冷卻期
            if self.cooldown_days > 0:
                self.cooldown_days -= 1
            
            # ===== V8 核心邏輯 =====
            if self.positions > 0:
                self.holding_days += 1
                
                if qqq_price > self.highest_qqq_price:
                    self.highest_qqq_price = qqq_price
                
                qqq_change_from_entry = (qqq_price - self.entry_qqq_price) / self.entry_qqq_price
                qqq_change_from_high = (qqq_price - self.highest_qqq_price) / self.highest_qqq_price
                tqqq_change = (tqqq_price - self.entry_price) / self.entry_price
                
                # 日間止損: -3%
                if qqq_change_from_entry <= -self.qqq_stop_loss:
                    signal = 'SELL_QQQ_STOP'
                    stop_reason = f'QQQ從入場跌{abs(qqq_change_from_entry)*100:.1f}%'
                    self.cooldown_days = self.cooldown_period
                
                # 高位回落止損: -3%
                elif qqq_change_from_high <= -self.qqq_trailing_stop:
                    signal = 'SELL_TRAILING_STOP'
                    stop_reason = f'從高位回落{abs(qqq_change_from_high)*100:.1f}%'
                    self.cooldown_days = self.cooldown_period
                
                # V8: 放寬止盈到 +15%
                elif tqqq_change >= self.take_profit_pct:
                    signal = 'SELL_PROFIT'
                    stop_reason = f'TQQQ盈利{tqqq_change*100:.1f}% (止盈15%)'
                
                # 7天重新評估
                elif self.holding_days >= self.reeval_days:
                    if final_score > 60:
                        signal = 'HOLD_BULL_CONTINUE'
                        self.holding_days = 0
                    else:
                        signal = 'SELL_REEVALUATE'
                        stop_reason = '7天重估熊市'
                
                else:
                    signal = 'HOLD'
            
            else:
                if self.cooldown_days > 0:
                    signal = 'HOLD_COOLDOWN'
                elif final_score > 60:
                    signal = 'BUY'
                else:
                    signal = 'HOLD'
            
            # 執行交易
            if signal == 'BUY' and self.positions == 0:
                shares = int(self.capital * self.max_position_pct / tqqq_price)
                if shares > 0:
                    commission = shares * tqqq_price * self.commission_rate
                    slippage_cost = shares * tqqq_price * self.slippage
                    total_cost = commission + slippage_cost
                    
                    self.positions = shares
                    self.entry_price = tqqq_price
                    self.entry_qqq_price = qqq_price
                    self.highest_qqq_price = qqq_price
                    self.entry_date = date
                    self.holding_days = 0
                    total_commission += total_cost
                    
                    self.trades.append({
                        'date': date,
                        'action': 'BUY',
                        'tqqq_price': tqqq_price,
                        'qqq_price': qqq_price,
                        'shares': shares,
                        'commission': commission,
                        'slippage': slippage_cost,
                        'abs_score': abs_score,
                        'ref_score': ref_score,
                        'final_score': final_score
                    })
                    
            elif 'SELL' in signal and self.positions > 0:
                gross_pnl = (tqqq_price - self.entry_price) * self.positions
                commission = self.positions * tqqq_price * self.commission_rate
                slippage_cost = self.positions * tqqq_price * self.slippage
                total_cost = commission + slippage_cost
                
                net_pnl = gross_pnl - total_cost
                self.capital += net_pnl
                total_commission += total_cost
                
                qqq_change_entry = (qqq_price - self.entry_qqq_price) / self.entry_qqq_price
                qqq_change_high = (qqq_price - self.highest_qqq_price) / self.highest_qqq_price
                tqqq_change = (tqqq_price - self.entry_price) / self.entry_price
                
                self.trades.append({
                    'date': date,
                    'action': signal,
                    'tqqq_price': tqqq_price,
                    'qqq_price': qqq_price,
                    'shares': self.positions,
                    'gross_pnl': gross_pnl,
                    'net_pnl': net_pnl,
                    'commission': commission,
                    'slippage': slippage_cost,
                    'qqq_change_from_entry': qqq_change_entry,
                    'qqq_change_from_high': qqq_change_high,
                    'tqqq_change': tqqq_change,
                    'holding_days': self.holding_days,
                    'highest_qqq': self.highest_qqq_price,
                    'stop_reason': stop_reason,
                    'abs_score': abs_score,
                    'ref_score': ref_score,
                    'final_score': final_score
                })
                
                self.positions = 0
                self.entry_price = 0
                self.entry_qqq_price = 0
                self.highest_qqq_price = 0
                self.holding_days = 0
            
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
                'portfolio_value': portfolio_value,
                'holding_days': self.holding_days if self.positions > 0 else 0,
                'cooldown_days': self.cooldown_days
            })
        
        self.daily_results = pd.DataFrame(daily_results)
        self.total_commission = total_commission
        return self.daily_results
    
    def calculate_metrics(self):
        """計算回測指標"""
        print("\n" + "="*60)
        print("回測結果 - V8 (放寬止盈版)")
        print("="*60)
        
        final_value = self.daily_results['portfolio_value'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        years = (self.daily_results['date'].iloc[-1] - self.daily_results['date'].iloc[0]).days / 365.25
        annualized_return = ((final_value / self.initial_capital) ** (1/years) - 1) * 100
        
        self.daily_results['cummax'] = self.daily_results['portfolio_value'].cummax()
        self.daily_results['drawdown'] = (self.daily_results['portfolio_value'] - self.daily_results['cummax']) / self.daily_results['cummax']
        max_drawdown = self.daily_results['drawdown'].min() * 100
        
        daily_returns = self.daily_results['portfolio_value'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = (daily_returns.mean() * 252 - 0.02) / (daily_returns.std() * np.sqrt(252))
        
        buy_trades = [t for t in self.trades if t['action'] == 'BUY']
        sell_trades = [t for t in self.trades if 'SELL' in t['action']]
        winning_trades = [t for t in sell_trades if t.get('net_pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('net_pnl', 0) <= 0]
        
        win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0
        avg_win = np.mean([t['tqqq_change'] for t in winning_trades]) * 100 if winning_trades else 0
        avg_loss = np.mean([t['tqqq_change'] for t in losing_trades]) * 100 if losing_trades else 0
        avg_holding_days = np.mean([t.get('holding_days', 0) for t in sell_trades]) if sell_trades else 0
        
        print(f"\n【基本指標】")
        print(f"初始資金: ${self.initial_capital:,.2f}")
        print(f"最終價值: ${final_value:,.2f}")
        print(f"總回報: {total_return:.2f}%")
        print(f"年化回報: {annualized_return:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        print(f"總交易成本: ${self.total_commission:,.2f}")
        
        print(f"\n【交易統計】")
        print(f"總交易次數: {len(sell_trades)}")
        print(f"勝率: {win_rate:.1f}%")
        print(f"平均盈利: {avg_win:.2f}%")
        print(f"平均虧損: {avg_loss:.2f}%")
        print(f"平均持倉: {avg_holding_days:.1f} 天")
        
        qqq_stops = [t for t in sell_trades if 'QQQ_STOP' in t['action']]
        trailing_stops = [t for t in sell_trades if 'TRAILING' in t['action']]
        profit_stops = [t for t in sell_trades if 'PROFIT' in t['action']]
        reeval_stops = [t for t in sell_trades if 'REEVALUATE' in t['action']]
        bull_continue = len([s for s in self.daily_results['signal'] if 'BULL_CONTINUE' in s])
        
        print(f"\n【賣出類型】")
        print(f"日間止損 (QQQ-3%): {len(qqq_stops)} 次")
        print(f"高位回落止損 (-3%): {len(trailing_stops)} 次")
        print(f"止盈 (+15%): {len(profit_stops)} 次")
        print(f"7天重估賣出: {len(reeval_stops)} 次")
        print(f"牛市續持次數: {bull_continue} 次")
        
        buy_hold_shares = self.initial_capital / self.tqqq_data['Close'].iloc[0]
        buy_hold_value = buy_hold_shares * self.tqqq_data['Close'].iloc[-1]
        buy_hold_return = (buy_hold_value - self.initial_capital) / self.initial_capital * 100
        
        print(f"\n【策略對比】")
        print(f"策略回報: {total_return:.2f}%")
        print(f"買入持有: {buy_hold_return:.2f}%")
        print(f"超額收益: {total_return - buy_hold_return:.2f}%")
        print(f"交易成本: ${self.total_commission:,.2f} ({self.total_commission/self.initial_capital*100:.2f}%)")
        
        self.metrics = {
            'version': 'V8_放寬止盈版',
            'total_return_pct': total_return,
            'annualized_return_pct': annualized_return,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_commission': self.total_commission,
            'total_trades': len(sell_trades),
            'win_rate': win_rate,
            'avg_holding_days': avg_holding_days,
            'qqq_stops': len(qqq_stops),
            'trailing_stops': len(trailing_stops),
            'profit_stops': len(profit_stops),
            'reeval_stops': len(reeval_stops),
            'bull_continue_count': bull_continue,
            'buy_hold_return_pct': buy_hold_return,
            'outperformance': total_return - buy_hold_return
        }
        
        return self.metrics
    
    def save_results(self):
        """保存回測結果"""
        os.makedirs('backtest/results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.daily_results.to_csv(f'backtest/results/v8_daily_{timestamp}.csv', index=False)
        
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_df.to_csv(f'backtest/results/v8_trades_{timestamp}.csv', index=False)
        
        with open(f'backtest/results/v8_metrics_{timestamp}.json', 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        
        print(f"\n結果已保存: backtest/results/v8_*_{timestamp}.*")

def main():
    backtest = SixLoopBacktestV8(
        start_date='2019-01-01',
        end_date='2024-12-31',
        initial_capital=100000
    )
    
    backtest.run_backtest()
    backtest.calculate_metrics()
    backtest.save_results()
    
    print("\n✅ V8 放寬止盈版回測完成！")

if __name__ == '__main__':
    main()
