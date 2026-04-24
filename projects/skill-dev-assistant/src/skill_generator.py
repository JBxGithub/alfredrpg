"""
Skill Generator - 兼容版
用於 alfred-cli 直接導入
"""

from pathlib import Path
from typing import Optional
from datetime import datetime


class SkillGenerator:
    """技能生成器"""
    
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            output_dir = Path.home() / "openclaw_workspace" / "skills"
        self.output_dir = Path(output_dir)
    
    def create(self, name: str, category: str = 'general') -> str:
        """創建新技能"""
        skill_dir = self.output_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # 創建 SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(f"""---
name: {name}
description: "{name} skill"
version: 1.0.0
category: {category}
---

# {name}

## Description

This is a generated skill.

## Usage

TODO: Add usage instructions.
""")
        
        # 創建 src 目錄
        src_dir = skill_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        # 創建 __init__.py
        init_file = src_dir / "__init__.py"
        init_file.write_text(f'"""{name} skill"""\n')
        
        return str(skill_dir)
