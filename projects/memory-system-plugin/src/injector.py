"""
記憶注入模組 (Memory Injector Module)
負責新 Session 記憶自動讀取、語義檢索和上下文注入

Author: ClawTeam - Injector
Date: 2026-04-07
Version: 1.0.0
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import hashlib


@dataclass
class MemoryEntry:
    """記憶條目數據結構"""
    id: str
    timestamp: str
    session_key: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_score: float = 0.0
    
    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MemoryEntry':
        """從字典創建實例"""
        return cls(**data)


@dataclass
class SessionContext:
    """Session 上下文數據結構"""
    session_id: str
    start_time: str
    context_usage: float = 0.0
    tokens_used: int = 0
    tokens_remaining: int = 0
    summary: str = ""
    decisions: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    emotions: str = ""
    next_continue: str = ""


class MemoryStore:
    """
    記憶存儲管理器
    負責記憶的存儲、讀取和基本檢索
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化記憶存儲
        
        Args:
            base_path: 記憶存儲基礎路徑，默認為 workspace/memory/
        """
        if base_path is None:
            self.base_path = Path(os.path.expanduser("~")) / "openclaw_workspace" / "memory"
        else:
            self.base_path = Path(base_path)
        
        self.summaries_path = self.base_path / "summaries"
        self.vectors_path = self.base_path / "vectors"
        
        # 確保目錄存在
        self.summaries_path.mkdir(parents=True, exist_ok=True)
        self.vectors_path.mkdir(parents=True, exist_ok=True)
        
        # 記憶緩存
        self._memory_cache: Dict[str, MemoryEntry] = {}
        self._load_cache()
    
    def _load_cache(self):
        """加載記憶緩存"""
        cache_file = self.vectors_path / "memory_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry_data in data.get('memories', []):
                        entry = MemoryEntry.from_dict(entry_data)
                        self._memory_cache[entry.id] = entry
            except Exception as e:
                print(f"[MemoryStore] 緩存加載失敗: {e}")
    
    def _save_cache(self):
        """保存記憶緩存"""
        cache_file = self.vectors_path / "memory_cache.json"
        try:
            data = {
                'last_updated': datetime.now().isoformat(),
                'memories': [entry.to_dict() for entry in self._memory_cache.values()]
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MemoryStore] 緩存保存失敗: {e}")
    
    def save_memory(self, entry: MemoryEntry) -> bool:
        """
        保存記憶條目
        
        Args:
            entry: 記憶條目
            
        Returns:
            是否保存成功
        """
        try:
            # 保存到緩存
            self._memory_cache[entry.id] = entry
            
            # 保存到文件
            memory_file = self.vectors_path / f"{entry.id}.json"
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(entry.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 更新緩存索引
            self._save_cache()
            
            return True
        except Exception as e:
            print(f"[MemoryStore] 保存記憶失敗: {e}")
            return False
    
    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """
        獲取指定記憶
        
        Args:
            memory_id: 記憶ID
            
        Returns:
            記憶條目或 None
        """
        # 先從緩存查找
        if memory_id in self._memory_cache:
            return self._memory_cache[memory_id]
        
        # 從文件加載
        memory_file = self.vectors_path / f"{memory_id}.json"
        if memory_file.exists():
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    entry = MemoryEntry.from_dict(data)
                    self._memory_cache[memory_id] = entry
                    return entry
            except Exception as e:
                print(f"[MemoryStore] 讀取記憶失敗: {e}")
        
        return None
    
    def get_all_memories(self, limit: Optional[int] = None) -> List[MemoryEntry]:
        """
        獲取所有記憶
        
        Args:
            limit: 限制數量，默認無限制
            
        Returns:
            記憶條目列表
        """
        memories = list(self._memory_cache.values())
        
        # 按時間排序（最新的在前）
        memories.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            memories = memories[:limit]
        
        return memories
    
    def get_recent_memories(self, hours: int = 24, limit: int = 10) -> List[MemoryEntry]:
        """
        獲取最近時間範圍內的記憶
        
        Args:
            hours: 時間範圍（小時）
            limit: 最大數量
            
        Returns:
            記憶條目列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_memories = []
        for entry in self._memory_cache.values():
            try:
                entry_time = datetime.fromisoformat(entry.timestamp)
                if entry_time >= cutoff_time:
                    recent_memories.append(entry)
            except:
                continue
        
        # 按時間排序
        recent_memories.sort(key=lambda x: x.timestamp, reverse=True)
        
        return recent_memories[:limit]
    
    def search_by_topics(self, topics: List[str], limit: int = 5) -> List[MemoryEntry]:
        """
        按主題搜索記憶
        
        Args:
            topics: 主題列表
            limit: 最大數量
            
        Returns:
            匹配的記憶條目列表
        """
        matched_memories = []
        
        for entry in self._memory_cache.values():
            entry_topics = entry.metadata.get('topics', [])
            # 計算匹配度
            match_count = sum(1 for t in topics if t.lower() in [et.lower() for et in entry_topics])
            if match_count > 0:
                entry.relevance_score = match_count / len(topics)
                matched_memories.append(entry)
        
        # 按相關度排序
        matched_memories.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return matched_memories[:limit]
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        刪除記憶
        
        Args:
            memory_id: 記憶ID
            
        Returns:
            是否刪除成功
        """
        try:
            # 從緩存刪除
            if memory_id in self._memory_cache:
                del self._memory_cache[memory_id]
            
            # 從文件刪除
            memory_file = self.vectors_path / f"{memory_id}.json"
            if memory_file.exists():
                memory_file.unlink()
            
            # 更新緩存索引
            self._save_cache()
            
            return True
        except Exception as e:
            print(f"[MemoryStore] 刪除記憶失敗: {e}")
            return False


class SemanticSearcher:
    """
    語義搜索器
    基於關鍵詞和簡單語義相似度的記憶檢索
    """
    
    def __init__(self, memory_store: MemoryStore):
        """
        初始化語義搜索器
        
        Args:
            memory_store: 記憶存儲實例
        """
        self.memory_store = memory_store
        
        # 簡單的關鍵詞權重映射
        self.topic_keywords = {
            '交易': ['trading', '策略', 'strategy', '買入', '賣出', 'buy', 'sell', 'order'],
            '程式': ['code', 'programming', 'python', '開發', 'debug', 'error', 'bug'],
            '財務': ['finance', 'money', '投資', 'investment', 'budget', '預算'],
            '系統': ['system', '架構', 'architecture', 'config', 'configuration'],
            '數據': ['data', 'database', 'sql', 'query', '分析', 'analysis'],
            '自動化': ['automation', '自動', 'script', '腳本', 'cron', 'schedule'],
        }
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        從文本中提取關鍵詞
        
        Args:
            text: 輸入文本
            
        Returns:
            關鍵詞列表
        """
        # 簡單的關鍵詞提取（中文和英文）
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
        
        # 過濾常見停用詞
        stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', 'the', 'is', 'a', 'an', 'and', 'or', 'but'}
        keywords = [w for w in words if w not in stopwords and len(w) > 1]
        
        return keywords
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        計算兩段文本的相似度（簡單實現）
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分數 (0.0 - 1.0)
        """
        # 提取關鍵詞
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Jaccard 相似度
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)
        
        return intersection / union if union > 0 else 0.0
    
    def search(self, query: str, limit: int = 5, 
               time_range_hours: Optional[int] = None) -> List[MemoryEntry]:
        """
        語義搜索記憶
        
        Args:
            query: 搜索查詢
            limit: 最大結果數
            time_range_hours: 時間範圍限制（小時）
            
        Returns:
            相關記憶列表
        """
        # 獲取記憶範圍
        if time_range_hours:
            memories = self.memory_store.get_recent_memories(time_range_hours, limit=100)
        else:
            memories = self.memory_store.get_all_memories(limit=100)
        
        # 計算相似度
        results = []
        for entry in memories:
            # 綜合相似度計算
            content_sim = self.calculate_similarity(query, entry.content)
            
            # 主題匹配
            topics_text = ' '.join(entry.metadata.get('topics', []))
            topic_sim = self.calculate_similarity(query, topics_text) * 1.5  # 主題權重更高
            
            # 決策內容匹配
            decisions_text = ' '.join(entry.metadata.get('decisions', []))
            decision_sim = self.calculate_similarity(query, decisions_text) * 1.3
            
            # 綜合分數
            entry.relevance_score = max(content_sim, topic_sim, decision_sim)
            
            if entry.relevance_score > 0.1:  # 閾值過濾
                results.append(entry)
        
        # 按相關度排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:limit]
    
    def search_by_session_context(self, session_context: SessionContext, 
                                   limit: int = 5) -> List[MemoryEntry]:
        """
        基於 Session 上下文搜索相關記憶
        
        Args:
            session_context: Session 上下文
            limit: 最大結果數
            
        Returns:
            相關記憶列表
        """
        # 構建搜索查詢
        query_parts = []
        
        # 加入主題
        if session_context.topics:
            query_parts.extend(session_context.topics)
        
        # 加入摘要內容
        if session_context.summary:
            query_parts.append(session_context.summary[:200])
        
        # 加入待完成項目
        if session_context.action_items:
            query_parts.extend(session_context.action_items)
        
        query = ' '.join(query_parts)
        
        return self.search(query, limit=limit)


class ContextInjector:
    """
    上下文注入器
    負責生成記憶上下文注入格式
    """
    
    def __init__(self, memory_store: MemoryStore, searcher: SemanticSearcher):
        """
        初始化上下文注入器
        
        Args:
            memory_store: 記憶存儲實例
            searcher: 語義搜索器實例
        """
        self.memory_store = memory_store
        self.searcher = searcher
    
    def generate_injection_prompt(self, current_topic: Optional[str] = None,
                                   session_context: Optional[SessionContext] = None,
                                   max_memories: int = 3) -> str:
        """
        生成記憶注入提示
        
        Args:
            current_topic: 當前對話主題
            session_context: 當前 Session 上下文
            max_memories: 最大記憶數量
            
        Returns:
            格式化的記憶注入提示
        """
        # 搜索相關記憶
        if current_topic:
            relevant_memories = self.searcher.search(current_topic, limit=max_memories)
        elif session_context:
            relevant_memories = self.searcher.search_by_session_context(session_context, limit=max_memories)
        else:
            # 默認獲取最近記憶
            relevant_memories = self.memory_store.get_recent_memories(hours=48, limit=max_memories)
        
        # 調試輸出
        print(f"[ContextInjector] 找到 {len(relevant_memories)} 條相關記憶")
        
        if not relevant_memories:
            return self._generate_empty_prompt()
        
        # 構建注入提示
        prompt_parts = [
            "[系統提示: 記憶恢復]",
            "",
            "根據之前的對話記錄，以下是相關背景：",
            ""
        ]
        
        for i, memory in enumerate(relevant_memories, 1):
            # 格式化時間
            try:
                mem_time = datetime.fromisoformat(memory.timestamp)
                time_str = mem_time.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = memory.timestamp
            
            prompt_parts.append(f"## 對話記錄 {i} [{time_str}]")
            prompt_parts.append("")
            
            # 摘要內容
            if memory.content:
                # 限制內容長度
                content = memory.content[:500] + "..." if len(memory.content) > 500 else memory.content
                prompt_parts.append(f"**摘要**: {content}")
                prompt_parts.append("")
            
            # 關鍵決策
            decisions = memory.metadata.get('decisions', [])
            if decisions:
                prompt_parts.append("**關鍵決策**:")
                for decision in decisions[:3]:  # 最多3個決策
                    prompt_parts.append(f"- {decision}")
                prompt_parts.append("")
            
            # 待完成項目
            action_items = memory.metadata.get('action_items', [])
            if action_items:
                pending = [item for item in action_items if not item.startswith('✅')]
                if pending:
                    prompt_parts.append("**待完成項目**:")
                    for item in pending[:3]:  # 最多3個待完成
                        prompt_parts.append(f"- {item}")
                    prompt_parts.append("")
            
            # 主題標籤
            topics = memory.metadata.get('topics', [])
            if topics:
                prompt_parts.append(f"**主題**: {', '.join(topics)}")
                prompt_parts.append("")
            
            prompt_parts.append("---")
            prompt_parts.append("")
        
        # 添加繼續提示
        prompt_parts.append("基於以上背景，請繼續對話。")
        prompt_parts.append("")
        
        return "\n".join(prompt_parts)
    
    def _generate_empty_prompt(self) -> str:
        """生成空記憶提示"""
        return """[系統提示: 記憶恢復]

