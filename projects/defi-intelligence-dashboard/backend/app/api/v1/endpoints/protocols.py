from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.models.base import get_db
from app.crud.protocol import get_protocols, get_protocol_by_id, get_protocol_by_slug, build_pagination_meta
from app.schemas.response import ProtocolResponse, ProtocolListResponse

router = APIRouter(prefix="/protocols", tags=["Protocols"])


@router.get("", response_model=ProtocolListResponse)
async def list_protocols(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("tvl", description="Sort field: tvl, change_1d, change_7d, name"),
    order: str = Query("desc", description="Sort order: asc, desc"),
    category: Optional[str] = Query(None, description="Filter by category"),
    chain: Optional[str] = Query(None, description="Filter by chain"),
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * page_size
    protocols, total = await get_protocols(
        db=db,
        skip=skip,
        limit=page_size,
        sort_by=sort_by,
        order=order,
        category=category,
        chain=chain
    )
    meta = build_pagination_meta(total, page, page_size)
    
    return ProtocolListResponse(
        items=[ProtocolResponse.model_validate(p) for p in protocols],
        meta=meta
    )


@router.get("/{protocol_id}", response_model=ProtocolResponse)
async def get_protocol(
    protocol_id: str,
    db: AsyncSession = Depends(get_db)
):
    protocol = await get_protocol_by_id(db, protocol_id)
    if not protocol:
        raise HTTPException(status_code=404, detail=f"Protocol '{protocol_id}' not found")
    return ProtocolResponse.model_validate(protocol)


@router.get("/slug/{slug}", response_model=ProtocolResponse)
async def get_protocol_by_slug_endpoint(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    protocol = await get_protocol_by_slug(db, slug)
    if not protocol:
        raise HTTPException(status_code=404, detail=f"Protocol with slug '{slug}' not found")
    return ProtocolResponse.model_validate(protocol)
