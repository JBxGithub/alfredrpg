from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.models.base import get_db
from app.crud.chain import get_chains, get_chain_by_id, get_chain_by_slug, build_pagination_meta
from app.schemas.response import ChainResponse, ChainListResponse, ErrorResponse

router = APIRouter(prefix="/chains", tags=["Chains"])


@router.get("", response_model=ChainListResponse)
async def list_chains(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("chain_rank", description="Sort field: chain_rank, tvl, name"),
    order: str = Query("asc", description="Sort order: asc, desc"),
    db: AsyncSession = Depends(get_db)
):
    skip = (page - 1) * page_size
    chains, total = await get_chains(
        db=db,
        skip=skip,
        limit=page_size,
        sort_by=sort_by,
        order=order
    )
    meta = build_pagination_meta(total, page, page_size)
    
    return ChainListResponse(
        items=[ChainResponse.model_validate(chain) for chain in chains],
        meta=meta
    )


@router.get("/{chain_id}", response_model=ChainResponse)
async def get_chain(
    chain_id: str,
    db: AsyncSession = Depends(get_db)
):
    chain = await get_chain_by_id(db, chain_id)
    if not chain:
        raise HTTPException(status_code=404, detail=f"Chain '{chain_id}' not found")
    return ChainResponse.model_validate(chain)


@router.get("/slug/{slug}", response_model=ChainResponse)
async def get_chain_by_slug_endpoint(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    chain = await get_chain_by_slug(db, slug)
    if not chain:
        raise HTTPException(status_code=404, detail=f"Chain with slug '{slug}' not found")
    return ChainResponse.model_validate(chain)
