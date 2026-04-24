# Plan 文件驅動機制研究報告

## 研究目標

本報告旨在為 OpenClaw 設計一套專案計劃管理系統，參考 Oh-My-OpenAgent (OMO) 的 Plan 文件驅動設計，並結合現有狀態管理實踐，提出一套完整、可執行的解決方案。

---

## 1. Plan 文件驅動核心概念

### 1.1 什麼是 Plan 文件驅動

Plan 文件驅動是一種將專案計劃從「對話式指令」轉換為「結構化文件」的開發模式。核心思想是：

- **分離規劃與執行**：規劃階段（Planning）與執行階段（Execution）完全分離
- **文件即狀態**：計劃文件本身就是狀態的載體，無需額外數據庫
- **可恢復性**：任何時刻都可以從計劃文件恢復工作狀態
- **可追蹤性**：計劃的變更歷史天然保存在版本控制中

### 1.2 OMO 的三層架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Planning Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Prometheus  │  │    Metis     │  │    Momus     │     │
│  │   (規劃者)    │  │   (顧問)     │  │  (審查者)     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Execution Layer                          │
│  ┌────────────────────────────────────────────────────┐   │
│  │                    Atlas (指揮者)                    │   │
│  │              - 讀取計劃                             │   │
│  │              - 分析任務                             │   │
│  │              - 委派工作                             │   │
│  │              - 驗證結果                             │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Worker Layer                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Junior  │ │  Oracle  │ │  Explore │ │ Frontend │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 核心優勢

| 優勢 | 說明 |
|------|------|
| **Context 管理** | 避免對話歷史過長導致的上下文丟失 |
| **認知漂移防護** | 結構化計劃減少執行過程中的偏離 |
| **驗證機制** | 每個階段都有明確的驗收標準 |
| **專業分工** | 不同 Agent 負責不同專業領域 |
| **累積學習** | 每次任務的經驗可以傳遞給後續任務 |

---

## 2. 建議的 Plan.md 文件格式

### 2.1 文件結構

採用 **YAML Frontmatter + Markdown** 的混合格式，兼顧機器可讀性和人類可讀性：

