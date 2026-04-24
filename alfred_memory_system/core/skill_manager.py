"""
Skill Manager - 技能管理器
從 hermes-memory-system 整合
管理 SKILL.md 文件，支持漸進式披露、版本控制和自動創建
"""

import os
import re
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict, field


@dataclass
class Skill:
    """技能定義數據類"""
    name: str
    description: str
    version: str
    content: str
    category: str = "general"
    tags: List[str] = None
    usage_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()


class SkillManager:
    """
    技能管理器
    - SKILL.md 格式管理
    - 漸進式披露 (Progressive Disclosure)
    - 技能版本控制
    - 自動創建與改進
    
    整合自 hermes-memory-system，為 AMS 提供技能管理功能
    """
    
    def __init__(self, skills_dir: Optional[str] = None):
        """
        初始化技能管理器
        
        Args:
            skills_dir: Skills 目錄路徑，默認為 ~/openclaw_workspace/skills
        """
        if skills_dir is None:
            skills_dir = os.path.expanduser("~/openclaw_workspace/skills")
        
        self.skills_dir = Path(skills_dir)
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self._skill_cache: Dict[str, Skill] = {}
    
    def _parse_skill_md(self, content: str) -> Dict[str, Any]:
        """解析 SKILL.md 文件，提取 YAML frontmatter 和正文"""
        # 提取 YAML frontmatter
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
                body = match.group(2)
            except yaml.YAMLError:
                frontmatter = {}
                body = content
        else:
            frontmatter = {}
            body = content
        
        return {
            'frontmatter': frontmatter,
            'body': body
        }
    
    def _build_skill_md(self, skill: Skill) -> str:
        """構建 SKILL.md 內容"""
        frontmatter = {
            'name': skill.name,
            'description': skill.description,
            'version': skill.version,
            'category': skill.category,
            'tags': skill.tags,
            'metadata': {
                'usage_count': skill.usage_count,
                'success_count': skill.success_count,
                'failure_count': skill.failure_count,
                'last_used': skill.last_used.isoformat() if skill.last_used else None,
                'created_at': skill.created_at.isoformat() if skill.created_at else None
            }
        }
        
        return f"""---
{yaml.dump(frontmatter, allow_unicode=True, sort_keys=False)}---

{skill.content}
"""
    
    def list_skills(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        """
        列出所有技能 (Level 0: 只返回名稱和描述)
        
        Returns:
            [{name, description, category}, ...]
        """
        skills = []
        
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    try:
                        content = skill_file.read_text(encoding='utf-8')
                        parsed = self._parse_skill_md(content)
                        fm = parsed['frontmatter']
                        
                        skill_info = {
                            'name': fm.get('name', skill_dir.name),
                            'description': fm.get('description', ''),
                            'category': fm.get('category', 'general'),
                            'path': str(skill_dir)
                        }
                        
                        if category is None or skill_info['category'] == category:
                            skills.append(skill_info)
                    
                    except Exception as e:
                        print(f"[SkillManager] Error parsing {skill_file}: {e}")
        
        return skills
    
    def get_skill(self, name: str, level: int = 1) -> Optional[Skill]:
        """
        獲取技能 (漸進式披露)
        
        Args:
            name: 技能名稱
            level: 披露層級 (1=完整內容, 2=參考文件, 3=特定部分)
        
        Returns:
            Skill 對象或 None
        """
        # 檢查緩存
        if name in self._skill_cache:
            return self._skill_cache[name]
        
        skill_dir = self.skills_dir / name
        skill_file = skill_dir / "SKILL.md"
        
        if not skill_file.exists():
            return None
        
        try:
            content = skill_file.read_text(encoding='utf-8')
            parsed = self._parse_skill_md(content)
            fm = parsed['frontmatter']
            
            skill = Skill(
                name=fm.get('name', name),
                description=fm.get('description', ''),
                version=fm.get('version', '1.0.0'),
                content=parsed['body'],
                category=fm.get('category', 'general'),
                tags=fm.get('tags', []),
                usage_count=fm.get('metadata', {}).get('usage_count', 0),
                success_count=fm.get('metadata', {}).get('success_count', 0),
                failure_count=fm.get('metadata', {}).get('failure_count', 0),
                last_used=datetime.fromisoformat(fm['metadata']['last_used']) if fm.get('metadata', {}).get('last_used') else None,
                created_at=datetime.fromisoformat(fm['metadata']['created_at']) if fm.get('metadata', {}).get('created_at') else None
            )
            
            self._skill_cache[name] = skill
            return skill
        
        except Exception as e:
            print(f"[SkillManager] Error loading skill {name}: {e}")
            return None
    
    def create_skill(self, name: str, description: str, content: str,
                     category: str = "general", tags: List[str] = None,
                     auto_created: bool = False) -> Skill:
        """
        創建新技能
        
        Args:
            name: 技能名稱
            description: 技能描述
            content: 技能內容 (Markdown)
            category: 分類
            tags: 標籤列表
            auto_created: 是否自動創建
        
        Returns:
            創建的 Skill 對象
        """
        skill = Skill(
            name=name,
            description=description,
            version="1.0.0",
            content=content,
            category=category,
            tags=tags or []
        )
        
        # 創建技能目錄
        skill_dir = self.skills_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # 寫入 SKILL.md
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(self._build_skill_md(skill), encoding='utf-8')
        
        # 更新緩存
        self._skill_cache[name] = skill
        
        return skill
    
    def update_skill(self, name: str, content: Optional[str] = None,
                     description: Optional[str] = None,
                     version: Optional[str] = None) -> bool:
        """
        更新技能
        
        Returns:
            是否成功
        """
        skill = self.get_skill(name)
        if not skill:
            return False
        
        if content:
            skill.content = content
        if description:
            skill.description = description
        if version:
            skill.version = version
        
        # 寫入文件
        skill_dir = self.skills_dir / name
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(self._build_skill_md(skill), encoding='utf-8')
        
        # 更新緩存
        self._skill_cache[name] = skill
        
        return True
    
    def record_usage(self, name: str, success: bool = True):
        """記錄技能使用"""
        skill = self.get_skill(name)
        if skill:
            skill.usage_count += 1
            if success:
                skill.success_count += 1
            else:
                skill.failure_count += 1
            skill.last_used = datetime.now()
            
            # 更新文件
            self.update_skill(name)
    
    def get_skill_stats(self) -> Dict[str, Any]:
        """獲取技能統計"""
        skills = self.list_skills()
        
        total = len(skills)
        by_category = {}
        
        for skill_info in skills:
            cat = skill_info['category']
            by_category[cat] = by_category.get(cat, 0) + 1
        
        return {
            'total_skills': total,
            'by_category': by_category,
            'skills_dir': str(self.skills_dir)
        }
    
    def suggest_improvements(self, name: str) -> List[str]:
        """
        分析技能並建議改進
        
        Returns:
            改進建議列表
        """
        skill = self.get_skill(name)
        if not skill:
            return []
        
        suggestions = []
        
        # 檢查使用頻率
        if skill.usage_count < 3:
            suggestions.append(f"技能使用次數較少 ({skill.usage_count} 次)，可能需要更多推廣")
        
        # 檢查內容長度
        if len(skill.content) < 500:
            suggestions.append("技能內容較短，可以添加更多細節或示例")
        
        # 檢查是否包含常見章節
        sections = ['When to Use', 'Procedure', 'Examples', 'Pitfalls']
        for section in sections:
            if section not in skill.content:
                suggestions.append(f"建議添加 '{section}' 章節")
        
        # 檢查失敗率
        if skill.usage_count > 0:
            failure_rate = skill.failure_count / skill.usage_count
            if failure_rate > 0.3:
                suggestions.append(f"失敗率較高 ({failure_rate*100:.1f}%)，建議檢查和改進")
        
        return suggestions
    
    def search_skills(self, query: str) -> List[Dict[str, str]]:
        """搜索技能"""
        all_skills = self.list_skills()
        results = []
        
        query_lower = query.lower()
        for skill in all_skills:
            if (query_lower in skill['name'].lower() or 
                query_lower in skill['description'].lower()):
                results.append(skill)
        
        return results
    
    def delete_skill(self, name: str) -> bool:
        """刪除技能"""
        skill_dir = self.skills_dir / name
        
        if not skill_dir.exists():
            return False
        
        # 刪除目錄
        import shutil
        shutil.rmtree(skill_dir)
        
        # 清除緩存
        if name in self._skill_cache:
            del self._skill_cache[name]
        
        return True
    
    def sync_to_database(self, db_manager) -> Tuple[int, int]:
        """
        將技能同步到數據庫
        
        Args:
            db_manager: 數據庫管理器實例
        
        Returns:
            (添加數量, 更新數量)
        """
        added = 0
        updated = 0
        
        for skill_info in self.list_skills():
            name = skill_info['name']
            skill = self.get_skill(name)
            
            if not skill:
                continue
            
            # 檢查數據庫中是否已存在
            existing = db_manager.get_skill(name)
            
            if existing:
                # 更新使用統計
                db_manager.update_skill_usage(name, success=True)
                updated += 1
            else:
                # 添加新技能
                import uuid
                db_manager.add_skill(
                    skill_id=str(uuid.uuid4())[:8],
                    name=skill.name,
                    description=skill.description,
                    content=skill.content,
                    auto_created=False
                )
                added += 1
        
        return added, updated
