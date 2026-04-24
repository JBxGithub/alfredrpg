from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ConflictType(str, Enum):
    VIOLENCE = "violence"
    PROTEST = "protest"
    RIOT = "riot"
    EXPLOSION = "explosion"


class DisasterType(str, Enum):
    EARTHQUAKE = "earthquake"
    TSUNAMI = "tsunami"
    VOLCANO = "volcano"
    FLOOD = "flood"
    TROPICAL_CYCLONE = "tropical_cyclone"
    DROUGHT = "drought"
    WILDFIRE = "wildfire"
    EXTREME_TEMPERATURE = "extreme_temperature"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorldBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Location(WorldBaseModel):
    lat: float
    lon: float
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    admin1: Optional[str] = None


class ConflictEvent(WorldBaseModel):
    event_id: str = Field(alias="data_id")
    event_date: datetime = Field(alias="event_date")
    event_type: ConflictType
    sub_event_type: Optional[str] = None
    location: Location
    actor1: Optional[str] = None
    actor2: Optional[str] = None
    interaction: Optional[int] = None
    fatalities: Optional[int] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    iso_code: Optional[str] = None


class NaturalDisaster(WorldBaseModel):
    disaster_id: str
    disaster_type: DisasterType
    event_time: datetime
    location: Location
    magnitude: Optional[float] = None
    depth: Optional[float] = None
    felt: Optional[int] = None
    cdi: Optional[float] = None
    mmi: Optional[float] = None
    alert_level: Optional[RiskLevel] = None
    tsunami: Optional[int] = None
    sig: Optional[int] = None
    net: Optional[str] = None
    nst: Optional[int] = None
    dmin: Optional[float] = None
    place: Optional[str] = None
    title: Optional[str] = None


class EconomicEvent(WorldBaseModel):
    event_id: str
    event_type: str
    event_date: datetime
    country: str
    country_code: str
    sector: Optional[str] = None
    impact: Optional[float] = None
    description: Optional[str] = None
    source: Optional[str] = None


class RiskIndicator(WorldBaseModel):
    indicator_name: str
    value: float
    unit: str
    timestamp: datetime
    country: Optional[str] = None
    region: Optional[str] = None
    category: Optional[str] = None


class RiskScore(WorldBaseModel):
    overall_score: float
    conflict_score: float
    disaster_score: float
    economic_score: float
    timestamp: datetime
    risk_level: RiskLevel
    affected_regions: List[str] = []


class MarketCorrelation(WorldBaseModel):
    event_id: str
    event_type: str
    region: str
    asset_class: str
    correlation: float
    impact_estimate: Optional[float] = None
    timeframe: str
    confidence: Optional[float] = None


class WorldMonitorResponse(WorldBaseModel):
    items: List
    total: int
    timestamp: datetime