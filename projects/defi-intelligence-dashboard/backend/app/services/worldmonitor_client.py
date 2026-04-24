import httpx
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.config import get_settings
from app.models.worldmonitor import (
    ConflictEvent, NaturalDisaster, RiskIndicator, RiskScore,
    MarketCorrelation, ConflictType, DisasterType, RiskLevel,
    Location
)

settings = get_settings()
logger = logging.getLogger(__name__)


class WorldMonitorAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class CacheManager:
    def __init__(self, ttl: int = 3600):
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.now() - timestamp).total_seconds() < self.ttl:
                return data
            del self._cache[key]
        return None

    def set(self, key: str, value: Any):
        self._cache[key] = (value, datetime.now())


cache_manager = CacheManager(ttl=settings.WORLD_DATA_CACHE_TTL)


class WorldMonitorClient:
    def __init__(self):
        self.acled_base = settings.ACLED_API_BASE
        self.usgs_base = settings.USGS_API_BASE
        self.timeout = settings.REQUEST_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self, url: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        client = await self._get_client()
        for attempt in range(settings.MAX_RETRIES):
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    await self.close()
                    raise WorldMonitorAPIError("Rate limited", 429)
                if attempt == settings.MAX_RETRIES - 1:
                    raise WorldMonitorAPIError(f"API error: {e}", e.response.status_code)
            except httpx.RequestError as e:
                if attempt == settings.MAX_RETRIES - 1:
                    raise WorldMonitorAPIError(f"Request failed: {e}")
        return None

    async def get_conflicts(
        self,
        country: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ConflictEvent]:
        cache_key = f"conflicts:{country}:{start_date}:{end_date}:{limit}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        params = {
            "key": "demo",
            "iso": country,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "limit": limit
        }

        try:
            data = await self._request(self.acled_base, params)
            events = self._parse_acled_conflicts(data, country)
            cache_manager.set(cache_key, events)
            return events
        except Exception as e:
            logger.warning(f"ACLED API failed: {e}, returning mock data")
            return self._get_mock_conflicts(country, limit)

    def _parse_acled_conflicts(
        self, data: Any, country: Optional[str]
    ) -> List[ConflictEvent]:
        events = []
        if not data or "data" not in data:
            return events

        for idx, item in enumerate(data.get("data", [])):
            try:
                location = Location(
                    lat=float(item.get("latitude", 0)),
                    lon=float(item.get("longitude", 0)),
                    country=item.get("country"),
                    country_code=item.get("iso"),
                    region=item.get("admin1"),
                    admin1=item.get("admin2")
                )
                event = ConflictEvent(
                    event_id=str(item.get("data_id", idx)),
                    event_date=datetime.fromisoformat(item.get("event_date", "").replace("Z", "+00:00")),
                    event_type=ConflictType(item.get("event_type", "violence")),
                    sub_event_type=item.get("sub_event_type"),
                    location=location,
                    actor1=item.get("actor1"),
                    actor2=item.get("actor2"),
                    interaction=item.get("interaction"),
                    fatalities=item.get("fatalities"),
                    notes=item.get("notes"),
                    source=item.get("source"),
                    iso_code=item.get("iso")
                )
                events.append(event)
            except Exception as e:
                logger.debug(f"Failed to parse conflict: {e}")
        return events

    def _get_mock_conflicts(
        self, country: Optional[str], limit: int
    ) -> List[ConflictEvent]:
        mock_data = [
            {
                "event_id": f"conflict-{i}",
                "event_date": (datetime.now() - timedelta(days=i)).isoformat(),
                "event_type": "violence",
                "sub_event_type": "Armed clash",
                "lat": 34.0 + i * 0.1,
                "lon": 36.0 + i * 0.1,
                "country": country or "Ukraine",
                "iso": "804",
                "fatalities": 10 + i * 5,
            },
            {
                "event_id": f"conflict-{i+100}",
                "event_date": (datetime.now() - timedelta(days=i+10)).isoformat(),
                "event_type": "protest",
                "sub_event_type": "Protest with stones",
                "lat": -1.0 + i * 0.1,
                "lon": 37.0 + i * 0.1,
                "country": country or "Kenya",
                "iso": "404",
                "fatalities": 0,
            },
            {
                "event_id": f"conflict-{i+200}",
                "event_date": (datetime.now() - timedelta(days=i+5)).isoformat(),
                "event_type": "riot",
                "sub_event_type": "Mob violence",
                "lat": 23.0 + i * 0.1,
                "lon": -82.0 + i * 0.1,
                "country": country or "Haiti",
                "iso": "332",
                "fatalities": 3 + i,
            },
        ]

        events = []
        for item in mock_data[:limit]:
            location = Location(
                lat=item["lat"],
                lon=item["lon"],
                country=item["country"],
                country_code=item["iso"]
            )
            events.append(ConflictEvent(
                event_id=item["event_id"],
                event_date=datetime.fromisoformat(item["event_date"]),
                event_type=ConflictType(item["event_type"]),
                sub_event_type=item["sub_event_type"],
                location=location,
                fatalities=item["fatalities"],
                iso_code=item["iso"]
            ))
        return events

    async def get_disasters(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_magnitude: Optional[float] = None,
        limit: int = 100
    ) -> List[NaturalDisaster]:
        cache_key = f"disasters:{start_time}:{end_time}:{min_magnitude}:{limit}"
        cached = cache_manager.get(cache_key)
        if cached:
            return cached

        if start_time is None:
            start_time = datetime.now() - timedelta(days=7)
        if end_time is None:
            end_time = datetime.now()

        params = {
            "format": "geojson",
            "starttime": start_time.isoformat(),
            "endtime": end_time.isoformat(),
            "limit": limit
        }

        if min_magnitude:
            params["minmagnitude"] = min_magnitude

        try:
            data = await self._request(self.usgs_base, params)
            disasters = self._parse_usgs_earthquakes(data)
            cache_manager.set(cache_key, disasters)
            return disasters
        except Exception as e:
            logger.warning(f"USGS API failed: {e}, returning mock data")
            return self._get_mock_disasters(limit)

    def _parse_usgs_earthquakes(self, data: Any) -> List[NaturalDisaster]:
        disasters = []
        if not data or "features" not in data:
            return disasters

        for feature in data.get("features", []):
            try:
                props = feature.get("properties", {})
                geometry = feature.get("geometry", {})
                coords = geometry.get("coordinates", [0, 0, 0])
                location = Location(
                    lat=coords[1],
                    lon=coords[0],
                    country=props.get("place", "").split(",")[-1].strip() if props.get("place") else None,
                    region=props.get("place", "").split(",")[0].strip() if props.get("place") else None
                )
                disaster = NaturalDisaster(
                    disaster_id=str(props.get("id", "")),
                    disaster_type=DisasterType.EARTHQUAKE,
                    event_time=datetime.fromisoformat(props.get("time", 0) / 1000),
                    location=location,
                    magnitude=props.get("mag"),
                    depth=coords[2] if len(coords) > 2 else None,
                    felt=props.get("felt"),
                    cdi=props.get("cdi"),
                    mmi=props.get("mmi"),
                    alert_level=RiskLevel.MEDIUM if props.get("mag", 0) >= 5 else RiskLevel.LOW,
                    sig=props.get("sig"),
                    place=props.get("place"),
                    title=props.get("title")
                )
                disasters.append(disaster)
            except Exception as e:
                logger.debug(f"Failed to parse disaster: {e}")
        return disasters

    def _get_mock_disasters(self, limit: int) -> List[NaturalDisaster]:
        import random
        mock_data = [
            {
                "disaster_id": "eq-1",
                "disaster_type": "earthquake",
                "time": datetime.now() - timedelta(hours=12),
                "lat": 38.0,
                "lon": 142.0,
                "country": "Japan",
                "magnitude": 5.8,
                "depth": 30.0,
                "place": "Honshu, Japan"
            },
            {
                "disaster_id": "eq-2",
                "disaster_type": "earthquake",
                "time": datetime.now() - timedelta(days=2),
                "lat": 37.5,
                "lon": -122.0,
                "country": "USA",
                "magnitude": 4.2,
                "depth": 15.0,
                "place": "California"
            },
            {
                "disaster_id": "eq-3",
                "disaster_type": "earthquake",
                "time": datetime.now() - timedelta(days=4),
                "lat": 41.0,
                "lon": 43.0,
                "country": "Turkey",
                "magnitude": 4.5,
                "depth": 10.0,
                "place": "Turkey"
            },
            {
                "disaster_id": "eq-4",
                "disaster_type": "earthquake",
                "time": datetime.now() - timedelta(days=1),
                "lat": -15.0,
                "lon": -75.0,
                "country": "Peru",
                "magnitude": 4.8,
                "depth": 25.0,
                "place": "Peru"
            },
        ]

        disasters = []
        for item in mock_data[:limit]:
            location = Location(
                lat=item["lat"],
                lon=item["lon"],
                country=item["country"],
                region=item["place"]
            )
            disasters.append(NaturalDisaster(
                disaster_id=item["disaster_id"],
                disaster_type=DisasterType(item["disaster_type"]),
                event_time=item["time"],
                location=location,
                magnitude=item["magnitude"],
                depth=item["depth"],
                place=item["place"],
                alert_level=RiskLevel.MEDIUM if item["magnitude"] >= 5 else RiskLevel.LOW
            ))
        return disasters

    def calculate_risk_score(
        self,
        conflicts: List[ConflictEvent],
        disasters: List[NaturalDisaster]
    ) -> RiskScore:
        conflict_score = 0.0
        if conflicts:
            total_fatalities = sum(
                c.fatalities or 0 for c in conflicts
            )
            conflict_score = min(100, total_fatalities / 10)

        disaster_score = 0.0
        if disasters:
            for d in disasters:
                if d.magnitude:
                    disaster_score += d.magnitude * 10
            disaster_score = min(100, disaster_score / len(disasters))

        economic_score = conflict_score * 0.7 + disaster_score * 0.3

        overall_score = (conflict_score * 0.4 + disaster_score * 0.3 + economic_score * 0.3)

        affected_regions = list(set(
            c.location.country for c in conflicts if c.location.country
        ))
        affected_regions.extend([
            d.location.country for d in disasters if d.location.country
        ])
        affected_regions = list(set(affected_regions))[:10]

        if overall_score >= 75:
            risk_level = RiskLevel.CRITICAL
        elif overall_score >= 50:
            risk_level = RiskLevel.HIGH
        elif overall_score >= 25:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return RiskScore(
            overall_score=overall_score,
            conflict_score=conflict_score,
            disaster_score=disaster_score,
            economic_score=economic_score,
            timestamp=datetime.now(),
            risk_level=risk_level,
            affected_regions=affected_regions
        )


def get_worldmonitor_client() -> WorldMonitorClient:
    return WorldMonitorClient()