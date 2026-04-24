"""
NQ 100 Analyzer - Analysis Core
新循環系統 - NQ 100 分析核心

RSI 30/70 threshold
Z-Score calculation
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from decimal import Decimal

import asyncpg
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class NQ100Analyzer:
    RSI_LOWER = 30
    RSI_UPPER = 70
    ZSCORE_LOWER = -2.0
    ZSCORE_UPPER = 2.0
    
    def __init__(self):
        self.db_pool = None
        
    async def initialize(self, db_pool: asyncpg.Pool):
        """Initialize with database connection"""
        self.db_pool = db_pool
        logger.info("NQ 100 Analyzer initialized")
        
    async def get_nq100_price_data(self, lookback_days: int = 30) -> pd.DataFrame:
        """Get NQ 100 price data for analysis"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT timestamp, close as price
                FROM raw_market_data
                WHERE symbol = 'MNQ'
                    AND timestamp > NOW() - INTERVAL '$1 days'
                ORDER BY timestamp ASC
            """, lookback_days)
            
            if not rows:
                rows = await conn.fetch("""
                    SELECT timestamp, price
                    FROM raw_market_data
                    WHERE symbol = 'NQ100'
                        AND timestamp > NOW() - INTERVAL '$1 days'
                    ORDER BY timestamp ASC
                """, lookback_days)
                
            if not rows:
                rows = await conn.fetch("""
                    SELECT timestamp, price
                    FROM raw_market_data
                    WHERE symbol = 'NDAQ'
                        AND timestamp > NOW() - INTERVAL '$1 days'
                    ORDER BY timestamp ASC
                """, lookback_days)
                
            if rows:
                df = pd.DataFrame(rows, columns=["timestamp", "price"])
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df["price"] = pd.to_numeric(df["price"], errors="coerce")
                return df.dropna()
            return pd.DataFrame()
            
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50.0
            
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not rsi.iloc[-1].isna() else 50.0
        
    def calculate_zscore(self, prices: pd.Series, lookback: int = 20) -> float:
        """Calculate Z-Score for mean reversion signal"""
        if len(prices) < lookback:
            return 0.0
            
        prices = prices.tail(lookback)
        mean = prices.mean()
        std = prices.std()
        
        if std == 0:
            return 0.0
            
        current_price = prices.iloc[-1]
        zscore = (current_price - mean) / std
        
        return float(zscore)
        
    def calculate_ma_scores(self, prices: pd.Series) -> Dict[str, float]:
        """Calculate MA-based scores"""
        if len(prices) < 50:
            return {"ma50_score": 50, "ma200_score": 50}
            
        ma50 = prices.rolling(window=50).mean().iloc[-1]
        ma200 = prices.rolling(window=200).mean().iloc[-1]
        current = prices.iloc[-1]
        
        if pd.isna(ma50) or pd.isna(ma200):
            return {"ma50_score": 50, "ma200_score": 50}
            
        ma50_score = min(100, max(0, (current / ma50 - 1) * 1000 + 50))
        ma200_score = min(100, max(0, (current / ma200 - 1) * 1000 + 50))
        
        return {
            "ma50_score": ma50_score,
            "ma200_score": ma200_score
        }
        
    async def analyze(self) -> Dict[str, Any]:
        """Main analysis function - returns NQ 100 signals"""
        logger.info("Analyzing NQ 100...")
        
        df = await self.get_nq100_price_data(lookback_days=60)
        
        if df.empty:
            logger.warning("No NQ 100 data available, using defaults")
            return {
                "rsi": 50.0,
                "zscore": 0.0,
                "ma50_score": 50,
                "ma200_score": 50,
                "signal": "HOLD",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        prices = df["price"]
        
        rsi = self.calculate_rsi(prices, period=14)
        zscore = self.calculate_zscore(prices, lookback=20)
        ma_scores = self.calculate_ma_scores(prices)
        
        signal = "HOLD"
        if rsi <= self.RSI_LOWER and zscore <= self.ZSCORE_LOWER:
            signal = "BUY"
        elif rsi >= self.RSI_UPPER and zscore >= self.ZSCORE_UPPER:
            signal = "SELL"
            
        logger.info(f"NQ 100 Analysis: RSI={rsi:.1f}, Z-Score={zscore:.2f}, Signal={signal}")
        
        return {
            "rsi": rsi,
            "zscore": zscore,
            "ma50_score": ma_scores["ma50_score"],
            "ma200_score": ma_scores["ma200_score"],
            "signal": signal,
            "timestamp": datetime.utcnow().isoformat(),
            "rsi_thresholds": {"lower": self.RSI_LOWER, "upper": self.RSI_UPPER},
            "zscore_thresholds": {"lower": self.ZSCORE_LOWER, "upper": self.ZSCORE_UPPER}
        }