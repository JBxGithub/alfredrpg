"""
FutuTradingBot - 靈活套利策略 (Flexible Arbitrage Strategy)
版本: 3.0.1 - 已整合BaseStrategy
核心概念: 根據市場狀態動態調整交易方向，持續套利
"""

from dataclasses import dataclass
from typing import Optional, Literal, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np

from src.strategies.base import BaseStrategy, TradeSignal, SignalType
from src.analysis.mtf_analyzer import MTFAnalyzer
from src.utils.logger import logger


@dataclass
class MarketState:
    """市場狀態定義"""
    state: Literal["bull", "bear", "choppy"]  # 牛市、熊市、震盪
    primary_direction: Literal["long", "short", "both"]  # 主導方向
    zscore_threshold: float  # 動態Z-Score閾值
    position_pct: float  # 倉位比例
    
    def __str__(self):
        return f"{self.state.upper()} | {self.primary_direction} | Z:{self.zscore_threshold} | Pos:{self.position_pct}"


class FlexibleArbitrageStrategy(BaseStrategy):
    """
    靈活套利策略
    
    核心邏輯:
    1. 每日判斷市場狀態（200日均線 + VIX）
    2. 根據市場狀態動態調整:
       - 牛市: 主要做多，Z-Score閾值放寬至1.2
       - 熊市: 主要做空，Z-Score閾值放寬至1.2
       - 震盪: 雙向交易，Z-Score閾值維持1.5
    3. 持續交易，不論牛熊都有機會
    
    已整合:
    - BaseStrategy
    - MTF分析器
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'take_profit_pct': 0.05,
            'stop_loss_pct': 0.03,
            'time_stop_days': 5,
            'exit_zscore': 0.3,
            'ma_period': 200,
            'vix_bull_threshold': 20,
            'vix_bear_threshold': 25,
            'use_mtf': True,
            'mtf_min_score': 60.0
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name="FlexibleArbitrage", config=default_config)
        
        # 基礎參數
        self.take_profit_pct = default_config['take_profit_pct']
        self.stop_loss_pct = default_config['stop_loss_pct']
        self.time_stop_days = default_config['time_stop_days']
        self.exit_zscore = default_config['exit_zscore']
        
        # 市場狀態判斷參數
        self.ma_period = default_config['ma_period']
        self.vix_bull_threshold = default_config['vix_bull_threshold']
        self.vix_bear_threshold = default_config['vix_bear_threshold']
        
        # MTF整合
        self.use_mtf = default_config.get('use_mtf', True)
        self.mtf_min_score = default_config.get('mtf_min_score', 60.0)
        if self.use_mtf:
            self.mtf_analyzer = MTFAnalyzer()
            logger.info("靈活套利策略: MTF分析已啟用")
        
        logger.info(f"靈活套利策略初始化完成")
        
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
    
    def on_data(self, data: Dict[str, Any]) -> Optional[TradeSignal]:
        """
        處理行情數據（BaseStrategy要求）
        
        Args:
            data: 行情數據字典
            
        Returns:
            TradeSignal or None
        """
        df = data.get('df')
        if df is None or len(df) < self.ma_period:
            return None
        
        # 獲取最新數據
        current_price = df['close'].iloc[-1]
        ma200 = df['close'].rolling(window=self.ma_period).mean().iloc[-1]
        
        # 計算Z-Score
        price_ma = df['close'].rolling(window=20).mean().iloc[-1]
        price_std = df['close'].rolling(window=20).std().iloc[-1]
        zscore = (current_price - price_ma) / price_std if price_std > 0 else 0
        
        # 獲取VIX（如有）
        vix = data.get('vix', 20)  # 默認20
        
        # 判斷市場狀態
        market_state = self.determine_market_state(current_price, ma200, vix)
        
        # 檢查進場條件
        if self.should_enter_long(zscore, market_state):
            return TradeSignal(
                signal=SignalType.BUY,
                symbol=data.get('symbol', 'TQQQ'),
                price=current_price,
                qty=100,  # 默認數量
                confidence=min(abs(zscore) / 3, 0.95),
                reason=f"靈活套利做多 | 市場:{market_state.state} | Z:{zscore:.2f}",
                metadata={
                    'zscore': zscore,
                    'market_state': market_state.state,
                    'strategy': 'FlexibleArbitrage'
                }
            )
        
        if self.should_enter_short(zscore, market_state):
            return TradeSignal(
                signal=SignalType.SELL,
                symbol=data.get('symbol', 'TQQQ'),
                price=current_price,
                qty=100,
                confidence=min(abs(zscore) / 3, 0.95),
                reason=f"靈活套利做空 | 市場:{market_state.state} | Z:{zscore:.2f}",
                metadata={
                    'zscore': zscore,
                    'market_state': market_state.state,
                    'strategy': 'FlexibleArbitrage'
                }
            )
        
        return None
    
    def on_order_update(self, order_update: Dict[str, Any]):
        """處理訂單更新（BaseStrategy要求）"""
        logger.debug(f"訂單更新: {order_update}")
    
    def on_position_update(self, position_update: Dict[str, Any]):
        """處理持倉更新（BaseStrategy要求）"""
        logger.debug(f"持倉更新: {position_update}")
    
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
