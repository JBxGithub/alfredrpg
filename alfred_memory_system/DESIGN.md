# Alfred Memory System (AMS) - Windows 版自適應學習記憶架構

> **靈感來源**: Hermes Agent + OpenClaw 記憶系統
> **設計目標**: 為呀鬼打造一個持續學習、自我改進的長期記憶系統
> **版本**: v1.0.0
> **日期**: 2026-04-08

---

## 🎯 系統願景

### 核心問題
現有的三層記憶系統（summary/memory/tacit）雖然有效，但缺乏：
1. **自動學習機制** - 無法從經驗中自動提取模式
2. **Context 監控** - 無法實時追蹤對話長度
3. **技能自我改進** - Skills 創建後不會自動優化
4. **跨 Session 智能檢索** - 無法自動關聯過去相關對話

### 解決方案
Alfred Memory System (AMS) - 一個輕量級、自適應、持續學習的記憶架構。

---

## 🏗️ 系統架構

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Alfred Memory System (AMS)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Context    │  │   Memory     │  │    Skill     │  │   Session    │    │
│  │   Monitor    │  │   Engine     │  │   Evolver    │  │   Search     │    │
│  │  (監控層)     │  │  (記憶層)     │  │  (進化層)     │  │  (檢索層)     │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │            │
│         ▼                 ▼                 ▼                 ▼            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Learning Loop (學習循環)                        │   │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐          │   │
│  │  │ Extract │───▶│ Pattern │───▶│ Validate│───▶│  Store  │          │   │
│  │  │ (提取)   │    │ (識別)   │    │ (驗證)   │    │ (存儲)   │          │   │
│  │  └─────────┘    └─────────┘    └─────────┘    └─────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Storage Layer (存儲層)                          │   │
│  │  SQLite (FTS5)  +  JSON  +  Markdown  +  Vector DB (可選)            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 核心組件

### 1. Context Monitor (Context 監控器)

**功能**: 實時監控對話長度，在達到閾值時自動觸發壓縮或通知

**設計**:
```python
class ContextMonitor:
    """
    監控對話 Context 使用情況
    """
    
    # 閾值設定 (可配置)
    WARNING_THRESHOLD = 0.70    # 70% - 發出警告
    COMPRESS_THRESHOLD = 0.85   # 85% - 自動壓縮
    CRITICAL_THRESHOLD = 0.95   # 95% - 緊急處理
    
    def __init__(self, model_context_length: int = 128000):
        self.context_length = model_context_length
        self.current_tokens = 0
        self.history = []
        
    def estimate_tokens(self, messages: list) -> int:
        """估算當前對話的 token 數量"""
        # 使用字符數 + 模型特定係數估算
        total_chars = sum(len(m.get('content', '')) for m in messages)
        # 中文字符約 1.5 tokens，英文約 0.25 tokens
        chinese_chars = sum(1 for m in messages for c in m.get('content', '') if '\u4e00' <= c <= '\u9fff')
        english_chars = total_chars - chinese_chars
        return int(chinese_chars * 1.5 + english_chars * 0.25 + len(messages) * 4)
    
    def check_context(self, messages: list) -> dict:
        """檢查當前 Context 狀態"""
        self.current_tokens = self.estimate_tokens(messages)
        usage_ratio = self.current_tokens / self.context_length
        
        status = {
            'tokens': self.current_tokens,
            'limit': self.context_length,
            'usage_percent': round(usage_ratio * 100, 1),
            'status': 'normal',
            'action_required': None
        }
        
        if usage_ratio >= self.CRITICAL_THRESHOLD:
            status['status'] = 'critical'
            status['action_required'] = 'emergency_compress'
        elif usage_ratio >= self.COMPRESS_THRESHOLD:
            status['status'] = 'compress'
            status['action_required'] = 'compress_context'
        elif usage_ratio >= self.WARNING_THRESHOLD:
            status['status'] = 'warning'
            status['action_required'] = 'notify_user'
            
        return status
```

