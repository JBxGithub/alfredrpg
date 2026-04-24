# 記憶系統插件 (Memory System Plugin)

一個為 OpenClaw 設計的智能記憶管理系統，自動解決 AI 對話中的上下文限制問題。

## 功能特性

- 🔍 **Context 監控**: 實時監控 Context 使用率，70% 預警，80% 自動觸發
- 🧠 **智能摘要**: 自動提取決策、行動項目、思考過程、情感脈絡
- 💾 **向量存儲**: 基於 ChromaDB 的語義記憶存儲和檢索
- 🔄 **記憶注入**: 新 Session 自動恢復相關記憶上下文
- 📊 **結構化輸出**: Markdown 和 JSON 雙格式摘要輸出

## 快速開始

### 安裝依賴

```bash
# 核心依賴
pip install chromadb sentence-transformers

# 可選依賴（用於備用嵌入）
pip install numpy
```

### 基本使用

```python
from src.main import create_memory_system

# 創建並初始化記憶系統
system = create_memory_system(
    session_id="my_session_001",
    warning_threshold=70.0,    # 70% 預警
    critical_threshold=80.0    # 80% 自動觸發
)

# 檢查 Context 使用情況
result = system.check_context(tokens_used=180000)
print(f"使用率: {result['usage_percentage']:.1f}%")
print(f"狀態: {result['status']}")
print(f"建議: {result['recommendation']}")
```

### 創建摘要

```python
# 對話文本
conversation = """
今天我們討論了交易策略優化。
決定保留3個核心策略，清理2個表現不佳的策略。
待完成：實盤部署、參數調整。
情感積極。
"""

# 生成摘要
summary = system.create_summary(
    conversation_text=conversation,
    title="策略優化討論"
)

print(f"摘要ID: {summary.id}")
print(f"主題: {summary.topics}")
print(f"決策數: {len(summary.decisions)}")
print(f"行動項目: {len(summary.action_items)}")
```

### 搜索記憶

```python
# 語義搜索
results = system.search_memories("交易策略", n_results=5)

for result in results:
    print(f"- {result['content'][:100]}...")
```

### 自動恢復上下文

```python
# 新 Session 啟動時自動恢復記憶
recovery_context = system.auto_recover_context(
    user_first_message="我想繼續優化交易策略"
)

print(recovery_context)
```

## 模組說明

### 1. Monitor (監控器)

監控 Context 使用率，實現預警和自動觸發機制。

```python
from src.monitor import create_monitor

monitor = create_monitor(
    session_id="session_001",
    warning_threshold=70.0,
    critical_threshold=80.0
)

# 註冊回調
def on_warning(metrics):
    print(f"預警: {metrics.usage_percentage:.1f}%")

def on_critical(metrics):
    print(f"危險: {metrics.usage_percentage:.1f}%")

monitor.register_callback(ContextStatus.WARNING, on_warning)
monitor.register_callback(ContextStatus.CRITICAL, on_critical)

# 檢查使用率
metrics = monitor.check_and_alert(tokens_used=180000)
```

### 2. Vector Store (向量存儲)

基於 ChromaDB 的語義記憶存儲和檢索。

```python
from src.vector_store import VectorStore

store = VectorStore(
    db_path="./vector_db",
    collection_name="my_memories"
)

# 存儲記憶
memory_id = store.store_memory(
    content="交易策略優化方案",
    session_key="session_001",
    topics=["交易策略", "優化"],
    decisions=["採用新策略"],
    emotions="積極"
)

# 語義搜索
results = store.search_similar("交易策略", n_results=5)
```

### 3. Summarizer (摘要生成器)

自動生成對話摘要，提取結構化信息。

```python
from src.summarizer import create_summarizer, quick_summarize

summarizer = create_summarizer()

# 生成摘要
summary = summarizer.generate_summary(
    session_id="session_001",
    conversation_text=conversation_text,
    title="會議摘要"
)

# 保存摘要
path = summarizer.save_summary(summary)

# 快速摘要
summary = quick_summarize(conversation_text, "session_001")
```

### 4. Injector (記憶注入器)

新 Session 自動恢復記憶上下文。

```python
from src.injector import create_memory_injector

injector = create_memory_injector()

# 獲取記憶上下文
context = injector.get_session_context(current_topic="交易策略")

# 自動恢復
recovery = injector.auto_recover_context(
    session_id="new_session",
    user_first_message="繼續討論策略"
)
```

## 配置

### 配置文件 (config.yaml)

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

### 代碼配置

