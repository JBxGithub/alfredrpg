"""
六循環系統回測 - V9.4 最終版
基於 V9 Asymmetric，優化執行層降低回撤：
1. 固定倉位上限: 90%
2. +10%盈利減倉50% → +20%再減30%
3. 保留 V9 核心評分系統和不對稱交易參數

回測表現 (2019-2024):
- 總回報: 2060.84%
- 年化回報: 66.99%
- 最大回撤: -64.93%
- 夏普比率: 1.64
- 勝率: 74.2%
- vs TQQQ Buy&Hold: +1263.33%
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import json
import os

class SixLoopBacktestV9_4:
    """
    六循環回測 V9.4 - 最終優化版
    
    核心改進:
    - 倉位管理: 90% 上限 (vs V9 原版 95%)
    - 盈利保護: +10%減倉50%, +20%再減30%
    - 不對稱參數: 多單穩健(-3%/-3%/+15%/7天), 空單敏捷(-2%/-2%/+10%/3天)
    """
    
    def __init__(self, start_date='2019-01-01', end_date='2024-12-31', initial_capital=100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        
        # 持倉狀態
        self.position = 0
        self.entry_price = 0
        self.entry_qqq_price = 0
        self.extreme_qqq_price = 0
        self.holding_days = 0
        self.cooldown_days = 0
        self.current_symbol = None
        self.trades = []
        
        # ===== V9.4 核心參數 =====
        # 倉位管理
        self.max_position_pct = 0.90  # 90% 倉位上限
        
        # 盈利減倉參數
        self.profit_level_1 = 0.10    # +10%
        self.reduce_1 = 0.50          # 減倉 50%
        self.profit_level_2 = 0.20    # +20%
        self.reduce_2 = 0.30          # 再減 30%
        
        # 多單參數 (穩健)
        self.long_stop_loss = 0.03    # -3%
        self.long_trailing = 0.03     # 回落 -3%
        self.long_take_profit = 0.15  # +15%
        self.long_reeval = 7          # 7天重估
        
        # 空單參數 (敏捷)
        self.short_stop_loss = 0.02   # +2% (更嚴格)
        self.short_trailing = 0.02    # 反彈 +2% (更嚴格)
        self.short_take_profit = 0.10 # +10% (更快)
        self.short_reeval = 3         # 3天重估 (更頻繁)
        
        # 閾值
        self.long_threshold = 60
        self.short_threshold = 40
        
        # 通用
        self.cooldown_period = 1
        self.commission_rate = 0.001
        self.slippage = 0.001
        
        # 狀態追蹤
        self.initial_shares = 0
        self.remaining_shares = 0
        self.profit_1_done = False
        self.profit_2_done = False
        
    def fetch_data(self):
        """獲取數據"""
        print(f"獲取數據: {self.start_date} 至 {self.end_date}")
        
        qqq = yf.Ticker("QQQ")
        self.qqq_data = qqq.history(start=self.start_date, end=self.end_date)
        
        tqqq = yf.Ticker("TQQQ")
        self.tqqq_data = tqqq.history(start=self.start_date, end=self.end_date)
        
        sqqq = yf.Ticker("SQQQ")
        self.sqqq_data = sqqq.history(start=self.start_date, end=self.end_date)
        
        vix = yf.Ticker("^VIX")
        self.vix_data = vix.history(start=self.start_date, end=self.end_date)
        
        print(f"QQQ: {len(self.qqq_data)} 天")
        print(f"TQQQ: {len(self.tqqq_data)} 天")
        print(f"SQQQ: {len(self.sqqq_data)} 天")
        print(f"VIX: {len(self.vix_data)} 天")
        
        return self.qqq_data, self.tqqq_data, self.sqqq_data, self.vix_data
    
    def calculate_indicators(self, data, idx):
        """計算技術指標 (V9 原版)"""
        if idx < 50:
            return None
        
        window = data.iloc[max(0, idx-200):idx+1]
        current_price = data['Close'].iloc[idx]
        
        # MA
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
        
        # 動量
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
        """Absolute Score (V9 原版)"""
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
        """Reference Score (V9 原版)"""
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
        """執行回測"""
        print("\n" + "="*70)
        print("六循環系統回測 - V9.4 最終版")
        print("="*70)
        print("【倉位管理】固定上限: 90%")
        print("【盈利保護】+10%減50% → +20%再減30%")
        print("【多單穩健】-3%/-3%/+15%/7天")
        print("【空單敏捷】-2%/-2%/+10%/3天")
        print("="*70)
        
        self.fetch_data()
        
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
            vix_price = self.vix_data['Close'].iloc[i] if i < len(self.vix_data) else 20
            
            indicators = self.calculate_indicators(qqq_aligned, i)
            
            if indicators:
                abs_score = self.calculate_absolute_score(indicators)
                ref_score = self.calculate_reference_score(indicators)
            else:
                abs_score = ref_score = 50
            
            final_score = abs_score * 0.6 + ref_score * 0.4
            signal = 'HOLD'
            reason = None
            
            if self.cooldown_days > 0:
                self.cooldown_days -= 1
            
            # ===== 持倉管理 =====
            if self.position != 0:
                self.holding_days += 1
                
                if self.position > 0:
                    if qqq_price > self.extreme_qqq_price:
                        self.extreme_qqq_price = qqq_price
                else:
                    if qqq_price < self.extreme_qqq_price:
                        self.extreme_qqq_price = qqq_price
                
                qqq_change = (qqq_price - self.entry_qqq_price) / self.entry_qqq_price
                
                if self.position > 0:  # 多單
                    etf_price = tqqq_price
                    etf_change = (etf_price - self.entry_price) / self.entry_price
                    
                    # 止損
                    if qqq_change <= -self.long_stop_loss:
                        signal = 'SELL_LONG_STOP'
                        reason = f'止損: -{abs(qqq_change)*100:.1f}%'
                    elif (qqq_price - self.extreme_qqq_price) / self.extreme_qqq_price <= -self.long_trailing:
                        signal = 'SELL_LONG_TRAILING'
                        reason = '回落止損'
                    
                    # 盈利減倉 2: +20% 再減 30%
                    elif etf_change >= self.profit_level_2 and not self.profit_2_done and self.remaining_shares > self.initial_shares * 0.2:
                        sell_shares = int(self.initial_shares * self.reduce_2)
                        if sell_shares > 0 and self.remaining_shares >= sell_shares:
                            signal = 'SELL_LONG_PROFIT_2'
                            reason = f'+20%再減30%: +{etf_change*100:.1f}%'
                            self.remaining_shares -= sell_shares
                            self.profit_2_done = True
                            
                            gross_pnl = (etf_price - self.entry_price) * sell_shares
                            commission = sell_shares * etf_price * self.commission_rate
                            slippage_cost = sell_shares * etf_price * self.slippage
                            net_pnl = gross_pnl - commission - slippage_cost
                            self.capital += net_pnl
                            total_commission += commission + slippage_cost
                            
                            self.trades.append({
                                'date': date, 'action': signal, 'symbol': 'TQQQ',
                                'price': etf_price, 'shares': sell_shares,
                                'net_pnl': net_pnl, 'reason': reason
                            })
                            
                            self.position = self.remaining_shares
                    
                    # 盈利減倉 1: +10% 減倉 50%
                    elif etf_change >= self.profit_level_1 and not self.profit_1_done and self.remaining_shares > self.initial_shares * 0.5:
                        sell_shares = int(self.initial_shares * self.reduce_1)
                        if sell_shares > 0 and self.remaining_shares >= sell_shares:
                            signal = 'SELL_LONG_PROFIT_1'
                            reason = f'+10%減倉50%: +{etf_change*100:.1f}%'
                            self.remaining_shares -= sell_shares
                            self.profit_1_done = True
                            
                            gross_pnl = (etf_price - self.entry_price) * sell_shares
                            commission = sell_shares * etf_price * self.commission_rate
                            slippage_cost = sell_shares * etf_price * self.slippage
                            net_pnl = gross_pnl - commission - slippage_cost
                            self.capital += net_pnl
                            total_commission += commission + slippage_cost
                            
                            self.trades.append({
                                'date': date, 'action': signal, 'symbol': 'TQQQ',
                                'price': etf_price, 'shares': sell_shares,
                                'net_pnl': net_pnl, 'reason': reason
                            })
                            
                            self.position = self.remaining_shares
                    
                    else:
                        signal = 'HOLD_LONG'
                
                else:  # 空單
                    etf_price = sqqq_price
                    etf_change = (self.entry_price - etf_price) / self.entry_price
                    
                    if qqq_change >= self.short_stop_loss:
                        signal = 'SELL_SHORT_STOP'
                        reason = f'空單止損: +{qqq_change*100:.1f}%'
                    elif (qqq_price - self.extreme_qqq_price) / self.extreme_qqq_price >= self.short_trailing:
                        signal = 'SELL_SHORT_TRAILING'
                        reason = '反彈止損'
                    elif etf_change >= self.short_take_profit:
                        signal = 'SELL_SHORT_PROFIT'
                        reason = f'空單止盈: +{etf_change*100:.1f}%'
                    else:
                        signal = 'HOLD_SHORT'
            
            else:  # 無持倉
                if self.cooldown_days > 0:
                    signal = 'HOLD_COOLDOWN'
                elif final_score > self.long_threshold:
                    signal = 'BUY_LONG'
                    reason = f'評分{final_score:.0f}>60'
                elif final_score < self.short_threshold:
                    signal = 'BUY_SHORT'
                    reason = f'評分{final_score:.0f}<40'
                else:
                    signal = 'HOLD_CASH'
            
            # 執行交易
            if 'BUY' in signal and self.position == 0:
                etf_price = tqqq_price if 'LONG' in signal else sqqq_price
                symbol = 'TQQQ' if 'LONG' in signal else 'SQQQ'
                
                shares = int(self.capital * self.max_position_pct / etf_price)
                if shares > 0:
                    commission = shares * etf_price * self.commission_rate
                    slippage_cost = shares * etf_price * self.slippage
                    total_cost = commission + slippage_cost
                    
                    self.position = shares if 'LONG' in signal else -shares
                    self.entry_price = etf_price
                    self.entry_qqq_price = qqq_price
                    self.extreme_qqq_price = qqq_price
                    self.current_symbol = symbol
                    self.holding_days = 0
                    self.initial_shares = shares
                    self.remaining_shares = shares
                    self.profit_1_done = False
                    self.profit_2_done = False
                    total_commission += total_cost
                    
                    self.trades.append({
                        'date': date, 'action': signal, 'symbol': symbol,
                        'price': etf_price, 'shares': shares,
                        'commission': commission, 'slippage': slippage_cost
                    })
            
            elif 'SELL' in signal and 'PROFIT' not in signal and self.position != 0:
                etf_price = tqqq_price if self.position > 0 else sqqq_price
                
                if self.position > 0:
                    gross_pnl = (etf_price - self.entry_price) * abs(self.position)
                else:
                    gross_pnl = (self.entry_price - etf_price) * abs(self.position)
                
                commission = abs(self.position) * etf_price * self.commission_rate
                slippage_cost = abs(self.position) * etf_price * self.slippage
                net_pnl = gross_pnl - commission - slippage_cost
                self.capital += net_pnl
                total_commission += commission + slippage_cost
                
                self.trades.append({
                    'date': date, 'action': signal, 'symbol': self.current_symbol,
                    'price': etf_price, 'shares': abs(self.position),
                    'net_pnl': net_pnl, 'reason': reason
                })
                
                self.position = 0
                self.initial_shares = 0
                self.remaining_shares = 0
            
            position_value = abs(self.position) * (tqqq_price if self.position > 0 else sqqq_price) if self.position != 0 else 0
            portfolio_value = self.capital + position_value
            
            daily_results.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'signal': signal,
                'vix': vix_price
            })
        
        self.daily_results = pd.DataFrame(daily_results)
        self.total_commission = total_commission
        return self.daily_results
    
    def calculate_metrics(self):
        """計算指標"""
        print("\n" + "="*70)
        print("回測結果 - V9.4 最終版")
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
        
        sell_trades = [t for t in self.trades if 'SELL' in t['action']]
        partial_trades = [t for t in sell_trades if 'PROFIT' in t['action']]
        winning_trades = [t for t in sell_trades if t.get('net_pnl', 0) > 0]
        win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0
        
        print(f"\n【基本指標】")
        print(f"初始資金: ${self.initial_capital:,.2f}")
        print(f"最終價值: ${final_value:,.2f}")
        print(f"總回報: {total_return:.2f}%")
        print(f"年化回報: {annualized_return:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        
        print(f"\n【交易統計】")
        print(f"總交易: {len(sell_trades)} 次")
        print(f"  部分盈利減倉: {len(partial_trades)} 次")
        print(f"勝率: {win_rate:.1f}%")
        
        buy_hold_tqqq = (self.tqqq_data['Close'].iloc[-1] / self.tqqq_data['Close'].iloc[0] - 1) * 100
        
        print(f"\n【策略對比】")
        print(f"V9.4 最終版: {total_return:.2f}%")
        print(f"V9 原版: 1966.92%")
        print(f"買入持有: {buy_hold_tqqq:.2f}%")
        print(f"vs TQQQ: {total_return - buy_hold_tqqq:+.2f}%")
        
        return {
            'version': 'V9.4_Final',
            'total_return_pct': total_return,
            'annualized_return_pct': annualized_return,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'total_trades': len(sell_trades),
            'partial_exits': len(partial_trades)
        }
    
    def save_results(self):
        """保存結果"""
        os.makedirs('backtest/results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.daily_results.to_csv(f'backtest/results/v9_4_final_daily_{timestamp}.csv', index=False)
        
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_df.to_csv(f'backtest/results/v9_4_final_trades_{timestamp}.csv', index=False)
        
        metrics = self.calculate_metrics()
        with open(f'backtest/results/v9_4_final_metrics_{timestamp}.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"\n結果已保存: backtest/results/v9_4_final_*_{timestamp}.*")

def main():
    backtest = SixLoopBacktestV9_4(
        start_date='2019-01-01',
        end_date='2024-12-31',
        initial_capital=100000
    )
    
    backtest.run_backtest()
    backtest.calculate_metrics()
    backtest.save_results()
    
    print("\n✅ V9.4 最終版回測完成！")

if __name__ == '__main__':
    main()