暫無相關歷史記錄。這是一個新的對話開始。

請繼續對話。
"""
    
    def generate_quick_summary(self, hours: int = 24) -> str:
        """
        生成快速摘要
        
        Args:
            hours: 時間範圍（小時）
            
        Returns:
            快速摘要文本
        """
        memories = self.memory_store.get_recent_memories(hours=hours, limit=10)
        
        if not memories:
            return "過去 {} 小時內暫無記錄。".format(hours)
        
        summary_parts = [f"## 過去 {hours} 小時摘要", ""]
        
        # 收集所有決策和待辦事項
        all_decisions = []
        all_pending = []
        all_topics = set()
        
        for memory in memories:
            all_decisions.extend(memory.metadata.get('decisions', []))
            action_items = memory.metadata.get('action_items', [])
            all_pending.extend([item for item in action_items if not item.startswith('✅')])
            all_topics.update(memory.metadata.get('topics', []))
        
        # 主題
        if all_topics:
            summary_parts.append(f"**涉及主題**: {', '.join(list(all_topics)[:5])}")
            summary_parts.append("")
        
        # 關鍵決策
        if all_decisions:
            summary_parts.append("**關鍵決策**:")
            for decision in all_decisions[:5]:
                summary_parts.append(f"- {decision}")
            summary_parts.append("")
        
        # 待完成項目
        if all_pending:
            summary_parts.append("**待完成項目**:")
            for item in all_pending[:5]:
                summary_parts.append(f"- {item}")
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    def inject_to_session(self, session_id: str, 
                          current_topic: Optional[str] = None) -> str:
        """
        注入記憶到 Session
        
        Args:
            session_id: Session ID
            current_topic: 當前主題
            
        Returns:
            注入的上下文文本
        """
        # 這裡可以擴展為與 OpenClaw API 集成
        # 目前返回格式化的注入文本
        
        prompt = self.generate_injection_prompt(current_topic=current_topic)
        
        # 記錄注入操作
        print(f"[ContextInjector] 已為 Session {session_id[:30]}... 注入記憶上下文")
        
        return prompt


class MemoryInjector:
    """
    記憶注入模組主類
    整合所有功能，提供統一接口
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化記憶注入模組
        
        Args:
            base_path: 記憶存儲基礎路徑
        """
        self.memory_store = MemoryStore(base_path)
        self.searcher = SemanticSearcher(self.memory_store)
        self.injector = ContextInjector(self.memory_store, self.searcher)
        
        print(f"[MemoryInjector] 記憶注入模組已初始化")
        print(f"[MemoryInjector] 存儲路徑: {self.memory_store.base_path}")
        print(f"[MemoryInjector] 已加載 {len(self.memory_store._memory_cache)} 條記憶")
    
    def save_session_summary(self, session_context: SessionContext) -> bool:
        """
        保存 Session 摘要
        
        Args:
            session_context: Session 上下文
            
        Returns:
            是否保存成功
        """
        # 生成記憶ID
        memory_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 構建記憶條目
        entry = MemoryEntry(
            id=memory_id,
            timestamp=datetime.now().isoformat(),
            session_key=session_context.session_id,
            content=session_context.summary,
            metadata={
                'topics': session_context.topics,
                'decisions': session_context.decisions,
                'action_items': session_context.action_items,
                'emotions': session_context.emotions,
                'next_continue': session_context.next_continue,
                'context_usage': session_context.context_usage,
                'tokens_used': session_context.tokens_used
            }
        )
        
        return self.memory_store.save_memory(entry)
    
    def get_session_context(self, current_topic: Optional[str] = None,
                           session_id: Optional[str] = None) -> str:
        """
        獲取 Session 上下文（用於新 Session 啟動）
        
        Args:
            current_topic: 當前對話主題
            session_id: 當前 Session ID
            
        Returns:
            格式化的上下文文本
        """
        return self.injector.generate_injection_prompt(
            current_topic=current_topic
        )
    
    def search_memories(self, query: str, limit: int = 5) -> List[MemoryEntry]:
        """
        搜索記憶
        
        Args:
            query: 搜索查詢
            limit: 最大結果數
            
        Returns:
            記憶條目列表
        """
        return self.searcher.search(query, limit=limit)
    
    def get_recent_context(self, hours: int = 24) -> str:
        """
        獲取最近上下文摘要
        
        Args:
            hours: 時間範圍（小時）
            
        Returns:
            摘要文本
        """
        return self.injector.generate_quick_summary(hours=hours)
    
    def auto_recover_context(self, session_id: str, 
                             user_first_message: str) -> str:
        """
        自動恢復上下文（新 Session 啟動時調用）
        
        Args:
            session_id: 新 Session ID
            user_first_message: 用戶第一條消息
            
        Returns:
            完整的記憶注入上下文
        """
        print(f"[MemoryInjector] 正在為新 Session 恢復上下文...")
        
        # 基於用戶第一條消息搜索相關記憶
        context = self.get_session_context(
            current_topic=user_first_message,
            session_id=session_id
        )
        
        # 添加自動恢復標記
        header = """[系統提示: 自動記憶恢復]

