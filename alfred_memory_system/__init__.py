"""
Alfred Memory System (AMS)

Windows 版自適應學習機制長期記憶架構
整合版本 v2.0.0

靈感來源: Hermes Agent + OpenClaw
設計目標: 為呀鬼打造持續學習、自我改進的記憶系統

整合內容：
- Context Monitor (現有)
- Memory Manager (從 hermes 整合)
- Skill Manager (從 hermes 整合)
- Learning Engine (從 hermes 整合)
- Summarizer (從 plugin 整合，可選)
"""

__version__ = "2.0.0"
__author__ = "Alfred (呀鬼)"

from .config import AMSConfig, ContextMonitorConfig, MemoryEngineConfig
from .storage import DatabaseManager
from .core import (
    ContextMonitor, ContextStatus, check_context_simple,
    MemoryManager, MemoryEntry,
    SkillManager, Skill,
    LearningEngine, TaskAnalysis, LearningEntry,
    Summarizer, ConversationSummary, SummaryType
)

__all__ = [
    'AMS',
    'AMSConfig',
    'ContextMonitorConfig',
    'MemoryEngineConfig',
    'DatabaseManager',
    'ContextMonitor',
    'ContextStatus',
    'check_context_simple',
    'MemoryManager',
    'MemoryEntry',
    'SkillManager',
    'Skill',
    'LearningEngine',
    'TaskAnalysis',
    'LearningEntry',
    'Summarizer',
    'ConversationSummary',
    'SummaryType',
]


