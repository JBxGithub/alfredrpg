from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Generic, TypeVar, Any
from datetime import datetime


T = TypeVar("T")


class DeFiLlamaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedResponse(Generic[T], DeFiLlamaBase):
    items: List[Any]
    meta: PaginationMeta


class ChainResponse(DeFiLlamaBase):
    id: int
    chain_id: str
    name: str
    slug: str
    icon_url: Optional[str] = None
    tvl: float
    chain_rank: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChainListResponse(PaginatedResponse):
    items: List[ChainResponse]


class ProtocolResponse(DeFiLlamaBase):
    id: int
    protocol_id: str
    name: str
    slug: str
    category: Optional[str] = None
    chain: Optional[str] = None
    icon_url: Optional[str] = None
    tvl: float
    change_1d: Optional[float] = None
    change_7d: Optional[float] = None
    change_30d: Optional[float] = None
    mcap: Optional[float] = None
    fdv: Optional[float] = None
    listed: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProtocolListResponse(PaginatedResponse):
    items: List[ProtocolResponse]


class TVLHistoryResponse(DeFiLlamaBase):
    id: int
    entity_type: str
    entity_id: str
    chain_id: Optional[str] = None
    date: datetime
    tvl: float
    tvl_prev_day: Optional[float] = None
    tvl_change_1d: Optional[float] = None


class TVLHistoryListResponse(PaginatedResponse):
    items: List[TVLHistoryResponse]


class YieldDataResponse(DeFiLlamaBase):
    id: int
    pool_id: str
    protocol_id: Optional[str] = None
    chain: Optional[str] = None
    project: Optional[str] = None
    symbol: str
    pool: Optional[str] = None
    tvl_usd: float
    apr: float
    apy: Optional[float] = None
    change_1d: Optional[float] = None
    change_7d: Optional[float] = None
    outliers: int = 0
    il_no: Optional[int] = None
    reward_tokens: Optional[str] = None
    stablecoin: int = 0
    underlying_tokens: Optional[str] = None
    prediction: int = 0
    confidence: Optional[float] = None
    count: int = 1
    mu: Optional[float] = None
    sigma: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class YieldDataListResponse(PaginatedResponse):
    items: List[YieldDataResponse]


class TopYieldResponse(DeFiLlamaBase):
    items: List[YieldDataResponse]
    meta: PaginationMeta
    min_tvl: Optional[float] = Field(default=0, description="Minimum TVL filter in USD")
    sort_by: str = "apy"
    sort_order: str = "desc"


class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int


class SuccessResponse(BaseModel):
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
