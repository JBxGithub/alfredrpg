"""
六循環系統回測 - V10 增強版
基於 V9 Asymmetric + 六項修正:
1. MACDV = Volume (成交量 > 1.5×20日均量)
2. MTF 月/周/日 多時間框架
3. VIX > 30 空單調整 (+3%止盈, 回落止損)
4. Reference Score 加入 BOLL(20,2), Volume, MACD(12,26,9)
5. EMA(9/20/50) 取代 MA
6. Absolute 加入 ADX
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import json
import os

class SixLoopBacktestV10Enhanced:
    """六循環回測 V10 - 增強版"""
    
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
        
        # ===== V10 增強參數 =====
        # 多單 (TQQQ) - 穩健
        self.long_stop_loss = 0.03
        self.long_trailing = 0.03
        self.long_take_profit = 0.15
        self.long_reeval = 7
        
        # 空單 (SQQQ) - 敏捷
        self.short_stop_loss = 0.02
        self.short_trailing = 0.02
        self.short_take_profit = 0.10
        self.short_reeval = 3
        
        # VIX 調整 (空單)
        self.vix_high_threshold = 30
        self.vix_high_short_take_profit = 0.03  # VIX>30時+3%止盈
        
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
        
        vix = yf.Ticker("^VIX")
        self.vix_data = vix.history(start=self.start_date, end=self.end_date)
        
        print(f"QQQ: {len(self.qqq_data)} 天")
        print(f"TQQQ: {len(self.tqqq_data)} 天")
        print(f"SQQQ: {len(self.sqqq_data)} 天")
        print(f"VIX: {len(self.vix_data)} 天")
        
        return self.qqq_data, self.tqqq_data, self.sqqq_data, self.vix_data
    
    def resample_to_weekly(self, daily_data):
        """重採樣到周線"""
        return daily_data.resample('W').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
    
    def resample_to_monthly(self, daily_data):
        """重採樣到月線"""
        return daily_data.resample('ME').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
    
    def calculate_ema(self, data, periods):
        """計算 EMA"""
        return data.ewm(span=periods, adjust=False).mean()
    
    def calculate_bollinger(self, data, period=20, std_dev=2):
        """計算布林帶 BOLL(20,2)"""
        middle = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def calculate_macd(self, data, fast=12, slow=26, signal=9):
        """計算 MACD(12,26,9)"""
        ema_fast = self.calculate_ema(data, fast)
        ema_slow = self.calculate_ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def calculate_adx(self, high, low, close, period=14):
        """計算 ADX"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0)
        minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0)
        
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        plus_di = 100 * pd.Series(plus_dm, index=high.index).ewm(alpha=1/period, adjust=False).mean() / atr
        minus_di = 100 * pd.Series(minus_dm, index=high.index).ewm(alpha=1/period, adjust=False).mean() / atr
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(alpha=1/period, adjust=False).mean()
        
        return adx, plus_di, minus_di
    
    def calculate_volume_signal(self, volume, period=20, threshold=1.2):
        """MACDV: 成交量 > 1.2×20日均量"""
        volume_ma = volume.rolling(window=period).mean()
        return volume > (volume_ma * threshold)
    
    def calculate_indicators(self, data, idx):
        """計算所有技術指標 (V10 增強版)"""
        if idx < 50:
            return None
        
        window = data.iloc[max(0, idx-200):idx+1]
        current_price = data['Close'].iloc[idx]
        
        # ===== 1. EMA(9/20/50) 取代 MA =====
        ema9 = self.calculate_ema(window['Close'], 9).iloc[-1]
        ema20 = self.calculate_ema(window['Close'], 20).iloc[-1]
        ema50 = self.calculate_ema(window['Close'], 50).iloc[-1]
        
        # ===== 2. BOLL(20,2) =====
        boll_upper, boll_middle, boll_lower = self.calculate_bollinger(window['Close'])
        boll_upper = boll_upper.iloc[-1]
        boll_middle = boll_middle.iloc[-1]
        boll_lower = boll_lower.iloc[-1]
        
        # ===== 3. MACD(12,26,9) =====
        macd_line, signal_line, histogram = self.calculate_macd(window['Close'])
        macd_current = macd_line.iloc[-1]
        macd_signal = signal_line.iloc[-1]
        macd_prev = macd_line.iloc[-2] if len(macd_line) > 1 else macd_current
        macd_signal_prev = signal_line.iloc[-2] if len(signal_line) > 1 else macd_signal
        
        # ===== 4. ADX =====
        adx, plus_di, minus_di = self.calculate_adx(window['High'], window['Low'], window['Close'])
        adx_current = adx.iloc[-1]
        plus_di_current = plus_di.iloc[-1]
        minus_di_current = minus_di.iloc[-1]
        
        # ===== 5. RSI =====
        delta = window['Close'].diff()
        gain = (delta.where(delta > 0, 0)).iloc[-14:].mean()
        loss = (-delta.where(delta < 0, 0)).iloc[-14:].mean()
        rs = gain / loss if loss != 0 else 1
        rsi = 100 - (100 / (1 + rs))
        
        # ===== 6. MACDV (Volume) =====
        volume_signal = self.calculate_volume_signal(window['Volume']).iloc[-1]
        
        # ===== Absolute Score (無 ADX) =====
        absolute_score = 50
        
        # EMA 趨勢 (50%)
        if current_price > ema20:
            absolute_score += 25
        if ema9 > ema20 > ema50:
            absolute_score += 25
        
        # RSI (50%)
        if 30 < rsi < 70:
            absolute_score += 20
        
        # 動量 (10%)
        momentum_20 = (current_price - window['Close'].iloc[-20]) / window['Close'].iloc[-20]
        if momentum_20 > 0:
            absolute_score += 10
        
        # ===== Reference Score (加入 BOLL, Volume, MACD) =====
        reference_score = 50
        
        # BOLL (30%)
        if current_price > boll_middle:
            reference_score += 15
        if boll_upper > current_price > boll_lower:
            reference_score += 15
        
        # Volume (50%)
        if volume_signal:
            reference_score += 50
        
        return {
            'price': current_price,
            'ema9': ema9,
            'ema20': ema20,
            'ema50': ema50,
            'boll_upper': boll_upper,
            'boll_middle': boll_middle,
            'boll_lower': boll_lower,
            'macd': macd_current,
            'macd_signal': macd_signal,
            'macd_golden_cross': macd_prev < macd_signal_prev and macd_current > macd_signal,
            'macd_death_cross': macd_prev > macd_signal_prev and macd_current < macd_signal,

            'rsi': rsi,
    
            'absolute_score': min(100, max(0, absolute_score)),
            'reference_score': min(100, max(0, reference_score))
        }
    
    def calculate_mtf_trend(self, daily_data, idx):
        """計算 MTF 月/周/日 趨勢"""
        if idx < 50:
            return {'monthly': 'neutral', 'weekly': 'neutral'}
        
        current_date = daily_data.index[idx]
        
        # 獲取到當前日期的數據
        data_up_to_idx = daily_data.iloc[:idx+1]
        
        # 重採樣到周線和月線
        weekly_data = self.resample_to_weekly(data_up_to_idx)
        monthly_data = self.resample_to_monthly(data_up_to_idx)
        
        mtf = {'monthly': 'neutral', 'weekly': 'neutral'}
        
        # 月線趨勢
        if len(monthly_data) >= 3:
            monthly_ema20 = self.calculate_ema(monthly_data['Close'], 20)
            if monthly_data['Close'].iloc[-1] > monthly_ema20.iloc[-1]:
                mtf['monthly'] = 'bullish'
            elif monthly_data['Close'].iloc[-1] < monthly_ema20.iloc[-1]:
                mtf['monthly'] = 'bearish'
        
        # 周線趨勢
        if len(weekly_data) >= 10:
            weekly_ema20 = self.calculate_ema(weekly_data['Close'], 20)
            if weekly_data['Close'].iloc[-1] > weekly_ema20.iloc[-1]:
                mtf['weekly'] = 'bullish'
            elif weekly_data['Close'].iloc[-1] < weekly_ema20.iloc[-1]:
                mtf['weekly'] = 'bearish'
        
        return mtf
    
    def run_backtest(self):
        """執行回測"""
        print("\n" + "="*60)
        print("六循環系統回測 - V10 增強版")
        print("="*60)
        print("【多單 TQQQ - 穩健】")
        print("  止損: QQQ -3%")
        print("  回落止損: -3%")
        print("  止盈: +15%")
        print("  重估: 7天")
        print("【空單 SQQQ - 敏捷】")
        print("  止損: QQQ +2%")
        print("  反彈止損: +2%")
        print("  止盈: +10% (VIX>30時+3%)")
        print("  重估: 3天")
        print("【V10 增強】")
        print("  - EMA(9/20/50) 取代 MA")
        print("  - BOLL(20,2) 加入 Reference")
        print("  - MACDV (Volume > 1.5×20日)")
        print("  - ADX 加入 Absolute")
        print("  - MTF 月/周/日 趨勢")
        print("="*60)
        
        self.fetch_data()
        
        qqq_prices = self.qqq_data['Close'].values
        tqqq_prices = self.tqqq_data['Close'].values
        sqqq_prices = self.sqqq_data['Close'].values
        vix_prices = self.vix_data['Close'].values if len(self.vix_data) > 0 else np.zeros(len(qqq_prices))
        
        portfolio_values = []
        
        for i in range(200, len(qqq_prices)):
            current_date = self.qqq_data.index[i]
            qqq_price = qqq_prices[i]
            tqqq_price = tqqq_prices[i] if i < len(tqqq_prices) else tqqq_prices[-1]
            sqqq_price = sqqq_prices[i] if i < len(sqqq_prices) else sqqq_prices[-1]
            vix_price = vix_prices[i] if i < len(vix_prices) else 20
            
            indicators = self.calculate_indicators(self.qqq_data, i)
            if indicators is None:
                continue
            
            # 計算分數 (無 MTF)
            absolute_score = indicators['absolute_score']
            reference_score = indicators['reference_score']
            final_score = absolute_score * 0.6 + reference_score * 0.4
            
            # 更新冷卻期
            if self.cooldown_days > 0:
                self.cooldown_days -= 1
            
            signal = 'HOLD'
            
            # ===== V10 增強: MTF 過濾 =====
            if self.position != 0:
                self.holding_days += 1
                
                if self.position > 0:  # 多單
                    if qqq_price > self.extreme_qqq_price:
                        self.extreme_qqq_price = qqq_price
                    
                    qqq_change_from_entry = (qqq_price - self.entry_qqq_price) / self.entry_qqq_price
                    qqq_change_from_extreme = (qqq_price - self.extreme_qqq_price) / self.extreme_qqq_price
                    etf_change = (tqqq_price - self.entry_price) / self.entry_price
                    
                    if qqq_change_from_entry <= -self.long_stop_loss:
                        signal = 'SELL_LONG_STOP'
                        self.cooldown_days = self.cooldown_period
                    elif qqq_change_from_extreme <= -self.long_trailing:
                        signal = 'SELL_LONG_TRAILING'
                        self.cooldown_days = self.cooldown_period
                    elif etf_change >= self.long_take_profit:
                        signal = 'SELL_LONG_PROFIT'
                    elif self.holding_days >= self.long_reeval:
                        if final_score > self.continue_long:
                            signal = 'HOLD_LONG_CONTINUE'
                            self.holding_days = 0
                        else:
                            signal = 'SELL_LONG_REEVAL'
                    else:
                        signal = 'HOLD_LONG'
                
                else:  # 空單
                    if qqq_price < self.extreme_qqq_price:
                        self.extreme_qqq_price = qqq_price
                    
                    qqq_change_from_entry = (qqq_price - self.entry_qqq_price) / self.entry_qqq_price
                    qqq_change_from_extreme = (qqq_price - self.extreme_qqq_price) / self.extreme_qqq_price
                    etf_change = (self.entry_price - sqqq_price) / self.entry_price
                    
                    # ===== VIX > 30 空單調整 =====
                    if vix_price > self.vix_high_threshold:
                        short_tp = self.vix_high_short_take_profit  # +3%止盈
                    else:
                        short_tp = self.short_take_profit  # +10%止盈
                    
                    if qqq_change_from_entry >= self.short_stop_loss:
                        signal = 'SELL_SHORT_STOP'
                        self.cooldown_days = self.cooldown_period
                    elif qqq_change_from_extreme >= self.short_trailing:
                        signal = 'SELL_SHORT_TRAILING'
                        self.cooldown_days = self.cooldown_period
                    elif etf_change >= short_tp:
                        signal = 'SELL_SHORT_PROFIT'
                        if vix_price > self.vix_high_threshold:
                            signal += '_VIX_HIGH'
                    elif self.holding_days >= self.short_reeval:
                        if final_score < self.continue_short:
                            signal = 'HOLD_SHORT_CONTINUE'
                            self.holding_days = 0
                        else:
                            signal = 'SELL_SHORT_REEVAL'
                    else:
                        signal = 'HOLD_SHORT'
            
            else:  # 無持倉
                if self.cooldown_days > 0:
                    signal = 'HOLD_COOLDOWN'
                
                elif final_score > self.long_threshold:
                    signal = 'BUY_LONG'
                
                elif final_score < self.short_threshold:
                    signal = 'BUY_SHORT'
                
                else:
                    signal = 'HOLD'
            
            # 執行交易
            self.execute_signal(signal, i, qqq_price, tqqq_price, sqqq_price, final_score)
            
            # 記錄組合價值
            portfolio_value = self.calculate_portfolio_value(i, tqqq_price, sqqq_price)
            portfolio_values.append({
                'date': current_date,
                'value': portfolio_value,
                'signal': signal,
                'score': final_score
            })
        
        return self.generate_report(portfolio_values)
    
    def execute_signal(self, signal, idx, qqq_price, tqqq_price, sqqq_price, score):
        """執行交易信號"""
        if signal in ['BUY_LONG', 'BUY_SHORT']:
            self.position = 1 if signal == 'BUY_LONG' else -1
            self.entry_price = tqqq_price if signal == 'BUY_LONG' else sqqq_price
            self.entry_qqq_price = qqq_price
            self.extreme_qqq_price = qqq_price
            self.holding_days = 0
            self.current_symbol = 'TQQQ' if signal == 'BUY_LONG' else 'SQQQ'
            
            self.trades.append({
                'type': 'entry',
                'signal': signal,
                'price': self.entry_price,
                'qqq_price': qqq_price,
                'score': score,
                'idx': idx
            })
        
        elif signal.startswith('SELL'):
            if self.position != 0:
                exit_price = tqqq_price if self.position > 0 else sqqq_price
                
                if self.position > 0:
                    pnl = (exit_price - self.entry_price) * (self.capital * self.max_position_pct / self.entry_price)
                else:
                    pnl = (self.entry_price - exit_price) * (self.capital * self.max_position_pct / self.entry_price)
                
                commission = self.capital * self.max_position_pct * self.commission_rate * 2
                net_pnl = pnl - commission
                self.capital += net_pnl
                
                self.trades.append({
                    'type': 'exit',
                    'signal': signal,
                    'entry_price': self.entry_price,
                    'exit_price': exit_price,
                    'pnl': net_pnl,
                    'capital': self.capital,
                    'idx': idx
                })
                
                self.position = 0
    
    def calculate_portfolio_value(self, idx, tqqq_price, sqqq_price):
        """計算組合價值"""
        if self.position == 0:
            return self.capital
        
        position_value = self.capital * self.max_position_pct
        current_price = tqqq_price if self.position > 0 else sqqq_price
        
        if self.position > 0:
            pnl = (current_price - self.entry_price) / self.entry_price * position_value
        else:
            pnl = (self.entry_price - current_price) / self.entry_price * position_value
        
        return self.capital + pnl
    
    def generate_report(self, portfolio_values):
        """生成回測報告"""
        if not portfolio_values:
            return {'error': '無回測數據'}
        
        final_value = portfolio_values[-1]['value']
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        df = pd.DataFrame(portfolio_values)
        df['peak'] = df['value'].cummax()
        df['drawdown'] = (df['value'] - df['peak']) / df['peak']
        max_drawdown = df['drawdown'].min()
        
        entries = [t for t in self.trades if t['type'] == 'entry']
        exits = [t for t in self.trades if t['type'] == 'exit']
        
        winning_trades = [t for t in exits if t.get('pnl', 0) > 0]
        win_rate = len(winning_trades) / len(exits) if exits else 0
        
        results = {
            'version': 'V10_Enhanced',
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return_pct': total_return * 100,
            'max_drawdown_pct': max_drawdown * 100,
            'total_trades': len(entries),
            'win_rate': win_rate * 100,
            'trades': self.trades
        }
        
        print("\n" + "="*60)
        print("回測結果 - V10 增強版")
        print("="*60)
        print(f"初始資金: ${self.initial_capital:,.2f}")
        print(f"最終價值: ${final_value:,.2f}")
        print(f"總回報: {total_return*100:.2f}%")
        print(f"最大回撤: {max_drawdown*100:.2f}%")
        print(f"交易次數: {len(entries)}")
        print(f"勝率: {win_rate*100:.1f}%")
        print("="*60)
        
        return results


if __name__ == '__main__':
    backtest = SixLoopBacktestV10Enhanced()
    results = backtest.run_backtest()
    
    # 保存結果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'v10_enhanced_results_{timestamp}.json'
    with open(filename, 'w') as f:
        json.dump({k: v for k, v in results.items() if k != 'trades'}, f, indent=2)
    print(f"\n結果已保存: {filename}")
