"""
Smart Router - 兼容版
用於 alfred-cli 直接導入
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional


class SmartRouter:
    """智能會話路由"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "skills.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._load_default_skills()
    
    def _init_db(self):
        """初始化數據庫"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    keywords TEXT NOT NULL,
                    category TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def _load_default_skills(self):
        """加載默認技能"""
        default_skills = [
            ("desktop-control-win", "Windows desktop control", "desktop,control,windows", "system"),
            ("browser-automation", "Browser automation", "browser,web,automation", "system"),
            ("web-content-fetcher", "Web content fetcher", "web,fetch,content", "system"),
            ("github-cli", "GitHub CLI operations", "github,git,repo", "development"),
            ("data-analysis", "Data analysis tools", "data,analysis,csv", "data"),
            ("tavily-search", "Tavily web search", "search,web,tavily", "search"),
            ("pdf-to-markdown", "PDF to markdown converter", "pdf,convert,markdown", "document"),
            ("ffmpeg", "Video/audio processing", "video,audio,ffmpeg", "media"),
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            for name, desc, keywords, category in default_skills:
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO skills (name, description, keywords, category)
                        VALUES (?, ?, ?, ?)
                    """, (name, desc, keywords, category))
                except:
                    pass
            conn.commit()
    
    def find_best_skills(self, query: str, top_n: int = 3) -> List[Dict]:
        """查找最匹配的技能"""
        query_lower = query.lower()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM skills")
            skills = [dict(row) for row in cursor.fetchall()]
        
        # 簡單匹配算法
        results = []
        for skill in skills:
            score = 0
            keywords = skill.get('keywords', '').lower()
            description = skill.get('description', '').lower()
            name = skill.get('name', '').lower()
            
            # 關鍵字匹配
            if any(word in keywords for word in query_lower.split()):
                score += 3
            
            # 描述匹配
            if any(word in description for word in query_lower.split()):
                score += 2
            
            # 名稱匹配
            if any(word in name for word in query_lower.split()):
                score += 4
            
            if score > 0:
                results.append({
                    'name': skill['name'],
                    'description': skill['description'],
                    'category': skill['category'],
                    'score': score
                })
        
        # 按分數排序
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_n]
