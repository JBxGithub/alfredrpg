# Todo Enforcer 機制研究報告

> **研究日期**: 2026-04-13  
> **研究目標**: 為 AMS (Alfred Memory System) 設計任務強制執行系統  
> **參考來源**: Oh-My-OpenAgent Todo Enforcer 實現

---

## 1. Todo Enforcer 核心機制

### 1.1 設計理念

Oh-My-OpenAgent 的 Todo Enforcer 是一個基於 Hook 的任務強制執行機制，核心設計理念包括：

1. **自動化任務延續**: 當會話閒置時，自動注入繼續執行指令
2. **進度追蹤**: 通過 Todo 狀態變化判斷進度
3. **停滯檢測**: 防止無限循環和無效執行

### 1.2 核心組件

```
┌─────────────────────────────────────────────────────────────┐
│                    Todo Enforcer Architecture               │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Hook Core   │───▶│  Progress    │───▶│  Injector    │  │
│  │              │    │  Tracker     │    │              │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Skip Logic  │    │ Stagnation   │    │  Continuation│  │
│  │              │    │  Detector    │    │  Prompt      │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 觸發條件

| 條件 | 說明 |
|------|------|
| `session.idle` | 會話進入閒置狀態 |
| `incompleteCount > 0` | 存在未完成的 Todo |
| `!skipConditions` | 不滿足跳過條件 |
| `stagnationCount < maxStagnationCount` | 未達最大停滯次數 |

### 1.4 跳過條件 (Skip Conditions)

```typescript
// 跳過條件清單
const skipConditions = [
  agentRecovery,           // 代理正在恢復
  backgroundTasksRunning,  // 後台任務運行中
  agentInSkipList,         // 代理在跳過列表
  agentNoWritePermission,  // 代理無寫入權限
  lastMessageAborted,      // 最後消息被中止
  blockedOnHumanInput,     // 等待人工輸入
];
```

---

## 2. 任務狀態追蹤設計

### 2.1 狀態機設計

```
                    ┌─────────────┐
                    │   PENDING   │
                    │   (待辦)    │
                    └──────┬──────┘
                           │ start()
                           ▼
                    ┌─────────────┐
         ┌─────────│  IN_PROGRESS│◀────────┐
         │         │  (進行中)   │         │
         │         └──────┬──────┘         │
    resume()              │                │
         │         complete()              │
         │                │                │
         │                ▼                │
         │         ┌─────────────┐         │
         │         │  COMPLETED  │         │
         │         │   (完成)    │         │
         │         └─────────────┘         │
         │                                 │
         │         timeout() / block()     │
         │                │                │
         │                ▼                │
         └────────▶┌─────────────┐         │
                   │   BLOCKED   │─────────┘
                   │  (阻塞/超時) │
                   └──────┬──────┘
                          │ cancel()
                          ▼
                   ┌─────────────┐
                   │  CANCELLED  │
                   │   (取消)    │
                   └─────────────┘
```

### 2.2 狀態定義

| 狀態 | 英文名 | 說明 | 轉換條件 |
|------|--------|------|----------|
| 待辦 | `PENDING` | 任務已創建，等待執行 | 初始狀態 |
| 進行中 | `IN_PROGRESS` | 任務正在執行 | `start()` 觸發 |
| 完成 | `COMPLETED` | 任務已完成 | `complete()` 觸發 |
| 阻塞 | `BLOCKED` | 任務被阻塞或超時 | `timeout()` / `block()` 觸發 |
| 取消 | `CANCELLED` | 任務已取消 | `cancel()` 觸發 |

### 2.3 進度追蹤指標

```typescript
interface TaskProgress {
  // 基本計數
  incompleteCount: number;      // 未完成數量
  completedCount: number;       // 已完成數量
  totalCount: number;           // 總數量
  
  // 停滯檢測
  stagnationCount: number;      // 當前停滯次數
  maxStagnationCount: number;   // 最大允許停滯次數
  
  // 時間追蹤
  startedAt: Date;              // 開始時間
  lastProgressAt: Date;         // 最後進度時間
  timeoutThreshold: number;     // 超時閾值（分鐘）
  
