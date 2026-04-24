from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple
from app.models.entities import Chain
from app.schemas.response import ChainResponse, PaginationMeta
import logging

logger = logging.getLogger(__name__)


async def get_chains(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    sort_by: str = "chain_rank",
    order: str = "asc"
) -> Tuple[List[Chain], int]:
    order_col = getattr(Chain, sort_by, Chain.chain_rank)
    if order == "desc":
        order_col = desc(order_col)
    
    count_query = select(func.count(Chain.id))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = (
        select(Chain)
        .order_by(order_col)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    chains = result.scalars().all()
    
    return chains, total


async def get_chain_by_id(db: AsyncSession, chain_id: str) -> Optional[Chain]:
    query = select(Chain).where(Chain.chain_id == chain_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_chain_by_slug(db: AsyncSession, slug: str) -> Optional[Chain]:
    query = select(Chain).where(Chain.slug == slug)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_chain(db: AsyncSession, chain_data: dict) -> Chain:
    chain = Chain(**chain_data)
    db.add(chain)
    await db.flush()
    await db.refresh(chain)
    return chain


async def update_chain(db: AsyncSession, chain_id: str, chain_data: dict) -> Optional[Chain]:
    chain = await get_chain_by_id(db, chain_id)
    if not chain:
        return None
    
    for key, value in chain_data.items():
        if hasattr(chain, key):
            setattr(chain, key, value)
    
    await db.flush()
    await db.refresh(chain)
    return chain


async def delete_chain(db: AsyncSession, chain_id: str) -> bool:
    chain = await get_chain_by_id(db, chain_id)
    if not chain:
        return False
    
    await db.delete(chain)
    await db.flush()
    return True


async def bulk_upsert_chains(db: AsyncSession, chains_data: List[dict]) -> int:
    updated_count = 0
    for chain_data in chains_data:
        chain = await get_chain_by_id(db, chain_data.get("chain_id"))
        if chain:
            for key, value in chain_data.items():
                if hasattr(chain, key):
                    setattr(chain, key, value)
        else:
            db.add(Chain(**chain_data))
        updated_count += 1
    
    await db.flush()
    return updated_count


def build_pagination_meta(total: int, page: int, page_size: int) -> PaginationMeta:
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return PaginationMeta(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
