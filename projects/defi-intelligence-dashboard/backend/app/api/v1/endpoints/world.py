from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timedelta
from app.services.worldmonitor_client import get_world_monitor_client, WorldMonitorClient
from app.models.worldmonitor import (
    ConflictEvent, NaturalDisaster, RiskScore, MarketCorrelation
)

router = APIRouter(prefix="/world", tags=["World Monitor"])


@router.get("/conflicts", response_model=List[ConflictEvent])
async def get_conflicts(
    country: Optional[str] = Query(None, description="Country ISO code or name"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500, description="Result limit"),
    client: WorldMonitorClient = Depends(get_world_monitor_client)
):
    try:
        start = None
        end = None
        if start_date:
            start = datetime.fromisoformat(start_date)
        if end_date:
            end = datetime.fromisoformat(end_date)

        events = await client.get_conflicts(
            country=country,
            start_date=start,
            end_date=end,
            limit=limit
        )
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conflicts: {str(e)}")


@router.get("/disasters", response_model=List[NaturalDisaster])
async def get_disasters(
    start_time: Optional[str] = Query(None, description="Start time (ISO format)"),
    end_time: Optional[str] = Query(None, description="End time (ISO format)"),
    min_magnitude: Optional[float] = Query(None, ge=0, description="Minimum magnitude"),
    limit: int = Query(100, ge=1, le=500, description="Result limit"),
    client: WorldMonitorClient = Depends(get_world_monitor_client)
):
    try:
        start = None
        end = None
        if start_time:
            start = datetime.fromisoformat(start_time)
        if end_time:
            end = datetime.fromisoformat(end_time)

        disasters = await client.get_disasters(
            start_time=start,
            end_time=end,
            min_magnitude=min_magnitude,
            limit=limit
        )
        return disasters
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch disasters: {str(e)}")


@router.get("/risk-score", response_model=RiskScore)
async def get_risk_score(
    country: Optional[str] = Query(None, description="Country filter"),
    client: WorldMonitorClient = Depends(get_world_monitor_client)
):
    try:
        conflicts = await client.get_conflicts(
            country=country,
            start_date=datetime.now() - timedelta(days=30),
            limit=100
        )
        disasters = await client.get_disasters(
            start_time=datetime.now() - timedelta(days=7),
            limit=100
        )

        risk_score = client.calculate_risk_score(conflicts, disasters)
        return risk_score
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate risk score: {str(e)}")


@router.get("/correlation", response_model=List[MarketCorrelation])
async def get_market_correlation(
    region: Optional[str] = Query(None, description="Region filter"),
    timeframe: str = Query("7d", description="Timeframe: 7d, 30d, 90d"),
    client: WorldMonitorClient = Depends(get_world_monitor_client)
):
    try:
        days = int(timeframe.replace("d", ""))
        conflicts = await client.get_conflicts(
            country=region,
            start_date=datetime.now() - timedelta(days=days),
            limit=50
        )
        disasters = await client.get_disasters(
            start_time=datetime.now() - timedelta(days=days),
            limit=50
        )

        correlations = []
        for c in conflicts[:20]:
            correlations.append(MarketCorrelation(
                event_id=c.event_id,
                event_type=c.event_type.value,
                region=c.location.country or "Unknown",
                asset_class="crypto",
                correlation=0.3,
                impact_estimate=float(c.fatalities or 0) / 100,
                timeframe=timeframe,
                confidence=0.7
            ))

        for d in disasters[:20]:
            correlations.append(MarketCorrelation(
                event_id=d.disaster_id,
                event_type=d.disaster_type.value,
                region=d.location.country or "Unknown",
                asset_class="crypto",
                correlation=0.5,
                impact_estimate=(d.magnitude or 0) / 10,
                timeframe=timeframe,
                confidence=0.8
            ))

        return correlations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch correlations: {str(e)}")