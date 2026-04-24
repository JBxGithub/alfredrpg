from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SignalSource(str, Enum):
    TRADITIONAL_MARKET = "traditional_market"
    DEFI_FLOW = "defi_flow"
    MACRO_RISK = "macro_risk"


class SignalType(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    WARNING = "warning"
    OPPORTUNITY = "opportunity"


class AllocationStrategy(str, Enum):
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    DEFENSIVE = "defensive"


class SignalBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MarketSentiment(SignalBaseModel):
    sentiment_score: float
    vix_level: float
    fear_greed_index: float
    market_momentum: str
    traditional_weight: float = 0.40


class DeFiFlow(SignalBaseModel):
    tvl_change_24h: float
    net_flow: float
    top_gainers: List[str] = []
    top_losers: List[str] = []
    defi_weight: float = 0.35


class MacroRisk(SignalBaseModel):
    conflict_count: int
    disaster_count: int
    risk_score: float
    affected_regions: List[str] = []
    macro_weight: float = 0.25


class UnifiedSignal(SignalBaseModel):
    signal_id: str
    signal_type: SignalType
    source: SignalSource
    confidence: float
    title: str
    description: str
    weight: float
    timestamp: datetime


class RiskScoreFusion(SignalBaseModel):
    overall_score: float
    traditional_market_score: float
    defi_flow_score: float
    macro_risk_score: float
    risk_level: str
    timestamp: datetime
    weights: dict


class AllocationRecommendation(SignalBaseModel):
    strategy: AllocationStrategy
    crypto_allocation: float
    stablecoin_allocation: float
    defi_allocation: float
    risk_adjusted_return: float
    reasoning: str
    timestamp: datetime


class FusionResponse(SignalBaseModel):
    signals: List[UnifiedSignal]
    risk_score: RiskScoreFusion
    allocation: AllocationRecommendation
    timestamp: datetime