**輸出格式**:
```
═══════════════════════════════════════════════════════════
📊 Context Usage: 73.5% (94,080 / 128,000 tokens)
⚠️  WARNING: Approaching compression threshold (85%)
═══════════════════════════════════════════════════════════
```

---

### 2. Memory Engine (記憶引擎)

**功能**: 自動提取、整理和存儲重要信息

**核心特性**:
- **自動提取**: 從對話中自動識別重要決策、偏好、事實
- **智能分類**: 自動分類為 User Profile / Environment / Learned Skills
- **容量管理**: 自動整合舊記憶，保持記憶精煉
- **衝突檢測**: 檢測新信息與舊記憶的衝突，提示更新

**記憶結構**:
```python
@dataclass
class MemoryEntry:
    id: str                          # 唯一ID
    content: str                     # 記憶內容
    category: str                    # 分類: user_profile / environment / skill / preference
    source_session: str              # 來源 Session ID
    timestamp: datetime              # 創建時間
    confidence: float                # 置信度 (0-1)
    access_count: int                # 訪問次數
    last_accessed: datetime          # 最後訪問時間
    related_entries: List[str]       # 相關記憶ID
    tags: List[str]                  # 標籤
```

**自動提取規則**:
```python
EXTRACTION_RULES = {
    'user_preference': {
        'patterns': [
            r'我(比較|更)?喜歡(.+?)[。，]',
            r'我(通常|習慣|偏好)(.+?)[。，]',
            r'(.+?)對我來說(很|更)重要',
        ],
        'category': 'preference',
        'priority': 'high'
    },
    'environment_fact': {
        'patterns': [
            r'(這台|我的)(電腦|機器|服務器)(.+?)[。，]',
            r'(項目|專案|代碼)位於(.+?)[。，]',
            r'(使用|運行|安裝)了(.+?)[。，]',
        ],
        'category': 'environment',
        'priority': 'medium'
    },
    'decision_record': {
        'patterns': [
            r'(決定|確定|選擇)使用(.+?)[。，]',
            r'(我們|咱們)(採用|使用)(.+?)方案',
            r'最終(.+?)選擇(.+?)[。，]',
        ],
        'category': 'decision',
        'priority': 'high'
    },
    'correction_learned': {
        'patterns': [
            r'(不對|錯了|更正)(.+?)[應該|要](.+?)[。，]',
            r'(記住|注意)(.+?)不是(.+?)[而是|是]',
        ],
        'category': 'correction',
        'priority': 'critical'
    }
}
```

---

### 3. Skill Evolver (技能進化器)

**功能**: 自動從經驗中創建和改進 Skills

**工作流程**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Skill Evolver Workflow                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. TRIGGER (觸發條件)                                       │
│     - 完成複雜任務 (>5 tool calls)                           │
│     - 用戶明確要求 "記住這個流程"                             │
│     - 多次執行相似任務 (模式識別)                             │
│     - 遇到錯誤後找到解決方案                                  │
│                                                             │
│  2. EXTRACT (提取內容)                                       │
│     - 任務目標                                                │
│     - 執行步驟                                                │
│     - 關鍵決策點                                              │
│     - 遇到的問題和解決方案                                     │
│     - 驗證方法                                                │
│                                                             │
│  3. GENERATE (生成 Skill)                                    │
│     - 創建 SKILL.md                                          │
│     - 提取可重用腳本                                          │
│     - 建立參考文檔                                            │
│                                                             │
│  4. VALIDATE (驗證)                                          │
│     - 檢查 Skill 完整性                                       │
│     - 測試關鍵步驟                                            │
│     - 用戶確認                                                │
│                                                             │
│  5. STORE (存儲)                                             │
│     - 保存到 skills/ 目錄                                     │
│     - 更新技能索引                                            │
│     - 記錄創建來源                                            │
│                                                             │
│  6. EVOLVE (進化)                                            │
│     - 追蹤 Skill 使用情況                                     │
│     - 收集改進建議                                            │
│     - 定期優化更新                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Skill 改進追蹤**:
```python
@dataclass
class SkillMetrics:
    skill_name: str
    created_at: datetime
    usage_count: int
    success_count: int
    failure_count: int
    last_used: datetime
    avg_execution_time: float
    user_ratings: List[int]  # 1-5 星評分
    improvement_suggestions: List[str]
    version_history: List[dict]
```

