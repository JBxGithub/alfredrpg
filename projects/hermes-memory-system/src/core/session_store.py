"""
Session Store - SQLite + FTS5 for conversation persistence
Manages all chat sessions with full-text search
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Message:
    """單條消息"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }


@dataclass
class Session:
    """會話記錄"""
    session_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int
    tags: List[str]
    summary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': self.message_count,
            'tags': self.tags,
            'summary': self.summary
        }


class SessionStore:
    """
    會話存儲管理器
    - SQLite 持久化
    - FTS5 全文搜索
    - Gemini Flash 摘要
    """
    
    def __init__(self, db_path: str):
        """初始化會話存儲"""
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_database()
    
    def _ensure_db_dir(self):
        """確保數據庫目錄存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """初始化數據庫結構"""
        with sqlite3.connect(self.db_path) as conn:
            # 會話表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    tags TEXT DEFAULT '[]',
                    summary TEXT
                )
            """)
            
            # 消息表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # FTS5 虛擬表 (全文搜索)
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    content,
                    session_id UNINDEXED,
                    message_id UNINDEXED,
                    tokenize='porter'
                )
            """)
            
            # 觸發器: 插入時同步到 FTS
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages
                BEGIN
                    INSERT INTO messages_fts(content, session_id, message_id)
                    VALUES (NEW.content, NEW.session_id, NEW.message_id);
                END
            """)
            
            # 觸發器: 刪除時同步到 FTS
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages
                BEGIN
                    DELETE FROM messages_fts WHERE message_id = OLD.message_id;
                END
            """)
            
            # 索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at)")
            
            conn.commit()
    
    def create_session(self, session_id: Optional[str] = None, 
                       title: Optional[str] = None) -> str:
        """
        創建新會話
        
        Returns:
            session_id
        """
        if session_id is None:
            session_id = hashlib.md5(
                datetime.now().isoformat().encode()
            ).hexdigest()[:16]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (session_id, title) VALUES (?, ?)",
                (session_id, title)
            )
            conn.commit()
        
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str,
                    metadata: Optional[Dict] = None) -> int:
        """
        添加消息到會話
        
        Returns:
            message_id
        """
        metadata_json = json.dumps(metadata or {})
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """INSERT INTO messages (session_id, role, content, metadata)
                   VALUES (?, ?, ?, ?)""",
                (session_id, role, content, metadata_json)
            )
            message_id = cursor.lastrowid
            
            # 更新會話統計
            conn.execute(
                """UPDATE sessions 
                   SET message_count = message_count + 1,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE session_id = ?""",
                (session_id,)
            )
            
            conn.commit()
        
        return message_id
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        FTS5 全文搜索
        
        Args:
            query: 搜索關鍵詞
            limit: 返回結果數量
        
        Returns:
            匹配的消息列表
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 使用 FTS5 匹配
            cursor = conn.execute(
                """SELECT m.*, s.title as session_title,
                          rank as relevance_score
                   FROM messages_fts fts
                   JOIN messages m ON fts.message_id = m.message_id
                   JOIN sessions s ON fts.session_id = s.session_id
                   WHERE messages_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit)
            )
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'message_id': row['message_id'],
                    'session_id': row['session_id'],
                    'session_title': row['session_title'],
                    'role': row['role'],
                    'content': row['content'],
                    'timestamp': row['timestamp'],
                    'relevance_score': row['relevance_score']
                })
            
            return results
    
    def get_session_messages(self, session_id: str, 
                            limit: Optional[int] = None) -> List[Message]:
        """獲取會話的所有消息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            sql = """SELECT * FROM messages 
                     WHERE session_id = ? 
                     ORDER BY timestamp"""
            params = [session_id]
            
            if limit:
                sql += " LIMIT ?"
                params.append(limit)
            
            cursor = conn.execute(sql, params)
            
            messages = []
            for row in cursor.fetchall():
                messages.append(Message(
                    role=row['role'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    metadata=json.loads(row['metadata'])
                ))
            
            return messages
    
    def get_recent_sessions(self, limit: int = 10) -> List[Session]:
        """獲取最近活躍的會話"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            cursor = conn.execute(
                """SELECT * FROM sessions 
                   ORDER BY updated_at DESC
                   LIMIT ?""",
                (limit,)
            )
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append(Session(
                    session_id=row['session_id'],
                    title=row['title'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at']),
                    message_count=row['message_count'],
                    tags=json.loads(row['tags']),
                    summary=row['summary']
                ))
            
            return sessions
    
    def update_session_summary(self, session_id: str, summary: str):
        """更新會話摘要"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE sessions SET summary = ? WHERE session_id = ?",
                (summary, session_id)
            )
            conn.commit()
    
    def tag_session(self, session_id: str, tags: List[str]):
        """為會話添加標籤"""
        with sqlite3.connect(self.db_path) as conn:
            # 獲取現有標籤
            cursor = conn.execute(
                "SELECT tags FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            existing_tags = json.loads(row[0]) if row else []
            
            # 合併標籤
            all_tags = list(set(existing_tags + tags))
            
            conn.execute(
                "UPDATE sessions SET tags = ? WHERE session_id = ?",
                (json.dumps(all_tags), session_id)
            )
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        with sqlite3.connect(self.db_path) as conn:
            # 會話數
            cursor = conn.execute("SELECT COUNT(*) FROM sessions")
            session_count = cursor.fetchone()[0]
            
            # 消息數
            cursor = conn.execute("SELECT COUNT(*) FROM messages")
            message_count = cursor.fetchone()[0]
            
            # 今日消息數
            cursor = conn.execute(
                """SELECT COUNT(*) FROM messages 
                   WHERE date(timestamp) = date('now')"""
            )
            today_count = cursor.fetchone()[0]
            
            return {
                'total_sessions': session_count,
                'total_messages': message_count,
                'today_messages': today_count,
                'database_path': self.db_path
            }
    
    def export_session(self, session_id: str, format: str = 'json') -> str:
        """
        導出會話
        
        Args:
            format: 'json' or 'markdown'
        """
        messages = self.get_session_messages(session_id)
        
        if format == 'json':
            return json.dumps([m.to_dict() for m in messages], ensure_ascii=False, indent=2)
        
        elif format == 'markdown':
            lines = [f"# Session: {session_id}\n"]
            for msg in messages:
                role_emoji = "👤" if msg.role == "user" else "🤖"
                lines.append(f"{role_emoji} **{msg.role}** ({msg.timestamp.strftime('%Y-%m-%d %H:%M')})")
                lines.append(f"{msg.content}\n")
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
