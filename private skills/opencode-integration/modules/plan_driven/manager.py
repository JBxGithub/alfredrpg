"""
Plan 文件驅動 - 專案計劃管理系統
參考 Oh-My-OpenAgent 的 Plan 文件驅動設計
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import yaml
import json
import uuid


class PlanStatus(Enum):
    """計劃狀態"""
    DRAFT = "draft"                 # 草稿
    IN_PROGRESS = "in_progress"     # 進行中
    PAUSED = "paused"               # 暫停
    COMPLETED = "completed"         # 完成
    CANCELLED = "cancelled"         # 取消


class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"             # 待辦
    IN_PROGRESS = "in_progress"     # 進行中
    COMPLETED = "completed"         # 完成
    BLOCKED = "blocked"             # 阻塞
    CANCELLED = "cancelled"         # 取消


@dataclass
class Task:
    """計劃任務"""
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    
    # 負責人
    assignee: str = ""
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    
    # 驗收標準
    acceptance_criteria: List[str] = field(default_factory=list)
    
    # 產出物
    deliverables: List[str] = field(default_factory=list)
    
    # 依賴
    dependencies: List[str] = field(default_factory=list)
    
    # 筆記
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'assignee': self.assignee,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'acceptance_criteria': self.acceptance_criteria,
            'deliverables': self.deliverables,
            'dependencies': self.dependencies,
            'notes': self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """從字典創建"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            title=data['title'],
            description=data.get('description', ''),
            status=TaskStatus(data.get('status', 'pending')),
            assignee=data.get('assignee', ''),
            estimated_hours=data.get('estimated_hours', 0.0),
            actual_hours=data.get('actual_hours', 0.0),
            acceptance_criteria=data.get('acceptance_criteria', []),
            deliverables=data.get('deliverables', []),
            dependencies=data.get('dependencies', []),
            notes=data.get('notes', ''),
        )


