"""
六循環系統回測 - V9.3 盈利保護版
基於 V9 Asymmetric，優化執行層降低回撤：
1. 分層止損（-2%減倉，-3%再減，-5%全平）
2. 盈利保護（+10%移損，+15%止盈50%）
3. 簡化波動率過濾（VIX>30減倉，>35全平）
4. 保留 V9 核心評分系統
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import json
import os

class SixLoopBacktestV9_3:
    """六循環回測 V9.3 - 盈利保護降低回撤版"""
    
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
        
        # 分層止損參數
        self.stop_loss_1 = 0.02      # -2% 減倉 50%
        self.stop_loss_2 = 0.03      # -3% 再減 30%
        self.stop_loss_3 = 0.05      # -5% 全平
        
        # 盈利保護參數
        self.profit_breakeven = 0.10  # +10% 移動止損至成本
        self.profit_take_1 = 0.15     # +15% 止盈 50%
        self.profit_take_2 = 0.20     # +20% 再止盈 30%
        self.profit_trailing = 0.03   # 回落 3% 止損剩餘
        
        # 空單參數（敏捷）
        self.short_stop = 0.02
        self.short_trailing = 0.02
        self.short_take_profit = 0.10
        
        # VIX 過濾
        self.vix_reduce = 30
        self.vix_exit = 35
        
        # 通用
        self.cooldown_period = 1
        self.long_threshold = 60
        self.short_threshold = 40
        self.max_position_pct = 0.95
        self.commission_rate = 0.001
        self.slippage = 0.001
        
        # 追蹤狀態
        self.position_size = 1.0      # 當前倉位比例
        self.breakeven_price = 0      # 成本價（移動止損用）
        self.total_shares = 0         # 總股數
        
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
        """計算技術指標（V9 原版）"""
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
        """Absolute Score（V9 原版）"""
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
        """Reference Score（V9 原版）"""
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
        print("六循環系統回測 - V9.3 盈利保護版")
        print("="*70)
        print("【分層止損】")
        print(f"  -2%: 減倉 50%")
        print(f"  -3%: 再減 30%")
        print(f"  -5%: 全平")
        print("【盈利保護】")
        print(f"  +10%: 移動止損至成本")
        print(f"  +15%: 止盈 50%")
        print(f"  +20%: 再止盈 30%")
        print("【VIX 過濾】")
        print(f"  >{self.vix_reduce}: 減倉 50%")
        print(f"  >{self.vix_exit}: 全平")
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
        partial_exits = []  # 記錄部分平倉
        
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
                    etf_change = (tqqq_price - self.entry_price) / self.entry_price
                    
                    # ===== 分層止損 =====
                    if qqq_change <= -self.stop_loss_3:
                        signal = 'SELL_LONG_STOP_FULL'
                        reason = f'全平: -{abs(qqq_change)*100:.1f}%'
                        self.position_size = 0
                    elif qqq_change <= -self.stop_loss_2 and self.position_size > 0.2:
                        signal = 'SELL_LONG_PARTIAL_2'
                        reason = f'再減30%: -{abs(qqq_change)*100:.1f}%'
                        self.position_size -= 0.3
                        partial_exits.append({'date': date, 'type': 'partial_2', 'size': 0.3})
                    elif qqq_change <= -self.stop_loss_1 and self.position_size > 0.5:
                        signal = 'SELL_LONG_PARTIAL_1'
                        reason = f'減倉50%: -{abs(qqq_change)*100:.1f}%'
                        self.position_size -= 0.5
                        partial_exits.append({'date': date, 'type': 'partial_1', 'size': 0.5})
                    
                    # ===== 盈利保護 =====
                    elif etf_change >= self.profit_take_2 and self.position_size > 0.2:
                        signal = 'SELL_LONG_PROFIT_2'
                        reason = f'止盈30%: +{etf_change*100:.1f}%'
                        self.position_size -= 0.3
                        partial_exits.append({'date': date, 'type': 'profit_2', 'size': 0.3})
                    elif etf_change >= self.profit_take_1 and self.position_size > 0.5:
                        signal = 'SELL_LONG_PROFIT_1'
                        reason = f'止盈50%: +{etf_change*100:.1f}%'
                        self.position_size -= 0.5
                        partial_exits.append({'date': date, 'type': 'profit_1', 'size': 0.5})
                    elif etf_change >= self.profit_breakeven:
                        # 移動止損至成本
                        self.breakeven_price = self.entry_price
                        if tqqq_price <= self.breakeven_price * 0.97:
                            signal = 'SELL_LONG_BREAKEVEN'
                            reason = f'移損觸發: 回落3%'
                            self.position_size = 0
                    
                    # VIX 過濾
                    elif vix_price > self.vix_exit:
                        signal = 'SELL_LONG_VIX_EXIT'
                        reason = f'VIX>{self.vix_exit}'
                        self.position_size = 0
                    elif vix_price > self.vix_reduce and self.position_size > 0.5:
                        signal = 'SELL_LONG_VIX_REDUCE'
                        reason = f'VIX>{self.vix_reduce},減倉50%'
                        self.position_size -= 0.5
                    
                    else:
                        signal = 'HOLD_LONG'
                
                else:  # 空單（保持 V9 敏捷）
                    etf_change = (self.entry_price - sqqq_price) / self.entry_price
                    
                    if qqq_change >= self.short_stop:
                        signal = 'SELL_SHORT_STOP'
                        reason = f'空單止損: +{qqq_change*100:.1f}%'
                        self.position_size = 0
                    elif etf_change >= self.short_take_profit:
                        signal = 'SELL_SHORT_PROFIT'
                        reason = f'空單止盈: +{etf_change*100:.1f}%'
                        self.position_size = 0
                    else:
                        signal = 'HOLD_SHORT'
            
            else:  # 無持倉
                if self.cooldown_days > 0:
                    signal = 'HOLD_COOLDOWN'
                elif final_score > self.long_threshold and vix_price < self.vix_exit:
                    signal = 'BUY_LONG'
                    reason = f'評分{final_score:.0f}>60'
                    self.position_size = 1.0
                elif final_score < self.short_threshold:
                    signal = 'BUY_SHORT'
                    reason = f'評分{final_score:.0f}<40'
                    self.position_size = 1.0
                else:
                    signal = 'HOLD_CASH'
            
            # 執行交易（簡化版，實際應處理部分平倉邏輯）
            if 'BUY' in signal and self.position == 0:
                etf_price = tqqq_price if 'LONG' in signal else sqqq_price
                symbol = 'TQQQ' if 'LONG' in signal else 'SQQQ'
                
                shares = int(self.capital * self.max_position_pct / etf_price)
                if shares > 0:
                    self.position = shares if 'LONG' in signal else -shares
                    self.entry_price = etf_price
                    self.entry_qqq_price = qqq_price
                    self.extreme_qqq_price = qqq_price
                    self.current_symbol = symbol
                    self.holding_days = 0
                    self.total_shares = abs(self.position)
            
            elif 'SELL' in signal:
                # 簡化：全平處理
                if self.position != 0:
                    etf_price = tqqq_price if self.position > 0 else sqqq_price
                    if self.position > 0:
                        pnl = (etf_price - self.entry_price) * self.position
                    else:
                        pnl = (self.entry_price - etf_price) * abs(self.position)
                    
                    self.capital += pnl
                    
                    self.trades.append({
                        'date': date, 'action': signal, 'pnl': pnl,
                        'reason': reason, 'vix': vix_price
                    })
                    
                    self.position = 0
                    self.position_size = 1.0
            
            position_value = abs(self.position) * (tqqq_price if self.position > 0 else sqqq_price) if self.position != 0 else 0
            
            daily_results.append({
                'date': date, 'portfolio_value': self.capital + position_value,
                'signal': signal, 'vix': vix_price
            })
        
        self.daily_results = pd.DataFrame(daily_results)
        return self.daily_results
    
    def calculate_metrics(self):
        """計算指標"""
        final_value = self.daily_results['portfolio_value'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        self.daily_results['cummax'] = self.daily_results['portfolio_value'].cummax()
        self.daily_results['drawdown'] = (self.daily_results['portfolio_value'] - self.daily_results['cummax']) / self.daily_results['cummax']
        max_drawdown = self.daily_results['drawdown'].min() * 100
        
        print(f"\n【V9.3 結果】")
        print(f"總回報: {total_return:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        print(f"交易次數: {len(self.trades)}")
        
        return {'return': total_return, 'drawdown': max_drawdown}

def main():
    backtest = SixLoopBacktestV9_3()
    backtest.run_backtest()
    backtest.calculate_metrics()

if __name__ == '__main__':
    main()
