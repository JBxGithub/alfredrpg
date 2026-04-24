"""
Project Tracker - 專案狀態追蹤

追蹤專案狀態變化，與現有 project-states/ 目錄整合。
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


class ProjectTracker:
    """
    專案追蹤器
    
    負責：
    1. 讀取 project-states/ 目錄
    2. 追蹤專案狀態變化
    3. 與數據庫同步
    """
    
    def __init__(self, 
                 workspace_path: Optional[str] = None,
                 db_manager=None):
        """
        初始化專案追蹤器
        
        Args:
            workspace_path: 工作區路徑，默認 ~/openclaw_workspace
            db_manager: 數據庫管理器實例
        """
        if workspace_path is None:
            workspace_path = os.path.expanduser("~/openclaw_workspace")
        
        self.workspace_path = Path(workspace_path)
        self.project_states_dir = self.workspace_path / "project-states"
        self.db = db_manager
        
        # 確保目錄存在
        self.project_states_dir.mkdir(parents=True, exist_ok=True)
    
    def scan_project_files(self) -> List[Dict[str, Any]]:
        """
        掃描 project-states/ 目錄中的文件
        
        Returns:
            專案文件信息列表
        """
        files = []
        
        if not self.project_states_dir.exists():
            return files
        
        for file_path in self.project_states_dir.glob("*.md"):
            try:
                stat = file_path.stat()
                content = file_path.read_text(encoding='utf-8')
                
                # 提取專案名稱
                project_name = self._extract_project_name(file_path.name)
                
                # 提取狀態
                status = self._extract_status(content)
                
                files.append({
                    'path': str(file_path),
                    'name': file_path.name,
                    'project_name': project_name,
                    'status': status,
                    'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'content_preview': content[:500]
                })
            except Exception as e:
                print(f"[ProjectTracker] Error reading {file_path}: {e}")
        
        return files
    
    def _extract_project_name(self, filename: str) -> str:
        """從文件名提取專案名稱"""
        # 移除 -STATUS.md 後綴
        name = filename.replace('-STATUS.md', '').replace('.md', '')
        # 轉換為可讀格式
        name = name.replace('-', ' ').replace('_', ' ')
        return name.title()
    
    def _extract_status(self, content: str) -> str:
        """從內容提取狀態"""
        # 查找狀態標記
        status_patterns = [
            r'狀態[：:]\s*(\w+)',
            r'Status[：:]\s*(\w+)',
            r'##\s*(進行中|已完成|暫停|活躍|Active|Completed|Paused)',
        ]
        
        for pattern in status_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                status = match.group(1).lower()
                status_map = {
                    '進行中': 'active',
                    '已完成': 'completed',
                    '暫停': 'paused',
                    '活躍': 'active',
                    'active': 'active',
                    'completed': 'completed',
                    'paused': 'paused'
                }
                return status_map.get(status, 'active')
        
        return 'active'  # 默認狀態
    
    def sync_to_database(self, dry_run: bool = False) -> Dict[str, int]:
        """
        將專案文件同步到數據庫
        
        Args:
            dry_run: 如果為 True，只預覽不實際寫入
        
        Returns:
            同步統計
        """
        if not self.db:
            return {'error': 'No database manager provided'}
        
        stats = {'added': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        
        projects = self.scan_project_files()
        
        for proj in projects:
            try:
                # 檢查數據庫中是否已存在
                existing = self.db.get_project_by_name(proj['project_name'])
                
                if existing:
                    # 檢查是否需要更新
                    if existing.get('status') != proj['status']:
                        if not dry_run:
                            self.db.update_project(
                                existing['id'],
                                status=proj['status']
                            )
                        stats['updated'] += 1
                    else:
                        stats['skipped'] += 1
                else:
                    # 添加新專案
                    if not dry_run:
                        import uuid
                        self.db.add_project(
                            project_id=str(uuid.uuid4())[:8],
                            name=proj['project_name'],
                            description=proj['content_preview'][:200],
                            path=proj['path'],
                            status=proj['status']
                        )
                    stats['added'] += 1
            
            except Exception as e:
                print(f"[ProjectTracker] Error syncing project: {e}")
                stats['errors'] += 1
        
        return stats
    
    def get_project_summary(self, project_name: str) -> Optional[str]:
        """
        獲取專案摘要
        
        Args:
            project_name: 專案名稱
        
        Returns:
            專案內容，如果不存在則返回 None
        """
        # 嘗試多種文件名格式
        possible_names = [
            f"{project_name}-STATUS.md",
            f"{project_name.replace(' ', '-')}-STATUS.md",
            f"{project_name.replace(' ', '_')}-STATUS.md",
        ]
        
        for name in possible_names:
            file_path = self.project_states_dir / name
            if file_path.exists():
                return file_path.read_text(encoding='utf-8')
        
        return None
    
    def list_active_projects(self) -> List[Dict[str, Any]]:
        """列出活躍專案"""
        if self.db:
            return self.db.list_projects(status='active')
        else:
            # 從文件系統讀取
            return [p for p in self.scan_project_files() if p['status'] == 'active']
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取專案統計"""
        projects = self.scan_project_files()
        
        by_status = {}
        for p in projects:
            status = p['status']
            by_status[status] = by_status.get(status, 0) + 1
        
        return {
            'total_projects': len(projects),
            'by_status': by_status,
            'project_states_dir': str(self.project_states_dir)
        }


# ==================== 便捷函數 ====================

def sync_projects(dry_run: bool = False, db_manager=None) -> Dict[str, Any]:
    """
    同步專案到數據庫
    
    Args:
        dry_run: 預覽模式
        db_manager: 數據庫管理器
    
    Returns:
        同步結果
    """
    tracker = ProjectTracker(db_manager=db_manager)
    
    results = {
        'projects_found': len(tracker.scan_project_files()),
        'database_sync': tracker.sync_to_database(dry_run=dry_run),
        'stats': tracker.get_stats()
    }
    
    return results