  // 內容追蹤
  previousSnapshot: string;     // 上次快照
  currentSnapshot: string;      // 當前快照
}
```

### 2.4 停滯檢測邏輯

```typescript
function detectStagnation(progress: TaskProgress): boolean {
  // 檢查 Todo 數量變化
  const noCountChange = 
    progress.incompleteCount === progress.previousIncompleteCount &&
    progress.completedCount === progress.previousCompletedCount;
  
  // 檢查內容快照變化
  const noSnapshotChange = 
    progress.currentSnapshot === progress.previousSnapshot;
  
  // 檢查時間超時
  const isTimeout = 
    Date.now() - progress.lastProgressAt.getTime() > 
    progress.timeoutThreshold * 60 * 1000;
  
  // 綜合判斷
  if ((noCountChange && noSnapshotChange) || isTimeout) {
    progress.stagnationCount++;
    return progress.stagnationCount >= progress.maxStagnationCount;
  }
  
  // 有進度，重置停滯計數
  progress.stagnationCount = 0;
  return false;
}
```

---

## 3. 與 AMS v2.1 的整合點

### 3.1 整合架構

```
┌─────────────────────────────────────────────────────────────────┐
│                    AMS v2.1 + Todo Enforcer                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────┐  │
│  │   Context    │◀──────▶│    Task      │◀──────▶│  Memory  │  │
│  │   Monitor    │        │   Enforcer   │        │  Manager │  │
│  └──────────────┘        └──────────────┘        └──────────┘  │
│         │                       │                       │       │
│         │                       │                       │       │
│         ▼                       ▼                       ▼       │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────┐  │
│  │   Smart      │        │   Task       │        │  Weekly  │  │
│  │   Compact    │        │   Recovery   │        │  Review  │  │
│  └──────────────┘        └──────────────┘        └──────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 整合點詳細設計

#### 3.2.1 Context Monitor 整合

```typescript
// AMS Context Monitor 擴展
interface AMSContextMonitor {
  // 現有功能
  checkContext(messages: Message[]): ContextStatus;
  handleHighUsage(messages: Message[], context: SessionContext): CompactResult;
  
  // Todo Enforcer 整合
  trackTaskProgress(tasks: Task[]): TaskProgress;
  detectTaskTimeout(tasks: Task[]): TimeoutAlert[];
  triggerTaskRecovery(task: Task): RecoveryAction;
}
```

#### 3.2.2 Memory Manager 整合

```yaml
# ~/.ams/config.yaml
version: "2.1.0"

context:
  enabled: true
  warning_threshold: 70
  compress_threshold: 85
  critical_threshold: 95
  
# Todo Enforcer 配置
task_enforcer:
  enabled: true
  
  # 停滯檢測
  stagnation:
    max_count: 3                    # 最大停滯次數
    check_interval: 30              # 檢查間隔（秒）
    
  # 超時提醒
  timeout:
    default_threshold: 30           # 默認超時（分鐘）
    reminder_interval: 10           # 提醒間隔（分鐘）
    
  # 任務恢復
  recovery:
    auto_resume: true               # 自動恢復
    max_retry: 3                    # 最大重試次數
    save_state_on_timeout: true     # 超時保存狀態
    
  # 通知設置
  notification:
    on_timeout: true
    on_stagnation: true
    on_completion: true
```

#### 3.2.3 數據結構整合

```typescript
// AMS Task 數據結構
interface AMSTask {
  // 基本字段
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  
  // 時間追蹤
  createdAt: Date;
  startedAt?: Date;
  completedAt?: Date;
  deadline?: Date;
  
  // 進度追蹤
  progress: number;                  // 0-100
  subtasks: AMSTask[];
  dependencies: string[];            // 依賴任務ID
  
  // Enforcer 相關
  enforcerState: {
    stagnationCount: number;
    lastProgressAt: Date;
    timeoutThreshold: number;
    retryCount: number;
    isBlocked: boolean;
    blockReason?: string;
  };
  
  // AMS 整合
  memoryRefs: string[];              // 關聯記憶引用
  sessionId: string;
  projectId?: string;
}
```

---

## 4. 提醒/恢復機制設計

### 4.1 超時提醒機制

