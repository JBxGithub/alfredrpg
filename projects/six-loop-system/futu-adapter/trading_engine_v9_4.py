"""
六循環交易引擎 V9.4 - 最終優化版
基於 V9 Asymmetric，優化執行層降低回撤

核心改進:
1. 倉位上限: 90% (vs V9 原版 95%)
2. 盈利保護: +10%減倉50%, +20%再減30%
3. 不對稱參數: 多單穩健(-3%/-3%/+15%/7天), 空單敏捷(-2%/-2%/+10%/3天)
"""

import futu as ft
import psycopg2
from datetime import datetime, timezone
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 數據庫配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'trading_db',
    'user': 'postgres',
    'password': 'PostgresqL'
}

class SixLoopTradingEngineV9_4:
    """六循環交易引擎 V9.4 - 最終優化版"""
    
    def __init__(self):
        self.quote_ctx = None
        self.connected = False
        
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
        self.cooldown_period = 1
        
        # 持倉狀態
        self.position = 0
        self.entry_price = 0
        self.entry_qqq_price = 0
        self.extreme_qqq_price = 0
        self.holding_days = 0
        self.cooldown_days = 0
        self.current_symbol = None
        
        # 盈利減倉狀態
        self.initial_shares = 0
        self.remaining_shares = 0
        self.profit_1_done = False
        self.profit_2_done = False
        
    def connect(self):
        """連接到 Futu OpenD"""
        try:
            logger.info("連接到 Futu OpenD...")
            self.quote_ctx = ft.OpenQuoteContext(host='127.0.0.1', port=11111)
            self.quote_ctx.start()
            self.connected = True
            logger.info("✅ 已連接")
            return True
        except Exception as e:
            logger.error(f"❌ 連接失敗: {e}")
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
                    'timestamp': datetime.now(timezone.utc)
                }
        except Exception as e:
            logger.error(f"獲取 {symbol} 失敗: {e}")
        
        return None
    
    def get_scores(self):
        """獲取評分"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT absolute_score, reference_score, final_score
                FROM decisions
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
            logger.error(f"獲取評分失敗: {e}")
        
        return {'absolute': 50, 'reference': 50, 'final': 50}
    
    def evaluate_signal(self, qqq_data, tqqq_data, sqqq_data, scores):
        """評估交易信號"""
        signal = 'HOLD'
        reason = None
        target_symbol = None
        
        if self.cooldown_days > 0:
            self.cooldown_days -= 1
        
        final_score = scores['final']
        
        # ===== 持倉中 =====
        if self.position != 0:
            self.holding_days += 1
            current_qqq = qqq_data['price']
            
            if self.position > 0:
                if current_qqq > self.extreme_qqq_price:
                    self.extreme_qqq_price = current_qqq
            else:
                if current_qqq < self.extreme_qqq_price:
                    self.extreme_qqq_price = current_qqq
            
            qqq_change = (current_qqq - self.entry_qqq_price) / self.entry_qqq_price
            
            if self.position > 0:  # 多單
                etf_price = tqqq_data['price']
                etf_change = (etf_price - self.entry_price) / self.entry_price
                
                # 止損
                if qqq_change <= -self.long_stop_loss:
                    signal = 'SELL_LONG_STOP'
                    reason = f'止損: -{abs(qqq_change)*100:.1f}%'
                elif (current_qqq - self.extreme_qqq_price) / self.extreme_qqq_price <= -self.long_trailing:
                    signal = 'SELL_LONG_TRAILING'
                    reason = '回落止損'
                
                # 盈利減倉 2: +20% 再減 30%
                elif etf_change >= self.profit_level_2 and not self.profit_2_done and self.remaining_shares > self.initial_shares * 0.2:
                    signal = 'SELL_LONG_PROFIT_2'
                    reason = f'+20%再減30%: +{etf_change*100:.1f}%'
                
                # 盈利減倉 1: +10% 減倉 50%
                elif etf_change >= self.profit_level_1 and not self.profit_1_done and self.remaining_shares > self.initial_shares * 0.5:
                    signal = 'SELL_LONG_PROFIT_1'
                    reason = f'+10%減倉50%: +{etf_change*100:.1f}%'
                
                else:
                    signal = 'HOLD_LONG'
            
            else:  # 空單
                etf_price = sqqq_data['price']
                etf_change = (self.entry_price - etf_price) / self.entry_price
                
                if qqq_change >= self.short_stop_loss:
                    signal = 'SELL_SHORT_STOP'
                    reason = f'空單止損: +{qqq_change*100:.1f}%'
                elif (current_qqq - self.extreme_qqq_price) / self.extreme_qqq_price >= self.short_trailing:
                    signal = 'SELL_SHORT_TRAILING'
                    reason = '反彈止損'
                elif etf_change >= self.short_take_profit:
                    signal = 'SELL_SHORT_PROFIT'
                    reason = f'空單止盈: +{etf_change*100:.1f}%'
                else:
                    signal = 'HOLD_SHORT'
        
        # ===== 無持倉 =====
        else:
            if self.cooldown_days > 0:
                signal = 'HOLD_COOLDOWN'
            elif final_score > self.long_threshold:
                signal = 'BUY_LONG'
                target_symbol = 'TQQQ'
                reason = f'評分 {final_score:.1f} > {self.long_threshold}, 做多'
            elif final_score < self.short_threshold:
                signal = 'BUY_SHORT'
                target_symbol = 'SQQQ'
                reason = f'評分 {final_score:.1f} < {self.short_threshold}, 做空'
            else:
                signal = 'HOLD_CASH'
        
        return signal, reason, target_symbol
    
    def execute_trade(self, signal, reason, target_symbol, tqqq_data, sqqq_data, account_balance):
        """執行交易"""
        
        # 平倉操作
        if 'SELL' in signal and self.position != 0:
            if self.position > 0:
                etf_data = tqqq_data
            else:
                etf_data = sqqq_data
            
            # 處理盈利減倉
            if 'PROFIT' in signal:
                if 'PROFIT_1' in signal:
                    sell_shares = int(self.initial_shares * self.reduce_1)
                    self.remaining_shares -= sell_shares
                    self.profit_1_done = True
                elif 'PROFIT_2' in signal:
                    sell_shares = int(self.initial_shares * self.reduce_2)
                    self.remaining_shares -= sell_shares
                    self.profit_2_done = True
                
                self.position = self.remaining_shares if self.position > 0 else -self.remaining_shares
                logger.info(f"部分平倉: {sell_shares} 股，剩餘: {self.remaining_shares}")
                return
            
            # 全平
            if self.position > 0:
                pnl = (etf_data['price'] - self.entry_price) * self.position
                pnl_pct = (etf_data['price'] - self.entry_price) / self.entry_price * 100
            else:
                pnl = (self.entry_price - etf_data['price']) * abs(self.position)
                pnl_pct = (self.entry_price - etf_data['price']) / self.entry_price * 100
            
            logger.info(f"\n🔴 平倉: {self.current_symbol}")
            logger.info(f"   信號: {signal}")
            logger.info(f"   原因: {reason}")
            logger.info(f"   盈虧: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
            
            self.log_trade(signal, self.current_symbol, etf_data['price'], 
                          abs(self.position), pnl, reason)
            
            # 重置
            self.position = 0
            self.entry_price = 0
            self.entry_qqq_price = 0
            self.extreme_qqq_price = 0
            self.holding_days = 0
            self.current_symbol = None
            self.initial_shares = 0
            self.remaining_shares = 0
            self.profit_1_done = False
            self.profit_2_done = False
        
        # 開倉操作
        elif 'BUY' in signal and self.position == 0 and target_symbol:
            if target_symbol == 'TQQQ':
                etf_data = tqqq_data
            else:
                etf_data = sqqq_data
            
            # V9.4: 90% 倉位上限
            shares = int(account_balance * self.max_position_pct / etf_data['price'])
            
            if shares > 0:
                if target_symbol == 'TQQQ':
                    self.position = shares
                else:
                    self.position = -shares
                
                self.entry_price = etf_data['price']
                self.entry_qqq_price = self.get_market_data('US.QQQ')['price']
                self.extreme_qqq_price = self.entry_qqq_price
                self.holding_days = 0
                self.current_symbol = target_symbol
                self.initial_shares = shares
                self.remaining_shares = shares
                self.profit_1_done = False
                self.profit_2_done = False
                
                direction = "做多" if self.position > 0 else "做空"
                logger.info(f"\n🟢 開倉: {target_symbol} ({direction})")
                logger.info(f"   價格: ${etf_data['price']:.2f}")
                logger.info(f"   股數: {shares}")
                logger.info(f"   倉位: {self.max_position_pct*100:.0f}%")
                logger.info(f"   原因: {reason}")
                
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
                  datetime.now(timezone.utc), 'V9.4_Final'))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"記錄失敗: {e}")
    
    def run(self, interval=60):
        """運行引擎"""
        logger.info("=" * 70)
        logger.info("六循環交易引擎 V9.4 - 最終優化版")
        logger.info("=" * 70)
        logger.info(f"倉位上限: {self.max_position_pct*100:.0f}%")
        logger.info(f"盈利減倉: +{self.profit_level_1*100:.0f}%減{self.reduce_1*100:.0f}%, +{self.profit_level_2*100:.0f}%再減{self.reduce_2*100:.0f}%")
        logger.info("=" * 70)
        
        if not self.connect():
            return False
        
        try:
            while True:
                qqq_data = self.get_market_data('US.QQQ')
                tqqq_data = self.get_market_data('US.TQQQ')
                sqqq_data = self.get_market_data('US.SQQQ')
                
                if qqq_data and tqqq_data and sqqq_data:
                    scores = self.get_scores()
                    signal, reason, target = self.evaluate_signal(
                        qqq_data, tqqq_data, sqqq_data, scores
                    )
                    
                    # 假設賬戶餘額
                    account_balance = 100000
                    self.execute_trade(signal, reason, target, tqqq_data, sqqq_data, account_balance)
                
                time.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("\n👋 引擎停止")
        
        finally:
            if self.quote_ctx:
                self.quote_ctx.close()

if __name__ == '__main__':
    engine = SixLoopTradingEngineV9_4()
    engine.run()
