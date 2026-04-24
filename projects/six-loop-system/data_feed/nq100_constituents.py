"""
NQ100 成份股爬蟲
從 NASDAQ API 獲取成份股列表，使用 yfinance 獲取市值數據計算權重
"""

import os
import sys
import logging
from datetime import datetime, date
from typing import List, Dict, Optional

import requests
import yfinance as yf
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


class NQ100Fetcher:
    """獲取 NQ100 成份股數據"""
    
    def __init__(self):
        self.nasdaq_api_url = "https://api.nasdaq.com/api/quote/list-type/nasdaq100"
        self.top_n = 50
        
    def fetch_constituents(self) -> List[Dict]:
        """從 NASDAQ API 獲取成份股列表"""
        logger.info("正在從 NASDAQ API 獲取 NQ100 成份股...")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            params = {'offset': 0, 'limit': 102}
            
            response = requests.get(
                self.nasdaq_api_url, 
                headers=headers, 
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            rows = data['data']['data']['rows']
            
            constituents = []
            for row in rows:
                constituents.append({
                    'symbol': row['symbol'],
                    'name': row['companyName'],
                    'market_cap_str': row.get('marketCap', ''),
                    'last_sale_price': row.get('lastSalePrice', ''),
                    'net_change': row.get('netChange', ''),
                    'percentage_change': row.get('percentageChange', '')
                })
            
            logger.info(f"從 NASDAQ API 獲取 {len(constituents)} 隻成份股")
            return constituents
            
        except Exception as e:
            logger.error(f"NASDAQ API 獲取失敗: {e}")
            return []
    
    def get_market_caps(self, symbols: List[str]) -> Dict[str, float]:
        """使用 yfinance 獲取市值數據"""
        logger.info(f"正在獲取 {len(symbols)} 隻股票的市值...")
        market_caps = {}
        
        # 分批處理，避免請求過多
        batch_size = 20
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            logger.info(f"處理第 {i//batch_size + 1} 批 ({len(batch)} 隻)...")
            
            for symbol in batch:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    market_cap = info.get('marketCap', 0)
                    if market_cap:
                        market_caps[symbol] = market_cap
                except Exception as e:
                    logger.warning(f"獲取 {symbol} 市值失敗: {e}")
                    
        logger.info(f"成功獲取 {len(market_caps)} 隻股票的市值")
        return market_caps
    
    def calculate_weights(self, constituents: List[Dict]) -> List[Dict]:
        """計算權重（基於市值）"""
        logger.info("正在計算權重...")
        
        # 獲取市值
        symbols = [c['symbol'] for c in constituents]
        market_caps = self.get_market_caps(symbols)
        
        # 添加市值到成份股數據
        total_market_cap = 0
        for c in constituents:
            c['market_cap'] = market_caps.get(c['symbol'], 0)
            total_market_cap += c['market_cap']
        
        # 計算權重
        for c in constituents:
            if total_market_cap > 0 and c['market_cap'] > 0:
                c['weight'] = (c['market_cap'] / total_market_cap) * 100
            else:
                c['weight'] = 0
        
        # 按權重排序
        constituents.sort(key=lambda x: x['weight'], reverse=True)
        
        return constituents
    
    def get_top_n(self, constituents: List[Dict], n: int = 50) -> List[Dict]:
        """獲取前 N 大權重成份股"""
        top_constituents = constituents[:n]
        
        # 重新計算權重百分比（基於前50隻）
        total_weight = sum(c['weight'] for c in top_constituents)
        if total_weight > 0:
            for c in top_constituents:
                c['weight'] = (c['weight'] / total_weight) * 100
        
        return top_constituents


class DatabaseManager:
    """數據庫管理"""
    
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'sixloop')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', '')
        
    def get_connection(self):
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )
    
    def init_table(self):
        """初始化資料表"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS constituents (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            name VARCHAR(255),
            weight DECIMAL(10, 4),
            market_cap BIGINT,
            market_cap_str VARCHAR(50),
            last_sale_price VARCHAR(20),
            net_change VARCHAR(20),
            percentage_change VARCHAR(20),
            report_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, report_date)
        );
        
        CREATE INDEX IF NOT EXISTS idx_symbol ON constituents(symbol);
        CREATE INDEX IF NOT EXISTS idx_report_date ON constituents(report_date);
        CREATE INDEX IF NOT EXISTS idx_weight ON constituents(weight);
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
            conn.commit()
        logger.info("資料表初始化完成")
    
    def save_constituents(self, constituents: List[Dict], report_date: str):
        """保存成份股到數據庫"""
        if not constituents:
            logger.warning("沒有數據需要存儲")
            return 0
        
        delete_sql = "DELETE FROM constituents WHERE report_date = %s"
        insert_sql = """
        INSERT INTO constituents 
            (symbol, name, weight, market_cap, market_cap_str, 
             last_sale_price, net_change, percentage_change, report_date)
        VALUES %s
        ON CONFLICT (symbol, report_date) DO UPDATE SET
            name = EXCLUDED.name,
            weight = EXCLUDED.weight,
            market_cap = EXCLUDED.market_cap,
            market_cap_str = EXCLUDED.market_cap_str,
            last_sale_price = EXCLUDED.last_sale_price,
            net_change = EXCLUDED.net_change,
            percentage_change = EXCLUDED.percentage_change,
            updated_at = CURRENT_TIMESTAMP
        """
        
        values = [
            (
                c['symbol'],
                c['name'],
                c.get('weight', 0),
                c.get('market_cap', 0),
                c.get('market_cap_str', ''),
                c.get('last_sale_price', ''),
                c.get('net_change', ''),
                c.get('percentage_change', ''),
                report_date
            )
            for c in constituents
        ]
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(delete_sql, (report_date,))
                execute_values(cur, insert_sql, values)
            conn.commit()
        
        logger.info(f"已存儲 {len(constituents)} 隻成份股到資料庫")
        return len(constituents)
    
    def get_constituents(self, report_date: str) -> List[Dict]:
        """獲取指定日期的成份股"""
        sql = """
        SELECT symbol, name, weight, market_cap, report_date, updated_at
        FROM constituents
        WHERE report_date = %s
        ORDER BY weight DESC
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (report_date,))
                rows = cur.fetchall()
                
        return [
            {
                'symbol': r[0],
                'name': r[1],
                'weight': float(r[2]) if r[2] else 0,
                'market_cap': r[3],
                'report_date': r[4],
                'updated_at': r[5]
            }
            for r in rows
        ]


