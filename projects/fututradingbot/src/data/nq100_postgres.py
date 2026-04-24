"""
NQ100 PostgreSQL Data Connector
連接 PostgreSQL 數據庫，提供讀寫接口
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pandas as pd

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'nq100_trading',
    'user': 'postgres',
    'password': 'PostgresqL'
}


class NQ100PostgresConnector:
    """NQ100 PostgreSQL 數據連接器"""
    
    def __init__(self):
        self.conn = None
        self.connect()
    
    def connect(self):
        """建立數據庫連接"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print(f"[NQ100 DB] Connected to PostgreSQL")
        except Exception as e:
            print(f"[NQ100 DB] Connection error: {e}")
            raise
    
    def close(self):
        """關閉連接"""
        if self.conn:
            self.conn.close()
            print("[NQ100 DB] Connection closed")
    
    # ==================== Price Data ====================
    
    def insert_price(self, timestamp: datetime, open_price: float, high: float, 
                     low: float, close: float, volume: int):
        """插入價格數據"""
        query = """
            INSERT INTO nq100_price (timestamp, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (timestamp) DO NOTHING
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (timestamp, open_price, high, low, close, volume))
            self.conn.commit()
    
    def get_latest_price(self) -> Optional[Dict]:
        """獲取最新價格"""
        query = "SELECT * FROM nq100_price ORDER BY timestamp DESC LIMIT 1"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return dict(cur.fetchone()) if cur.rowcount > 0 else None
    
    def get_price_history(self, days: int = 30) -> pd.DataFrame:
        """獲取歷史價格"""
        query = """
            SELECT * FROM nq100_price 
            WHERE timestamp >= NOW() - INTERVAL '%s days'
            ORDER BY timestamp ASC
        """
        return pd.read_sql(query, self.conn, params=(days,))
    
    # ==================== Components ====================
    
    def insert_component(self, symbol: str, name: str, weight: float, 
                        sector: str, market_cap: int, date: datetime.date):
        """插入成份股數據"""
        query = """
            INSERT INTO nq100_components (symbol, name, weight, sector, market_cap, date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (symbol, name, weight, sector, market_cap, date))
            self.conn.commit()
    
    def get_top_components(self, limit: int = 20) -> List[Dict]:
        """獲取前N大權重成份股"""
        query = """
            SELECT symbol, name, weight, sector
            FROM nq100_components
            WHERE date = (SELECT MAX(date) FROM nq100_components)
            ORDER BY weight DESC
            LIMIT %s
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, (limit,))
            return [dict(row) for row in cur.fetchall()]
    
    # ==================== Technical Indicators ====================
    
    def insert_indicators(self, timestamp: datetime, ma_50: float, ma_200: float,
                         ema_20_w: float, ema_50_w: float, rsi: float, 
                         atr: float, macd: float, macd_signal: float):
        """插入技術指標"""
        query = """
            INSERT INTO technical_indicators 
            (timestamp, ma_50, ma_200, ema_20_weekly, ema_50_weekly, rsi_14, atr_14, macd, macd_signal)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (timestamp, ma_50, ma_200, ema_20_w, ema_50_w, 
                              rsi, atr, macd, macd_signal))
            self.conn.commit()
    
    def get_latest_indicators(self) -> Optional[Dict]:
        """獲取最新技術指標"""
        query = "SELECT * FROM technical_indicators ORDER BY timestamp DESC LIMIT 1"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return dict(cur.fetchone()) if cur.rowcount > 0 else None
    
    # ==================== Absolute/Reference Scores ====================
    
    def insert_scores(self, timestamp: datetime, 
                     score_ma200: float, score_ma50: float, score_weekly: float,
                     absolute_total: float, absolute_signal: str,
                     comp_breadth: float, event_risk: float, rsi_score: float, 
                     vol_score: float, reference_total: float,
                     final_signal: str, confidence: float):
        """插入 Absolute/Reference 分數"""
        query = """
            INSERT INTO absolute_reference_scores 
            (timestamp, score_vs_ma200, score_vs_ma50, score_weekly_ema,
             absolute_total, absolute_signal, component_breadth, event_risk,
             rsi_score, volatility_score, reference_total, final_signal, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (timestamp, score_ma200, score_ma50, score_weekly,
                              absolute_total, absolute_signal, comp_breadth, 
                              event_risk, rsi_score, vol_score, reference_total,
                              final_signal, confidence))
            self.conn.commit()
    
    def get_latest_scores(self) -> Optional[Dict]:
        """獲取最新分數"""
        query = "SELECT * FROM absolute_reference_scores ORDER BY timestamp DESC LIMIT 1"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query)
            return dict(cur.fetchone()) if cur.rowcount > 0 else None
    
    # ==================== Trading Decisions ====================
    
    def insert_decision(self, timestamp: datetime, signal: str, 
                       absolute_score: float, reference_score: float,
                       position_size: float, stop_loss: float, take_profit: float):
        """記錄交易決策"""
        query = """
            INSERT INTO trading_decisions 
            (timestamp, signal, absolute_score, reference_score, position_size, stop_loss, take_profit)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (timestamp, signal, absolute_score, reference_score,
                              position_size, stop_loss, take_profit))
            self.conn.commit()
    
    # ==================== Error Protection ====================
    
    def log_error_protection(self, timestamp: datetime, error_type: str, 
                            description: str, action: str):
        """記錄錯誤保護事件"""
        query = """
            INSERT INTO error_protection_log (timestamp, error_type, description, action_taken)
            VALUES (%s, %s, %s, %s)
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (timestamp, error_type, description, action))
            self.conn.commit()
    
    def check_recent_errors(self, hours: int = 24) -> bool:
        """檢查最近是否有錯誤保護事件"""
        query = """
            SELECT COUNT(*) FROM error_protection_log
            WHERE timestamp >= NOW() - INTERVAL '%s hours'
            AND resolved = FALSE
        """
        with self.conn.cursor() as cur:
            cur.execute(query, (hours,))
            count = cur.fetchone()[0]
            return count > 0


# Singleton instance
_db_connector = None

def get_connector() -> NQ100PostgresConnector:
    """獲取數據庫連接器實例"""
    global _db_connector
    if _db_connector is None:
        _db_connector = NQ100PostgresConnector()
    return _db_connector


if __name__ == "__main__":
    # Test connection
    db = get_connector()
    print("Testing NQ100 PostgreSQL connection...")
    
    # Test get latest price
    latest = db.get_latest_price()
    print(f"Latest price: {latest}")
    
    # Test get top components
    top = db.get_top_components(5)
    print(f"Top 5 components: {top}")
    
    db.close()
