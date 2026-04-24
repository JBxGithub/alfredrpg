from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from enum import Enum

class StrategyType(str, Enum):
    TQQQ = "tqqq"
    TREND = "trend"
    ZSCORE = "zscore"
    BREAKOUT = "breakout"
    MOMENTUM = "momentum"
    FLEXIBLE_ARBITRAGE = "flexible_arbitrage"

class TQQQStrategy(BaseModel):
    zscore_threshold: float = Field(default=1.65, ge=0.5, le=3.0, description="Z-Score閾值")
    rsi_overbought: int = Field(default=70, ge=50, le=90, description="RSI超買閾值")
    rsi_oversold: int = Field(default=30, ge=10, le=50, description="RSI超賣閾值")
    take_profit_pct: float = Field(default=5.0, ge=1.0, le=20.0, description="止盈百分比")
    stop_loss_pct: float = Field(default=3.0, ge=0.5, le=10.0, description="止損百分比")
    time_stop_days: int = Field(default=7, ge=1, le=30, description="時間止損天數")
    position_pct: float = Field(default=50.0, ge=10.0, le=100.0, description="倉位百分比")

class TrendStrategy(BaseModel):
    ema_fast: int = Field(default=12, ge=5, le=50, description="EMA快線週期")
    ema_slow: int = Field(default=26, ge=20, le=100, description="EMA慢線週期")
    ema_signal: int = Field(default=9, ge=5, le=20, description="EMA信號週期")
    indicator_confluence: int = Field(default=2, ge=1, le=5, description="指標共振數量")
    volume_threshold: float = Field(default=1.5, ge=1.0, le=5.0, description="成交量閾值倍數")

class ZScoreStrategy(BaseModel):
    zscore_entry: float = Field(default=2.0, ge=0.5, le=4.0, description="Z-Score入場閾值")
    zscore_exit: float = Field(default=0.5, ge=0.1, le=2.0, description="Z-Score出場閾值")
    exit_condition: Literal["mean_reversion", "opposite_signal", "both"] = Field(
        default="mean_reversion", description="出場條件"
    )
    lookback_period: int = Field(default=20, ge=10, le=60, description="回望週期")

class BreakoutStrategy(BaseModel):
    breakout_threshold: float = Field(default=2.0, ge=0.5, le=5.0, description="突破閾值(%)")
    volume_confirm: bool = Field(default=True, description="成交量確認")
    volume_multiplier: float = Field(default=2.0, ge=1.0, le=5.0, description="成交量倍數")
    consolidation_period: int = Field(default=20, ge=5, le=60, description="盤整週期")

class MomentumStrategy(BaseModel):
    momentum_period: int = Field(default=14, ge=5, le=30, description="動量週期")
    rsi_period: int = Field(default=14, ge=5, le=30, description="RSI週期")
    rsi_threshold: int = Field(default=50, ge=30, le=70, description="RSI閾值")
    momentum_threshold: float = Field(default=0.0, ge=-10.0, le=10.0, description="動量閾值")

class FlexibleArbitrageStrategy(BaseModel):
    market_state_threshold: float = Field(default=0.5, ge=0.1, le=1.0, description="市場狀態閾值")
    zscore_dynamic: bool = Field(default=True, description="Z-Score動態調整")
    zscore_min: float = Field(default=1.5, ge=0.5, le=3.0, description="Z-Score最小值")
    zscore_max: float = Field(default=2.5, ge=1.5, le=4.0, description="Z-Score最大值")
    volatility_adjust: bool = Field(default=True, description="波動率調整")

class MTFSettings(BaseModel):
    enabled: bool = Field(default=True, description="MTF分析開關")
    macd_v_enabled: bool = Field(default=True, description="MACD-V開關")
    divergence_enabled: bool = Field(default=True, description="背離檢測開關")
    monthly_weight: int = Field(default=40, ge=0, le=100, description="月線權重")
    weekly_weight: int = Field(default=35, ge=0, le=100, description="週線權重")
    daily_weight: int = Field(default=25, ge=0, le=100, description="日線權重")
    min_score_threshold: int = Field(default=60, ge=0, le=100, description="最低評分閾值")

class RiskControl(BaseModel):
    max_risk_per_trade: float = Field(default=1.0, ge=0.1, le=5.0, description="單筆最大風險(%)")
    max_daily_loss: float = Field(default=2.0, ge=0.5, le=10.0, description="每日最大虧損(%)")
    max_positions: int = Field(default=3, ge=1, le=10, description="最大持倉數")
    partial_profit_enabled: bool = Field(default=True, description="部分獲利開關")
    dynamic_stoploss_enabled: bool = Field(default=True, description="動態止損開關")

class StrategyConfig(BaseModel):
    strategy_type: StrategyType = Field(default=StrategyType.TQQQ)
    tqqq: TQQQStrategy = Field(default_factory=TQQQStrategy)
    trend: TrendStrategy = Field(default_factory=TrendStrategy)
    zscore: ZScoreStrategy = Field(default_factory=ZScoreStrategy)
    breakout: BreakoutStrategy = Field(default_factory=BreakoutStrategy)
    momentum: MomentumStrategy = Field(default_factory=MomentumStrategy)
    flexible_arbitrage: FlexibleArbitrageStrategy = Field(default_factory=FlexibleArbitrageStrategy)
    mtf: MTFSettings = Field(default_factory=MTFSettings)
    risk: RiskControl = Field(default_factory=RiskControl)
    name: str = Field(default="Default Strategy", description="策略名稱")
    description: Optional[str] = Field(default=None, description="策略描述")

class ConfigResponse(BaseModel):
    success: bool
    message: str
    config: Optional[StrategyConfig] = None
    errors: Optional[List[str]] = None
