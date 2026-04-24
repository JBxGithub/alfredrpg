"""
測試 API 連接
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.futu_client import FutuAPIClient, Market, SubType
from src.utils.logger import setup_logger


def test_quote_connection():
    """測試行情連接"""
    logger = setup_logger()
    logger.info("測試行情連接...")
    
    client = FutuAPIClient(host="127.0.0.1", port=11111)
    
    # 連接行情
    if not client.connect_quote():
        logger.error("行情連接失敗，請確保 OpenD 已啟動")
        return False
    
    # 測試獲取市場快照
    ret_code, ret_data = client.quote_client.get_market_snapshot(["HK.00700"])
    if ret_code == 0:
        logger.info(f"獲取市場快照成功:\n{ret_data}")
    else:
        logger.error(f"獲取市場快照失敗: {ret_data}")
    
    # 測試獲取交易日
    ret_code, ret_data = client.quote_client.get_trading_days(Market.HK)
    if ret_code == 0:
        logger.info(f"獲取交易日成功，共 {len(ret_data)} 天")
    
    # 關閉連接
    client.disconnect_all()
    logger.info("測試完成")
    return True


if __name__ == "__main__":
    test_quote_connection()
