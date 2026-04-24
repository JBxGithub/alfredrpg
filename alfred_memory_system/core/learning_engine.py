"""
Learning Engine - 學習引擎
從 hermes-memory-system 整合
自適應學習機制：自動創建技能、追蹤使用情況、提供改進建議
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class TaskAnalysis:
    """任務分析結果"""
    task_description: str
    complexity_score: int
    should_create_skill: bool
    reasons: List[str]
    steps: List[str]
    errors_encountered: List[str]


@dataclass
class LearningEntry:
    """學習記錄條目"""
    id: str
    type: str  # 'error', 'correction', 'improvement', 'pattern'
    content: str
    category: str
    source_session: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime] = None
    status: str = "pending"  # 'pending', 'resolved', 'promoted'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'category': self.category,
            'source_session': self.source_session,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'status': self.status
        }


class LearningEngine:
    """
    自適應學習引擎
    - 複雜任務後自動創建技能
    - 技能使用頻率追蹤
    - 技能改進建議
    - 定期自我提醒 (Nudges)
    - 錯誤記錄和改進建議
    
    整合自 hermes-memory-system，為 AMS 提供學習能力
    """
    
    # 默認配置
    DEFAULT_CONFIG = {
        'complexity_threshold': 5,  # 步驟數閾值
        'duration_threshold': 10,   # 持續時間閾值（分鐘）
        'min_tool_calls': 5,        # 最小 tool calls 數
        'include_errors': True,     # 是否包含錯誤處理
        'include_code': True,       # 是否包含代碼示例
        'usage_threshold': 3,       # 進化前最小使用次數
        'nudges_enabled': True,     # 是否啟用提醒
        'nudge_frequency': 'daily', # 提醒頻率
    }
    
    def __init__(self, 
                 db_manager=None,
                 skill_manager=None,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化學習引擎
        
        Args:
            db_manager: 數據庫管理器實例
            skill_manager: 技能管理器實例
            config: 配置字典
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.db = db_manager
        self.skills = skill_manager
        
        # 學習狀態文件路徑
        workspace = os.path.expanduser("~/openclaw_workspace/alfred_memory_system")
        self.state_file = Path(workspace) / 'data' / 'learning_state.json'
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """加載學習狀態"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        
        return {
            'task_history': [],
            'skill_creation_log': [],
            'last_nudge': None,
            'improvement_queue': [],
            'learning_entries': []
        }
    
    def _save_state(self):
        """保存學習狀態"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def analyze_task(self, task_description: str, steps: List[str],
                     duration_minutes: float = 0, 
                     errors_encountered: List[str] = None,
                     tool_calls_count: int = 0) -> TaskAnalysis:
        """
        分析任務複雜度並決定是否創建技能
        
        Args:
            task_description: 任務描述
            steps: 執行步驟列表
            duration_minutes: 任務持續時間
            errors_encountered: 遇到的錯誤
            tool_calls_count: tool calls 數量
        
        Returns:
            TaskAnalysis 對象
        """
        # 計算複雜度分數
        complexity_score = 0
        reasons = []
        
        # 步驟數檢查
        if len(steps) >= self.config['complexity_threshold']:
            complexity_score += 30
            reasons.append(f"步驟數達到 {len(steps)}")
        
        # 持續時間檢查
        if duration_minutes >= self.config['duration_threshold']:
            complexity_score += 30
            reasons.append(f"持續時間 {duration_minutes:.1f} 分鐘")
        
        # Tool calls 檢查
        if tool_calls_count >= self.config['min_tool_calls']:
            complexity_score += 20
            reasons.append(f"Tool calls 數量 {tool_calls_count}")
        
        # 錯誤處理檢查
        if errors_encountered and len(errors_encountered) > 0:
            complexity_score += 20
            reasons.append(f"遇到 {len(errors_encountered)} 個錯誤並解決")
        
        # 綜合評估
        should_create_skill = complexity_score >= 50
        
        result = TaskAnalysis(
            task_description=task_description,
            complexity_score=complexity_score,
            should_create_skill=should_create_skill,
            reasons=reasons,
            steps=steps,
            errors_encountered=errors_encountered or []
        )
        
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
    
    def auto_create_skill(self, task_analysis: TaskAnalysis) -> Optional[Dict[str, str]]:
        """
        根據任務分析自動創建技能
        
        Returns:
            創建的技能信息或 None
        """
        if not task_analysis.should_create_skill:
            return None
        
        if not self.skills:
            return None
        
        # 生成技能名稱
        task_desc = task_analysis.task_description
        skill_name = self._generate_skill_name(task_desc)
        
        # 生成技能內容
        content = self._generate_skill_content(task_analysis)
        
        try:
            # 創建技能
            skill = self.skills.create_skill(
                name=skill_name,
                description=task_desc[:200],
                content=content,
                category=self._categorize_task(task_desc),
                tags=['auto-created'],
                auto_created=True
            )
            
            # 記錄
            self.state['skill_creation_log'].append({
                'timestamp': datetime.now().isoformat(),
                'skill_name': skill_name,
                'task': task_desc,
                'complexity_score': task_analysis.complexity_score
            })
            self._save_state()
            
            return {
                'name': skill_name,
                'description': skill.description,
                'category': skill.category
            }
        except Exception as e:
            print(f"[LearningEngine] Failed to create skill: {e}")
            return None
    
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
            'analyze': 'analysis',
            'integrate': 'integration',
            'extract': 'extraction',
            'sync': 'sync',
            'monitor': 'monitoring',
            'manage': 'management'
        }
        
        # 尋找關鍵詞
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in verb_map:
                return verb_map[clean_word]
        
        # 默認使用前三個詞
        clean_words = [re.sub(r'[^\w]', '', w) for w in words[:3] if w]
        return '-'.join(clean_words) if clean_words else 'auto-skill'
    
    def _generate_skill_content(self, task_analysis: TaskAnalysis) -> str:
        """生成技能內容"""
        lines = [
            f"# {task_analysis.task_description}",
            "",
            "## When to Use",
            f"This skill is useful when you need to {task_analysis.task_description.lower()}.",
            "",
            "## Procedure",
        ]
        
        # 添加步驟
        for i, step in enumerate(task_analysis.steps, 1):
            lines.append(f"{i}. {step}")
        
        lines.append("")
        
        # 添加錯誤處理
        if self.config['include_errors'] and task_analysis.errors_encountered:
            lines.extend([
                "## Pitfalls",
                "Common issues and their solutions:",
                ""
            ])
            for error in task_analysis.errors_encountered:
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
        
        # 添加代碼示例
        if self.config['include_code']:
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
            'data': ['data', 'etl', 'analytics', 'ml', 'model', 'training'],
            'memory': ['memory', 'remember', 'recall', 'store'],
            'integration': ['integrate', 'sync', 'connect', 'import', 'export']
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
        if not self.skills:
            return []
        
        suggestions = []
        all_skills = self.skills.list_skills()
        
        for skill_info in all_skills:
            skill = self.skills.get_skill(skill_info['name'])
            if not skill:
                continue
            
            # 檢查使用次數
            if skill.usage_count >= self.config['usage_threshold']:
                skill_suggestions = self.skills.suggest_improvements(skill.name)
                
                if skill_suggestions:
                    suggestions.append({
                        'skill_name': skill.name,
                        'usage_count': skill.usage_count,
                        'suggestions': skill_suggestions
                    })
        
        return suggestions
    
    def add_learning(self, entry_type: str, content: str, 
                     category: str = "general",
                     source_session: Optional[str] = None) -> str:
        """
        添加學習記錄
        
        Args:
            entry_type: 類型 ('error', 'correction', 'improvement', 'pattern')
            content: 內容
            category: 分類
            source_session: 來源 session ID
        
        Returns:
            記錄 ID
        """
        import uuid
        entry_id = str(uuid.uuid4())[:8]
        
        entry = LearningEntry(
            id=entry_id,
            type=entry_type,
            content=content,
            category=category,
            source_session=source_session,
            created_at=datetime.now()
        )
        
        # 保存到狀態
        self.state['learning_entries'].append(entry.to_dict())
        self._save_state()
        
        # 同時保存到數據庫（如果有）
        if self.db:
            try:
                self.db.add_learning(
                    entry_id=entry_id,
                    entry_type=entry_type,
                    content=content,
                    category=category,
                    source_session=source_session
                )
            except Exception as e:
                print(f"[LearningEngine] Failed to save to database: {e}")
        
        return entry_id
    
    def get_learnings(self, entry_type: Optional[str] = None,
                      status: Optional[str] = None) -> List[Dict[str, Any]]:
        """獲取學習記錄"""
        entries = self.state.get('learning_entries', [])
        
        if entry_type:
            entries = [e for e in entries if e['type'] == entry_type]
        
        if status:
            entries = [e for e in entries if e['status'] == status]
        
        # 按時間倒序
        entries.sort(key=lambda x: x['created_at'], reverse=True)
        
        return entries
    
    def resolve_learning(self, entry_id: str) -> bool:
        """標記學習記錄為已解決"""
        for entry in self.state.get('learning_entries', []):
            if entry['id'] == entry_id:
                entry['status'] = 'resolved'
                entry['resolved_at'] = datetime.now().isoformat()
                self._save_state()
                return True
        return False
    
    def generate_nudge(self) -> Optional[Dict[str, str]]:
        """
        生成提醒 (Nudge)
        
        Returns:
            提醒內容或 None
        """
        if not self.config['nudges_enabled']:
            return None
        
        # 檢查上次提醒時間
        last_nudge = self.state.get('last_nudge')
        if last_nudge:
            last_time = datetime.fromisoformat(last_nudge)
            freq = self.config['nudge_frequency']
            
            if freq == 'daily':
                if datetime.now() - last_time < timedelta(days=1):
                    return None
            elif freq == 'weekly':
                if datetime.now() - last_time < timedelta(weeks=1):
                    return None
        
        # 選擇提醒類型
        # 如果有待處理的學習記錄
        pending = self.get_learnings(status='pending')
        if pending:
            nudge = {
                'type': 'learning_review',
                'title': '🧠 Learning Review',
                'content': f"You have {len(pending)} pending learnings to review.",
                'action': 'Check learning entries'
            }
        
        # 如果有技能需要改進
        elif self.state.get('improvement_queue'):
            skill_name = self.state['improvement_queue'][0]
            nudge = {
                'type': 'skill_practice',
                'title': '🔧 Skill Improvement',
                'content': f"The skill '{skill_name}' could be improved.",
                'action': f'Review skill: {skill_name}'
            }
        
        # 默認提醒
        else:
            nudge = {
                'type': 'knowledge_persist',
                'title': '💡 Knowledge Persistence',
                'content': 'Have you learned anything new today worth remembering?',
                'action': 'Add new learning'
            }
        
        # 更新上次提醒時間
        self.state['last_nudge'] = datetime.now().isoformat()
        self._save_state()
        
        return nudge
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """獲取學習統計"""
        entries = self.state.get('learning_entries', [])
        
        return {
            'tasks_analyzed': len(self.state.get('task_history', [])),
            'skills_auto_created': len(self.state.get('skill_creation_log', [])),
            'total_learnings': len(entries),
            'pending_learnings': len([e for e in entries if e['status'] == 'pending']),
            'resolved_learnings': len([e for e in entries if e['status'] == 'resolved']),
            'last_nudge': self.state.get('last_nudge')
        }
