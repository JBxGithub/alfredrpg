#!/usr/bin/env python3
"""
檢查 Survival Trader 狀態
"""
import json
from datetime import datetime
from pathlib import Path

def check_status():
    status_file = Path(r"C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot\trading_status.json")
    
    if status_file.exists():
        with open(status_file, 'r') as f:
            status = json.load(f)
        
        print("="*50)
        print("[Survival Trader 狀態報告]")
        print("="*50)
        print(f"狀態: {status.get('status', '未知')}")
        print(f"帳戶: {status.get('account', '6896')}")
        print(f"運行時間: {status.get('runtime', 'N/A')}")
        print(f"今日盈虧: ${status.get('daily_pnl', 0):.2f}")
        print(f"交易次數: {status.get('trades_today', 0)}")
        print(f"最後更新: {status.get('last_update', 'N/A')}")
        print("="*50)
    else:
        print("[狀態] 交易系統尚未啟動或狀態文件不存在")
        print(f"[時間] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    check_status()
