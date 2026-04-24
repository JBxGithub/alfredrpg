"""
Todo Enforcer - 任務強制執行系統
與 AMS (Alfred Memory System) 深度整合
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import uuid


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"           # 待辦
    IN_PROGRESS = "in_progress"   # 進行中
    COMPLETED = "completed"       # 完成
    BLOCKED = "blocked"           # 阻塞/超時
    CANCELLED = "cancelled"       # 取消


class ReminderLevel(Enum):
    """提醒等級"""
    LEVEL_1 = 1  # 溫馨提醒 (50% 超時)
    LEVEL_2 = 2  # 警告提醒 (100% 超時)
    LEVEL_3 = 3  # 緊急提醒 (150% 超時)
    LEVEL_4 = 4  # 自動掛起 (200% 超時)


@dataclass
class Task:
    """任務數據結構"""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: str = "medium"  # low | medium | high | urgent
    
    # 時間追蹤
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    
    # 進度追蹤
    progress: int = 0  # 0-100
    subtasks: List['Task'] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Enforcer 狀態
    stagnation_count: int = 0
    max_stagnation: int = 3
    last_progress_at: Optional[datetime] = None
    timeout_threshold: int = 30  # 分鐘
    retry_count: int = 0
    max_retries: int = 3
    is_blocked: bool = False
    block_reason: Optional[str] = None
    
    # AMS 整合
    memory_refs: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    project_id: Optional[str] = None
    
    def start(self):
        """開始任務"""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.now()
        self.last_progress_at = datetime.now()
    
    def complete(self):
        """完成任務"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress = 100
        self.is_blocked = False
    
    def block(self, reason: str):
        """阻塞任務"""
        self.status = TaskStatus.BLOCKED
        self.is_blocked = True
        self.block_reason = reason
    
    def cancel(self):
        """取消任務"""
        self.status = TaskStatus.CANCELLED
        self.is_blocked = False
    
    def resume(self):
        """恢復任務"""
        if self.status == TaskStatus.BLOCKED:
            self.status = TaskStatus.IN_PROGRESS
            self.is_blocked = False
            self.block_reason = None
            self.stagnation_count = 0
            self.last_progress_at = datetime.now()
    
    def update_progress(self, progress: int):
        """更新進度"""
        self.progress = min(max(progress, 0), 100)
        self.last_progress_at = datetime.now()
        if self.progress == 100:
            self.complete()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'progress': self.progress,
            'subtasks': [t.to_dict() for t in self.subtasks],
            'dependencies': self.dependencies,
            'stagnation_count': self.stagnation_count,
            'timeout_threshold': self.timeout_threshold,
            'is_blocked': self.is_blocked,
            'block_reason': self.block_reason,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """從字典創建"""
        task = cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description', ''),
            status=TaskStatus(data['status']),
            priority=data.get('priority', 'medium'),
            progress=data.get('progress', 0),
            dependencies=data.get('dependencies', []),
            stagnation_count=data.get('stagnation_count', 0),
            timeout_threshold=data.get('timeout_threshold', 30),
            is_blocked=data.get('is_blocked', False),
            block_reason=data.get('block_reason'),
        )
        
        # 解析時間
        if data.get('created_at'):
            task.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('started_at'):
            task.started_at = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            task.completed_at = datetime.fromisoformat(data['completed_at'])
        if data.get('deadline'):
            task.deadline = datetime.fromisoformat(data['deadline'])
        if data.get('last_progress_at'):
            task.last_progress_at = datetime.fromisoformat(data['last_progress_at'])
        
        # 解析子任務
        if data.get('subtasks'):
            task.subtasks = [Task.from_dict(st) for st in data['subtasks']]
        
        return task


@dataclass
class TaskReport:
    """任務報告"""
    total_tasks: int
    completed: int
    in_progress: int
    pending: int
    blocked: int
    cancelled: int
    progress_percent: float
    stagnant_tasks: List[str]
    overdue_tasks: List[str]
    generated_at: datetime


