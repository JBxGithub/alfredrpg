import logging
import uuid
import random
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.fusion import (
    UnifiedSignal, RiskScoreFusion, AllocationRecommendation,
    SignalType, SignalSource, AllocationStrategy, MarketSentiment,
    DeFiFlow, MacroRisk
)
from app.services.worldmonitor_client import WorldMonitorClient, get_worldmonitor_client

logger = logging.getLogger(__name__)


class FusionEngine:
    WEIGHT_TRADITIONAL = 0.40
    WEIGHT_DEFI = 0.35
    WEIGHT_MACRO = 0.25

    def __init__(self):
        self.world_client: Optional[WorldMonitorClient] = None

    def _get_world_client(self) -> WorldMonitorClient:
        if self.world_client is None:
            self.world_client = get_worldmonitor_client()
        return self.world_client

    def _generate_traditional_market_sentiment(self) -> MarketSentiment:
        sentiment_score = random.uniform(40, 70)
        vix_level = random.uniform(10, 30)
        fear_greed_index = random.uniform(30, 70)

        if sentiment_score > 60:
            momentum = "bullish"
        elif sentiment_score < 45:
            momentum = "bearish"
        else:
            momentum = "neutral"

        return MarketSentiment(
            sentiment_score=sentiment_score,
            vix_level=vix_level,
            fear_greed_index=fear_greed_index,
            market_momentum=momentum,
            traditional_weight=self.WEIGHT_TRADITIONAL
        )

    def _generate_defi_flow(self) -> DeFiFlow:
        tvl_change = random.uniform(-5, 10)
        net_flow = random.uniform(-100e6, 500e6)

        top_gainers = random.sample(
            ["Aave", "Compound", "Maker", "Curve", "Uniswap", "Lido", "Rocket Pool"],
            k=random.randint(2, 4)
        )
        top_losers = random.sample(
            ["LUNA-Classic", "Avalanche", "Solana", "Polygon", "Fantom"],
            k=random.randint(1, 3)
        )

        return DeFiFlow(
            tvl_change_24h=tvl_change,
            net_flow=net_flow,
            top_gainers=top_gainers,
            top_losers=top_losers,
            defi_weight=self.WEIGHT_DEFI
        )

    async def _generate_macro_risk(self) -> MacroRisk:
        client = self._get_world_client()

        conflicts = await client.get_conflicts(
            start_date=datetime.now() - timedelta(days=30),
            limit=100
        )
        disasters = await client.get_disasters(
            start_time=datetime.now() - timedelta(days=7),
            limit=100
        )

        risk_score_obj = client.calculate_risk_score(conflicts, disasters)

        affected_regions = list(set(
            c.location.country for c in conflicts if c.location.country
        ))[:5]
        affected_regions.extend(
            d.location.country for d in disasters if d.location.country
        )
        affected_regions = list(set(affected_regions))[:5]

        return MacroRisk(
            conflict_count=len(conflicts),
            disaster_count=len(disasters),
            risk_score=risk_score_obj.overall_score,
            affected_regions=affected_regions,
            macro_weight=self.WEIGHT_MACRO
        )

    def _calculate_fusion_risk_score(
        self,
        sentiment: MarketSentiment,
        defi_flow: DeFiFlow,
        macro_risk: MacroRisk
    ) -> RiskScoreFusion:
        traditional_normalized = (sentiment.sentiment_score - 50) / 50 * 100
        traditional_score = max(0, min(100, 50 + traditional_normalized))

        defi_score = 50 + (defi_flow.tvl_change_24h * 3) + (defi_flow.net_flow / 50e6)
        defi_score = max(0, min(100, defi_score))

        macro_score = 100 - macro_risk.risk_score
        macro_score = max(0, min(100, macro_score))

        overall = (
            traditional_score * self.WEIGHT_TRADITIONAL +
            defi_score * self.WEIGHT_DEFI +
            macro_score * self.WEIGHT_MACRO
        )

        if overall >= 75:
            risk_level = "low"
        elif overall >= 50:
            risk_level = "medium"
        elif overall >= 25:
            risk_level = "high"
        else:
            risk_level = "critical"

        return RiskScoreFusion(
            overall_score=round(overall, 2),
            traditional_market_score=round(traditional_score, 2),
            defi_flow_score=round(defi_score, 2),
            macro_risk_score=round(macro_score, 2),
            risk_level=risk_level,
            timestamp=datetime.now(),
            weights={
                "traditional": self.WEIGHT_TRADITIONAL,
                "defi": self.WEIGHT_DEFI,
                "macro": self.WEIGHT_MACRO
            }
        )

    def _generate_signals(
        self,
        sentiment: MarketSentiment,
        defi_flow: DeFiFlow,
        macro_risk: MacroRisk
    ) -> List[UnifiedSignal]:
        signals = []

        if sentiment.market_momentum == "bullish":
            signals.append(UnifiedSignal(
                signal_id=str(uuid.uuid4()),
                signal_type=SignalType.BULLISH,
                source=SignalSource.TRADITIONAL_MARKET,
                confidence=sentiment.sentiment_score / 100,
                title="Traditional Market Bullish Momentum",
                description=f"Market momentum is {sentiment.market_momentum} with VIX at {sentiment.vix_level:.1f}",
                weight=self.WEIGHT_TRADITIONAL,
                timestamp=datetime.now()
            ))
        elif sentiment.market_momentum == "bearish":
            signals.append(UnifiedSignal(
                signal_id=str(uuid.uuid4()),
                signal_type=SignalType.BEARISH,
                source=SignalSource.TRADITIONAL_MARKET,
                confidence=(100 - sentiment.sentiment_score) / 100,
                title="Traditional Market Risk Aversion",
                description=f"High VIX ({sentiment.vix_level:.1f}) indicates increased market volatility",
                weight=self.WEIGHT_TRADITIONAL,
                timestamp=datetime.now()
            ))

        if defi_flow.tvl_change_24h > 3:
            signals.append(UnifiedSignal(
                signal_id=str(uuid.uuid4()),
                signal_type=SignalType.OPPORTUNITY,
                source=SignalSource.DEFI_FLOW,
                confidence=min(1.0, defi_flow.tvl_change_24h / 20),
                title="DeFi TVL Inflow",
                description=f"DeFi TVL up {defi_flow.tvl_change_24h:.2f}% in 24h",
                weight=self.WEIGHT_DEFI,
                timestamp=datetime.now()
            ))
        elif defi_flow.tvl_change_24h < -2:
            signals.append(UnifiedSignal(
                signal_id=str(uuid.uuid4()),
                signal_type=SignalType.WARNING,
                source=SignalSource.DEFI_FLOW,
                confidence=min(1.0, abs(defi_flow.tvl_change_24h) / 10),
                title="DeFi TVL Outflow",
                description=f"DeFi TVL down {abs(defi_flow.tvl_change_24h):.2f}% in 24h",
                weight=self.WEIGHT_DEFI,
                timestamp=datetime.now()
            ))

        if macro_risk.risk_score > 50:
            signals.append(UnifiedSignal(
                signal_id=str(uuid.uuid4()),
                signal_type=SignalType.WARNING,
                source=SignalSource.MACRO_RISK,
                confidence=macro_risk.risk_score / 100,
                title="Elevated Global Risk",
                description=f"{macro_risk.conflict_count} conflicts, {macro_risk.disaster_count} disasters",
                weight=self.WEIGHT_MACRO,
                timestamp=datetime.now()
            ))

        return signals

    def _generate_allocation(
        self,
        risk_score: RiskScoreFusion,
        signals: List[UnifiedSignal]
    ) -> AllocationRecommendation:
        overall = risk_score.overall_score

        bullish_signals = sum(1 for s in signals if s.signal_type in [SignalType.BULLISH, SignalType.OPPORTUNITY])
        bearish_signals = sum(1 for s in signals if s.signal_type in [SignalType.BEARISH, SignalType.WARNING])

        if overall >= 70 and bullish_signals > bearish_signals:
            strategy = AllocationStrategy.AGGRESSIVE
            crypto = 70
            stablecoin = 10
            defi = 20
            reasoning = "Strong risk appetite with bullish signals"
        elif overall >= 50:
            strategy = AllocationStrategy.BALANCED
            crypto = 50
            stablecoin = 25
            defi = 25
            reasoning = "Balanced exposure across markets"
        elif overall >= 30:
            strategy = AllocationStrategy.CONSERVATIVE
            crypto = 30
            stablecoin = 40
            defi = 30
            reasoning = "Defensive posture with elevated risk"
        else:
            strategy = AllocationStrategy.DEFENSIVE
            crypto = 15
            stablecoin = 55
            defi = 30
            reasoning = "Maximum protection amid critical risk conditions"

        risk_adjusted_return = (overall / 100) * 0.15 * (crypto / 100)

        return AllocationRecommendation(
            strategy=strategy,
            crypto_allocation=crypto,
            stablecoin_allocation=stablecoin,
            defi_allocation=defi,
            risk_adjusted_return=round(risk_adjusted_return, 4),
            reasoning=reasoning,
            timestamp=datetime.now()
        )

    async def generate_fusion_data(self):
        sentiment = self._generate_traditional_market_sentiment()
        defi_flow = self._generate_defi_flow()
        macro_risk = await self._generate_macro_risk()

        risk_score = self._calculate_fusion_risk_score(sentiment, defi_flow, macro_risk)
        signals = self._generate_signals(sentiment, defi_flow, macro_risk)
        allocation = self._generate_allocation(risk_score, signals)

        return {
            "signals": signals,
            "risk_score": risk_score,
            "allocation": allocation,
            "timestamp": datetime.now()
        }


_fusion_engine: Optional[FusionEngine] = None


def get_fusion_engine() -> FusionEngine:
    global _fusion_engine
    if _fusion_engine is None:
        _fusion_engine = FusionEngine()
    return _fusion_engine