```markdown
---
# 基本資訊
plan_id: "plan-20250413-auth-refactor"
name: "用戶認證系統重構"
description: "將現有的 Session-based 認證遷移至 JWT 機制"
created_at: "2025-04-13T10:00:00+08:00"
updated_at: "2025-04-13T14:30:00+08:00"
created_by: "Prometheus"

# 狀態資訊
status: "in_progress"  # draft | in_progress | paused | completed | cancelled
progress:
  total_tasks: 8
  completed: 3
  in_progress: 1
  pending: 4
  blocked: 0

# 優先級與分類
priority: "high"  # low | medium | high | critical
category: "backend"
tags: ["auth", "jwt", "security", "refactoring"]

# 負責人與協作者
owner: "Atlas"
collaborators: ["Junior", "Oracle"]

# 關聯資訊
parent_plan: null
related_plans: ["plan-20250401-api-v2"]
linked_issues: ["#123", "#145"]
linked_prs: []

# 時間規劃
timeline:
  start_date: "2025-04-13"
  target_date: "2025-04-20"
  estimated_hours: 16

# 驗收標準
acceptance_criteria:
  - "所有現有測試通過"
  - "JWT Token 正確生成與驗證"
  - "Session 遷移無縫進行"
  - "API 響應時間 < 100ms"

# 風險與依賴
risks:
  - id: "risk-001"
    description: "向後兼容性問題"
    mitigation: "保留舊版 API 端點 30 天"
    severity: "medium"

dependencies:
  - id: "dep-001"
    description: "等待 Redis 集群部署完成"
    status: "completed"
    blocking: false

# 狀態追蹤檔案
state_file: ".openclaw/state/plan-20250413-auth-refactor.json"
notepad_dir: ".openclaw/notepads/plan-20250413-auth-refactor"
---

# 計劃概述

## 背景

目前的 Session-based 認證機制在微服務架構下存在以下問題：
- 需要共享 Session Store，增加複雜度
- 跨域場景支持不佳
- 水平擴展受限

## 目標

遷移至 JWT-based 認證，實現：
- 無狀態服務設計
- 更好的跨域支持
- 提升系統可擴展性

## 技術方案

採用 RS256 非對稱加密，Token 結構：
```json
{
  "header": { "alg": "RS256", "typ": "JWT" },
  "payload": { "sub": "user_id", "exp": 1234567890 },
  "signature": "..."
}
```

---

# 任務清單

## Phase 1: 基礎設施準備

- [x] **Task 1**: 設計 JWT 配置結構
  - **任務 ID**: `task-001`
  - **狀態**: completed
  - **負責人**: Oracle
  - **預估工時**: 2h
  - **實際工時**: 1.5h
  - **驗收標準**:
    - [x] 配置 Schema 定義完成
    - [x] 環境變數映射設計
  - **產出物**:
    - `config/jwt.schema.json`
    - `.env.example` 更新
  - **筆記**: 參考 Auth0 最佳實踐，採用 JWKS 輪換機制

- [x] **Task 2**: 實現 JWT 工具類
  - **任務 ID**: `task-002`
  - **狀態**: completed
  - **負責人**: Junior
  - **預估工時**: 3h
  - **實際工時**: 3h
  - **驗收標準**:
    - [x] Token 生成與驗證
    - [x] 過期處理
    - [x] 刷新機制
  - **產出物**:
    - `src/utils/jwt.ts`
    - `tests/utils/jwt.test.ts`
  - **依賴**: task-001

- [x] **Task 3**: 創建 Redis Token 黑名單
  - **任務 ID**: `task-003`
  - **狀態**: completed
  - **負責人**: Junior
  - **預估工時**: 2h
  - **實際工時**: 2.5h
  - **驗收標準**:
    - [x] 登出時 Token 加入黑名單
    - [x] 黑名單自動清理
  - **產出物**:
    - `src/services/token-blacklist.ts`

## Phase 2: API 遷移

- [ ] **Task 4**: 重構登入端點
  - **任務 ID**: `task-004`
  - **狀態**: in_progress
  - **負責人**: Junior
  - **預估工時**: 4h
  - **實際工時**: 
  - **驗收標準**:
    - [ ] 返回 JWT 而非 Session ID
    - [ ] 保持 API 兼容性
    - [ ] 錯誤處理完善
  - **產出物**:
    - `src/routes/auth.ts` (更新)
    - API 文檔更新
  - **依賴**: task-002, task-003
  - **阻塞原因**: 等待 Task 3 完成

- [ ] **Task 5**: 實現認證中間件
  - **任務 ID**: `task-005`
  - **狀態**: pending
  - **負責人**: Junior
  - **預估工時**: 3h
  - **驗收標準**:
    - [ ] 從 Header 提取 Token
    - [ ] 驗證 Token 有效性
    - [ ] 處理黑名單檢查
  - **產出物**:
    - `src/middleware/auth.ts`
  - **依賴**: task-004

## Phase 3: 測試與部署

- [ ] **Task 6**: 編寫整合測試
  - **任務 ID**: `task-006`
  - **狀態**: pending
  - **負責人**: Junior
  - **預估工時**: 4h
  - **驗收標準**:
    - [ ] 登入流程測試
    - [ ] Token 刷新測試
    - [ ] 權限驗證測試
  - **產出物**:
    - `tests/integration/auth.test.ts`
  - **依賴**: task-005

- [ ] **Task 7**: 性能測試
  - **任務 ID**: `task-007`
  - **狀態**: pending
  - **負責人**: Atlas
  - **預估工時**: 2h
  - **驗收標準**:
    - [ ] 認證延遲 < 50ms
    - [ ] 並發測試通過
  - **產出物**:
    - `tests/performance/auth.perf.ts`

- [ ] **Task 8**: 部署與監控
  - **任務 ID**: `task-008`
  - **狀態**: pending
  - **負責人**: Atlas
  - **預估工時**: 2h
  - **驗收標準**:
    - [ ] 生產環境部署
    - [ ] 監控告警配置
    - [ ] 回滾方案準備
  - **產出物**:
    - 部署文檔
    - 監控儀表板

---

# 決策記錄

## ADR-001: 採用 RS256 而非 HS256

**狀態**: accepted  
**日期**: 2025-04-13

**背景**: 需要選擇 JWT 簽名算法

**決策**: 使用 RS256 (RSA + SHA-256)

**原因**:
- 私鑰僅存於服務端，安全性更高
- 支持密鑰輪換而不影響客戶端
- 符合行業標準

**替代方案**: HS256 - 對稱密鑰管理簡單但安全性較低

---

# 會議記錄

## 2025-04-13 計劃啟動會

**參與者**: Prometheus, Atlas, User  
**結論**:
1. 確認技術方案
2. 確定分三個階段執行
3. 預計 4/20 完成

---

# 變更歷史

| 日期 | 版本 | 變更內容 | 作者 |
|------|------|----------|------|
| 2025-04-13 | v1.0 | 初始計劃創建 | Prometheus |
| 2025-04-13 | v1.1 | 完成 Task 1-3，更新進度 | Atlas |
```

