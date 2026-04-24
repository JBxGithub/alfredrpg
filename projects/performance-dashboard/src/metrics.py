import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TaskMetrics:
    task_id: str
    task_type: str
    completion_time: float
    tool_count: int
    success: bool
    retry_count: int
    timestamp: datetime


@dataclass
class SessionMetrics:
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    task_count: int
    context_usage: float
    success_rate: float


class MetricsCalculator:
    def __init__(self, db_path: str = "data/performance.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    task_type TEXT NOT NULL,
                    completion_time REAL,
                    tool_count INTEGER DEFAULT 0,
                    success INTEGER DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    task_count INTEGER DEFAULT 0,
                    context_usage REAL DEFAULT 0.0,
                    success_rate REAL DEFAULT 0.0
                );

                CREATE TABLE IF NOT EXISTS tool_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
                );

                CREATE TABLE IF NOT EXISTS skill_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    skill_category TEXT,
                    completion_level REAL DEFAULT 0.0,
                    last_practiced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at);
                CREATE INDEX IF NOT EXISTS idx_tool_usage ON tool_usage(tool_name);
                CREATE INDEX IF NOT EXISTS idx_sessions_time ON sessions(start_time);
            """)

    def calculate_efficiency_score(self, days: int = 7) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    AVG(completion_time) as avg_time,
                    SUM(tool_count) as total_tools,
                    COUNT(*) as total_tasks,
                    SUM(success) as successful_tasks
                FROM tasks
                WHERE created_at >= datetime('now', ?)
            """, (f'-{days} days',))
            row = cursor.fetchone()

            avg_time = row['avg_time'] or 0
            total_tasks = row['total_tasks'] or 0
            successful = row['successful_tasks'] or 0

            efficiency = 0
            if avg_time > 0 and total_tasks > 0:
                time_score = max(0, 100 - (avg_time / 60 * 10))
                success_score = (successful / total_tasks * 100) if total_tasks > 0 else 0
                efficiency = (time_score * 0.4 + success_score * 0.6)

            return {
                "avg_completion_time_seconds": round(avg_time, 2),
                "total_tasks": total_tasks,
                "successful_tasks": successful,
                "success_rate": round(successful / total_tasks * 100, 1) if total_tasks > 0 else 0,
                "efficiency_score": round(efficiency, 1)
            }

    def calculate_accuracy_metrics(self, days: int = 7) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    SUM(retry_count) as total_retries,
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN retry_count > 0 THEN 1 ELSE 0 END) as tasks_with_retries
                FROM tasks
                WHERE created_at >= datetime('now', ?)
            """, (f'-{days} days',))
            row = cursor.fetchone()

            total = row['total_tasks'] or 0
            retries = row['total_retries'] or 0
            retry_tasks = row['tasks_with_retries'] or 0

            return {
                "error_rate": round((retry_tasks / total * 100), 1) if total > 0 else 0,
                "total_retries": retries,
                "retry_tasks": retry_tasks,
                "avg_retries_per_task": round(retries / total, 2) if total > 0 else 0
            }

    def calculate_tool_usage_stats(self, days: int = 7) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    tool_name,
                    SUM(usage_count) as total_usage
                FROM tool_usage
                WHERE timestamp >= datetime('now', ?)
                GROUP BY tool_name
                ORDER BY total_usage DESC
            """, (f'-{days} days',))

            results = []
            total_usage = 0
            for row in cursor.fetchall():
                total_usage += row['total_usage']

            if total_usage > 0:
                conn.execute("""
                    SELECT tool_name, SUM(usage_count) as total_usage
                    FROM tool_usage
                    WHERE timestamp >= datetime('now', ?)
                    GROUP BY tool_name
                    ORDER BY total_usage DESC
                """, (f'-{days} days',))
                for row in conn.execute("""
                    SELECT tool_name, SUM(usage_count) as total_usage
                    FROM tool_usage
                    WHERE timestamp >= datetime('now', ?)
                    GROUP BY tool_name
                    ORDER BY total_usage DESC
                """, (f'-{days} days',)):
                    results.append({
                        "tool_name": row['tool_name'],
                        "usage_count": row['total_usage'],
                        "percentage": round(row['total_usage'] / total_usage * 100, 1)
                    })

            return results

    def calculate_context_usage(self, days: int = 7) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    AVG(context_usage) as avg_context,
                    MAX(context_usage) as max_context,
                    MIN(context_usage) as min_context
                FROM sessions
                WHERE start_time >= datetime('now', ?)
            """, (f'-{days} days',))
            row = cursor.fetchone()

            return {
                "avg_context_usage": round(row['avg_context'] or 0, 1),
                "max_context_usage": round(row['max_context'] or 0, 1),
                "min_context_usage": round(row['min_context'] or 0, 1),
                "context_efficiency": round(100 - (row['avg_context'] or 0), 1)
            }

    def calculate_skill_progress(self) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT skill_name, skill_category, completion_level, last_practiced
                FROM skill_progress
                ORDER BY completion_level DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_trend_data(self, metric: str, days: int = 7) -> List[Dict]:
        with self._get_connection() as conn:
            if metric == "tasks":
                cursor = conn.execute("""
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM tasks
                    WHERE created_at >= datetime('now', ?)
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """, (f'-{days} days',))
            elif metric == "success_rate":
                cursor = conn.execute("""
                    SELECT DATE(created_at) as date,
                           ROUND(SUM(success) * 100.0 / COUNT(*), 1) as rate
                    FROM tasks
                    WHERE created_at >= datetime('now', ?)
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """, (f'-{days} days',))
            elif metric == "completion_time":
                cursor = conn.execute("""
                    SELECT DATE(created_at) as date,
                           ROUND(AVG(completion_time), 1) as avg_time
                    FROM tasks
                    WHERE created_at >= datetime('now', ?)
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """, (f'-{days} days',))
            else:
                return []

            return [{"date": row[0], metric: row[1]} for row in cursor.fetchall()]

    def get_task_type_distribution(self, days: int = 7) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT task_type, COUNT(*) as count
                FROM tasks
                WHERE created_at >= datetime('now', ?)
                GROUP BY task_type
                ORDER BY count DESC
            """, (f'-{days} days',))
            return [{"task_type": row[0], "count": row[1]} for row in cursor.fetchall()]

    def calculate_session_summary(self, days: int = 7) -> Dict:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_sessions,
                    SUM(task_count) as total_tasks,
                    AVG(success_rate) as avg_success_rate,
                    AVG(context_usage) as avg_context
                FROM sessions
                WHERE start_time >= datetime('now', ?)
            """, (f'-{days} days',))
            row = cursor.fetchone()

            return {
                "total_sessions": row['total_sessions'] or 0,
                "total_tasks": row['total_tasks'] or 0,
                "avg_success_rate": round(row['avg_success_rate'] or 0, 1),
                "avg_context_usage": round(row['avg_context'] or 0, 1)
            }
