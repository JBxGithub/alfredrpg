"""
SKILL.md 解析器 - 解析技能文檔
"""

import re
from pathlib import Path
from typing import Dict, Optional, List


class SkillParser:
    """解析 SKILL.md 文件"""
    
    def parse(self, skill_path: str) -> Optional[Dict]:
        """解析技能文檔"""
        skill_md = Path(skill_path) / "SKILL.md"
        
        if not skill_md.exists():
            return None
        
        try:
            content = skill_md.read_text(encoding='utf-8')
            return self._parse_content(content, skill_path)
        except Exception as e:
            return {'error': str(e), 'path': skill_path}
    
    def _parse_content(self, content: str, skill_path: str) -> Dict:
        """解析文檔內容"""
        # 解析 frontmatter
        frontmatter = self._parse_frontmatter(content)
        
        # 提取標題
        title = self._extract_title(content)
        
        # 提取描述
        description = self._extract_description(content)
        
        return {
            'name': frontmatter.get('name', Path(skill_path).name),
            'title': title,
            'description': description,
            'version': frontmatter.get('version', 'unknown'),
            'category': frontmatter.get('category', 'uncategorized'),
            'tags': frontmatter.get('tags', []),
            'path': skill_path
        }
    
    def _parse_frontmatter(self, content: str) -> Dict:
        """解析 YAML frontmatter"""
        frontmatter = {}
        
        # 匹配 --- 包圍的 frontmatter
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            yaml_content = match.group(1)
            
            # 簡單解析 key: value
            for line in yaml_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 處理列表
                    if value.startswith('[') and value.endswith(']'):
                        value = [v.strip().strip('"\'') for v in value[1:-1].split(',')]
                    
                    frontmatter[key] = value
        
        return frontmatter
    
    def _extract_title(self, content: str) -> str:
        """提取標題"""
        # 找第一個 # 標題
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        return match.group(1).strip() if match else "Untitled"
    
    def _extract_description(self, content: str) -> str:
        """提取描述"""
        # 找第一個段落
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('---'):
                return line[:200]  # 限制長度
        return ""
