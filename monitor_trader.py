#!/usr/bin/env python3
"""
Trader Monitor - 監控 survival_trader 狀態
每30秒報告一次
"""
import time
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("C:/Users/BurtClaw/openclaw_workspace/trader_status.json")

def log_status(status, message=""):
    """記錄狀態到 JSON 檔案"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "message": message
    }
    with open(LOG_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {status}: {message}")

if __name__ == "__main__":
    print("Trader Monitor 啟動...")
    log_status("MONITOR_START", "監控程序已啟動")
    
    counter = 0
    while True:
        counter += 1
        log_status("HEARTBEAT", f"監控運行中 - 第 {counter} 次檢查")
        time.sleep(30)