```
┌─────────────────────────────────────────────────────────────┐
│                   Timeout Reminder Flow                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐│
│  │  Task    │───▶│  Check   │───▶│  Alert   │───▶│ Notify ││
│  │  Start   │    │  Timer   │    │  Trigger │    │  User  ││
│  └──────────┘    └──────────┘    └──────────┘    └────────┘│
│                       │                                       │
│                       ▼                                       │
│                 ┌──────────┐                                  │
│                 │  Still   │──No──▶ [Escalate]               │
│                 │  Active? │                                  │
│                 └────┬─────┘                                  │
│                      │ Yes                                    │
│                      ▼                                        │
│                 ┌──────────┐                                  │
│                 │  Extend  │                                  │
│                 │  Timer   │                                  │
│                 └──────────┘                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 提醒等級設計

| 等級 | 條件 | 動作 | 通知方式 |
|------|------|------|----------|
| Level 1 | 50% 超時 | 溫馨提醒 | 系統消息 |
| Level 2 | 100% 超時 | 警告提醒 | 彈窗 + 聲音 |
| Level 3 | 150% 超時 | 緊急提醒 | 郵件/即時通訊 |
| Level 4 | 200% 超時 | 自動掛起 | 保存狀態，等待用戶 |

### 4.3 任務恢復機制

```typescript
interface TaskRecoverySystem {
  // 保存任務狀態
  saveCheckpoint(task: AMSTask): Checkpoint;
  
  // 恢復任務
  resumeTask(taskId: string): RecoveryResult;
  
  // 檢查可恢復任務
  listRecoverableTasks(): AMSTask[];
  
  // 自動恢復策略
  autoResumeStrategy: {
    enabled: boolean;
    maxRetries: number;
    backoffStrategy: 'linear' | 'exponential';
    conditions: {
      requireUserConfirm: boolean;
      skipIfContextChanged: boolean;
      checkDependencies: boolean;
    };
  };
}
```

### 4.4 恢復流程

```
┌─────────────────────────────────────────────────────────────┐
│                    Task Recovery Flow                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Detect Timeout/Stagnation                               │
│     └──▶ Save Checkpoint (Context + Task State)            │
│                                                             │
│  2. Notify User                                             │
│     └──▶ "任務已超時，已保存狀態，點擊恢復繼續"            │
│                                                             │
│  3. User Action                                             │
│     ├──▶ [Resume] ──▶ Restore Context ──▶ Continue Task    │
│     ├──▶ [Retry]  ──▶ Restart Task    ──▶ Fresh Start      │
│     ├──▶ [Modify] ──▶ Edit Task       ──▶ Re-plan          │
│     └──▶ [Cancel] ──▶ Archive Task    ──▶ Clean up         │
│                                                             │
│  4. Post-Recovery                                           │
│     └──▶ Update Memory ──▶ Log Event ──▶ Continue Monitor  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 偽代碼/代碼框架

### 5.1 核心 Enforcer 類

