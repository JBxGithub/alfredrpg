#!/usr/bin/env python3
"""
Survival Trader 包裝器 - 啟動並記錄輸出
"""
import sys
import os
import time
from datetime import datetime
from pathlib import Path

# 設置輸出日誌文件
log_file = Path(r"C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot\survival_output.log")

def log_message(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_msg = f"[{timestamp}] {msg}"
    print(full_msg)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(full_msg + '\n')
        f.flush()

# 重定向輸出
class TeeOutput:
    def __init__(self, stdout, file):
        self.stdout = stdout
        self.file = file
    
    def write(self, data):
        self.stdout.write(data)
        self.file.write(data)
        self.file.flush()
    
    def flush(self):
        self.stdout.flush()
        self.file.flush()

# 創建日誌文件
log_file.parent.mkdir(parents=True, exist_ok=True)
log_file.write_text(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Survival Trader 啟動日誌\n", encoding='utf-8')
log_file.write_text("="*50 + "\n", encoding='utf-8')

log_message("啟動 Survival Trader...")
log_message("帳戶: 6896")
log_message("目標: 每日盈利 $50+")
log_message("="*50)

# 導入並運行 survival_trader
try:
    sys.path.insert(0, str(Path(__file__).parent))
    
    # 導入 survival_trader 模塊
    import importlib.util
    spec = importlib.util.spec_from_file_location("survival_trader", 
        r"C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot\survival_trader.py")
    survival_module = importlib.util.module_from_spec(spec)
    
    log_message("正在加載 survival_trader 模塊...")
    spec.loader.exec_module(survival_module)
    
    log_message("模塊加載完成，初始化 SurvivalTrader...")
    trader = survival_module.SurvivalTrader()
    
    log_message("啟動交易循環...")
    trader.run()
    
except Exception as e:
    log_message(f"錯誤: {e}")
    import traceback
    log_message(traceback.format_exc())
    sys.exit(1)

log_message("Survival Trader 已停止")
