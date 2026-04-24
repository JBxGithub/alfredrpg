"""
六循環系統回測 - V8 Plan B 多空雙向版
測試雙向交易策略
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import json
import os

class SixLoopBacktestV8Bidirectional:
    """六循環回測 V8 Plan B - 多空雙向版"""
    
    def __init__(self, start_date='2019-01-01', end_date='2024-12-31', initial_capital=100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        
        # 持倉狀態: 正數=多單(TQQQ), 負數=空單(SQQQ), 0=無持倉
        self.position = 0
        self.entry_price = 0
        self.entry_qqq_price = 0
        self.extreme_qqq_price = 0
        self.holding_days = 0
        self.cooldown_days = 0
        self.current_symbol = None
        self.trades = []
        
        # V8 Plan B 參數
        self.qqq_stop_loss = 0.03
        self.qqq_trailing_stop = 0.03
        self.take_profit_pct = 0.15
        self.reeval_days = 7
        self.cooldown_period = 1
        
        # 閾值
        self.long_threshold = 60
        self.short_threshold = 40
        self.continue_long = 60
        self.continue_short = 40
        
        # 交易成本
        self.commission_rate = 0.001
        self.slippage = 0.001
        
    def fetch_data(self):
        """獲取數據"""
        print(f"獲取數據: {self.start_date} 至 {self.end_date}")
        
        # QQQ (指數)
        qqq = yf.Ticker("QQQ")
        self.qqq_data = qqq.history(start=self.start_date, end=self.end_date)
        
        # TQQQ (3x 多)
        tqqq = yf.Ticker("TQQQ")
        self.tqqq_data = tqqq.history(start=self.start_date, end=self.end_date)
        
        # SQQQ (3x 空)
        sqqq = yf.Ticker("SQQQ")
        self.sqqq_data = sqqq.history(start=self.start_date, end=self.end_date)
        
        print(f"QQQ: {len(self.qqq_data)} 天")
        print(f"TQQQ: {len(self.tqqq_data)} 天")
        print(f"SQQQ: {len(self.sqqq_data)} 天")
        
        return self.qqq_data, self.tqqq_data, self.sqqq_data
    
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
        print("\n" + "="*70)
        print("六循環系統回測 - V8 Plan B (多空雙向版)")
        print("="*70)
        print(f"做多: 評分 >{self.long_threshold}, 標的 TQQQ")
        print(f"做空: 評分 <{self.short_threshold}, 標的 SQQQ")
        print(f"觀望: 評分 {self.short_threshold}-{self.long_threshold}, 持有現金")
        print(f"對稱止損: QQQ ±{self.qqq_stop_loss*100:.0f}%")
        print(f"對稱止盈: ETF ±{self.take_profit_pct*100:.0f}%")
        
        self.fetch_data()
        
        # 對齊數據
        common_dates = self.qqq_data.index.intersection(self.tqqq_data.index).intersection(self.sqqq_data.index)
        qqq_aligned = self.qqq_data.loc[common_dates]
        tqqq_aligned = self.tqqq_data.loc[common_dates]
        sqqq_aligned = self.sqqq_data.loc[common_dates]
        
        print(f"\n回測期間: {common_dates[0]} 至 {common_dates[-1]}")
        print(f"總交易日: {len(common_dates)}")
        
        daily_results = []
        total_commission = 0
        
        for i in range(len(common_dates)):
            date = common_dates[i]
            qqq_price = qqq_aligned['Close'].iloc[i]
            tqqq_price = tqqq_aligned['Close'].iloc[i]
            sqqq_price = sqqq_aligned['Close'].iloc[i]
            
            indicators = self.calculate_indicators(qqq_aligned, i)
            
            if indicators:
                abs_score = self.calculate_absolute_score(indicators)
                ref_score = self.calculate_reference_score(indicators)
            else:
                abs_score = ref_score = 50
            
            final_score = abs_score * 0.6 + ref_score * 0.4
            signal = 'HOLD'
            reason = None
            
            # 更新冷卻期
            if self.cooldown_days > 0:
                self.cooldown_days -= 1
            
            # ===== Plan B 核心邏輯 =====
            if self.position != 0:
                # 有持倉
                self.holding_days += 1
                
                # 更新極值
                if self.position > 0:  # 多單
                    if qqq_price > self.extreme_qqq_price:
                        self.extreme_qqq_price = qqq_price
                else:  # 空單
                    if qqq_price < self.extreme_qqq_price:
                        self.extreme_qqq_price = qqq_price
                
                qqq_change_from_entry = (qqq_price - self.entry_qqq_price) / self.entry_qqq_price
                
                if self.position > 0:  # 多單 TQQQ
                    qqq_change_from_extreme = (qqq_price - self.extreme_qqq_price) / self.extreme_qqq_price
                    etf_change = (tqqq_price - self.entry_price) / self.entry_price
                    
                    # 多單止損
                    if qqq_change_from_entry <= -self.qqq_stop_loss:
                        signal = 'SELL_LONG_STOP'
                        reason = f'多單止損: {qqq_change_from_entry*100:.1f}%'
                        self.cooldown_days = self.cooldown_period
                    
                    elif qqq_change_from_extreme <= -self.qqq_trailing_stop:
                        signal = 'SELL_LONG_TRAILING'
                        reason = f'多單回落: {qqq_change_from_extreme*100:.1f}%'
                        self.cooldown_days = self.cooldown_period
                    
                    elif etf_change >= self.take_profit_pct:
                        signal = 'SELL_LONG_PROFIT'
                        reason = f'多單止盈: {etf_change*100:.1f}%'
                    
                    elif self.holding_days >= self.reeval_days:
                        if final_score > self.continue_long:
                            signal = 'HOLD_LONG_CONTINUE'
                            self.holding_days = 0
                            reason = '牛市續持'
                        else:
                            signal = 'SELL_LONG_REEVAL'
                            reason = '多單重估賣出'
                    
                    else:
                        signal = 'HOLD_LONG'
                
                else:  # 空單 SQQQ
                    qqq_change_from_extreme = (qqq_price - self.extreme_qqq_price) / self.extreme_qqq_price
                    etf_change = (self.entry_price - sqqq_price) / self.entry_price
                    
                    # 空單止損 (QQQ上升)
                    if qqq_change_from_entry >= self.qqq_stop_loss:
                        signal = 'SELL_SHORT_STOP'
                        reason = f'空單止損: +{qqq_change_from_entry*100:.1f}%'
                        self.cooldown_days = self.cooldown_period
                    
                    elif qqq_change_from_extreme >= self.qqq_trailing_stop:
                        signal = 'SELL_SHORT_TRAILING'
                        reason = f'空單反彈: +{qqq_change_from_extreme*100:.1f}%'
                        self.cooldown_days = self.cooldown_period
                    
                    elif etf_change >= self.take_profit_pct:
                        signal = 'SELL_SHORT_PROFIT'
                        reason = f'空單止盈: {etf_change*100:.1f}%'
                    
                    elif self.holding_days >= self.reeval_days:
                        if final_score < self.continue_short:
                            signal = 'HOLD_SHORT_CONTINUE'
                            self.holding_days = 0
                            reason = '熊市續持'
                        else:
                            signal = 'SELL_SHORT_REEVAL'
                            reason = '空單重估賣出'
                    
                    else:
                        signal = 'HOLD_SHORT'
            
            else:
                # 無持倉
                if self.cooldown_days > 0:
                    signal = 'HOLD_COOLDOWN'
                
                elif final_score > self.long_threshold:
                    signal = 'BUY_LONG'
                    reason = f'評分{final_score:.1f}>60,做多'
                
                elif final_score < self.short_threshold:
                    signal = 'BUY_SHORT'
                    reason = f'評分{final_score:.1f}<40,做空'
                
                else:
                    signal = 'HOLD_CASH'
                    reason = f'評分{final_score:.1f},觀望'
            
            # 執行交易
            if 'BUY' in signal and self.position == 0:
                # 開新倉
                if signal == 'BUY_LONG':
                    etf_price = tqqq_price
                    symbol = 'TQQQ'
                    self.position = 1  # 標記多單
                else:
                    etf_price = sqqq_price
                    symbol = 'SQQQ'
                    self.position = -1  # 標記空單
                
                shares = int(self.capital * 0.95 / etf_price)
                
                if shares > 0:
                    commission = shares * etf_price * self.commission_rate
                    slippage_cost = shares * etf_price * self.slippage
                    total_cost = commission + slippage_cost
                    
                    # 實際持倉股數
                    self.position = shares if self.position > 0 else -shares
                    self.entry_price = etf_price
                    self.entry_qqq_price = qqq_price
                    self.extreme_qqq_price = qqq_price
                    self.current_symbol = symbol
                    self.holding_days = 0
                    total_commission += total_cost
                    
                    self.trades.append({
                        'date': date,
                        'action': signal,
                        'symbol': symbol,
                        'price': etf_price,
                        'shares': abs(shares),
                        'commission': commission,
                        'slippage': slippage_cost,
                        'abs_score': abs_score,
                        'ref_score': ref_score,
                        'final_score': final_score
                    })
            
            elif 'SELL' in signal and self.position != 0:
                # 平倉
                if self.position > 0:  # 平多單
                    etf_price = tqqq_price
                    gross_pnl = (etf_price - self.entry_price) * self.position
                else:  # 平空單
                    etf_price = sqqq_price
                    gross_pnl = (self.entry_price - etf_price) * abs(self.position)
                
                commission = abs(self.position) * etf_price * self.commission_rate
                slippage_cost = abs(self.position) * etf_price * self.slippage
                total_cost = commission + slippage_cost
                
                net_pnl = gross_pnl - total_cost
                self.capital += net_pnl
                total_commission += total_cost
                
                qqq_change = (qqq_price - self.entry_qqq_price) / self.entry_qqq_price
                
                if self.position > 0:
                    etf_change = (etf_price - self.entry_price) / self.entry_price
                else:
                    etf_change = (self.entry_price - etf_price) / self.entry_price
                
                self.trades.append({
                    'date': date,
                    'action': signal,
                    'symbol': self.current_symbol,
                    'price': etf_price,
                    'shares': abs(self.position),
                    'gross_pnl': gross_pnl,
                    'net_pnl': net_pnl,
                    'commission': commission,
                    'slippage': slippage_cost,
                    'qqq_change': qqq_change,
                    'etf_change': etf_change,
                    'holding_days': self.holding_days,
                    'stop_reason': reason,
                    'abs_score': abs_score,
                    'ref_score': ref_score,
                    'final_score': final_score
                })
                
                # 重置
                self.position = 0
                self.entry_price = 0
                self.entry_qqq_price = 0
                self.extreme_qqq_price = 0
                self.current_symbol = None
                self.holding_days = 0
            
            # 計算組合價值
            position_value = 0
            if self.position > 0:
                position_value = self.position * tqqq_price
            elif self.position < 0:
                position_value = abs(self.position) * sqqq_price
            
            portfolio_value = self.capital + position_value
            
            daily_results.append({
                'date': date,
                'qqq_price': qqq_price,
                'tqqq_price': tqqq_price,
                'sqqq_price': sqqq_price,
                'absolute_score': abs_score,
                'reference_score': ref_score,
                'final_score': final_score,
                'signal': signal,
                'capital': self.capital,
                'position': self.position,
                'position_value': position_value,
                'portfolio_value': portfolio_value,
                'holding_days': self.holding_days if self.position != 0 else 0,
                'cooldown_days': self.cooldown_days
            })
        
        self.daily_results = pd.DataFrame(daily_results)
        self.total_commission = total_commission
        return self.daily_results
    
    def calculate_metrics(self):
        """計算回測指標"""
        print("\n" + "="*70)
        print("回測結果 - V8 Plan B (多空雙向版)")
        print("="*70)
        
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
        
        # 交易統計
        buy_trades = [t for t in self.trades if 'BUY' in t['action']]
        sell_trades = [t for t in self.trades if 'SELL' in t['action']]
        winning_trades = [t for t in sell_trades if t.get('net_pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('net_pnl', 0) <= 0]
        
        win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0
        avg_win = np.mean([t['etf_change'] for t in winning_trades]) * 100 if winning_trades else 0
        avg_loss = np.mean([t['etf_change'] for t in losing_trades]) * 100 if losing_trades else 0
        avg_holding_days = np.mean([t.get('holding_days', 0) for t in sell_trades]) if sell_trades else 0
        
        # 多空分開統計
        long_trades = [t for t in sell_trades if 'LONG' in t['action']]
        short_trades = [t for t in sell_trades if 'SHORT' in t['action']]
        long_wins = len([t for t in long_trades if t.get('net_pnl', 0) > 0])
        short_wins = len([t for t in short_trades if t.get('net_pnl', 0) > 0])
        
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
        print(f"  多單: {len(long_trades)} 次 (勝率: {long_wins/len(long_trades)*100 if long_trades else 0:.1f}%)")
        print(f"  空單: {len(short_trades)} 次 (勝率: {short_wins/len(short_trades)*100 if short_trades else 0:.1f}%)")
        print(f"整體勝率: {win_rate:.1f}%")
        print(f"平均盈利: {avg_win:.2f}%")
        print(f"平均虧損: {avg_loss:.2f}%")
        print(f"平均持倉: {avg_holding_days:.1f} 天")
        
        # 賣出類型
        long_stops = [t for t in long_trades if 'STOP' in t['action'] or 'TRAILING' in t['action']]
        long_profits = [t for t in long_trades if 'PROFIT' in t['action']]
        short_stops = [t for t in short_trades if 'STOP' in t['action'] or 'TRAILING' in t['action']]
        short_profits = [t for t in short_trades if 'PROFIT' in t['action']]
        
        print(f"\n【賣出類型】")
        print(f"多單止損: {len(long_stops)} 次 | 多單止盈: {len(long_profits)} 次")
        print(f"空單止損: {len(short_stops)} 次 | 空單止盈: {len(short_profits)} 次")
        
        # 對比
        buy_hold_tqqq = (self.tqqq_data['Close'].iloc[-1] / self.tqqq_data['Close'].iloc[0] - 1) * 100
        buy_hold_sqqq = (self.sqqq_data['Close'].iloc[-1] / self.sqqq_data['Close'].iloc[0] - 1) * 100
        
        print(f"\n【策略對比】")
        print(f"Plan B 多空策略: {total_return:.2f}%")
        print(f"買入持有 TQQQ: {buy_hold_tqqq:.2f}%")
        print(f"買入持有 SQQQ: {buy_hold_sqqq:.2f}%")
        print(f"vs TQQQ: {total_return - buy_hold_tqqq:+.2f}%")
        print(f"vs SQQQ: {total_return - buy_hold_sqqq:+.2f}%")
        
        self.metrics = {
            'version': 'V8_PlanB_Bidirectional',
            'total_return_pct': total_return,
            'annualized_return_pct': annualized_return,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_commission': self.total_commission,
            'total_trades': len(sell_trades),
            'long_trades': len(long_trades),
            'short_trades': len(short_trades),
            'win_rate': win_rate,
            'avg_holding_days': avg_holding_days,
            'buy_hold_tqqq': buy_hold_tqqq,
            'buy_hold_sqqq': buy_hold_sqqq,
            'outperformance_vs_tqqq': total_return - buy_hold_tqqq,
            'outperformance_vs_sqqq': total_return - buy_hold_sqqq
        }
        
        return self.metrics
    
    def save_results(self):
        """保存結果"""
        os.makedirs('backtest/results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.daily_results.to_csv(f'backtest/results/v8_planb_daily_{timestamp}.csv', index=False)
        
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_df.to_csv(f'backtest/results/v8_planb_trades_{timestamp}.csv', index=False)
        
        with open(f'backtest/results/v8_planb_metrics_{timestamp}.json', 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        
        print(f"\n結果已保存: backtest/results/v8_planb_*_{timestamp}.*")

def main():
    backtest = SixLoopBacktestV8Bidirectional(
        start_date='2019-01-01',
        end_date='2024-12-31',
        initial_capital=100000
    )
    
    backtest.run_backtest()
    backtest.calculate_metrics()
    backtest.save_results()
    
    print("\n✅ V8 Plan B 多空回測完成！")

if __name__ == '__main__':
    main()
