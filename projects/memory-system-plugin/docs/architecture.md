# 記憶系統插件 - 架構文檔

## 概述

記憶系統插件是一個為 OpenClaw 設計的智能記憶管理系統，用於解決 AI 對話中的上下文限制問題。當 Context 使用率達到閾值時，系統自動生成摘要、存儲到向量數據庫，並在新 Session 中恢復記憶上下文。

## 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        Memory System Plugin                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Monitor    │  │  Summarizer  │  │   Injector   │           │
│  │   Module     │  │   Module     │  │   Module     │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌──────────────────────────────────────────────────────┐      │
│  │                  Main Controller                      │      │
│  │              (MemorySystem Class)                     │      │
│  └──────────────────────┬───────────────────────────────┘      │
│                         │                                       │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              Vector Store (ChromaDB)                  │      │
│  │         + Embedding (sentence-transformers)           │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 核心模組

### 1. Monitor Module (monitor.py)

**職責**: 監控 Context 使用率，實現預警和自動觸發機制

**核心類**:
- `ContextMonitor`: 主監控器類
- `ContextMetrics`: Context 使用指標數據類
- `AlertConfig`: 預警配置
- `SessionState`: Session 狀態

**關鍵功能**:
- 實時計算 Context 使用率
- 70% 預警通知
- 80% 自動觸發 Session 切換流程
- 歷史數據記錄和趨勢分析

**觸發機制**:
```python
if usage_percentage >= 80%:
    trigger_critical_alert()  # 自動觸發
elif usage_percentage >= 70%:
    trigger_warning_alert()   # 預警通知
```

### 2. Vector Store Module (vector_store.py)

**職責**: 記憶的向量存儲和語義檢索

**核心類**:
- `VectorStore`: 向量數據庫管理器
- `EmbeddingProvider`: 文本嵌入提供者
- `MemoryEntry`: 記憶條目數據類

**技術棧**:
- **ChromaDB**: 本地向量數據庫
- **sentence-transformers**: 文本嵌入模型 (all-MiniLM-L6-v2)

**關鍵功能**:
- 記憶存儲 (store_memory)
- 語義搜索 (search_similar)
- 主題搜索 (search_by_topic)
- 最近記憶獲取 (get_recent_memories)

**數據結構**:
```python
{
    "id": "mem_20260408_120000_abc123",
    "content": "記憶內容",
    "timestamp": "2026-04-08T12:00:00",
    "session_key": "session_001",
    "topics": ["交易策略", "優化"],
    "decisions": ["保留3個策略"],
    "emotions": "積極",
    "priority": "high",
    "metadata": {...}
}
```

### 3. Summarizer Module (summarizer.py)

**職責**: 自動生成對話摘要，提取結構化信息

**核心類**:
- `Summarizer`: 摘要生成器主類
- `ContentAnalyzer`: 內容分析器
- `ConversationSummary`: 對話摘要數據類
- `Decision`, `ActionItem`, `ThinkingProcess`, `EmotionalContext`: 結構化數據類

**提取內容**:
- **決策**: 關鍵決定和原因
- **行動項目**: 待完成項目和已完成項目
- **思考過程**: 問題分析、替代方案
- **情感脈絡**: 情緒狀態和觸發因素
- **主題標籤**: 自動分類

**摘要類型**:
- `SESSION`: Session 摘要
- `DAILY`: 每日摘要
- `TOPIC`: 主題摘要
- `DECISION`: 決策摘要

### 4. Injector Module (injector.py)

**職責**: 新 Session 記憶自動讀取、語義檢索和上下文注入

**核心類**:
- `MemoryInjector`: 記憶注入模組主類
- `MemoryStore`: 記憶存儲管理器
- `SemanticSearcher`: 語義搜索器
- `ContextInjector`: 上下文注入器
- `SessionContext`: Session 上下文數據結構

**關鍵功能**:
- 自動記憶恢復 (auto_recover_context)
- 語義搜索 (search)
- 上下文注入 (generate_injection_prompt)
- 快速摘要 (generate_quick_summary)

### 5. Main Module (main.py)

**職責**: 整合所有模組，提供統一 API

**核心類**:
- `MemorySystem`: 記憶系統主類
- `MemorySystemConfig`: 系統配置
- `MemorySystemAPI`: RESTful API 接口

**配置選項**:
```python
@dataclass
class MemorySystemConfig:
    base_path: Path                    # 基礎路徑
    warning_threshold: float = 70.0    # 預警閾值
    critical_threshold: float = 80.0   # 危險閾值
    check_interval: int = 300          # 檢測間隔
    collection_name: str = "memory_store"
    embedding_model: str = "all-MiniLM-L6-v2"
    auto_summarize: bool = True
    auto_inject: bool = True
```

## 數據流

### 1. 記憶存儲流程

```
對話文本
    ↓
Summarizer.generate_summary()
    ↓
提取: 決策、行動項目、主題、情感
    ↓
VectorStore.store_memory()
    ↓
生成嵌入向量 (sentence-transformers)
    ↓
存儲到 ChromaDB
```

### 2. 記憶恢復流程

