"""
Learning Engine - Adaptive Learning Mechanism
Auto-creates skills, tracks usage, and provides improvement suggestions
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path

from .memory_manager import MemoryManager
from .session_store import SessionStore
from .skill_manager import SkillManager


class LearningEngine:
    """
    自適應學習引擎
    - 複雜任務後自動創建技能
    - 技能使用頻率追蹤
    - 技能改進建議
    - 定期自我提醒 (Nudges)
    """
    
    def __init__(self, config: Dict[str, Any],
                 memory_manager: MemoryManager,
                 session_store: SessionStore,
                 skill_manager: SkillManager):
        """初始化學習引擎"""
        self.config = config
        self.memory = memory_manager
        self.sessions = session_store
        self.skills = skill_manager
        
        # 學習狀態文件
        self.state_file = Path(config['paths']['workspace']) / 'learning_state.json'
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """加載學習狀態"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'task_history': [],
            'skill_creation_log': [],
            'last_nudge': None,
            'improvement_queue': []
        }
    
    def _save_state(self):
        """保存學習狀態"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def analyze_task(self, task_description: str, steps: List[str],
                     duration_minutes: float, errors_encountered: List[str] = None) -> Dict[str, Any]:
        """
        分析任務複雜度並決定是否創建技能
        
        Args:
            task_description: 任務描述
            steps: 執行步驟列表
            duration_minutes: 任務持續時間
            errors_encountered: 遇到的錯誤
        
        Returns:
            分析結果
        """
        config = self.config['learning']['auto_creation']
        
        # 計算複雜度分數
        complexity_score = 0
        reasons = []
        
        # 步驟數檢查
        if len(steps) >= config['complexity_threshold']:
            complexity_score += 30
            reasons.append(f"步驟數達到 {len(steps)}")
        
        # 持續時間檢查
        if duration_minutes >= config['duration_threshold']:
            complexity_score += 30
            reasons.append(f"持續時間 {duration_minutes:.1f} 分鐘")
        
        # 錯誤處理檢查
        if errors_encountered and len(errors_encountered) > 0:
            complexity_score += 20
            reasons.append(f"遇到 {len(errors_encountered)} 個錯誤並解決")
        
        # 綜合評估
        should_create_skill = complexity_score >= 50
        
        result = {
            'task_description': task_description,
            'complexity_score': complexity_score,
            'should_create_skill': should_create_skill,
            'reasons': reasons,
            'steps': steps,
            'errors_encountered': errors_encountered or []
        }
        
        # 記錄到歷史
        self.state['task_history'].append({
            'timestamp': datetime.now().isoformat(),
            'task': task_description,
            'complexity_score': complexity_score,
            'skill_created': should_create_skill
        })
        
        # 只保留最近 100 條
        self.state['task_history'] = self.state['task_history'][-100:]
        self._save_state()
        
        return result
    
    def auto_create_skill(self, task_analysis: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        根據任務分析自動創建技能
        
        Returns:
            創建的技能信息或 None
        """
        if not task_analysis['should_create_skill']:
            return None
        
        # 生成技能名稱
        task_desc = task_analysis['task_description']
        skill_name = self._generate_skill_name(task_desc)
        
        # 生成技能內容
        content = self._generate_skill_content(task_analysis)
        
        # 創建技能
        skill = self.skills.create_skill(
            name=skill_name,
            description=task_desc[:200],
            content=content,
            category=self._categorize_task(task_desc),
            tags=['auto-created']
        )
        
        # 記錄
        self.state['skill_creation_log'].append({
            'timestamp': datetime.now().isoformat(),
            'skill_name': skill_name,
            'task': task_desc,
            'complexity_score': task_analysis['complexity_score']
        })
        self._save_state()
        
        return {
            'name': skill_name,
            'description': skill.description,
            'category': skill.category
        }
    
    def _generate_skill_name(self, task_description: str) -> str:
        """從任務描述生成技能名稱"""
        # 簡單的關鍵詞提取
        words = task_description.lower().split()
        
        # 常見動詞映射
        verb_map = {
            'deploy': 'deployment',
            'setup': 'setup',
            'configure': 'configuration',
            'install': 'installation',
            'build': 'building',
            'create': 'creation',
            'migrate': 'migration',
            'optimize': 'optimization',
            'debug': 'debugging',
            'analyze': 'analysis'
        }
        
        # 尋找關鍵詞
        for word in words:
            if word in verb_map:
                return verb_map[word]
        
        # 默認使用前三個詞
        return '-'.join(words[:3])
    
    def _generate_skill_content(self, task_analysis: Dict[str, Any]) -> str:
        """生成技能內容"""
        config = self.config['learning']['auto_creation']
        
        lines = [
            f"# {task_analysis['task_description']}",
            "",
            "## When to Use",
            f"This skill is useful when you need to {task_analysis['task_description'].lower()}.",
            "",
            "## Procedure",
        ]
        
        # 添加步驟
        for i, step in enumerate(task_analysis['steps'], 1):
            lines.append(f"{i}. {step}")
        
        lines.append("")
        
        # 添加錯誤處理 (如果配置啟用)
        if config['include_errors'] and task_analysis['errors_encountered']:
            lines.extend([
                "## Pitfalls",
                "Common issues and their solutions:",
                ""
            ])
            for error in task_analysis['errors_encountered']:
                lines.append(f"- **Issue**: {error}")
                lines.append(f"  - **Solution**: [Add solution here]")
            lines.append("")
        
        # 添加驗證
        lines.extend([
            "## Verification",
            "To verify this skill was applied correctly:",
            "- [ ] Check [specific outcome]",
            "- [ ] Confirm [expected result]",
            ""
        ])
        
        # 添加代碼示例 (如果配置啟用)
        if config['include_code']:
            lines.extend([
                "## Examples",
                "",
                "```bash",
                "# Example command",
                "[Add example here]",
                "```",
                ""
            ])
        
        return '\n'.join(lines)
    
    def _categorize_task(self, task_description: str) -> str:
        """對任務進行分類"""
        categories = {
            'devops': ['deploy', 'server', 'docker', 'kubernetes', 'k8s', 'ci/cd', 'pipeline'],
            'database': ['database', 'sql', 'migration', 'schema', 'query'],
            'frontend': ['react', 'vue', 'angular', 'css', 'ui', 'component'],
            'backend': ['api', 'server', 'endpoint', 'microservice'],
            'security': ['auth', 'security', 'encrypt', 'password', 'token'],
            'data': ['data', 'etl', 'analytics', 'ml', 'model', 'training']
        }
        
        task_lower = task_description.lower()
        for category, keywords in categories.items():
            if any(kw in task_lower for kw in keywords):
                return category
        
        return 'general'
    
    def check_skill_improvements(self) -> List[Dict[str, Any]]:
        """
        檢查需要改進的技能
        
        Returns:
            改進建議列表
        """
        config = self.config['learning']['skill_improvement']
        
        if not config['enabled']:
            return []
        
        suggestions = []
        all_skills = self.skills.list_skills()
        
        for skill_info in all_skills:
            skill = self.skills.get_skill(skill_info['name'])
            if not skill:
                continue
            
            # 檢查使用次數
            if skill.usage_count >= config['usage_threshold']:
                skill_suggestions = self.skills.suggest_improvements(skill.name)
                
                if skill_suggestions:
                    suggestions.append({
                        'skill_name': skill.name,
                        'usage_count': skill.usage_count,
                        'suggestions': skill_suggestions
                    })
        
        return suggestions
    
    def generate_nudge(self) -> Optional[Dict[str, str]]:
        """
        生成提醒 (Nudge)
        
        Returns:
            提醒內容或 None
        """
        config = self.config['learning']['nudges']
        
        if not config['enabled']:
            return None
        
        # 檢查上次提醒時間
        last_nudge = self.state.get('last_nudge')
        if last_nudge:
            last_time = datetime.fromisoformat(last_nudge)
            if config['frequency'] == 'daily':
                if datetime.now() - last_time < timedelta(days=1):
                    return None
            elif config['frequency'] == 'weekly':
                if datetime.now() - last_time < timedelta(weeks=1):
                    return None
        
        # 選擇提醒類型
        nudge_types = config['types']
        
        # 根據當前狀態選擇最合適的提醒
        memory_stats = self.memory.get_stats()
        skill_stats = self.skills.get_skill_stats()
        
        # 如果記憶使用率過高，提醒回顧
        if memory_stats['memory']['usage_percent'] > 80:
            nudge = {
                'type': 'memory_review',
                'title': '🧠 Memory Review Reminder',
                'content': f"Your MEMORY.md is {memory_stats['memory']['usage_percent']}% full. Consider reviewing and consolidating old entries.",
                'action': 'Run `hermes memory review` to see suggestions'
            }
        
        # 如果有技能需要改進
        elif self.state['improvement_queue']:
            skill_name = self.state['improvement_queue'][0]
            nudge = {
                'type': 'skill_practice',
                'title': '🔧 Skill Improvement Opportunity',
                'content': f"The skill '{skill_name}' has been used frequently. Consider improving it based on your experience.",
                'action': f'Run `hermes skill improve {skill_name}`'
            }
        
        # 默認提醒
        else:
            nudge = {
                'type': 'knowledge_persist',
                'title': '💡 Knowledge Persistence',
                'content': 'Have you learned anything new today worth remembering?',
                'action': 'Use `hermes memory add "..."` to save important insights'
            }
        
        # 更新上次提醒時間
        self.state['last_nudge'] = datetime.now().isoformat()
        self._save_state()
        
        return nudge
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """獲取學習統計"""
        return {
            'tasks_analyzed': len(self.state['task_history']),
            'skills_auto_created': len(self.state['skill_creation_log']),
            'last_nudge': self.state.get('last_nudge'),
            'improvement_queue_size': len(self.state.get('improvement_queue', []))
        }
