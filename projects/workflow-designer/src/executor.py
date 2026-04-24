"""
Workflow Executor - 兼容版
用於 alfred-cli 直接導入
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class WorkflowExecutor:
    """工作流執行器"""
    
    def __init__(self, workflows_dir: str = None):
        if workflows_dir is None:
            workflows_dir = Path(__file__).parent.parent / "workflows"
        self.workflows_dir = Path(workflows_dir)
    
    def list_workflows(self) -> List[str]:
        """列出所有工作流"""
        workflows = []
        if self.workflows_dir.exists():
            for wf_file in self.workflows_dir.glob("*.yaml"):
                workflows.append(wf_file.stem)
        return workflows
    
    def load_workflow(self, name: str) -> Dict[str, Any]:
        """加載工作流"""
        wf_file = self.workflows_dir / f"{name}.yaml"
        if not wf_file.exists():
            return None
        
        with open(wf_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def execute(self, name: str) -> Dict[str, Any]:
        """執行工作流"""
        workflow = self.load_workflow(name)
        if not workflow:
            return {'success': False, 'error': f'Workflow "{name}" not found'}
        
        print(f"🚀 執行工作流: {workflow.get('name', name)}")
        print(f"📋 描述: {workflow.get('description', 'N/A')}")
        print()
        
        steps = workflow.get('steps', [])
        results = []
        
        for i, step in enumerate(steps, 1):
            step_name = step.get('name', f'Step {i}')
            action = step.get('action', 'unknown')
            
            print(f"  Step {i}: {step_name} ({action})")
            
            # 模擬執行
            result = self._execute_step(step)
            results.append(result)
            
            if result['success']:
                print(f"    ✅ 完成")
            else:
                print(f"    ❌ 失敗: {result.get('error', 'Unknown error')}")
                break
        
        return {
            'success': all(r['success'] for r in results),
            'workflow': name,
            'steps_completed': len([r for r in results if r['success']]),
            'total_steps': len(steps)
        }
    
    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """執行單個步驟"""
        action = step.get('action', '')
        
        # 模擬不同動作
        if action == 'check_status':
            return {'success': True, 'output': 'Status checked'}
        elif action == 'send_notification':
            return {'success': True, 'output': 'Notification sent'}
        elif action == 'run_command':
            return {'success': True, 'output': 'Command executed'}
        elif action == 'collect_metrics':
            return {'success': True, 'output': 'Metrics collected'}
        else:
            return {'success': True, 'output': f'Action {action} completed'}
