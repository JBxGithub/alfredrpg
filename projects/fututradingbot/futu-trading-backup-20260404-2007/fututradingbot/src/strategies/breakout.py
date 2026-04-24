"""
突破策略 - Breakout Strategy

基於價格突破支撐/阻力位進行交易
適用於趨勢啟動階段

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from src.strategies.base import BaseStrategy, TradeSignal, SignalType
from src.indicators.technical import TechnicalIndicators
from src.utils.logger import logger


@dataclass
class BreakoutConfig:
    """突破策略配置"""
    lookback_period: int = 20           # 回看週期 (計算支撐阻力)
    volume_threshold: float = 1.5       # 成交量閾值倍數
    confirmation_bars: int = 1          # 確認突破的K線數
    stop_loss_pct: float = 0.03         # 止損比例
    take_profit_pct: float = 0.06       # 止盈比例
    position_pct: float = 0.02          # 倉位比例
    min_breakout_pct: float = 0.02      # 最小突破幅度


class BreakoutStrategy(BaseStrategy):
    """
    突破策略
    
    核心邏輯:
    1. 識別支撐位和阻力位 (近期高低點)
    2. 價格突破阻力位且成交量放大時買入
    3. 價格跌破支撐位且成交量放大時賣出
    4. 使用ATR動態調整止損
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'lookback_period': 20,
            'volume_threshold': 1.5,
            'confirmation_bars': 1,
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.06,
            'position_pct': 0.02,
            'min_breakout_pct': 0.02
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name="Breakout", config=default_config)
        
        self.lookback_period = self.config['lookback_period']
        self.volume_threshold = self.config['volume_threshold']
        self.confirmation_bars = self.config['confirmation_bars']
        self.stop_loss_pct = self.config['stop_loss_pct']
        self.take_profit_pct = self.config['take_profit_pct']
        self.position_pct = self.config['position_pct']
        self.min_breakout_pct = self.config['min_breakout_pct']
        
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.recent_highs: Dict[str, float] = {}
        self.recent_lows: Dict[str, float] = {}
        
        logger.info(f"突破策略初始化 | 回看週期: {self.lookback_period}, 成交量閾值: {self.volume_threshold}x")
    
    def on_data(self, data: Dict[str, Any]) -> Optional[TradeSignal]:
        """處理行情數據"""
        code = data.get('code')
        df = data.get('df')
        
        if df is None or len(df) < self.lookback_period + 5:
            return None
        
        # 檢查現有持倉
        if code in self.positions:
            return self._check_exit(code, df)
        
        # 計算支撐阻力位
        resistance, support = self._calculate_levels(df)
        
        if resistance is None or support is None:
            return None
        
        # 保存近期高低點
        self.recent_highs[code] = resistance
        self.recent_lows[code] = support
        
        current_price = df['close'].iloc[-1]
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]
        
        # 檢查成交量
        volume_ok = self._check_volume(df)
        
        # 向上突破
        if current_high > resistance:
            breakout_pct = (current_high - resistance) / resistance
            
            if breakout_pct >= self.min_breakout_pct and volume_ok:
                qty = self._calculate_position_size(current_price)
                stop_loss = current_price * (1 - self.stop_loss_pct)
                take_profit = current_price * (1 + self.take_profit_pct)
                
                signal = TradeSignal(
                    code=code,
                    signal=SignalType.BUY,
                    price=current_price,
                    qty=qty,
                    reason=f"向上突破 | 突破幅度: {breakout_pct*100:.2f}% | 成交量確認: {volume_ok}",
                    metadata={
                        'resistance': resistance,
                        'breakout_pct': breakout_pct,
                        'volume_confirmed': volume_ok,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'strategy': 'breakout'
                    }
                )
                
                self._record_entry(code, signal, True)
                return signal
        
        # 向下突破
        if current_low < support:
            breakout_pct = (support - current_low) / support
            
            if breakout_pct >= self.min_breakout_pct and volume_ok:
                qty = self._calculate_position_size(current_price)
                stop_loss = current_price * (1 + self.stop_loss_pct)
                take_profit = current_price * (1 - self.take_profit_pct)
                
                signal = TradeSignal(
                    code=code,
                    signal=SignalType.SELL,
                    price=current_price,
                    qty=qty,
                    reason=f"向下突破 | 突破幅度: {breakout_pct*100:.2f}% | 成交量確認: {volume_ok}",
                    metadata={
                        'support': support,
                        'breakout_pct': breakout_pct,
                        'volume_confirmed': volume_ok,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'strategy': 'breakout'
                    }
                )
                
                self._record_entry(code, signal, False)
                return signal
        
        return None
    
    def _calculate_levels(self, df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
        """計算支撐阻力位"""
        if len(df) < self.lookback_period:
            return None, None
        
        # 使用近期高低點作為支撐阻力
        recent_highs = df['high'].iloc[-self.lookback_period:]
        recent_lows = df['low'].iloc[-self.lookback_period:]
        
        resistance = recent_highs.max()
        support = recent_lows.min()
        
        return resistance, support
    
    def _check_volume(self, df: pd.DataFrame) -> bool:
        """檢查成交量是否放大"""
        if 'volume' not in df.columns or len(df) < self.lookback_period:
            return True  # 沒有成交量數據時默認通過
        
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].iloc[-self.lookback_period:-1].mean()
        
        if avg_volume == 0:
            return True
        
        volume_ratio = current_volume / avg_volume
        
        return volume_ratio >= self.volume_threshold
    
    def _check_exit(self, code: str, df: pd.DataFrame) -> Optional[TradeSignal]:
        """檢查出場條件"""
        if code not in self.positions:
            return None
        
        position = self.positions[code]
        current_price = df['close'].iloc[-1]
        entry_price = position['entry_price']
        is_long = position['is_long']
        
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
        
        # 反向突破出場
        elif is_long and code in self.recent_lows:
            if current_price < self.recent_lows[code]:
                exit_reason = f"反向突破支撐位 | {self.recent_lows[code]:.2f}"
        
        elif not is_long and code in self.recent_highs:
            if current_price > self.recent_highs[code]:
                exit_reason = f"反向突破阻力位 | {self.recent_highs[code]:.2f}"
        
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
            'entry_time': pd.Timestamp.now()
        }
    
    def on_order_update(self, order: Dict[str, Any]):
        """處理訂單更新"""
        pass
    
    def on_position_update(self, position: Dict[str, Any]):
        """處理持倉更新"""
        pass
