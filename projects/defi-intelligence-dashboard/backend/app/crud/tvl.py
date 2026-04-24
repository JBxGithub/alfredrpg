from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import List, Optional, Tuple
from datetime import datetime
from app.models.entities import TVLData
from app.schemas.response import TVLHistoryResponse, PaginationMeta
import logging

logger = logging.getLogger(__name__)


async def get_tvl_history(
    db: AsyncSession,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    chain_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    sort_by: str = "date",
    order: str = "desc"
) -> Tuple[List[TVLData], int]:
    query = select(TVLData)
    count_query = select(func.count(TVLData.id))
    
    filters = []
    if entity_type:
        filters.append(TVLData.entity_type == entity_type)
    if entity_id:
        filters.append(TVLData.entity_id == entity_id)
    if chain_id:
        filters.append(TVLData.chain_id == chain_id)
    if start_date:
        filters.append(TVLData.date >= start_date)
    if end_date:
        filters.append(TVLData.date <= end_date)
    
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    order_col = getattr(TVLData, sort_by, TVLData.date)
    if order == "asc":
        query = query.order_by(order_col)
    else:
        query = query.order_by(desc(order_col))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    tvl_data = result.scalars().all()
    
    return tvl_data, total


async def get_tvl_by_entity(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[TVLData]:
    query = select(TVLData).where(
        and_(
            TVLData.entity_type == entity_type,
            TVLData.entity_id == entity_id
        )
    )
    
    if start_date:
        query = query.where(TVLData.date >= start_date)
    if end_date:
        query = query.where(TVLData.date <= end_date)
    
    query = query.order_by(TVLData.date)
    result = await db.execute(query)
    return result.scalars().all()


async def create_tvl_data(db: AsyncSession, tvl_data: dict) -> TVLData:
    tvl_record = TVLData(**tvl_data)
    db.add(tvl_record)
    await db.flush()
    await db.refresh(tvl_record)
    return tvl_record


async def bulk_upsert_tvl_data(db: AsyncSession, tvl_data_list: List[dict]) -> int:
    updated_count = 0
    for tvl_data in tvl_data_list:
        query = select(TVLData).where(
            and_(
                TVLData.entity_type == tvl_data.get("entity_type"),
                TVLData.entity_id == tvl_data.get("entity_id"),
                TVLData.date == tvl_data.get("date")
            )
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            for key, value in tvl_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
        else:
            db.add(TVLData(**tvl_data))
        updated_count += 1
    
    await db.flush()
    return updated_count


async def delete_tvl_data(
    db: AsyncSession,
    entity_type: str,
    entity_id: str
) -> int:
    query = select(TVLData).where(
        and_(
            TVLData.entity_type == entity_type,
            TVLData.entity_id == entity_id
        )
    )
    result = await db.execute(query)
    records = result.scalars().all()
    count = len(records)
    
    for record in records:
        await db.delete(record)
    
    await db.flush()
    return count
