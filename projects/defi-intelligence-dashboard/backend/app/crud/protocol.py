from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Optional, Tuple
from app.models.entities import Protocol
from app.schemas.response import ProtocolResponse, PaginationMeta
import logging

logger = logging.getLogger(__name__)


async def get_protocols(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    sort_by: str = "tvl",
    order: str = "desc",
    category: Optional[str] = None,
    chain: Optional[str] = None
) -> Tuple[List[Protocol], int]:
    query = select(Protocol)
    count_query = select(func.count(Protocol.id))
    
    if category:
        query = query.where(Protocol.category == category)
        count_query = count_query.where(Protocol.category == category)
    if chain:
        query = query.where(Protocol.chain == chain)
        count_query = count_query.where(Protocol.chain == chain)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    order_col = getattr(Protocol, sort_by, Protocol.tvl)
    if order == "asc":
        query = query.order_by(order_col)
    else:
        query = query.order_by(desc(order_col))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    protocols = result.scalars().all()
    
    return protocols, total


async def get_protocol_by_id(db: AsyncSession, protocol_id: str) -> Optional[Protocol]:
    query = select(Protocol).where(Protocol.protocol_id == protocol_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_protocol_by_slug(db: AsyncSession, slug: str) -> Optional[Protocol]:
    query = select(Protocol).where(Protocol.slug == slug)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_protocol(db: AsyncSession, protocol_data: dict) -> Protocol:
    protocol = Protocol(**protocol_data)
    db.add(protocol)
    await db.flush()
    await db.refresh(protocol)
    return protocol


async def update_protocol(db: AsyncSession, protocol_id: str, protocol_data: dict) -> Optional[Protocol]:
    protocol = await get_protocol_by_id(db, protocol_id)
    if not protocol:
        return None
    
    for key, value in protocol_data.items():
        if hasattr(protocol, key):
            setattr(protocol, key, value)
    
    await db.flush()
    await db.refresh(protocol)
    return protocol


async def delete_protocol(db: AsyncSession, protocol_id: str) -> bool:
    protocol = await get_protocol_by_id(db, protocol_id)
    if not protocol:
        return False
    
    await db.delete(protocol)
    await db.flush()
    return True


async def bulk_upsert_protocols(db: AsyncSession, protocols_data: List[dict]) -> int:
    updated_count = 0
    for protocol_data in protocols_data:
        protocol = await get_protocol_by_id(db, protocol_data.get("protocol_id"))
        if protocol:
            for key, value in protocol_data.items():
                if hasattr(protocol, key):
                    setattr(protocol, key, value)
        else:
            db.add(Protocol(**protocol_data))
        updated_count += 1
    
    await db.flush()
    return updated_count


async def get_protocols_by_category(db: AsyncSession, category: str) -> List[Protocol]:
    query = select(Protocol).where(Protocol.category == category).order_by(desc(Protocol.tvl))
    result = await db.execute(query)
    return result.scalars().all()


async def get_protocols_by_chain(db: AsyncSession, chain: str) -> List[Protocol]:
    query = select(Protocol).where(Protocol.chain == chain).order_by(desc(Protocol.tvl))
    result = await db.execute(query)
    return result.scalars().all()
