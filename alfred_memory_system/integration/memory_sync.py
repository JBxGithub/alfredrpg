"""
Memory Sync - 記憶同步模組

自動讀取 memory/ 目錄，同步到數據庫和 MEMORY.md / USER.md
與現有文件系統整合，保持向後兼容。
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


class MemorySync:
    """
    記憶同步器
    
    負責：
    1. 自動讀取 memory/ 目錄
    2. 自動更新 MEMORY.md
    3. 自動更新 USER.md
    4. 與數據庫同步
    """
    
    def __init__(self, 
                 workspace_path: Optional[str] = None,
                 db_manager=None):
        """
        初始化記憶同步器
        
        Args:
            workspace_path: 工作區路徑，默認 ~/openclaw_workspace
            db_manager: 數據庫管理器實例
        """
        if workspace_path is None:
            workspace_path = os.path.expanduser("~/openclaw_workspace")
        
        self.workspace_path = Path(workspace_path)
        self.memory_dir = self.workspace_path / "memory"
        self.memory_file = self.workspace_path / "MEMORY.md"
        self.user_file = self.workspace_path / "USER.md"
        self.db = db_manager
        
        # 確保目錄存在
        self.memory_dir.mkdir(parents=True, exist_ok=True)
    
    def scan_memory_files(self, days: int = 14) -> List[Dict[str, Any]]:
        """
        掃描 memory/ 目錄中的文件
        
        Args:
            days: 掃描最近幾天的文件
        
        Returns:
            文件信息列表
        """
        files = []
        cutoff_date = datetime.now() - __import__('datetime').timedelta(days=days)
        
        if not self.memory_dir.exists():
            return files
        
        for file_path in self.memory_dir.glob("*.md"):
            try:
                stat = file_path.stat()
                file_date = datetime.fromtimestamp(stat.st_mtime)
                
                if file_date >= cutoff_date:
                    content = file_path.read_text(encoding='utf-8')
                    files.append({
                        'path': str(file_path),
                        'name': file_path.name,
                        'date': file_date.isoformat(),
                        'size': stat.st_size,
                        'content': content[:1000]  # 只取前1000字符
                    })
            except Exception as e:
                print(f"[MemorySync] Error reading {file_path}: {e}")
        
        # 按時間排序
        files.sort(key=lambda x: x['date'], reverse=True)
        return files
    
    def extract_memories_from_file(self, file_path: str) -> List[Dict[str, str]]:
        """
        從記憶文件中提取記憶條目
        
        Args:
            file_path: 文件路徑
        
        Returns:
            記憶條目列表
        """
        try:
            content = Path(file_path).read_text(encoding='utf-8')
        except Exception:
            return []
        
        memories = []
        
        # 嘗試多種格式
        # 格式1: - **[timestamp]** (category) content
        pattern1 = r'- \*\*\[(\d{4}-\d{2}-\d{2}[\s\d:\-]*)\]\*\* \((\w+)\) (.+)'
        for match in re.finditer(pattern1, content):
            memories.append({
                'timestamp': match.group(1),
                'category': match.group(2),
                'content': match.group(3).strip()
            })
        
        # 格式2: - [timestamp] content
        pattern2 = r'- \[(\d{4}-\d{2}-\d{2})\]\s*(.+)'  
        for match in re.finditer(pattern2, content):
            if not any(m['content'] == match.group(2).strip() for m in memories):
                memories.append({
                    'timestamp': match.group(1),
                    'category': 'general',
                    'content': match.group(2).strip()
                })
        
        # 格式3: ## 標題 + 內容
        pattern3 = r'##\s*(.+?)\n\n(.+?)(?=\n##|\Z)'
        for match in re.finditer(pattern3, content, re.DOTALL):
            title = match.group(1).strip()
            body = match.group(2).strip()
            if len(body) > 20:  # 只取有意義的內容
                memories.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d'),
                    'category': 'extracted',
                    'content': f"{title}: {body[:200]}"
                })
        
        return memories
    
    def sync_to_database(self, dry_run: bool = False) -> Dict[str, int]:
        """
        將文件系統記憶同步到數據庫
        
        Args:
            dry_run: 如果為 True，只預覽不實際寫入
        
        Returns:
            同步統計
        """
        if not self.db:
            return {'error': 'No database manager provided'}
        
        stats = {'added': 0, 'skipped': 0, 'errors': 0}
        
        # 掃描記憶文件
        files = self.scan_memory_files(days=30)
        
        for file_info in files:
            memories = self.extract_memories_from_file(file_info['path'])
            
            for mem in memories:
                try:
                    # 生成唯一 ID
                    import hashlib
                    content_hash = hashlib.md5(mem['content'].encode()).hexdigest()[:8]
                    memory_id = f"sync_{content_hash}"
                    
                    # 檢查是否已存在
                    existing = self.db.get_memory(memory_id)
                    if existing:
                        stats['skipped'] += 1
                        continue
                    
                    if not dry_run:
                        success = self.db.add_memory(
                            memory_id=memory_id,
                            content=mem['content'],
                            category=mem['category'],
                            confidence=0.8  # 文件同步的記憶置信度稍低
                        )
                        if success:
                            stats['added'] += 1
                        else:
                            stats['errors'] += 1
                    else:
                        stats['added'] += 1  # 預覽模式下計數
                
                except Exception as e:
                    print(f"[MemorySync] Error syncing memory: {e}")
                    stats['errors'] += 1
        
        return stats
    
    def update_memory_md(self, new_entries: List[str], 
                         category: str = "general") -> Tuple[bool, str]:
        """
        更新 MEMORY.md 文件
        
        Args:
            new_entries: 新記憶條目列表
            category: 分類
        
        Returns:
            (成功與否, 消息)
        """
        try:
            from ..core.memory_manager import MemoryManager
            
            mm = MemoryManager()
            added = 0
            failed = 0
            
            for entry in new_entries:
                success, _ = mm.add(entry, category=category, target="memory")
                if success:
                    added += 1
                else:
                    failed += 1
            
            return True, f"Added {added} entries to MEMORY.md ({failed} failed)"
        
        except Exception as e:
            return False, f"Error: {e}"
    
    def update_user_md(self, new_entries: List[str],
                       category: str = "preference") -> Tuple[bool, str]:
        """
        更新 USER.md 文件
        
        Args:
            new_entries: 新記憶條目列表
            category: 分類
        
        Returns:
            (成功與否, 消息)
        """
        try:
            from ..core.memory_manager import MemoryManager
            
            mm = MemoryManager()
            added = 0
            failed = 0
            
            for entry in new_entries:
                success, _ = mm.add(entry, category=category, target="user")
                if success:
                    added += 1
                else:
                    failed += 1
            
            return True, f"Added {added} entries to USER.md ({failed} failed)"
        
        except Exception as e:
            return False, f"Error: {e}"
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """獲取記憶統計"""
        stats = {
            'memory_dir': str(self.memory_dir),
            'memory_file': str(self.memory_file),
            'user_file': str(self.user_file),
            'recent_files': len(self.scan_memory_files(days=7)),
            'total_files': len(list(self.memory_dir.glob("*.md"))) if self.memory_dir.exists() else 0
        }
        
        # 文件大小
        if self.memory_file.exists():
            stats['memory_file_size'] = self.memory_file.stat().st_size
        if self.user_file.exists():
            stats['user_file_size'] = self.user_file.stat().st_size
        
        return stats


# ==================== 便捷函數 ====================

def sync_all(dry_run: bool = False, db_manager=None) -> Dict[str, Any]:
    """
    執行完整同步
    
    Args:
        dry_run: 預覽模式
        db_manager: 數據庫管理器
    
    Returns:
        同步結果
    """
    sync = MemorySync(db_manager=db_manager)
    
    results = {
        'files_scanned': len(sync.scan_memory_files(days=30)),
        'database_sync': sync.sync_to_database(dry_run=dry_run),
        'stats': sync.get_memory_stats()
    }
    
    return results
