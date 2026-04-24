import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import uuid


class DataCollector:
    def __init__(self, db_path: str = "data/performance.db"):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def record_task(self, task_type: str, completion_time: float,
                    tool_count: int = 0, success: bool = True,
                    retry_count: int = 0, tools_used: List[str] = None) -> str:
        task_id = str(uuid.uuid4())[:8]

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO tasks (task_id, task_type, completion_time, tool_count, success, retry_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (task_id, task_type, completion_time, tool_count, int(success), retry_count))

            if tools_used:
                for tool_name in tools_used:
                    conn.execute("""
                        INSERT INTO tool_usage (task_id, tool_name)
                        VALUES (?, ?)
                    """, (task_id, tool_name))

        return task_id

    def record_session(self, session_id: str, task_count: int = 0,
                       context_usage: float = 0.0, success_rate: float = 0.0) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO sessions (session_id, start_time, task_count, context_usage, success_rate)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, datetime.now(), task_count, context_usage, success_rate))
            return True
        except sqlite3.IntegrityError:
            return False

    def end_session(self, session_id: str, task_count: int,
                    context_usage: float, success_rate: float) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                UPDATE sessions
                SET end_time = ?, task_count = ?, context_usage = ?, success_rate = ?
                WHERE session_id = ?
            """, (datetime.now(), task_count, context_usage, success_rate, session_id))
            return cursor.rowcount > 0

    def record_skill_progress(self, skill_name: str, completion_level: float,
                               skill_category: str = None) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO skill_progress (skill_name, skill_category, completion_level)
                VALUES (?, ?, ?)
                ON CONFLICT(skill_name) DO UPDATE SET
                    completion_level = excluded.completion_level,
                    last_practiced = CURRENT_TIMESTAMP
            """, (skill_name, skill_category, completion_level))
            return cursor.rowcount > 0

    def update_task_tools(self, task_id: str, tools_used: List[str]) -> bool:
        with self._get_connection() as conn:
            for tool in tools_used:
                conn.execute("""
                    INSERT INTO tool_usage (task_id, tool_name, usage_count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(task_id, tool_name) DO UPDATE SET
                        usage_count = tool_usage.usage_count + 1
                """, (task_id, tool))
        return True

    def import_from_log_file(self, log_file: Path) -> int:
        if not log_file.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")

        imported_count = 0
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get('type') == 'task':
                        self.record_task(
                            task_type=entry.get('task_type', 'unknown'),
                            completion_time=entry.get('completion_time', 0),
                            tool_count=entry.get('tool_count', 0),
                            success=entry.get('success', True),
                            retry_count=entry.get('retry_count', 0),
                            tools_used=entry.get('tools', [])
                        )
                        imported_count += 1
                    elif entry.get('type') == 'session':
                        self.record_session(
                            session_id=entry.get('session_id', ''),
                            task_count=entry.get('task_count', 0),
                            context_usage=entry.get('context_usage', 0),
                            success_rate=entry.get('success_rate', 0)
                        )
                except json.JSONDecodeError:
                    continue

        return imported_count

    def get_recent_tasks(self, limit: int = 10) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM tasks
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as total_tasks,
                    SUM(success) as successful,
                    AVG(completion_time) as avg_time,
                    SUM(tool_count) as total_tools
                FROM tasks
                WHERE created_at >= datetime('now', ?)
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (f'-{days} days',))
            return [dict(row) for row in cursor.fetchall()]

    def generate_sample_data(self):
        import random
        from datetime import timedelta

        task_types = ['code_review', 'bug_fix', 'feature', 'refactor', 'documentation', 'testing']
        tools = ['read', 'write', 'edit', 'bash', 'grep', 'glob', 'web_search', 'web_fetch']

        base_time = datetime.now() - timedelta(days=7)

        for day in range(7):
            for _ in range(random.randint(5, 15)):
                session_id = f"session_{day}_{random.randint(1000, 9999)}"
                self.record_session(
                    session_id=session_id,
                    task_count=random.randint(1, 5),
                    context_usage=random.uniform(30, 85),
                    success_rate=random.uniform(70, 100)
                )

                task_type = random.choice(task_types)
                task_tools = random.sample(tools, k=random.randint(1, 4))

                self.record_task(
                    task_type=task_type,
                    completion_time=random.uniform(30, 300),
                    tool_count=len(task_tools),
                    success=random.random() > 0.15,
                    retry_count=random.randint(0, 2),
                    tools_used=task_tools
                )

                for skill in random.sample(['python', 'git', 'testing', 'debugging', 'refactoring'],
                                           k=random.randint(1, 3)):
                    self.record_skill_progress(
                        skill_name=skill,
                        completion_level=random.uniform(50, 95),
                        skill_category='technical'
                    )

        return "Sample data generated successfully"
