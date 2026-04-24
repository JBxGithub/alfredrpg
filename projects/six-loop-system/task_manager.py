"""
六循環系統任務管理器
使用 Todo Enforcer 追蹤完善進度
"""

import sys
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/private skills/opencode-integration')

from modules.todo_enforcer.enforcer import TodoEnforcer, TaskStatus
from datetime import datetime, timedelta
import json
import os

class SixLoopTaskManager:
    """六循環系統任務管理器"""
    
    def __init__(self):
        self.enforcer = TodoEnforcer()
        self.tasks_file = 'tasks/six_loop_tasks.json'
        os.makedirs('tasks', exist_ok=True)
        self.load_tasks()
    
    def create_phase1_tasks(self):
        """創建 Phase 1 任務"""
        print("創建 Phase 1 任務...")
        
        tasks = [
            {
                'title': 'Node-RED Flow 管理',
                'description': '檢查 Node-RED 狀態，導出 Flows 備份',
                'status': 'completed',
            },
            {
                'title': 'Futu OpenD 連接',
                'description': '連接 Futu OpenD API，獲取 QQQ 數據',
                'status': 'completed',
            },
            {
                'title': '數據流修復',
                'description': '修復數據寫入問題，確保數據正確寫入數據庫',
                'status': 'completed',
            },
            {
                'title': '分析標的確認',
                'description': '確認使用 QQQ 作為 NQ 100 代理',
                'status': 'completed',
            },
        ]
        
        for task_data in tasks:
            task = self.enforcer.create_task(
                title=task_data['title'],
                description=task_data['description'],
                priority='high'
            )
            if task_data['status'] == 'completed':
                task.complete()
            print(f"  ✅ {task.title}")
    
    def create_phase2_tasks(self):
        """創建 Phase 2 任務"""
        print("\n創建 Phase 2 任務...")
        
        tasks = [
            {
                'title': '系統監控自動化',
                'description': '設置 Cron Job 自動監控系統健康狀態',
                'priority': 'high',
            },
            {
                'title': '異常告警通知',
                'description': '整合 WhatsApp 通知，異常時自動發送警報',
                'priority': 'high',
            },
            {
                'title': 'AMS 任務記錄',
                'description': '整合 AMS 記錄任務執行狀態',
                'priority': 'medium',
            },
        ]
        
        for task_data in tasks:
            task = self.enforcer.create_task(
                title=task_data['title'],
                description=task_data['description'],
                priority=task_data['priority']
            )
            print(f"  📝 {task.title}")
    
    def create_phase3_tasks(self):
        """創建 Phase 3 任務"""
        print("\n創建 Phase 3 任務...")
        
        tasks = [
            {
                'title': '端到端測試',
                'description': '測試完整交易流程，驗證所有組件協同運作',
                'priority': 'high',
            },
            {
                'title': '風險管理驗證',
                'description': '驗證風險管理機制有效，止損止盈正常運作',
                'priority': 'high',
            },
            {
                'title': '成就系統測試',
                'description': '測試每日收盤任務和成就徽章系統',
                'priority': 'medium',
            },
        ]
        
        for task_data in tasks:
            task = self.enforcer.create_task(
                title=task_data['title'],
                description=task_data['description'],
                priority=task_data['priority']
            )
            print(f"  📝 {task.title}")
    
    def create_phase4_tasks(self):
        """創建 Phase 4 任務"""
        print("\n創建 Phase 4 任務...")
        
        tasks = [
            {
                'title': '安全檢查',
                'description': '審查 API 密鑰配置，驗證風險限制設置',
                'priority': 'high',
            },
            {
                'title': '文檔完善',
                'description': '更新系統架構文檔，編寫操作手冊',
                'priority': 'medium',
            },
            {
                'title': '實盤部署準備',
                'description': '設置生產環境配置，測試系統恢復流程',
                'priority': 'high',
            },
        ]
        
        for task_data in tasks:
            task = self.enforcer.create_task(
                title=task_data['title'],
                description=task_data['description'],
                priority=task_data['priority']
            )
            print(f"  📝 {task.title}")
    
    def get_progress_report(self):
        """獲取進度報告"""
        report = self.enforcer.get_report()
        
        print("\n" + "=" * 60)
        print("六循環系統任務進度報告")
        print("=" * 60)
        print(f"總任務數: {report.total_tasks}")
        print(f"已完成: {report.completed} ({report.progress_percent:.1f}%)")
        print(f"進行中: {report.in_progress}")
        print(f"待辦: {report.pending}")
        print(f"阻塞: {report.blocked}")
        
        if report.stagnant_tasks:
            print(f"\n⚠️ 停滯任務: {len(report.stagnant_tasks)}")
        
        if report.overdue_tasks:
            print(f"\n⚠️ 超時任務: {len(report.overdue_tasks)}")
        
        print("=" * 60)
        
        return report
    
    def save_tasks(self):
        """保存任務到文件"""
        tasks_data = {
            'updated_at': datetime.now().isoformat(),
            'tasks': [task.to_dict() for task in self.enforcer.tasks.values()]
        }
        
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n任務已保存到: {self.tasks_file}")
    
    def load_tasks(self):
        """從文件加載任務"""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for task_data in data.get('tasks', []):
                    from modules.todo_enforcer.enforcer import Task
                    task = Task.from_dict(task_data)
                    self.enforcer.tasks[task.id] = task
                
                print(f"已加載 {len(self.enforcer.tasks)} 個任務")
            except Exception as e:
                print(f"加載任務失敗: {e}")
    
    def initialize_all_tasks(self):
        """初始化所有任務"""
        print("=" * 60)
        print("初始化六循環系統任務")
        print("=" * 60)
        
        self.create_phase1_tasks()
        self.create_phase2_tasks()
        self.create_phase3_tasks()
        self.create_phase4_tasks()
        
        self.save_tasks()
        self.get_progress_report()

def main():
    """主函數"""
    manager = SixLoopTaskManager()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'init':
            manager.initialize_all_tasks()
        elif sys.argv[1] == 'report':
            manager.get_progress_report()
        else:
            print("Usage: python task_manager.py [init|report]")
    else:
        manager.get_progress_report()

if __name__ == '__main__':
    main()
