#!/usr/bin/env python3
"""
六循環系統監控器
Six-Loop System Monitor
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/system-monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "trading_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "PostgresqL")
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def check_data_flow():
    """Check if data is flowing through the system"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check raw_market_data
                cur.execute("SELECT COUNT(*) as count FROM raw_market_data WHERE timestamp > NOW() - INTERVAL '5 minutes'")
                raw_count = cur.fetchone()['count']
                
                # Check absolute_scores
                cur.execute("SELECT COUNT(*) as count FROM absolute_scores WHERE timestamp > NOW() - INTERVAL '5 minutes'")
                abs_count = cur.fetchone()['count']
                
                # Check reference_scores
                cur.execute("SELECT COUNT(*) as count FROM reference_scores WHERE timestamp > NOW() - INTERVAL '5 minutes'")
                ref_count = cur.fetchone()['count']
                
                # Check decisions
                cur.execute("SELECT COUNT(*) as count FROM decisions WHERE timestamp > NOW() - INTERVAL '5 minutes'")
                dec_count = cur.fetchone()['count']
                
                return {
                    'raw_market_data': raw_count,
                    'absolute_scores': abs_count,
                    'reference_scores': ref_count,
                    'decisions': dec_count
                }
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return None


def get_latest_decision():
    """Get the latest trading decision"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT * FROM decisions 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                return cur.fetchone()
    except Exception as e:
        logger.error(f"Failed to get latest decision: {e}")
        return None


def print_status():
    """Print system status"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("=" * 60)
    print("  六循環系統監控器 - Six-Loop System Monitor")
    print("=" * 60)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    # Check data flow
    flow = check_data_flow()
    if flow:
        print("📊 Data Flow (Last 5 minutes):")
        print(f"   Raw Market Data: {flow['raw_market_data']} records")
        print(f"   Absolute Scores: {flow['absolute_scores']} records")
        print(f"   Reference Scores: {flow['reference_scores']} records")
        print(f"   Decisions: {flow['decisions']} records")
        print()
    else:
        print("❌ Database connection failed!")
        print()
    
    # Latest decision
    decision = get_latest_decision()
    if decision:
        print("🎯 Latest Decision:")
        print(f"   ID: {decision['id']}")
        print(f"   Signal: {decision['signal']}")
        print(f"   Final Score: {decision['final_score']}")
        print(f"   Absolute: {decision['absolute_score']}")
        print(f"   Reference: {decision['reference_score']}")
        print(f"   Risk Check: {'✅ Passed' if decision['risk_check_passed'] else '❌ Failed'}")
        print(f"   Time: {decision['timestamp']}")
        print()
    else:
        print("⚠️  No decisions found")
        print()
    
    print("=" * 60)
    print("Press Ctrl+C to exit")
    print("=" * 60)


def main():
    logger.info("Starting Six-Loop System Monitor...")
    
    try:
        while True:
            print_status()
            time.sleep(5)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
        print("\n👋 Monitor stopped")


if __name__ == "__main__":
    main()