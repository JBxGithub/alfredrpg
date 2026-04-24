"""
Alfred Memory System (AMS) - Database

SQLite 數據庫管理，包含會話、消息、記憶、Skill 等表的創建和管理。
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from contextlib import contextmanager

from ..config import AMSConfig


# 數據庫 Schema
SCHEMA_SQL = """
-- 會話表
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    platform TEXT,
    summary TEXT,
    message_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0
);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role TEXT,
    content TEXT,
    tool_calls TEXT,
    tool_results TEXT,
    token_estimate INTEGER
);

-- 消息全文搜索 (FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content,
    content_rowid=rowid,
    prefix=2,
    tokenize='porter'
);

-- 記憶表
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT,
    source_session TEXT REFERENCES sessions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence REAL DEFAULT 1.0,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    tags TEXT
);

-- 記憶全文搜索
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content,
    content_rowid=rowid,
    prefix=2
);

-- Skill 表
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    version TEXT DEFAULT '1.0.0',
    auto_created BOOLEAN DEFAULT FALSE,
    source_sessions TEXT
);

-- Context 使用記錄
CREATE TABLE IF NOT EXISTS context_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens_used INTEGER,
    tokens_limit INTEGER,
    usage_percent REAL,
    action_taken TEXT
);

-- 學習記錄表 (從 LearningEngine 整合)
CREATE TABLE IF NOT EXISTS learnings (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,  -- 'error', 'correction', 'improvement', 'pattern'
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    status TEXT DEFAULT 'pending',  -- 'pending', 'resolved', 'promoted'
    source_session TEXT REFERENCES sessions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- 學習記錄全文搜索
CREATE VIRTUAL TABLE IF NOT EXISTS learnings_fts USING fts5(
    content,
    content_rowid=rowid,
    prefix=2
);

-- 專案狀態追蹤表
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',  -- 'active', 'paused', 'completed', 'archived'
    path TEXT,
    priority INTEGER DEFAULT 3,  -- 1-5, 5為最高
    progress_percent INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT  -- JSON 格式存儲額外信息
);

-- 專案與 Session 關聯表
CREATE TABLE IF NOT EXISTS project_sessions (
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, session_id)
);

-- 觸發器：自動更新記憶的 updated_at
CREATE TRIGGER IF NOT EXISTS update_memory_timestamp 
AFTER UPDATE ON memories
BEGIN
    UPDATE memories SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 觸發器：自動更新 Skill 的 updated_at
CREATE TRIGGER IF NOT EXISTS update_skill_timestamp 
AFTER UPDATE ON skills
BEGIN
    UPDATE skills SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 觸發器：同步消息到 FTS
CREATE TRIGGER IF NOT EXISTS messages_fts_insert 
AFTER INSERT ON messages
BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (NEW.rowid, NEW.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_delete 
AFTER DELETE ON messages
BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES ('delete', OLD.rowid, OLD.content);
END;

-- 觸發器：同步記憶到 FTS
CREATE TRIGGER IF NOT EXISTS memories_fts_insert 
AFTER INSERT ON memories
BEGIN
    INSERT INTO memories_fts(rowid, content) VALUES (NEW.rowid, NEW.content);
END;

CREATE TRIGGER IF NOT EXISTS memories_fts_delete 
AFTER DELETE ON memories
BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content) VALUES ('delete', OLD.rowid, OLD.content);
END;

-- 觸發器：同步學習記錄到 FTS
CREATE TRIGGER IF NOT EXISTS learnings_fts_insert 
AFTER INSERT ON learnings
BEGIN
    INSERT INTO learnings_fts(rowid, content) VALUES (NEW.rowid, NEW.content);
END;

CREATE TRIGGER IF NOT EXISTS learnings_fts_delete 
AFTER DELETE ON learnings
BEGIN
    INSERT INTO learnings_fts(learnings_fts, rowid, content) VALUES ('delete', OLD.rowid, OLD.content);
