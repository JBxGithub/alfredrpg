"""
六循環交易引擎 V8 - Plan B 多空雙向版
基於靚仔要求:
- 牛市: 做多 TQQQ (評分 > 60)
- 熊市: 做空 SQQQ (評分 < 40)
- 震盪: 持有現金 (40-60)
- 對稱止損止盈設計
"""

import futu as ft
import psycopg2
from datetime import datetime, timezone
import time

# 數據庫配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'trading_db',
    'user': 'postgres',
    'password': 'PostgresqL'
}

class SixLoopTradingEngineV8Bidirectional:
    """六循環交易引擎 V8 - 多空雙向版"""
    
    def __init__(self):
        self.quote_ctx = None
        self.connected = False
        
        # V8 多空對稱參數
        self.qqq_stop_loss = 0.03           # 日間止損: QQQ ±3%
        self.qqq_trailing_stop = 0.03       # 回落/反彈止損: ±3%
        self.take_profit_pct = 0.15         # 止盈: ±15%
        self.reeval_days = 7                # 7天評估
        self.cooldown_period = 1            # 1天冷卻期
        
        # 閾值
        self.long_threshold = 60            # 做多閾值
        self.short_threshold = 40           # 做空閾值
        self.continue_long = 60             # 續持多單
        self.continue_short = 40            # 續持空單
        
        # 持倉狀態
        self.position = 0                   # 正數=多單，負數=空單，0=無持倉
        self.entry_price = 0                # 入場價
        self.entry_qqq_price = 0            # QQQ入場參考價
        self.extreme_qqq_price = 0          # 持倉期間極值(多單=最高，空單=最低)
        self.holding_days = 0               # 持倉天數
        self.cooldown_days = 0              # 冷卻期
        self.current_symbol = None          # 當前持倉代碼 (TQQQ 或 SQQQ)
        
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
    
    def get_market_data(self, symbol):
        """獲取市場數據"""
        if not self.connected:
            return None
        
        try:
            ret, data = self.quote_ctx.get_market_snapshot([symbol])
            if ret == ft.RET_OK and not data.empty:
                return {
                    'symbol': symbol,
                    'price': float(data['last_price'].values[0]),
                    'open': float(data['open_price'].values[0]),
                    'high': float(data['high_price'].values[0]),
                    'low': float(data['low_price'].values[0]),
                    'volume': int(data['volume'].values[0]),
                    'timestamp': datetime.now(timezone.utc)
                }
        except Exception as e:
            print(f"[{datetime.now()}] 獲取 {symbol} 失敗: {e}")
        
        return None
    
    def get_qqq_data(self):
        """獲取 QQQ 數據"""
        return self.get_market_data('US.QQQ')
    
    def get_tqqq_data(self):
        """獲取 TQQQ 數據"""
        return self.get_market_data('US.TQQQ')
    
    def get_sqqq_data(self):
        """獲取 SQQQ 數據 (3x 反向)"""
        return self.get_market_data('US.SQQQ')
    
    def calculate_scores(self):
        """計算評分"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
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
                    'absolute': float(result[0]),
                    'reference': float(result[1]),
                    'final': float(result[2])
                }
        except Exception as e:
            print(f"[{datetime.now()}] 獲取評分失敗: {e}")
        
        return {'absolute': 50, 'reference': 50, 'final': 50}
    
    def evaluate_signal(self, qqq_data, tqqq_data, sqqq_data, scores):
        """評估交易信號 - 多空雙向"""
        signal = 'HOLD'
        reason = None
        target_symbol = None
        
        # 更新冷卻期
        if self.cooldown_days > 0:
            self.cooldown_days -= 1
        
        final_score = scores['final']
        
        # ===== 持倉中 =====
        if self.position != 0:
            self.holding_days += 1
            
            current_qqq = qqq_data['price']
            
            # 更新極值
            if self.position > 0:  # 多單
                if current_qqq > self.extreme_qqq_price:
                    self.extreme_qqq_price = current_qqq
            else:  # 空單
                if current_qqq < self.extreme_qqq_price:
                    self.extreme_qqq_price = current_qqq
            
            # 計算變化
            qqq_change_from_entry = (current_qqq - self.entry_qqq_price) / self.entry_qqq_price
            
            if self.position > 0:  # 多單
                qqq_change_from_extreme = (current_qqq - self.extreme_qqq_price) / self.extreme_qqq_price
                etf_change = (tqqq_data['price'] - self.entry_price) / self.entry_price
                
                # 多單止損: QQQ -3%
                if qqq_change_from_entry <= -self.qqq_stop_loss:
                    signal = 'SELL_LONG_STOP'
                    reason = f'多單止損: QQQ {qqq_change_from_entry*100:.1f}%'
                    self.cooldown_days = self.cooldown_period
                
                # 多單回落止損: -3%
                elif qqq_change_from_extreme <= -self.qqq_trailing_stop:
                    signal = 'SELL_LONG_TRAILING'
                    reason = f'多單回落: {qqq_change_from_extreme*100:.1f}%'
                    self.cooldown_days = self.cooldown_period
                
                # 多單止盈: +15%
                elif etf_change >= self.take_profit_pct:
                    signal = 'SELL_LONG_PROFIT'
                    reason = f'多單止盈: {etf_change*100:.1f}%'
                
                # 7天重估
                elif self.holding_days >= self.reeval_days:
                    if final_score > self.continue_long:
                        signal = 'HOLD_LONG_CONTINUE'
                        self.holding_days = 0
                        reason = '牛市續持多單'
                    else:
                        signal = 'SELL_LONG_REEVAL'
                        reason = '多單7天重估賣出'
                
                else:
                    signal = 'HOLD_LONG'
            
            else:  # 空單 (position < 0)
                qqq_change_from_extreme = (current_qqq - self.extreme_qqq_price) / self.extreme_qqq_price
                etf_change = (self.entry_price - sqqq_data['price']) / self.entry_price  # 空單盈利計算
                
                # 空單止損: QQQ +3% (反向)
                if qqq_change_from_entry >= self.qqq_stop_loss:
                    signal = 'SELL_SHORT_STOP'
                    reason = f'空單止損: QQQ +{qqq_change_from_entry*100:.1f}%'
                    self.cooldown_days = self.cooldown_period
                
                # 空單反彈止損: +3% (反向)
                elif qqq_change_from_extreme >= self.qqq_trailing_stop:
                    signal = 'SELL_SHORT_TRAILING'
                    reason = f'空單反彈: +{qqq_change_from_extreme*100:.1f}%'
                    self.cooldown_days = self.cooldown_period
                
                # 空單止盈: SQQQ +15%
                elif etf_change >= self.take_profit_pct:
                    signal = 'SELL_SHORT_PROFIT'
                    reason = f'空單止盈: {etf_change*100:.1f}%'
                
                # 7天重估
                elif self.holding_days >= self.reeval_days:
                    if final_score < self.continue_short:
                        signal = 'HOLD_SHORT_CONTINUE'
                        self.holding_days = 0
                        reason = '熊市續持空單'
                    else:
                        signal = 'SELL_SHORT_REEVAL'
                        reason = '空單7天重估賣出'
                
                else:
                    signal = 'HOLD_SHORT'
        
        # ===== 無持倉 =====
        else:
            if self.cooldown_days > 0:
                signal = 'HOLD_COOLDOWN'
                reason = f'冷卻期剩餘 {self.cooldown_days} 天'
            
            # 做多信號
            elif final_score > self.long_threshold:
                signal = 'BUY_LONG'
                target_symbol = 'TQQQ'
                reason = f'評分 {final_score:.1f} > {self.long_threshold}, 做多'
            
            # 做空信號
            elif final_score < self.short_threshold:
                signal = 'BUY_SHORT'
                target_symbol = 'SQQQ'
                reason = f'評分 {final_score:.1f} < {self.short_threshold}, 做空'
            
            else:
                signal = 'HOLD_CASH'
                reason = f'評分 {final_score:.1f}, 觀望'
        
        return signal, reason, target_symbol
    
    def execute_trade(self, signal, reason, target_symbol, tqqq_data, sqqq_data):
        """執行交易"""
        
        # 平倉操作
        if 'SELL' in signal and self.position != 0:
            if self.position > 0:  # 平多單
                etf_data = tqqq_data
                pnl = (etf_data['price'] - self.entry_price) * self.position
                pnl_pct = (etf_data['price'] - self.entry_price) / self.entry_price * 100
            else:  # 平空單
                etf_data = sqqq_data
                pnl = (self.entry_price - etf_data['price']) * abs(self.position)
                pnl_pct = (self.entry_price - etf_data['price']) / self.entry_price * 100
            
            print(f"\n🔴 [{datetime.now().strftime('%H:%M:%S')}] 平倉: {self.current_symbol}")
            print(f"   信號: {signal}")
            print(f"   原因: {reason}")
            print(f"   價格: ${etf_data['price']:.2f}")
            print(f"   入場: ${self.entry_price:.2f}")
            print(f"   盈虧: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
            print(f"   持倉天數: {self.holding_days}")
            
            self.log_trade(signal, self.current_symbol, etf_data['price'], 
                          abs(self.position), pnl, reason)
            
            # 重置
            self.position = 0
            self.entry_price = 0
            self.entry_qqq_price = 0
            self.extreme_qqq_price = 0
            self.holding_days = 0
            self.current_symbol = None
        
        # 開倉操作
        elif 'BUY' in signal and self.position == 0 and target_symbol:
            if target_symbol == 'TQQQ':
                etf_data = tqqq_data
            else:
                etf_data = sqqq_data
            
            # 假設資金
            available_capital = 100000
            shares = int(available_capital * 0.95 / etf_data['price'])
            
            if shares > 0:
                if target_symbol == 'TQQQ':
                    self.position = shares  # 正數 = 多單
                else:
                    self.position = -shares  # 負數 = 空單
                
                self.entry_price = etf_data['price']
                self.entry_qqq_price = self.get_qqq_data()['price']
                self.extreme_qqq_price = self.entry_qqq_price
                self.entry_date = datetime.now(timezone.utc)
                self.holding_days = 0
                self.current_symbol = target_symbol
                
                direction = "做多" if self.position > 0 else "做空"
                print(f"\n🟢 [{datetime.now().strftime('%H:%M:%S')}] 開倉: {target_symbol} ({direction})")
                print(f"   價格: ${etf_data['price']:.2f}")
                print(f"   股數: {abs(shares)}")
                print(f"   QQQ參考: ${self.entry_qqq_price:.2f}")
                print(f"   原因: {reason}")
                
                self.log_trade(signal, target_symbol, etf_data['price'], shares, None, reason)
    
    def log_trade(self, action, symbol, price, shares, pnl, reason):
        """記錄交易"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO trades 
                (symbol, action, price, shares, pnl, reason, timestamp, strategy_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (symbol, action, price, shares, pnl, reason, 
                  datetime.now(timezone.utc), 'V8_Bidirectional'))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"[{datetime.now()}] 記錄失敗: {e}")
    
    def print_status(self, qqq_data, tqqq_data, sqqq_data, scores, signal, reason):
        """打印狀態"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 六循環 V8-PlanB 狀態")
        print("-" * 60)
        print(f"QQQ:  ${qqq_data['price']:.2f}")
        print(f"TQQQ: ${tqqq_data['price']:.2f} | SQQQ: ${sqqq_data['price']:.2f}")
        print(f"評分: A={scores['absolute']:.1f} R={scores['reference']:.1f} F={scores['final']:.1f}")
        print(f"信號: {signal}")
        if reason:
            print(f"原因: {reason}")
        
        if self.position != 0:
            direction = "多單" if self.position > 0 else "空單"
            symbol = self.current_symbol
            etf_price = tqqq_data['price'] if symbol == 'TQQQ' else sqqq_data['price']
            
            if self.position > 0:
                etf_change = (etf_price - self.entry_price) / self.entry_price * 100
            else:
                etf_change = (self.entry_price - etf_price) / self.entry_price * 100
            
            qqq_change = (qqq_data['price'] - self.entry_qqq_price) / self.entry_qqq_price * 100
            
            print(f"\n持倉狀態: {direction} {symbol}")
            print(f"  入場價: ${self.entry_price:.2f} (QQQ: ${self.entry_qqq_price:.2f})")
            print(f"  極值價: ${self.extreme_qqq_price:.2f}")
            print(f"  現價: ${etf_price:.2f}")
            print(f"  ETF變化: {etf_change:+.2f}%")
            print(f"  QQQ變化: {qqq_change:+.2f}%")
            print(f"  持倉天數: {self.holding_days}")
        
        if self.cooldown_days > 0:
            print(f"\n冷卻期: {self.cooldown_days} 天")
        
        print("-" * 60)
    
    def run(self, interval=60):
        """運行引擎"""
        print("=" * 70)
        print("六循環交易引擎 V8 - Plan B 多空雙向版")
        print("=" * 70)
        print(f"策略參數:")
        print(f"  做多閾值: >{self.long_threshold}")
        print(f"  做空閾值: <{self.short_threshold}")
        print(f"  日間止損: QQQ ±{self.qqq_stop_loss*100:.0f}%")
        print(f"  回落/反彈止損: ±{self.qqq_trailing_stop*100:.0f}%")
        print(f"  止盈: ETF ±{self.take_profit_pct*100:.0f}%")
        print(f"  7天評估: 多單續持>{self.continue_long}, 空單續持<{self.continue_short}")
        print("=" * 70)
        
        if not self.connect():
            return False
        
        try:
            while True:
                qqq_data = self.get_qqq_data()
                tqqq_data = self.get_tqqq_data()
                sqqq_data = self.get_sqqq_data()
                
                if qqq_data and tqqq_data and sqqq_data:
                    scores = self.calculate_scores()
                    signal, reason, target = self.evaluate_signal(
                        qqq_data, tqqq_data, sqqq_data, scores
                    )
                    
                    self.print_status(qqq_data, tqqq_data, sqqq_data, scores, signal, reason)
                    self.execute_trade(signal, reason, target, tqqq_data, sqqq_data)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] 停止引擎")
        except Exception as e:
            print(f"[{datetime.now()}] 錯誤: {e}")
        finally:
            self.close()
        
        return True
    
    def close(self):
        """關閉"""
        if self.quote_ctx:
            self.quote_ctx.close()
            self.connected = False
            print(f"[{datetime.now()}] 已關閉")

def main():
    engine = SixLoopTradingEngineV8Bidirectional()
    engine.run(interval=60)

if __name__ == '__main__':
    main()