@dataclass
class Plan:
    """計劃數據結構"""
    # 基本資訊
    plan_id: str
    name: str
    description: str = ""
    
    # 時間
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    # 狀態
    status: PlanStatus = PlanStatus.DRAFT
    
    # 進度
    progress: Dict[str, Any] = field(default_factory=lambda: {
        'total_tasks': 0,
        'completed': 0,
        'in_progress': 0,
        'pending': 0,
        'blocked': 0,
    })
    
    # 分類
    priority: str = "medium"  # low | medium | high | critical
    category: str = ""
    tags: List[str] = field(default_factory=list)
    
    # 負責人
    owner: str = ""
    collaborators: List[str] = field(default_factory=list)
    
    # 關聯
    parent_plan: Optional[str] = None
    related_plans: List[str] = field(default_factory=list)
    linked_issues: List[str] = field(default_factory=list)
    linked_prs: List[str] = field(default_factory=list)
    
    # 時間規劃
    timeline: Dict[str, Any] = field(default_factory=lambda: {
        'start_date': None,
        'target_date': None,
        'estimated_hours': 0,
    })
    
    # 驗收標準
    acceptance_criteria: List[str] = field(default_factory=list)
    
    # 風險與依賴
    risks: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[Dict[str, Any]] = field(default_factory=list)
    
    # 任務清單
    tasks: List[Task] = field(default_factory=list)
    
    # 狀態追蹤
    state_file: str = ""
    notepad_dir: str = ""
    
    def update_progress(self):
        """更新進度統計"""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        in_progress = sum(1 for t in self.tasks if t.status == TaskStatus.IN_PROGRESS)
        pending = sum(1 for t in self.tasks if t.status == TaskStatus.PENDING)
        blocked = sum(1 for t in self.tasks if t.status == TaskStatus.BLOCKED)
        
        self.progress = {
            'total_tasks': total,
            'completed': completed,
            'in_progress': in_progress,
            'pending': pending,
            'blocked': blocked,
        }
        self.updated_at = datetime.now()
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """獲取任務"""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def add_task(self, task: Task):
        """添加任務"""
        self.tasks.append(task)
        self.update_progress()
    
    def to_frontmatter(self) -> Dict[str, Any]:
        """生成 YAML Frontmatter"""
        return {
            'plan_id': self.plan_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': self.created_by,
            'status': self.status.value,
            'progress': self.progress,
            'priority': self.priority,
            'category': self.category,
            'tags': self.tags,
            'owner': self.owner,
            'collaborators': self.collaborators,
            'parent_plan': self.parent_plan,
            'related_plans': self.related_plans,
            'linked_issues': self.linked_issues,
            'linked_prs': self.linked_prs,
            'timeline': self.timeline,
            'acceptance_criteria': self.acceptance_criteria,
            'risks': self.risks,
            'dependencies': self.dependencies,
            'state_file': self.state_file,
            'notepad_dir': self.notepad_dir,
        }
    
    def to_markdown(self) -> str:
        """生成 Markdown 內容"""
        lines = []
        
        # 任務清單
        lines.append("# 任務清單\n")
        
        for task in self.tasks:
            status_icon = {
                TaskStatus.PENDING: "⬜",
                TaskStatus.IN_PROGRESS: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.BLOCKED: "🚫",
                TaskStatus.CANCELLED: "❌",
            }.get(task.status, "⬜")
            
            lines.append(f"## {status_icon} {task.title}\n")
            lines.append(f"- **任務 ID**: `{task.id}`")
            lines.append(f"- **狀態**: {task.status.value}")
            lines.append(f"- **負責人**: {task.assignee or '未分配'}")
            lines.append(f"- **預估工時**: {task.estimated_hours}h")
            if task.actual_hours > 0:
                lines.append(f"- **實際工時**: {task.actual_hours}h")
            
            if task.description:
                lines.append(f"\n{task.description}\n")
            
            if task.acceptance_criteria:
                lines.append("\n**驗收標準**:")
                for criterion in task.acceptance_criteria:
                    lines.append(f"- [ ] {criterion}")
                lines.append("")
            
            if task.deliverables:
                lines.append("\n**產出物**:")
                for deliverable in task.deliverables:
                    lines.append(f"- {deliverable}")
                lines.append("")
            
            if task.dependencies:
                lines.append(f"\n**依賴**: {', '.join(task.dependencies)}")
            
            if task.notes:
                lines.append(f"\n**筆記**: {task.notes}")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def save(self, file_path: Path):
        """保存計劃文件"""
        # YAML Frontmatter
        frontmatter = yaml.dump(self.to_frontmatter(), allow_unicode=True, sort_keys=False)
        
        # Markdown 內容
        markdown = self.to_markdown()
        
        # 組合
        content = f"---\n{frontmatter}---\n\n{markdown}"
        
        # 寫入文件
        file_path.write_text(content, encoding='utf-8')
        
        # 更新時間
        self.updated_at = datetime.now()
    
    @classmethod
    def load(cls, file_path: Path) -> 'Plan':
        """加載計劃文件"""
        content = file_path.read_text(encoding='utf-8')
        
        # 解析 YAML Frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                markdown_content = parts[2]
            else:
                frontmatter = {}
                markdown_content = content
        else:
            frontmatter = {}
            markdown_content = content
        
        # 創建 Plan 對象
        plan = cls(
            plan_id=frontmatter.get('plan_id', str(uuid.uuid4())),
            name=frontmatter.get('name', 'Untitled Plan'),
            description=frontmatter.get('description', ''),
            created_by=frontmatter.get('created_by', ''),
            status=PlanStatus(frontmatter.get('status', 'draft')),
            priority=frontmatter.get('priority', 'medium'),
            category=frontmatter.get('category', ''),
            tags=frontmatter.get('tags', []),
            owner=frontmatter.get('owner', ''),
            collaborators=frontmatter.get('collaborators', []),
            parent_plan=frontmatter.get('parent_plan'),
            related_plans=frontmatter.get('related_plans', []),
            linked_issues=frontmatter.get('linked_issues', []),
            linked_prs=frontmatter.get('linked_prs', []),
            timeline=frontmatter.get('timeline', {}),
            acceptance_criteria=frontmatter.get('acceptance_criteria', []),
            risks=frontmatter.get('risks', []),
            dependencies=frontmatter.get('dependencies', []),
            state_file=frontmatter.get('state_file', ''),
            notepad_dir=frontmatter.get('notepad_dir', ''),
        )
        
        # 解析時間
        if frontmatter.get('created_at'):
            plan.created_at = datetime.fromisoformat(frontmatter['created_at'])
        if frontmatter.get('updated_at'):
            plan.updated_at = datetime.fromisoformat(frontmatter['updated_at'])
        
        # 解析任務（簡化版）
        # 實際應使用更複雜的解析邏輯
        
        return plan


