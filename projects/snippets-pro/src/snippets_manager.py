"""
Snippets Manager - 兼容版
用於 alfred-cli 直接導入
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class SnippetsManager:
    """代碼片段管理器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "snippets.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化數據庫"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS snippets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    code TEXT NOT NULL,
                    language TEXT DEFAULT 'python',
                    tags TEXT DEFAULT '',
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.commit()
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """搜索片段"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM snippets 
                WHERE title LIKE ? OR description LIKE ? OR tags LIKE ?
                ORDER BY updated_at DESC
            """, (f'%{query}%', f'%{query}%', f'%{query}%'))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def add(self, title: str, code: str, language: str = 'python', 
            description: str = '', tags: str = '') -> int:
        """添加片段"""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO snippets (title, description, code, language, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, description, code, language, tags, now, now))
            conn.commit()
            return cursor.lastrowid