### 2.2 YAML Frontmatter 欄位規範

#### 必填欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `plan_id` | string | 唯一標識符，建議格式：`plan-{YYYYMMDD}-{slug}` |
| `name` | string | 計劃名稱，簡潔描述 |
| `status` | enum | 計劃整體狀態 |
| `created_at` | ISO8601 | 創建時間 |
| `updated_at` | ISO8601 | 最後更新時間 |

#### 狀態欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `progress.total_tasks` | number | 總任務數 |
| `progress.completed` | number | 已完成任務數 |
| `progress.in_progress` | number | 進行中任務數 |
| `progress.pending` | number | 待處理任務數 |
| `progress.blocked` | number | 阻塞任務數 |

#### 可選欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `priority` | enum | low/medium/high/critical |
| `category` | string | 計劃分類 |
| `tags` | string[] | 標籤列表 |
| `owner` | string | 主要負責 Agent |
| `collaborators` | string[] | 協作 Agents |
| `parent_plan` | string | 父計劃 ID |
| `timeline.start_date` | date | 開始日期 |
| `timeline.target_date` | date | 目標日期 |
| `state_file` | string | 狀態文件路徑 |
| `notepad_dir` | string | 筆記目錄路徑 |

### 2.3 任務格式規範

每個任務採用統一的 Markdown 結構：

```markdown
- [ ] **Task {n}**: {任務標題}
  - **任務 ID**: `{task-id}`
  - **狀態**: {pending | in_progress | completed | blocked}
  - **負責人**: {Agent 名稱}
  - **預估工時**: {Xh}
  - **實際工時**: {Xh}
  - **驗收標準**:
    - [ ] {標準 1}
    - [ ] {標準 2}
  - **產出物**:
    - {文件路徑}
  - **依賴**: {依賴的任務 ID}
  - **阻塞原因**: {如果狀態為 blocked}
  - **筆記**: {執行過程中的經驗}
```

---

## 3. 階段定義和狀態流轉設計

### 3.1 計劃生命週期

```
                    ┌─────────────┐
                    │    draft    │
                    │   (草稿)     │
                    └──────┬──────┘
                           │ /start-work
                           ▼
                    ┌─────────────┐
         ┌─────────│ in_progress │◄────────┐
         │         │  (進行中)    │         │
         │         └──────┬──────┘         │
    /pause│                │               │resume
         │                │               │
         ▼                │               │
    ┌─────────┐           │               │
    │ paused  │───────────┘               │
    │ (暫停)   │                           │
    └─────────┘                           │
                                          │
         ┌────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   completed     │
│   (已完成)       │
└─────────────────┘
         ▲
         │
    ┌────┴────┐
    │cancelled│
    │(已取消)  │
    └─────────┘
```

### 3.2 任務狀態流轉

```
┌─────────┐    assign    ┌─────────────┐   complete   ┌───────────┐
│ pending │─────────────►│ in_progress │─────────────►│ completed │
└────┬────┘              └──────┬──────┘              └───────────┘
     │                          │
     │ block                    │ fail
     ▼                          ▼
┌─────────┐              ┌─────────────┐
│ blocked │              │    failed   │
└────┬────┘              └──────┬──────┘
     │                          │
     │ unblock                  │ retry
     └─────────────────────────►│
                                ▼
                         ┌─────────────┐
                         │ in_progress │
                         └─────────────┘
```

### 3.3 狀態定義

#### 計劃狀態

| 狀態 | 說明 | 可轉換至 |
|------|------|----------|
| `draft` | 計劃草稿，尚未開始執行 | in_progress, cancelled |
| `in_progress` | 計劃正在執行中 | paused, completed, cancelled |
| `paused` | 計劃暫停，可隨時恢復 | in_progress, cancelled |
| `completed` | 計劃已完成 | - |
| `cancelled` | 計劃已取消 | - |

