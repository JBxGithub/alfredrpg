"""
技能掃描器 - 掃描技能目錄
"""

import os
from pathlib import Path
from typing import List, Dict, Optional


class SkillScanner:
    """掃描 OpenClaw 技能目錄"""
    
    def __init__(self, skills_dir: Optional[str] = None):
        if skills_dir is None:
            skills_dir = os.path.expanduser("~/.openclaw/skills")
        self.skills_dir = Path(skills_dir)
    
    def scan(self) -> List[Dict]:
        """掃描所有技能"""
        skills = []
        
        if not self.skills_dir.exists():
            return skills
        
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                skill_info = self._parse_skill(skill_path)
                if skill_info:
                    skills.append(skill_info)
        
        return skills
    
    def _parse_skill(self, skill_path: Path) -> Optional[Dict]:
        """解析單個技能"""
        skill_md = skill_path / "SKILL.md"
        
        if not skill_md.exists():
            return None
        
        try:
            content = skill_md.read_text(encoding='utf-8')
            return {
                'name': skill_path.name,
                'path': str(skill_path),
                'has_skill_md': True,
                'size': self._get_dir_size(skill_path)
            }
        except Exception:
            return None
    
    def _get_dir_size(self, path: Path) -> int:
        """獲取目錄大小"""
        total = 0
        for entry in path.rglob('*'):
            if entry.is_file():
                total += entry.stat().st_size
        return total