```python
from src.main import MemorySystem, MemorySystemConfig
from pathlib import Path

config = MemorySystemConfig(
    base_path=Path.home() / "my_memory",
    warning_threshold=65.0,
    critical_threshold=75.0,
    embedding_model="all-mpnet-base-v2"
)

system = MemorySystem(config)
```

## 測試

### 運行所有測試

```bash
cd tests
python test_suite.py
```

### 運行特定測試

```python
# 在 Python 中運行
from tests.test_suite import run_tests
result = run_tests()
```

### 測試覆蓋

- ✅ Context 監控測試（70%預警/80%觸發）
- ✅ 向量存儲和語義檢索測試
- ✅ 摘要生成測試
- ✅ 記憶注入測試
- ✅ 完整流程整合測試

## 使用示例

### 示例 1: 完整工作流程

```python
from src.main import create_memory_system

# 1. 創建系統
system = create_memory_system("session_001")

# 2. 模擬對話過程中檢查 Context
result = system.check_context(tokens_used=180000)
if result['status'] == 'warning':
    print("⚠️ Context 使用率較高，建議準備切換 Session")

# 3. 對話結束，生成摘要
conversation = """
今天我們討論了：
1. 交易策略優化方案
2. 決定保留3個核心策略
3. 待完成：實盤部署
"""

summary = system.create_summary(conversation, "策略討論")

# 4. 關閉系統
system.shutdown()

# 5. 新 Session 啟動，恢復記憶
new_system = create_memory_system("session_002")
context = new_system.auto_recover_context("繼續優化策略")
print(context)  # 顯示相關歷史記憶
```

### 示例 2: 監控警報

```python
from src.monitor import create_monitor, ContextStatus

monitor = create_monitor("session_001")

# 自定義警報處理
def on_critical(metrics):
    print(f"🚨 Context 使用率達 {metrics.usage_percentage:.1f}%!")
    print("自動生成摘要並建議切換 Session...")
    
    # 這裡可以調用摘要生成和存儲
    # summary = system.create_summary(...)

monitor.register_callback(ContextStatus.CRITICAL, on_critical)

# 模擬 Context 使用
for tokens in [100000, 180000, 210000]:
    metrics = monitor.check_and_alert(tokens)
    print(f"Tokens: {tokens}, Status: {metrics.status.value}")
```

### 示例 3: 批量記憶管理

```python
from src.vector_store import VectorStore

store = VectorStore()

# 批量存儲
memories = [
    {"content": "策略A分析", "topics": ["策略A"]},
    {"content": "策略B分析", "topics": ["策略B"]},
    {"content": "系統架構設計", "topics": ["架構"]},
]

for mem in memories:
    store.store_memory(
        content=mem["content"],
        session_key="batch_session",
        topics=mem["topics"]
    )

# 主題搜索
results = store.search_by_topic("策略", n_results=10)
print(f"找到 {len(results)} 條相關記憶")

# 獲取統計
stats = store.get_stats()
print(f"總記憶數: {stats['total_memories']}")
```

## 存儲結構

```
~/openclaw_workspace/memory/
├── summaries/               # 摘要存儲
│   ├── summary_20260408_120000_xxx.json  # JSON 格式
│   └── summary_20260408_120000_xxx.md    # Markdown 格式
├── vector_db/               # ChromaDB 數據
│   └── chroma.sqlite3
└── vectors/                 # 向量緩存
    └── memory_cache.json
```

## 依賴說明

### 必需依賴
- `chromadb`: 向量數據庫
- `sentence-transformers`: 文本嵌入

### 可選依賴
- `numpy`: 數值計算
- `torch`: 深度學習框架（sentence-transformers 需要）

### 備用方案
如果 sentence-transformers 不可用，系統會自動使用簡單的哈希嵌入作為備用。

## 故障排除

### 問題 1: ChromaDB 初始化失敗

**解決方案**:
```python
# 使用內存存儲作為備用
store = VectorStore(db_path=None)  # 不指定路徑使用內存存儲
```

### 問題 2: 嵌入模型加載緩慢

**解決方案**:
```python
# 首次運行會下載模型，後續會緩存
# 可以預先下載模型
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
```

### 問題 3: 記憶搜索無結果

**解決方案**:
```python
# 檢查是否有存儲的記憶
stats = store.get_stats()
print(f"總記憶數: {stats['total_memories']}")

# 調整搜索參數
results = store.search_similar("查詢", n_results=10)  # 增加返回數量
```

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 許可證

MIT License

## 作者

ClawTeam - Lead Developer

## 更新日誌

### v1.0.0 (2026-04-08)
- 初始版本發布
- 實現核心功能：監控、存儲、摘要、注入
- 完整測試覆蓋
