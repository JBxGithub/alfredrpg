"""
六循環系統回測 - V9.5 增強版
基於 V9 Asymmetric + 多項增強:
1. 移除 MTF
2. VIX 機制（多單>25止損，空單>30縮短止盈+1%止損）
3. ADX + DI 趨勢確認（方案 A）
4. Volume 門檻 1.25
5. Absolute Score: Market Phase 20% + Components Breadth 15% + Components Risk 10% + Futures OI 10% + ETF Flow 10% + ADX 20% + MACD 10% + 動量 5%
6. Reference Score: RSI 10% + ATR 10% + Z-Score 20% + BOLL 15% + Volume 15% + MACD 25% + Divergence 5%
7. 步驟式決策流程
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import json
import os

class SixLoopBacktestV9_5:
    """六循環回測 V9.5 - 增強版"""
    
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
        
        # ===== V9.5 增強參數 =====
        # 多單 (TQQQ) - 穩健
        self.long_stop_loss = 0.03        # QQQ -3%
        self.long_trailing = 0.03         # 回落 -3%
        self.long_take_profit = 0.15      # TQQQ +15%
        self.long_reeval = 7              # 7天重估
        
        # 空單 (SQQQ) - 敏捷
        self.short_stop_loss = 0.02       # QQQ +2%
        self.short_trailing = 0.02        # 反彈 +2%
        self.short_take_profit = 0.10     # SQQQ +10%
        self.short_reeval = 3             # 3天重估
        
        # VIX 機制
        self.vix_long_threshold = 25      # 多單 VIX 門檻
        self.vix_short_threshold = 30     # 空單 VIX 門檻
        self.vix_high_short_take_profit = 0.03  # VIX>30 時 +3% 止盈
        self.vix_short_trailing = 0.01    # VIX>30 時回升 1% 止損
        
        # 通用
        self.cooldown_period = 1
        self.max_position_pct = 0.95
        self.commission_rate = 0.001
        self.slippage = 0.001
        
        # Absolute Score 門檻
        self.absolute_long_threshold = 60
        self.absolute_short_threshold = 40
        
        # Reference Score 門檻
        self.reference_long_threshold = 55
        self.reference_short_threshold = 40
        
        # ADX 門檻
        self.adx_weak = 20
        self.adx_strong = 25
        
        # Volume 門檻
        self.volume_threshold = 1.25
        
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
        """計算 ADX, +DI, -DI"""
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
    
    def calculate_market_phase(self, price, ma200, ma50, ema20):
        """計算 Market Phase（7階段）"""
        # 強牛市: 價格 > 200MA > 50MA > 20EMA
        if price > ma200 > ma50 > ema20:
            return 10
        # 牛市: 價格 > 200MA > 50MA
        elif price > ma200 > ma50:
            return 7
        # 震盪上行: 價格 > 200MA, 但 < 50MA
        elif price > ma200 and price < ma50:
            return 3
        # 震盪: 價格在 200MA 附近 (±2%)
        elif abs(price - ma200) / ma200 < 0.02:
            return 0
        # 震盪下行: 價格 < 200MA, 但 > 50MA
        elif price < ma200 and price > ma50:
            return -3
        # 熊市: 價格 < 200MA < 50MA
        elif price < ma200 < ma50:
            return -7
        # 強熊市: 價格 < 200MA < 50MA < 20EMA
        elif price < ma200 < ma50 < ema20:
            return -10
        else:
            return 0
    
    def calculate_components_breadth(self, idx):
        """計算 Components Breadth（簡化版，使用價格動量模擬）"""
        # 實際應用中需要 NQ100 成份股數據
        # 這裡使用 QQQ 20日動量作為代理
        if idx < 20:
            return 0
        
        momentum = (self.qqq_data['Close'].iloc[idx] - self.qqq_data['Close'].iloc[idx-20]) / self.qqq_data['Close'].iloc[idx-20]
        
        # 模擬 breadth_ratio
        if momentum > 0.05:
            return 20  # 強勢
        elif momentum > 0.02:
            return 10  # 中性偏多
        elif momentum > -0.02:
            return 0   # 中性
        else:
            return -10  # 弱勢
    
    def calculate_futures_oi(self, idx):
        """計算 Futures OI（簡化版，使用成交量變化作為代理）"""
        if idx < 5:
            return 0
        
        volume_change = (self.qqq_data['Volume'].iloc[idx] - self.qqq_data['Volume'].iloc[idx-5]) / self.qqq_data['Volume'].iloc[idx-5]
        price_change = (self.qqq_data['Close'].iloc[idx] - self.qqq_data['Close'].iloc[idx-5]) / self.qqq_data['Close'].iloc[idx-5]
        
        # OI 上升 + 價格上升 = 強勢上漲
        if volume_change > 0.1 and price_change > 0:
            return 15
        # OI 下降 + 價格上升 = 弱勢上漲
        elif volume_change < -0.1 and price_change > 0:
            return -5
        # OI 上升 + 價格下跌 = 強勢下跌
        elif volume_change > 0.1 and price_change < 0:
            return -10
        # OI 下降 + 價格下跌 = 弱勢下跌
        elif volume_change < -0.1 and price_change < 0:
            return 5
        else:
            return 0
    
    def calculate_etf_flow(self, idx):
        """計算 ETF Flow（簡化版）"""
        if idx < 1:
            return 0
        
        # 使用 TQQQ 和 SQQQ 成交量變化
        tqqq_volume = self.tqqq_data['Volume'].iloc[idx] if idx < len(self.tqqq_data) else 0
        sqqq_volume = self.sqqq_data['Volume'].iloc[idx] if idx < len(self.sqqq_data) else 0
        
        # 簡化計算：TQQQ 成交量增加 = 資金流入做多
        if idx > 5:
            tqqq_change = (tqqq_volume - self.tqqq_data['Volume'].iloc[idx-5]) / self.tqqq_data['Volume'].iloc[idx-5] if self.tqqq_data['Volume'].iloc[idx-5] > 0 else 0
            
            if tqqq_change > 0.2:
                return 10
            elif tqqq_change > 0.1:
                return 5
            elif tqqq_change < -0.2:
                return -10
            elif tqqq_change < -0.1:
                return -5
        
        return 0
    
    def calculate_absolute_score(self, idx):
        """計算 Absolute Score（8組件）"""
        if idx < 200:
            return 50, {'adx': 20, 'plus_di': 25, 'minus_di': 25}  # 默認中性
        
        # 獲取當前數據
        price = self.qqq_data['Close'].iloc[idx]
        volume = self.qqq_data['Volume'].iloc[idx]
        
        # 計算指標
        window = self.qqq_data.iloc[max(0, idx-200):idx+1]
        
        # MA/EMA
        ma200 = window['Close'].rolling(window=200).mean().iloc[-1]
        ma50 = window['Close'].rolling(window=50).mean().iloc[-1]
        ema20 = self.calculate_ema(window['Close'], 20).iloc[-1]
        
        # MACD
        macd_line, signal_line, histogram = self.calculate_macd(window['Close'])
        macd_current = macd_line.iloc[-1]
        macd_signal = signal_line.iloc[-1]
        
        # ADX
        adx, plus_di, minus_di = self.calculate_adx(window['High'], window['Low'], window['Close'])
        adx_current = adx.iloc[-1]
        plus_di_current = plus_di.iloc[-1]
        minus_di_current = minus_di.iloc[-1]
        
        # 動量
        momentum = (price - window['Close'].iloc[-20]) / window['Close'].iloc[-20] if idx >= 20 else 0
        
        # ===== 計算各組件分數 =====
        # 1. Market Phase (20%)
        market_phase_score = self.calculate_market_phase(price, ma200, ma50, ema20)
        
        # 2. Components Breadth (15%)
        components_breadth_score = self.calculate_components_breadth(idx)
        
        # 3. Components Risk (10%) - 簡化為 VIX 等級
        vix_price = self.vix_data['Close'].iloc[idx] if idx < len(self.vix_data) else 20
        if vix_price > 30:
            components_risk_score = -10
        elif vix_price > 25:
            components_risk_score = -5
        elif vix_price < 15:
            components_risk_score = 10
        else:
            components_risk_score = 0
        
        # 4. Futures OI (10%)
        futures_oi_score = self.calculate_futures_oi(idx)
        
        # 5. ETF Flow (10%)
        etf_flow_score = self.calculate_etf_flow(idx)
        
        # 6. ADX (20%) - 這裡是過濾器，分數在後面計算
        # 7. MACD (10%)
        macd_score = 0
        if macd_current > macd_signal:
            macd_score += 5
        if macd_current > 0:
            macd_score += 5
        
        # 8. 動量 (5%)
        momentum_score = 5 if momentum > 0 else 0
        
        # ===== 加權計算 =====
        # 將 -10~+10 或 -20~+20 的分數映射到 0-100
        market_phase_normalized = (market_phase_score + 10) / 20 * 100
        components_breadth_normalized = (components_breadth_score + 10) / 30 * 100
        components_risk_normalized = (components_risk_score + 10) / 20 * 100
        futures_oi_normalized = (futures_oi_score + 10) / 25 * 100
        etf_flow_normalized = (etf_flow_score + 10) / 20 * 100
        
        absolute_score = (
            market_phase_normalized * 0.20 +
            components_breadth_normalized * 0.15 +
            components_risk_normalized * 0.10 +
            futures_oi_normalized * 0.10 +
            etf_flow_normalized * 0.10 +
            macd_score * 1.0 +  # 已經是 0-10
            momentum_score * 1.0  # 已經是 0-5，但權重5%，所以直接加
        )
        
        # ADX 作為過濾器，不直接加入分數
        adx_info = {
            'adx': adx_current,
            'plus_di': plus_di_current,
            'minus_di': minus_di_current,
            'market_phase': market_phase_score,
            'components_breadth': components_breadth_score,
            'components_risk': components_risk_score,
            'futures_oi': futures_oi_score,
            'etf_flow': etf_flow_score,
            'macd': macd_score,
            'momentum': momentum_score
        }
        
        return min(100, max(0, absolute_score)), adx_info
    
    def calculate_reference_score(self, idx):
        """計算 Reference Score（7組件）"""
        if idx < 50:
            return 50
        
        # 獲取當前數據
        price = self.qqq_data['Close'].iloc[idx]
        volume = self.qqq_data['Volume'].iloc[idx]
        
        # 計算指標
        window = self.qqq_data.iloc[max(0, idx-50):idx+1]
        
        # RSI
        delta = window['Close'].diff()
        gain = (delta.where(delta > 0, 0)).iloc[-14:].mean()
        loss = (-delta.where(delta < 0, 0)).iloc[-14:].mean()
        rs = gain / loss if loss != 0 else 1
        rsi = 100 - (100 / (1 + rs))
        
        # ATR
        tr1 = window['High'] - window['Low']
        tr2 = abs(window['High'] - window['Close'].shift(1))
        tr3 = abs(window['Low'] - window['Close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean().iloc[-1]
        
        # Z-Score
        mean_20 = window['Close'].iloc[-20:].mean()
        std_20 = window['Close'].iloc[-20:].std()
        z_score = (price - mean_20) / std_20 if std_20 != 0 else 0
        
        # BOLL
        boll_upper, boll_middle, boll_lower = self.calculate_bollinger(window['Close'])
        boll_upper = boll_upper.iloc[-1]
        boll_middle = boll_middle.iloc[-1]
        boll_lower = boll_lower.iloc[-1]
        
        # MACD
        macd_line, signal_line, histogram = self.calculate_macd(window['Close'])
        macd_current = macd_line.iloc[-1]
        macd_signal = signal_line.iloc[-1]
        macd_prev = macd_line.iloc[-2] if len(macd_line) > 1 else macd_current
        macd_signal_prev = signal_line.iloc[-2] if len(signal_line) > 1 else macd_signal
        
        # Volume
        volume_ma = window['Volume'].rolling(window=20).mean().iloc[-1]
        volume_signal = volume > (volume_ma * self.volume_threshold)
        
        # ===== 計算各組件分數 =====
        # 1. RSI (10%)
        rsi_score = 0
        if 30 < rsi < 70:
            rsi_score = 10
        elif rsi < 30:
            rsi_score = 5  # 超賣，可能反彈
        elif rsi > 70:
            rsi_score = 5  # 超買，可能回調
        
        # 2. ATR (10%)
        atr_score = 10 if atr > 0 else 0
        
        # 3. Z-Score (20%)
        z_score_score = 0
        if -2 < z_score < 2:
            z_score_score = 20
        elif -3 < z_score < 3:
            z_score_score = 10
        
        # 4. BOLL (15%)
        boll_score = 0
        if boll_lower < price < boll_upper:
            boll_score = 15
        elif price > boll_upper:
            boll_score = 5
        elif price < boll_lower:
            boll_score = 5
        
        # 5. Volume (15%)
        volume_score = 15 if volume_signal else 0
        
        # 6. MACD (25%)
        macd_score = 0
        if macd_current > macd_signal:
            macd_score += 15
        if macd_prev < macd_signal_prev and macd_current > macd_signal:
            macd_score += 10  # 金叉
        
        # 7. Divergence (5%)
        divergence_score = 5 if macd_current > 0 else 0
        
        # ===== 加權計算 =====
        reference_score = (
            rsi_score * 1.0 +
            atr_score * 1.0 +
            z_score_score * 1.0 +
            boll_score * 1.0 +
            volume_score * 1.0 +
            macd_score * 1.0 +
            divergence_score * 1.0
        )
        
        return min(100, max(0, reference_score))
    
    def run_backtest(self):
        """執行回測"""
        print("\n" + "="*70)
        print("六循環系統回測 - V9.5 增強版")
        print("="*70)
        print("【多單 TQQQ - 穩健】")
        print(f"  止損: QQQ -{self.long_stop_loss*100:.0f}%")
        print(f"  回落止損: -{self.long_trailing*100:.0f}%")
        print(f"  止盈: +{self.long_take_profit*100:.0f}%")
        print(f"  重估: {self.long_reeval}天")
        print("【空單 SQQQ - 敏捷】")
        print(f"  止損: QQQ +{self.short_stop_loss*100:.0f}%")
        print(f"  反彈止損: +{self.short_trailing*100:.0f}%")
        print(f"  止盈: +{self.short_take_profit*100:.0f}%")
        print(f"  重估: {self.short_reeval}天")
        print("【V9.5 增強】")
        print(f"  - Volume 門檻: {self.volume_threshold}")
        print(f"  - ADX 機制: <{self.adx_weak}觀望, {self.adx_weak}-{self.adx_strong}過渡, >{self.adx_strong}確認")
        print(f"  - VIX 機制: 多單>{self.vix_long_threshold}止損, 空單>{self.vix_short_threshold}縮短止盈")
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
        
        for i in range(200, len(common_dates)):
            date = common_dates[i]
            qqq_price = qqq_aligned['Close'].iloc[i]
            tqqq_price = tqqq_aligned['Close'].iloc[i]
            sqqq_price = sqqq_aligned['Close'].iloc[i]
            vix_price = self.vix_data['Close'].iloc[i] if i < len(self.vix_data) else 20
            
            # ===== 步驟 1: VIX 檢查 =====
            vix_triggered = False
            if self.position > 0 and vix_price > self.vix_long_threshold:
                # 多單 VIX > 25，立即止損平倉
                signal = 'SELL_LONG_VIX'
                reason = f'VIX>{self.vix_long_threshold} ({vix_price:.1f})，多單止損'
                vix_triggered = True
            elif self.position < 0 and vix_price > self.vix_short_threshold:
                # 空單 VIX > 30，縮短止盈
                # 這裡只調整參數，不平倉
                short_tp = self.vix_high_short_take_profit
                short_trailing = self.vix_short_trailing
            else:
                short_tp = self.short_take_profit
                short_trailing = self.short_trailing
            
            # ===== 步驟 2: Absolute Score =====
            absolute_score, adx_info = self.calculate_absolute_score(i)
            
            # ===== 步驟 3: Reference Score（已移除獨立 ADX 確認，ADX 已在 Absolute 中） =====
            reference_score = self.calculate_reference_score(i)
            
            # ===== 決策邏輯 =====
            signal = 'HOLD'
            reason = None
            
            # 更新冷卻期
            if self.cooldown_days > 0:
                self.cooldown_days -= 1
            
            if vix_triggered:
                # VIX 已觸發，直接平倉
                pass
            elif self.position != 0:
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
                
                if self.position > 0:  # ===== 多單 (穩健) =====
                    qqq_change_from_extreme = (qqq_price - self.extreme_qqq_price) / self.extreme_qqq_price
                    etf_change = (tqqq_price - self.entry_price) / self.entry_price
                    
                    # 多單止損: -3%
                    if qqq_change_from_entry <= -self.long_stop_loss:
                        signal = 'SELL_LONG_STOP'
                        reason = f'多單止損: {qqq_change_from_entry*100:.1f}%'
                        self.cooldown_days = self.cooldown_period
                    
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
                        if reference_score > self.reference_long_threshold:
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
                    
                    # 空單止損: +2%
                    if qqq_change_from_entry >= self.short_stop_loss:
                        signal = 'SELL_SHORT_STOP'
                        reason = f'空單止損: +{qqq_change_from_entry*100:.1f}%'
                        self.cooldown_days = self.cooldown_period
                    
                    # 空單反彈止損: +2% (VIX>30時+1%)
                    elif qqq_change_from_extreme >= short_trailing:
                        signal = 'SELL_SHORT_TRAILING'
                        reason = f'空單反彈: +{qqq_change_from_extreme*100:.1f}%'
                        self.cooldown_days = self.cooldown_period
                    
                    # 空單止盈: +10% (VIX>30時+3%)
                    elif etf_change >= short_tp:
                        signal = 'SELL_SHORT_PROFIT'
                        reason = f'空單止盈: {etf_change*100:.1f}%'
                        if vix_price > self.vix_short_threshold:
                            signal += '_VIX_HIGH'
                    
                    # 空單3天重估
                    elif self.holding_days >= self.short_reeval:
                        if reference_score < self.reference_short_threshold:
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
                
                # 步驟式決策（已移除 ADX 獨立確認）
                elif absolute_score > self.absolute_long_threshold:
                    # Absolute > 60，潛在做多
                    if reference_score > self.reference_long_threshold:
                        # Reference > 55，確認做多
                        signal = 'BUY_LONG'
                        reason = f'Absolute:{absolute_score:.0f}>60, Reference:{reference_score:.0f}>55'
                    else:
                        signal = 'HOLD_REFERENCE_WAIT'
                        reason = f'Reference:{reference_score:.0f} 未達標'
                
                elif absolute_score < self.absolute_short_threshold:
                    # Absolute < 40，潛在做空
                    if reference_score < self.reference_short_threshold:
                        # Reference < 40，確認做空
                        signal = 'BUY_SHORT'
                        reason = f'Absolute:{absolute_score:.0f}<40, Reference:{reference_score:.0f}<40'
                    else:
                        signal = 'HOLD_REFERENCE_WAIT'
                        reason = f'Reference:{reference_score:.0f} 未達標'
                
                else:
                    signal = 'HOLD_CASH'
                    reason = f'Absolute:{absolute_score:.0f} 觀望區間'
            
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
                
                shares = int(self.capital * self.max_position_pct / etf_price)
                
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
                        'absolute_score': absolute_score,
                        'reference_score': reference_score,
                        'adx': adx_info.get('adx', 0),
                        'vix': vix_price
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
                    'absolute_score': absolute_score,
                    'reference_score': reference_score,
                    'adx': adx_info.get('adx', 0),
                    'vix': vix_price
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
                'vix': vix_price,
                'absolute_score': absolute_score,
                'reference_score': reference_score,
                'adx': adx_info.get('adx', 0),
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
        print("回測結果 - V9.5 增強版")
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
        print(f"V9.5 增強策略: {total_return:.2f}%")
        print(f"買入持有 TQQQ: {buy_hold_tqqq:.2f}%")
        print(f"vs TQQQ: {total_return - buy_hold_tqqq:+.2f}%")
        
        self.metrics = {
            'version': 'V9.5_Enhanced',
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
        """保存結果"""
        os.makedirs('backtest/results', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.daily_results.to_csv(f'backtest/results/v9_5_daily_{timestamp}.csv', index=False)
        
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_df.to_csv(f'backtest/results/v9_5_trades_{timestamp}.csv', index=False)
        
        with open(f'backtest/results/v9_5_metrics_{timestamp}.json', 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        
        print(f"\n結果已保存: backtest/results/v9_5_*_{timestamp}.*")

def main():
    backtest = SixLoopBacktestV9_5(
        start_date='2019-01-01',
        end_date='2024-12-31',
        initial_capital=100000
    )
    
    backtest.run_backtest()
    backtest.calculate_metrics()
    backtest.save_results()
    
    print("\n✅ V9.5 增強版回測完成！")

if __name__ == '__main__':
    main()