#### 任務狀態

| 狀態 | 說明 | 圖標 |
|------|------|------|
| `pending` | 等待處理 | ⏳ |
| `in_progress` | 進行中 | 🔄 |
| `completed` | 已完成 | ✅ |
| `blocked` | 被阻塞 | ⛔ |
| `failed` | 失敗 | ❌ |
| `skipped` | 已跳過 | ⏭️ |

### 3.4 狀態追蹤文件 (boulder.json)

```json
{
  "version": "1.0.0",
  "plan_id": "plan-20250413-auth-refactor",
  "plan_path": ".openclaw/plans/plan-20250413-auth-refactor.md",
  "status": "in_progress",
  "session_ids": [
    "session-abc123",
    "session-def456"
  ],
  "started_at": "2025-04-13T10:00:00+08:00",
  "last_active_at": "2025-04-13T14:30:00+08:00",
  "completed_at": null,
  "current_task": {
    "task_id": "task-004",
    "started_at": "2025-04-13T14:00:00+08:00"
  },
  "completed_tasks": ["task-001", "task-002", "task-003"],
  "pending_tasks": ["task-005", "task-006", "task-007", "task-008"],
  "blocked_tasks": [],
  "checkpoints": [
    {
      "sequence": 1,
      "timestamp": "2025-04-13T12:30:00+08:00",
      "completed_tasks": ["task-001", "task-002"],
      "notes": "基礎設施準備完成"
    },
    {
      "sequence": 2,
      "timestamp": "2025-04-13T14:30:00+08:00",
      "completed_tasks": ["task-001", "task-002", "task-003"],
      "notes": "Phase 1 完成"
    }
  ],
  "metadata": {
    "total_tokens_used": 15000,
    "estimated_remaining_hours": 12
  }
}
```

---

## 4. 與 Dashboard 整合方案

