"""
簡化版 Dashboard - 修復啟動問題
直接使用內置服務器，不依賴 uvicorn 命令
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dashboard.app import app
import uvicorn

if __name__ == "__main__":
    print("=" * 50)
    print("FutuTradingBot Dashboard")
    print("URL: http://127.0.0.1:8080")
    print("Password: futu2024")
    print("=" * 50)
    print()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        log_level="info",
        access_log=True
    )
