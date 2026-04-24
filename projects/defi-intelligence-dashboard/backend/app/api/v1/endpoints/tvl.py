from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from app.models.base import get_db
from app.crud.tvl import get_tvl_history, get_tvl_by_entity, build_pagination_meta
from app.schemas.response import TVLHistoryResponse, TVLHistoryListResponse

router = APIRouter(prefix="/tvl", tags=["TVL"])


@router.get("/history", response_model=TVLHistoryListResponse)
async def get_tvl_history_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
    entity_type: Optional[str] = Query(None, description="Entity type: chain, protocol"),
    entity_id: Optional[str] = Query(None, description="Entity ID"),
    chain_id: Optional[str] = Query(None, description="Chain ID filter"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    sort_by: str = Query("date", description="Sort field: date, tvl"),
    order: str = Query("desc", description="Sort order: asc, desc"),
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * page_size
    tvl_data, total = await get_tvl_history(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        chain_id=chain_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=page_size,
        sort_by=sort_by,
        order=order
    )
    meta = build_pagination_meta(total, page, page_size)
    
    return TVLHistoryListResponse(
        items=[TVLHistoryResponse.model_validate(t) for t in tvl_data],
        meta=meta
    )


@router.get("/{entity_type}/{entity_id}", response_model=TVLHistoryListResponse)
async def get_entity_tvl(
    entity_type: str,
    entity_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db)
):
    tvl_data = await get_tvl_by_entity(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return TVLHistoryListResponse(
        items=[TVLHistoryResponse.model_validate(t) for t in tvl_data],
        meta=build_pagination_meta(len(tvl_data), 1, len(tvl_data))
    )
