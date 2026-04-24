"""
Database Manager - 數據庫管理器
"""

import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """數據庫管理器"""
    
    def __init__(self, db_path: str = "clawtrade.db"):
        self.db_path = db_path
    
    def init_database(self):
        """初始化數據庫"""
        try:
            with open('schema.sql', 'r') as f:
                schema = f.read()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.executescript(schema)
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    def get_connection(self):
        """獲取數據庫連接"""
        return sqlite3.connect(self.db_path)
    
    def save_price(self, symbol: str, price: float, **kwargs):
        """保存價格數據"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO price_data (symbol, price, open, high, low, volume, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol, price,
            kwargs.get('open'),
            kwargs.get('high'),
            kwargs.get('low'),
            kwargs.get('volume'),
            kwargs.get('source', 'futu')
        ))
        
        conn.commit()
        conn.close()
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """獲取最新價格"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT price FROM price_data
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (symbol,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def save_trade(self, trade: Dict):
        """保存交易記錄"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trades 
            (symbol, side, quantity, entry_price, entry_time, strategy, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade['symbol'],
            trade['side'],
            trade['quantity'],
            trade['entry_price'],
            trade['entry_time'],
            trade.get('strategy', 'TQQQ_Momentum'),
            'OPEN'
        ))
        
        conn.commit()
        conn.close()
    
    def close_trade(self, trade_id: int, exit_price: float, 
                    exit_time: datetime, pnl: float, reason: str):
        """平倉更新"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE trades
            SET exit_price = ?, exit_time = ?, pnl = ?, 
                exit_reason = ?, status = 'CLOSED'
            WHERE id = ?
        ''', (exit_price, exit_time, pnl, reason, trade_id))
        
        conn.commit()
        conn.close()
    
    def save_signal(self, signal: Dict):
        """保存交易信號"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO signals
            (symbol, signal_type, price, z_score, rsi, volume_ratio, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            signal['symbol'],
            signal['signal_type'],
            signal['price'],
            signal.get('z_score'),
            signal.get('rsi'),
            signal.get('volume_ratio'),
            signal.get('reason')
        ))
        
        conn.commit()
        conn.close()
    
    def log_system_event(self, level: str, component: str, message: str):
        """記錄系統事件"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_logs (level, component, message)
            VALUES (?, ?, ?)
        ''', (level, component, message))
        
        conn.commit()
        conn.close()


def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database Manager')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    parser.add_argument('--db', default='clawtrade.db', help='Database path')
    
    args = parser.parse_args()
    
    db = DatabaseManager(args.db)
    
    if args.init:
        db.init_database()
        print(f"✅ Database initialized: {args.db}")
    else:
        print("Use --init to initialize database")


if __name__ == "__main__":
    main()
