"""Storage management with SQLite."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .snippet import Snippet


class Storage:
    """Manages SQLite database for snippets."""
    
    def __init__(self, db_path: str = "data/snippets.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
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
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snippets_language 
                ON snippets(language)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_snippets_tags 
                ON snippets(tags)
            """)
            conn.commit()
    
    def add(self, snippet: Snippet) -> int:
        """Add a new snippet, return its ID."""
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO snippets (title, description, code, language, tags, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                snippet.title,
                snippet.description,
                snippet.code,
                snippet.language,
                ",".join(snippet.tags),
                now,
                now,
            ))
            conn.commit()
            return cursor.lastrowid
    
    def update(self, snippet: Snippet) -> bool:
        """Update an existing snippet."""
        if snippet.id is None:
            return False
        
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE snippets 
                SET title=?, description=?, code=?, language=?, tags=?, updated_at=?
                WHERE id=?
            """, (
                snippet.title,
                snippet.description,
                snippet.code,
                snippet.language,
                ",".join(snippet.tags),
                now,
                snippet.id,
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete(self, snippet_id: int) -> bool:
        """Delete a snippet by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM snippets WHERE id=?", (snippet_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_by_id(self, snippet_id: int) -> Optional[Snippet]:
        """Get a snippet by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM snippets WHERE id=?", (snippet_id,)).fetchone()
            if row:
                return Snippet.from_dict(dict(row))
            return None
    
    def get_all(self) -> list[Snippet]:
        """Get all snippets."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM snippets ORDER BY updated_at DESC").fetchall()
            return [Snippet.from_dict(dict(row)) for row in rows]
    
    def search(self, query: str = "", language: Optional[str] = None, tags: Optional[list[str]] = None) -> list[Snippet]:
        """Search snippets with filters."""
        sql = "SELECT * FROM snippets WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (title LIKE ? OR description LIKE ? OR code LIKE ?)"
            q = f"%{query}%"
            params.extend([q, q, q])
        
        if language:
            sql += " AND language = ?"
            params.append(language)
        
        if tags:
            for tag in tags:
                sql += " AND tags LIKE ?"
                params.append(f"%{tag}%")
        
        sql += " ORDER BY updated_at DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
            return [Snippet.from_dict(dict(row)) for row in rows]
    
    def count(self) -> int:
        """Count total snippets."""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("SELECT COUNT(*) FROM snippets").fetchone()
            return result[0] if result else 0
    
    def import_from_json(self, json_path: str) -> int:
        """Import snippets from JSON file."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        count = 0
        for item in data.get("snippets", []):
            snippet = Snippet(
                title=item.get("title", ""),
                description=item.get("description", ""),
                code=item.get("code", ""),
                language=item.get("language", "python"),
                tags=item.get("tags", []),
            )
            self.add(snippet)
            count += 1
        
        return count
    
    def export_to_json(self, json_path: str) -> int:
        """Export snippets to JSON file."""
        snippets = self.get_all()
        data = {
            "snippets": [
                {
                    "title": s.title,
                    "description": s.description,
                    "code": s.code,
                    "language": s.language,
                    "tags": s.tags,
                }
                for s in snippets
            ]
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return len(snippets)
