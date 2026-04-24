#!/usr/bin/env python3
"""
Survival Trader Launcher - 啟動 survival_trader.py 並監控
"""
import subprocess
import sys
import time
import socket
from datetime import datetime

def check_opend():
    """檢查 Futu OpenD 是否運行"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 11111))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"[錯誤] 檢查 OpenD 時出錯: {e}")
        return False

def launch_trader():
    """啟動 survival_trader.py"""
    trader_path = r"C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot\survival_trader.py"
    python_exe = r"C:\Python314\python.exe"
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 啟動 survival_trader.py...")
    
    try:
        # 啟動進程
        process = subprocess.Popen(
            [python_exe, trader_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 進程已啟動 (PID: {process.pid})")
        
        # 監控輸出
        while True:
            output = process.stdout.readline()
            if output:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {output.strip()}")
            
            # 檢查進程是否仍在運行
            retcode = process.poll()
            if retcode is not None:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 進程已結束 (返回碼: {retcode})")
                break
                
            time.sleep(0.1)
            
    except Exception as e:
        print(f"[錯誤] 啟動失敗: {e}")
        return False
    
    return True

def main():
    print("="*60)
    print("[生存挑戰] Survival Trader 啟動器")
    print("="*60)
    
    # 1. 檢查 OpenD
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 檢查 Futu OpenD 狀態...")
    if check_opend():
        print("[結果] ✅ OpenD 正在運行 (端口 11111)")
    else:
        print("[結果] ❌ OpenD 未運行 (端口 11111)")
        print("[警告] 請先啟動 Futu OpenD 再運行此腳本")
        return
    
    # 2. 啟動 trader
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 準備啟動交易程序...")
    launch_trader()

if __name__ == "__main__":
    main()
