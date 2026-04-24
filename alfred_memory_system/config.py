"""
Alfred Memory System (AMS) - Configuration

核心配置管理，支持從 YAML 文件和環境變量加載配置。
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from pathlib import Path


@dataclass
class ContextMonitorConfig:
    """Context 監控配置"""
    enabled: bool = True
    warning_threshold: float = 0.70      # 70% - 發出警告
    compress_threshold: float = 0.85     # 85% - 自動壓縮
    critical_threshold: float = 0.95     # 95% - 緊急處理
    model_context_length: int = 128000   # 默認模型 Context 長度
    check_interval: int = 5              # 檢查間隔（消息數）


@dataclass
class MemoryEngineConfig:
    """記憶引擎配置"""
    enabled: bool = True
    auto_extract: bool = True            # 自動提取記憶
    max_memory_entries: int = 100        # 最大記憶條目數
    consolidation_threshold: float = 0.80  # 記憶整合閾值
    min_confidence: float = 0.60         # 最小置信度
    categories: List[str] = field(default_factory=lambda: [
        'user_profile', 'environment', 'preference', 'decision', 'skill', 'correction'
    ])


@dataclass
class SkillEvolverConfig:
    """技能進化器配置"""
    enabled: bool = True
    auto_create: bool = True             # 自動創建 Skill
    min_tool_calls: int = 5              # 觸發 Skill 創建的最小 tool calls
    min_usage_before_evolve: int = 3     # 進化前最小使用次數
    evolution_interval_days: int = 7     # 進化檢查間隔


@dataclass
class SessionSearchConfig:
    """會話搜索配置"""
    enabled: bool = True
    default_limit: int = 10
    min_relevance: float = 0.50
    enable_semantic: bool = False        # 是否啟用語義搜索（需要額外依賴）
    summary_model: Optional[str] = None  # 摘要生成模型


@dataclass
class StorageConfig:
    """存儲配置"""
    db_path: str = "~/openclaw_workspace/alfred_memory_system/data/alfred_memory.db"
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    backup_retention_days: int = 30
    max_db_size_mb: int = 500


@dataclass
class AMSConfig:
    """AMS 主配置"""
    version: str = "1.0.0"
    debug: bool = False
    
    # 子配置
    context: ContextMonitorConfig = field(default_factory=ContextMonitorConfig)
    memory: MemoryEngineConfig = field(default_factory=MemoryEngineConfig)
    skill: SkillEvolverConfig = field(default_factory=SkillEvolverConfig)
    search: SessionSearchConfig = field(default_factory=SessionSearchConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    
    # 路徑配置
    workspace_path: str = "~/openclaw_workspace"
    memory_path: str = "~/openclaw_workspace/memory"
    skills_path: str = "~/openclaw_workspace/skills"
    
    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> 'AMSConfig':
        """從 YAML 文件加載配置"""
        if config_path is None:
            config_path = os.path.expanduser("~/.ams/config.yaml")
        
        config = cls()
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                
            # 加載各個子配置
            if 'context' in data:
                config.context = ContextMonitorConfig(**data['context'])
            if 'memory' in data:
                config.memory = MemoryEngineConfig(**data['memory'])
            if 'skill' in data:
                config.skill = SkillEvolverConfig(**data['skill'])
            if 'search' in data:
                config.search = SessionSearchConfig(**data['search'])
            if 'storage' in data:
                config.storage = StorageConfig(**data['storage'])
            
            # 加載其他配置
            config.debug = data.get('debug', False)
            config.workspace_path = data.get('workspace_path', config.workspace_path)
        
        return config
    
    def save_to_file(self, config_path: Optional[str] = None):
        """保存配置到 YAML 文件"""
        if config_path is None:
            config_path = os.path.expanduser("~/.ams/config.yaml")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        data = {
            'version': self.version,
            'debug': self.debug,
            'context': self.context.__dict__,
            'memory': self.memory.__dict__,
            'skill': self.skill.__dict__,
            'search': self.search.__dict__,
            'storage': self.storage.__dict__,
            'workspace_path': self.workspace_path,
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
    
    def get_db_path(self) -> str:
        """獲取數據庫路徑（展開用戶目錄）"""
        return os.path.expanduser(self.storage.db_path)


# 默認配置實例
DEFAULT_CONFIG = AMSConfig()
