"""
Windows Scheduler Integration
Manages Windows Task Scheduler for automated nudges and tasks
"""

import subprocess
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class WindowsScheduler:
    """
    Windows Task Scheduler 整合
    - 創建定期提醒任務
    - 管理任務生命周期
    - 替代 Linux cron
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化 Windows 排程器"""
        self.config = config
        self.task_prefix = config['windows']['task_scheduler']['task_prefix']
        self.run_as = config['windows']['task_scheduler']['run_as']
    
    def _run_schtasks(self, args: list) -> tuple:
        """執行 schtasks 命令"""
        cmd = ['schtasks.exe'] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def create_nudge_task(self, time: str = "09:00", 
                          frequency: str = "daily") -> bool:
        """
        創建提醒任務
        
        Args:
            time: 執行時間 (HH:MM)
            frequency: 頻率 (daily, weekly, hourly)
        
        Returns:
            是否成功
        """
        task_name = f"{self.task_prefix}Nudge"
        
        # 構建命令
        workspace = Path(self.config['paths']['workspace'])
        script_path = workspace / "scripts" / "nudge_task.ps1"
        
        # 確保腳本存在
        self._ensure_nudge_script(script_path)
        
        # 刪除舊任務
        self.delete_task(task_name)
        
        # 創建新任務
        hour, minute = time.split(':')
        
        if frequency == "daily":
            schedule = f"/SC DAILY /ST {time}"
        elif frequency == "weekly":
            schedule = f"/SC WEEKLY /D MON /ST {time}"
        elif frequency == "hourly":
            schedule = f"/SC HOURLY /MO 1"
        else:
            schedule = f"/SC DAILY /ST {time}"
        
        cmd_args = [
            '/Create',
            '/TN', task_name,
            '/TR', f'powershell.exe -ExecutionPolicy Bypass -File "{script_path}"',
            '/RU', self.run_as,
            schedule,
            '/F'  # 強制創建
        ]
        
        success, stdout, stderr = self._run_schtasks(cmd_args)
        
        if not success:
            print(f"Failed to create task: {stderr}")
        
        return success
    
    def _ensure_nudge_script(self, script_path: Path):
        """確保提醒腳本存在"""
        script_path.parent.mkdir(parents=True, exist_ok=True)
        
        script_content = '''# Hermes Nudge Task Script
# Auto-generated for Windows Task Scheduler

param(
    [string]$ConfigPath = "$env:USERPROFILE\\openclaw_workspace\\config\\hermes_config.yaml"
)

# 加載配置
$config = Get-Content $ConfigPath | ConvertFrom-Yaml

# 執行提醒檢查
python -c @"
import sys
sys.path.insert(0, '$($config.paths.workspace)\\projects\\hermes-memory-system\\src')
from core.learning_engine import LearningEngine
from core.memory_manager import MemoryManager
from core.session_store import SessionStore
from core.skill_manager import SkillManager
import yaml

with open('$ConfigPath', 'r') as f:
    config = yaml.safe_load(f)

memory = MemoryManager('$ConfigPath')
sessions = SessionStore(config['paths']['database_file'])
skills = SkillManager(config['paths']['skills_dir'])
engine = LearningEngine(config, memory, sessions, skills)

nudge = engine.generate_nudge()
if nudge:
    print(f\"[{nudge['type']}] {nudge['title']}\")
    print(nudge['content'])
    print(f\"Action: {nudge['action']}\")
else:
    print("No nudge needed at this time.")
"@

# 發送 Windows 通知 (可選)
if (Get-Command "burnttoast" -ErrorAction SilentlyContinue) {
    New-BurntToastNotification -Text "Hermes Reminder", "Check your memory system"
}
'''
        
        script_path.write_text(script_content, encoding='utf-8')
    
    def delete_task(self, task_name: str) -> bool:
        """刪除任務"""
        success, _, _ = self._run_schtasks(['/Delete', '/TN', task_name, '/F'])
        return success
    
    def list_tasks(self) -> list:
        """列出所有 Hermes 任務"""
        success, stdout, _ = self._run_schtasks([
            '/Query', '/FO', 'CSV', '/NH'
        ])
        
        if not success:
            return []
        
        tasks = []
        for line in stdout.strip().split('\n'):
            if self.task_prefix in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    tasks.append({
                        'name': parts[0].strip('"'),
                        'next_run': parts[1].strip('"') if len(parts) > 1 else 'N/A',
                        'status': parts[2].strip('"') if len(parts) > 2 else 'Unknown'
                    })
        
        return tasks
    
    def run_task_now(self, task_name: str) -> bool:
        """立即執行任務"""
        success, _, _ = self._run_schtasks(['/Run', '/TN', task_name])
        return success
    
    def enable_task(self, task_name: str) -> bool:
        """啟用任務"""
        success, _, _ = self._run_schtasks(['/Change', '/TN', task_name, '/ENABLE'])
        return success
    
    def disable_task(self, task_name: str) -> bool:
        """禁用任務"""
        success, _, _ = self._run_schtasks(['/Change', '/TN', task_name, '/DISABLE'])
        return success
    
    def get_task_info(self, task_name: str) -> Optional[Dict[str, Any]]:
        """獲取任務詳細信息"""
        success, stdout, _ = self._run_schtasks([
            '/Query', '/TN', task_name, '/FO', 'LIST', '/V'
        ])
        
        if not success:
            return None
        
        info = {}
        for line in stdout.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        
        return info