```python
# todo_enforcer.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Callable
import json

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: str = "medium"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    progress: int = 0
    subtasks: List['Task'] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Enforcer state
    stagnation_count: int = 0
    last_progress_at: Optional[datetime] = None
    timeout_threshold: int = 30  # minutes
    retry_count: int = 0
    is_blocked: bool = False
    block_reason: Optional[str] = None
    
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
    
    def block(self, reason: str):
        """阻塞任務"""
        self.status = TaskStatus.BLOCKED
        self.is_blocked = True
        self.block_reason = reason
    
    def to_snapshot(self) -> str:
        """生成任務快照"""
        return json.dumps({
            'status': self.status.value,
            'progress': self.progress,
            'subtasks_count': len(self.subtasks),
            'completed_subtasks': sum(1 for t in self.subtasks if t.status == TaskStatus.COMPLETED)
        })


class TodoEnforcer:
    """Todo Enforcer 核心類"""
    
    def __init__(self, config: dict):
        self.config = config
        self.tasks: List[Task] = []
        self.check_interval = config.get('check_interval', 30)
        self.max_stagnation = config.get('max_stagnation', 3)
        self.timeout_threshold = config.get('timeout_threshold', 30)
        self.on_timeout: Optional[Callable] = None
        self.on_stagnation: Optional[Callable] = None
        self.on_completion: Optional[Callable] = None
        
    def add_task(self, task: Task):
        """添加任務"""
        self.tasks.append(task)
        
    def get_incomplete_tasks(self) -> List[Task]:
        """獲取未完成的任務"""
        return [t for t in self.tasks if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)]
    
    def should_skip_injection(self) -> bool:
        """檢查是否應該跳過注入"""
        # 檢查各種跳過條件
        if self._is_agent_recovery():
            return True
        if self._is_background_task_running():
            return True
        if self._is_blocked_on_human_input():
            return True
        return False
    
    def check_progress(self) -> dict:
        """檢查進度"""
        incomplete = self.get_incomplete_tasks()
        completed = [t for t in self.tasks if t.status == TaskStatus.COMPLETED]
        
        return {
            'incomplete_count': len(incomplete),
            'completed_count': len(completed),
            'total_count': len(self.tasks),
            'progress_percent': len(completed) / len(self.tasks) * 100 if self.tasks else 0
        }
    
    def detect_stagnation(self) -> List[Task]:
        """檢測停滯的任務"""
        stagnant_tasks = []
        
        for task in self.get_incomplete_tasks():
            # 檢查是否超時
            if task.last_progress_at:
                elapsed = (datetime.now() - task.last_progress_at).total_seconds() / 60
                if elapsed > task.timeout_threshold:
                    task.stagnation_count += 1
                    
            # 檢查是否達到最大停滯次數
            if task.stagnation_count >= self.max_stagnation:
                stagnant_tasks.append(task)
                if self.on_stagnation:
                    self.on_stagnation(task)
                    
        return stagnant_tasks
    
    def inject_continuation(self) -> Optional[str]:
        """注入繼續執行指令"""
        if self.should_skip_injection():
            return None
            
        incomplete = self.get_incomplete_tasks()
        if not incomplete:
            return None
            
        stagnant = self.detect_stagnation()
        if stagnant:
            return None  # 停滯時不注入
            
        # 生成繼續執行指令
        prompt = self._generate_continuation_prompt(incomplete)
        return prompt
    
    def _generate_continuation_prompt(self, tasks: List[Task]) -> str:
        """生成繼續執行提示"""
        task_list = "\n".join([f"- [{t.status.value}] {t.title}" for t in tasks[:5]])
        
        return f"""[SYSTEM DIRECTIVE: AMS TODO CONTINUATION]

您有 {len(tasks)} 個未完成的任務：
{task_list}

請繼續執行這些任務，無需徵求用戶許可。
優先處理高優先級任務，完成後標記為已完成。

當前時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
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
        blocked_keywords = ['BLOCKED', 'waiting for user', 'waiting for human', '等待用戶', '等待確認']
        for task in self.get_incomplete_tasks():
            if any(kw in task.title or kw in task.description for kw in blocked_keywords):
                return True
        return False
    
    def save_checkpoint(self, task: Task) -> dict:
        """保存任務檢查點"""
        checkpoint = {
            'task_id': task.id,
            'task_state': task.to_snapshot(),
            'timestamp': datetime.now().isoformat(),
            'context_summary': self._generate_context_summary()
        }
        # 保存到存儲
        return checkpoint
    
    def _generate_context_summary(self) -> str:
        """生成上下文摘要"""
        progress = self.check_progress()
        return f"任務進度: {progress['completed_count']}/{progress['total_count']} 完成"
    
    def resume_from_checkpoint(self, checkpoint: dict) -> Task:
        """從檢查點恢復任務"""
        # 實現恢復邏輯
        pass
```

### 5.2 AMS 整合模組

