"""
Futu Trading Adapter - Execution Layer
新循環系統 - 執行層 (系統 4)

Analysis: NQ 100 (RSI 30/70, Z-Score)
Execution: TQQQ
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import asyncpg
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

from nq100_analyzer import NQ100Analyzer
from tqqq_executor import TQQQExecutor


class FutuAdapter:
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.nq100_analyzer = NQ100Analyzer()
        self.tqqq_executor = TQQQExecutor()
        
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "trading_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "PostgresqL"),
        }
        
    async def initialize(self):
        """Initialize database connection and components"""
        logger.info("Initializing Futu Adapter...")
        
        self.db_pool = await asyncpg.create_pool(**self.db_config)
        logger.info(f"Connected to PostgreSQL: {self.db_config['database']}")
        
        await self.nq100_analyzer.initialize(self.db_pool)
        await self.tqqq_executor.initialize(self.db_pool)
        
        logger.info("Futu Adapter initialized successfully")
        
    async def close(self):
        """Cleanup resources"""
        if self.db_pool:
            await self.db_pool.close()
        logger.info("Futu Adapter closed")
        
    async def get_latest_decision(self) -> Optional[Dict[str, Any]]:
        """Read latest decision from decisions table"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, absolute_score, reference_score, final_score, 
                       signal, position_size, stop_loss, take_profit,
                       timestamp
                FROM decisions
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            if row:
                return dict(row)
            return None
            
    async def process_cycle(self):
        """Main processing cycle - analyze NQ100, execute TQQQ trades"""
        logger.info("=" * 50)
        logger.info("Processing cycle started")
        logger.info("=" * 50)
        
        decision = await self.get_latest_decision()
        
        if not decision:
            logger.warning("No decision found in decisions table")
            return
            
        logger.info(f"Decision: {decision}")
        
        nq100_analysis = await self.nq100_analyzer.analyze()
        logger.info(f"NQ 100 Analysis: RSI={nq100_analysis.get('rsi')}, Z-Score={nq100_analysis.get('zscore')}")
        
        signal = decision.get("signal")
        
        if signal == "BUY":
            await self.tqqq_executor.execute_buy(
                position_size=decision.get("position_size", 0.33),
                stop_loss=decision.get("stop_loss"),
                take_profit=decision.get("take_profit"),
                nq100_analysis=nq100_analysis
            )
        elif signal == "SELL":
            await self.tqqq_executor.execute_sell(
                stop_loss=decision.get("stop_loss"),
                take_profit=decision.get("take_profit"),
                nq100_analysis=nq100_analysis
            )
        else:
            logger.info("Signal is HOLD, no action taken")
            
        logger.info("Processing cycle completed")


async def main():
    adapter = FutuAdapter()
    
    try:
        await adapter.initialize()
        await adapter.process_cycle()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await adapter.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())