### 4.1 整合架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        Dashboard                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ 計劃總覽    │  │ 進度圖表    │  │ 任務分佈               │ │
│  │ Plan Cards  │  │ Progress    │  │ Task Distribution       │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
└─────────┼────────────────┼─────────────────────┼───────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Plan Parser Service                         │
│  - 解析 Plan.md YAML Frontmatter                               │
│  - 提取任務狀態                                                │
│  - 計算進度指標                                                │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    File System Watcher                         │
│  - 監聽 .openclaw/plans/*.md 變更                             │
│  - 監聽 .openclaw/state/*.json 變更                           │
│  - 觸發 Dashboard 更新                                         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Dashboard 組件設計

#### 4.2.1 計劃總覽卡片

```
┌─────────────────────────────────────────────────────┐
│ [🔴 High] 用戶認證系統重構              [in_progress] │
│ Plan ID: plan-20250413-auth-refactor                │
├─────────────────────────────────────────────────────┤
│ 進度: [████████░░░░░░░░] 37.5% (3/8)               │
│                                                     │
│ ⏳ Pending: 4  🔄 In Progress: 1  ✅ Done: 3       │
│                                                     │
│ 開始: 2025-04-13  預計完成: 2025-04-20             │
│ 負責人: Atlas                                      │
├─────────────────────────────────────────────────────┤
│ [查看詳情] [繼續執行] [暫停計劃]                    │
└─────────────────────────────────────────────────────┘
```

#### 4.2.2 任務看板 (Kanban)

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   ⏳ Pending  │ 🔄 In Progress│   ⛔ Blocked  │   ✅ Done    │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ Task 5       │ Task 4       │              │ Task 1       │
│ 實現認證     │ 重構登入     │              │ 設計配置     │
│ 中間件       │ 端點         │              │ 結構         │
│ [2h]         │ [4h]         │              │ [2h]         │
├──────────────┤              ├──────────────┼──────────────┤
│ Task 6       │              │              │ Task 2       │
│ 編寫整合     │              │              │ 實現 JWT     │
│ 測試         │              │              │ 工具類       │
│ [4h]         │              │              │ [3h]         │
├──────────────┤              ├──────────────┼──────────────┤
│ Task 7       │              │              │ Task 3       │
│ 性能測試     │              │              │ Redis 黑名單 │
│ [2h]         │              │              │ [2h]         │
├──────────────┤              ├──────────────┼──────────────┤
│ Task 8       │              │              │              │
│ 部署與監控   │              │              │              │
│ [2h]         │              │              │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

#### 4.2.3 甘特圖視圖

```
任務名稱           │ 4/13 │ 4/14 │ 4/15 │ 4/16 │ 4/17 │ 4/18 │ 4/19 │ 4/20 │
───────────────────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┼──────┤
Task 1: 設計配置   │██████│      │      │      │      │      │      │      │
Task 2: JWT 工具   │      │██████│██████│      │      │      │      │      │
Task 3: Redis 黑名單│     │      │██████│      │      │      │      │      │
Task 4: 重構端點   │      │      │      │██████│██████│      │      │      │
Task 5: 認證中間件 │      │      │      │      │      │██████│      │      │
Task 6: 整合測試   │      │      │      │      │      │      │██████│      │
Task 7: 性能測試   │      │      │      │      │      │      │██████│      │
Task 8: 部署監控   │      │      │      │      │      │      │      │██████│
```

### 4.3 API 設計

```typescript
// Plan 數據結構
interface Plan {
  id: string;
  name: string;
  description: string;
  status: PlanStatus;
  progress: {
    total: number;
    completed: number;
    inProgress: number;
    pending: number;
    blocked: number;
    percentage: number;
  };
  timeline: {
    startDate: Date;
    targetDate: Date;
    estimatedHours: number;
    actualHours: number;
  };
  tasks: Task[];
  metadata: PlanMetadata;
}

// Dashboard API
interface DashboardAPI {
  // 獲取所有計劃
  getPlans(filter?: PlanFilter): Promise<Plan[]>;
  
  // 獲取單個計劃詳情
  getPlan(planId: string): Promise<Plan>;
  
  // 獲取計劃統計
  getPlanStats(): Promise<PlanStats>;
  
  // 訂閱計劃變更
  subscribeToPlanChanges(callback: (plan: Plan) => void): Unsubscribe;
  
  // 執行計劃命令
  executeCommand(planId: string, command: PlanCommand): Promise<void>;
}

// 支持的命令
type PlanCommand = 
  | { type: 'start' }
  | { type: 'pause' }
  | { type: 'resume' }
  | { type: 'cancel' }
  | { type: 'restart' }
  | { type: 'updateTaskStatus'; taskId: string; status: TaskStatus }
  | { type: 'addCheckpoint'; note: string };
```

### 4.4 實時同步機制

```javascript
// 文件監聽器
class PlanFileWatcher {
  constructor(watchPaths) {
    this.watchPaths = watchPaths;
    this.callbacks = [];
  }

  start() {
    // 使用 chokidar 或類似庫監聽文件變更
    const watcher = chokidar.watch(this.watchPaths, {
      persistent: true,
      ignoreInitial: false
    });

    watcher
      .on('change', (path) => this.handleFileChange(path))
      .on('add', (path) => this.handleFileAdd(path));
  }

  handleFileChange(path) {
    const plan = this.parsePlanFile(path);
    this.notifySubscribers(plan);
  }

  parsePlanFile(path) {
    const content = fs.readFileSync(path, 'utf-8');
    const { attributes, body } = frontMatter(content);
    const tasks = this.extractTasks(body);
    
    return {
      ...attributes,
      tasks,
      content: body
    };
  }

  extractTasks(markdown) {
    // 解析 Markdown 中的任務列表
    const taskRegex = /- \[([ x])\] \*\*Task (\d+)\*\*: (.+?)\n((?:  - \*\*.+?:\*\* .+\n?)*)/g;
    const tasks = [];
    let match;
    
    while ((match = taskRegex.exec(markdown)) !== null) {
      tasks.push({
        completed: match[1] === 'x',
        number: parseInt(match[2]),
        title: match[3],
        details: this.parseTaskDetails(match[4])
      });
    }
    
    return tasks;
  }
}
```

---

## 5. 示例 Plan 文件模板

### 5.1 功能開發模板

```markdown
---
plan_id: "plan-{YYYYMMDD}-{feature-name}"
name: "{功能名稱}"
description: "{簡短描述}"
created_at: "{ISO8601}"
updated_at: "{ISO8601}"
status: "draft"
progress:
  total_tasks: 0
  completed: 0
  in_progress: 0
  pending: 0
  blocked: 0
priority: "medium"
category: "feature"
tags: []
owner: "Atlas"
collaborators: ["Junior"]
timeline:
  start_date: "{YYYY-MM-DD}"
  target_date: "{YYYY-MM-DD}"
  estimated_hours: 0
acceptance_criteria: []
state_file: ".openclaw/state/{plan_id}.json"
notepad_dir: ".openclaw/notepads/{plan_id}"
---

# 計劃概述

## 背景

{描述為什麼需要這個功能}

## 目標

{描述要達成的具體目標}

## 技術方案

{描述技術實現方案}

---

# 任務清單

## Phase 1: 需求與設計

- [ ] **Task 1**: 需求分析
  - **任務 ID**: `task-001`
  - **狀態**: pending
  - **負責人**: Oracle
  - **預估工時**: 2h
  - **驗收標準**:
    - [ ] 需求文檔完成
    - [ ] 利益相關者確認

## Phase 2: 實現

- [ ] **Task 2**: 核心功能開發
  - **任務 ID**: `task-002`
  - **狀態**: pending
  - **負責人**: Junior
  - **預估工時**: 4h
  - **驗收標準**:
    - [ ] 功能實現
    - [ ] 單元測試通過
  - **依賴**: task-001

## Phase 3: 測試與部署

- [ ] **Task 3**: 整合測試
  - **任務 ID**: `task-003`
  - **狀態**: pending
  - **負責人**: Junior
  - **預估工時**: 2h
  - **驗收標準**:
    - [ ] 整合測試通過
  - **依賴**: task-002

---

# 決策記錄

## ADR-001: {決策標題}

**狀態**: proposed  
**日期**: {YYYY-MM-DD}

**背景**: {決策背景}

**決策**: {具體決策}

**原因**: {決策原因}

**替代方案**: {考慮過的替代方案}

---

# 變更歷史

| 日期 | 版本 | 變更內容 | 作者 |
|------|------|----------|------|
| {YYYY-MM-DD} | v1.0 | 初始計劃創建 | {Agent} |
```

### 5.2 Bug 修復模板

```markdown
---
plan_id: "plan-{YYYYMMDD}-bugfix-{issue-id}"
name: "修復: {Bug 描述}"
description: "{詳細描述}"
created_at: "{ISO8601}"
updated_at: "{ISO8601}"
status: "draft"
progress:
  total_tasks: 4
  completed: 0
  in_progress: 0
  pending: 4
  blocked: 0
priority: "high"
category: "bugfix"
tags: ["bug", "urgent"]
owner: "Junior"
linked_issues: ["#{issue-id}"]
timeline:
  start_date: "{YYYY-MM-DD}"
  target_date: "{YYYY-MM-DD}"
state_file: ".openclaw/state/{plan_id}.json"
---

# Bug 描述

## 問題現象

{描述 Bug 的表現}

## 重現步驟

1. {步驟 1}
2. {步驟 2}
3. {步驟 3}

## 預期行為

{描述應該發生什麼}

## 實際行為

{描述實際發生什麼}

---

# 修復計劃

- [ ] **Task 1**: 問題調查與根因分析
  - **任務 ID**: `task-001`
  - **狀態**: pending
  - **預估工時**: 1h
  - **驗收標準**:
    - [ ] 確定根因
    - [ ] 記錄調查過程

- [ ] **Task 2**: 實現修復
  - **任務 ID**: `task-002`
  - **狀態**: pending
  - **預估工時**: 2h
  - **驗收標準**:
    - [ ] Bug 修復
    - [ ] 不引入回歸
  - **依賴**: task-001

- [ ] **Task 3**: 編寫回歸測試
  - **任務 ID**: `task-003`
  - **狀態**: pending
  - **預估工時**: 1h
  - **驗收標準**:
    - [ ] 測試能重現原 Bug
    - [ ] 測試驗證修復
  - **依賴**: task-002

- [ ] **Task 4**: 驗證與部署
  - **任務 ID**: `task-004`
  - **狀態**: pending
  - **預估工時**: 1h
  - **驗收標準**:
    - [ ] 生產環境驗證
  - **依賴**: task-003
```

### 5.3 重構模板

```markdown
---
plan_id: "plan-{YYYYMMDD}-refactor-{component}"
name: "重構: {組件名稱}"
description: "{重構目標}"
created_at: "{ISO8601}"
updated_at: "{ISO8601}"
status: "draft"
progress:
  total_tasks: 0
  completed: 0
  in_progress: 0
  pending: 0
  blocked: 0
priority: "medium"
category: "refactoring"
tags: ["refactor", "tech-debt"]
owner: "Oracle"
collaborators: ["Junior"]
timeline:
  start_date: "{YYYY-MM-DD}"
  target_date: "{YYYY-MM-DD}"
state_file: ".openclaw/state/{plan_id}.json"
---

# 重構概述

## 現有問題

{描述當前代碼的問題}

## 重構目標

{描述重構要達成的目標}

## 風險評估

| 風險 | 嚴重性 | 緩解措施 |
|------|--------|----------|
| {風險 1} | High | {措施} |
| {風險 2} | Medium | {措施} |

## 回滾策略

{描述如何回滾}

---

# 重構步驟

- [ ] **Task 1**: 現有代碼分析
  - **任務 ID**: `task-001`
  - **狀態**: pending
  - **預估工時**: 2h
  - **驗收標準**:
    - [ ] 識別所有改動點
    - [ ] 標記依賴關係

- [ ] **Task 2**: 編寫保護測試
  - **任務 ID**: `task-002`
  - **狀態**: pending
  - **預估工時**: 3h
  - **驗收標準**:
    - [ ] 行為保留測試覆蓋率 > 90%
  - **依賴**: task-001

- [ ] **Task 3**: 執行重構
  - **任務 ID**: `task-003`
  - **狀態**: pending
  - **預估工時**: 4h
  - **驗收標準**:
    - [ ] 所有測試通過
    - [ ] 代碼質量提升
  - **依賴**: task-002
```

---

## 6. 實現步驟建議

### Phase 1: 基礎架構 (1-2 週)

#### 6.1.1 目錄結構設計

```
.openclaw/
├── plans/                    # 計劃文件目錄
│   ├── plan-20250413-auth.md
│   ├── plan-20250414-api.md
│   └── archive/              # 已完成的計劃
├── state/                    # 狀態文件目錄
│   ├── plan-20250413-auth.json
│   └── current.json          # 當前活動計劃
├── notepads/                 # 筆記目錄
│   └── plan-20250413-auth/
│       ├── learnings.md
│       ├── decisions.md
│       ├── issues.md
│       └── verification.md
└── templates/                # 計劃模板
    ├── feature.md
    ├── bugfix.md
    └── refactor.md
```

#### 6.1.2 核心組件實現

1. **PlanParser**: 解析 Plan.md 文件
   ```typescript
   class PlanParser {
     parse(filePath: string): Plan {
       const content = fs.readFileSync(filePath, 'utf-8');
       const { attributes, body } = frontMatter(content);
       return {
         ...attributes,
         tasks: this.extractTasks(body),
         decisions: this.extractDecisions(body),
         meetings: this.extractMeetings(body)
       };
     }
   }
   ```

2. **StateManager**: 管理狀態文件
   ```typescript
   class StateManager {
     loadState(planId: string): PlanState {
       const statePath = `.openclaw/state/${planId}.json`;
       return JSON.parse(fs.readFileSync(statePath, 'utf-8'));
     }
     
     saveState(planId: string, state: PlanState): void {
       const statePath = `.openclaw/state/${planId}.json`;
       fs.writeFileSync(statePath, JSON.stringify(state, null, 2));
     }
     
     updateTaskStatus(planId: string, taskId: string, status: TaskStatus): void {
       const state = this.loadState(planId);
       // 更新狀態邏輯
       this.saveState(planId, state);
     }
   }
   ```

3. **PlanExecutor**: 執行計劃
   ```typescript
   class PlanExecutor {
     async start(planId: string): Promise<void> {
       const plan = this.planParser.parse(`.openclaw/plans/${planId}.md`);
       const state = this.stateManager.loadState(planId);
       
       // 初始化執行環境
       await this.initialize(plan, state);
       
       // 開始執行任務
       await this.executeNextTask(plan, state);
     }
     
     async executeNextTask(plan: Plan, state: PlanState): Promise<void> {
       const nextTask = this.findNextTask(plan, state);
       if (!nextTask) {
         await this.completePlan(plan, state);
         return;
       }
       
       // 委派給對應的 Agent
       const result = await this.delegateToAgent(nextTask);
       
       // 更新狀態
       await this.updateTaskStatus(plan.id, nextTask.id, result.status);
       
       // 繼續下一個任務
       await this.executeNextTask(plan, state);
     }
   }
   ```

### Phase 2: Dashboard 整合 (1-2 週)

#### 6.2.1 Dashboard 組件

1. **PlanOverview**: 計劃總覽組件
2. **TaskBoard**: 任務看板組件
3. **ProgressChart**: 進度圖表組件
4. **TimelineView**: 時間線視圖組件

#### 6.2.2 實時同步

- 實現文件監聽器
- WebSocket 或 SSE 推送更新
- 樂觀更新策略

### Phase 3: 命令與工具 (1 週)

#### 6.3.1 CLI 命令

```bash
# 創建新計劃
openclaw plan create --template feature --name "新功能"

# 列出所有計劃
openclaw plan list --status in_progress

# 查看計劃詳情
openclaw plan show <plan-id>

# 開始執行計劃
openclaw plan start <plan-id>

# 暫停計劃
openclaw plan pause <plan-id>

# 更新任務狀態
openclaw plan task update <plan-id> <task-id> --status completed

# 生成報告
openclaw plan report <plan-id>
```

#### 6.3.2 Skill 整合

創建 `plan-driven` Skill，提供：
- 計劃解析工具
- 狀態管理工具
- 任務執行工具
- 報告生成工具

### Phase 4: 進階功能 (2-3 週)

#### 6.4.1 計劃分片 (Plan Sharding)

對於大型計劃（40+ 任務），支持分片執行：

```json
{
  "plan_id": "large-plan",
  "shards": [
    { "id": "shard-1", "tasks": ["task-001" to "task-015"], "status": "completed" },
    { "id": "shard-2", "tasks": ["task-016" to "task-030"], "status": "in_progress" },
    { "id": "shard-3", "tasks": ["task-031" to "task-045"], "status": "pending" }
  ],
  "active_shard": "shard-2",
  "execution_window": 3
}
```

#### 6.4.2 檢查點機制

每完成 K 個任務自動創建檢查點：

```typescript
interface Checkpoint {
  sequence: number;
  timestamp: string;
  completed_tasks: string[];
  state_snapshot: PlanState;
  notes: string;
}
```

#### 6.4.3 智能恢復

- 會話恢復：從 boulder.json 恢復執行狀態
- 故障恢復：從最近檢查點恢復
- 上下文重建：自動讀取相關 notepad 文件

### Phase 5: 整合與優化 (持續)

#### 6.5.1 與現有系統整合

- 與 Memory 系統整合：自動記錄計劃相關經驗
- 與 Subagent 系統整合：支持計劃委派給 Subagent
- 與 Notification 系統整合：計劃狀態變更通知

#### 6.5.2 性能優化

- 增量解析：只解析變更的部分
- 緩存機制：緩存已解析的計劃
- 懶加載：按需加載計劃詳情

---

## 7. 參考資料

### 7.1 OMO 相關資源

- [Oh-My-OpenAgent GitHub](https://github.com/code-yeongyu/oh-my-openagent)
- [Orchestration Guide](https://github.com/code-yeongyu/oh-my-openagent/blob/dev/docs/guide/orchestration.md)
- [Feature Request: Persistent plan/todo tracking #1688](https://github.com/code-yeongyu/oh-my-openagent/issues/1688)
- [Feature Request: /omo-spec command #854](https://github.com/code-yeongyu/oh-my-openagent/issues/854)
- [Feature Request: Native long-run execution mode #1751](https://github.com/code-yeongyu/oh-my-openagent/issues/1751)

### 7.2 設計原則

1. **文件優先**: 所有狀態保存在文件中，便於版本控制
2. **人機共讀**: Markdown 格式兼顧人類閱讀和機器解析
3. **漸進增強**: 基礎功能優先，進階功能逐步添加
4. **開放擴展**: 預留擴展點，支持自定義欄位和行為

---

## 8. 總結

本報告提出了一套完整的 Plan 文件驅動設計方案，包括：

1. **核心概念**: 分離規劃與執行，文件即狀態
2. **文件格式**: YAML Frontmatter + Markdown 的混合格式
3. **狀態管理**: 完整的生命週期和流轉設計
4. **Dashboard 整合**: 可視化展示和實時同步
5. **實現路徑**: 分五個階段逐步實現

這套設計可以幫助 OpenClaw 實現：
- 更清晰的專案管理
- 更可靠的狀態追蹤
- 更好的協作體驗
- 更強的可恢復性

---

*報告生成時間: 2025-04-13*  
*版本: v1.0*