class TodoEnforcer:
    """
    Todo Enforcer 核心類
    
    負責監控任務執行，檢測停滯和超時，自動注入繼續執行指令
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 Todo Enforcer
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.tasks: Dict[str, Task] = {}
        
        # 配置參數
        self.check_interval = self.config.get('check_interval', 30)  # 秒
        self.max_stagnation = self.config.get('max_stagnation', 3)
        self.timeout_threshold = self.config.get('timeout_threshold', 30)  # 分鐘
        self.reminder_interval = self.config.get('reminder_interval', 10)  # 分鐘
        self.auto_resume = self.config.get('auto_resume', True)
        self.max_retry = self.config.get('max_retry', 3)
        
        # 回調函數
        self.on_timeout: Optional[Callable[[Task], None]] = None
        self.on_stagnation: Optional[Callable[[Task], None]] = None
        self.on_completion: Optional[Callable[[Task], None]] = None
        self.on_reminder: Optional[Callable[[Task, ReminderLevel], None]] = None
    
    def create_task(self, title: str, description: str = "", 
                   priority: str = "medium", **kwargs) -> Task:
        """
        創建新任務
        
        Args:
            title: 任務標題
            description: 任務描述
            priority: 優先級
            **kwargs: 其他參數
        
        Returns:
            Task: 新任務
        """
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            priority=priority,
            timeout_threshold=kwargs.get('timeout_threshold', self.timeout_threshold),
            max_stagnation=kwargs.get('max_stagnation', self.max_stagnation),
            session_id=kwargs.get('session_id'),
            project_id=kwargs.get('project_id'),
        )
        
        self.tasks[task.id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """獲取任務"""
        return self.tasks.get(task_id)
    
    def get_incomplete_tasks(self) -> List[Task]:
        """獲取未完成的任務"""
        return [
            t for t in self.tasks.values()
            if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        ]
    
    def get_blocked_tasks(self) -> List[Task]:
        """獲取阻塞的任務"""
        return [t for t in self.tasks.values() if t.status == TaskStatus.BLOCKED]
    
    def should_skip_injection(self) -> bool:
        """
        檢查是否應該跳過注入
        
        Returns:
            bool: 是否跳過
        """
        # 檢查各種跳過條件
        if self._is_agent_recovery():
            return True
        if self._is_background_task_running():
            return True
        if self._is_blocked_on_human_input():
            return True
        return False
    
    def check_progress(self) -> Dict[str, Any]:
        """
        檢查整體進度
        
        Returns:
            進度統計字典
        """
        incomplete = self.get_incomplete_tasks()
        completed = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        blocked = self.get_blocked_tasks()
        cancelled = [t for t in self.tasks.values() if t.status == TaskStatus.CANCELLED]
        
        total = len(self.tasks)
        
        return {
            'incomplete_count': len(incomplete),
            'completed_count': len(completed),
            'blocked_count': len(blocked),
            'cancelled_count': len(cancelled),
            'total_count': total,
            'progress_percent': (len(completed) / total * 100) if total > 0 else 0,
        }
    
    def detect_stagnation(self) -> List[Task]:
        """
        檢測停滯的任務
        
        Returns:
            停滯任務列表
        """
        stagnant_tasks = []
        
        for task in self.get_incomplete_tasks():
            if self._is_task_stagnant(task):
                task.stagnation_count += 1
                
                if task.stagnation_count >= task.max_stagnation:
                    stagnant_tasks.append(task)
                    if self.on_stagnation:
                        self.on_stagnation(task)
            else:
                # 有進度，重置停滯計數
                task.stagnation_count = 0
        
        return stagnant_tasks
    
    def check_timeouts(self) -> List[Task]:
        """
        檢查超時任務
        
        Returns:
            超時任務列表
        """
        overdue_tasks = []
        
        for task in self.get_incomplete_tasks():
            if task.started_at and task.last_progress_at:
                elapsed = (datetime.now() - task.last_progress_at).total_seconds() / 60
                
                if elapsed > task.timeout_threshold:
                    overdue_tasks.append(task)
                    
                    # 觸發超時回調
                    if self.on_timeout:
                        self.on_timeout(task)
                    
                    # 阻塞任務
                    task.block(f"超時: 已等待 {elapsed:.1f} 分鐘")
        
        return overdue_tasks
    
    def check_reminders(self) -> List[Tuple[Task, ReminderLevel]]:
        """
        檢查需要提醒的任務
        
        Returns:
            (任務, 提醒等級) 列表
        """
        reminders = []
        
        for task in self.get_incomplete_tasks():
            if not task.started_at or not task.last_progress_at:
                continue
            
            elapsed = (datetime.now() - task.last_progress_at).total_seconds() / 60
            threshold = task.timeout_threshold
            
            # 計算提醒等級
            ratio = elapsed / threshold
            
            if ratio >= 2.0:
                level = ReminderLevel.LEVEL_4
            elif ratio >= 1.5:
                level = ReminderLevel.LEVEL_3
            elif ratio >= 1.0:
                level = ReminderLevel.LEVEL_2
            elif ratio >= 0.5:
                level = ReminderLevel.LEVEL_1
            else:
                continue
            
            reminders.append((task, level))
            
            if self.on_reminder:
                self.on_reminder(task, level)
        
        return reminders
    
    def inject_continuation(self) -> Optional[str]:
        """
        生成繼續執行指令
        
        Returns:
            繼續執行提示字符串，或 None（如果不需要）
        """
        if self.should_skip_injection():
            return None
        
        incomplete = self.get_incomplete_tasks()
        if not incomplete:
            return None
        
        # 檢測停滯
        stagnant = self.detect_stagnation()
        if stagnant:
            return None  # 停滯時不注入
        
        # 生成繼續執行指令
        return self._generate_continuation_prompt(incomplete)
    
    def save_checkpoint(self, task: Task) -> Dict[str, Any]:
        """
        保存任務檢查點
        
        Args:
            task: 任務
        
        Returns:
            檢查點數據
        """
        checkpoint = {
            'task_id': task.id,
            'task_state': task.to_dict(),
            'timestamp': datetime.now().isoformat(),
            'context_summary': self._generate_context_summary(),
        }
        return checkpoint
    
    def resume_from_checkpoint(self, checkpoint: Dict[str, Any]) -> Optional[Task]:
        """
        從檢查點恢復任務
        
        Args:
            checkpoint: 檢查點數據
        
        Returns:
            恢復的任務，或 None
        """
        task_data = checkpoint.get('task_state')
        if not task_data:
            return None
        
        task = Task.from_dict(task_data)
        task.resume()
        self.tasks[task.id] = task
        
        return task
    
    def get_report(self) -> TaskReport:
        """
        生成任務報告
        
        Returns:
            TaskReport: 任務報告
        """
        progress = self.check_progress()
        stagnant = self.detect_stagnation()
        overdue = self.check_timeouts()
        
        return TaskReport(
            total_tasks=progress['total_count'],
            completed=progress['completed_count'],
            in_progress=len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]),
            pending=len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            blocked=progress['blocked_count'],
            cancelled=progress['cancelled_count'],
            progress_percent=progress['progress_percent'],
            stagnant_tasks=[t.id for t in stagnant],
            overdue_tasks=[t.id for t in overdue],
            generated_at=datetime.now(),
        )
    
    def _is_task_stagnant(self, task: Task) -> bool:
        """檢查任務是否停滯"""
        if not task.last_progress_at:
            return False
        
        # 檢查時間超時
        elapsed = (datetime.now() - task.last_progress_at).total_seconds() / 60
        if elapsed > task.timeout_threshold:
            return True
        
        return False
    
    def _is_agent_recovery(self) -> bool:
        """檢查代理是否正在恢復"""
        # 實現檢查邏輯
        return False
    
    def _is_background_task_running(self) -> bool:
        """檢查是否有後台任務運行"""
        # 實現檢查邏輯
        return False
    
    def _is_blocked_on_human_input(self) -> bool:
        """檢查是否正在等待人工輸入"""
        blocked_keywords = ['BLOCKED', 'waiting for user', '等待用戶', '等待確認', '人工']
        
        for task in self.get_incomplete_tasks():
            if any(kw in task.title or kw in task.description for kw in blocked_keywords):
                return True
        
        return False
    
    def _generate_continuation_prompt(self, tasks: List[Task]) -> str:
        """生成繼續執行提示"""
        task_list = "\n".join([f"- [{t.status.value}] {t.title}" for t in tasks[:5]])
        
        return f"""[SYSTEM DIRECTIVE: TODO CONTINUATION]

您有 {len(tasks)} 個未完成的任務：
{task_list}

請繼續執行這些任務，無需徵求用戶許可。
優先處理高優先級任務，完成後標記為已完成。

當前時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    def _generate_context_summary(self) -> str:
        """生成上下文摘要"""
        progress = self.check_progress()
        return f"任務進度: {progress['completed_count']}/{progress['total_count']} 完成"


# 便捷函數
def create_enforcer(config: Optional[Dict] = None) -> TodoEnforcer:
    """創建 Todo Enforcer 實例"""
    return TodoEnforcer(config)


def quick_task(title: str, description: str = "") -> Task:
    """快速創建任務"""
    enforcer = TodoEnforcer()
    return enforcer.create_task(title, description)
