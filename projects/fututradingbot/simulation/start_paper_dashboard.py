"""
簡化版模擬 Dashboard - 修復啟動問題
直接使用內置服務器，不依賴 uvicorn 命令
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.paper_dashboard import app
import uvicorn

if __name__ == "__main__":
    print("=" * 50)
    print("FutuTradingBot Paper Trading Dashboard")
    print("URL: http://127.0.0.1:8081")
    print("Password: paper2024")
    print("=" * 50)
    print()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8081,
        log_level="info",
        access_log=True
    )
