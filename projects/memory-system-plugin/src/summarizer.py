"""
摘要生成器模組 (Summarizer Module)
負責自動生成對話摘要，提取決策、行動項目、思考過程、情感脈絡

Author: ClawTeam - Summarizer
Date: 2026-04-08
Version: 1.0.0
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum


class SummaryType(Enum):
    """摘要類型"""
    SESSION = "session"           # Session 摘要
    DAILY = "daily"               # 每日摘要
    TOPIC = "topic"               # 主題摘要
    DECISION = "decision"         # 決策摘要


@dataclass
class Decision:
    """決策記錄"""
    content: str                  # 決策內容
    reason: str                   # 決策原因
    timestamp: str                # 時間戳
    impact: str = ""              # 影響評估
    alternatives: List[str] = field(default_factory=list)  # 替代方案
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ActionItem:
    """行動項目"""
    content: str                  # 項目內容
    status: str                   # 狀態: pending, completed, cancelled
    priority: str                 # 優先級: high, medium, low
    deadline: Optional[str] = None  # 截止日期
    assignee: str = ""            # 負責人
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ThinkingProcess:
    """思考過程"""
    problem: str                  # 問題描述
    analysis: str                 # 分析過程
    conclusion: str               # 結論
    alternatives_considered: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EmotionalContext:
    """情感脈絡"""
    primary_emotion: str          # 主要情緒
    intensity: int                # 強度 1-10
    triggers: List[str] = field(default_factory=list)  # 觸發因素
    trend: str = ""               # 趨勢: improving, stable, declining
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConversationSummary:
    """對話摘要數據類"""
    id: str
    session_id: str
    timestamp: str
    summary_type: SummaryType
    
    # 核心內容
    title: str                    # 摘要標題
    overview: str                 # 概述
    topics: List[str] = field(default_factory=list)  # 主題標籤
    
    # 結構化數據
    decisions: List[Decision] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    thinking_processes: List[ThinkingProcess] = field(default_factory=list)
    emotional_context: Optional[EmotionalContext] = None
    
    # 關鍵數據
    key_data: Dict[str, Any] = field(default_factory=dict)
    
    # 下次繼續
    next_continue: str = ""       # 建議下次切入點
    
    # 元數據
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "summary_type": self.summary_type.value,
            "title": self.title,
            "overview": self.overview,
            "topics": self.topics,
            "decisions": [d.to_dict() for d in self.decisions],
            "action_items": [a.to_dict() for a in self.action_items],
            "thinking_processes": [t.to_dict() for t in self.thinking_processes],
            "emotional_context": self.emotional_context.to_dict() if self.emotional_context else None,
            "key_data": self.key_data,
            "next_continue": self.next_continue,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSummary':
        """從字典創建實例"""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            timestamp=data["timestamp"],
            summary_type=SummaryType(data["summary_type"]),
            title=data["title"],
            overview=data["overview"],
            topics=data.get("topics", []),
            decisions=[Decision(**d) for d in data.get("decisions", [])],
            action_items=[ActionItem(**a) for a in data.get("action_items", [])],
            thinking_processes=[ThinkingProcess(**t) for t in data.get("thinking_processes", [])],
            emotional_context=EmotionalContext(**data["emotional_context"]) if data.get("emotional_context") else None,
            key_data=data.get("key_data", {}),
            next_continue=data.get("next_continue", ""),
            metadata=data.get("metadata", {})
        )


class ContentAnalyzer:
    """內容分析器 - 使用規則和模式識別提取信息"""
    
    def __init__(self):
        # 決策關鍵詞模式
        self.decision_patterns = [
            r'(?:決定|決議|確定|選擇|採用|使用|採納).{0,30}(?:使用|採用|保留|刪除|調整|修改|設置|配置)',
            r'(?:我們|建議|應該|需要).{0,20}(?:使用|採用|保留|刪除|調整|修改|設置|配置)',
            r'(?:方案|策略|方法|方式).{0,10}(?:是|為|選擇|確定)',
            r'(?:最終|最後|總結|結論).{0,15}(?:決定|選擇|採用|使用)',
        ]
        
        # 行動項目模式
        self.action_patterns = [
            r'(?:待完成|待辦|TODO|待處理|需要|必須|應該).{0,30}(?:完成|處理|開發|測試|部署|檢查)',
            r'(?:下一步|接下來|之後|稍後).{0,20}(?:需要|要|將|會).{0,20}(?:完成|處理|開發|測試)',
            r'(?:任務|工作|事項).{0,10}(?:是|為|包括)',
        ]
        
        # 情感關鍵詞
        self.emotion_keywords = {
            '積極': ['積極', '興奮', '滿意', '開心', '高興', '期待', '樂觀', '自信', '滿足', '愉快'],
            '消極': ['消極', '沮喪', '失望', '擔心', '焦慮', '不滿', '困惑', '疲憊', '壓力', '煩躁'],
            '專注': ['專注', '認真', '投入', '集中', '嚴謹', '仔細', '謹慎'],
            '輕鬆': ['輕鬆', '放鬆', '隨意', '自在', '舒適'],
        }
        
        # 完成標記
        self.completed_markers = ['✅', '完成', '已做', 'done', 'finished', 'completed']
        self.pending_markers = ['⏳', '待完成', '待辦', 'pending', 'todo', '待處理']
    
    def extract_decisions(self, text: str) -> List[Decision]:
        """從文本中提取決策"""
        decisions = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 檢查決策模式
            for pattern in self.decision_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    decision_content = self._clean_decision_text(line)
                    if decision_content and len(decision_content) > 5:
                        decision = Decision(
                            content=decision_content,
                            reason=self._extract_reason(line, text),
                            timestamp=datetime.now().isoformat()
                        )
                        decisions.append(decision)
                        break
        
        # 去重
        seen = set()
        unique_decisions = []
        for d in decisions:
            if d.content not in seen:
                seen.add(d.content)
                unique_decisions.append(d)
        
        return unique_decisions
    
    def _clean_decision_text(self, text: str) -> str:
        """清理決策文本"""
        prefixes = ['決定', '確定', '選擇', '採用', '我們', '建議', '最終']
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        text = text.strip('：:，,。.')
        return text
    
    def _extract_reason(self, line: str, context: str) -> str:
        """提取決策原因"""
        reason_patterns = [
            r'(?:因為|由於|原因|考慮到|基於).{0,50}',
            r'(?:為了|以便|目的是).{0,30}',
        ]
        
        for pattern in reason_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0).strip()
        return ""
    
    def extract_action_items(self, text: str) -> List[ActionItem]:
        """從文本中提取行動項目"""
        action_items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            is_action = False
            status = "pending"
            priority = "medium"
            
            # 檢查完成標記
            for marker in self.completed_markers:
                if marker in line:
                    status = "completed"
                    is_action = True
                    break
            
            # 檢查待完成標記
            for marker in self.pending_markers:
                if marker in line:
                    status = "pending"
                    is_action = True
                    break
            
            # 檢查行動模式
            if not is_action:
                for pattern in self.action_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        is_action = True
                        break
            
            if is_action:
                content = self._clean_action_text(line)
                if content and len(content) > 3:
                    if any(kw in line for kw in ['緊急', '重要', '關鍵', '必須', 'urgent', 'critical']):
                        priority = "high"
                    elif any(kw in line for kw in ['低優先', '不急', '可以等', 'low']):
                        priority = "low"
                    
                    action = ActionItem(
                        content=content,
                        status=status,
                        priority=priority
                    )
                    action_items.append(action)
        
        return action_items
    
    def _clean_action_text(self, text: str) -> str:
        """清理行動項目文本"""
        for marker in self.completed_markers + self.pending_markers:
            text = text.replace(marker, '')
        prefixes = ['待完成', '待辦', 'TODO', '需要', '必須', '應該', '下一步']
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        return text.strip('：:，,。.')
    
    def extract_thinking_process(self, text: str) -> List[ThinkingProcess]:
        """提取思考過程"""
        thinking_processes = []
        thinking_patterns = [
            r'(?:考慮|思考|分析|評估).{0,10}[：:]([\s\S]{0,500}?)(?=\n\n|\Z)',
            r'(?:為什麼|為何|怎麼|如何).{0,30}[\?？]([\s\S]{0,300}?)(?=\n\n|\Z)',
            r'(?:比較|對比|權衡).{0,50}([\s\S]{0,400}?)(?=\n\n|\Z)',
        ]
        
        for pattern in thinking_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                content = match.group(0).strip()
                if len(content) > 20:
                    thinking = ThinkingProcess(
                        problem=self._extract_problem(content),
                        analysis=content[:300],
                        conclusion=self._extract_conclusion(content)
                    )
                    thinking_processes.append(thinking)
        
        return thinking_processes
    
    def _extract_problem(self, text: str) -> str:
        """提取問題"""
        lines = text.split('\n')
        for line in lines[:3]:
            if '?' in line or '？' in line or '問題' in line:
                return line.strip()
        return ""
    
    def _extract_conclusion(self, text: str) -> str:
        """提取結論"""
        conclusion_patterns = [
            r'(?:結論|總結|因此|所以|最終|決定).{0,100}',
            r'(?:建議|方案|選擇).{0,50}(?:是|為|：)',
        ]
        
        for pattern in conclusion_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).strip()
        return ""
    
    def extract_emotional_context(self, text: str) -> Optional[EmotionalContext]:
        """提取情感脈絡"""
        emotions_found = {}
        
        for emotion_type, keywords in self.emotion_keywords.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > 0:
                emotions_found[emotion_type] = count
        
        if not emotions_found:
            return None
        
        primary_emotion = max(emotions_found, key=emotions_found.get)
        intensity = min(emotions_found[primary_emotion] * 2, 10)
        
        return EmotionalContext(
            primary_emotion=primary_emotion,
            intensity=intensity,
            triggers=self._extract_emotion_triggers(text)
        )
    
    def _extract_emotion_triggers(self, text: str) -> List[str]:
        """提取情緒觸發因素"""
        triggers = []
        trigger_patterns = [
            r'(?:因為|由於).{0,30}(?:問題|錯誤|成功|完成|進展)',
            r'(?:看到|聽到|發現).{0,30}',
        ]
        
        for pattern in trigger_patterns:
            matches = re.findall(pattern, text)
            triggers.extend(matches)
        
        return triggers[:3]
    
    def extract_topics(self, text: str) -> List[str]:
        """提取主題標籤"""
        topics = set()
        topic_keywords = {
            '交易策略': ['策略', '交易', '買入', '賣出', '訂單', '持倉'],
            '系統開發': ['開發', '代碼', '程式', '系統', '功能', '模組'],
            '數據分析': ['數據', '分析', '統計', '報表', '指標'],
            '自動化': ['自動', '腳本', '排程', '定時', 'cron'],
            '財務規劃': ['財務', '預算', '投資', '資金', '收益'],
            '問題排查': ['問題', '錯誤', 'bug', '排查', '修復', 'debug'],
            '架構設計': ['架構', '設計', '結構', '模塊', '組件'],
            '性能優化': ['性能', '優化', '速度', '效率', '改進'],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text for kw in keywords):
                topics.add(topic)
        
        return list(topics)[:5]
    
    def extract_key_data(self, text: str) -> Dict[str, Any]:
        """提取關鍵數據"""
        key_data = {}
        number_patterns = [
            (r'(\d+)\s*個?策略', '策略數量'),
            (r'(\d+)\s*個?任務', '任務數量'),
            (r'(\d+)%', '百分比'),
            (r'(\d+)\s*小時', '時間'),
            (r'(\d+)\s*天', '天數'),
        ]
        
        for pattern, label in number_patterns:
            matches = re.findall(pattern, text)
            if matches:
                key_data[label] = matches
        
        config_patterns = [
            r'([\w_]+)\s*[=:：]\s*([\w\d\.]+)',
        ]
        
        for pattern in config_patterns:
            matches = re.findall(pattern, text)
            for key, value in matches:
                if key not in key_data:
                    key_data[key] = value
        
        return key_data


class Summarizer:
    """摘要生成器主類"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.analyzer = ContentAnalyzer()
        self.storage_path = storage_path or Path.home() / "openclaw_workspace" / "memory" / "summaries"
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def generate_summary(
        self,
        session_id: str,
        conversation_text: str,
        title: Optional[str] = None,
        summary_type: SummaryType = SummaryType.SESSION
    ) -> ConversationSummary:
        """生成對話摘要"""
        summary_id = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{session_id[:8]}"
        
        decisions = self.analyzer.extract_decisions(conversation_text)
        action_items = self.analyzer.extract_action_items(conversation_text)
        thinking_processes = self.analyzer.extract_thinking_process(conversation_text)
        emotional_context = self.analyzer.extract_emotional_context(conversation_text)
        topics = self.analyzer.extract_topics(conversation_text)
        key_data = self.analyzer.extract_key_data(conversation_text)
        
        overview = self._generate_overview(conversation_text, decisions, action_items, topics)
        
        if not title:
            title = self._generate_title(topics, decisions)
        
        next_continue = self._generate_next_continue(action_items, decisions)
        
        summary = ConversationSummary(
            id=summary_id,
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            summary_type=summary_type,
            title=title,
            overview=overview,
            topics=topics,
            decisions=decisions,
            action_items=action_items,
            thinking_processes=thinking_processes,
            emotional_context=emotional_context,
            key_data=key_data,
            next_continue=next_continue,
            metadata={
                "text_length": len(conversation_text),
                "decision_count": len(decisions),
                "action_count": len(action_items),
            }
        )
        
        return summary
    
    def _generate_overview(self, text: str, decisions: List[Decision], 
                          action_items: List[ActionItem], topics: List[str]) -> str:
        """生成概述"""
        parts = []
        
        if topics:
            parts.append(f"本次對話主要涉及：{', '.join(topics)}。")
        
        if decisions:
            parts.append(f"共做出 {len(decisions)} 項決策。")
        
        if action_items:
            pending = sum(1 for a in action_items if a.status == "pending")
            completed = sum(1 for a in action_items if a.status == "completed")
            parts.append(f"行動項目：{completed} 項已完成，{pending} 項待完成。")
        
        if not parts:
            overview = text[:200].replace('\n', ' ')
            if len(text) > 200:
                overview += "..."
            return overview
        
        return " ".join(parts)
    
    def _generate_title(self, topics: List[str], decisions: List[Decision]) -> str:
        """生成標題"""
        if topics:
            main_topic = topics[0]
            if decisions:
                return f"{main_topic}討論與決策"
            return f"{main_topic}討論"
        
        if decisions:
            return "策略決策會議"
        
        return "對話摘要"
    
    def _generate_next_continue(self, action_items: List[ActionItem], 
                                decisions: List[Decision]) -> str:
        """生成下次繼續建議"""
        suggestions = []
        
        pending_high = [a for a in action_items if a.status == "pending" and a.priority == "high"]
        if pending_high:
            suggestions.append(f"優先處理：{pending_high[0].content}")
        
        if decisions:
            suggestions.append(f"跟進決策：{decisions[-1].content[:50]}...")
        
        if not suggestions:
            return "可繼續深入討論相關主題。"
        
        return "；".join(suggestions)
    
    def format_summary_markdown(self, summary: ConversationSummary) -> str:
        """將摘要格式化為 Markdown"""
        lines = [
            f"## {summary.title}",
            "",
            f"**時間**: {summary.timestamp}",
            f"**Session**: {summary.session_id}",
            "",
            "### 概述",
            summary.overview,
            "",
        ]
        
        if summary.topics:
            lines.extend([
                "### 主題標籤",
                ", ".join([f"`{t}`" for t in summary.topics]),
                "",
            ])
        
        if summary.decisions:
            lines.extend(["### 關鍵決策", ""])
            for i, decision in enumerate(summary.decisions, 1):
                lines.append(f"{i}. **{decision.content}**")
                if decision.reason:
                    lines.append(f"   - 原因：{decision.reason}")
                lines.append("")
        
        if summary.action_items:
            lines.extend(["### 行動項目", ""])
            for item in summary.action_items:
                status_icon = "✅" if item.status == "completed" else "⏳"
                priority_icon = "🔴" if item.priority == "high" else "🟡" if item.priority == "medium" else "🟢"
                lines.append(f"{status_icon} {priority_icon} {item.content}")
            lines.append("")
        
        if summary.thinking_processes:
            lines.extend(["### 思考過程", ""])
            for thinking in summary.thinking_processes[:2]:
                if thinking.problem:
                    lines.append(f"**問題**: {thinking.problem}")
                lines.append(f"{thinking.analysis[:200]}...")
                if thinking.conclusion:
                    lines.append(f"**結論**: {thinking.conclusion}")
                lines.append("")
        
        if summary.emotional_context:
            lines.extend([
                "### 情感脈絡",
                "",
                f"主要情緒: {summary.emotional_context.primary_emotion} "
                f"(強度: {summary.emotional_context.intensity}/10)",
                "",
            ])
        
        if summary.key_data:
            lines.extend(["### 關鍵數據", ""])
            for key, value in list(summary.key_data.items())[:5]:
                lines.append(f"- **{key}**: {value}")
            lines.append("")
        
        lines.extend(["### 下次繼續", summary.next_continue, ""])
        
        return "\n".join(lines)
    
    def save_summary(self, summary: ConversationSummary) -> Path:
        """保存摘要到文件"""
        json_path = self.storage_path / f"{summary.id}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2)
        
        md_path = self.storage_path / f"{summary.id}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self.format_summary_markdown(summary))
        
        print(f"[Summarizer] 摘要已保存: {json_path}")
        return json_path
    
    def load_summary(self, summary_id: str) -> Optional[ConversationSummary]:
        """從文件加載摘要"""
        json_path = self.storage_path / f"{summary_id}.json"
        if not json_path.exists():
            return None
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ConversationSummary.from_dict(data)
        except Exception as e:
            print(f"[Summarizer] 加載摘要失敗: {e}")
            return None


