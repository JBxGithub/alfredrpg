"""
動量策略 - Momentum Strategy

基於價格動量進行交易
適用於趨勢市場

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.strategies.base import BaseStrategy, TradeSignal, SignalType
from src.indicators.technical import TechnicalIndicators
from src.analysis.mtf_analyzer import MTFAnalyzer
from src.utils.logger import logger


@dataclass
class MomentumConfig:
    """動量策略配置"""
    short_period: int = 12              # 短期動量週期
    medium_period: int = 26             # 中期動量週期
    long_period: int = 50               # 長期動量週期
    momentum_threshold: float = 0.02    # 動量閾值
    rsi_period: int = 14                # RSI週期
    rsi_overbought: float = 70.0        # RSI超買水平
    rsi_oversold: float = 30.0          # RSI超賣水平
    stop_loss_pct: float = 0.04         # 止損比例
    take_profit_pct: float = 0.08       # 止盈比例
    position_pct: float = 0.02          # 倉位比例
    trailing_stop: bool = True          # 啟用移動止損
    trailing_stop_pct: float = 0.05     # 移動止損比例


class MomentumStrategy(BaseStrategy):
    """
    動量策略
    
    核心邏輯:
    1. 計算多週期動量 (短期、中期、長期)
    2. 當短期動量 > 中期動量 > 長期動量時買入
    3. 當短期動量 < 中期動量 < 長期動量時賣出
    4. 使用RSI過濾極端情況
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'short_period': 12,
            'medium_period': 26,
            'long_period': 50,
            'momentum_threshold': 0.02,
            'rsi_period': 14,
            'rsi_overbought': 70.0,
            'rsi_oversold': 30.0,
            'stop_loss_pct': 0.04,
            'take_profit_pct': 0.08,
            'position_pct': 0.02,
            'trailing_stop': True,
            'trailing_stop_pct': 0.05
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name="Momentum", config=default_config)
        
        self.short_period = self.config['short_period']
        self.medium_period = self.config['medium_period']
        self.long_period = self.config['long_period']
        self.momentum_threshold = self.config['momentum_threshold']
        self.rsi_period = self.config['rsi_period']
        self.rsi_overbought = self.config['rsi_overbought']
        self.rsi_oversold = self.config['rsi_oversold']
        self.stop_loss_pct = self.config['stop_loss_pct']
        self.take_profit_pct = self.config['take_profit_pct']
        self.position_pct = self.config['position_pct']
        self.trailing_stop = self.config['trailing_stop']
        self.trailing_stop_pct = self.config['trailing_stop_pct']
        
        # MTF整合
        self.use_mtf = default_config.get('use_mtf', True)
        self.mtf_min_score = default_config.get('mtf_min_score', 60.0)
        if self.use_mtf:
            self.mtf_analyzer = MTFAnalyzer()
            logger.info("動量策略: MTF分析已啟用")
        
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"動量策略初始化 | 短期: {self.short_period}, 中期: {self.medium_period}, 長期: {self.long_period}")
    
    def on_data(self, data: Dict[str, Any]) -> Optional[TradeSignal]:
        """處理行情數據"""
        code = data.get('code')
        df = data.get('df')
        
        if df is None or len(df) < self.long_period + 10:
            return None
        
        # 檢查現有持倉
        if code in self.positions:
            return self._check_exit(code, df)
        
        # 計算動量
        momentum_signal = self._calculate_momentum(df)
        
        if momentum_signal is None:
            return None
        
        # 計算RSI
        rsi = self._calculate_rsi(df)
        
        current_price = df['close'].iloc[-1]
        
        # 多頭動量信號
        if momentum_signal == 'bullish':
            # RSI過濾 - 避免超買區域
            if rsi < self.rsi_overbought:
                qty = self._calculate_position_size(current_price)
                stop_loss = current_price * (1 - self.stop_loss_pct)
                take_profit = current_price * (1 + self.take_profit_pct)
                
                signal = TradeSignal(
                    code=code,
                    signal=SignalType.BUY,
                    price=current_price,
                    qty=qty,
                    reason=f"動量買入 | 多週期動量共振 | RSI: {rsi:.1f}",
                    metadata={
                        'rsi': rsi,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'strategy': 'momentum',
                        'momentum_signal': momentum_signal
                    }
                )
                
                self._record_entry(code, signal, True)
                return signal
        
        # 空頭動量信號
        if momentum_signal == 'bearish':
            # RSI過濾 - 避免超賣區域
            if rsi > self.rsi_oversold:
                qty = self._calculate_position_size(current_price)
                stop_loss = current_price * (1 + self.stop_loss_pct)
                take_profit = current_price * (1 - self.take_profit_pct)
                
                signal = TradeSignal(
                    code=code,
                    signal=SignalType.SELL,
                    price=current_price,
                    qty=qty,
                    reason=f"動量賣出 | 多週期動量共振 | RSI: {rsi:.1f}",
                    metadata={
                        'rsi': rsi,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'strategy': 'momentum',
                        'momentum_signal': momentum_signal
                    }
                )
                
                self._record_entry(code, signal, False)
                return signal
        
        return None
    
    def _calculate_momentum(self, df: pd.DataFrame) -> Optional[str]:
        """計算動量信號"""
        if len(df) < self.long_period:
            return None
        
        close = df['close']
        
        # 計算不同週期的動量
        short_momentum = (close.iloc[-1] - close.iloc[-self.short_period]) / close.iloc[-self.short_period]
        medium_momentum = (close.iloc[-1] - close.iloc[-self.medium_period]) / close.iloc[-self.medium_period]
        long_momentum = (close.iloc[-1] - close.iloc[-self.long_period]) / close.iloc[-self.long_period]
        
        # 多頭動量: 短期 > 中期 > 長期，且都為正
        if (short_momentum > medium_momentum > long_momentum and 
            short_momentum > self.momentum_threshold):
            return 'bullish'
        
        # 空頭動量: 短期 < 中期 < 長期，且都為負
        if (short_momentum < medium_momentum < long_momentum and 
            short_momentum < -self.momentum_threshold):
            return 'bearish'
        
        return None
    
    def _calculate_rsi(self, df: pd.DataFrame) -> float:
        """計算RSI"""
        close = df['close']
        
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def _check_exit(self, code: str, df: pd.DataFrame) -> Optional[TradeSignal]:
        """檢查出場條件"""
        if code not in self.positions:
            return None
        
        position = self.positions[code]
        current_price = df['close'].iloc[-1]
        entry_price = position['entry_price']
        is_long = position['is_long']
        highest_price = position.get('highest_price', entry_price)
        lowest_price = position.get('lowest_price', entry_price)
        
        # 更新最高/最低價格
        if is_long:
            highest_price = max(highest_price, current_price)
            position['highest_price'] = highest_price
        else:
            lowest_price = min(lowest_price, current_price)
            position['lowest_price'] = lowest_price
        
        # 計算盈虧
        pnl_pct = (current_price - entry_price) / entry_price
        if not is_long:
            pnl_pct = -pnl_pct
        
        exit_reason = None
        
        # 止損出場
        if pnl_pct <= -self.stop_loss_pct:
            exit_reason = f"止損觸發 | 虧損: {pnl_pct*100:.2f}%"
        
        # 止盈出場
        elif pnl_pct >= self.take_profit_pct:
            exit_reason = f"止盈觸發 | 盈利: {pnl_pct*100:.2f}%"
        
        # 移動止損
        elif self.trailing_stop:
            if is_long:
                trailing_stop_price = highest_price * (1 - self.trailing_stop_pct)
                if current_price <= trailing_stop_price and pnl_pct > 0:
                    exit_reason = f"移動止損 | 最高: {highest_price:.2f}, 當前: {current_price:.2f}"
            else:
                trailing_stop_price = lowest_price * (1 + self.trailing_stop_pct)
                if current_price >= trailing_stop_price and pnl_pct > 0:
                    exit_reason = f"移動止損 | 最低: {lowest_price:.2f}, 當前: {current_price:.2f}"
        
        # 動量反轉出場
        momentum_signal = self._calculate_momentum(df)
        if momentum_signal:
            if is_long and momentum_signal == 'bearish':
                exit_reason = f"動量反轉 | 空頭信號出現"
            elif not is_long and momentum_signal == 'bullish':
                exit_reason = f"動量反轉 | 多頭信號出現"
        
        if exit_reason:
            signal = TradeSignal(
                code=code,
                signal=SignalType.SELL if is_long else SignalType.BUY,
                price=current_price,
                qty=position['qty'],
                reason=exit_reason,
                metadata={
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl_pct': pnl_pct
                }
            )
            
            del self.positions[code]
            return signal
        
        return None
    
    def _calculate_position_size(self, price: float) -> int:
        """計算倉位大小"""
        account_value = 1000000
        position_value = account_value * self.position_pct
        return max(int(position_value / price), 0)
    
    def _record_entry(self, code: str, signal: TradeSignal, is_long: bool):
        """記錄進場"""
        self.positions[code] = {
            'entry_price': signal.price,
            'qty': signal.qty,
            'is_long': is_long,
            'entry_time': pd.Timestamp.now(),
            'highest_price': signal.price,
            'lowest_price': signal.price
        }
    
    def on_order_update(self, order: Dict[str, Any]):
        """處理訂單更新"""
        pass
    
    def on_position_update(self, position: Dict[str, Any]):
        """處理持倉更新"""
        pass
