"""
報告生成器 - 生成分析報告
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


class SkillReporter:
    """生成技能分析報告"""
    
    def generate_markdown(self, analysis: Dict[str, Any]) -> str:
        """生成 Markdown 報告"""
        lines = [
            "# 技能生態分析報告",
            f"",
            f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            "## 概覽",
            f"",
            f"- **總技能數**: {analysis.get('total_skills', 0)}",
            f"",
            "## 分類分佈",
            f""
        ]
        
        # 分類
        categories = analysis.get('categories', {})
        for category, skills in categories.items():
            lines.append(f"### {category}")
            lines.append(f"")
            for skill in skills:
                lines.append(f"- {skill}")
            lines.append(f"")
        
        # 重複
        duplicates = analysis.get('duplicates', [])
        if duplicates:
            lines.extend([
                "## ⚠️ 重複技能",
                f"",
                f"發現 {len(duplicates)} 個可能重複:",
                f""
            ])
            for dup in duplicates:
                lines.append(f"- **{dup['name']}**: {', '.join(dup['paths'])}")
            lines.append(f"")
        
        # 建議
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            lines.extend([
                "## 💡 建議",
                f""
            ])
            for rec in recommendations:
                lines.append(f"- {rec}")
            lines.append(f"")
        
        return '\n'.join(lines)
    
    def generate_json(self, analysis: Dict[str, Any]) -> str:
        """生成 JSON 報告"""
        return json.dumps(analysis, indent=2, ensure_ascii=False)
    
    def save_report(self, analysis: Dict[str, Any], output_dir: str = None):
        """保存報告"""
        if output_dir is None:
            output_dir = Path.home() / "openclaw_workspace" / "reports"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存 Markdown
        md_path = output_dir / f"skill-analysis-{datetime.now().strftime('%Y%m%d')}.md"
        md_path.write_text(self.generate_markdown(analysis), encoding='utf-8')
        
        # 保存 JSON
        json_path = output_dir / f"skill-analysis-{datetime.now().strftime('%Y%m%d')}.json"
        json_path.write_text(self.generate_json(analysis), encoding='utf-8')
        
        return str(md_path), str(json_path)
