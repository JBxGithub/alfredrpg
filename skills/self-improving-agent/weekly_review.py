#!/usr/bin/env python3
"""
Self-Improving Skills - Weekly Review Trigger

每週一自動執行：
1. 讀取本週的 .learnings/ 記錄
2. 分析重複模式
3. 生成改進建議
4. 提醒更新相關文件
"""

import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any


class SelfImprovingWeeklyReview:
    """Self-Improving Skills 每週回顧"""
    
    def __init__(self):
        self.workspace = Path.home() / "openclaw_workspace"
        self.learnings_dir = self.workspace / ".learnings"
        
    def read_weekly_learnings(self) -> Dict[str, List[Dict]]:
        """讀取本週學習記錄"""
        learnings = {
            'errors': [],
            'corrections': [],
            'patterns': [],
            'features': []
        }
        
        files = {
            'errors': ('ERRORS.md', 'error'),
            'learnings': ('LEARNINGS.md', 'learning'),
            'features': ('FEATURE_REQUESTS.md', 'feature')
        }
        
        for category, (filename, type_key) in files.items():
            filepath = self.learnings_dir / filename
            if filepath.exists():
                content = filepath.read_text(encoding='utf-8')
                entries = self._parse_entries(content, type_key)
                # 分類
                for entry in entries:
                    if self._is_this_week(entry.get('date', '')):
                        if 'correction' in entry.get('category', '').lower():
                            learnings['corrections'].append(entry)
                        elif type_key == 'error':
                            learnings['errors'].append(entry)
                        elif type_key == 'feature':
                            learnings['features'].append(entry)
                        else:
                            # 檢查是否為重複模式
                            if self._is_recurring_pattern(entry):
                                learnings['patterns'].append(entry)
                            else:
                                learnings.setdefault('others', []).append(entry)
        
        return learnings
    
    def _parse_entries(self, content: str, entry_type: str) -> List[Dict]:
        """解析學習記錄"""
        entries = []
        # 匹配 ## [ID] 標題
        pattern = r'##\s*\[([^\]]+)\]\s*(.+?)\n(.*?)(?=##\s*\[|$)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            entry_id = match[0]
            title = match[1].strip()
            body = match[2].strip()
            
            # 提取日期
            date_match = re.search(r'\*\*Logged\*\*:\s*(\d{4}-\d{2}-\d{2})', body)
            date = date_match.group(1) if date_match else ''
            
            # 提取分類
            cat_match = re.search(r'\*\*Category\*\*:\s*(\w+)', body)
            category = cat_match.group(1) if cat_match else 'general'
            
            entries.append({
                'id': entry_id,
                'title': title,
                'body': body,
                'date': date,
                'category': category,
                'type': entry_type
            })
        
        return entries
    
    def _is_this_week(self, date_str: str) -> bool:
        """檢查是否為本週"""
        if not date_str:
            return False
        try:
            entry_date = datetime.strptime(date_str, '%Y-%m-%d')
            # 獲取本週一
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())
            monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
            return entry_date >= monday
        except:
            return False
    
    def _is_recurring_pattern(self, entry: Dict) -> bool:
        """檢查是否為重複出現的模式"""
        # 檢查是否有 Recurrence-Count 或 See Also
        body = entry.get('body', '')
        has_recurrence = 'Recurrence-Count' in body and int(re.search(r'Recurrence-Count:\s*(\d+)', body).group(1)) > 1 if re.search(r'Recurrence-Count:\s*(\d+)', body) else False
        has_see_also = 'See Also:' in body
        return has_recurrence or has_see_also
    
    def analyze_patterns(self, learnings: Dict) -> List[Dict]:
        """分析重複模式"""
        patterns = []
        
        # 分析錯誤模式
        if learnings.get('errors'):
            error_areas = {}
            for err in learnings['errors']:
                area = err.get('category', 'unknown')
                error_areas[area] = error_areas.get(area, 0) + 1
            
            # 找出高頻錯誤區域
            for area, count in error_areas.items():
                if count >= 2:
                    patterns.append({
                        'type': 'error_pattern',
                        'area': area,
                        'count': count,
                        'suggestion': f'考慮為 {area} 創建預防性 Skill'
                    })
        
        # 分析糾正模式
        if learnings.get('corrections'):
            patterns.append({
                'type': 'correction_pattern',
                'count': len(learnings['corrections']),
                'suggestion': '審查常見糾正，更新相關文檔'
            })
        
        return patterns
    
    def generate_report(self) -> str:
        """生成週報"""
        learnings = self.read_weekly_learnings()
        patterns = self.analyze_patterns(learnings)
        
        lines = [
            "# Self-Improving Skills - 每週回顧",
            f"\n**回顧週期**: 本週 (週一至週日)",
            f"**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "\n---\n",
            "## 📊 本週統計",
            f"\n- 錯誤記錄: {len(learnings.get('errors', []))} 條",
            f"- 糾正記錄: {len(learnings.get('corrections', []))} 條",
            f"- 重複模式: {len(learnings.get('patterns', []))} 條",
            f"- 功能請求: {len(learnings.get('features', []))} 條",
            "\n---\n",
        ]
        
        # 重複模式分析
        if patterns:
            lines.extend([
                "## 🔍 重複模式分析",
                "\n發現以下重複出現的模式：",
            ])
            for p in patterns:
                lines.append(f"\n### {p['type']}")
                lines.append(f"- 區域/次數: {p.get('area', p.get('count'))}")
                lines.append(f"- 建議: {p['suggestion']}")
            lines.append("\n---\n")
        
        # 行動建議
        lines.extend([
            "## 🎯 行動建議",
            "\n基於本週學習，建議採取以下行動：",
        ])
        
        if learnings.get('errors'):
            lines.append("\n### 高優先級")
            lines.append("- [ ] 審查並修復本週記錄的錯誤")
            lines.append("- [ ] 為高頻錯誤創建預防措施")
        
        if learnings.get('corrections'):
            lines.append("\n### 中優先級")
            lines.append("- [ ] 更新相關 Skills 或文檔")
            lines.append("- [ ] 將常見糾正提煉為指導原則")
        
        if learnings.get('patterns'):
            lines.append("\n### 長期改進")
            lines.append("- [ ] 為重複模式創建自動化 Skill")
            lines.append("- [ ] 更新 SOUL.md 或 AGENTS.md")
        
        lines.extend([
            "\n---\n",
            "## 📝 待處理項目",
            "\n- [ ] 審查本週所有記錄",
            "- [ ] 更新相關 Skills",
            "- [ ] 同步到 AMS LearningEngine",
            "- [ ] 歸檔已解決的記錄",
            "\n---\n",
            f"*報告生成: {datetime.now().isoformat()}*",
        ])
        
        return '\n'.join(lines)
    
    def save_and_notify(self, report: str):
        """保存報告並顯示通知"""
        # 保存到 memory 目錄
        report_dir = self.workspace / "memory"
        report_dir.mkdir(exist_ok=True)
        
        filename = f"self-improving-weekly-{datetime.now().strftime('%Y-%m-%d')}.md"
        filepath = report_dir / filename
        
        filepath.write_text(report, encoding='utf-8')
        
        # 顯示摘要
        print("\n" + "=" * 60)
        print("🔄 Self-Improving Skills - 每週回顧完成")
        print("=" * 60)
        
        learnings = self.read_weekly_learnings()
        print(f"\n📊 本週統計:")
        print(f"   錯誤: {len(learnings.get('errors', []))} 條")
        print(f"   糾正: {len(learnings.get('corrections', []))} 條")
        print(f"   模式: {len(learnings.get('patterns', []))} 條")
        print(f"   功能: {len(learnings.get('features', []))} 條")
        
        print(f"\n📄 報告已保存: {filepath}")
        print("\n💡 建議：審查報告並採取行動項目")
        print("=" * 60)
        
        return filepath
    
    def run(self):
        """執行每週回顧"""
        report = self.generate_report()
        self.save_and_notify(report)
        return report


def main():
    """主入口"""
    reviewer = SelfImprovingWeeklyReview()
    reviewer.run()
    return 0


if __name__ == '__main__':
    sys.exit(main())
