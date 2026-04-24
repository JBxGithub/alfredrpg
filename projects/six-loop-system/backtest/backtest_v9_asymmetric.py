"""
六循環系統回測 - V9 不對稱版
多單穩健 + 空單敏捷
多單: 止損-3%, 回落-3%, 止盈+15%, 重估7天
空單: 止損+2%, 反彈+2%, 止盈+10%, 重估3天
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import json
import os

class SixLoopBacktestV9Asymmetric:
    """六循環回測 V9 - 不對稱版"""
    
    def __init__(self, start_date='2019-01-01', end_date='2024-12-31', initial_capital=100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        
        # 持倉狀態
        self.position = 0  # 正數=多單, 負數=空單
        self.entry_price = 0
        self.entry_qqq_price = 0
        self.extreme_qqq_price = 0
        self.holding_days = 0
        self.cooldown_days = 0
        self.current_symbol = None
        self.trades = []
        
        # ===== V9 不對稱參數 =====
        # 多單 (TQQQ) - 穩健
        self.long_stop_loss = 0.03        # QQQ -3%
        self.long_trailing = 0.03         # 回落 -3%
        self.long_take_profit = 0.15      # TQQQ +15%
        self.long_reeval = 7              # 7天重估
        
        # 空單 (SQQQ) - 敏捷
        self.short_stop_loss = 0.02       # QQQ +2% (更嚴格)
        self.short_trailing = 0.02        # 反彈 +2% (更嚴格)
        self.short_take_profit = 0.10     # SQQQ +10% (更快獲利)
        self.short_reeval = 3             # 3天重估 (更頻繁)
        
        # 通用
        self.cooldown_period = 1
        self.long_threshold = 60
        self.short_threshold = 40
        self.continue_long = 60
        self.continue_short = 40
        self.max_position_pct = 0.95
        self.commission_rate = 0.001
        self.slippage = 0.001
        
    def fetch_data(self):
        """獲取數據"""
        print(f"獲取數據: {self.start_date} 至 {self.end_date}")
        
        qqq = yf.Ticker("QQQ")
        self.qqq_data = qqq.history(start=self.start_date, end=self.end_date)
        
        tqqq = yf.Ticker("TQQQ")
        self.tqqq_data = tqqq.history(start=self.start_date, end=self.end_date)
        
        sqqq = yf.Ticker("SQQQ")
        self.sqqq_data = sqqq.history(start=self.start_date, end=self.end_date)
        
        # 獲取 VIX 數據
        vix = yf.Ticker("^VIX")
        self.vix_data = vix.history(start=self.start_date, end=self.end_date)
        
        print(f"QQQ: {len(self.qqq_data)} 天")
        print(f"TQQQ: {len(self.tqqq_data)} 天")
        print(f"SQQQ: {len(self.sqqq_data)} 天")
        print(f"VIX: {len(self.vix_data)} 天")
        
        return self.qqq_data, self.tqqq_data, self.sqqq_data, self.vix_data
    
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
        print("六循環系統回測 - V9 (不對稱版)")
        print("="*70)
        print("【多單 TQQQ - 穩健】")
        print(f"  止損: QQQ -{self.long_stop_loss*100:.0f}%")
        print(f"  回落止損: -{self.long_trailing*100:.0f}%")
        print(f"  止盈: +{self.long_take_profit*100:.0f}%")
        print(f"  重估: {self.long_reeval}天")
        print("【空單 SQQQ - 敏捷】")
        print(f"  止損: QQQ +{self.short_stop_loss*100:.0f}% (更嚴格)")
        print(f"  反彈止損: +{self.short_trailing*100:.0f}% (更嚴格)")
        print(f"  止盈: +{self.short_take_profit*100:.0f}% (更快)")
        print(f"  重估: {self.short_reeval}天 (更頻繁)")
        
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
            
            # ===== V9 不對稱核心邏輯 =====
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
                
                # ===== VIX 波動率適應機制 =====
                vix_price = self.vix_data['Close'].iloc[i] if i < len(self.vix_data) else 20
                adjusted_long_stop = self.long_stop_loss
                adjusted_short_stop = self.short_stop_loss
                
                # VIX > 30 時收緊止損
                if vix_price > 30:
                    adjusted_long_stop = 0.02  # 由 -3% 收緊至 -2%
                    adjusted_short_stop = 0.01  # 由 +2% 收緊至 +1%
                
                # 單日跌幅 > 5% 強制減倉
                qqq_daily_change = (qqq_price - self.qqq_data['Close'].iloc[i-1]) / self.qqq_data['Close'].iloc[i-1] if i > 0 else 0
                emergency_reduce = qqq_daily_change < -0.05
                
                if self.position > 0:  # ===== 多單 (穩健) =====
                    qqq_change_from_extreme = (qqq_price - self.extreme_qqq_price) / self.extreme_qqq_price
                    etf_change = (tqqq_price - self.entry_price) / self.entry_price
                    
                    # 多單止損: -3% (VIX高時-2%)
                    if qqq_change_from_entry <= -adjusted_long_stop:
                        signal = 'SELL_LONG_STOP'
                        reason = f'多單止損: {qqq_change_from_entry*100:.1f}% (VIX={vix_price:.1f})'
                        self.cooldown_days = self.cooldown_period
                    
                    # 單日暴跌 > 5% 強制減倉
                    elif emergency_reduce:
                        signal = 'EMERGENCY_REDUCE_LONG'
                        reason = f'單日暴跌 {qqq_daily_change*100:.1f}%,強制減倉'
                        self.cooldown_days = self.cooldown_period * 2  # 冷卻2倍
                    
                    # 多單回落止損: -3%
                    elif qqq_change_from_extreme <= -self.long_trailing:
                        signal = 'SELL_LONG_TRAILING'
                        reason = f'多單回落: {qqq_change_from_extreme*100:.1f}%'
                        self.cooldown_days = self.cooldown_period
                    
                    # 多單止盈: +15%
                    elif etf_change >= self.long_take_profit:
                        signal = 'SELL_LONG_PROFIT'
                        reason = f'多單止盈: {etf_change*100:.1f}%'
                    
                    # 多單7天重估
                    elif self.holding_days >= self.long_reeval:
                        if final_score > self.continue_long:
                            signal = 'HOLD_LONG_CONTINUE'
                            self.holding_days = 0
                            reason = '牛市續持'
                        else:
                            signal = 'SELL_LONG_REEVAL'
                            reason = '多單重估賣出'
                    
                    else:
                        signal = 'HOLD_LONG'
                
                else:  # ===== 空單 (敏捷) =====
                    qqq_change_from_extreme = (qqq_price - self.extreme_qqq_price) / self.extreme_qqq_price
                    etf_change = (self.entry_price - sqqq_price) / self.entry_price
                    
                    # 空單止損: +2% (VIX高時+1%)
                    if qqq_change_from_entry >= adjusted_short_stop:
                        signal = 'SELL_SHORT_STOP'
                        reason = f'空單止損: +{qqq_change_from_entry*100:.1f}% (敏捷,VIX={vix_price:.1f})'
                        self.cooldown_days = self.cooldown_period
                    
                    # 單日暴漲 > 5% 強制減倉 (空單)
                    elif qqq_daily_change > 0.05:
                        signal = 'EMERGENCY_REDUCE_SHORT'
                        reason = f'單日暴漲 +{qqq_daily_change*100:.1f}%,強制減倉'
                        self.cooldown_days = self.cooldown_period * 2
                    
                    # 空單反彈止損: +2% (更嚴格！)
                    elif qqq_change_from_extreme >= self.short_trailing:
                        signal = 'SELL_SHORT_TRAILING'
                        reason = f'空單反彈: +{qqq_change_from_extreme*100:.1f}% (敏捷)'
                        self.cooldown_days = self.cooldown_period
                    
                    # 空單止盈: +10% (更快！)
                    elif etf_change >= self.short_take_profit:
                        signal = 'SELL_SHORT_PROFIT'
                        reason = f'空單止盈: {etf_change*100:.1f}% (敏捷)'
                    
                    # 空單3天重估 (更頻繁！)
                    elif self.holding_days >= self.short_reeval:
                        if final_score < self.continue_short:
                            signal = 'HOLD_SHORT_CONTINUE'
                            self.holding_days = 0
                            reason = '熊市續持(敏捷)'
                        else:
                            signal = 'SELL_SHORT_REEVAL'
                            reason = '空單3天重估賣出(敏捷)'
                    
                    else:
                        signal = 'HOLD_SHORT'
            
            else:
                # 無持倉
                if self.cooldown_days > 0:
                    signal = 'HOLD_COOLDOWN'
                
                elif final_score > self.long_threshold:
                    signal = 'BUY_LONG'
                    reason = f'評分{final_score:.1f}>60,做多(穩健)'
                
                elif final_score < self.short_threshold:
                    signal = 'BUY_SHORT'
                    reason = f'評分{final_score:.1f}<40,做空(敏捷)'
                
                else:
                    signal = 'HOLD_CASH'
                    reason = f'評分{final_score:.1f},觀望'
            
            # 執行交易
            if 'BUY' in signal and self.position == 0:
                if signal == 'BUY_LONG':
                    etf_price = tqqq_price
                    symbol = 'TQQQ'
                    self.position = 1
                else:
                    etf_price = sqqq_price
                    symbol = 'SQQQ'
                    self.position = -1
                
                shares = int(self.capital * 0.95 / etf_price)
                
                if shares > 0:
                    commission = shares * etf_price * self.commission_rate
                    slippage_cost = shares * etf_price * self.slippage
                    total_cost = commission + slippage_cost
                    
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
                if self.position > 0:
                    etf_price = tqqq_price
                    gross_pnl = (etf_price - self.entry_price) * self.position
                else:
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
                
                self.position = 0
                self.entry_price = 0
                self.entry_qqq_price = 0
                self.extreme_qqq_price = 0
                self.current_symbol = None
                self.holding_days = 0
            
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
        """計算指標"""
        print("\n" + "="*70)
        print("回測結果 - V9 (不對稱版)")
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
        winning_trades = [t for t in sell_trades if t.get('net_pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('net_pnl', 0) <= 0]
        
        win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0
        avg_win = np.mean([t['etf_change'] for t in winning_trades]) * 100 if winning_trades else 0
        avg_loss = np.mean([t['etf_change'] for t in losing_trades]) * 100 if losing_trades else 0
        avg_holding_days = np.mean([t.get('holding_days', 0) for t in sell_trades]) if sell_trades else 0
        
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
        print(f"總交易: {len(sell_trades)} 次")
        print(f"  多單(穩健): {len(long_trades)} 次, 勝率 {long_wins/len(long_trades)*100 if long_trades else 0:.1f}%")
        print(f"  空單(敏捷): {len(short_trades)} 次, 勝率 {short_wins/len(short_trades)*100 if short_trades else 0:.1f}%")
        print(f"整體勝率: {win_rate:.1f}%")
        print(f"平均盈利: {avg_win:.2f}%")
        print(f"平均虧損: {avg_loss:.2f}%")
        print(f"平均持倉: {avg_holding_days:.1f} 天")
        
        # 對比
        buy_hold_tqqq = (self.tqqq_data['Close'].iloc[-1] / self.tqqq_data['Close'].iloc[0] - 1) * 100
        
        print(f"\n【策略對比】")
        print(f"V9 不對稱策略: {total_return:.2f}%")
        print(f"V8 對稱策略: 977.17% (參考)")
        print(f"買入持有 TQQQ: {buy_hold_tqqq:.2f}%")
        print(f"vs TQQQ: {total_return - buy_hold_tqqq:+.2f}%")
        
        self.metrics = {
            'version': 'V9_Asymmetric',
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
            'outperformance': total_return - buy_hold_tqqq
        }
        
        return self.metrics
    
    def save_results(self):
        """保存"""
        os.makedirs('backtest/results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.daily_results.to_csv(f'backtest/results/v9_daily_{timestamp}.csv', index=False)
        
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_df.to_csv(f'backtest/results/v9_trades_{timestamp}.csv', index=False)
        
        with open(f'backtest/results/v9_metrics_{timestamp}.json', 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        
        print(f"\n結果已保存: backtest/results/v9_*_{timestamp}.*")

def main():
    backtest = SixLoopBacktestV9Asymmetric(
        start_date='2019-01-01',
        end_date='2024-12-31',
        initial_capital=100000
    )
    
    backtest.run_backtest()
    backtest.calculate_metrics()
    backtest.save_results()
    
    print("\n✅ V9 不對稱版回測完成！")

if __name__ == '__main__':
    main()
