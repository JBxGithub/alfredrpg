"""
AMS (Alfred Memory System) 整合
將六循環系統任務狀態同步到 AMS
"""

import sys
import os

# Add AMS to path
sys.path.insert(0, os.path.expanduser('~/.openclaw/skills/alfred-memory-system'))

from ams_simple import AMS
from datetime import datetime
import json

class SixLoopAMSIntegration:
    """六循環系統 AMS 整合器"""
    
    def __init__(self):
        self.ams = AMS()
        self.ams.initialize()
        self.project_id = "six-loop-system"
        
    def sync_task_status(self, tasks_data):
        """同步任務狀態到 AMS"""
        print("同步任務狀態到 AMS...")
        
        # Create memory entry
        memory_entry = {
            "type": "project_status",
            "project": "Six-Loop System",
            "timestamp": datetime.now().isoformat(),
            "tasks": tasks_data,
            "summary": self._generate_summary(tasks_data)
        }
        
        # Store in AMS
        self.ams.store_memory(
            content=json.dumps(memory_entry, ensure_ascii=False),
            category="project",
            tags=["six-loop", "trading", "status"],
            importance=8
        )
        
        print("✅ 任務狀態已同步到 AMS")
        
    def _generate_summary(self, tasks_data):
        """生成摘要"""
        total = len(tasks_data)
        completed = sum(1 for t in tasks_data if t.get('status') == 'completed')
        pending = sum(1 for t in tasks_data if t.get('status') == 'pending')
        in_progress = sum(1 for t in tasks_data if t.get('status') == 'in_progress')
        
        return {
            "total_tasks": total,
            "completed": completed,
            "pending": pending,
            "in_progress": in_progress,
            "progress_percent": (completed / total * 100) if total > 0 else 0
        }
    
    def log_system_event(self, event_type, details):
        """記錄系統事件"""
        event = {
            "type": "system_event",
            "project": "Six-Loop System",
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
        self.ams.store_memory(
            content=json.dumps(event, ensure_ascii=False),
            category="system",
            tags=["six-loop", "event", event_type],
            importance=7
        )
        
        print(f"✅ 事件已記錄: {event_type}")

def main():
    """測試 AMS 整合"""
    integration = SixLoopAMSIntegration()
    
    # Sample tasks data
    sample_tasks = [
        {"title": "Futu OpenD 連接", "status": "completed"},
        {"title": "數據流修復", "status": "completed"},
        {"title": "系統監控", "status": "in_progress"},
    ]
    
    integration.sync_task_status(sample_tasks)
    integration.log_system_event("test", "AMS 整合測試")
    
    print("\nAMS 整合測試完成!")

if __name__ == '__main__':
    main()
