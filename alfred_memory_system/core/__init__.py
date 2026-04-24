"""
Alfred Memory System (AMS) - Core Components

核心組件模組，包含：
- ContextMonitor: Context 監控器
- MemoryManager: 記憶管理器（從 hermes 整合）
- SkillManager: 技能管理器（從 hermes 整合）
- LearningEngine: 學習引擎（從 hermes 整合）
- Summarizer: 摘要生成器（從 plugin 整合，可選）
"""

from .context_monitor import ContextMonitor, ContextStatus, check_context_simple
from .memory_manager import MemoryManager, MemoryEntry
from .skill_manager import SkillManager, Skill
from .learning_engine import LearningEngine, TaskAnalysis, LearningEntry
from .summarizer import Summarizer, ConversationSummary, SummaryType

__all__ = [
    # Context Monitor
    'ContextMonitor',
    'ContextStatus',
    'check_context_simple',
    
    # Memory Manager
    'MemoryManager',
    'MemoryEntry',
    
    # Skill Manager
    'SkillManager',
    'Skill',
    
    # Learning Engine
    'LearningEngine',
    'TaskAnalysis',
    'LearningEntry',
    
    # Summarizer (Optional)
    'Summarizer',
    'ConversationSummary',
    'SummaryType',
]
