"""
處理記錄追蹤器 - 防止重覆輸入
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# 記錄檔案
PROCESSED_LOG = Path(__file__).parent / '.processed_files.json'


def get_file_hash(file_path: str) -> str:
    """取得檔案雜湊 (用於識別唯一檔案)"""
    try:
        import os
        stat = os.stat(file_path)
        # 使用檔案路徑 + 修改時間 + 大小作為唯一識別
        unique_str = f"{file_path}:{stat.st_mtime}:{stat.st_size}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]
    except:
        return None


def is_file_processed(file_path: str) -> bool:
    """檢查檔案是否已處理"""
    if not PROCESSED_LOG.exists():
        return False
    
    try:
        with open(PROCESSED_LOG, 'r', encoding='utf-8') as f:
            processed = json.load(f)
        
        file_hash = get_file_hash(file_path)
        if not file_hash:
            return False
        
        # 檢查是否在記錄中且未過期 (7天)
        if file_hash in processed:
            processed_time = datetime.fromisoformat(processed[file_hash]['time'])
            if datetime.now() - processed_time < timedelta(days=7):
                return True
        
        return False
        
    except Exception as e:
        print(f"⚠️ 檢查處理記錄失敗: {e}")
        return False


def mark_file_processed(file_path: str, receipt_no: str = '', amount: float = 0):
    """標記檔案為已處理"""
    try:
        # 載入現有記錄
        processed = {}
        if PROCESSED_LOG.exists():
            with open(PROCESSED_LOG, 'r', encoding='utf-8') as f:
                processed = json.load(f)
        
        # 清理過期記錄 (超過7天)
        current_time = datetime.now()
        processed = {
            k: v for k, v in processed.items()
            if current_time - datetime.fromisoformat(v['time']) < timedelta(days=7)
        }
        
        # 添加新記錄
        file_hash = get_file_hash(file_path)
        if file_hash:
            processed[file_hash] = {
                'time': current_time.isoformat(),
                'path': file_path,
                'receipt_no': receipt_no,
                'amount': amount
            }
        
        # 儲存記錄
        with open(PROCESSED_LOG, 'w', encoding='utf-8') as f:
            json.dump(processed, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"⚠️ 標記處理記錄失敗: {e}")
        return False


def get_processed_count() -> int:
    """取得已處理檔案數量"""
    if not PROCESSED_LOG.exists():
        return 0
    
    try:
        with open(PROCESSED_LOG, 'r', encoding='utf-8') as f:
            processed = json.load(f)
        return len(processed)
    except:
        return 0
