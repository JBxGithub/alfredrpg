"""
Memory Manager - 記憶管理器
從 hermes-memory-system 整合
管理 MEMORY.md (Agent 記憶) 和 USER.md (用戶畫像) 的雙層記憶架構
"""

import os
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict


@dataclass
class MemoryEntry:
    """單條記憶條目"""
    content: str
    timestamp: str
    category: str = "general"
    priority: int = 1  # 1-5, 5為最高
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        return cls(**data)


class MemoryManager:
    """
    雙層記憶架構管理器
    - MEMORY.md: Agent 記憶 (2200 chars)
    - USER.md: 用戶畫像 (1375 chars)
    
    整合自 hermes-memory-system，為 AMS 提供文件級記憶管理
    """
    
    # 默認字符限制
    MEMORY_MAX_CHARS = 2200
    USER_MAX_CHARS = 1375
    COMPRESSION_THRESHOLD = 0.9  # 達到 90% 時觸發壓縮
    KEEP_RECENT_MEMORIES = 20  # 壓縮時保留的最新記憶數量
    
    def __init__(self, 
                 memory_file: Optional[str] = None,
                 user_file: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化記憶管理器
        
        Args:
            memory_file: MEMORY.md 路徑，默認為 ~/openclaw_workspace/MEMORY.md
            user_file: USER.md 路徑，默認為 ~/openclaw_workspace/USER.md
            config: 可選配置字典
        """
        self.config = config or {}
        
        # 設置文件路徑
        workspace = os.path.expanduser("~/openclaw_workspace")
        self.memory_file = memory_file or os.path.join(workspace, "MEMORY.md")
        self.user_file = user_file or os.path.join(workspace, "USER.md")
        
        # 字符限制（可從配置覆蓋）
        self.memory_max = self.config.get('memory_max_chars', self.MEMORY_MAX_CHARS)
        self.user_max = self.config.get('user_max_chars', self.USER_MAX_CHARS)
        
        # 確保文件存在
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """確保記憶文件存在"""
        for file_path in [self.memory_file, self.user_file]:
            dir_path = os.path.dirname(file_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self._get_default_header(file_path))
    
    def _get_default_header(self, file_path: str) -> str:
        """獲取默認文件頭"""
        if 'MEMORY' in file_path.upper():
            return """# MEMORY.md - Agent Long-Term Memory

*Curated memories and learnings - managed by AMS*

## Core Memories

"""
        else:
            return """# USER.md - User Profile

*Learn about the person you're helping - managed by AMS*

## User Information

"""
    
    def _read_file(self, file_path: str) -> str:
        """讀取文件內容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""
    
    def _write_file(self, file_path: str, content: str):
        """寫入文件內容"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _get_current_length(self, file_path: str) -> int:
        """獲取文件當前字符數"""
        content = self._read_file(file_path)
        return len(content)
    
    def _format_entry(self, content: str, category: str = "general") -> str:
        """格式化記憶條目"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"- **[{timestamp}]** ({category}) {content}\n"
    
    def _compress_if_needed(self, file_path: str, max_chars: int) -> bool:
        """
        如果超過限制，壓縮舊記憶
        保留最新的 N 條，其餘摘要存檔
        
        Returns:
            是否進行了壓縮
        """
        content = self._read_file(file_path)
        threshold = int(max_chars * self.COMPRESSION_THRESHOLD)
        
        if len(content) <= threshold:
            return False
        
        # 解析記憶條目
        lines = content.split('\n')
        header_lines = []
        memory_lines = []
        
        in_header = True
        for line in lines:
            if in_header:
                header_lines.append(line)
                if line.startswith('## '):
                    in_header = False
            else:
                if line.strip():
                    memory_lines.append(line)
        
        # 保留最新的記憶
        keep_count = self.KEEP_RECENT_MEMORIES
        recent_memories = memory_lines[-keep_count:] if len(memory_lines) > keep_count else memory_lines
        old_memories = memory_lines[:-keep_count] if len(memory_lines) > keep_count else []
        
        # 如果有舊記憶，創建摘要並存檔
        if old_memories:
            self._archive_memories(file_path, old_memories)
        
        # 重建文件
        new_content = '\n'.join(header_lines) + '\n' + '\n'.join(recent_memories) + '\n'
        self._write_file(file_path, new_content)
        
        return True
    
    def _archive_memories(self, source_file: str, memories: List[str]):
        """將舊記憶存檔"""
        archive_dir = os.path.join(
            os.path.dirname(source_file),
            'archives'
        )
        os.makedirs(archive_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{os.path.basename(source_file)}.{timestamp}.archive.md"
        archive_path = os.path.join(archive_dir, filename)
        
        with open(archive_path, 'w', encoding='utf-8') as f:
            f.write(f"# Archived Memories from {os.path.basename(source_file)}\n\n")
            f.write(f"*Archived on: {datetime.now().isoformat()}*\n\n")
            for mem in memories:
                f.write(mem + '\n')
    
    # ==================== 公開 API ====================
    
    def add(self, content: str, category: str = "general", target: str = "memory") -> Tuple[bool, str]:
        """
        添加記憶
        
        Args:
            content: 記憶內容
            category: 分類 (general, preference, lesson, decision, etc.)
            target: 目標文件 ("memory" 或 "user")
        
        Returns:
            (成功與否, 消息)
        """
        file_path = self.memory_file if target == "memory" else self.user_file
        max_chars = self.memory_max if target == "memory" else self.user_max
        
        # 檢查添加後是否會超過限制
        current_len = self._get_current_length(file_path)
        entry = self._format_entry(content, category)
        
        if current_len + len(entry) > max_chars:
            # 嘗試壓縮
            self._compress_if_needed(file_path, max_chars)
            current_len = self._get_current_length(file_path)
            
            if current_len + len(entry) > max_chars:
                return False, f"Memory limit reached ({max_chars} chars). Please remove old entries first."
        
        # 添加記憶
        file_content = self._read_file(file_path)
        file_content += entry
        self._write_file(file_path, file_content)
        
        return True, f"Added to {target.upper()}.md ({self._get_current_length(file_path)}/{max_chars} chars)"
    
    def replace(self, old_pattern: str, new_content: str, target: str = "memory") -> Tuple[bool, str]:
        """
        替換記憶
        
        Args:
            old_pattern: 要替換的內容模式 (支持正則)
            new_content: 新內容
            target: 目標文件
        
        Returns:
            (成功與否, 消息)
        """
        file_path = self.memory_file if target == "memory" else self.user_file
        
        content = self._read_file(file_path)
        new_content_full = re.sub(old_pattern, new_content, content)
        
        if new_content_full == content:
            return False, "Pattern not found"
        
        self._write_file(file_path, new_content_full)
        return True, f"Replaced in {target.upper()}.md"
    
    def remove(self, pattern: str, target: str = "memory") -> Tuple[bool, str]:
        """
        移除記憶
        
        Args:
            pattern: 要移除的內容模式 (支持正則)
            target: 目標文件
        
        Returns:
            (成功與否, 消息)
        """
        file_path = self.memory_file if target == "memory" else self.user_file
        
        content = self._read_file(file_path)
        lines = content.split('\n')
        
        # 過濾掉匹配的行
        new_lines = []
        removed_count = 0
        
        for line in lines:
            if re.search(pattern, line):
                removed_count += 1
            else:
                new_lines.append(line)
        
        if removed_count == 0:
            return False, "Pattern not found"
        
        self._write_file(file_path, '\n'.join(new_lines))
        return True, f"Removed {removed_count} entries from {target.upper()}.md"
    
    def search(self, query: str, target: str = "both") -> List[Dict[str, Any]]:
        """
        搜索記憶
        
        Args:
            query: 搜索關鍵詞
            target: 搜索目標 ("memory", "user", "both")
        
        Returns:
            匹配的記憶列表
        """
        results = []
        targets = []
        
        if target in ["memory", "both"]:
            targets.append(("memory", self.memory_file))
        if target in ["user", "both"]:
            targets.append(("user", self.user_file))
        
        for name, file_path in targets:
            content = self._read_file(file_path)
            lines = content.split('\n')
            
            for line in lines:
                if query.lower() in line.lower():
                    results.append({
                        "source": name,
                        "content": line,
                        "file": file_path
                    })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取記憶統計信息"""
        memory_len = self._get_current_length(self.memory_file)
        user_len = self._get_current_length(self.user_file)
        
        return {
            "memory": {
                "current": memory_len,
                "max": self.memory_max,
                "usage_percent": round(memory_len / self.memory_max * 100, 1),
                "file": self.memory_file
            },
            "user": {
                "current": user_len,
                "max": self.user_max,
                "usage_percent": round(user_len / self.user_max * 100, 1),
                "file": self.user_file
            }
        }
    
    def get_all(self, target: str = "memory") -> List[MemoryEntry]:
        """獲取所有記憶條目"""
        file_path = self.memory_file if target == "memory" else self.user_file
        content = self._read_file(file_path)
        
        entries = []
        # 解析記憶條目格式: - **[timestamp]** (category) content
        pattern = r'- \*\*\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\*\* \((\w+)\) (.+)'
        
        for match in re.finditer(pattern, content):
            entries.append(MemoryEntry(
                timestamp=match.group(1),
                category=match.group(2),
                content=match.group(3)
            ))
        
        return entries
    
    def sync_from_database(self, db_memories: List[Dict[str, Any]], 
                          target: str = "memory") -> Tuple[int, int]:
        """
        從數據庫同步記憶到文件
        
        Args:
            db_memories: 數據庫中的記憶列表
            target: 目標文件 ("memory" 或 "user")
        
        Returns:
            (添加數量, 跳過數量)
        """
        added = 0
        skipped = 0
        
        # 獲取現有記憶內容（用於去重）
        existing = self._read_file(self.memory_file if target == "memory" else self.user_file)
        
        for mem in db_memories:
            content = mem.get('content', '')
            
            # 檢查是否已存在
            if content in existing:
                skipped += 1
                continue
            
            # 添加記憶
            category = mem.get('category', 'general')
            success, _ = self.add(content, category, target)
            
            if success:
                added += 1
            else:
                skipped += 1
        
        return added, skipped
