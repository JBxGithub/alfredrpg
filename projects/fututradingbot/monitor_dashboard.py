#!/usr/bin/env python3
"""
Dashboard Monitor - 監控交易狀態
用於無法直接啟動時，通過API監控
"""

import requests
import time
from datetime import datetime

DASHBOARD_URL = "http://127.0.0.1:8080"
PASSWORD = "futu2024"

def check_dashboard():
    """檢查Dashboard狀態"""
    try:
        # 檢查健康狀態
        resp = requests.get(f"{DASHBOARD_URL}/api/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Dashboard: OK")
            print(f"  Account: ${data.get('total_assets', 0):,.2f}")
            print(f"  Cash: ${data.get('cash', 0):,.2f}")
            print(f"  PnL: ${data.get('daily_pnl', 0):,.2f}")
            return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Dashboard: OFFLINE - {e}")
    return False

def monitor():
    """持續監控"""
    print("="*50)
    print("[MONITOR] FutuTradingBot Dashboard Monitor")
    print("="*50)
    
    while True:
        check_dashboard()
        time.sleep(30)  # 30秒檢查一次

if __name__ == "__main__":
    monitor()