---

### 4. Session Search (會話搜索)

**功能**: 智能檢索過去對話，支持語義搜索

**特性**:
- **FTS5 全文搜索**: 基於 SQLite FTS5 的快速搜索
- **語義搜索**: 使用嵌入向量進行相似度匹配 (可選)
- **時間範圍**: 支持按時間範圍過濾
- **相關性評分**: 基於 TF-IDF + 時間衰減的評分
- **自動摘要**: 使用 LLM 生成會話摘要

**搜索模式**:
```python
class SessionSearch:
    def search(
        self,
        query: str,
        mode: str = 'hybrid',           # 'keyword', 'semantic', 'hybrid'
        time_range: Optional[tuple] = None,  # (start_date, end_date)
        limit: int = 10,
        min_relevance: float = 0.5
    ) -> List[SearchResult]:
        """
        搜索過去會話
        
        Args:
            query: 搜索查詢
            mode: 搜索模式
            time_range: 時間範圍過濾
            limit: 返回結果數量
            min_relevance: 最小相關性分數
        """
        pass
```

---

## 💾 存儲層設計

### 數據庫結構 (SQLite + FTS5)

```sql
-- 會話表
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    platform TEXT,  -- whatsapp, telegram, cli, etc.
    summary TEXT,
    message_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0
);

-- 消息表
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role TEXT,  -- user, assistant, system
    content TEXT,
    tool_calls TEXT,  -- JSON
    tool_results TEXT,  -- JSON
    token_estimate INTEGER
);

-- 消息全文搜索 (FTS5)
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    content_rowid=rowid,
    prefix=2,  -- 支持前綴搜索
    tokenize='porter'  -- 詞幹提取
);

-- 記憶表
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    category TEXT,  -- user_profile, environment, skill, preference, decision
    source_session TEXT REFERENCES sessions(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence REAL DEFAULT 1.0,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    tags TEXT  -- JSON array
);

-- 記憶全文搜索
CREATE VIRTUAL TABLE memories_fts USING fts5(
    content,
    content_rowid=rowid,
    prefix=2
);

-- Skill 表
CREATE TABLE skills (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    content TEXT,  -- SKILL.md 內容
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    version TEXT DEFAULT '1.0.0',
    auto_created BOOLEAN DEFAULT FALSE,
    source_sessions TEXT  -- JSON array of session IDs
);

-- Context 使用記錄
CREATE TABLE context_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens_used INTEGER,
    tokens_limit INTEGER,
    usage_percent REAL,
    action_taken TEXT  -- notify, compress, emergency_compress
);

-- 索引
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_memories_category ON memories(category);
CREATE INDEX idx_memories_accessed ON memories(last_accessed);
CREATE INDEX idx_skills_name ON skills(name);
```

---

## 🔄 學習循環 (Learning Loop)

### 自動學習流程

