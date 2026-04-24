#!/usr/bin/env python3
"""
Learning Archiver Hook - OpenClaw Session Hook
每次對話結束後自動觸發歸檔
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Skill 路徑
SKILL_DIR = Path(__file__).parent
ARCHIVER_SCRIPT = SKILL_DIR / "archiver.py"

def run_archiver(session_data):
    """執行歸檔腳本"""
    try:
        # 將 session 數據傳遞給 archiver
        result = subprocess.run(
            [sys.executable, str(ARCHIVER_SCRIPT)],
            input=json.dumps(session_data),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"[Learning Archiver] Success: {result.stdout}")
        else:
            print(f"[Learning Archiver] Error: {result.stderr}")
            
    except Exception as e:
        print(f"[Learning Archiver] Failed: {e}")


def on_session_end(session_data):
    """
    OpenClaw Hook: 會話結束時觸發
    
    session_data 格式:
    {
        "session_id": "...",
        "messages": [...],
        "tool_calls": [...],
        "start_time": "...",
        "end_time": "..."
    }
    """
    # 檢查是否有足夠數據
    messages = session_data.get("messages", [])
    
    # 只處理有意義的對話 (>3 條消息)
    if len(messages) < 3:
        return
    
    # 異步執行歸檔 (不阻塞主流程)
    import threading
    thread = threading.Thread(target=run_archiver, args=(session_data,))
    thread.daemon = True
    thread.start()


# 如果直接執行 (測試用)
if __name__ == "__main__":
    # 測試數據
    test_session = {
        "session_id": "test-123",
        "messages": [
            {"role": "user", "content": "幫我設定 heartbeat", "timestamp": "2026-04-19T14:00:00"},
            {"role": "assistant", "content": "好的，我會刪除舊的設定", "timestamp": "2026-04-19T14:00:05"},
            {"role": "user", "content": "錯了，我說 stop 不是 delete", "timestamp": "2026-04-19T14:00:10"},
        ],
        "tool_calls": [
            {"tool": "cron.remove", "status": "executed"},
        ]
    }
    
    on_session_end(test_session)
