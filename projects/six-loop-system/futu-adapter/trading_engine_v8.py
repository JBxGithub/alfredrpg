"""
六循環交易引擎 V8 - 最終版
基於回測優化結果:
- 日間止損: QQQ -3%
- 高位回落止損: -3%
- 止盈: TQQQ +15%
- 7天評估: 牛市續持(>60)
- 冷卻期: 止損後1日
"""

import futu as ft
import psycopg2
from datetime import datetime, timezone, timedelta
import time
import json
import os

# 數據庫配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'trading_db',
    'user': 'postgres',
    'password': 'PostgresqL'
}

class SixLoopTradingEngineV8:
    """六循環交易引擎 V8"""
    
    def __init__(self):
        self.quote_ctx = None
        self.connected = False
        
        # V8 策略參數
        self.qqq_stop_loss = 0.03           # QQQ -3%
        self.qqq_trailing_stop = 0.03       # 高位回落 -3%
        self.take_profit_pct = 0.15         # TQQQ +15%
        self.reeval_days = 7                # 7天評估
        self.cooldown_period = 1            # 1天冷卻期
        
        # 交易狀態
        self.position = 0                   # 當前持倉
        self.entry_price = 0                # 入場價
        self.entry_qqq_price = 0            # QQQ入場價
        self.highest_qqq_price = 0          # 持倉期間最高價
        self.entry_date = None              # 入場日期
        self.holding_days = 0               # 持倉天數
        self.cooldown_days = 0              # 冷卻期
        
        # 評分參數
        self.buy_threshold = 60             # 買入閾值
        self.sell_threshold = 40            # 賣出閾值
        self.continue_threshold = 60        # 續持閾值
        
    def connect(self):
        """連接到 Futu OpenD"""
        try:
            print(f"[{datetime.now()}] 連接到 Futu OpenD...")
            self.quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)
            self.quote_ctx.start()
            self.connected = True
            print(f"[{datetime.now()}] ✅ 已連接")
            return True
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 連接失敗: {e}")
            return False
    
    def get_qqq_data(self):
        """獲取 QQQ 數據"""
        if not self.connected:
            return None
        
        try:
            ret, data = self.quote_ctx.get_market_snapshot(['US.QQQ'])
            if ret == ft.RET_OK and not data.empty:
                return {
                    'price': float(data['last_price'].values[0]),
                    'open': float(data['open_price'].values[0]),
                    'high': float(data['high_price'].values[0]),
                    'low': float(data['low_price'].values[0]),
                    'volume': int(data['volume'].values[0]),
                    'timestamp': datetime.now(timezone.utc)
                }
        except Exception as e:
            print(f"[{datetime.now()}] 獲取 QQQ 失敗: {e}")
        
        return None
    
    def get_tqqq_data(self):
        """獲取 TQQQ 數據"""
        if not self.connected:
            return None
        
        try:
            ret, data = self.quote_ctx.get_market_snapshot(['US.TQQQ'])
            if ret == ft.RET_OK and not data.empty:
                return {
                    'price': float(data['last_price'].values[0]),
                    'open': float(data['open_price'].values[0]),
                    'high': float(data['high_price'].values[0]),
                    'low': float(data['low_price'].values[0]),
                    'volume': int(data['volume'].values[0]),
                    'timestamp': datetime.now(timezone.utc)
                }
        except Exception as e:
            print(f"[{datetime.now()}] 獲取 TQQQ 失敗: {e}")
        
        return None
    
    def calculate_scores(self, qqq_data, historical_data=None):
        """計算 Absolute + Reference 評分"""
        # 簡化版：基於價格動量
        # 實際應從數據庫獲取技術指標
        
        current_price = qqq_data['price']
        
        # 模擬評分 (實際應連接 Node-RED 計算結果)
        # 這裡使用簡化邏輯
        
        # 假設從數據庫獲取最新評分
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # 獲取最新評分
            cursor.execute("""
                SELECT absolute_score, reference_score, final_score
                FROM absolute_scores
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return {
                    'absolute': result[0],
                    'reference': result[1],
                    'final': result[2]
                }
        except Exception as e:
            print(f"[{datetime.now()}] 獲取評分失敗: {e}")
        
        # 默認中性評分
        return {'absolute': 50, 'reference': 50, 'final': 50}
    
    def evaluate_signal(self, qqq_data, tqqq_data, scores):
        """評估交易信號"""
        signal = 'HOLD'
        reason = None
        
        # 更新冷卻期
        if self.cooldown_days > 0:
            self.cooldown_days -= 1
        
        # ===== V8 交易邏輯 =====
        if self.position > 0:
            # 有持倉，檢查賣出條件
            self.holding_days += 1
            
            current_qqq = qqq_data['price']
            current_tqqq = tqqq_data['price']
            
            # 更新最高價
            if current_qqq > self.highest_qqq_price:
                self.highest_qqq_price = current_qqq
            
            # 計算變化
            qqq_change_from_entry = (current_qqq - self.entry_qqq_price) / self.entry_qqq_price
            qqq_change_from_high = (current_qqq - self.highest_qqq_price) / self.highest_qqq_price
            tqqq_change = (current_tqqq - self.entry_price) / self.entry_price
            
            # 1. 日間止損: QQQ -3%
            if qqq_change_from_entry <= -self.qqq_stop_loss:
                signal = 'SELL_QQQ_STOP'
                reason = f'QQQ止損: {qqq_change_from_entry*100:.1f}%'
                self.cooldown_days = self.cooldown_period
            
            # 2. 高位回落止損: -3%
            elif qqq_change_from_high <= -self.qqq_trailing_stop:
                signal = 'SELL_TRAILING_STOP'
                reason = f'高位回落: {qqq_change_from_high*100:.1f}%'
                self.cooldown_days = self.cooldown_period
            
            # 3. 止盈: TQQQ +15%
            elif tqqq_change >= self.take_profit_pct:
                signal = 'SELL_PROFIT'
                reason = f'止盈: {tqqq_change*100:.1f}%'
            
            # 4. 7天重新評估
            elif self.holding_days >= self.reeval_days:
                if scores['final'] > self.continue_threshold:
                    signal = 'HOLD_BULL_CONTINUE'
                    self.holding_days = 0  # 重置，續持
                    reason = '牛市續持'
                else:
                    signal = 'SELL_REEVALUATE'
                    reason = '7天重估賣出'
            
            else:
                signal = 'HOLD'
        
        else:
            # 無持倉，檢查買入
            if self.cooldown_days > 0:
                signal = 'HOLD_COOLDOWN'
                reason = f'冷卻期剩餘 {self.cooldown_days} 天'
            elif scores['final'] > self.buy_threshold:
                signal = 'BUY'
                reason = f'評分 {scores["final"]:.1f} > {self.buy_threshold}'
            else:
                signal = 'HOLD'
        
        return signal, reason
    
    def execute_buy(self, tqqq_data):
        """執行買入"""
        try:
            # 計算買入股數 (使用 95% 資金)
            # 實際應查詢賬戶餘額
            available_capital = 100000  # 假設
            shares = int(available_capital * 0.95 / tqqq_data['price'])
            
            if shares > 0:
                # 更新狀態
                self.position = shares
                self.entry_price = tqqq_data['price']
                self.entry_qqq_price = self.get_qqq_data()['price']
                self.highest_qqq_price = self.entry_qqq_price
                self.entry_date = datetime.now(timezone.utc)
                self.holding_days = 0
                
                print(f"\n🟢 [{datetime.now()}] 買入 TQQQ")
                print(f"   價格: ${tqqq_data['price']:.2f}")
                print(f"   股數: {shares}")
                print(f"   QQQ參考: ${self.entry_qqq_price:.2f}")
                
                # 記錄到數據庫
                self.log_trade('BUY', tqqq_data['price'], shares)
                
                return True
        except Exception as e:
            print(f"[{datetime.now()}] 買入失敗: {e}")
        
        return False
    
    def execute_sell(self, tqqq_data, signal, reason):
        """執行賣出"""
        try:
            if self.position > 0:
                # 計算盈虧
                pnl = (tqqq_data['price'] - self.entry_price) * self.position
                pnl_pct = (tqqq_data['price'] - self.entry_price) / self.entry_price * 100
                
                print(f"\n🔴 [{datetime.now()}] 賣出 TQQQ")
                print(f"   信號: {signal}")
                print(f"   原因: {reason}")
                print(f"   價格: ${tqqq_data['price']:.2f}")
                print(f"   入場: ${self.entry_price:.2f}")
                print(f"   盈虧: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
                print(f"   持倉天數: {self.holding_days}")
                
                # 記錄到數據庫
                self.log_trade(signal, tqqq_data['price'], self.position, pnl, reason)
                
                # 重置狀態
                self.position = 0
                self.entry_price = 0
                self.entry_qqq_price = 0
                self.highest_qqq_price = 0
                self.holding_days = 0
                
                return True
        except Exception as e:
            print(f"[{datetime.now()}] 賣出失敗: {e}")
        
        return False
    
    def log_trade(self, action, price, shares, pnl=None, reason=None):
        """記錄交易到數據庫"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO trades 
                (symbol, action, price, shares, pnl, reason, timestamp, strategy_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, ('TQQQ', action, price, shares, pnl, reason, 
                  datetime.now(timezone.utc), 'V8'))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"[{datetime.now()}] 記錄交易失敗: {e}")
    
    def print_status(self, qqq_data, tqqq_data, scores, signal, reason):
        """打印狀態"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 六循環 V8 狀態")
        print("-" * 50)
        print(f"QQQ:  ${qqq_data['price']:.2f}")
        print(f"TQQQ: ${tqqq_data['price']:.2f}")
        print(f"評分: A={scores['absolute']:.1f} R={scores['reference']:.1f} F={scores['final']:.1f}")
        print(f"信號: {signal}")
        if reason:
            print(f"原因: {reason}")
        
        if self.position > 0:
            qqq_change = (qqq_data['price'] - self.entry_qqq_price) / self.entry_qqq_price * 100
            tqqq_change = (tqqq_data['price'] - self.entry_price) / self.entry_price * 100
            print(f"\n持倉狀態:")
            print(f"  入場價: ${self.entry_price:.2f} (QQQ: ${self.entry_qqq_price:.2f})")
            print(f"  最高價: ${self.highest_qqq_price:.2f}")
            print(f"  QQQ變化: {qqq_change:+.2f}%")
            print(f"  TQQQ變化: {tqqq_change:+.2f}%")
            print(f"  持倉天數: {self.holding_days}")
        
        if self.cooldown_days > 0:
            print(f"\n冷卻期: {self.cooldown_days} 天")
        
        print("-" * 50)
    
    def run(self, interval=60):
        """運行交易引擎"""
        print("=" * 60)
        print("六循環交易引擎 V8 - 最終版")
        print("=" * 60)
        print(f"策略參數:")
        print(f"  日間止損: QQQ -{self.qqq_stop_loss*100:.0f}%")
        print(f"  高位回落: -{self.qqq_trailing_stop*100:.0f}%")
        print(f"  止盈: TQQQ +{self.take_profit_pct*100:.0f}%")
        print(f"  7天評估: 續持閾值 >{self.continue_threshold}")
        print(f"  冷卻期: {self.cooldown_period} 天")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            while True:
                # 獲取數據
                qqq_data = self.get_qqq_data()
                tqqq_data = self.get_tqqq_data()
                
                if qqq_data and tqqq_data:
                    # 計算評分
                    scores = self.calculate_scores(qqq_data)
                    
                    # 評估信號
                    signal, reason = self.evaluate_signal(qqq_data, tqqq_data, scores)
                    
                    # 打印狀態
                    self.print_status(qqq_data, tqqq_data, scores, signal, reason)
                    
                    # 執行交易
                    if signal == 'BUY':
                        self.execute_buy(tqqq_data)
                    elif 'SELL' in signal:
                        self.execute_sell(tqqq_data, signal, reason)
                
                # 等待下一次輪詢
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] 停止交易引擎")
        except Exception as e:
            print(f"[{datetime.now()}] 運行錯誤: {e}")
        finally:
            self.close()
        
        return True
    
    def close(self):
        """關閉連接"""
        if self.quote_ctx:
            self.quote_ctx.close()
            self.connected = False
            print(f"[{datetime.now()}] 已關閉連接")

def main():
    """主函數"""
    engine = SixLoopTradingEngineV8()
    engine.run(interval=60)  # 每分鐘檢查一次

if __name__ == '__main__':
    main()