```python
class LearningLoop:
    """
    持續學習循環 - 每次對話後自動執行
    """
    
    def run(self, session_id: str, messages: list):
        """執行學習循環"""
        
        # 1. EXTRACT - 提取潛在記憶
        candidates = self.extract_candidates(messages)
        
        # 2. PATTERN - 識別模式
        patterns = self.identify_patterns(candidates)
        
        # 3. VALIDATE - 驗證和過濾
        validated = self.validate_patterns(patterns)
        
        # 4. STORE - 存儲有效記憶
        for item in validated:
            self.store_memory(item, session_id)
        
        # 5. SKILL CHECK - 檢查是否需要創建 Skill
        if self.should_create_skill(messages):
            skill_draft = self.generate_skill_draft(messages)
            self.propose_skill(skill_draft)
        
        # 6. CONTEXT CHECK - 檢查 Context 使用
        context_status = self.context_monitor.check_context(messages)
        if context_status['action_required']:
            self.handle_context_action(context_status)
    
    def extract_candidates(self, messages: list) -> List[dict]:
        """從對話中提取候選記憶"""
        candidates = []
        
        for msg in messages:
            if msg['role'] != 'user':
                continue
                
            content = msg.get('content', '')
            
            # 應用提取規則
            for rule_name, rule in EXTRACTION_RULES.items():
                for pattern in rule['patterns']:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        candidates.append({
                            'type': rule_name,
                            'category': rule['category'],
                            'content': match if isinstance(match, str) else ' '.join(match),
                            'priority': rule['priority'],
                            'source_message': msg.get('id')
                        })
        
        return candidates
    
    def identify_patterns(self, candidates: list) -> List[dict]:
        """識別重複出現的模式"""
        # 使用簡單的相似度聚類
        patterns = []
        
        # 按類型分組
        by_type = defaultdict(list)
        for c in candidates:
            by_type[c['type']].append(c)
        
        # 識別重複模式
        for type_name, items in by_type.items():
            if len(items) >= 3:  # 出現3次以上視為模式
                patterns.append({
                    'type': type_name,
                    'frequency': len(items),
                    'examples': items[:3],
                    'confidence': min(1.0, len(items) / 10)  # 越多越確信
                })
        
        return patterns
```

---

## 🛠️ 實現計劃

### Phase 1: 基礎架構 (1-2 天)
- [ ] 建立 SQLite 數據庫結構
- [ ] 實現 ContextMonitor 基礎功能
- [ ] 建立會話記錄機制
- [ ] 整合到現有 OpenClaw 流程

### Phase 2: 記憶引擎 (2-3 天)
- [ ] 實現自動提取規則
- [ ] 建立記憶存儲和檢索
- [ ] 實現記憶整合和容量管理
- [ ] 建立 MEMORY.md 自動更新

### Phase 3: 技能進化 (3-4 天)
- [ ] 實現 Skill 自動創建
- [ ] 建立 Skill 使用追蹤
- [ ] 實現 Skill 改進建議
- [ ] 建立 Skill 版本管理

### Phase 4: 搜索與優化 (2-3 天)
- [ ] 實現 FTS5 全文搜索
- [ ] 建立語義搜索 (可選)
- [ ] 優化性能和存儲
- [ ] 建立監控 Dashboard

---

## 📁 檔案結構

```
~/openclaw_workspace/
├── alfred_memory_system/           # AMS 主目錄
│   ├── __init__.py
│   ├── config.py                   # 配置管理
│   ├── database.py                 # 數據庫連接
│   │
│   ├── core/                       # 核心組件
│   │   ├── __init__.py
│   │   ├── context_monitor.py      # Context 監控
│   │   ├── memory_engine.py        # 記憶引擎
│   │   ├── skill_evolver.py        # 技能進化
│   │   └── session_search.py       # 會話搜索
│   │
│   ├── learning/                   # 學習模組
│   │   ├── __init__.py
│   │   ├── extractor.py            # 信息提取
│   │   ├── pattern_matcher.py      # 模式識別
│   │   └── validator.py            # 驗證器
│   │
│   ├── storage/                    # 存儲層
│   │   ├── __init__.py
│   │   ├── sqlite_store.py         # SQLite 存儲
│   │   └── vector_store.py         # 向量存儲 (可選)
│   │
│   ├── cli/                        # 命令行工具
│   │   ├── __init__.py
│   │   ├── ams_cli.py              # 主 CLI
│   │   └── commands/               # 子命令
│   │
│   └── data/                       # 數據目錄
│       ├── alfred_memory.db        # 主數據庫
│       ├── vector_index/           # 向量索引 (可選)
│       └── backups/                # 備份
│
├── skills/
│   └── alfred-memory/              # AMS Skill
│       ├── SKILL.md
│       └── scripts/
│           ├── memory_tool.py      # memory tool 實現
│           └── context_check.py    # context 檢查
│
└── scripts/
    └── ams_daemon.py               # 背景守護進程
```

---

## 🚀 使用方式

