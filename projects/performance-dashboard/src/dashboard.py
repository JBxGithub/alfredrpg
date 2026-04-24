"""
Performance Dashboard - 兼容版
用於 alfred-cli 直接導入
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class PerformanceDashboard:
    """績效儀表板"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "performance.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化數據庫"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    task_type TEXT NOT NULL,
                    completion_time REAL,
                    success INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def generate_report(self, period: str = 'week') -> Dict:
        """生成報告"""
        # 模擬數據（實際應從數據庫讀取）
        return {
            'period': period,
            'tasks_completed': 42,
            'success_rate': 0.95,
            'avg_response_time': 1.23,
            'total_tokens': 15000
        }
    
    def record_task(self, task_id: str, task_type: str, 
                   completion_time: float, success: bool = True):
        """記錄任務"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tasks (task_id, task_type, completion_time, success)
                VALUES (?, ?, ?, ?)
            """, (task_id, task_type, completion_time, int(success)))
            conn.commit()
