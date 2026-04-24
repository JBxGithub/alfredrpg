from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import List, Optional, Tuple
from app.models.entities import YieldData
from app.schemas.response import PaginationMeta
import logging

logger = logging.getLogger(__name__)


async def get_yields(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    sort_by: str = "apy",
    order: str = "desc",
    chain: Optional[str] = None,
    protocol_id: Optional[str] = None,
    symbol: Optional[str] = None,
    min_tvl: float = 0,
    min_apy: Optional[float] = None
) -> Tuple[List[YieldData], int]:
    query = select(YieldData)
    count_query = select(func.count(YieldData.id))
    
    filters = []
    if chain:
        filters.append(YieldData.chain == chain)
    if protocol_id:
        filters.append(YieldData.protocol_id == protocol_id)
    if symbol:
        filters.append(YieldData.symbol.ilike(f"%{symbol}%"))
    if min_tvl > 0:
        filters.append(YieldData.tvl_usd >= min_tvl)
    if min_apy is not None:
        filters.append(YieldData.apy >= min_apy)
    
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    order_col = getattr(YieldData, sort_by, YieldData.apy)
    if order == "asc":
        query = query.order_by(order_col)
    else:
        query = query.order_by(desc(order_col))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    yields = result.scalars().all()
    
    return yields, total


async def get_top_yields(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    min_tvl: float = 10000,
    chains: Optional[List[str]] = None,
    stablecoin_only: bool = False
) -> Tuple[List[YieldData], int]:
    query = select(YieldData)
    count_query = select(func.count(YieldData.id))
    
    filters = [YieldData.tvl_usd >= min_tvl]
    
    if chains:
        filters.append(YieldData.chain.in_(chains))
    if stablecoin_only:
        filters.append(YieldData.stablecoin == 1)
    
    query = query.where(and_(*filters))
    count_query = count_query.where(and_(*filters))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(desc(YieldData.apy)).offset(skip).limit(limit)
    result = await db.execute(query)
    yields = result.scalars().all()
    
    return yields, total


async def get_yield_by_id(db: AsyncSession, pool_id: str) -> Optional[YieldData]:
    query = select(YieldData).where(YieldData.pool_id == pool_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_yield(db: AsyncSession, yield_data: dict) -> YieldData:
    yield_record = YieldData(**yield_data)
    db.add(yield_record)
    await db.flush()
    await db.refresh(yield_record)
    return yield_record


async def update_yield(db: AsyncSession, pool_id: str, yield_data: dict) -> Optional[YieldData]:
    yield_record = await get_yield_by_id(db, pool_id)
    if not yield_record:
        return None
    
    for key, value in yield_data.items():
        if hasattr(yield_record, key):
            setattr(yield_record, key, value)
    
    await db.flush()
    await db.refresh(yield_record)
    return yield_record


async def delete_yield(db: AsyncSession, pool_id: str) -> bool:
    yield_record = await get_yield_by_id(db, pool_id)
    if not yield_record:
        return False
    
    await db.delete(yield_record)
    await db.flush()
    return True


async def bulk_upsert_yields(db: AsyncSession, yields_data: List[dict]) -> int:
    updated_count = 0
    for yield_data in yields_data:
        query = select(YieldData).where(YieldData.pool_id == yield_data.get("pool_id"))
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            for key, value in yield_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
        else:
            db.add(YieldData(**yield_data))
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