```
新 Session 啟動
    ↓
Injector.auto_recover_context()
    ↓
基於用戶第一條消息搜索
    ↓
SemanticSearcher.search()
    ↓
VectorStore.search_similar()
    ↓
格式化記憶上下文
    ↓
注入到新 Session
```

### 3. Context 監控流程

```
定期檢測 / 手動檢查
    ↓
Monitor.check_and_alert(tokens_used)
    ↓
計算使用率 percentage
    ↓
判斷狀態: NORMAL / WARNING / CRITICAL
    ↓
觸發相應回調
    ↓
CRITICAL → 自動生成摘要 → 存儲 → 建議切換 Session
```

## 文件結構

```
memory-system-plugin/
├── src/
│   ├── main.py              # 主程序，整合所有模組
│   ├── monitor.py           # Context 監控
│   ├── vector_store.py      # 向量存儲
│   ├── summarizer.py        # 摘要生成
│   ├── injector.py          # 記憶注入
│   └── data/                # 數據存儲
│       └── monitor/         # 監控數據
├── tests/
│   └── test_suite.py        # 完整測試套件
├── docs/
│   └── architecture.md      # 架構文檔
├── config.yaml              # 配置文件
└── README.md                # 使用說明
```

## 存儲結構

```
~/openclaw_workspace/memory/
├── summaries/               # 摘要存儲
│   ├── summary_20260408_120000_xxx.json
│   └── summary_20260408_120000_xxx.md
├── vector_db/               # ChromaDB 數據
│   └── chroma.sqlite3
└── vectors/                 # 向量緩存
    └── memory_cache.json
```

## API 接口

### MemorySystem 類

```python
# 初始化
system = MemorySystem(config)
system.initialize(session_id)

# Context 檢查
result = system.check_context(tokens_used)

# 創建摘要
summary = system.create_summary(conversation_text, title)

# 搜索記憶
results = system.search_memories(query, n_results=5)

# 獲取記憶上下文
context = system.get_memory_context(query)

# 自動恢復上下文
recovery = system.auto_recover_context(user_first_message)

# 獲取系統狀態
status = system.get_system_status()

# 關閉系統
system.shutdown()
```

### 便捷函數

```python
# 快速創建系統
system = create_memory_system(session_id)

# 快速初始化
system = quick_init(session_id)

# 快速生成摘要
summary = quick_summarize(conversation_text, session_id)

# 快速恢復上下文
context = quick_recover_context(user_message)
```

## 配置說明

### config.yaml

```yaml
memory_system:
  # 路徑配置
  base_path: "~/openclaw_workspace/memory"
  
  # Context 監控配置
  warning_threshold: 70.0      # 70% 預警
  critical_threshold: 80.0     # 80% 自動觸發
  check_interval: 300          # 每 5 分鐘檢測
  
  # 向量數據庫配置
  collection_name: "memory_store"
  embedding_model: "all-MiniLM-L6-v2"
  
  # 摘要配置
  auto_summarize: true
  summary_on_critical: true
  
  # 記憶注入配置
  auto_inject: true
  max_inject_memories: 3
```

## 性能考量

### 嵌入生成
- 模型: all-MiniLM-L6-v2 (384維)
- 性能: ~1000 tokens/秒
- 備用: 哈希嵌入（當 sentence-transformers 不可用時）

### 向量搜索
- 使用 ChromaDB 的 HNSW 索引
- 餘弦相似度計算
- 典型搜索延遲: < 100ms (1000條記錄)

### 存儲優化
- 內存緩存熱數據
- 定期持久化到磁盤
- 自動清理過期數據

## 擴展性

### 支持的擴展
1. **自定義嵌入模型**: 替換 sentence-transformers
2. **遠程向量數據庫**: 支持 Pinecone, Weaviate 等
3. **多模態記憶**: 圖像、音頻存儲
4. **分佈式部署**: 多實例共享記憶存儲

### 集成點
- OpenClaw API 集成
- Webhook 通知
- 自定義回調函數
- 插件系統集成

## 安全考量

1. **數據隱私**: 本地存儲，不上傳雲端
2. **訪問控制**: 基於文件系統權限
3. **數據加密**: 可選的靜態數據加密
4. **備份機制**: 自動備份到指定路徑

## 故障排除

### 常見問題

1. **ChromaDB 初始化失敗**
   - 檢查磁盤空間
   - 檢查文件權限
   - 回退到內存存儲

2. **嵌入模型加載失敗**
   - 自動使用哈希嵌入備用
   - 提示用戶安裝 sentence-transformers

3. **記憶搜索無結果**
   - 檢查是否有存儲的記憶
   - 調整搜索閾值
   - 檢查時間範圍

## 版本歷史

- **v1.0.0** (2026-04-08)
  - 初始版本
  - 實現核心功能: 監控、存儲、摘要、注入
  - 完整測試覆蓋

## 參考資料

- [ChromaDB 文檔](https://docs.trychroma.com/)
- [sentence-transformers](https://www.sbert.net/)
- [OpenClaw 文檔](https://openclaw.ai/docs)