class AMS:
    """
    Alfred Memory System 主類 v2.0.0
    
    整合所有記憶功能：
    - Context Monitor: 實時監控對話長度
    - Memory Manager: 管理 MEMORY.md 和 USER.md
    - Skill Manager: 管理 SKILL.md 文件
    - Learning Engine: 自動學習和技能創建
    - Summarizer: 對話摘要生成（可選）
    
    使用方式:
        from alfred_memory_system import AMS
        
        # 初始化
        ams = AMS()
        ams.initialize()
        
        # 檢查 Context
        status = ams.context_monitor.check_context(messages)
        print(status)
        
        # 記錄使用情況
        ams.context_monitor.log_usage(session_id, status)
        
        # 添加記憶
        ams.memory_manager.add("用戶偏好使用深色主題", category="preference")
        
        # 分析任務並可能創建技能
        analysis = ams.learning_engine.analyze_task(
            task_description="部署 TradingBot",
            steps=["步驟1", "步驟2", "步驟3"],
            duration_minutes=15,
            tool_calls_count=8
        )
        if analysis.should_create_skill:
            ams.learning_engine.auto_create_skill(analysis)
    """
    
    def __init__(self, config: AMSConfig = None):
        """
        初始化 AMS 系統
        
        Args:
            config: AMS 配置對象，默認使用默認配置
        """
        self.config = config or AMSConfig()
        
        # 初始化數據庫
        self.db = DatabaseManager(self.config)
        
        # 初始化 Context Monitor
        self.context_monitor = ContextMonitor(self.config.context, self.db)
        
        # 初始化 Memory Manager（從 hermes 整合）
        self.memory_manager = MemoryManager(
            memory_file=None,  # 使用默認路徑
            user_file=None,
            config=self.config.memory.__dict__ if hasattr(self.config, 'memory') else None
        )
        
        # 初始化 Skill Manager（從 hermes 整合）
        self.skill_manager = SkillManager(
            skills_dir=self.config.skills_path if hasattr(self.config, 'skills_path') else None
        )
        
        # 初始化 Learning Engine（從 hermes 整合）
        self.learning_engine = LearningEngine(
            db_manager=self.db,
            skill_manager=self.skill_manager,
            config=self.config.skill.__dict__ if hasattr(self.config, 'skill') else None
        )
        
        # 初始化 Summarizer（從 plugin 整合，默認關閉）
        self.summarizer = Summarizer(
            enabled=getattr(self.config, 'summarizer_enabled', False)
        )
    
    def initialize(self):
        """初始化 AMS 系統，創建數據庫表"""
        self.db.initialize()
        print(f"✅ Alfred Memory System v{__version__} initialized")
        print(f"   - Context Monitor: {'enabled' if self.config.context.enabled else 'disabled'}")
        print(f"   - Memory Manager: enabled")
        print(f"   - Skill Manager: enabled")
        print(f"   - Learning Engine: {'enabled' if self.config.skill.enabled else 'disabled'}")
        print(f"   - Summarizer: {'enabled' if self.summarizer.enabled else 'disabled (optional)'}")
    
    def reset(self):
        """重置 AMS 系統（清除所有數據）"""
        self.db.reset()
    
    def get_stats(self):
        """獲取系統統計信息"""
        return self.db.get_stats()
    
    def status(self):
        """顯示系統狀態"""
        stats = self.get_stats()
        
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║           Alfred Memory System Status                        ║")
        print(f"║                    Version {__version__}                            ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()
        print(f"📊 Database Statistics:")
        print(f"   Total Sessions: {stats.get('total_sessions', 0)}")
        print(f"   Total Messages: {stats.get('total_messages', 0)}")
        print(f"   Total Memories: {stats.get('total_memories', 0)}")
        print(f"   Total Skills: {stats.get('total_skills', 0)} (Auto-created: {stats.get('auto_created_skills', 0)})")
        print(f"   Total Learnings: {stats.get('total_learnings', 0)}")
        print(f"   Total Projects: {stats.get('total_projects', 0)}")
        print(f"   Database Size: {stats.get('db_size_mb', 0)} MB")
        print()
        
        if stats.get('memories_by_category'):
            print("🧠 Memories by Category:")
            for category, count in stats['memories_by_category'].items():
                print(f"   - {category}: {count}")
        print()
        
        if stats.get('learnings_by_status'):
            print("📚 Learnings by Status:")
            for status, count in stats['learnings_by_status'].items():
                print(f"   - {status}: {count}")
        print()
        
        if stats.get('projects_by_status'):
            print("📁 Projects by Status:")
            for status, count in stats['projects_by_status'].items():
                print(f"   - {status}: {count}")
        print()
        
        # Memory Manager 統計
        mem_stats = self.memory_manager.get_stats()
        print("📝 File Memory Statistics:")
        print(f"   MEMORY.md: {mem_stats['memory']['usage_percent']:.1f}% ({mem_stats['memory']['current']}/{mem_stats['memory']['max']} chars)")
        print(f"   USER.md: {mem_stats['user']['usage_percent']:.1f}% ({mem_stats['user']['current']}/{mem_stats['user']['max']} chars)")
        print()
        
        # Skill Manager 統計
        skill_stats = self.skill_manager.get_skill_stats()
        print(f"🛠️  Skills: {skill_stats['total_skills']} total")
        if skill_stats['by_category']:
            for cat, count in skill_stats['by_category'].items():
                print(f"   - {cat}: {count}")
        print()
        
        # Learning Engine 統計
        learning_stats = self.learning_engine.get_learning_stats()
        print(f"🎓 Learning Statistics:")
        print(f"   Tasks Analyzed: {learning_stats['tasks_analyzed']}")
        print(f"   Skills Auto-Created: {learning_stats['skills_auto_created']}")
        print(f"   Pending Learnings: {learning_stats['pending_learnings']}")
        print()
        
        print("═══════════════════════════════════════════════════════════════")
    
    def sync_memory_files(self) -> dict:
        """
        同步數據庫記憶到文件 (MEMORY.md / USER.md)
        
        Returns:
            同步結果統計
        """
        # 從數據庫獲取記憶
        db_memories = self.db.list_memories(limit=1000)
        
        # 分類記憶
        memory_entries = [m for m in db_memories if m.get('category') not in ['user_profile', 'preference']]
        user_entries = [m for m in db_memories if m.get('category') in ['user_profile', 'preference']]
        
        # 同步到文件
        mem_added, mem_skipped = self.memory_manager.sync_from_database(memory_entries, target="memory")
        user_added, user_skipped = self.memory_manager.sync_from_database(user_entries, target="user")
        
        return {
            'memory': {'added': mem_added, 'skipped': mem_skipped},
            'user': {'added': user_added, 'skipped': user_skipped}
        }
    
    def sync_skills_to_database(self) -> dict:
        """
        同步文件系統 Skills 到數據庫
        
        Returns:
            同步結果統計
        """
        added, updated = self.skill_manager.sync_to_database(self.db)
        return {'added': added, 'updated': updated}
    
    def check_context_and_warn(self, messages: list, session_id: str = None) -> ContextStatus:
        """
        檢查 Context 並在超過閾值時發出警告
        
        Args:
            messages: 當前對話消息列表
            session_id: 可選 Session ID
        
        Returns:
            ContextStatus 對象
        """
        status = self.context_monitor.check_context(messages)
        
        # 如果超過警告閾值，記錄到數據庫
        if status.action_required and session_id:
            self.context_monitor.log_usage(session_id, status)
        
        return status
    
    def process_session(self, session_id: str, messages: list, 
                       generate_summary: bool = False) -> dict:
        """
        處理 Session 結束後的學習和記錄
        
        Args:
            session_id: Session ID
            messages: 對話消息列表
            generate_summary: 是否生成摘要（默認 False）
        
        Returns:
            處理結果統計
        """
        results = {
            'context_status': None,
            'summary': None,
            'learnings_added': 0
        }
        
        # 檢查 Context
        status = self.check_context_and_warn(messages, session_id)
        results['context_status'] = status.to_dict()
        
        # 生成摘要（如果啟用）
        if generate_summary and self.summarizer.enabled:
            conversation_text = "\n".join([
                f"{m.get('role', 'unknown')}: {m.get('content', '')}"
                for m in messages
            ])
            summary = self.summarizer.generate_summary(session_id, conversation_text)
            if summary:
                self.summarizer.save_summary(summary)
                results['summary'] = summary.to_dict()
        
        return results