def run(update: bool = False) -> List[Dict]:
    """運行爬蟲"""
    logger.info("=" * 60)
    logger.info("NQ100 成份股爬蟲啟動")
    logger.info("=" * 60)
    
    fetcher = NQ100Fetcher()
    db = DatabaseManager()
    
    report_date = date.today().strftime('%Y-%m-%d')
    
    # 1. 獲取所有成份股
    constituents = fetcher.fetch_constituents()
    if not constituents:
        logger.error("無法獲取成份股列表")
        return []
    
    logger.info(f"獲取 {len(constituents)} 隻成份股")
    
    # 2. 計算權重
    constituents = fetcher.calculate_weights(constituents)
    
    # 3. 取前50
    top_50 = fetcher.get_top_n(constituents, 50)
    
    # 4. 保存到數據庫
    db.init_table()
    saved_count = db.save_constituents(top_50, report_date)
    
    # 5. 顯示結果
    logger.info("\n前10大成份股:")
    for i, c in enumerate(top_50[:10], 1):
        weight_str = f"{c['weight']:.2f}%" if c['weight'] > 0 else "N/A"
        logger.info(f"  {i:2d}. {c['symbol']:6s} - {c['name'][:40]:40s} - 權重: {weight_str}")
    
    logger.info(f"\n✅ 成功存儲 {saved_count} 隻成份股")
    logger.info("=" * 60)
    
    return top_50


if __name__ == "__main__":
    run()