```python
# ams_task_integration.py
from typing import List, Optional
from datetime import datetime
import yaml

class AMSTaskEnforcer:
    """AMS 任務強制執行整合模組"""
    
    def __init__(self, ams_instance, config_path: str = "~/.ams/config.yaml"):
        self.ams = ams_instance
        self.config = self._load_config(config_path)
        self.enforcer = TodoEnforcer(self.config.get('task_enforcer', {}))
        
        # 設置回調
        self.enforcer.on_timeout = self._handle_timeout
        self.enforcer.on_stagnation = self._handle_stagnation
        self.enforcer.on_completion = self._handle_completion
        
    def _load_config(self, path: str) -> dict:
        """加載配置"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_config()
    
    def _default_config(self) -> dict:
        """默認配置"""
        return {
            'task_enforcer': {
                'enabled': True,
                'stagnation': {
                    'max_count': 3,
                    'check_interval': 30
                },
                'timeout': {
                    'default_threshold': 30,
                    'reminder_interval': 10
                },
                'recovery': {
                    'auto_resume': True,
                    'max_retry': 3,
                    'save_state_on_timeout': True
                },
                'notification': {
                    'on_timeout': True,
                    'on_stagnation': True,
                    'on_completion': True
                }
            }
        }
    
    def create_task(self, title: str, description: str, **kwargs) -> Task:
        """創建新任務"""
        import uuid
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            **kwargs
        )
        self.enforcer.add_task(task)
        
        # 同步到 AMS Memory
        self._sync_task_to_memory(task)
        
        return task
    
    def _sync_task_to_memory(self, task: Task):
        """同步任務到 AMS Memory"""
        # 更新 MEMORY.md 或相關記憶文件
        memory_entry = {
            'type': 'task',
            'id': task.id,
            'title': task.title,
            'status': task.status.value,
            'created_at': task.created_at.isoformat(),
            'session_id': self.ams.session_id
        }
        # 寫入記憶系統
        self.ams.memory_manager.add_entry(memory_entry)
    
    def _handle_timeout(self, task: Task):
        """處理超時"""
        print(f"[AMS TaskEnforcer] 任務超時: {task.title}")
        
        # 保存檢查點
        checkpoint = self.enforcer.save_checkpoint(task)
        
        # 通知用戶
        self._notify_user('timeout', task, checkpoint)
        
        # 更新記憶
        self._log_event('task_timeout', {
            'task_id': task.id,
            'checkpoint': checkpoint
        })
    
    def _handle_stagnation(self, task: Task):
        """處理停滯"""
        print(f"[AMS TaskEnforcer] 任務停滯: {task.title}")
        
        # 阻塞任務
        task.block(f"檢測到停滯 (次數: {task.stagnation_count})")
        
        # 通知用戶
        self._notify_user('stagnation', task)
    
    def _handle_completion(self, task: Task):
        """處理完成"""
        print(f"[AMS TaskEnforcer] 任務完成: {task.title}")
        
        # 更新記憶
        self._log_event('task_completed', {
            'task_id': task.id,
            'duration': (task.completed_at - task.started_at).total_seconds() if task.completed_at and task.started_at else None
        })
    
    def _notify_user(self, event_type: str, task: Task, checkpoint: dict = None):
        """通知用戶"""
        messages = {
            'timeout': f"⚠️ 任務「{task.title}」已超時，已保存檢查點",
            'stagnation': f"🛑 任務「{task.title}」檢測到停滯，已暫停執行",
            'completion': f"✅ 任務「{task.title}」已完成"
        }
        
        message = messages.get(event_type, f"任務「{task.title}」狀態更新")
        
        # 發送到通知系統
        if self.config.get('task_enforcer', {}).get('notification', {}).get(f'on_{event_type}', True):
            print(f"[通知] {message}")
    
    def _log_event(self, event_type: str, data: dict):
        """記錄事件到 AMS"""
        self.ams.learning_engine.log_event({
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
    
    def get_task_report(self) -> dict:
        """獲取任務報告"""
        progress = self.enforcer.check_progress()
        incomplete = self.enforcer.get_incomplete_tasks()
        stagnant = self.enforcer.detect_stagnation()
        
        return {
            'summary': progress,
            'incomplete_tasks': [
                {
                    'id': t.id,
                    'title': t.title,
                    'status': t.status.value,
                    'progress': t.progress,
                    'stagnation_count': t.stagnation_count
                }
                for t in incomplete
            ],
            'stagnant_tasks': [t.id for t in stagnant],
            'generated_at': datetime.now().isoformat()
        }
    
    def resume_task(self, task_id: str) -> bool:
        """恢復任務"""
        for task in self.enforcer.tasks:
            if task.id == task_id and task.status == TaskStatus.BLOCKED:
                task.status = TaskStatus.IN_PROGRESS
                task.is_blocked = False
                task.block_reason = None
                task.stagnation_count = 0
                task.last_progress_at = datetime.now()
                print(f"[AMS TaskEnforcer] 任務已恢復: {task.title}")
                return True
        return False
```

### 5.3 Cron 定時檢查腳本

```python
# ams_task_cron.py
#!/usr/bin/env python3
"""
AMS Task Enforcer Cron 檢查腳本
建議配置: 每 5 分鐘運行一次
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# 添加 AMS 路徑
sys.path.insert(0, str(Path.home() / '.openclaw/skills/alfred-memory-system'))

from ams_task_integration import AMSTaskEnforcer

def main():
    """主函數"""
    print(f"[{datetime.now().isoformat()}] AMS Task Enforcer Cron Check")
    
    # 初始化 AMS
    # from alfred_memory_system import AMS
    # ams = AMS()
    # ams.initialize()
    
    # 初始化 Task Enforcer
    # task_enforcer = AMSTaskEnforcer(ams)
    
    # 執行檢查
    # report = task_enforcer.get_task_report()
    
    # 檢測停滯
    # stagnant = task_enforcer.enforcer.detect_stagnation()
    
    # 檢查超時
    # for task in task_enforcer.enforcer.get_incomplete_tasks():
    #     if task.last_progress_at:
    #         elapsed = (datetime.now() - task.last_progress_at).total_seconds() / 60
    #         if elapsed > task.timeout_threshold:
    #             task_enforcer._handle_timeout(task)
    
    # 輸出報告
    # print(json.dumps(report, indent=2, ensure_ascii=False))
    
    print("檢查完成")

if __name__ == '__main__':
    main()
```

