"""
FutuTradingBot - 靈活套利策略 (Flexible Arbitrage Strategy)
版本: 3.0.0
核心概念: 根據市場狀態動態調整交易方向，持續套利
"""

from dataclasses import dataclass
from typing import Optional, Literal
import pandas as pd
import numpy as np

@dataclass
class MarketState:
    """市場狀態定義"""
    state: Literal["bull", "bear", "choppy"]  # 牛市、熊市、震盪
    primary_direction: Literal["long", "short", "both"]  # 主導方向
    zscore_threshold: float  # 動態Z-Score閾值
    position_pct: float  # 倉位比例
    
    def __str__(self):
        return f"{self.state.upper()} | {self.primary_direction} | Z:{self.zscore_threshold} | Pos:{self.position_pct}"


class FlexibleArbitrageStrategy:
    """
    靈活套利策略
    
    核心邏輯:
    1. 每日判斷市場狀態（200日均線 + VIX）
    2. 根據市場狀態動態調整:
       - 牛市: 主要做多，Z-Score閾值放寬至1.2
       - 熊市: 主要做空，Z-Score閾值放寬至1.2
       - 震盪: 雙向交易，Z-Score閾值維持1.5
    3. 持續交易，不論牛熊都有機會
    """
    
    def __init__(self):
        self.name = "Flexible Arbitrage Strategy"
        self.version = "3.0.0"
        
        # 基礎參數
        self.take_profit_pct = 0.05  # 5%止盈
        self.stop_loss_pct = 0.03    # 3%止損
        self.time_stop_days = 5      # 5天時間止損（延長）
        self.exit_zscore = 0.3       # 出場Z-Score（更靈敏）
        
        # 市場狀態判斷參數
        self.ma_period = 200         # 200日均線
        self.vix_bull_threshold = 20  # VIX牛市閾值
        self.vix_bear_threshold = 25  # VIX熊市閾值
        
    def determine_market_state(self, price: float, ma200: float, vix: float) -> MarketState:
        """
        判斷市場狀態
        
        Args:
            price: 當前價格
            ma200: 200日均線
            vix: VIX指數
            
        Returns:
            MarketState: 市場狀態對象
        """
        # 牛市條件: 價格在200日均線之上 + VIX低
        if price > ma200 and vix < self.vix_bull_threshold:
            return MarketState(
                state="bull",
                primary_direction="long",
                zscore_threshold=1.2,  # 放寬閾值
                position_pct=0.70      # 70%倉位
            )
        
        # 熊市條件: 價格在200日均線之下 + VIX高
        elif price < ma200 and vix > self.vix_bear_threshold:
            return MarketState(
                state="bear",
                primary_direction="short",
                zscore_threshold=1.2,  # 放寬閾值
                position_pct=0.70      # 70%倉位
            )
        
        # 震盪市: 其他情況
        else:
            return MarketState(
                state="choppy",
                primary_direction="both",
                zscore_threshold=1.5,  # 維持較嚴格
                position_pct=0.50      # 50%倉位（雙向）
            )
    
    def should_enter_long(self, zscore: float, market_state: MarketState) -> bool:
        """
        判斷是否應該做多進場
        
        Args:
            zscore: 當前Z-Score
            market_state: 市場狀態
            
        Returns:
            bool: 是否進場
        """
        # 牛市或震盪市可以做多
        if market_state.primary_direction in ["long", "both"]:
            return zscore < -market_state.zscore_threshold
        return False
    
    def should_enter_short(self, zscore: float, market_state: MarketState) -> bool:
        """
        判斷是否應該做空進場
        
        Args:
            zscore: 當前Z-Score
            market_state: 市場狀態
            
        Returns:
            bool: 是否進場
        """
        # 熊市或震盪市可以做空
        if market_state.primary_direction in ["short", "both"]:
            return zscore > market_state.zscore_threshold
        return False
    
    def should_exit(self, zscore: float, entry_zscore: float, 
                   days_held: int, pnl_pct: float) -> tuple[bool, str]:
        """
        判斷是否應該出場
        
        Args:
            zscore: 當前Z-Score
            entry_zscore: 進場時Z-Score
            days_held: 持倉天數
            pnl_pct: 當前盈虧百分比
            
        Returns:
            tuple: (是否出場, 出場原因)
        """
        # 止盈
        if pnl_pct >= self.take_profit_pct:
            return True, f"止盈({pnl_pct:.2%})"
        
        # 止損
        if pnl_pct <= -self.stop_loss_pct:
            return True, f"止損({pnl_pct:.2%})"
        
        # 時間止損
        if days_held >= self.time_stop_days:
            return True, f"時間止損({days_held}天)"
        
        # Z-Score回歸（更靈敏）
        if abs(zscore) < self.exit_zscore:
            return True, f"Z-Score回歸({zscore:.2f})"
        
        return False, ""
    
    def get_strategy_config(self) -> dict:
        """獲取策略配置"""
        return {
            "name": self.name,
            "version": self.version,
            "take_profit_pct": self.take_profit_pct,
            "stop_loss_pct": self.stop_loss_pct,
            "time_stop_days": self.time_stop_days,
            "exit_zscore": self.exit_zscore,
            "ma_period": self.ma_period,
            "vix_bull_threshold": self.vix_bull_threshold,
            "vix_bear_threshold": self.vix_bear_threshold,
            "market_state_rules": {
                "bull": {"zscore": 1.2, "direction": "long", "position": 0.70},
                "bear": {"zscore": 1.2, "direction": "short", "position": 0.70},
                "choppy": {"zscore": 1.5, "direction": "both", "position": 0.50}
            }
        }


# 策略實例
strategy = FlexibleArbitrageStrategy()
