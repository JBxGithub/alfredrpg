"""
均值回歸策略 - Mean Reversion Strategy

基於價格偏離均值後回歸的統計特性進行交易
適用於震盪市場

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.strategies.base import BaseStrategy, TradeSignal, SignalType
from src.indicators.technical import TechnicalIndicators
from src.utils.logger import logger


@dataclass
class MeanReversionConfig:
    """均值回歸策略配置"""
    lookback_period: int = 20           # 回看週期
    entry_zscore: float = 2.0           # 進場Z分數閾值
    exit_zscore: float = 0.5            # 出場Z分數閾值
    stop_loss_pct: float = 0.05         # 止損比例
    take_profit_pct: float = 0.03       # 止盈比例
    position_pct: float = 0.02          # 倉位比例
    min_adx: float = 20.0               # 最小ADX值 (避免趨勢市場)


class MeanReversionStrategy(BaseStrategy):
    """
    均值回歸策略
    
    核心邏輯:
    1. 計算價格相對於移動平均線的Z分數
    2. 當Z分數超過閾值時，預期價格回歸均值
    3. 在超賣時買入，超買時賣出
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'lookback_period': 20,
            'entry_zscore': 2.0,
            'exit_zscore': 0.5,
            'stop_loss_pct': 0.05,
            'take_profit_pct': 0.03,
            'position_pct': 0.02,
            'min_adx': 20.0
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name="MeanReversion", config=default_config)
        
        self.lookback_period = self.config['lookback_period']
        self.entry_zscore = self.config['entry_zscore']
        self.exit_zscore = self.config['exit_zscore']
        self.stop_loss_pct = self.config['stop_loss_pct']
        self.take_profit_pct = self.config['take_profit_pct']
        self.position_pct = self.config['position_pct']
        self.min_adx = self.config['min_adx']
        
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"均值回歸策略初始化 | 回看週期: {self.lookback_period}, 進場Z分數: {self.entry_zscore}")
    
    def on_data(self, data: Dict[str, Any]) -> Optional[TradeSignal]:
        """處理行情數據"""
        code = data.get('code')
        df = data.get('df')
        
        if df is None or len(df) < self.lookback_period + 10:
            return None
        
        # 檢查現有持倉
        if code in self.positions:
            return self._check_exit(code, df)
        
        # 計算Z分數
        zscore = self._calculate_zscore(df)
        
        if zscore is None:
            return None
        
        # 檢查趨勢強度 (避免在強趨勢中交易)
        adx = self._calculate_adx(df)
        if adx > 30:  # 強趨勢市場，不交易
            return None
        
        current_price = df['close'].iloc[-1]
        
        # 超賣信號 (Z分數 < -閾值) -> 買入
        if zscore < -self.entry_zscore:
            qty = self._calculate_position_size(current_price)
            stop_loss = current_price * (1 - self.stop_loss_pct)
            take_profit = current_price * (1 + self.take_profit_pct)
            
            signal = TradeSignal(
                code=code,
                signal=SignalType.BUY,
                price=current_price,
                qty=qty,
                reason=f"均值回歸買入 | Z分數: {zscore:.2f} (超賣)",
                metadata={
                    'zscore': zscore,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strategy': 'mean_reversion'
                }
            )
            
            self._record_entry(code, signal, True)
            return signal
        
        # 超買信號 (Z分數 > 閾值) -> 賣出 (做空)
        if zscore > self.entry_zscore:
            qty = self._calculate_position_size(current_price)
            stop_loss = current_price * (1 + self.stop_loss_pct)
            take_profit = current_price * (1 - self.take_profit_pct)
            
            signal = TradeSignal(
                code=code,
                signal=SignalType.SELL,
                price=current_price,
                qty=qty,
                reason=f"均值回歸賣出 | Z分數: {zscore:.2f} (超買)",
                metadata={
                    'zscore': zscore,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strategy': 'mean_reversion'
                }
            )
            
            self._record_entry(code, signal, False)
            return signal
        
        return None
    
    def _calculate_zscore(self, df: pd.DataFrame) -> Optional[float]:
        """計算價格Z分數"""
        if len(df) < self.lookback_period:
            return None
        
        close = df['close']
        
        # 計算移動平均線和標準差
        ma = close.rolling(window=self.lookback_period).mean()
        std = close.rolling(window=self.lookback_period).std()
        
        current_price = close.iloc[-1]
        current_ma = ma.iloc[-1]
        current_std = std.iloc[-1]
        
        if current_std == 0 or pd.isna(current_std):
            return None
        
        zscore = (current_price - current_ma) / current_std
        
        return round(zscore, 2)
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> float:
        """計算ADX趨勢強度"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # +DM and -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        plus_dm[plus_dm <= minus_dm] = 0
        minus_dm[minus_dm <= plus_dm] = 0
        
        # Smooth TR, +DM, -DM
        atr = tr.ewm(span=period, adjust=False).mean()
        plus_di = 100 * plus_dm.ewm(span=period, adjust=False).mean() / atr
        minus_di = 100 * minus_dm.ewm(span=period, adjust=False).mean() / atr
        
        # DX and ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period, adjust=False).mean()
        
        return adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 0
    
    def _check_exit(self, code: str, df: pd.DataFrame) -> Optional[TradeSignal]:
        """檢查出場條件"""
        if code not in self.positions:
            return None
        
        position = self.positions[code]
        current_price = df['close'].iloc[-1]
        entry_price = position['entry_price']
        is_long = position['is_long']
        
        # 計算當前Z分數
        zscore = self._calculate_zscore(df)
        
        # 計算盈虧
        pnl_pct = (current_price - entry_price) / entry_price
        if not is_long:
            pnl_pct = -pnl_pct
        
        exit_reason = None
        
        # Z分數回歸出場
        if is_long and zscore and zscore >= -self.exit_zscore:
            exit_reason = f"Z分數回歸 | {zscore:.2f}"
        elif not is_long and zscore and zscore <= self.exit_zscore:
            exit_reason = f"Z分數回歸 | {zscore:.2f}"
        
        # 止損出場
        elif pnl_pct <= -self.stop_loss_pct:
            exit_reason = f"止損觸發 | 虧損: {pnl_pct*100:.2f}%"
        
        # 止盈出場
        elif pnl_pct >= self.take_profit_pct:
            exit_reason = f"止盈觸發 | 盈利: {pnl_pct*100:.2f}%"
        
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
                    'pnl_pct': pnl_pct,
                    'zscore': zscore
                }
            )
            
            del self.positions[code]
            return signal
        
        return None
    
    def _calculate_position_size(self, price: float) -> int:
        """計算倉位大小"""
        account_value = 1000000  # 假設賬戶價值
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
