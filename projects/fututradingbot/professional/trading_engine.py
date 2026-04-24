"""
FutuTradingBot 專業級交易引擎
整合 MTF 分析、風險管理、信號生成
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime, date
import yfinance as yf

from indicators import TechnicalIndicators, SignalGenerator
from mtf_analyzer import MTFAnalyzer
from risk_manager import RiskManager, TrailingStopManager


class TradingEngine:
    """專業級交易引擎"""
    
    def __init__(self, initial_capital: float = 100000, symbol: str = 'QQQ'):
        self.symbol = symbol
        self.leveraged_symbol_long = 'TQQQ'   # 3倍做多
        self.leveraged_symbol_short = 'SQQQ'  # 3倍做空
        self.vix_symbol = '^VIX'
        
        # 初始化組件
        self.indicators = TechnicalIndicators()
        self.mtf = MTFAnalyzer()
        self.risk_manager = RiskManager(initial_capital)
        
        # 狀態
        self.position = None  # None, 'long', 'short'
        self.position_size = 0
        self.entry_price = 0
        self.stop_loss = 0
        self.take_profit = 0
        self.entry_date = None
        self.trailing_stop = None
        self.holding_days = 0
        
        # 數據緩存
        self.data_cache = {}
        
    def fetch_data(self, symbol: str, period: str = '2y', interval: str = '1d') -> pd.DataFrame:
        """
        獲取股票數據
        
        Args:
            symbol: 股票代碼
            period: 數據周期
            interval: 時間間隔
            
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"{symbol}_{period}_{interval}"
        
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)
        
        self.data_cache[cache_key] = data
        return data
    
    def prepare_mtf_data(self) -> Dict[str, pd.DataFrame]:
        """
        準備多時間框架數據
        
        Returns:
            dict with daily, weekly, monthly data
        """
        # 獲取日線數據 (2年)
        daily = self.fetch_data(self.symbol, period='2y', interval='1d')
        
        # 重採樣到周線和月線
        weekly = self.mtf.resample_data(daily, 'W')
        monthly = self.mtf.resample_data(daily, 'M')
        
        return {
            'daily': daily,
            'weekly': weekly,
            'monthly': monthly
        }
    
    def generate_signal(self, current_date: date) -> Dict:
        """
        生成交易信號
        
        Args:
            current_date: 當前日期
            
        Returns:
            dict with signal details
        """
        try:
            # 準備數據
            mtf_data = self.prepare_mtf_data()
            
            # 獲取 VIX
            vix_data = self.fetch_data(self.vix_symbol, period='1y', interval='1d')
            current_vix = vix_data['Close'].iloc[-1] if len(vix_data) > 0 else 20
            
            # MTF 分析
            signal = self.mtf.get_mtf_signal(
                mtf_data['monthly'],
                mtf_data['weekly'],
                mtf_data['daily']
            )
            
            # 檢查風險管理
            can_trade, reason = self.risk_manager.can_trade(current_date, current_vix)
            
            result = {
                'date': current_date,
                'signal': signal['final_signal'],
                'confidence': signal.get('confidence', 'low'),
                'can_trade': can_trade,
                'reason': reason if not can_trade else signal.get('reason', ''),
                'vix': current_vix,
                'monthly_trend': signal['monthly'].get('signal', 'unknown'),
                'weekly_trend': signal['weekly'].get('signal', 'unknown'),
                'daily_analysis': signal['daily']
            }
            
            return result
            
        except Exception as e:
            return {
                'date': current_date,
                'signal': 'error',
                'error': str(e)
            }
    
    def execute_entry(self, signal: Dict, current_price: float, 
                     atr: float) -> Dict:
        """
        執行入場 (支持分層倉位)
        
        Args:
            signal: 信號字典
            current_price: 當前價格
            atr: ATR 值
            
        Returns:
            dict with execution result
        """
        if signal['signal'] not in ['long', 'short']:
            return {'executed': False, 'reason': '無有效信號'}
        
        if not signal['can_trade']:
            return {'executed': False, 'reason': signal['reason']}
        
        if self.position is not None:
            return {'executed': False, 'reason': f'已有持倉: {self.position}'}
        
        # 確定方向
        direction = signal['signal']
        
        # 獲取分層倉位大小
        position_size_pct = signal.get('position_size', 0.95)
        
        # 計算止損 (ATR 1.5-2倍)
        stop_loss = self.risk_manager.calculate_stop_loss(
            current_price, atr, direction, multiplier=1.5
        )
        
        # 計算止盈 (1:2 風險報酬比)
        take_profit = self.risk_manager.calculate_take_profit(
            current_price, stop_loss, risk_reward_ratio=2.0
        )
        
        # 計算倉位大小 (根據信號強度調整)
        position_calc = self.risk_manager.calculate_position_size(
            current_price, stop_loss, signal['vix']
        )
        
        if not position_calc['valid']:
            return {'executed': False, 'reason': position_calc['reason']}
        
        # 根據信號強度調整倉位
        adjusted_position_size = int(position_calc['position_size'] * position_size_pct)
        
        # 執行入場
        self.position = direction
        self.position_size = adjusted_position_size
        self.entry_price = current_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.entry_date = signal['date']
        self.holding_days = 0
        self.signal_strength = signal.get('strength', 'medium')
        
        # 初始化移動止損
        self.trailing_stop = TrailingStopManager(trailing_type='ema20')
        self.trailing_stop.extreme_price = current_price
        
        # 記錄交易
        trade_record = {
            'action': 'open',
            'date': signal['date'],
            'direction': direction,
            'symbol': self.leveraged_symbol_long if direction == 'long' else self.leveraged_symbol_short,
            'entry_price': current_price,
            'position_size': adjusted_position_size,
            'position_size_pct': position_size_pct,
            'signal_strength': self.signal_strength,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_amount': position_calc['risk_amount'] * position_size_pct,
            'vix': signal['vix']
        }
        self.risk_manager.record_trade(trade_record)
        
        return {
            'executed': True,
            'direction': direction,
            'signal_strength': self.signal_strength,
            'position_size': adjusted_position_size,
            'position_size_pct': position_size_pct,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'risk_amount': position_calc['risk_amount'] * position_size_pct
        }
    
    def check_exit(self, current_price: float, current_date: date,
                  ema20: float = None) -> Dict:
        """
        檢查出場條件
        
        Args:
            current_price: 當前價格
            current_date: 當前日期
            ema20: 20 EMA (用於移動止損)
            
        Returns:
            dict with exit decision
        """
        if self.position is None:
            return {'should_exit': False}
        
        self.holding_days += 1
        
        exit_reason = None
        exit_price = current_price
        
        # 1. 止損檢查
        if self.position == 'long' and current_price <= self.stop_loss:
            exit_reason = f'止損觸發 ({current_price:.2f} <= {self.stop_loss:.2f})'
        elif self.position == 'short' and current_price >= self.stop_loss:
            exit_reason = f'止損觸發 ({current_price:.2f} >= {self.stop_loss:.2f})'
        
        # 2. 止盈檢查
        elif self.position == 'long' and current_price >= self.take_profit:
            exit_reason = f'止盈觸發 ({current_price:.2f} >= {self.take_profit:.2f})'
        elif self.position == 'short' and current_price <= self.take_profit:
            exit_reason = f'止盈觸發 ({current_price:.2f} <= {self.take_profit:.2f})'
        
        # 3. 移動止損檢查
        if exit_reason is None and self.trailing_stop:
            self.trailing_stop.update_trailing_stop(current_price, ema20, self.position)
            if self.trailing_stop.check_exit(current_price, self.position):
                exit_reason = f'移動止損 ({self.trailing_stop.current_stop:.2f})'
                exit_price = self.trailing_stop.current_stop
        
        # 4. MACD 反轉 (簡化檢查)
        # 實際應用中需要傳入 MACD 數據
        
        if exit_reason:
            # 計算盈虧
            if self.position == 'long':
                pnl = (current_price - self.entry_price) * self.position_size
                pnl_pct = (current_price - self.entry_price) / self.entry_price * 100
            else:  # short
                pnl = (self.entry_price - current_price) * self.position_size
                pnl_pct = (self.entry_price - current_price) / self.entry_price * 100
            
            # 記錄交易
            trade_record = {
                'action': 'close',
                'date': current_date,
                'direction': self.position,
                'exit_price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'holding_days': self.holding_days,
                'reason': exit_reason
            }
            self.risk_manager.record_trade(trade_record)
            
            # 重置持倉
            result = {
                'should_exit': True,
                'exit_price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'reason': exit_reason,
                'holding_days': self.holding_days
            }
            
            self.position = None
            self.position_size = 0
            self.trailing_stop = None
            
            return result
        
        return {'should_exit': False}
    
    def run_daily(self, current_date: date) -> Dict:
        """
        每日運行
        
        Args:
            current_date: 當前日期
            
        Returns:
            dict with daily actions
        """
        results = {
            'date': current_date,
            'actions': []
        }
        
        # 生成信號
        signal = self.generate_signal(current_date)
        results['signal'] = signal
        
        # 獲取當前數據
        try:
            daily_data = self.fetch_data(self.symbol, period='1mo', interval='1d')
            current_price = daily_data['Close'].iloc[-1]
            atr = self.indicators.calculate_atr(daily_data).iloc[-1]
            ema20 = daily_data['Close'].ewm(span=20).mean().iloc[-1]
        except:
            results['error'] = '無法獲取當前數據'
            return results
        
        # 檢查現有持倉
        if self.position is not None:
            exit_check = self.check_exit(current_price, current_date, ema20)
            if exit_check['should_exit']:
                results['actions'].append({
                    'action': 'exit',
                    'details': exit_check
                })
        
        # 檢查新入場
        elif signal['signal'] in ['long', 'short'] and signal['can_trade']:
            entry_result = self.execute_entry(signal, current_price, atr)
            if entry_result['executed']:
                results['actions'].append({
                    'action': 'entry',
                    'details': entry_result
                })
            else:
                results['actions'].append({
                    'action': 'entry_rejected',
                    'reason': entry_result['reason']
                })
        
        # 風險報告
        results['risk_report'] = self.risk_manager.get_risk_report()
        
        return results


if __name__ == '__main__':
    print("TradingEngine 模組已載入")
    print("專業級交易引擎 - 整合 MTF + 風險管理")
    print("核心: 絕不逆月線大勢")
