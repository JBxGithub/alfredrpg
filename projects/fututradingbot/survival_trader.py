#!/usr/bin/env python3
"""
Survival Trader - 精簡版套利腳本
目標: 持續套利，確保API續費資金
時間: 週一至五 21:30 - 04:00
帳戶: 6896 (零限制)
"""

import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project path
sys.path.insert(0, str(Path(__file__).parent))

from src.api.futu_client import FutuTradeClient, FutuQuoteClient, Market, TrdEnv, TrdSide
from src.strategies.tqqq_long_short import TQQQLongShortStrategy, TQQQStrategyConfig

# ============ 生存配置 ============
ACCOUNT_ID = 6896  # 閒置帳戶
MIN_PROFIT_TARGET = 50  # 每日最低盈利目標 (USD)
MAX_DAILY_LOSS = 100    # 每日最大虧損限制 (USD)
TRADING_HOURS = {
    'start': 21,  # 21:30
    'end': 4      # 04:00
}

# TQQQ 策略配置 (優化版)
STRATEGY_CONFIG = {
    'entry_zscore': 1.65,
    'exit_zscore': 0.5,
    'stop_loss_zscore': 3.5,
    'position_pct': 0.30,  # 保守30%倉位
    'max_positions': 1,     # 單一持倉
    'rsi_overbought': 70.0,
    'rsi_oversold': 30.0,
    'take_profit_pct': 0.04,  # 4%止盈
    'stop_loss_pct': 0.02,    # 2%止損
    'time_stop_days': 5,
}

class SurvivalTrader:
    """生存交易者 - 精簡高效"""
    
    def __init__(self):
        self.quote_client = None
        self.trade_client = None
        self.strategy = TQQQLongShortStrategy(STRATEGY_CONFIG)
        self.daily_pnl = 0
        self.trades_today = 0
        self.is_running = False
        
    def connect(self):
        """連接富途API"""
        print("[生存模式] 連接富途 OpenD...")
        
        self.quote_client = FutuQuoteClient()
        if not self.quote_client.connect():
            print("[錯誤] 行情連接失敗")
            return False
            
        self.trade_client = FutuTradeClient()
        if not self.trade_client.connect():
            print("[錯誤] 交易連接失敗")
            return False
            
        # 解鎖交易
        self.trade_client.unlock_trade("011087")
        
        print("[生存模式] 連接成功")
        return True
    
    def check_account(self):
        """檢查帳戶資金"""
        account = self.trade_client.get_account_info(TrdEnv.REAL)
        if account:
            cash = account.get('cash', 0)
            total = account.get('total_assets', 0)
            print(f"[帳戶] 現金: ${cash:,.2f} | 總資產: ${total:,.2f}")
            return cash > 1000  # 至少$1000才能交易
        return False
    
    def get_tqqq_data(self):
        """獲取TQQQ數據"""
        try:
            # 獲取60日歷史數據計算Z-Score
            df = self.quote_client.get_kline("TQQQ", Market.US, 'K_DAY', 60)
            if df is not None and len(df) >= 60:
                return df
        except Exception as e:
            print(f"[錯誤] 獲取數據失敗: {e}")
        return None
    
    def check_signal(self):
        """檢查交易信號"""
        df = self.get_tqqq_data()
        if df is None:
            return None
            
        # 生成信號
        signal_data = self.strategy.generate_signal(df)
        return signal_data
    
    def execute_trade(self, signal_type, price):
        """執行交易"""
        if signal_type == 'BUY':
            side = TrdSide.BUY
            qty = 100  # 固定100股
        elif signal_type == 'SELL':
            side = TrdSide.SELL
            qty = 100
        else:
            return None
            
        order = self.trade_client.place_order(
            symbol="TQQQ",
            market=Market.US,
            side=side,
            qty=qty,
            price=price,
            env=TrdEnv.REAL
        )
        
        if order:
            self.trades_today += 1
            print(f"[交易] {signal_type} TQQQ @ ${price:.2f} x {qty}")
        return order
    
    def run(self):
        """主循環"""
        print("="*50)
        print("[生存模式啟動] FutuTradingBot - 6896帳戶")
        print("目標: 每日盈利$50+ | 最大虧損$100")
        print("="*50)
        
        if not self.connect():
            return
            
        if not self.check_account():
            print("[錯誤] 帳戶資金不足")
            return
        
        self.is_running = True
        
        try:
            while self.is_running:
                now = datetime.now()
                hour = now.hour
                
                # 檢查交易時間 (21:30 - 04:00)
                is_trading_hours = (hour >= 21) or (hour < 4)
                
                if not is_trading_hours:
                    print(f"[{now.strftime('%H:%M')}] 非交易時間，等待...")
                    time.sleep(300)  # 5分鐘檢查一次
                    continue
                
                # 檢查每日虧損限制
                if self.daily_pnl <= -MAX_DAILY_LOSS:
                    print(f"[風控] 達到每日虧損限制 ${MAX_DAILY_LOSS}，停止交易")
                    break
                
                # 檢查信號
                signal = self.check_signal()
                if signal and signal.get('signal') != 0:
                    signal_type = 'BUY' if signal['signal'] == 1 else 'SELL'
                    zscore = signal.get('zscore', 0)
                    
                    print(f"[{now.strftime('%H:%M:%S')}] 信號: {signal_type} | Z-Score: {zscore:.2f}")
                    
                    # 獲取當前價格
                    quote = self.quote_client.get_quote("TQQQ", Market.US)
                    if quote:
                        price = quote.get('last_price', 0)
                        self.execute_trade(signal_type, price)
                
                # 每30秒檢查一次 (Heartbeat)
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\n[生存模式] 用戶停止")
        except Exception as e:
            print(f"[錯誤] {e}")
        finally:
            self.stop()
    
    def stop(self):
        """停止交易"""
        self.is_running = False
        if self.quote_client:
            self.quote_client.close()
        if self.trade_client:
            self.trade_client.close()
        print("[生存模式] 已停止")

if __name__ == "__main__":
    trader = SurvivalTrader()
    trader.run()