### 啟動 AMS
```powershell
# 初始化數據庫
python -m alfred_memory_system init

# 啟動背景監控
python scripts/ams_daemon.py start

# 檢查狀態
python -m alfred_memory_system status
```

### 在對話中使用
```python
# 自動監控 (每次對話後自動執行)
from alfred_memory_system import AMS

ams = AMS()
ams.process_session(session_id, messages)

# 手動檢查 Context
context_status = ams.context_monitor.check_context(messages)
print(f"Context Usage: {context_status['usage_percent']}%")

# 搜索記憶
memories = ams.memory_engine.search("TradingBot 參數")

# 搜索過去會話
results = ams.session_search.search("回測結果", time_range=("2026-04-01", "2026-04-08"))
```

### CLI 命令
```powershell
# 查看 Context 使用
ams context

# 查看記憶
ams memory list --category preference
ams memory add "用戶偏好使用深色主題"

# 搜索會話
ams search "TradingBot" --limit 5

# 查看 Skills
ams skill list
ams skill stats

# 手動觸發壓縮
ams compress

# 生成報告
ams report --days 7
```

---

## 📊 監控 Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                 Alfred Memory System Dashboard                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📊 Context Usage                                                │
│  ████████████████████░░░░░░░░░░  73.5% (94K/128K tokens)        │
│  Status: ⚠️  Warning (approaching 85% compression threshold)    │
│                                                                 │
│  🧠 Memory Statistics                                            │
│  ┌─────────────┬────────┬────────┬────────┐                     │
│  │ Category    │ Total  │ Hot    │ Cold   │                     │
│  ├─────────────┼────────┼────────┼────────┤                     │
│  │ User Profile│   12   │   8    │   4    │                     │
│  │ Environment │   23   │  15    │   8    │                     │
│  │ Preference  │   18   │  12    │   6    │                     │
│  │ Decision    │    9   │   6    │   3    │                     │
│  └─────────────┴────────┴────────┴────────┘                     │
│                                                                 │
│  🛠️ Skills                                                       │
│  Total: 45 | Auto-created: 12 | Most used: trading-bot (127x)   │
│                                                                 │
│  📈 Learning Activity (Last 7 Days)                              │
│  New memories: 23 | Patterns identified: 5 | Skills created: 2   │
│                                                                 │
│  🔍 Recent Searches                                              │
│  - "TradingBot 參數" (3 results)                                │
│  - "回測結果" (7 results)                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 安全考慮

1. **數據本地存儲**: 所有數據存儲在本地 SQLite，不上傳雲端
2. **敏感信息過濾**: 自動檢測和過濾 API keys、密碼等敏感信息
3. **訪問控制**: 記憶文件權限設置為僅當前用戶可讀
4. **備份機制**: 自動備份，防止數據丟失

---

## 📝 與現有系統整合

### 與 OpenClaw 整合
```python
# 在 AGENTS.md 啟動序列中添加
1. 讀取 SOUL.md
2. 讀取 USER.md
3. 讀取 MEMORY.md
4. 讀取 MEMORY_SYNC_PROTOCOL.md
5. 讀取 project-states/*.md
6. 讀取 memory/YYYY-MM-DD.md
7. **啟動 AMS Context Monitor** ← 新增
8. **加載相關記憶** ← 新增
9. 讀取 SKILL_PROTOCOL.md
```

### 與現有記憶系統整合
- **MEMORY.md**: AMS 自動更新，保持兼容
- **memory/YYYY-MM-DD.md**: AMS 自動生成和讀取
- **project-states/**: AMS 追蹤專案狀態變化

---

## 🎯 成功指標

| 指標 | 目標 | 測量方式 |
|------|------|----------|
| Context 監控準確率 | >90% | 與實際 token 使用比較 |
| 記憶提取準確率 | >80% | 用戶確認有用/無用 |
| Skill 創建接受率 | >70% | 用戶接受/拒絕比例 |
| 搜索相關性 | >85% | 前3結果包含目標信息 |
| 系統響應時間 | <100ms | 記憶檢索時間 |

---

*設計完成，等待靚仔指示開始實現。*