END;

-- 觸發器：自動更新專案的 last_updated
CREATE TRIGGER IF NOT EXISTS update_project_timestamp 
AFTER UPDATE ON projects
BEGIN
    UPDATE projects SET last_updated = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- 索引
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
CREATE INDEX IF NOT EXISTS idx_memories_accessed ON memories(last_accessed);
CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name);
CREATE INDEX IF NOT EXISTS idx_context_usage_session ON context_usage(session_id);
CREATE INDEX IF NOT EXISTS idx_context_usage_timestamp ON context_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_learnings_type ON learnings(type);
CREATE INDEX IF NOT EXISTS idx_learnings_status ON learnings(status);
CREATE INDEX IF NOT EXISTS idx_learnings_category ON learnings(category);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_priority ON projects(priority);
CREATE INDEX IF NOT EXISTS idx_project_sessions_project ON project_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_project_sessions_session ON project_sessions(session_id);
"""


class DatabaseManager:
    """數據庫管理器"""
    
    def __init__(self, config: Optional[AMSConfig] = None):
        self.config = config or AMSConfig()
        self.db_path = self.config.get_db_path()
        self._ensure_db_directory()
    
    def _ensure_db_directory(self):
        """確保數據庫目錄存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """獲取數據庫連接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def initialize(self):
        """初始化數據庫，創建所有表"""
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
        print(f"✅ Database initialized: {self.db_path}")
    
    def reset(self):
        """重置數據庫（刪除所有數據）"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.initialize()
        print(f"🔄 Database reset: {self.db_path}")
    
    # === 會話操作 ===
    
    def create_session(self, session_id: str, platform: str = 'unknown') -> bool:
        """創建新會話"""
        with self.get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO sessions (id, platform) VALUES (?, ?)",
                    (session_id, platform)
                )
                return True
            except sqlite3.IntegrityError:
                return False  # 會話已存在
    
    def end_session(self, session_id: str, summary: Optional[str] = None):
        """結束會話"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE sessions SET end_time = CURRENT_TIMESTAMP, summary = ? WHERE id = ?",
                (summary, session_id)
            )
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """獲取會話信息"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """列出會話"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY start_time DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
            return [dict(row) for row in rows]
    
    # === 消息操作 ===
    
    def add_message(self, message_id: str, session_id: str, role: str, 
                    content: str, tool_calls: Optional[List] = None,
                    tool_results: Optional[List] = None, 
                    token_estimate: int = 0) -> bool:
        """添加消息"""
        with self.get_connection() as conn:
            try:
                conn.execute(
                    """INSERT INTO messages 
                       (id, session_id, role, content, tool_calls, tool_results, token_estimate)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (message_id, session_id, role, content,
                     json.dumps(tool_calls) if tool_calls else None,
                     json.dumps(tool_results) if tool_results else None,
                     token_estimate)
                )
                # 更新會話消息計數
                conn.execute(
                    "UPDATE sessions SET message_count = message_count + 1 WHERE id = ?",
                    (session_id,)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """獲取會話的所有消息"""
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM messages 
                   WHERE session_id = ? 
                   ORDER BY timestamp""",
                (session_id,)
            ).fetchall()
            messages = []
            for row in rows:
                msg = dict(row)
                if msg.get('tool_calls'):
                    msg['tool_calls'] = json.loads(msg['tool_calls'])
                if msg.get('tool_results'):
                    msg['tool_results'] = json.loads(msg['tool_results'])
                messages.append(msg)
            return messages
    
    # === 記憶操作 ===
    
    def add_memory(self, memory_id: str, content: str, category: str,
                   source_session: Optional[str] = None,
                   confidence: float = 1.0, tags: Optional[List[str]] = None) -> bool:
        """添加記憶"""
        with self.get_connection() as conn:
            try:
                conn.execute(
                    """INSERT INTO memories 
                       (id, content, category, source_session, confidence, tags)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (memory_id, content, category, source_session, confidence,
                     json.dumps(tags) if tags else None)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_memory(self, memory_id: str) -> Optional[Dict]:
        """獲取記憶"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
            if row:
                mem = dict(row)
                if mem.get('tags'):
                    mem['tags'] = json.loads(mem['tags'])
                return mem
            return None
    
    def update_memory_access(self, memory_id: str):
        """更新記憶訪問計數"""
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE memories 
                   SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (memory_id,)
            )
    
    def list_memories(self, category: Optional[str] = None, 
                      limit: int = 100) -> List[Dict]:
        """列出記憶"""
        with self.get_connection() as conn:
            if category:
                rows = conn.execute(
                    """SELECT * FROM memories 
                       WHERE category = ? 
                       ORDER BY last_accessed DESC NULLS LAST, created_at DESC
                       LIMIT ?""",
                    (category, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM memories 
                       ORDER BY last_accessed DESC NULLS LAST, created_at DESC
                       LIMIT ?""",
                    (limit,)
                ).fetchall()
            
            memories = []
            for row in rows:
                mem = dict(row)
                if mem.get('tags'):
                    mem['tags'] = json.loads(mem['tags'])
                memories.append(mem)
            return memories
    
    def delete_memory(self, memory_id: str) -> bool:
        """刪除記憶"""
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0
    
    def search_memories(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索記憶（使用 FTS5）"""
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT m.* FROM memories m
                   JOIN memories_fts fts ON m.rowid = fts.rowid
                   WHERE memories_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit)
            ).fetchall()
            
            memories = []
            for row in rows:
                mem = dict(row)
                if mem.get('tags'):
                    mem['tags'] = json.loads(mem['tags'])
                memories.append(mem)
            return memories
    
    # === Skill 操作 ===
    
    def add_skill(self, skill_id: str, name: str, description: str,
                  content: str, auto_created: bool = False,
                  source_sessions: Optional[List[str]] = None) -> bool:
        """添加 Skill"""
        with self.get_connection() as conn:
            try:
                conn.execute(
                    """INSERT INTO skills 
                       (id, name, description, content, auto_created, source_sessions)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (skill_id, name, description, content, auto_created,
                     json.dumps(source_sessions) if source_sessions else None)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def update_skill_usage(self, skill_name: str, success: bool = True):
        """更新 Skill 使用統計"""
        with self.get_connection() as conn:
            if success:
                conn.execute(
                    """UPDATE skills 
                       SET usage_count = usage_count + 1, 
                           success_count = success_count + 1,
                           last_used = CURRENT_TIMESTAMP
                       WHERE name = ?""",
                    (skill_name,)
                )
            else:
                conn.execute(
                    """UPDATE skills 
                       SET usage_count = usage_count + 1, 
                           failure_count = failure_count + 1,
                           last_used = CURRENT_TIMESTAMP
                       WHERE name = ?""",
                    (skill_name,)
                )
    
    def get_skill(self, skill_name: str) -> Optional[Dict]:
        """獲取 Skill"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM skills WHERE name = ?", (skill_name,)
            ).fetchone()
            if row:
                skill = dict(row)
                if skill.get('source_sessions'):
                    skill['source_sessions'] = json.loads(skill['source_sessions'])
                return skill
            return None
    
    def list_skills(self, auto_created_only: bool = False) -> List[Dict]:
        """列出 Skills"""
        with self.get_connection() as conn:
            if auto_created_only:
                rows = conn.execute(
                    "SELECT * FROM skills WHERE auto_created = TRUE ORDER BY usage_count DESC"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM skills ORDER BY usage_count DESC"
                ).fetchall()
            
            skills = []
            for row in rows:
                skill = dict(row)
                if skill.get('source_sessions'):
                    skill['source_sessions'] = json.loads(skill['source_sessions'])
                skills.append(skill)
            return skills
    
    # === Context 使用記錄 ===
    
    def log_context_usage(self, session_id: str, tokens_used: int,
                          tokens_limit: int, usage_percent: float,
                          action_taken: Optional[str] = None):
        """記錄 Context 使用情況"""
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO context_usage 
                   (session_id, tokens_used, tokens_limit, usage_percent, action_taken)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, tokens_used, tokens_limit, usage_percent, action_taken)
            )
    
    def get_context_usage_history(self, session_id: Optional[str] = None,
                                   limit: int = 100) -> List[Dict]:
        """獲取 Context 使用歷史"""
        with self.get_connection() as conn:
            if session_id:
                rows = conn.execute(
                    """SELECT * FROM context_usage 
                       WHERE session_id = ? 
                       ORDER BY timestamp DESC LIMIT ?""",
                    (session_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM context_usage 
                       ORDER BY timestamp DESC LIMIT ?""",
                    (limit,)
                ).fetchall()
            return [dict(row) for row in rows]
    
    # === 學習記錄操作 ===
    
    def add_learning(self, entry_id: str, entry_type: str, content: str,
                     category: str = "general", status: str = "pending",
                     source_session: Optional[str] = None) -> bool:
        """添加學習記錄"""
        with self.get_connection() as conn:
            try:
                conn.execute(
                    """INSERT INTO learnings 
                       (id, type, content, category, status, source_session)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (entry_id, entry_type, content, category, status, source_session)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_learning(self, entry_id: str) -> Optional[Dict]:
        """獲取學習記錄"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM learnings WHERE id = ?", (entry_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def list_learnings(self, entry_type: Optional[str] = None,
                       status: Optional[str] = None,
                       category: Optional[str] = None,
                       limit: int = 100) -> List[Dict]:
        """列出學習記錄"""
        with self.get_connection() as conn:
            query = "SELECT * FROM learnings WHERE 1=1"
            params = []
            
            if entry_type:
                query += " AND type = ?"
                params.append(entry_type)
            if status:
                query += " AND status = ?"
                params.append(status)
            if category:
                query += " AND category = ?"
                params.append(category)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    def update_learning_status(self, entry_id: str, status: str) -> bool:
        """更新學習記錄狀態"""
        with self.get_connection() as conn:
            if status == 'resolved':
                cursor = conn.execute(
                    """UPDATE learnings 
                       SET status = ?, resolved_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (status, entry_id)
                )
            else:
                cursor = conn.execute(
                    "UPDATE learnings SET status = ? WHERE id = ?",
                    (status, entry_id)
                )
            return cursor.rowcount > 0
    
    def search_learnings(self, query: str, limit: int = 10) -> List[Dict]:
        """搜索學習記錄"""
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT l.* FROM learnings l
                   JOIN learnings_fts fts ON l.rowid = fts.rowid
                   WHERE learnings_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit)
            ).fetchall()
            return [dict(row) for row in rows]
    
    # === 專案操作 ===
    
    def add_project(self, project_id: str, name: str, description: str = "",
                    path: Optional[str] = None, priority: int = 3,
                    status: str = "active",
                    metadata: Optional[Dict] = None) -> bool:
        """添加專案"""
        with self.get_connection() as conn:
            try:
                conn.execute(
                    """INSERT INTO projects 
                       (id, name, description, path, priority, status, metadata)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (project_id, name, description, path, priority, status,
                     json.dumps(metadata) if metadata else None)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """獲取專案"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
            if row:
                proj = dict(row)
                if proj.get('metadata'):
                    proj['metadata'] = json.loads(proj['metadata'])
                return proj
            return None
    
    def get_project_by_name(self, name: str) -> Optional[Dict]:
        """通過名稱獲取專案"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM projects WHERE name = ?", (name,)
            ).fetchone()
            if row:
                proj = dict(row)
                if proj.get('metadata'):
                    proj['metadata'] = json.loads(proj['metadata'])
                return proj
            return None
    
    def list_projects(self, status: Optional[str] = None,
                      limit: int = 50) -> List[Dict]:
        """列出專案"""
        with self.get_connection() as conn:
            if status:
                rows = conn.execute(
                    """SELECT * FROM projects 
                       WHERE status = ? 
                       ORDER BY priority DESC, last_updated DESC
                       LIMIT ?""",
                    (status, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM projects 
                       ORDER BY priority DESC, last_updated DESC
                       LIMIT ?""",
                    (limit,)
                ).fetchall()
            
            projects = []
            for row in rows:
                proj = dict(row)
                if proj.get('metadata'):
                    proj['metadata'] = json.loads(proj['metadata'])
                projects.append(proj)
            return projects
    
    def update_project(self, project_id: str, 
                       status: Optional[str] = None,
                       progress_percent: Optional[int] = None,
                       description: Optional[str] = None) -> bool:
        """更新專案"""
        with self.get_connection() as conn:
            updates = []
            params = []
            
            if status:
                updates.append("status = ?")
                params.append(status)
            if progress_percent is not None:
                updates.append("progress_percent = ?")
                params.append(progress_percent)
            if description:
                updates.append("description = ?")
                params.append(description)
            
            if not updates:
                return False
            
            params.append(project_id)
            query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ?"
            
            cursor = conn.execute(query, params)
            return cursor.rowcount > 0
    
    def link_session_to_project(self, project_id: str, session_id: str) -> bool:
        """將 Session 關聯到專案"""
        with self.get_connection() as conn:
            try:
                conn.execute(
                    """INSERT INTO project_sessions (project_id, session_id)
                       VALUES (?, ?)""",
                    (project_id, session_id)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_project_sessions(self, project_id: str) -> List[Dict]:
        """獲取專案關聯的所有 Sessions"""
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT s.* FROM sessions s
                   JOIN project_sessions ps ON s.id = ps.session_id
                   WHERE ps.project_id = ?
                   ORDER BY s.start_time DESC""",
                (project_id,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    # === 統計信息 ===
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取數據庫統計信息"""
        with self.get_connection() as conn:
            stats = {}
            
            # 會話統計
            row = conn.execute("SELECT COUNT(*) as count FROM sessions").fetchone()
            stats['total_sessions'] = row['count']
            
            # 消息統計
            row = conn.execute("SELECT COUNT(*) as count FROM messages").fetchone()
            stats['total_messages'] = row['count']
            
            # 記憶統計
            row = conn.execute("SELECT COUNT(*) as count FROM memories").fetchone()
            stats['total_memories'] = row['count']
            
            row = conn.execute(
                "SELECT category, COUNT(*) as count FROM memories GROUP BY category"
            ).fetchall()
            stats['memories_by_category'] = {r['category']: r['count'] for r in row}
            
            # Skill 統計
            row = conn.execute("SELECT COUNT(*) as count FROM skills").fetchone()
            stats['total_skills'] = row['count']
            
            row = conn.execute(
                "SELECT COUNT(*) as count FROM skills WHERE auto_created = TRUE"
            ).fetchone()
            stats['auto_created_skills'] = row['count']
            
            # 學習記錄統計
            row = conn.execute("SELECT COUNT(*) as count FROM learnings").fetchone()
            stats['total_learnings'] = row['count']
            
            row = conn.execute(
                "SELECT status, COUNT(*) as count FROM learnings GROUP BY status"
            ).fetchall()
            stats['learnings_by_status'] = {r['status']: r['count'] for r in row}
            
            # 專案統計
            row = conn.execute("SELECT COUNT(*) as count FROM projects").fetchone()
            stats['total_projects'] = row['count']
            
            row = conn.execute(
                "SELECT status, COUNT(*) as count FROM projects GROUP BY status"
            ).fetchall()
            stats['projects_by_status'] = {r['status']: r['count'] for r in row}
            
            # 數據庫大小
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            stats['db_size_mb'] = round(db_size / (1024 * 1024), 2)
            
            return stats
