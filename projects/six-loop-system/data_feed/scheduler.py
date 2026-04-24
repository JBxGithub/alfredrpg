import os
import sys
import time
import logging
from datetime import datetime, date
import schedule

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nq100_constituents import NQ100Fetcher, DatabaseManager, run

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def job():
    logger.info("=" * 50)
    logger.info("排程任務執行")
    logger.info("=" * 50)
    
    try:
        constituents = run()
        
        if constituents:
            logger.info(f"✅ 成功更新 {len(constituents)} 隻成份股")
        else:
            logger.error("❌ 更新失敗")
            
    except Exception as e:
        logger.error(f"排程任務失敗: {e}")


def main():
    logger.info("NQ100 自動更新排程啟動")
    logger.info("-" * 50)
    logger.info("每日執行時間: 09:30, 14:00, 21:00")
    logger.info("-" * 50)
    
    schedule.every().day.at("09:30").do(job)
    schedule.every().day.at("14:00").do(job)
    schedule.every().day.at("21:00").do(job)
    
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()