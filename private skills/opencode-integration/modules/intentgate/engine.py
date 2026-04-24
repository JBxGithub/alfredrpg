"""
IntentGate - 意圖分類引擎
Semantic routing system for OpenClaw + ClawTeam
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import hashlib


class IntentCategory(Enum):
    """意圖分類領域"""
    CRITICAL = "critical"           # 緊急處理
    FINANCE = "finance"             # 財務相關
    TECHNOLOGY = "technology"       # 技術相關
    LIFESTYLE = "lifestyle"         # 生活相關
    MONITORING = "monitoring"       # 監控相關
    RESEARCH = "research"           # 研究相關
    META = "meta"                   # 系統相關


class IntentType(Enum):
    """具體意圖類型"""
    # CRITICAL
    SECURITY_ALERT = "security_alert"
    SYSTEM_FAILURE = "system_failure"
    EMERGENCY_REQUEST = "emergency_request"
    
    # FINANCE
    EXPENSE_TRACKING = "expense_tracking"
    BUDGET_ANALYSIS = "budget_analysis"
    INVESTMENT_RESEARCH = "investment_research"
    ACCOUNTING_QUERY = "accounting_query"
    FINANCIAL_REPORT = "financial_report"
    
    # TECHNOLOGY
    CODE_DEVELOPMENT = "code_development"
    CODE_REVIEW = "code_review"
    DEBUGGING = "debugging"
    SYSTEM_ARCHITECTURE = "system_architecture"
    DEVOPS = "devops"
    TECHNICAL_RESEARCH = "technical_research"
    
    # LIFESTYLE
    SCHEDULING = "scheduling"
    TRAVEL_PLANNING = "travel_planning"
    SHOPPING = "shopping"
    HEALTH_WELLNESS = "health_wellness"
    ENTERTAINMENT = "entertainment"
    PERSONAL_TASK = "personal_task"
    
    # MONITORING
    STOCK_MONITOR = "stock_monitor"
    PRICE_ALERT = "price_alert"
    NEWS_TRACKING = "news_tracking"
    SYSTEM_MONITOR = "system_monitor"
    DATA_SYNC = "data_sync"
    
    # RESEARCH
    WEB_SEARCH = "web_search"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    TREND_ANALYSIS = "trend_analysis"
    COMPETITIVE_INTEL = "competitive_intel"
    
    # META
    SKILL_MANAGEMENT = "skill_management"
    CONFIGURATION = "configuration"
    HELP_REQUEST = "help_request"
    STATUS_QUERY = "status_query"
    CONVERSATION = "conversation"


@dataclass
class IntentClassification:
    """意圖分類結果"""
    intent: IntentType
    category: IntentCategory
    confidence: float
    sub_intents: List[IntentType]
    entities: List[Dict[str, Any]]
    urgency: str  # 'low' | 'medium' | 'high' | 'critical'
    complexity: str  # 'simple' | 'moderate' | 'complex'
    metadata: Dict[str, Any]


@dataclass
class RoutingDecision:
    """路由決策結果"""
    target_agent: str
    fallback_agents: List[str]
    routing_type: str  # 'direct' | 'hybrid' | 'fallback'
    confidence: float
    context: Dict[str, Any]


class IntentGate:
    """
    IntentGate 核心引擎
    
    負責解析用戶真實意圖，而非僅僅字面意思
    """
    
    # 置信度閾值
    HIGH_CONFIDENCE = 0.85
    MEDIUM_CONFIDENCE = 0.70
    
    # 關鍵詞映射（簡化版，實際應使用向量嵌入）
    INTENT_KEYWORDS = {
        # CRITICAL
        IntentType.SECURITY_ALERT: ['安全', '警報', '入侵', '攻擊', '漏洞'],
        IntentType.SYSTEM_FAILURE: ['故障', '崩潰', '錯誤', '失敗', 'down'],
        IntentType.EMERGENCY_REQUEST: ['緊急', '立刻', '馬上', '現在就要'],
        
        # FINANCE
        IntentType.EXPENSE_TRACKING: ['支出', '花費', '消費', '記帳'],
        IntentType.BUDGET_ANALYSIS: ['預算', '開支', '財務規劃'],
        IntentType.INVESTMENT_RESEARCH: ['投資', '股票', '基金', '理財'],
        IntentType.ACCOUNTING_QUERY: ['會計', '報稅', '發票', '賬目'],
        IntentType.FINANCIAL_REPORT: ['財報', '報表', '分析'],
        
        # TECHNOLOGY
        IntentType.CODE_DEVELOPMENT: ['編程', '寫代碼', '開發', '實現'],
        IntentType.CODE_REVIEW: ['審查', 'review', '檢查代碼'],
        IntentType.DEBUGGING: ['調試', 'bug', '錯誤', '修復'],
        IntentType.SYSTEM_ARCHITECTURE: ['架構', '設計', '系統'],
        IntentType.DEVOPS: ['部署', '運維', 'CI/CD', 'docker'],
        IntentType.TECHNICAL_RESEARCH: ['技術研究', '調研', '評估'],
        
        # LIFESTYLE
        IntentType.SCHEDULING: ['日程', '安排', '時間', '計劃'],
        IntentType.TRAVEL_PLANNING: ['旅行', '機票', '酒店', '行程'],
        IntentType.SHOPPING: ['購物', '買', '訂購', '推薦'],
        IntentType.HEALTH_WELLNESS: ['健康', '運動', '飲食', '醫療'],
        IntentType.ENTERTAINMENT: ['娛樂', '電影', '遊戲', '音樂'],
        IntentType.PERSONAL_TASK: ['個人', '私事', '待辦'],
        
        # MONITORING
        IntentType.STOCK_MONITOR: ['股票監控', '股價', '行情'],
        IntentType.PRICE_ALERT: ['價格提醒', '到價', '通知'],
        IntentType.NEWS_TRACKING: ['新聞', '資訊', '追蹤'],
        IntentType.SYSTEM_MONITOR: ['系統監控', '性能', '狀態'],
        IntentType.DATA_SYNC: ['同步', '備份', '更新'],
        
        # RESEARCH
        IntentType.WEB_SEARCH: ['搜索', '查找', '查詢', '資料'],
        IntentType.DATA_ANALYSIS: ['分析', '數據', '統計', '圖表'],
        IntentType.DOCUMENT_PROCESSING: ['文檔', 'PDF', '處理', '轉換'],
        IntentType.TREND_ANALYSIS: ['趨勢', '預測', '走向'],
        IntentType.COMPETITIVE_INTEL: ['競爭', '對手', '市場'],
        
        # META
        IntentType.SKILL_MANAGEMENT: ['技能', '安裝', '更新', '插件'],
        IntentType.CONFIGURATION: ['配置', '設置', '設定'],
        IntentType.HELP_REQUEST: ['幫助', '說明', '怎麼', '如何'],
        IntentType.STATUS_QUERY: ['狀態', '進度', '情況'],
        IntentType.CONVERSATION: ['聊天', '對話', '閒聊'],
    }
    
    # ClawTeam 角色映射
    AGENT_MAPPING = {
        IntentCategory.CRITICAL: ['隊長', '監控員'],
        IntentCategory.FINANCE: ['財務官', '分析師'],
        IntentCategory.TECHNOLOGY: ['技術官', '執行員'],
        IntentCategory.LIFESTYLE: ['執行員', '研究員'],
        IntentCategory.MONITORING: ['監控員', '分析師'],
        IntentCategory.RESEARCH: ['研究員', '分析師'],
        IntentCategory.META: ['隊長', '技術官'],
    }
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 IntentGate
        
        Args:
            config: 配置字典，可包含自定義閾值等
        """
        self.config = config or {}
        self.high_threshold = self.config.get('high_confidence', self.HIGH_CONFIDENCE)
        self.medium_threshold = self.config.get('medium_confidence', self.MEDIUM_CONFIDENCE)
    
    def classify(self, query: str, context: Optional[Dict] = None) -> IntentClassification:
        """
        分類用戶意圖
        
        Args:
            query: 用戶輸入
            context: 上下文信息
            
        Returns:
            IntentClassification: 分類結果
        """
        # 簡化版：基於關鍵詞匹配
        # 實際應使用向量嵌入模型
        scores = self._calculate_scores(query)
        
        # 選擇最高分的意圖
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        
        # 確定分類
        category = self._get_category(best_intent)
        
        # 檢測子意圖
        sub_intents = self._detect_sub_intents(query, scores)
        
        # 提取實體
        entities = self._extract_entities(query)
        
        # 評估緊急度和複雜度
        urgency = self._assess_urgency(query, context)
        complexity = self._assess_complexity(query, scores)
        
        return IntentClassification(
            intent=best_intent,
            category=category,
            confidence=best_score,
            sub_intents=sub_intents,
            entities=entities,
            urgency=urgency,
            complexity=complexity,
            metadata={'raw_scores': scores, 'context': context}
        )
    
    def route(self, classification: IntentClassification) -> RoutingDecision:
        """
        根據分類結果決定路由
        
        Args:
            classification: 意圖分類結果
            
        Returns:
            RoutingDecision: 路由決策
        """
        confidence = classification.confidence
        category = classification.category
        
        # 確定路由類型
        if confidence >= self.high_threshold:
            routing_type = 'direct'
        elif confidence >= self.medium_threshold:
            routing_type = 'hybrid'
        else:
            routing_type = 'fallback'
        
        # 選擇目標代理
        primary_agents = self.AGENT_MAPPING.get(category, ['隊長'])
        target_agent = primary_agents[0]
        fallback_agents = primary_agents[1:] if len(primary_agents) > 1 else ['隊長']
        
        return RoutingDecision(
            target_agent=target_agent,
            fallback_agents=fallback_agents,
            routing_type=routing_type,
            confidence=confidence,
            context={
                'category': category.value,
                'intent': classification.intent.value,
                'urgency': classification.urgency,
                'complexity': classification.complexity
            }
        )
    
    def process(self, query: str, context: Optional[Dict] = None) -> Tuple[IntentClassification, RoutingDecision]:
        """
        完整處理流程：分類 + 路由
        
        Args:
            query: 用戶輸入
            context: 上下文信息
            
        Returns:
            (IntentClassification, RoutingDecision): 分類和路由結果
        """
        classification = self.classify(query, context)
        routing = self.route(classification)
        return classification, routing
    
    def _calculate_scores(self, query: str) -> Dict[IntentType, float]:
        """計算各意圖的匹配分數"""
        scores = {}
        query_lower = query.lower()
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = 0.0
            for keyword in keywords:
                if keyword in query_lower:
                    score += 0.2  # 每個匹配關鍵詞加 0.2
            scores[intent] = min(score, 1.0)  # 最高分 1.0
        
        # 確保至少有個默認分數
        if not scores or max(scores.values()) == 0:
            scores[IntentType.CONVERSATION] = 0.5
        
        return scores
    
    def _get_category(self, intent: IntentType) -> IntentCategory:
        """根據意圖獲取分類"""
        category_map = {
            # CRITICAL
            IntentType.SECURITY_ALERT: IntentCategory.CRITICAL,
            IntentType.SYSTEM_FAILURE: IntentCategory.CRITICAL,
            IntentType.EMERGENCY_REQUEST: IntentCategory.CRITICAL,
            
            # FINANCE
            IntentType.EXPENSE_TRACKING: IntentCategory.FINANCE,
            IntentType.BUDGET_ANALYSIS: IntentCategory.FINANCE,
            IntentType.INVESTMENT_RESEARCH: IntentCategory.FINANCE,
            IntentType.ACCOUNTING_QUERY: IntentCategory.FINANCE,
            IntentType.FINANCIAL_REPORT: IntentCategory.FINANCE,
            
            # TECHNOLOGY
            IntentType.CODE_DEVELOPMENT: IntentCategory.TECHNOLOGY,
            IntentType.CODE_REVIEW: IntentCategory.TECHNOLOGY,
            IntentType.DEBUGGING: IntentCategory.TECHNOLOGY,
            IntentType.SYSTEM_ARCHITECTURE: IntentCategory.TECHNOLOGY,
            IntentType.DEVOPS: IntentCategory.TECHNOLOGY,
            IntentType.TECHNICAL_RESEARCH: IntentCategory.TECHNOLOGY,
            
            # LIFESTYLE
            IntentType.SCHEDULING: IntentCategory.LIFESTYLE,
            IntentType.TRAVEL_PLANNING: IntentCategory.LIFESTYLE,
            IntentType.SHOPPING: IntentCategory.LIFESTYLE,
            IntentType.HEALTH_WELLNESS: IntentCategory.LIFESTYLE,
            IntentType.ENTERTAINMENT: IntentCategory.LIFESTYLE,
            IntentType.PERSONAL_TASK: IntentCategory.LIFESTYLE,
            
            # MONITORING
            IntentType.STOCK_MONITOR: IntentCategory.MONITORING,
            IntentType.PRICE_ALERT: IntentCategory.MONITORING,
            IntentType.NEWS_TRACKING: IntentCategory.MONITORING,
            IntentType.SYSTEM_MONITOR: IntentCategory.MONITORING,
            IntentType.DATA_SYNC: IntentCategory.MONITORING,
            
            # RESEARCH
            IntentType.WEB_SEARCH: IntentCategory.RESEARCH,
            IntentType.DATA_ANALYSIS: IntentCategory.RESEARCH,
            IntentType.DOCUMENT_PROCESSING: IntentCategory.RESEARCH,
            IntentType.TREND_ANALYSIS: IntentCategory.RESEARCH,
            IntentType.COMPETITIVE_INTEL: IntentCategory.RESEARCH,
            
            # META
            IntentType.SKILL_MANAGEMENT: IntentCategory.META,
            IntentType.CONFIGURATION: IntentCategory.META,
            IntentType.HELP_REQUEST: IntentCategory.META,
            IntentType.STATUS_QUERY: IntentCategory.META,
            IntentType.CONVERSATION: IntentCategory.META,
        }
        return category_map.get(intent, IntentCategory.META)
    
    def _detect_sub_intents(self, query: str, scores: Dict[IntentType, float]) -> List[IntentType]:
        """檢測子意圖"""
        # 選擇分數較高的其他意圖作為子意圖
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        sub_intents = [intent for intent, score in sorted_intents[1:3] if score > 0.3]
        return sub_intents
    
    def _extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """提取實體（簡化版）"""
        entities = []
        # 這裡應使用 NER 模型
        # 簡化處理：提取引號內的內容
        import re
        quoted = re.findall(r'["""]([^"""]+)["""]', query)
        for q in quoted:
            entities.append({'type': 'quoted_text', 'value': q})
        return entities
    
    def _assess_urgency(self, query: str, context: Optional[Dict]) -> str:
        """評估緊急度"""
        urgent_keywords = ['緊急', '立刻', '馬上', '現在', 'asap', 'urgent']
        if any(kw in query.lower() for kw in urgent_keywords):
            return 'critical' if '緊急' in query else 'high'
        return 'medium'
    
    def _assess_complexity(self, query: str, scores: Dict[IntentType, float]) -> str:
        """評估複雜度"""
        # 基於查詢長度和意圖數量評估
        if len(query) > 100 or len([s for s in scores.values() if s > 0.3]) > 2:
            return 'complex'
        elif len(query) > 50:
            return 'moderate'
        return 'simple'


# 便捷函數
def classify_intent(query: str, context: Optional[Dict] = None) -> IntentClassification:
    """便捷函數：分類意圖"""
    gate = IntentGate()
    return gate.classify(query, context)


def route_intent(classification: IntentClassification) -> RoutingDecision:
    """便捷函數：路由意圖"""
    gate = IntentGate()
    return gate.route(classification)


def process_query(query: str, context: Optional[Dict] = None) -> Tuple[IntentClassification, RoutingDecision]:
    """便捷函數：完整處理"""
    gate = IntentGate()
    return gate.process(query, context)