# ==================== 便捷函數 ====================

def create_summarizer(storage_path: Optional[str] = None) -> Summarizer:
    """創建摘要生成器實例"""
    path = Path(storage_path) if storage_path else None
    return Summarizer(path)


def quick_summarize(conversation_text: str, session_id: str = "default",
                    title: Optional[str] = None) -> ConversationSummary:
    """快速生成摘要"""
    summarizer = create_summarizer()
    return summarizer.generate_summary(session_id, conversation_text, title)


def summarize_and_save(conversation_text: str, session_id: str,
                       title: Optional[str] = None) -> Tuple[ConversationSummary, Path]:
    """生成摘要並保存"""
    summarizer = create_summarizer()
    summary = summarizer.generate_summary(session_id, conversation_text, title)
    path = summarizer.save_summary(summary)
    return summary, path


# ==================== 測試代碼 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("摘要生成器測試")
    print("=" * 60)
    
    test_conversation = """
今天我們討論了交易策略優化的問題。

首先分析了當前的5個策略，發現其中2個表現不佳。
經過仔細考慮，我們決定保留3個核心策略，清理掉2個表現不佳的策略。
原因是這3個策略在回測中表現穩定，夏普比率都大於2.0。

決定採用新的MTF整合方案，將多時間框架分析整合到現有系統中。
這個決定是基於提高信號準確性的考慮。

待完成項目：
⏳ 等待實盤部署
⏳ 完成策略參數調整面板
✅ 已經完成策略回測

下一步需要完成系統整合測試，確保所有模組正常工作。

情感上感覺很積極，對這個方向充滿信心。

關鍵數據：
- 策略數量: 3個保留
- 清理數量: 2個
- 夏普比率: >2.0
- 預計完成時間: 2天
    """
    
    summarizer = create_summarizer()
    
    print("\n[測試] 生成摘要...")
    summary = summarizer.generate_summary(
        session_id="test_session_001",
        conversation_text=test_conversation,
        title="交易策略優化討論"
    )
    
    print(f"\n標題: {summary.title}")
    print(f"主題: {', '.join(summary.topics)}")
    print(f"決策數量: {len(summary.decisions)}")
    print(f"行動項目: {len(summary.action_items)}")
    
    print("\n[測試] 保存摘要...")
    path = summarizer.save_summary(summary)
    print(f"保存路徑: {path}")
    
    print("\n[測試] Markdown 格式預覽:")
    print(summarizer.format_summary_markdown(summary)[:500] + "...")
    
    print("\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
