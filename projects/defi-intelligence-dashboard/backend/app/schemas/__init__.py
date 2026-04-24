from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class DeFiLlamaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ChainSummary(DeFiLlamaBase):
    chain_id: str = Field(alias="id")
    name: str
    slug: str
    tvl: float
    chain_rank: Optional[int] = None
    icon_url: Optional[str] = None


class ProtocolSummary(DeFiLlamaBase):
    protocol_id: str = Field(alias="id")
    name: str
    slug: str
    category: Optional[str] = None
    chain: Optional[str] = None
    tvl: float
    change_1d: Optional[float] = None
    change_7d: Optional[float] = None
    change_30d: Optional[float] = None
    mcap: Optional[float] = None
    fdv: Optional[float] = None
    icon_url: Optional[str] = None


class YieldPool(DeFiLlamaBase):
    pool_id: str = Field(alias="pool")
    protocol_id: str = Field(alias="id")
    chain: str
    project: str
    symbol: str
    tvl_usd: float
    apy: Optional[float] = None
    apr: Optional[float] = None
    reward_tokens: Optional[List[str]] = None
    underlying_tokens: Optional[List[str]] = None
    stablecoin: bool = False


class TVLHistoryPoint(DeFiLlamaBase):
    date: datetime
    tvl: float
    tvlPrev: Optional[float] = None


class ProtocolTVLResponse(DeFiLlamaBase):
    id: str
    name: str
    slug: str
    tvl: float
    tvlHistory: List[TVLHistoryPoint] = []


class ChainTVLResponse(DeFiLlamaBase):
    id: str
    name: str
    tvl: float
    tvlHistory: List[TVLHistoryPoint] = []