檢測到新 Session 啟動，已自動檢索相關歷史記憶。

"""
        
        return header + context


# ==================== 便捷函數 ====================

def create_memory_injector(base_path: Optional[str] = None) -> MemoryInjector:
    """
    創建記憶注入器實例（便捷函數）
    
    Args:
        base_path: 記憶存儲基礎路徑
        
    Returns:
        MemoryInjector 實例
    """
    return MemoryInjector(base_path)


def quick_save_summary(session_id: str, summary: str, 
                       topics: List[str] = None,
                       decisions: List[str] = None,
                       action_items: List[str] = None,
                       base_path: Optional[str] = None) -> bool:
    """
    快速保存 Session 摘要（便捷函數）
    
    Args:
        session_id: Session ID
        summary: 摘要內容
        topics: 主題列表
        decisions: 決策列表
        action_items: 行動項目列表
        base_path: 存儲路徑
        
    Returns:
        是否保存成功
    """
    injector = create_memory_injector(base_path)
    
    context = SessionContext(
        session_id=session_id,
        start_time=datetime.now().isoformat(),
        summary=summary,
        topics=topics or [],
        decisions=decisions or [],
        action_items=action_items or []
    )
    
    return injector.save_session_summary(context)


def quick_recover_context(user_message: str, 
                          session_id: Optional[str] = None,
                          base_path: Optional[str] = None) -> str:
    """
    快速恢復上下文（便捷函數）
    
    Args:
        user_message: 用戶消息
        session_id: Session ID
        base_path: 存儲路徑
        
    Returns:
        記憶上下文文本
    """
    injector = create_memory_injector(base_path)
    
    if session_id:
        return injector.auto_recover_context(session_id, user_message)
    else:
        return injector.get_session_context(current_topic=user_message)


# ==================== 測試代碼 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("記憶注入模組測試")
    print("=" * 60)
    
    # 創建測試實例
    injector = create_memory_injector()
    
    # 測試保存摘要
    print("\n[測試] 保存 Session 摘要...")
    test_context = SessionContext(
        session_id="test_session_001",
        start_time=datetime.now().isoformat(),
        summary="測試交易策略優化，決定保留3個核心策略",
        topics=["交易策略", "MTF整合"],
        decisions=["保留3個策略", "清理2個策略"],
        action_items=["⏳ 等待實盤部署", "✅ 完成策略參數調整"],
        emotions="積極、專注"
    )
    
    success = injector.save_session_summary(test_context)
    print(f"保存結果: {'成功' if success else '失敗'}")
    
    # 測試保存另一條記憶
    print("\n[測試] 保存第二條記憶...")
    test_context2 = SessionContext(
        session_id="test_session_002",
        start_time=datetime.now().isoformat(),
        summary="開發記憶系統插件，實現自動記憶注入功能",
        topics=["系統開發", "記憶插件"],
        decisions=["使用ChromaDB存儲", "實現語義搜索"],
        action_items=["⏳ 完成injector.py", "⏳ 整合到OpenClaw"],
        emotions="專注、高效"
    )
    success2 = injector.save_session_summary(test_context2)
    print(f"保存結果: {'成功' if success2 else '失敗'}")
    
    # 測試搜索記憶
    print("\n[測試] 搜索記憶 '交易策略'...")
    results = injector.search_memories("交易策略", limit=3)
    print(f"找到 {len(results)} 條相關記憶")
    for r in results:
        print(f"  - {r.id}: 相關度 {r.relevance_score:.2f}")
        print(f"    內容: {r.content[:50]}...")
    
    # 測試搜索記憶 - 系統開發
    print("\n[測試] 搜索記憶 '系統開發'...")
    results2 = injector.search_memories("系統開發", limit=3)
    print(f"找到 {len(results2)} 條相關記憶")
    for r in results2:
        print(f"  - {r.id}: 相關度 {r.relevance_score:.2f}")
        print(f"    內容: {r.content[:50]}...")
    
    # 測試生成上下文
    print("\n[測試] 生成記憶上下文 (主題: 交易策略)...")
    context = injector.get_session_context(current_topic="交易策略優化")
    print(context)
    
    # 測試生成上下文 - 系統開發
    print("\n[測試] 生成記憶上下文 (主題: 系統開發)...")
    context2 = injector.get_session_context(current_topic="記憶系統開發")
    print(context2)
    
    # 測試自動恢復
    print("\n[測試] 自動恢復上下文...")
    recovery = injector.auto_recover_context(
        "new_session_001",
        "我想繼續優化交易策略"
    )
    print(recovery)
    
    # 測試快速摘要
    print("\n[測試] 生成快速摘要...")
    summary = injector.get_recent_context(hours=24)
    print(summary)
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
