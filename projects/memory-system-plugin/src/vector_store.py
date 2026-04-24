"""
向量數據庫模組 - vector_store.py
負責記憶的向量存儲和語義檢索功能

功能：
1. ChromaDB 本地部署整合
2. 文本嵌入（使用 sentence-transformers）
3. 記憶存儲和語義檢索
4. 記憶管理和維護

作者: ClawTeam - VectorDB 工程師
日期: 2026-04-07
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

# 嘗試導入可選依賴
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


@dataclass
class MemoryEntry:
    """記憶條目數據類"""
    id: str
    content: str
    timestamp: str
    session_key: str
    topics: List[str]
    decisions: List[str]
    emotions: str
    priority: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """從字典創建"""
        return cls(**data)


class EmbeddingProvider:
    """文本嵌入提供者"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        初始化嵌入提供者
        
        Args:
            model_name: sentence-transformers 模型名稱
                       推薦: "all-MiniLM-L6-v2" (快速, 384維)
                       可選: "all-mpnet-base-v2" (更準確, 768維)
        """
        self.model_name = model_name
        self.model = None
        self.dimension = 384  # MiniLM 默認維度
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
                self.dimension = self.model.get_sentence_embedding_dimension()
                print(f"[VectorDB] 嵌入模型已載入: {model_name} (維度: {self.dimension})")
            except Exception as e:
                print(f"[VectorDB] 警告: 無法載入嵌入模型: {e}")
                self.model = None
        else:
            print("[VectorDB] 警告: sentence-transformers 未安裝，將使用簡單哈希嵌入")
    
    def embed(self, text: str) -> List[float]:
        """
        將文本轉換為向量嵌入
        
        Args:
            text: 輸入文本
            
        Returns:
            向量嵌入列表
        """
        if self.model is not None:
            try:
                embedding = self.model.encode(text, convert_to_list=True)
                return embedding
            except Exception as e:
                print(f"[VectorDB] 嵌入生成失敗: {e}")
                return self._fallback_embed(text)
        else:
            return self._fallback_embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成嵌入
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        if self.model is not None:
            try:
                embeddings = self.model.encode(texts, convert_to_list=True)
                return embeddings
            except Exception as e:
                print(f"[VectorDB] 批量嵌入生成失敗: {e}")
                return [self._fallback_embed(t) for t in texts]
        else:
            return [self._fallback_embed(t) for t in texts]
    
    def _fallback_embed(self, text: str) -> List[float]:
        """
        備用嵌入方法（簡單哈希）
        當 sentence-transformers 不可用時使用
        """
        # 使用 MD5 哈希生成偽嵌入（僅供測試）
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # 轉換為浮點數向量
        embedding = []
        for i in range(0, len(hash_bytes), 2):
            val = (hash_bytes[i] + hash_bytes[i+1] * 256) / 65535.0
            embedding.append(val)
        
        # 擴展到目標維度
        while len(embedding) < self.dimension:
            embedding.extend(embedding)
        
        return embedding[:self.dimension]


class VectorStore:
    """
    向量數據庫管理器
    基於 ChromaDB 實現記憶的存儲和語義檢索
    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        collection_name: str = "memory_store",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        初始化向量存儲
        
        Args:
            db_path: ChromaDB 存儲路徑，默認為 ~/openclaw_workspace/memory/vector_db
            collection_name: 集合名稱
            embedding_model: 嵌入模型名稱
        """
        # 設置數據庫路徑
        if db_path is None:
            home_dir = Path.home()
            db_path = home_dir / "openclaw_workspace" / "memory" / "vector_db"
        else:
            db_path = Path(db_path)
        
        self.db_path = db_path
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_provider = EmbeddingProvider(embedding_model)
        
        # 初始化數據庫
        self._init_db()
    
    def _init_db(self):
        """初始化 ChromaDB"""
        if not CHROMADB_AVAILABLE:
            print("[VectorDB] 警告: ChromaDB 未安裝，將使用內存存儲")
            self._init_memory_storage()
            return
        
        try:
            # 確保目錄存在
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 創建 ChromaDB 客戶端
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 獲取或創建集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # 使用餘弦相似度
            )
            
            count = self.collection.count()
            print(f"[VectorDB] ChromaDB 已初始化: {self.db_path}")
            print(f"[VectorDB] 集合 '{self.collection_name}' 已有 {count} 條記錄")
            
        except Exception as e:
            print(f"[VectorDB] ChromaDB 初始化失敗: {e}")
            print("[VectorDB] 回退到內存存儲")
            self._init_memory_storage()
    
    def _init_memory_storage(self):
        """初始化內存存儲（備用方案）"""
        self.memory_store: Dict[str, Dict] = {}
        print("[VectorDB] 內存存儲已初始化")
    
    def store_memory(
        self,
        content: str,
        session_key: str,
        topics: Optional[List[str]] = None,
        decisions: Optional[List[str]] = None,
        emotions: str = "",
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        存儲記憶
        
        Args:
            content: 記憶內容
            session_key: Session 標識
            topics: 主題標籤列表
            decisions: 決策列表
            emotions: 情感狀態
            priority: 優先級 (high/normal/low)
            metadata: 額外元數據
            
        Returns:
            記憶 ID
        """
        # 生成唯一 ID
        timestamp = datetime.now().isoformat()
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        # 創建記憶條目
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            timestamp=timestamp,
            session_key=session_key,
            topics=topics or [],
            decisions=decisions or [],
            emotions=emotions,
            priority=priority,
            metadata=metadata or {}
        )
        
        # 生成嵌入
        embedding = self.embedding_provider.embed(content)
        
        # 存儲到數據庫
        if self.collection is not None:
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    "timestamp": timestamp,
                    "session_key": session_key,
                    "topics": json.dumps(topics or []),
                    "decisions": json.dumps(decisions or []),
                    "emotions": emotions,
                    "priority": priority,
                    "metadata": json.dumps(metadata or {})
                }]
            )
        else:
            # 內存存儲
            self.memory_store[memory_id] = {
                "id": memory_id,
                "content": content,
                "embedding": embedding,
                "timestamp": timestamp,
                "session_key": session_key,
                "topics": topics or [],
                "decisions": decisions or [],
                "emotions": emotions,
                "priority": priority,
                "metadata": metadata or {}
            }
        
        print(f"[VectorDB] 記憶已存儲: {memory_id}")
        return memory_id
    
    def search_similar(
        self,
        query: str,
        n_results: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        語義搜索相似記憶
        
        Args:
            query: 搜索查詢
            n_results: 返回結果數量
            filter_dict: 過濾條件
            
        Returns:
            相似記憶列表
        """
        query_embedding = self.embedding_provider.embed(query)
        
        if self.collection is not None:
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=filter_dict
                )
                
                memories = []
                for i, memory_id in enumerate(results['ids'][0]):
                    memory = {
                        "id": memory_id,
                        "content": results['documents'][0][i],
                        "distance": results['distances'][0][i],
                        "metadata": self._parse_metadata(results['metadatas'][0][i])
                    }
                    memories.append(memory)
                
                return memories
                
            except Exception as e:
                print(f"[VectorDB] 搜索失敗: {e}")
                return []
        else:
            # 內存搜索（簡單線性搜索）
            return self._memory_search(query_embedding, n_results)
    
    def _memory_search(
        self,
        query_embedding: List[float],
        n_results: int
    ) -> List[Dict[str, Any]]:
        """內存存儲搜索"""
        import math
        
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            dot = sum(x*y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x*x for x in a))
            norm_b = math.sqrt(sum(x*x for x in b))
            return dot / (norm_a * norm_b) if norm_a and norm_b else 0
        
        scored_memories = []
        for memory_id, data in self.memory_store.items():
            similarity = cosine_similarity(query_embedding, data["embedding"])
            scored_memories.append((similarity, data))
        
        # 按相似度排序
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for similarity, data in scored_memories[:n_results]:
            results.append({
                "id": data["id"],
                "content": data["content"],
                "distance": 1 - similarity,  # 轉換為距離
                "metadata": {
                    "timestamp": data["timestamp"],
                    "session_key": data["session_key"],
                    "topics": data["topics"],
                    "decisions": data["decisions"],
                    "emotions": data["emotions"],
                    "priority": data["priority"]
                }
            })
        
        return results
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取特定記憶
        
        Args:
            memory_id: 記憶 ID
            
        Returns:
            記憶數據或 None
        """
        if self.collection is not None:
            try:
                result = self.collection.get(ids=[memory_id])
                if result and result['ids']:
                    return {
                        "id": result['ids'][0],
                        "content": result['documents'][0],
                        "metadata": self._parse_metadata(result['metadatas'][0])
                    }
            except Exception as e:
                print(f"[VectorDB] 獲取記憶失敗: {e}")
            return None
        else:
            return self.memory_store.get(memory_id)
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        刪除記憶
        
        Args:
            memory_id: 記憶 ID
            
        Returns:
            是否成功
        """
        if self.collection is not None:
            try:
                self.collection.delete(ids=[memory_id])
                print(f"[VectorDB] 記憶已刪除: {memory_id}")
                return True
            except Exception as e:
                print(f"[VectorDB] 刪除失敗: {e}")
                return False
        else:
            if memory_id in self.memory_store:
                del self.memory_store[memory_id]
                print(f"[VectorDB] 記憶已刪除: {memory_id}")
                return True
            return False
    
    def get_recent_memories(
        self,
        n: int = 10,
        session_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        獲取最近記憶
        
        Args:
            n: 返回數量
            session_key: 可選 Session 過濾
            
        Returns:
            記憶列表
        """
        if self.collection is not None:
            try:
                where_filter = {}
                if session_key:
                    where_filter["session_key"] = session_key
                
                results = self.collection.get(
                    where=where_filter if where_filter else None,
                    limit=n
                )
                
                memories = []
                for i, memory_id in enumerate(results['ids']):
                    memories.append({
                        "id": memory_id,
                        "content": results['documents'][i],
                        "metadata": self._parse_metadata(results['metadatas'][i])
                    })
                
                # 按時間戳排序
                memories.sort(
                    key=lambda x: x['metadata'].get('timestamp', ''),
                    reverse=True
                )
                
                return memories[:n]
                
            except Exception as e:
                print(f"[VectorDB] 獲取最近記憶失敗: {e}")
                return []
        else:
            # 內存存儲排序
            memories = sorted(
                self.memory_store.values(),
                key=lambda x: x['timestamp'],
                reverse=True
            )
            
            if session_key:
                memories = [m for m in memories if m['session_key'] == session_key]
            
            return [{"id": m["id"], "content": m["content"], "metadata": m} 
                    for m in memories[:n]]
    
    def search_by_topic(
        self,
        topic: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        按主題搜索記憶
        
        Args:
            topic: 主題關鍵詞
            n_results: 返回數量
            
        Returns:
            記憶列表
        """
        if self.collection is not None:
            try:
                # 獲取所有記憶並手動過濾
                results = self.collection.get()
                
                matching_memories = []
                for i, memory_id in enumerate(results['ids']):
                    metadata = self._parse_metadata(results['metadatas'][i])
                    topics = metadata.get('topics', [])
                    
                    if topic.lower() in [t.lower() for t in topics]:
                        matching_memories.append({
                            "id": memory_id,
                            "content": results['documents'][i],
                            "metadata": metadata
                        })
                
                return matching_memories[:n_results]
                
            except Exception as e:
                print(f"[VectorDB] 主題搜索失敗: {e}")
                return []
        else:
            matching = []
            for data in self.memory_store.values():
                if topic.lower() in [t.lower() for t in data.get('topics', [])]:
                    matching.append({
                        "id": data["id"],
                        "content": data["content"],
                        "metadata": data
                    })
            return matching[:n_results]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        獲取數據庫統計信息
        
        Returns:
            統計數據字典
        """
        if self.collection is not None:
            count = self.collection.count()
        else:
            count = len(self.memory_store)
        
        return {
            "total_memories": count,
            "db_path": str(self.db_path),
            "collection_name": self.collection_name,
            "embedding_dimension": self.embedding_provider.dimension,
            "embedding_model": self.embedding_provider.model_name if self.embedding_provider.model else "fallback",
            "storage_type": "chroma" if self.collection else "memory"
        }
    
    def _parse_metadata(self, metadata: Dict[str, str]) -> Dict[str, Any]:
        """解析元數據中的 JSON 字符串"""
        parsed = dict(metadata)
        for key in ['topics', 'decisions', 'metadata']:
            if key in parsed and isinstance(parsed[key], str):
                try:
                    parsed[key] = json.loads(parsed[key])
                except:
                    parsed[key] = []
        return parsed
    
    def backup(self, backup_path: Optional[str] = None) -> str:
        """
        備份數據庫
        
        Args:
            backup_path: 備份路徑
            
        Returns:
            備份文件路徑
        """
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.db_path.parent / f"backup_{timestamp}.json"
        else:
            backup_path = Path(backup_path)
        
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 獲取所有記憶
        if self.collection is not None:
            results = self.collection.get()
            memories = []
            for i, memory_id in enumerate(results['ids']):
                memories.append({
                    "id": memory_id,
                    "content": results['documents'][i],
                    "metadata": results['metadatas'][i]
                })
        else:
            memories = list(self.memory_store.values())
        
        # 保存為 JSON
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump({
                "backup_time": datetime.now().isoformat(),
                "collection_name": self.collection_name,
                "memories": memories
            }, f, ensure_ascii=False, indent=2)
        
        print(f"[VectorDB] 備份完成: {backup_path}")
        return str(backup_path)
    
    def clear_all(self) -> bool:
        """
        清空所有記憶（謹慎使用）
        
        Returns:
            是否成功
        """
        if self.collection is not None:
            try:
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                print("[VectorDB] 所有記憶已清空")
                return True
            except Exception as e:
                print(f"[VectorDB] 清空失敗: {e}")
                return False
        else:
            self.memory_store.clear()
            print("[VectorDB] 所有記憶已清空")
            return True


# 便捷函數

def create_vector_store(
    db_path: Optional[str] = None,
    collection_name: str = "memory_store"
) -> VectorStore:
    """
    創建向量存儲實例
    
    Args:
        db_path: 數據庫路徑
        collection_name: 集合名稱
        
    Returns:
        VectorStore 實例
    """
    return VectorStore(db_path=db_path, collection_name=collection_name)


def quick_store(content: str, session_key: str, **kwargs) -> str:
    """
    快速存儲記憶
    
    Args:
        content: 記憶內容
        session_key: Session 標識
        **kwargs: 其他參數
        
    Returns:
        記憶 ID
    """
    store = VectorStore()
    return store.store_memory(content=content, session_key=session_key, **kwargs)


def quick_search(query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """
    快速搜索記憶
    
    Args:
        query: 搜索查詢
        n_results: 返回數量
        
    Returns:
        記憶列表
    """
    store = VectorStore()
    return store.search_similar(query=query, n_results=n_results)


# 測試代碼
if __name__ == "__main__":
    print("=" * 60)
    print("VectorDB 測試")
    print("=" * 60)
    
    # 創建存儲實例
    store = VectorStore()
    
    # 顯示統計
    stats = store.get_stats()
    print(f"\n數據庫統計:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 測試存儲
    print("\n測試存儲記憶...")
    memory_id = store.store_memory(
        content="今天討論了交易策略優化，決定保留3個策略，清理2個策略",
        session_key="test_session_001",
        topics=["交易策略", "系統優化"],
        decisions=["保留3個策略", "清理2個策略"],
        emotions="積極、專注",
        priority="high"
    )
    
    # 測試搜索
    print("\n測試語義搜索...")
    results = store.search_similar("交易策略", n_results=3)
    for r in results:
        print(f"  - {r['content'][:50]}... (距離: {r['distance']:.4f})")
    
    # 測試主題搜索
    print("\n測試主題搜索...")
    results = store.search_by_topic("交易策略")
    for r in results:
        print(f"  - {r['content'][:50]}...")
    
    # 測試最近記憶
    print("\n測試獲取最近記憶...")
    results = store.get_recent_memories(n=5)
    for r in results:
        print(f"  - {r['content'][:50]}...")
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
