#!/usr/bin/env python3
"""
啟動 Survival Trader 並監控輸出
"""
import subprocess
import sys
import time
from datetime import datetime

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 啟動 Survival Trader...")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 工作目錄: C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 帳戶: 6896")
    print("="*50)
    
    try:
        # 啟動 survival_trader.py
        process = subprocess.Popen(
            [sys.executable, "survival_trader.py"],
            cwd=r"C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 進程已啟動 PID: {process.pid}")
        print("="*50)
        
        # 監控輸出
        for line in process.stdout:
            print(line, end='')
            
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 用戶中斷")
        if process:
            process.terminate()
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 錯誤: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
