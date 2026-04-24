"""
Entry Signal Generator Module - 入場信號生成器模組

止損計算邏輯:
- 做多止損 = 入場價 × (1 - 止損百分比)
- 做空止損 = 入場價 × (1 + 止損百分比)
- ATR倍數止損 = 入場價 ± (ATR × ATR倍數)
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import pandas as pd
import numpy as np


class TradeDirection(Enum):
    """交易方向"""
    LONG = 1     # 做多
    SHORT = -1   # 做空
    NONE = 0     # 無交易


class StopLossType(Enum):
    """止損類型"""
    PERCENTAGE = "percentage"      # 百分比止損
    ATR = "atr"                    # ATR倍數止損
    SUPPORT_RESISTANCE = "sr"      # 支撐阻力位止損
    FIXED = "fixed"                # 固定金額止損


@dataclass  
class EntrySignal:
    """入場信號"""
    direction: TradeDirection           # 交易方向
    entry_price: float                  # 入場價格
    stop_loss_price: float              # 止損價格
    take_profit_price: float            # 止盈價格
    position_size: float                # 倉位大小
    position_value: float               # 倉位價值
    risk_amount: float                  # 風險金額
    risk_percentage: float              # 風險百分比
    stop_loss_distance: float           # 止損距離
    stop_loss_percentage: float         # 止損百分比
    take_profit_distance: float         # 止盈距離
    take_profit_percentage: float       # 止盈百分比
    risk_reward_ratio: float            # 風險報酬比
    stop_loss_type: StopLossType        # 止損類型
    atr_value: float                    # ATR值
    confidence_score: float             # 信心分數
    mtf_score: float                    # MTF評分
    entry_reason: str                   # 入場理由
    exit_reason: str                    # 出場理由
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PositionSizingConfig:
    """倉位配置"""
    account_balance: float              # 賬戶總資金
    risk_per_trade: float               # 單筆風險百分比
    max_position_size: float            # 最大倉位限制
    min_position_size: float            # 最小倉位
    leverage: float                     # 槓桿倍數


class EntryGenerator:
    """
    入場信號生成器
    
    止損計算邏輯:
    1. 百分比止損: 入場價 × (1 ± 止損百分比)
    2. ATR止損: 入場價 ± (ATR × ATR倍數)
    """
    
    DEFAULT_STOP_LOSS_PCT = 0.03       # 默認3%止損
    DEFAULT_TAKE_PROFIT_PCT = 0.05     # 默認5%止盈
    DEFAULT_ATR_MULTIPLIER = 2.0       # 默認2倍ATR止損
    DEFAULT_RISK_PER_TRADE = 0.02      # 默認2%風險
    DEFAULT_RISK_REWARD_RATIO = 1.5    # 默認1.5:1風險報酬比
    
    def __init__(self, 
                 stop_loss_pct: float = DEFAULT_STOP_LOSS_PCT,
                 take_profit_pct: float = DEFAULT_TAKE_PROFIT_PCT,
                 atr_multiplier: float = DEFAULT_ATR_MULTIPLIER,
                 risk_per_trade: float = DEFAULT_RISK_PER_TRADE,
                 risk_reward_ratio: float = DEFAULT_RISK_REWARD_RATIO):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.atr_multiplier = atr_multiplier
        self.risk_per_trade = risk_per_trade
        self.risk_reward_ratio = risk_reward_ratio
    
    def _calculate_stop_loss(self, entry_price: float, direction: TradeDirection,
                            stop_loss_type: StopLossType, atr: float,
                            daily_data: pd.DataFrame) -> float:
        """
        計算止損價格
        
        止損計算邏輯:
        - 做多止損 = 入場價 × (1 - 止損百分比)
        - 做空止損 = 入場價 × (1 + 止損百分比)
        - ATR止損 = 入場價 ± (ATR × ATR倍數)
        """
        if stop_loss_type == StopLossType.PERCENTAGE:
            # 百分比止損
            if direction == TradeDirection.LONG:
                # 做多: 止損價 = 入場價 × (1 - 止損百分比)
                stop_loss = entry_price * (1 - self.stop_loss_pct)
            else:
                # 做空: 止損價 = 入場價 × (1 + 止損百分比)
                stop_loss = entry_price * (1 + self.stop_loss_pct)
        
        elif stop_loss_type == StopLossType.ATR:
            # ATR倍數止損
            if direction == TradeDirection.LONG:
                # 做多: 止損價 = 入場價 - (ATR × ATR倍數)
                stop_loss = entry_price - (atr * self.atr_multiplier)
            else:
                # 做空: 止損價 = 入場價 + (ATR × ATR倍數)
                stop_loss = entry_price + (atr * self.atr_multiplier)
        
        else:
            # 默認使用百分比止損
            if direction == TradeDirection.LONG:
                stop_loss = entry_price * (1 - self.stop_loss_pct)
            else:
                stop_loss = entry_price * (1 + self.stop_loss_pct)
        
        # 確保止損價格有效
        if direction == TradeDirection.LONG:
            # 做多時止損價必須低於入場價
            if stop_loss >= entry_price:
                stop_loss = entry_price * (1 - self.stop_loss_pct)
        else:
            # 做空時止損價必須高於入場價
            if stop_loss <= entry_price:
                stop_loss = entry_price * (1 + self.stop_loss_pct)
        
        return stop_loss
    
    def _calculate_take_profit(self, entry_price: float, direction: TradeDirection,
                               stop_loss: float) -> float:
        """計算止盈價格"""
        stop_distance = abs(entry_price - stop_loss)
        profit_distance = stop_distance * self.risk_reward_ratio
        
        if direction == TradeDirection.LONG:
            take_profit = entry_price + profit_distance
        else:
            take_profit = entry_price - profit_distance
        
        return take_profit
    
    def _calculate_position_size(self, entry_price: float, stop_loss: float,
                                 config: PositionSizingConfig) -> Tuple[float, float, float]:
        """
        計算倉位大小
        
        公式:
        風險金額 = 賬戶總資金 × 單筆風險百分比
        止損距離 = |入場價 - 止損價|
        倉位大小 = 風險金額 / 止損距離
        """
        risk_amount = config.account_balance * config.risk_per_trade
        stop_distance = abs(entry_price - stop_loss)
        
        if stop_distance == 0:
            return 0, 0, 0
        
        position_size = risk_amount / stop_distance
        position_value = position_size * entry_price
        
        # 應用最大倉位限制
        max_position_value = config.account_balance * config.max_position_size
        if position_value > max_position_value:
            position_value = max_position_value
            position_size = position_value / entry_price
            risk_amount = position_size * stop_distance
        
        # 應用最小倉位限制
        if position_size < config.min_position_size:
            position_size = config.min_position_size
            position_value = position_size * entry_price
            risk_amount = position_size * stop_distance
        
        return position_size, position_value, risk_amount
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """計算ATR"""
        if df is None or len(df) < period:
            return 0.0
        
        df = df.copy()
        df['prev_close'] = df['close'].shift(1)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['prev_close'])
        df['tr3'] = abs(df['low'] - df['prev_close'])
        df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        atr = df['tr'].rolling(window=period).mean().iloc[-1]
        return float(atr) if not pd.isna(atr) else 0.0


# ============ 單元測試 ============

if __name__ == "__main__":
    print("Entry Generator 單元測試")
    print("=" * 60)
    
    generator = EntryGenerator(stop_loss_pct=0.03, risk_reward_ratio=1.5)
    
    # 測試1: 做多止損計算
    print("\n測試1: 做多止損計算 (百分比止損)")
    entry_price = 100.0
    stop_loss = generator._calculate_stop_loss(
        entry_price, TradeDirection.LONG, StopLossType.PERCENTAGE, 2.0, None
    )
    expected = entry_price * (1 - 0.03)  # 97.0
    print(f"  入場價格: {entry_price}")
    print(f"  止損價格: {stop_loss:.2f}")
    print(f"  預期價格: {expected:.2f}")
    print(f"  止損百分比: {(entry_price - stop_loss) / entry_price * 100:.2f}%")
    assert stop_loss < entry_price, "做多止損必須低於入場價!"
    assert abs(stop_loss - expected) < 0.01, "止損計算錯誤!"
    print("  ✓ 測試通過")
    
    # 測試2: 做空止損計算
    print("\n測試2: 做空止損計算 (百分比止損)")
    stop_loss = generator._calculate_stop_loss(
        entry_price, TradeDirection.SHORT, StopLossType.PERCENTAGE, 2.0, None
    )
    expected = entry_price * (1 + 0.03)  # 103.0
    print(f"  入場價格: {entry_price}")
    print(f"  止損價格: {stop_loss:.2f}")
    print(f"  預期價格: {expected:.2f}")
    print(f"  止損百分比: {(stop_loss - entry_price) / entry_price * 100:.2f}%")
    assert stop_loss > entry_price, "做空止損必須高於入場價!"
    assert abs(stop_loss - expected) < 0.01, "止損計算錯誤!"
    print("  ✓ 測試通過")
    
    # 測試3: ATR止損計算
    print("\n測試3: ATR倍數止損計算")
    atr_value = 2.5
    stop_loss_long = generator._calculate_stop_loss(
        entry_price, TradeDirection.LONG, StopLossType.ATR, atr_value, None
    )
    stop_loss_short = generator._calculate_stop_loss(
        entry_price, TradeDirection.SHORT, StopLossType.ATR, atr_value, None
    )
    expected_long = entry_price - (atr_value * 2.0)  # 95.0
    expected_short = entry_price + (atr_value * 2.0)  # 105.0
    print(f"  入場價格: {entry_price}")
    print(f"  ATR值: {atr_value}")
    print(f"  ATR倍數: 2.0")
    print(f"  做多止損: {stop_loss_long:.2f} (預期: {expected_long:.2f})")
    print(f"  做空止損: {stop_loss_short:.2f} (預期: {expected_short:.2f})")
    assert stop_loss_long < entry_price, "做多ATR止損必須低於入場價!"
    assert stop_loss_short > entry_price, "做空ATR止損必須高於入場價!"
    assert abs(stop_loss_long - expected_long) < 0.01, "做多ATR止損計算錯誤!"
    assert abs(stop_loss_short - expected_short) < 0.01, "做空ATR止損計算錯誤!"
    print("  ✓ 測試通過")
    
    # 測試4: 止盈計算
    print("\n測試4: 止盈價格計算")
    stop_loss = 97.0  # 做多止損
    take_profit = generator._calculate_take_profit(entry_price, TradeDirection.LONG, stop_loss)
    stop_distance = entry_price - stop_loss  # 3.0
    expected_profit = entry_price + (stop_distance * 1.5)  # 104.5
    print(f"  入場價格: {entry_price}")
    print(f"  止損價格: {stop_loss}")
    print(f"  止損距離: {stop_distance}")
    print(f"  風險報酬比: 1.5")
    print(f"  止盈價格: {take_profit:.2f} (預期: {expected_profit:.2f})")
    assert take_profit > entry_price, "做多止盈必須高於入場價!"
    assert abs(take_profit - expected_profit) < 0.01, "止盈計算錯誤!"
    print("  ✓ 測試通過")
    
    # 測試5: 倉位計算
    print("\n測試5: 倉位大小計算")
    config = PositionSizingConfig(
        account_balance=100000.0,
        risk_per_trade=0.02,  # 2%
        max_position_size=0.5,  # 50%
        min_position_size=100,
        leverage=1.0
    )
    entry = 100.0
    stop = 97.0  # 3% 止損
    position_size, position_value, risk_amount = generator._calculate_position_size(
        entry, stop, config
    )
    # 由於倉位價值 666.67 * 100 = 66667 > 最大倉位 50000，所以會被限制
    max_position_value = config.account_balance * config.max_position_size  # 50000
    expected_size_limited = max_position_value / entry  # 500
    expected_risk_limited = expected_size_limited * (entry - stop)  # 500 * 3 = 1500
    print(f"  賬戶資金: {config.account_balance}")
    print(f"  風險金額: {risk_amount:.2f} (限制後預期: {expected_risk_limited:.2f})")
    print(f"  倉位大小: {position_size:.2f} (限制後預期: {expected_size_limited:.2f})")
    print(f"  倉位價值: {position_value:.2f}")
    assert abs(risk_amount - expected_risk_limited) < 0.01, "風險金額計算錯誤!"
    assert abs(position_size - expected_size_limited) < 0.01, "倉位大小計算錯誤!"
    print("  ✓ 測試通過 (已應用最大倉位限制)")
    
    # 測試6: 止損邏輯邊界測試
    print("\n測試6: 止損邏輯邊界測試 (確保做多止損 < 入場價)")
    test_cases = [
        (100.0, TradeDirection.LONG, 0.03, 97.0),
        (50.0, TradeDirection.LONG, 0.05, 47.5),
        (200.0, TradeDirection.SHORT, 0.03, 206.0),
        (75.0, TradeDirection.SHORT, 0.05, 78.75),
    ]
    for entry, direction, stop_pct, expected in test_cases:
        gen = EntryGenerator(stop_loss_pct=stop_pct)
        stop = gen._calculate_stop_loss(entry, direction, StopLossType.PERCENTAGE, 0, None)
        print(f"  入場:{entry}, 方向:{direction.name}, 止損:{stop:.2f}, 預期:{expected:.2f}")
        assert abs(stop - expected) < 0.01, f"止損計算錯誤: {stop} != {expected}"
        if direction == TradeDirection.LONG:
            assert stop < entry, "做多止損必須低於入場價!"
        else:
            assert stop > entry, "做空止損必須高於入場價!"
    print("  ✓ 測試通過")
    
    print("\n" + "=" * 60)
    print("所有測試通過! 止損計算邏輯正確。")
    print("\n止損計算公式驗證:")
    print("  做多止損 = 入場價 × (1 - 止損百分比) ✓")
    print("  做空止損 = 入場價 × (1 + 止損百分比) ✓")
    print("  ATR止損 = 入場價 ± (ATR × ATR倍數) ✓")
