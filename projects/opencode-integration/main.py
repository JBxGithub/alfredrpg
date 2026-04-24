"""
OpenClaw Oh-My-Opencode 整合系統主入口

整合四個核心機制：
1. IntentGate - 意圖分類與智能路由
2. Hash-Anchored Edit - 哈希驗證編輯系統
3. Todo Enforcer - 任務強制執行機制
4. Plan 文件驅動 - 專案計劃管理
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# 添加模組路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.intentgate.engine import IntentGate, process_query
from modules.hash_anchored_edit.editor import HashAnchoredEditor
from modules.todo_enforcer.enforcer import TodoEnforcer
from modules.plan_driven.manager import PlanManager


class OpenClawIntegration:
    """
    OpenClaw 整合系統主類
    
    協調四個核心模組的工作
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化整合系統
        
        Args:
            config_path: 配置文件路徑
        """
        self.config_path = config_path or "config/integration.yaml"
        
        # 初始化各模組
        self.intent_gate = IntentGate()
        self.hash_editor = HashAnchoredEditor()
        self.todo_enforcer = TodoEnforcer()
        self.plan_manager = PlanManager()
        
        print("🚀 OpenClaw Integration System Initialized")
        print("   - IntentGate: Ready")
        print("   - Hash-Anchored Edit: Ready")
        print("   - Todo Enforcer: Ready")
        print("   - Plan Driven: Ready")
    
    def process_user_query(self, query: str) -> dict:
        """
        處理用戶查詢（完整流程）
        
        Args:
            query: 用戶輸入
        
        Returns:
            處理結果
        """
        # Step 1: IntentGate 分類和路由
        classification, routing = self.intent_gate.process(query)
        
        print(f"\n🎯 Intent Classification:")
        print(f"   Intent: {classification.intent.value}")
        print(f"   Category: {classification.category.value}")
        print(f"   Confidence: {classification.confidence:.2f}")
        print(f"   Target Agent: {routing.target_agent}")
        
        # Step 2: 創建任務（Todo Enforcer）
        task = self.todo_enforcer.create_task(
            title=f"Process: {query[:50]}...",
            description=query,
            priority="high" if classification.urgency == "critical" else "medium"
        )
        task.start()
        
        # Step 3: 返回處理結果
        result = {
            'query': query,
            'classification': {
                'intent': classification.intent.value,
                'category': classification.category.value,
                'confidence': classification.confidence,
                'urgency': classification.urgency,
                'complexity': classification.complexity,
            },
            'routing': {
                'target_agent': routing.target_agent,
                'fallback_agents': routing.fallback_agents,
                'routing_type': routing.routing_type,
            },
            'task_id': task.id,
        }
        
        return result
    
    def edit_file(self, file_path: str, line_number: int, 
                  expected_hash: str, new_content: str) -> dict:
        """
        編輯文件（Hash-Anchored）
        
        Args:
            file_path: 文件路徑
            line_number: 行號
            expected_hash: 期望的哈希
            new_content: 新內容
        
        Returns:
            編輯結果
        """
        result = self.hash_editor.edit_line(
            file_path, line_number, expected_hash, new_content
        )
        
        return {
            'success': result.success,
            'result': result.result.value,
            'message': result.message,
            'affected_lines': result.affected_lines,
            'new_hashes': result.new_hashes,
        }
    
    def create_plan(self, name: str, description: str = "", **kwargs) -> dict:
        """
        創建計劃
        
        Args:
            name: 計劃名稱
            description: 計劃描述
            **kwargs: 其他參數
        
        Returns:
            計劃信息
        """
        plan = self.plan_manager.create_plan(name, description, **kwargs)
        
        return {
            'plan_id': plan.plan_id,
            'name': plan.name,
            'status': plan.status.value,
            'file_path': str(self.plan_manager.plans_dir / f"{plan.plan_id}.md"),
        }
    
    def get_task_report(self) -> dict:
        """
        獲取任務報告
        
        Returns:
            任務統計
        """
        report = self.todo_enforcer.get_report()
        
        return {
            'total_tasks': report.total_tasks,
            'completed': report.completed,
            'in_progress': report.in_progress,
            'pending': report.pending,
            'blocked': report.blocked,
            'cancelled': report.cancelled,
            'progress_percent': report.progress_percent,
            'stagnant_tasks': report.stagnant_tasks,
            'overdue_tasks': report.overdue_tasks,
        }
    
    def get_system_status(self) -> dict:
        """
        獲取系統狀態
        
        Returns:
            系統狀態
        """
        plan_stats = self.plan_manager.get_plan_stats()
        task_report = self.get_task_report()
        
        return {
            'modules': {
                'intentgate': 'active',
                'hash_anchored_edit': 'active',
                'todo_enforcer': 'active',
                'plan_driven': 'active',
            },
            'plans': plan_stats,
            'tasks': task_report,
            'status': 'healthy',
        }


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='OpenClaw Oh-My-Opencode Integration System'
    )
    parser.add_argument(
        '--config', '-c',
        help='Configuration file path',
        default='config/integration.yaml'
    )
    parser.add_argument(
        '--command', '-cmd',
        help='Command to execute',
        choices=['status', 'query', 'edit', 'plan', 'report']
    )
    parser.add_argument(
        '--query', '-q',
        help='User query to process'
    )
    
    args = parser.parse_args()
    
    # 初始化系統
    integration = OpenClawIntegration(args.config)
    
    if args.command == 'status':
        status = integration.get_system_status()
        print("\n📊 System Status:")
        print(f"   Overall: {status['status']}")
        print(f"\n   Modules:")
        for module, state in status['modules'].items():
            print(f"      - {module}: {state}")
        print(f"\n   Plans: {status['plans']['total_plans']}")
        print(f"   Tasks: {status['tasks']['total_tasks']}")
    
    elif args.command == 'query' and args.query:
        result = integration.process_user_query(args.query)
        print("\n✅ Query processed successfully")
    
    elif args.command == 'report':
        report = integration.get_task_report()
        print("\n📋 Task Report:")
        print(f"   Total: {report['total_tasks']}")
        print(f"   Completed: {report['completed']}")
        print(f"   In Progress: {report['in_progress']}")
        print(f"   Progress: {report['progress_percent']:.1f}%")
    
    else:
        # 交互模式
        print("\n" + "="*50)
        print("OpenClaw Integration System")
        print("="*50)
        print("\nAvailable commands:")
        print("  status  - Show system status")
        print("  query   - Process user query")
        print("  plan    - Create new plan")
        print("  report  - Show task report")
        print("  exit    - Exit system")
        print()
        
        while True:
            try:
                cmd = input("> ").strip().lower()
                
                if cmd == 'exit':
                    print("Goodbye!")
                    break
                
                elif cmd == 'status':
                    status = integration.get_system_status()
                    print(f"\nStatus: {status['status']}")
                    print(f"Plans: {status['plans']['total_plans']}")
                    print(f"Tasks: {status['tasks']['total_tasks']}")
                
                elif cmd == 'report':
                    report = integration.get_task_report()
                    print(f"\nProgress: {report['progress_percent']:.1f}%")
                    print(f"Completed: {report['completed']}/{report['total_tasks']}")
                
                elif cmd.startswith('query '):
                    query = cmd[6:]
                    result = integration.process_user_query(query)
                    print(f"\nRouted to: {result['routing']['target_agent']}")
                
                elif cmd == '':
                    continue
                
                else:
                    print(f"Unknown command: {cmd}")
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == '__main__':
    main()
