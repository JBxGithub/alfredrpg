"""
記憶系統插件 - 主程序 (Main Module)
整合所有模組，提供統一API

Author: ClawTeam - Lead Developer
Date: 2026-04-08
Version: 1.0.0
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Tuple
from pathlib import Path
from dataclasses import dataclass, field

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent))

# 導入各個模組
try:
    from monitor import (
        ContextMonitor, ContextMetrics, ContextStatus,
        AlertConfig, SessionState, create_monitor
    )
    from vector_store import VectorStore, MemoryEntry
    from injector import MemoryInjector, SessionContext
    from summarizer import (
        Summarizer, ConversationSummary, SummaryType,
        quick_summarize, summarize_and_save
    )
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"[MemorySystem] 警告: 部分模組無法導入: {e}")
    MODULES_AVAILABLE = False


# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class MemorySystemConfig:
    """記憶系統配置"""
    # 路徑配置
    base_path: Path = field(default_factory=lambda: Path.home() / "openclaw_workspace" / "memory")
    
    # Context 監控配置
    warning_threshold: float = 70.0      # 70% 預警
    critical_threshold: float = 80.0     # 80% 自動觸發
    check_interval: int = 300            # 每 5 分鐘檢測
    
    # 向量數據庫配置
    vector_db_path: Optional[Path] = None
    collection_name: str = "memory_store"
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # 摘要配置
    auto_summarize: bool = True          # 自動生成摘要
    summary_on_critical: bool = True     # 危險時自動摘要
    
    # 記憶注入配置
    auto_inject: bool = True             # 自動注入記憶
    max_inject_memories: int = 3         # 最大注入記憶數
    
    def __post_init__(self):
        if self.vector_db_path is None:
            self.vector_db_path = self.base_path / "vector_db"


class MemorySystem:
    """
    記憶系統主類
    整合 Session 監控、向量存儲、摘要生成、記憶注入功能
    """
    
    def __init__(self, config: Optional[MemorySystemConfig] = None):
        """
        初始化記憶系統
        
        Args:
            config: 系統配置
        """
        self.config = config or MemorySystemConfig()
        
        # 初始化各個組件
        self.monitor: Optional[ContextMonitor] = None
        self.vector_store: Optional[VectorStore] = None
        self.injector: Optional[MemoryInjector] = None
        self.summarizer: Optional[Summarizer] = None
        
        # 狀態追蹤
        self.current_session_id: Optional[str] = None
        self.is_initialized: bool = False
        
        # 回調函數
        self._on_warning: Optional[Callable] = None
        self._on_critical: Optional[Callable] = None
        self._on_summary_ready: Optional[Callable] = None
        
        logger.info("[MemorySystem] 記憶系統初始化中...")
    
    def initialize(self, session_id: str) -> bool:
        """
        初始化系統組件
        
        Args:
            session_id: 當前 Session ID
            
        Returns:
            是否初始化成功
        """
        try:
            self.current_session_id = session_id
            
            # 初始化向量存儲
            logger.info("[MemorySystem] 初始化向量存儲...")
            self.vector_store = VectorStore(
                db_path=self.config.vector_db_path,
                collection_name=self.config.collection_name,
                embedding_model=self.config.embedding_model
            )
            
            # 初始化摘要生成器
            logger.info("[MemorySystem] 初始化摘要生成器...")
            self.summarizer = Summarizer(
                storage_path=self.config.base_path / "summaries"
            )
            
            # 初始化記憶注入器
            logger.info("[MemorySystem] 初始化記憶注入器...")
            self.injector = MemoryInjector(
                base_path=str(self.config.base_path)
            )
            
            # 初始化 Session 監控
            logger.info("[MemorySystem] 初始化 Session 監控...")
            self.monitor = create_monitor(
                session_id=session_id,
                warning_threshold=self.config.warning_threshold,
                critical_threshold=self.config.critical_threshold
            )
            
            # 註冊回調
            self._register_monitor_callbacks()
            
            self.is_initialized = True
            logger.info(f"[MemorySystem] 系統初始化完成 - Session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"[MemorySystem] 初始化失敗: {e}")
            return False
    
    def _register_monitor_callbacks(self):
        """註冊監控回調"""
        if not self.monitor:
            return
        
        # 預警回調
        def on_warning(metrics: ContextMetrics):
            logger.warning(f"[MemorySystem] Context 使用率預警: {metrics.usage_percentage:.1f}%")
            if self._on_warning:
                self._on_warning(metrics)
        
        # 危險回調
        def on_critical(metrics: ContextMetrics):
            logger.error(f"[MemorySystem] Context 使用率危險: {metrics.usage_percentage:.1f}%")
            
            # 自動生成摘要
            if self.config.summary_on_critical:
                logger.info("[MemorySystem] 自動觸發摘要生成...")
                # 這裡可以觸發摘要生成
            
            if self._on_critical:
                self._on_critical(metrics)
        
        self.monitor.register_callback(ContextStatus.WARNING, on_warning)
        self.monitor.register_callback(ContextStatus.CRITICAL, on_critical)
    
    def check_context(self, tokens_used: int) -> Dict[str, Any]:
        """
        檢查 Context 使用情況
        
        Args:
            tokens_used: 已使用的 tokens
            
        Returns:
            檢查結果
        """
        if not self.monitor:
            return {"error": "監控器未初始化"}
        
        metrics = self.monitor.check_and_alert(tokens_used)
        
        return {
            "status": metrics.status.value,
            "usage_percentage": metrics.usage_percentage,
            "tokens_used": metrics.tokens_used,
            "tokens_remaining": metrics.tokens_remaining,
            "recommendation": self._get_recommendation(metrics)
        }
    
    def _get_recommendation(self, metrics: ContextMetrics) -> str:
        """獲取建議"""
        if metrics.status == ContextStatus.CRITICAL:
            return "🚨 強烈建議立即開啟新 Session！Context 使用率已達危險水平。"
        elif metrics.status == ContextStatus.WARNING:
            return "⚠️ 建議準備開啟新 Session，完成當前任務後切換。"
        elif metrics.usage_percentage >= 60:
            return "ℹ️ Context 使用率正常偏高，注意對話長度。"
        else:
            return "✅ Context 使用率健康。"
    
    def create_summary(self, conversation_text: str, 
                       title: Optional[str] = None) -> Optional[ConversationSummary]:
        """
        創建對話摘要
        
        Args:
            conversation_text: 對話文本
            title: 標題
            
        Returns:
            摘要對象或 None
        """
        if not self.summarizer or not self.current_session_id:
            logger.error("[MemorySystem] 摘要生成器未初始化")
            return None
        
        try:
            summary = self.summarizer.generate_summary(
                session_id=self.current_session_id,
                conversation_text=conversation_text,
                title=title
            )
            
            # 保存摘要
            self.summarizer.save_summary(summary)
            
            # 同時存儲到向量數據庫
            if self.vector_store:
                self._store_summary_to_vector(summary)
            
            logger.info(f"[MemorySystem] 摘要已創建: {summary.id}")
            
            if self._on_summary_ready:
                self._on_summary_ready(summary)
            
            return summary
            
        except Exception as e:
            logger.error(f"[MemorySystem] 摘要創建失敗: {e}")
            return None
    
    def _store_summary_to_vector(self, summary: ConversationSummary):
        """將摘要存儲到向量數據庫"""
        if not self.vector_store:
            return
        
        # 構建存儲內容
        content_parts = [
            summary.overview,
            "決策: " + "; ".join([d.content for d in summary.decisions]),
            "行動: " + "; ".join([a.content for a in summary.action_items]),
        ]
        content = "\n".join(content_parts)
        
        # 存儲到向量數據庫
        self.vector_store.store_memory(
            content=content,
            session_key=summary.session_id,
            topics=summary.topics,
            decisions=[d.content for d in summary.decisions],
            emotions=summary.emotional_context.primary_emotion if summary.emotional_context else "",
            priority="high" if summary.summary_type == SummaryType.SESSION else "normal",
            metadata={
                "summary_id": summary.id,
                "timestamp": summary.timestamp,
                "action_items": [a.to_dict() for a in summary.action_items],
                "next_continue": summary.next_continue
            }
        )
    
    def get_memory_context(self, query: Optional[str] = None) -> str:
        """
        獲取記憶上下文
        
        Args:
            query: 搜索查詢（可選）
            
        Returns:
            格式化的記憶上下文
        """
        if not self.injector:
            return "[記憶系統未初始化]"
        
        return self.injector.get_session_context(current_topic=query)
    
    def auto_recover_context(self, user_first_message: str) -> str:
        """
        自動恢復上下文（新 Session 啟動時調用）
        
        Args:
            user_first_message: 用戶第一條消息
            
        Returns:
            完整的記憶注入上下文
        """
        if not self.injector or not self.current_session_id:
            return "[記憶系統未初始化]"
        
        if not self.config.auto_inject:
            return "[自動記憶注入已禁用]"
        
        return self.injector.auto_recover_context(
            session_id=self.current_session_id,
            user_first_message=user_first_message
        )
    
    def search_memories(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        搜索記憶
        
        Args:
            query: 搜索查詢
            n_results: 返回結果數
            
        Returns:
            記憶列表
        """
        results = []
        
        # 從向量數據庫搜索
        if self.vector_store:
            vector_results = self.vector_store.search_similar(query, n_results=n_results)
            results.extend(vector_results)
        
        # 從注入器搜索
        if self.injector:
            injector_results = self.injector.search_memories(query, limit=n_results)
            for r in injector_results:
                results.append({
                    "id": r.id,
                    "content": r.content,
                    "metadata": r.metadata
                })
        
        return results[:n_results]
    
    def get_recent_summary(self, hours: int = 24) -> str:
        """
        獲取最近摘要
        
        Args:
            hours: 時間範圍（小時）
            
        Returns:
            摘要文本
        """
        if self.injector:
            return self.injector.get_recent_context(hours=hours)
        return "無可用摘要"
    
    def save_session_summary(self, summary_text: str, topics: List[str] = None,
                            decisions: List[str] = None, 
                            action_items: List[str] = None) -> bool:
        """
        保存 Session 摘要
        
        Args:
            summary_text: 摘要文本
            topics: 主題列表
            decisions: 決策列表
            action_items: 行動項目列表
            
        Returns:
            是否保存成功
        """
        if not self.injector or not self.current_session_id:
            return False
        
        context = SessionContext(
            session_id=self.current_session_id,
            start_time=datetime.now().isoformat(),
            summary=summary_text,
            topics=topics or [],
            decisions=decisions or [],
            action_items=action_items or []
        )
        
        return self.injector.save_session_summary(context)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        獲取系統狀態
        
        Returns:
            系統狀態字典
        """
        status = {
            "initialized": self.is_initialized,
            "session_id": self.current_session_id,
            "components": {}
        }
        
        # 監控器狀態
        if self.monitor:
            status["components"]["monitor"] = {
                "active": self.monitor.state.is_active,
                "alert_count": self.monitor.state.alert_count,
                "current_usage": self.monitor.state.context_metrics.usage_percentage if self.monitor.state.context_metrics else 0
            }
        
        # 向量數據庫狀態
        if self.vector_store:
            stats = self.vector_store.get_stats()
            status["components"]["vector_store"] = stats
        
        # 注入器狀態
        if self.injector:
            status["components"]["injector"] = {
                "memory_count": len(self.injector.memory_store._memory_cache)
            }
        
        return status
    
    def register_callbacks(self, on_warning=None, on_critical=None, 
                          on_summary_ready=None):
        """
        註冊回調函數
        
        Args:
            on_warning: 預警回調
            on_critical: 危險回調
            on_summary_ready: 摘要就緒回調
        """
        self._on_warning = on_warning
        self._on_critical = on_critical
        self._on_summary_ready = on_summary_ready
    
    def shutdown(self):
        """關閉系統"""
        logger.info("[MemorySystem] 正在關閉系統...")
        
        if self.monitor:
            self.monitor.stop_monitoring()
        
        self.is_initialized = False
        logger.info("[MemorySystem] 系統已關閉")


# ==================== 便捷函數 ====================

def create_memory_system(
    session_id: str,
    base_path: Optional[str] = None,
    warning_threshold: float = 70.0,
    critical_threshold: float = 80.0
) -> MemorySystem:
    """
    創建並初始化記憶系統
    
    Args:
        session_id: Session ID
        base_path: 基礎路徑
        warning_threshold: 預警閾值
        critical_threshold: 危險閾值
        
    Returns:
        初始化後的 MemorySystem 實例
    """
    config = MemorySystemConfig(
        warning_threshold=warning_threshold,
        critical_threshold=critical_threshold
    )
    
    if base_path:
        config.base_path = Path(base_path)
    
    system = MemorySystem(config)
    system.initialize(session_id)
    
    return system


def quick_init(session_id: str) -> MemorySystem:
    """
    快速初始化記憶系統
    
    Args:
        session_id: Session ID
        
    Returns:
        MemorySystem 實例
    """
    return create_memory_system(session_id)


# ==================== API 類 ====================

class MemorySystemAPI:
    """
    記憶系統 API
    提供 RESTful 風格的接口
    """
    
    def __init__(self):
        self.systems: Dict[str, MemorySystem] = {}
    
    def create_system(self, session_id: str, 
                      config: Optional[MemorySystemConfig] = None) -> MemorySystem:
        """創建記憶系統實例"""
        system = MemorySystem(config)
        system.initialize(session_id)
        self.systems[session_id] = system
        return system
    
    def get_system(self, session_id: str) -> Optional[MemorySystem]:
        """獲取記憶系統實例"""
        return self.systems.get(session_id)
    
    def remove_system(self, session_id: str) -> bool:
        """移除記憶系統實例"""
        if session_id in self.systems:
            self.systems[session_id].shutdown()
            del self.systems[session_id]
            return True
        return False
    
    def check_context(self, session_id: str, tokens_used: int) -> Dict[str, Any]:
        """檢查 Context 使用情況"""
        system = self.get_system(session_id)
        if not system:
            return {"error": "Session not found"}
        return system.check_context(tokens_used)
    
    def create_summary(self, session_id: str, 
                       conversation_text: str) -> Optional[ConversationSummary]:
        """創建摘要"""
        system = self.get_system(session_id)
        if not system:
            return None
        return system.create_summary(conversation_text)
    
    def get_memory_context(self, session_id: str, 
                           query: Optional[str] = None) -> str:
        """獲取記憶上下文"""
        system = self.get_system(session_id)
        if not system:
            return "[Session not found]"
        return system.get_memory_context(query)
    
    def search_memories(self, session_id: str, query: str, 
                        n_results: int = 5) -> List[Dict[str, Any]]:
        """搜索記憶"""
        system = self.get_system(session_id)
        if not system:
            return []
        return system.search_memories(query, n_results)
    
    def get_status(self, session_id: str) -> Dict[str, Any]:
        """獲取系統狀態"""
        system = self.get_system(session_id)
        if not system:
            return {"error": "Session not found"}
        return system.get_system_status()


# ==================== 測試代碼 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("記憶系統插件 - 主程序測試")
    print("=" * 60)
    
    # 創建記憶系統
    print("\n[測試] 創建記憶系統...")
    system = create_memory_system(
        session_id="test_session_main_001",
        warning_threshold=70.0,
        critical_threshold=80.0
    )
    
    # 檢查系統狀態
    print("\n[測試] 系統狀態:")
    status = system.get_system_status()
    print(json.dumps(status, indent=2, ensure_ascii=False, default=str))
    
    # 測試 Context 檢查
    print("\n[測試] Context 檢查 (模擬 75% 使用率)...")
    result = system.check_context(tokens_used=192000)  # 75% of 256k
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 測試摘要生成
    print("\n[測試] 生成摘要...")
    test_conversation = """
今天我們討論了記憶系統的開發計劃。
決定採用 ChromaDB 作為向量數據庫，sentence-transformers 作為嵌入模型。
待完成項目：
⏳ 完成 summarizer.py
⏳ 完成 main.py
✅ 已完成 monitor.py
情感上感覺很積極，進展順利。
    """
    
    summary = system.create_summary(test_conversation, "記憶系統開發討論")
    if summary:
        print(f"摘要標題: {summary.title}")
        print(f"主題: {summary.topics}")
        print(f"決策數: {len(summary.decisions)}")
    
    # 測試記憶搜索
    print("\n[測試] 搜索記憶 '交易策略'...")
    results = system.search_memories("交易策略", n_results=3)
    print(f"找到 {len(results)} 條記憶")
    
    # 測試記憶上下文
    print("\n[測試] 獲取記憶上下文...")
    context = system.get_memory_context("系統開發")
    print(context[:500] + "...")
    
    # 關閉系統
    print("\n[測試] 關閉系統...")
    system.shutdown()
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
