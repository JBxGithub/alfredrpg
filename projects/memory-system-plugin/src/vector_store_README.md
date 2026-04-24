# 向量數據庫模組 - 使用說明

## 概述

`vector_store.py` 是記憶系統插件的核心組件，負責：
- ChromaDB 本地部署整合
- 文本嵌入（使用 sentence-transformers）
- 記憶存儲和語義檢索
- 記憶管理和維護

## 安裝依賴

```bash
# 核心依賴
pip install chromadb sentence-transformers

# 可選：使用 GPU 加速（如有 CUDA）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 快速開始

```python
from vector_store import VectorStore, create_vector_store

# 創建存儲實例
store = VectorStore()

# 存儲記憶
memory_id = store.store_memory(
    content="今天討論了交易策略優化...",
    session_key="session_001",
    topics=["交易策略", "系統優化"],
    decisions=["保留3個策略"],
    emotions="積極",
    priority="high"
)

# 語義搜索
results = store.search_similar("交易策略", n_results=5)
for r in results:
    print(f"{r['content']} (相似度: {1-r['distance']:.2f})")

# 獲取最近記憶
recent = store.get_recent_memories(n=10)
```

## 主要功能

### 1. 記憶存儲
- `store_memory()`: 存儲單條記憶，自動生成嵌入
- 支持主題標籤、決策記錄、情感狀態
- 自動時間戳記錄

### 2. 語義檢索
- `search_similar()`: 基於語義相似度搜索
- `search_by_topic()`: 按主題標籤搜索
- `get_recent_memories()`: 獲取最近記憶

### 3. 記憶管理
- `get_memory()`: 獲取特定記憶
- `delete_memory()`: 刪除記憶
- `clear_all()`: 清空所有記憶
- `backup()`: 備份數據庫
- `get_stats()`: 獲取統計信息

## 數據結構

### MemoryEntry
```python
{
    "id": "mem_20260407_224500_a1b2c3d4",
    "content": "記憶內容",
    "timestamp": "2026-04-07T22:45:00",
    "session_key": "session_001",
    "topics": ["交易策略", "系統優化"],
    "decisions": ["保留3個策略"],
    "emotions": "積極",
    "priority": "high",
    "metadata": {}
}
```

## 配置選項

```python
# 自定義配置
store = VectorStore(
    db_path="/path/to/vector_db",  # 數據庫路徑
    collection_name="memory_store",  # 集合名稱
    embedding_model="all-MiniLM-L6-v2"  # 嵌入模型
)
```

### 推薦的嵌入模型

| 模型 | 維度 | 速度 | 準確度 |
|------|------|------|--------|
| all-MiniLM-L6-v2 | 384 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| all-mpnet-base-v2 | 768 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## 存儲位置

默認存儲路徑：`~/openclaw_workspace/memory/vector_db`

## 備份與恢復

```python
# 備份
backup_path = store.backup()

# 恢復（手動）
import json
with open(backup_path, 'r') as f:
    data = json.load(f)
    for mem in data['memories']:
        store.store_memory(**mem['metadata'])
```

## 注意事項

1. **首次運行**: 會自動下載嵌入模型（約 100MB）
2. **內存使用**: ChromaDB 會在內存中緩存數據
3. **並發安全**: ChromaDB 支持多進程讀取，但寫入需要同步
4. **備份策略**: 建議定期調用 `backup()` 進行備份

## 故障排除

### ChromaDB 未安裝
如果沒有安裝 ChromaDB，會自動回退到內存存儲（數據不會持久化）

### 模型下載失敗
檢查網絡連接，或手動下載模型：
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
```

### 存儲空間不足
ChromaDB 數據會隨記憶數量增長，定期清理舊記憶或備份後刪除
