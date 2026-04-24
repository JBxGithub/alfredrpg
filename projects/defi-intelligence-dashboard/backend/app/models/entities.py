from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class Chain(Base):
    __tablename__ = "chains"

    id = Column(Integer, primary_key=True, index=True)
    chain_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    icon_url = Column(String(500), nullable=True)
    tvl = Column(Float, default=0.0)
    chain_rank = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tvl_history = relationship("TVLData", back_populates="chain")
    yield_data = relationship("YieldData", back_populates="chain")

    __table_args__ = (
        Index("idx_chain_tvl", "tvl"),
        Index("idx_chain_rank", "chain_rank"),
    )


class Protocol(Base):
    __tablename__ = "protocols"

    id = Column(Integer, primary_key=True, index=True)
    protocol_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, nullable=False, index=True)
    category = Column(String(100), nullable=True, index=True)
    chain = Column(String(100), nullable=True, index=True)
    icon_url = Column(String(500), nullable=True)
    tvl = Column(Float, default=0.0)
    change_1d = Column(Float, nullable=True)
    change_7d = Column(Float, nullable=True)
    change_30d = Column(Float, nullable=True)
    mcap = Column(Float, nullable=True)
    fdv = Column(Float, nullable=True)
    listed = Column(Integer, default=0)
   vestige = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    tvl_history = relationship("TVLData", back_populates="protocol")
    yield_data = relationship("YieldData", back_populates="protocol")

    __table_args__ = (
        Index("idx_protocol_tvl", "tvl"),
        Index("idx_protocol_category", "category"),
        Index("idx_protocol_chain", "chain"),
    )


class TVLData(Base):
    __tablename__ = "tvl_data"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(String(100), nullable=False, index=True)
    chain_id = Column(String(100), ForeignKey("chains.chain_id"), nullable=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    tvl = Column(Float, nullable=False)
    tvl_prev_day = Column(Float, nullable=True)
    tvl_change_1d = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chain = relationship("Chain", back_populates="tvl_history")
    protocol = relationship("Protocol", back_populates="tvl_history")

    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "date", name="uq_tvl_entity_date"),
        Index("idx_tvl_entity_date", "entity_type", "entity_id", "date"),
    )


class YieldData(Base):
    __tablename__ = "yield_data"

    id = Column(Integer, primary_key=True, index=True)
    pool_id = Column(String(200), unique=True, nullable=False, index=True)
    protocol_id = Column(String(100), ForeignKey("protocols.protocol_id"), nullable=True)
    chain = Column(String(100), ForeignKey("chains.chain_id"), nullable=True, index=True)
    project = Column(String(200), nullable=True)
    symbol = Column(String(100), nullable=False, index=True)
    pool = Column(String(500), nullable=True)
    tvl_usd = Column(Float, default=0.0)
    apr = Column(Float, nullable=False)
    apy = Column(Float, nullable=True)
    change_1d = Column(Float, nullable=True)
    change_7d = Column(Float, nullable=True)
    outliers = Column(Integer, default=0)
    il_no = Column(Integer, nullable=True)
    reward_tokens = Column(String(500), nullable=True)
    stablecoin = Column(Integer, default=0)
    underlying_tokens = Column(String(500), nullable=True)
    prediction = Column(Integer, default=0)
    confidence = Column(Float, nullable=True)
    count = Column(Integer, default=1)
    mu = Column(Float, nullable=True)
    sigma = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    chain = relationship("Chain", back_populates="yield_data")
    protocol = relationship("Protocol", back_populates="yield_data")

    __table_args__ = (
        Index("idx_yield_apy", "apy"),
        Index("idx_yield_symbol", "symbol"),
        Index("idx_yield_tvl", "tvl_usd"),
    )
