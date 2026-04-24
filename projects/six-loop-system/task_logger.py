"""
任務記錄器 - 記錄六循環系統任務狀態
"""

import json
import os
from datetime import datetime

class TaskLogger:
    """任務記錄器"""
    
    def __init__(self):
        self.log_dir = 'logs/tasks'
        os.makedirs(self.log_dir, exist_ok=True)
        
    def log_task_status(self, tasks_data, phase):
        """記錄任務狀態"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{self.log_dir}/phase{phase}_{timestamp}.json'
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'phase': phase,
            'tasks': tasks_data,
            'summary': self._generate_summary(tasks_data)
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 任務狀態已記錄: {filename}")
        return filename
    
    def _generate_summary(self, tasks_data):
        """生成摘要"""
        total = len(tasks_data)
        completed = sum(1 for t in tasks_data if t.get('status') == 'completed')
        pending = sum(1 for t in tasks_data if t.get('status') == 'pending')
        in_progress = sum(1 for t in tasks_data if t.get('status') == 'in_progress')
        blocked = sum(1 for t in tasks_data if t.get('status') == 'blocked')
        
        return {
            'total_tasks': total,
            'completed': completed,
            'pending': pending,
            'in_progress': in_progress,
            'blocked': blocked,
            'progress_percent': round((completed / total * 100), 1) if total > 0 else 0
        }
    
    def log_system_event(self, event_type, details):
        """記錄系統事件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{self.log_dir}/event_{timestamp}.json'
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(event, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 事件已記錄: {event_type}")
        return filename
    
    def get_latest_status(self):
        """獲取最新狀態"""
        files = [f for f in os.listdir(self.log_dir) if f.startswith('phase')]
        if not files:
            return None
        
        latest = sorted(files)[-1]
        with open(f'{self.log_dir}/{latest}', 'r', encoding='utf-8') as f:
            return json.load(f)

def main():
    """測試任務記錄器"""
    logger = TaskLogger()
    
    # Sample tasks
    sample_tasks = [
        {"title": "Futu OpenD 連接", "status": "completed", "phase": 1},
        {"title": "數據流修復", "status": "completed", "phase": 1},
        {"title": "系統監控", "status": "completed", "phase": 2},
        {"title": "AMS 整合", "status": "in_progress", "phase": 2},
    ]
    
    logger.log_task_status(sample_tasks, phase=2)
    logger.log_system_event("phase2_progress", "Phase 2 任務管理進行中")
    
    print("\n任務記錄測試完成!")

if __name__ == '__main__':
    main()
