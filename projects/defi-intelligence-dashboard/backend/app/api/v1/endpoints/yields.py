from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.models.base import get_db
from app.crud.yield import (
    get_yields, get_top_yields, get_yield_by_id, build_pagination_meta
)
from app.schemas.response import YieldDataResponse, YieldDataListResponse, TopYieldResponse

router = APIRouter(prefix="/yields", tags=["Yields"])


@router.get("", response_model=YieldDataListResponse)
async def list_yields(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("apy", description="Sort field: apy, tvl_usd, apr"),
    order: str = Query("desc", description="Sort order: asc, desc"),
    chain: Optional[str] = Query(None, description="Filter by chain"),
    protocol_id: Optional[str] = Query(None, description="Filter by protocol"),
    symbol: Optional[str] = Query(None, description="Filter by symbol (partial match)"),
    min_tvl: float = Query(0, ge=0, description="Minimum TVL in USD"),
    min_apy: Optional[float] = Query(None, description="Minimum APY"),
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * page_size
    yields, total = await get_yields(
        db=db,
        skip=skip,
        limit=page_size,
        sort_by=sort_by,
        order=order,
        chain=chain,
        protocol_id=protocol_id,
        symbol=symbol,
        min_tvl=min_tvl,
        min_apy=min_apy
    )
    meta = build_pagination_meta(total, page, page_size)
    
    return YieldDataListResponse(
        items=[YieldDataResponse.model_validate(y) for y in yields],
        meta=meta
    )


@router.get("/top", response_model=TopYieldResponse)
async def get_top_yields_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    min_tvl: float = Query(10000, ge=0, description="Minimum TVL in USD"),
    chains: Optional[str] = Query(None, description="Comma-separated chain list"),
    stablecoin_only: bool = Query(False, description="Only show stablecoin pools"),
    db: AsyncSession = Depends(get_db)
):
    chain_list = chains.split(",") if chains else None
    skip = (page - 1) * page_size
    
    yields, total = await get_top_yields(
        db=db,
        skip=skip,
        limit=page_size,
        min_tvl=min_tvl,
        chains=chain_list,
        stablecoin_only=stablecoin_only
    )
    meta = build_pagination_meta(total, page, page_size)
    
    return TopYieldResponse(
        items=[YieldDataResponse.model_validate(y) for y in yields],
        meta=meta,
        min_tvl=min_tvl,
        sort_by="apy",
        sort_order="desc"
    )


@router.get("/{pool_id}", response_model=YieldDataResponse)
async def get_yield(
    pool_id: str,
    db: AsyncSession = Depends(get_db)
):
    yield_data = await get_yield_by_id(db, pool_id)
    if not yield_data:
        raise HTTPException(status_code=404, detail=f"Yield pool '{pool_id}' not found")
    return YieldDataResponse.model_validate(yield_data)