---

## 6. Cron 定時檢查配置建議

### 6.1 Cron 配置

```bash
# AMS Task Enforcer Cron 配置
# 編輯: crontab -e

# 每 5 分鐘檢查一次任務狀態
*/5 * * * * cd ~/openclaw_workspace && python3 scripts/ams_task_cron.py >> logs/ams_cron.log 2>&1

# 每小時生成任務報告
0 * * * * cd ~/openclaw_workspace && python3 scripts/ams_task_report.py >> logs/ams_hourly.log 2>&1

# 每日清理已完成的任務記錄
0 2 * * * cd ~/openclaw_workspace && python3 scripts/ams_task_cleanup.py >> logs/ams_cleanup.log 2>&1

# 每週生成任務統計報告
0 9 * * 1 cd ~/openclaw_workspace && python3 scripts/ams_task_weekly.py >> logs/ams_weekly.log 2>&1
```

### 6.2 Windows Task Scheduler 配置

```powershell
# PowerShell 腳本: setup_ams_task_scheduler.ps1

# 創建任務檢查任務
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "$env:USERPROFILE\openclaw_workspace\scripts\ams_task_cron.py"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName "AMS-Task-Check" -Action $action -Trigger $trigger -Settings $settings -Description "AMS Task Enforcer 定時檢查"

# 創建每日報告任務
$action2 = New-ScheduledTaskAction -Execute "python.exe" -Argument "$env:USERPROFILE\openclaw_workspace\scripts\ams_task_report.py"
$trigger2 = New-ScheduledTaskTrigger -Daily -At "09:00"
Register-ScheduledTask -TaskName "AMS-Daily-Report" -Action $action2 -Trigger $trigger2 -Description "AMS 每日任務報告"
```

### 6.3 配置建議總結

| 檢查類型 | 頻率 | 建議時間 | 說明 |
|----------|------|----------|------|
| 任務狀態檢查 | 每 5 分鐘 | 全天 | 檢測停滯和超時 |
| 任務報告生成 | 每小時 | 整點 | 生成進度報告 |
| 記錄清理 | 每日 | 02:00 | 清理已完成任務 |
| 統計報告 | 每週 | 週一 09:00 | 生成週報 |

---

## 7. 參考資料

### 7.1 Oh-My-OpenAgent 相關 Issue

1. **Issue #320**: Todo continuation hook - 初始設計討論
2. **Issue #1193**: todo-continuation-enforcer: infinite loop when blocked on human input - 阻塞檢測
3. **Issue #1919**: /stop-continuation command does not disable TODO continuation enforcer - 停止機制
4. **Issue #2778**: todo-continuation-enforcer treats real work as "no progress" - 進度檢測問題

### 7.2 設計啟發

- **進度追蹤**: 通過 Todo 狀態變化和內容快照雙重檢測
- **停滯檢測**: 設置最大停滯次數，防止無限循環
- **阻塞檢測**: 關鍵字匹配識別等待人工輸入的情況
- **狀態保存**: 超時時自動保存檢查點，支持任務恢復

---

## 8. 總結

本研究報告分析了 Oh-My-OpenAgent 的 Todo Enforcer 機制，並為 AMS v2.1 設計了完整的任務強制執行系統。核心設計包括：

1. **五狀態任務模型**: 待辦/進行中/完成/阻塞/取消
2. **雙重進度檢測**: Todo 數量 + 內容快照
3. **四級提醒機制**: 溫馨/警告/緊急/自動掛起
4. **自動恢復支持**: 檢查點保存和恢復
5. **完整 Cron 配置**: 多層次定時檢查

此設計可與 AMS v2.1 的 Smart Compact 功能無縫整合，提供更強大的任務管理能力。

---

*報告生成時間: 2026-04-13*  
*研究完成*