class PlanManager:
    """
    計劃管理器
    
    管理多個 Plan 文件的生命週期
    """
    
    def __init__(self, plans_dir: Path = None):
        """
        初始化計劃管理器
        
        Args:
            plans_dir: 計劃文件存儲目錄
        """
        if plans_dir is None:
            plans_dir = Path.home() / 'openclaw_workspace' / 'plans'
        
        self.plans_dir = Path(plans_dir)
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        
        self.plans: Dict[str, Plan] = {}
    
    def create_plan(self, name: str, description: str = "", 
                   created_by: str = "", **kwargs) -> Plan:
        """
        創建新計劃
        
        Args:
            name: 計劃名稱
            description: 計劃描述
            created_by: 創建者
            **kwargs: 其他參數
        
        Returns:
            Plan: 新計劃
        """
        plan_id = f"plan-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
        
        plan = Plan(
            plan_id=plan_id,
            name=name,
            description=description,
            created_by=created_by,
            status=PlanStatus.DRAFT,
            priority=kwargs.get('priority', 'medium'),
            category=kwargs.get('category', ''),
            tags=kwargs.get('tags', []),
            owner=kwargs.get('owner', created_by),
            collaborators=kwargs.get('collaborators', []),
            timeline=kwargs.get('timeline', {}),
            acceptance_criteria=kwargs.get('acceptance_criteria', []),
        )
        
        # 設置狀態文件路徑
        plan.state_file = f".openclaw/state/{plan_id}.json"
        plan.notepad_dir = f".openclaw/notepads/{plan_id}"
        
        self.plans[plan_id] = plan
        
        # 保存文件
        self._save_plan_file(plan)
        
        return plan
    
    def load_plan(self, plan_id: str) -> Optional[Plan]:
        """
        加載計劃
        
        Args:
            plan_id: 計劃 ID
        
        Returns:
            Plan: 計劃對象，或 None
        """
        # 檢查緩存
        if plan_id in self.plans:
            return self.plans[plan_id]
        
        # 從文件加載
        plan_file = self.plans_dir / f"{plan_id}.md"
        if plan_file.exists():
            plan = Plan.load(plan_file)
            self.plans[plan_id] = plan
            return plan
        
        return None
    
    def save_plan(self, plan: Plan):
        """保存計劃"""
        self.plans[plan.plan_id] = plan
        self._save_plan_file(plan)
    
    def _save_plan_file(self, plan: Plan):
        """保存計劃到文件"""
        plan_file = self.plans_dir / f"{plan.plan_id}.md"
        plan.save(plan_file)
    
    def list_plans(self, status: Optional[PlanStatus] = None) -> List[Plan]:
        """
        列出計劃
        
        Args:
            status: 過濾狀態
        
        Returns:
            Plan 列表
        """
        plans = list(self.plans.values())
        
        if status:
            plans = [p for p in plans if p.status == status]
        
        return plans
    
    def get_plan_stats(self) -> Dict[str, Any]:
        """
        獲取計劃統計
        
        Returns:
            統計字典
        """
        total = len(self.plans)
        by_status = {}
        
        for status in PlanStatus:
            count = len([p for p in self.plans.values() if p.status == status])
            by_status[status.value] = count
        
        total_tasks = sum(len(p.tasks) for p in self.plans.values())
        completed_tasks = sum(
            sum(1 for t in p.tasks if t.status == TaskStatus.COMPLETED)
            for p in self.plans.values()
        )
        
        return {
            'total_plans': total,
            'by_status': by_status,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        }


# 便捷函數
def create_plan(name: str, description: str = "", **kwargs) -> Plan:
    """快速創建計劃"""
    manager = PlanManager()
    return manager.create_plan(name, description, **kwargs)


def load_plan(plan_id: str) -> Optional[Plan]:
    """加載計劃"""
    manager = PlanManager()
    return manager.load_plan(plan_id)
