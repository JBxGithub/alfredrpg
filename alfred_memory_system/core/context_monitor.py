"""
Alfred Memory System (AMS) - Context Monitor

實時監控對話 Context 使用情況，在達到閾值時發出警告或自動觸發壓縮。
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from typing import List, Dict, Optional

from ..config import ContextMonitorConfig
from ..storage import DatabaseManager


@dataclass
class ContextStatus:
    """Context 狀態數據類"""
    tokens: int
    limit: int
    usage_percent: float
    status: str  # 'normal', 'warning', 'compress', 'critical'
    action_required: Optional[str]
    message_count: int
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'tokens': self.tokens,
            'limit': self.limit,
            'usage_percent': round(self.usage_percent, 1),
            'status': self.status,
            'action_required': self.action_required,
            'message_count': self.message_count,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __str__(self) -> str:
        bar_length = 40
        filled = int(bar_length * self.usage_percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        status_emoji = {
            'normal': '✅',
            'warning': '⚠️',
            'compress': '📦',
            'critical': '🚨'
        }.get(self.status, '❓')
        
        lines = [
            "═══════════════════════════════════════════════════════════",
            f"📊 Context Usage: {self.usage_percent:.1f}% ({self.tokens:,} / {self.limit:,} tokens)",
            f"{bar}",
            f"{status_emoji} Status: {self.status.upper()}",
        ]
        
        if self.action_required:
            action_desc = {
                'notify_user': '建議開始新對話或壓縮上下文',
                'compress_context': '自動壓縮已觸發',
                'emergency_compress': '緊急壓縮已觸發'
            }.get(self.action_required, self.action_required)
            lines.append(f"⚡ Action: {action_desc}")
        
        lines.append("═══════════════════════════════════════════════════════════")
        
        return '\n'.join(lines)


class ContextMonitor:
    """
    Context 監控器 - 實時監控對話長度
    
    使用方式:
        monitor = ContextMonitor(config)
        status = monitor.check_context(messages)
        print(status)
        
        if status.action_required:
            monitor.log_usage(session_id, status)
    """
    
    # 模型 Context 長度映射
    MODEL_CONTEXT_LENGTHS = {
        # OpenAI
        'gpt-4': 8192,
        'gpt-4-turbo': 128000,
        'gpt-4o': 128000,
        'gpt-3.5-turbo': 16385,
        
        # Anthropic
        'claude-3-opus': 200000,
        'claude-3-sonnet': 200000,
        'claude-3-haiku': 200000,
        
        # Moonshot (Kimi)
        'moonshot/kimi-k2.5': 128000,
        'moonshot/kimi-k1.5': 128000,
        
        # Google
        'gemini-pro': 128000,
        'gemini-ultra': 128000,
        
        # Default
        'default': 128000
    }
    
    def __init__(self, config: Optional[ContextMonitorConfig] = None, 
                 db: Optional[DatabaseManager] = None):
        self.config = config or ContextMonitorConfig()
        self.db = db
        self._message_counter = 0
    
    def set_model(self, model_name: str):
        """設置當前使用的模型，自動調整 Context 長度"""
        # 嘗試匹配模型名稱
        for key, length in self.MODEL_CONTEXT_LENGTHS.items():
            if key in model_name.lower():
                self.config.model_context_length = length
                return
        
        # 使用默認值
        self.config.model_context_length = self.MODEL_CONTEXT_LENGTHS['default']
    
    def estimate_tokens(self, messages: List[Dict]) -> int:
        """
        估算消息的 token 數量
        
        使用簡化的估算方法：
        - 中文字符：約 1.5 tokens
        - 英文/數字符：約 0.25 tokens
        - 消息結構開銷：每條消息 4 tokens
        """
        total_tokens = 0
        
        for msg in messages:
            content = msg.get('content', '') or ''
            
            # 計算字符數
            chinese_chars = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
            other_chars = len(content) - chinese_chars
            
            # 估算 tokens
            content_tokens = int(chinese_chars * 1.5 + other_chars * 0.25)
            
            # 消息結構開銷 (role, metadata 等)
            overhead = 4
            
            # Tool calls 和 results 的估算
            tool_calls = msg.get('tool_calls', [])
            tool_results = msg.get('tool_results', [])
            
            if tool_calls:
                tool_content = str(tool_calls)
                tool_tokens = int(len(tool_content) * 0.3)  # JSON 結構開銷較大
                content_tokens += tool_tokens
            
            if tool_results:
                result_content = str(tool_results)
                result_tokens = int(len(result_content) * 0.3)
                content_tokens += result_tokens
            
            total_tokens += content_tokens + overhead
        
        return total_tokens
    
    def check_context(self, messages: List[Dict]) -> ContextStatus:
        """
        檢查當前 Context 使用情況
        
        Args:
            messages: 當前對話消息列表
            
        Returns:
            ContextStatus 對象，包含使用情況和建議操作
        """
        tokens = self.estimate_tokens(messages)
        limit = self.config.model_context_length
        usage_percent = (tokens / limit) * 100
        
        # 確定狀態和行動
        status = 'normal'
        action = None
        
        if usage_percent >= self.config.critical_threshold * 100:
            status = 'critical'
            action = 'emergency_compress'
        elif usage_percent >= self.config.compress_threshold * 100:
            status = 'compress'
            action = 'compress_context'
        elif usage_percent >= self.config.warning_threshold * 100:
            status = 'warning'
            action = 'notify_user'
        
        self._message_counter = len(messages)
        
        return ContextStatus(
            tokens=tokens,
            limit=limit,
            usage_percent=usage_percent,
            status=status,
            action_required=action,
            message_count=len(messages),
            timestamp=datetime.now()
        )
    
    def should_check(self, message_count: int) -> bool:
        """
        判斷是否應該進行 Context 檢查
        
        基於消息數量間隔，避免頻繁檢查
        """
        return message_count % self.config.check_interval == 0
    
    def log_usage(self, session_id: str, status: ContextStatus):
        """記錄 Context 使用情況到數據庫"""
        if self.db:
            self.db.log_context_usage(
                session_id=session_id,
                tokens_used=status.tokens,
                tokens_limit=status.limit,
                usage_percent=status.usage_percent,
                action_taken=status.action_required
            )
    
    def get_usage_trend(self, session_id: str, 
                        samples: int = 10) -> List[Dict]:
        """
        獲取 Context 使用趨勢
        
        返回最近 N 條記錄，用於分析增長趨勢
        """
        if not self.db:
            return []
        
        history = self.db.get_context_usage_history(session_id, limit=samples)
        return [
            {
                'timestamp': h['timestamp'],
                'usage_percent': h['usage_percent'],
                'tokens_used': h['tokens_used'],
                'action_taken': h['action_taken']
            }
            for h in reversed(history)  # 按時間順序
        ]
    
    def predict_full_time(self, trend: List[Dict]) -> Optional[str]:
        """
        預測 Context 何時會達到 100%
        
        基於最近的使用趨勢進行線性預測
        """
        if len(trend) < 3:
            return None
        
        # 計算平均增長速度
        growth_rates = []
        for i in range(1, len(trend)):
            prev = trend[i-1]
            curr = trend[i]
            
            # 解析時間
            try:
                prev_time = datetime.fromisoformat(prev['timestamp'].replace('Z', '+00:00'))
                curr_time = datetime.fromisoformat(curr['timestamp'].replace('Z', '+00:00'))
                time_diff = (curr_time - prev_time).total_seconds() / 60  # 分鐘
                
                if time_diff > 0:
                    usage_diff = curr['usage_percent'] - prev['usage_percent']
                    growth_rate = usage_diff / time_diff  # % per minute
                    growth_rates.append(growth_rate)
            except:
                continue
        
        if not growth_rates:
            return None
        
        avg_growth_rate = sum(growth_rates) / len(growth_rates)
        
        if avg_growth_rate <= 0:
            return "Context 使用穩定或下降"
        
        current_usage = trend[-1]['usage_percent']
        remaining = 100 - current_usage
        minutes_to_full = remaining / avg_growth_rate
        
        if minutes_to_full < 60:
            return f"預計 {int(minutes_to_full)} 分鐘後達到 100%"
        elif minutes_to_full < 1440:
            return f"預計 {int(minutes_to_full / 60)} 小時後達到 100%"
        else:
            return f"預計 {int(minutes_to_full / 1440)} 天後達到 100%"
    
    def generate_report(self, session_id: Optional[str] = None) -> str:
        """生成 Context 使用報告"""
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║           Alfred Memory System - Context Report              ║",
            "╚══════════════════════════════════════════════════════════════╝",
            "",
            f"📊 Configuration:",
            f"   Model Context Length: {self.config.model_context_length:,} tokens",
            f"   Warning Threshold: {self.config.warning_threshold * 100:.0f}%",
            f"   Compress Threshold: {self.config.compress_threshold * 100:.0f}%",
            f"   Critical Threshold: {self.config.critical_threshold * 100:.0f}%",
            "",
        ]
        
        if session_id and self.db:
            trend = self.get_usage_trend(session_id)
            if trend:
                lines.extend([
                    f"📈 Session {session_id[-8:]} Trend:",
                    f"   Current Usage: {trend[-1]['usage_percent']:.1f}%",
                    f"   Messages: {len(trend) * self.config.check_interval}",
                ])
                
                prediction = self.predict_full_time(trend)
                if prediction:
                    lines.append(f"   Prediction: {prediction}")
                
                lines.append("")
        
        lines.append("═══════════════════════════════════════════════════════════════")
        
        return '\n'.join(lines)


# 便捷函數
def check_context_simple(messages: List[Dict], 
                         model: str = 'default') -> ContextStatus:
    """
    簡易 Context 檢查函數
    
    使用方式:
        status = check_context_simple(messages, model='moonshot/kimi-k2.5')
        if status.usage_percent > 70:
            print("Context 即將用盡，建議開始新對話")
    """
    monitor = ContextMonitor()
    monitor.set_model(model)
    return monitor.check_context(messages)
