# IntentGate 機制設計研究報告

## OpenClaw + ClawTeam 意圖分類系統設計

**研究日期**: 2026-04-13  
**版本**: v1.0  
**作者**: AI Research Agent

---

## 目錄

1. [執行摘要](#1-執行摘要)
2. [IntentGate 核心機制分析](#2-intentgate-核心機制分析)
3. [建議的意圖分類標籤系統](#3-建議的意圖分類標籤系統)
4. [與 ClawTeam 7人角色的映射關係](#4-與-clawteam-7人角色的映射關係)
5. [代碼框架與實現方案](#5-代碼框架與實現方案)
6. [整合入現有系統的步驟](#6-整合入現有系統的步驟)
7. [附錄：參考資料](#7-附錄參考資料)

---

## 1. 執行摘要

本研究深入分析了 Oh-My-OpenAgent 的 IntentGate 設計原理，並為 OpenClaw + ClawTeam 設計了一套完整的意圖分類系統。該系統採用**語義路由（Semantic Routing）**作為核心機制，結合多層次分類標籤和智能代理映射，實現高效、準確的任務分發。

### 核心發現

- **IntentGate 本質**: 一個前置的意圖分類閘道，負責解析用戶真實意圖而非字面意思
- **技術基礎**: 基於向量嵌入（Vector Embedding）的語義相似度匹配
- **架構優勢**: 支持多代理並行、動態路由、置信度評估和優雅降級

---

## 2. IntentGate 核心機制分析

### 2.1 設計哲學

IntentGate 的設計理念源自 Oh-My-OpenAgent 的核心原則：

> **"Parses what you meant, not just what you typed"**
> （解析你的真實意圖，而不僅僅是你輸入的文字）

這與傳統的關鍵詞匹配有本質區別：

| 特性 | 傳統關鍵詞匹配 | IntentGate 語義路由 |
|------|---------------|-------------------|
| 匹配方式 | 正則表達式、關鍵詞列表 | 向量嵌入相似度 |
| 容錯性 | 低，必須精確匹配 | 高，理解同義表達 |
| 擴展性 | 需手動添加規則 | 自動泛化到新表達 |
| 多語言 | 需單獨處理 | 嵌入模型天然支持 |
| 語義理解 | 無 | 深度語義理解 |

### 2.2 核心組件

```
┌─────────────────────────────────────────────────────────────┐
│                    IntentGate Architecture                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ User Query   │───▶│  Embedding   │───▶│  Similarity  │  │
│  │   (Text)     │    │    Model     │    │   Matching   │  │
│  └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                  │          │
│                              ┌───────────────────┘          │
│                              ▼                              │
│                    ┌──────────────────┐                     │
│                    │  Route Selection │                     │
│                    │  (Threshold >=)  │                     │
│                    └────────┬─────────┘                     │
│                             │                               │
│              ┌──────────────┼──────────────┐                │
│              ▼              ▼              ▼                │
│        ┌─────────┐   ┌──────────┐   ┌──────────┐           │
│        │ Route A │   │ Route B  │   │ Fallback │           │
│        │ Agent   │   │  Agent   │   │  Handler │           │
│        └─────────┘   └──────────┘   └──────────┘           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 工作流程

#### Phase 1: Intent Classification（意圖分類）

```
輸入: 用戶查詢 Q
輸出: 意圖類別 C，置信度 S

步驟:
1. E_Q = Embedding(Q)  // 將查詢轉換為向量
2. FOR each route R in Routes:
     S_R = Cosine_Similarity(E_Q, E_R)
3. C = argmax(S_R)
4. S = max(S_R)
5. IF S >= Threshold:
     RETURN C
   ELSE:
     RETURN "uncertain"
```

#### Phase 2: Route Selection（路由選擇）

基於分類結果，選擇最適合的處理路徑：

- **直接路由**: 高置信度（>0.85）→ 直接分配給專業代理
- **混合路由**: 中等置信度（0.70-0.85）→ LLM 輔助確認
- **默認路由**: 低置信度（<0.70）→ 通用代理或人工介入

#### Phase 3: Context Passing（上下文傳遞）

```typescript
interface IntentContext {
  intent: string;           // 主要意圖
  subIntents: string[];     // 子意圖列表
  confidence: number;       // 置信度分數
  entities: Entity[];       // 提取的實體
  urgency: 'low' | 'medium' | 'high' | 'critical';
  complexity: 'simple' | 'moderate' | 'complex';
  domain: string;           // 領域分類
  metadata: Record<string, any>;
}
```

### 2.4 數學基礎

#### 餘弦相似度計算

```
cosine_sim(A, B) = (A · B) / (||A|| × ||B||)
                = Σ(Aᵢ × Bᵢ) / (√Σ(Aᵢ²) × √Σ(Bᵢ²))
```

#### 閾值設定建議

| 應用場景 | 建議閾值 | 說明 |
|---------|---------|------|
| 高準確率要求 | 0.85-0.90 | 寧願誤判也不願錯分 |
| 平衡模式 | 0.75-0.80 | 預設推薦值 |
| 高覆蓋率要求 | 0.65-0.70 | 盡量減少未分類 |

---

## 3. 建議的意圖分類標籤系統

### 3.1 分類體系架構

```
Intent Classification Hierarchy
│
├── 🔴 CRITICAL（緊急處理）
│   ├── security_alert      # 安全警報
│   ├── system_failure      # 系統故障
│   └── emergency_request   # 緊急請求
│
├── 💰 FINANCE（財務相關）
│   ├── expense_tracking    # 支出追蹤
│   ├── budget_analysis     # 預算分析
│   ├── investment_research # 投資研究
│   ├── accounting_query    # 會計查詢
│   └── financial_report    # 財務報告
│
├── 💻 TECHNOLOGY（技術相關）
│   ├── code_development    # 代碼開發
│   ├── code_review         # 代碼審查
│   ├── debugging           # 除錯
│   ├── system_architecture # 系統架構
│   ├── devops              # 運維部署
│   └── technical_research  # 技術研究
│
├── 🏠 LIFESTYLE（生活相關）
│   ├── scheduling          # 日程安排
│   ├── travel_planning     # 旅行規劃
│   ├── shopping            # 購物建議
│   ├── health_wellness     # 健康養生
│   ├── entertainment       # 娛樂推薦
│   └── personal_task       # 個人事務
│
├── 📊 MONITORING（監控相關）
│   ├── stock_monitor       # 股票監控
│   ├── price_alert         # 價格提醒
│   ├── news_tracking       # 新聞追蹤
│   ├── system_monitor      # 系統監控
│   └── data_sync           # 數據同步
│
├── 🔬 RESEARCH（研究相關）
│   ├── web_search          # 網頁搜索
│   ├── data_analysis       # 數據分析
│   ├── document_processing # 文檔處理
│   ├── trend_analysis      # 趨勢分析
│   └── competitive_intel   # 競爭情報
│
├── 🤖 META（系統相關）
│   ├── skill_management    # 技能管理
│   ├── configuration       # 配置設定
│   ├── help_request        # 幫助請求
│   ├── status_query        # 狀態查詢
│   └── conversation        # 一般對話
│
└── 🔄 COMPOSITE（複合意圖）
    ├── multi_domain        # 多領域組合
    └── sequential_tasks    # 順序任務
```

### 3.2 詳細標籤定義

#### 3.2.1 FINANCE（財務）領域

```typescript
const FinanceIntents = {
  EXPENSE_TRACKING: {
    code: 'finance.expense_tracking',
    description: '追蹤和記錄個人或企業支出',
    examples: [
      '記錄今天午餐花了 50 元',
      '查看本月支出總額',
      '分類上週的所有消費',
      '設定每月餐飲預算 3000 元'
    ],
    keywords: ['支出', '花費', '記帳', '預算', '消費'],
    required_entities: ['amount', 'category', 'date'],
    complexity: 'simple'
  },
  
  BUDGET_ANALYSIS: {
    code: 'finance.budget_analysis',
    description: '分析預算執行情況和偏差',
    examples: [
      '分析本月預算執行狀況',
      '為什麼餐飲支出超標了？',
      '預測下個月的現金流',
      '生成預算執行報告'
    ],
    keywords: ['預算分析', '超支', '偏差', '預測'],
    required_entities: ['time_period', 'budget_category'],
    complexity: 'moderate'
  },
  
  INVESTMENT_RESEARCH: {
    code: 'finance.investment_research',
    description: '投資標的研究和分析',
    examples: [
      '研究蘋果公司的財報',
      '分析特斯拉股票的技術指標',
      '比較兩檔 ETF 的表現',
      '評估這個投資組合的風險'
    ],
    keywords: ['股票', '投資', '財報', '分析', 'ETF', '風險'],
    required_entities: ['symbol', 'metric_type'],
    complexity: 'complex'
  },
  
  ACCOUNTING_QUERY: {
    code: 'finance.accounting_query',
    description: '會計相關查詢和計算',
    examples: [
      '計算折舊費用',
      '這筆交易應該記在哪個科目？',
      '生成試算表',
      '核對銀行對帳單'
    ],
    keywords: ['會計', '科目', '折舊', '試算表', '對帳'],
    required_entities: ['transaction_type'],
    complexity: 'moderate'
  }
};
```

#### 3.2.2 TECHNOLOGY（技術）領域

```typescript
const TechnologyIntents = {
  CODE_DEVELOPMENT: {
    code: 'tech.code_development',
    description: '編寫新代碼或實現功能',
    examples: [
      '寫一個 Python 函數來計算斐波那契數列',
      '實現一個用戶認證系統',
      '創建一個 React 組件',
      '幫我寫這個 API 的端點'
    ],
    keywords: ['寫代碼', '實現', '創建', '開發', '函數'],
    required_entities: ['language', 'functionality'],
    complexity: 'complex'
  },
  
  CODE_REVIEW: {
    code: 'tech.code_review',
    description: '審查代碼質量和問題',
    examples: [
      '幫我 review 這段代碼',
      '這個實現有什麼問題嗎？',
      '檢查代碼風格是否符合規範',
      '找出潛在的安全漏洞'
    ],
    keywords: ['review', '審查', '檢查', '問題', '改進'],
    required_entities: ['code_snippet'],
    complexity: 'moderate'
  },
  
  DEBUGGING: {
    code: 'tech.debugging',
    description: '調試和解決錯誤',
    examples: [
      '這個錯誤是什麼意思？',
      '為什麼程序崩潰了？',
      '幫我修復這個 bug',
      '這個異常怎麼處理？'
    ],
    keywords: ['bug', '錯誤', '異常', '崩潰', '修復', 'debug'],
    required_entities: ['error_message'],
    complexity: 'moderate'
  },
  
  SYSTEM_ARCHITECTURE: {
    code: 'tech.system_architecture',
    description: '系統設計和架構決策',
    examples: [
      '設計一個微服務架構',
      '這個系統應該用什麼數據庫？',
      '如何實現高可用性？',
      '評估這個架構方案'
    ],
    keywords: ['架構', '設計', '系統', '微服務', '數據庫'],
    required_entities: ['system_requirements'],
    complexity: 'complex'
  }
};
```

#### 3.2.3 MONITORING（監控）領域

```typescript
const MonitoringIntents = {
  STOCK_MONITOR: {
    code: 'monitoring.stock_monitor',
    description: '監控股票價格和指標',
    examples: [
      '監控台積電股價，超過 600 元通知我',
      '追蹤我的投資組合表現',
      '設定止損提醒',
      '監控成交量異常'
    ],
    keywords: ['監控', '追蹤', '提醒', '通知', '股票'],
    required_entities: ['symbol', 'condition', 'threshold'],
    complexity: 'moderate'
  },
  
  PRICE_ALERT: {
    code: 'monitoring.price_alert',
    description: '商品價格變動提醒',
    examples: [
      'iPhone 降價通知我',
      '監控這個商品的價格變化',
      '機票價格低於 5000 通知我',
      '追蹤比特幣價格'
    ],
    keywords: ['價格', '降價', '優惠', '提醒', '通知'],
    required_entities: ['product', 'target_price'],
    complexity: 'simple'
  },
  
  NEWS_TRACKING: {
    code: 'monitoring.news_tracking',
    description: '新聞和資訊追蹤',
    examples: [
      '追蹤 AI 領域的最新新聞',
      '有關於蘋果公司的最新消息嗎？',
      '監控這個話題的發展',
      '設定關鍵字提醒'
    ],
    keywords: ['新聞', '追蹤', '最新', '資訊', '報導'],
    required_entities: ['topic', 'source_preference'],
    complexity: 'simple'
  },
  
  SYSTEM_MONITOR: {
    code: 'monitoring.system_monitor',
    description: '系統健康狀態監控',
    examples: [
      '檢查系統狀態',
      '監控硬碟使用率',
      'CPU 使用率過高提醒',
      '檢查服務是否正常運行'
    ],
    keywords: ['系統', '監控', '狀態', '使用率', '健康'],
    required_entities: ['metric_type', 'threshold'],
    complexity: 'moderate'
  }
};
```

### 3.3 意圖組合規則

```typescript
interface IntentComposition {
  // 順序組合：按順序執行多個意圖
  sequential: {
    pattern: 'A → B → C',
    example: '查詢股價 → 分析趨勢 → 設定監控',
    condition: '前一個意圖完成後觸發下一個'
  },
  
  // 並行組合：同時執行多個獨立意圖
  parallel: {
    pattern: 'A + B + C',
    example: '同時監控多檔股票',
    condition: '意圖之間無依賴關係'
  },
  
  // 條件組合：根據結果選擇分支
  conditional: {
    pattern: 'A → (B | C)',
    example: '分析預算 → 如果超支則警告，否則繼續監控',
    condition: '基於前一個意圖的輸出決定'
  }
}
```

---

## 4. 與 ClawTeam 7人角色的映射關係

### 4.1 ClawTeam 角色定義

```
┌─────────────────────────────────────────────────────────────┐
│                     ClawTeam 組織架構                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                    ┌──────────────┐                         │
│                    │   隊長 (Captain) │                      │
│                    │   協調與決策    │                       │
│                    └───────┬──────┘                         │
│                            │                                │
│        ┌───────────────────┼───────────────────┐            │
│        │                   │                   │            │
│   ┌────┴────┐        ┌────┴────┐        ┌────┴────┐       │
│   │ 財務官  │        │ 技術官  │        │ 分析師  │       │
│   │Finance │        │  Tech   │        │ Analyst │       │
│   └────┬────┘        └────┬────┘        └────┬────┘       │
│        │                   │                   │            │
│   ┌────┴────┐        ┌────┴────┐        ┌────┴────┐       │
│   │ 監控員  │        │ 研究員  │        │ 執行員  │       │
│   │Monitor │        │Research │        │Executor │       │
│   └─────────┘        └─────────┘        └─────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 角色-意圖映射表

| 角色 | 英文名稱 | 主要職責 | 對應意圖類別 | 處理複雜度 |
|------|---------|---------|-------------|-----------|
| **隊長** | Captain | 意圖分發、衝突解決、最終決策 | 所有類別（路由層） | N/A |
| **財務官** | Finance Officer | 財務分析、預算管理、投資建議 | FINANCE | 中-高 |
| **技術官** | Tech Officer | 代碼開發、技術架構、問題排查 | TECHNOLOGY | 高 |
| **分析師** | Analyst | 數據分析、報告生成、趨勢預測 | RESEARCH + MONITORING | 中-高 |
| **監控員** | Monitor | 實時監控、警報處理、狀態追蹤 | MONITORING | 低-中 |
| **研究員** | Researcher | 資訊搜集、深度研究、文檔處理 | RESEARCH | 中 |
| **執行員** | Executor | 任務執行、日程管理、自動化 | LIFESTYLE + META | 低-中 |

### 4.3 詳細映射關係

#### 4.3.1 隊長 (Captain) - 中央協調器

```typescript
const CaptainConfig = {
  role: 'orchestrator',
  description: '中央協調器，負責意圖分發和衝突解決',
  
  responsibilities: [
    '接收所有用戶輸入',
    '執行 IntentGate 分類',
    '決定任務分配給哪個角色',
    '處理多意圖組合',
    '解決角色間的衝突',
    '監控整體執行狀態'
  ],
  
  routingRules: {
    'finance.*': 'FinanceOfficer',
    'tech.*': 'TechOfficer',
    'monitoring.*': 'Monitor',
    'research.*': 'Researcher',
    'lifestyle.*': 'Executor',
    'meta.*': 'Captain',  // 自己處理
    'critical.*': 'Captain'  // 緊急情況升級
  },
  
  fallbackStrategy: {
    lowConfidence: 'request_clarification',  // 低置信度時請求澄清
    multiIntent: 'decompose_and_parallel',   // 多意圖時分解並行
    conflict: 'escalate_to_human'            // 衝突時升級
  }
};
```

#### 4.3.2 財務官 (Finance Officer)

```typescript
const FinanceOfficerConfig = {
  role: 'specialist',
  description: '財務專家，處理所有財務相關任務',
  
  assignedIntents: [
    'finance.expense_tracking',
    'finance.budget_analysis',
    'finance.investment_research',
    'finance.accounting_query',
    'finance.financial_report'
  ],
  
  skills: [
    'accounting-bot',
    'stock-study',
    'data-analyst',
    'spreadsheet'
  ],
  
  modelPreference: 'claude-sonnet-4',  // 平衡成本和性能
  
  escalationTriggers: [
    '涉及法律合規問題',
    '需要專業會計師簽證',
    '涉及大額交易決策（>100萬）'
  ]
};
```

#### 4.3.3 技術官 (Tech Officer)

```typescript
const TechOfficerConfig = {
  role: 'specialist',
  description: '技術專家，處理所有技術開發任務',
  
  assignedIntents: [
    'tech.code_development',
    'tech.code_review',
    'tech.debugging',
    'tech.system_architecture',
    'tech.devops',
    'tech.technical_research'
  ],
  
  skills: [
    'coding-agent',
    'github-cli',
    'git-workflows',
    'github-actions-generator'
  ],
  
  modelPreference: 'gpt-5.4',  // 深度編碼能力
  
  subAgents: {
    'code_development': 'HephaestusMode',  // 深度開發模式
    'code_review': 'OracleMode',           // 架構審查模式
    'debugging': 'AtlasMode'               // 執行調試模式
  }
};
```

#### 4.3.4 分析師 (Analyst)

```typescript
const AnalystConfig = {
  role: 'specialist',
  description: '數據分析專家，處理複雜分析和報告',
  
  assignedIntents: [
    'research.data_analysis',
    'research.trend_analysis',
    'research.competitive_intel',
    'monitoring.stock_monitor',
    'finance.budget_analysis'
  ],
  
  skills: [
    'data-analyst-pro',
    'data-anomaly-detector',
    'stock-strategy-backtester',
    'excel-xlsx'
  ],
  
  capabilities: [
    'statistical_analysis',
    'predictive_modeling',
    'data_visualization',
    'report_generation'
  ]
};
```

#### 4.3.5 監控員 (Monitor)

```typescript
const MonitorConfig = {
  role: 'specialist',
  description: '監控專家，處理實時監控和警報',
  
  assignedIntents: [
    'monitoring.stock_monitor',
    'monitoring.price_alert',
    'monitoring.news_tracking',
    'monitoring.system_monitor',
    'monitoring.data_sync'
  ],
  
  skills: [
    'stock-watcher',
    'stock-monitor',
    'red-alert',
    'pushover-notify',
    'universal-notify'
  ],
  
  executionMode: 'background',  // 背景持續運行
  
  alertChannels: [
    'whatsapp',
    'email',
    'pushover',
    'webhook'
  ]
};
```

#### 4.3.6 研究員 (Researcher)

```typescript
const ResearcherConfig = {
  role: 'specialist',
  description: '研究專家，處理資訊搜集和深度研究',
  
  assignedIntents: [
    'research.web_search',
    'research.document_processing',
    'tech.technical_research',
    'finance.investment_research'
  ],
  
  skills: [
    'tavily-search',
    'web-content-fetcher',
    'pdf-to-markdown',
    'github-research'
  ],
  
  researchDepth: {
    'quick': 'basic_search',      // 快速搜索
    'standard': 'multi_source',   // 多源驗證
    'deep': 'comprehensive'       // 全面深入研究
  }
};
```

#### 4.3.7 執行員 (Executor)

```typescript
const ExecutorConfig = {
  role: 'specialist',
  description: '執行專家，處理日常任務和自動化',
  
  assignedIntents: [
    'lifestyle.scheduling',
    'lifestyle.travel_planning',
    'lifestyle.shopping',
    'lifestyle.personal_task',
    'meta.skill_management',
    'meta.configuration'
  ],
  
  skills: [
    'outlook',
    'desktop-control-win',
    'windows-ui-automation',
    'webhook-send'
  ],
  
  automationCapabilities: [
    'schedule_tasks',
    'send_notifications',
    'trigger_workflows',
    'manage_files'
  ]
};
```

### 4.4 動態組隊規則

```typescript
interface TeamFormation {
  // 單一專家模式
  singleExpert: {
    condition: 'intent.confidence > 0.85 && subIntents.length === 1',
    example: '簡單的支出記錄 → 僅 FinanceOfficer'
  },
  
  // 雙人協作模式
  pairCollaboration: {
    condition: 'intent.complexity === "complex" || subIntents.length === 2',
    example: '投資研究 → Researcher + FinanceOfficer',
    collaborationPattern: 'Researcher 搜集資訊 → FinanceOfficer 分析建議'
  },
  
  // 小組模式
  squadMode: {
    condition: 'intent.complexity === "complex" && subIntents.length >= 3',
    example: '新產品開發項目',
    roles: ['TechOfficer', 'Analyst', 'Researcher', 'Executor']
  },
  
  // 全員模式
  fullTeam: {
    condition: 'intent.urgency === "critical" || intent.domain === "composite"',
    example: '系統全面升級項目',
    coordination: 'Captain 主持每日站會'
  }
}
```

---

## 5. 代碼框架與實現方案

### 5.1 核心架構

```typescript
// intentgate/core/types.ts

// 意圖定義
export interface Intent {
  code: string;
  name: string;
  description: string;
  domain: string;
  examples: string[];
  keywords: string[];
  requiredEntities: string[];
  complexity: 'simple' | 'moderate' | 'complex';
  embedding?: number[];
}

// 意圖分類結果
export interface IntentClassification {
  primaryIntent: Intent;
  subIntents: Intent[];
  confidence: number;
  entities: Entity[];
  urgency: UrgencyLevel;
  complexity: ComplexityLevel;
  timestamp: Date;
}

// 實體定義
export interface Entity {
  type: string;
  value: string;
  confidence: number;
  startPos?: number;
  endPos?: number;
}

// 路由決策
export interface RoutingDecision {
  targetAgent: string;
  strategy: 'direct' | 'hybrid' | 'fallback';
  confidence: number;
  context: IntentContext;
  fallbackChain: string[];
}

// 意圖上下文
export interface IntentContext {
  originalQuery: string;
  classification: IntentClassification;
  metadata: Record<string, any>;
  sessionId: string;
  userId: string;
}
```

### 5.2 IntentGate 核心類

```typescript
// intentgate/core/IntentGate.ts

import { OpenAIEmbeddings } from '@langchain/openai';
import { cosineSimilarity } from './utils';

export class IntentGate {
  private routes: Map<string, Intent>;
  private embeddings: OpenAIEmbeddings;
  private threshold: number;
  private captain: CaptainAgent;
  
  constructor(config: IntentGateConfig) {
    this.routes = new Map();
    this.embeddings = new OpenAIEmbeddings({
      modelName: config.embeddingModel || 'text-embedding-3-small'
    });
    this.threshold = config.threshold || 0.75;
    this.captain = new CaptainAgent(config.captainConfig);
    
    this.initializeRoutes();
  }
  
  // 初始化所有意圖路由
  private async initializeRoutes(): Promise<void> {
    const allIntents = [
      ...Object.values(FinanceIntents),
      ...Object.values(TechnologyIntents),
      ...Object.values(MonitoringIntents),
      ...Object.values(ResearchIntents),
      ...Object.values(LifestyleIntents),
      ...Object.values(MetaIntents)
    ];
    
    for (const intent of allIntents) {
      // 預計算每個意圖的嵌入向量
      const text = `${intent.description}\n${intent.examples.join('\n')}`;
      intent.embedding = await this.embeddings.embedQuery(text);
      this.routes.set(intent.code, intent);
    }
  }
  
  // 主要入口：處理用戶查詢
  async process(query: string, context?: Partial<IntentContext>): Promise<RoutingDecision> {
    // 步驟 1: 意圖分類
    const classification = await this.classify(query);
    
    // 步驟 2: 實體提取
    const entities = await this.extractEntities(query, classification);
    classification.entities = entities;
    
    // 步驟 3: 緊急程度評估
    classification.urgency = this.assessUrgency(query, classification);
    
    // 步驟 4: 路由決策
    const decision = await this.makeRoutingDecision(query, classification);
    
    // 步驟 5: 執行路由
    return decision;
  }
  
  // 意圖分類核心算法
  private async classify(query: string): Promise<IntentClassification> {
    const queryEmbedding = await this.embeddings.embedQuery(query);
    
    const similarities: Array<{ intent: Intent; score: number }> = [];
    
    for (const [code, intent] of this.routes) {
      if (intent.embedding) {
        const score = cosineSimilarity(queryEmbedding, intent.embedding);
        similarities.push({ intent, score });
      }
    }
    
    // 排序並選擇最佳匹配
    similarities.sort((a, b) => b.score - a.score);
    
    const primary = similarities[0];
    const subIntents = similarities
      .slice(1, 4)
      .filter(s => s.score > this.threshold * 0.9)
      .map(s => s.intent);
    
    return {
      primaryIntent: primary.intent,
      subIntents,
      confidence: primary.score,
      entities: [],
      urgency: 'medium',
      complexity: primary.intent.complexity,
      timestamp: new Date()
    };
  }
  
  // 實體提取
  private async extractEntities(
    query: string, 
    classification: IntentClassification
  ): Promise<Entity[]> {
    const entities: Entity[] = [];
    const intent = classification.primaryIntent;
    
    // 基於規則的實體提取
    for (const entityType of intent.requiredEntities) {
      const extracted = this.extractEntityByType(query, entityType);
      if (extracted) {
        entities.push(extracted);
      }
    }
    
    // 使用 LLM 進行補充提取
    const llmEntities = await this.extractWithLLM(query, intent);
    entities.push(...llmEntities);
    
    return entities;
  }
  
  // 緊急程度評估
  private assessUrgency(query: string, classification: IntentClassification): UrgencyLevel {
    const urgentKeywords = ['緊急', '馬上', '立刻', '現在', 'asap', 'urgent', 'critical'];
    const hasUrgentKeyword = urgentKeywords.some(kw => 
      query.toLowerCase().includes(kw.toLowerCase())
    );
    
    if (classification.primaryIntent.code.startsWith('critical.')) {
      return 'critical';
    }
    
    if (hasUrgentKeyword) {
      return 'high';
    }
    
    return 'medium';
  }
  
  // 路由決策
  private async makeRoutingDecision(
    query: string,
    classification: IntentClassification
  ): Promise<RoutingDecision> {
    const confidence = classification.confidence;
    
    let strategy: RoutingStrategy;
    let targetAgent: string;
    
    if (confidence >= 0.85) {
      // 高置信度：直接路由
      strategy = 'direct';
      targetAgent = this.mapIntentToAgent(classification.primaryIntent);
    } else if (confidence >= 0.70) {
      // 中等置信度：混合模式（LLM 確認）
      strategy = 'hybrid';
      targetAgent = await this.confirmWithLLM(query, classification);
    } else {
      // 低置信度：降級處理
      strategy = 'fallback';
      targetAgent = 'Captain';  // 交給隊長決定
    }
    
    return {
      targetAgent,
      strategy,
      confidence,
      context: {
        originalQuery: query,
        classification,
        metadata: {},
        sessionId: context?.sessionId || generateSessionId(),
        userId: context?.userId || 'anonymous'
      },
      fallbackChain: this.buildFallbackChain(classification)
    };
  }
  
  // 意圖到代理的映射
  private mapIntentToAgent(intent: Intent): string {
    const domainAgentMap: Record<string, string> = {
      'finance': 'FinanceOfficer',
      'tech': 'TechOfficer',
      'monitoring': 'Monitor',
      'research': 'Researcher',
      'lifestyle': 'Executor',
      'meta': 'Captain',
      'critical': 'Captain'
    };
    
    const domain = intent.code.split('.')[0];
    return domainAgentMap[domain] || 'Captain';
  }
  
  // 構建降級鏈
  private buildFallbackChain(classification: IntentClassification): string[] {
    const chain = ['Captain'];
    
    // 根據意圖類型添加備選
    if (classification.primaryIntent.code.startsWith('finance.')) {
      chain.push('Analyst', 'Executor');
    } else if (classification.primaryIntent.code.startsWith('tech.')) {
      chain.push('Researcher', 'Captain');
    }
    
    return chain;
  }
}
```

### 5.3 Captain Agent 實現

```typescript
// intentgate/agents/CaptainAgent.ts

export class CaptainAgent {
  private team: Map<string, SpecialistAgent>;
  private llm: ChatOpenAI;
  
  constructor(config: CaptainConfig) {
    this.team = new Map();
    this.llm = new ChatOpenAI({ modelName: 'gpt-4' });
    
    // 初始化團隊成員
    this.initializeTeam();
  }
  
  private initializeTeam(): void {
    this.team.set('FinanceOfficer', new FinanceOfficerAgent());
    this.team.set('TechOfficer', new TechOfficerAgent());
    this.team.set('Analyst', new AnalystAgent());
    this.team.set('Monitor', new MonitorAgent());
    this.team.set('Researcher', new ResearcherAgent());
    this.team.set('Executor', new ExecutorAgent());
  }
  
  // 協調執行
  async orchestrate(decision: RoutingDecision): Promise<ExecutionResult> {
    const { targetAgent, context } = decision;
    
    // 單一代理執行
    if (context.classification.subIntents.length === 0) {
      return this.executeSingleAgent(targetAgent, context);
    }
    
    // 多代理協作
    if (context.classification.subIntents.length > 0) {
      return this.executeCollaborative(context);
    }
    
    // 複雜任務分解
    if (context.classification.complexity === 'complex') {
      return this.executeDecomposed(context);
    }
    
    return this.executeSingleAgent(targetAgent, context);
  }
  
  // 單一代理執行
  private async executeSingleAgent(
    agentName: string, 
    context: IntentContext
  ): Promise<ExecutionResult> {
    const agent = this.team.get(agentName);
    if (!agent) {
      throw new Error(`Agent ${agentName} not found`);
    }
    
    return agent.execute(context);
  }
  
  // 協作執行
  private async executeCollaborative(context: IntentContext): Promise<ExecutionResult> {
    const results: Record<string, any> = {};
    
    // 並行執行獨立子任務
    const independentTasks = context.classification.subIntents
      .filter(intent => this.isIndependent(intent));
    
    await Promise.all(
      independentTasks.map(async (intent) => {
        const agentName = this.mapIntentToAgent(intent);
        const agent = this.team.get(agentName);
        if (agent) {
          results[intent.code] = await agent.execute({
            ...context,
            classification: { ...context.classification, primaryIntent: intent }
          });
        }
      })
    );
    
    // 聚合結果
    return this.aggregateResults(results, context);
  }
  
  // 任務分解執行
  private async executeDecomposed(context: IntentContext): Promise<ExecutionResult> {
    // 使用 LLM 分解任務
    const decomposition = await this.decomposeTask(context);
    
    // 按依賴順序執行
    const executionPlan = this.topologicalSort(decomposition.tasks);
    
    const results: Record<string, any> = {};
    for (const task of executionPlan) {
      const agent = this.team.get(task.agent);
      if (agent) {
        results[task.id] = await agent.execute({
          ...context,
          task: task
        });
      }
    }
    
    return {
      success: true,
      results,
      summary: await this.generateSummary(results, context)
    };
  }
  
  // 任務分解
  private async decomposeTask(context: IntentContext): Promise<TaskDecomposition> {
    const prompt = `
      將以下複雜任務分解為可執行的子任務：
      
      用戶查詢: ${context.originalQuery}
      主要意圖: ${context.classification.primaryIntent.name}
      複雜度: ${context.classification.complexity}
      
      可用代理: ${Array.from(this.team.keys()).join(', ')}
      
      請輸出 JSON 格式的任務分解：
      {
        "tasks": [
          {
            "id": "task_1",
            "description": "任務描述",
            "agent": "負責代理",
            "dependencies": ["依賴的任務ID"],
            "estimatedTime": "預計時間"
          }
        ]
      }
    `;
    
    const response = await this.llm.invoke(prompt);
    return JSON.parse(response.content);
  }
  
  // 結果聚合
  private async aggregateResults(
    results: Record<string, any>,
    context: IntentContext
  ): Promise<ExecutionResult> {
    const prompt = `
      將以下多個代理的執行結果整合為一個連貫的回應：
      
      用戶查詢: ${context.originalQuery}
      
      執行結果:
      ${JSON.stringify(results, null, 2)}
      
      請提供：
      1. 綜合摘要
      2. 關鍵發現
      3. 建議行動
    `;
    
    const summary = await this.llm.invoke(prompt);
    
    return {
      success: true,
      results,
      summary: summary.content
    };
  }
}
```

### 5.4 配置系統

```typescript
// intentgate/config/default.ts

export const DefaultIntentGateConfig: IntentGateConfig = {
  // 嵌入模型配置
  embeddingModel: 'text-embedding-3-small',
  
  // 相似度閾值
  threshold: 0.75,
  
  // 隊長配置
  captainConfig: {
    model: 'gpt-4',
    maxIterations: 5,
    enableReflection: true
  },
  
  // 路由配置
  routing: {
    enableHybridMode: true,
    enableParallelExecution: true,
    maxParallelAgents: 5,
    timeoutMs: 300000  // 5分鐘
  },
  
  // 降級策略
  fallback: {
    lowConfidenceAction: 'request_clarification',
    timeoutAction: 'escalate_to_human',
    errorAction: 'retry_with_backup_agent'
  },
  
  // 監控配置
  monitoring: {
    enableMetrics: true,
    logLevel: 'info',
    trackLatency: true
  }
};

// 意圖定義配置
export const IntentDefinitions = {
  // 財務意圖
  FINANCE: {
    EXPENSE_TRACKING: {
      code: 'finance.expense_tracking',
      name: '支出追蹤',
      description: '記錄和追蹤個人或企業支出',
      examples: [
        '記錄今天午餐花了 50 元',
        '查看本月支出總額',
        '分類上週的所有消費'
      ],
      keywords: ['支出', '花費', '記帳', '預算'],
      agent: 'FinanceOfficer',
      complexity: 'simple'
    },
    
    INVESTMENT_RESEARCH: {
      code: 'finance.investment_research',
      name: '投資研究',
      description: '研究投資標的和分析',
      examples: [
        '研究蘋果公司的財報',
        '分析特斯拉股票的技術指標'
      ],
      keywords: ['股票', '投資', '財報', '分析'],
      agent: 'FinanceOfficer',
      complexity: 'complex'
    }
  },
  
  // 技術意圖
  TECHNOLOGY: {
    CODE_DEVELOPMENT: {
      code: 'tech.code_development',
      name: '代碼開發',
      description: '編寫新代碼或實現功能',
      examples: [
        '寫一個 Python 函數來計算斐波那契數列',
        '實現一個用戶認證系統'
      ],
      keywords: ['寫代碼', '實現', '創建', '開發'],
      agent: 'TechOfficer',
      complexity: 'complex'
    },
    
    DEBUGGING: {
      code: 'tech.debugging',
      name: '除錯',
      description: '調試和解決錯誤',
      examples: [
        '這個錯誤是什麼意思？',
        '幫我修復這個 bug'
      ],
      keywords: ['bug', '錯誤', '異常', '修復'],
      agent: 'TechOfficer',
      complexity: 'moderate'
    }
  },
  
  // 監控意圖
  MONITORING: {
    STOCK_MONITOR: {
      code: 'monitoring.stock_monitor',
      name: '股票監控',
      description: '監控股票價格和指標',
      examples: [
        '監控台積電股價，超過 600 元通知我',
        '追蹤我的投資組合表現'
      ],
      keywords: ['監控', '追蹤', '提醒', '股票'],
      agent: 'Monitor',
      complexity: 'moderate'
    },
    
    PRICE_ALERT: {
      code: 'monitoring.price_alert',
      name: '價格提醒',
      description: '商品價格變動提醒',
      examples: [
        'iPhone 降價通知我',
        '監控這個商品的價格變化'
      ],
      keywords: ['價格', '降價', '優惠', '提醒'],
      agent: 'Monitor',
      complexity: 'simple'
    }
  },
  
  // 研究意圖
  RESEARCH: {
    WEB_SEARCH: {
      code: 'research.web_search',
      name: '網頁搜索',
      description: '搜索網頁資訊',
      examples: [
        '搜索最新的 AI 發展',
        '查找關於區塊鏈的資料'
      ],
      keywords: ['搜索', '查找', '資訊', '資料'],
      agent: 'Researcher',
      complexity: 'simple'
    },
    
    DATA_ANALYSIS: {
      code: 'research.data_analysis',
      name: '數據分析',
      description: '分析數據和生成報告',
      examples: [
        '分析這份銷售數據',
        '生成數據視覺化報告'
      ],
      keywords: ['分析', '數據', '報告', '統計'],
      agent: 'Analyst',
      complexity: 'complex'
    }
  }
};
```

### 5.5 使用示例

```typescript
// 示例 1: 基本使用
import { IntentGate } from './intentgate';

const gate = new IntentGate(DefaultIntentGateConfig);

// 處理查詢
const result = await gate.process('記錄今天午餐花了 120 元');
console.log(result);
// 輸出:
// {
//   targetAgent: 'FinanceOfficer',
//   strategy: 'direct',
//   confidence: 0.92,
//   context: { ... }
// }

// 示例 2: 複雜查詢
const complexResult = await gate.process(
  '研究台積電的財報，分析投資價值，並設定股價監控'
);
console.log(complexResult);
// 輸出:
// {
//   targetAgent: 'Captain',
//   strategy: 'hybrid',
//   confidence: 0.78,
//   context: {
//     primaryIntent: 'finance.investment_research',
//     subIntents: ['monitoring.stock_monitor'],
//     complexity: 'complex'
//   }
// }

// 示例 3: 執行任務
const executionResult = await gate.execute('幫我寫一個 Python 爬蟲程序');
console.log(executionResult);
```

---

## 6. 整合入現有系統的步驟

### 6.1 整合路線圖

```
Phase 1: 基礎建設 (2-3 週)
├── 安裝依賴和配置環境
├── 實現核心 IntentGate 類
├── 定義基礎意圖分類
└── 單元測試

Phase 2: 代理集成 (2-3 週)
├── 實現 Captain Agent
├── 集成現有 Specialist Agents
├── 建立代理間通信機制
└── 集成測試

Phase 3: 功能完善 (2 週)
├── 添加多意圖處理
├── 實現任務分解
├── 添加監控和日誌
└── 性能優化

Phase 4: 生產部署 (1-2 週)
├── 灰度發布
├── A/B 測試
├── 監控告警
└── 文檔完善
```

### 6.2 詳細整合步驟

#### 步驟 1: 環境準備

```bash
# 1.1 安裝依賴
npm install @langchain/openai @langchain/core
npm install openai
npm install vector-db-client  # 向量數據庫客戶端

# 1.2 配置環境變量
cat > .env << EOF
OPENAI_API_KEY=your_api_key
INTENTGATE_THRESHOLD=0.75
INTENTGATE_EMBEDDING_MODEL=text-embedding-3-small
LOG_LEVEL=info
EOF
```

#### 步驟 2: 核心代碼部署

```bash
# 2.1 創建目錄結構
mkdir -p src/intentgate/{core,agents,config,utils}
mkdir -p src/intentgate/skills
mkdir -p tests/intentgate

# 2.2 複製核心文件
cp intentgate/core/*.ts src/intentgate/core/
cp intentgate/agents/*.ts src/intentgate/agents/
cp intentgate/config/*.ts src/intentgate/config/

# 2.3 編譯
tsc --build
```

#### 步驟 3: 與現有系統集成

```typescript
// src/integration/openclaw-bridge.ts

import { IntentGate } from '../intentgate';
import { OpenClawMessageHandler } from './message-handler';

export class OpenClawIntentGateBridge {
  private intentGate: IntentGate;
  private messageHandler: OpenClawMessageHandler;
  
  constructor() {
    this.intentGate = new IntentGate(DefaultIntentGateConfig);
    this.messageHandler = new OpenClawMessageHandler();
    
    this.setupIntegration();
  }
  
  private setupIntegration(): void {
    // 攔截所有傳入消息
    this.messageHandler.onMessage(async (message) => {
      // 使用 IntentGate 處理
      const decision = await this.intentGate.process(message.text, {
        userId: message.from,
        sessionId: message.sessionId
      });
      
      // 記錄決策
      this.logDecision(decision);
      
      // 執行路由
      return this.executeRoute(decision);
    });
  }
  
  private async executeRoute(decision: RoutingDecision): Promise<Response> {
    const { targetAgent, context } = decision;
    
    // 調用對應的 Skill
    switch (targetAgent) {
      case 'FinanceOfficer':
        return this.invokeSkill('accounting-bot', context);
      case 'TechOfficer':
        return this.invokeSkill('coding-agent', context);
      case 'Monitor':
        return this.invokeSkill('stock-monitor', context);
      case 'Researcher':
        return this.invokeSkill('tavily-search', context);
      case 'Analyst':
        return this.invokeSkill('data-analyst-pro', context);
      case 'Executor':
        return this.invokeSkill('desktop-control-win', context);
      case 'Captain':
      default:
        return this.handleCaptainRequest(context);
    }
  }
  
  private async invokeSkill(skillName: string, context: IntentContext): Promise<Response> {
    // 調用 OpenClaw Skill 系統
    const skill = await loadSkill(skillName);
    return skill.execute(context);
  }
}
```

#### 步驟 4: Skill 適配

為現有 Skills 添加 IntentGate 支持：

```typescript
// skills/accounting-bot/intent-adapter.ts

import { SkillAdapter } from '../intentgate';

export class AccountingBotAdapter implements SkillAdapter {
  name = 'accounting-bot';
  
  supportedIntents = [
    'finance.expense_tracking',
    'finance.budget_analysis',
    'finance.accounting_query'
  ];
  
  async canHandle(context: IntentContext): Promise<boolean> {
    return this.supportedIntents.includes(
      context.classification.primaryIntent.code
    );
  }
  
  async execute(context: IntentContext): Promise<SkillResult> {
    const { primaryIntent, entities } = context.classification;
    
    switch (primaryIntent.code) {
      case 'finance.expense_tracking':
        return this.trackExpense(entities);
      case 'finance.budget_analysis':
        return this.analyzeBudget(entities);
      case 'finance.accounting_query':
        return this.handleAccountingQuery(context);
      default:
        throw new Error(`Unsupported intent: ${primaryIntent.code}`);
    }
  }
  
  private async trackExpense(entities: Entity[]): Promise<SkillResult> {
    const amount = entities.find(e => e.type === 'amount')?.value;
    const category = entities.find(e => e.type === 'category')?.value;
    
    // 調用原有的 accounting-bot 功能
    return accountingBot.recordExpense({ amount, category });
  }
}
```

#### 步驟 5: 配置更新

```yaml
# config/intentgate.yaml

intentgate:
  enabled: true
  threshold: 0.75
  
  embedding:
    model: text-embedding-3-small
    cache_enabled: true
    
  routing:
    default_agent: Captain
    fallback_enabled: true
    parallel_execution: true
    max_parallel_agents: 5
    
  agents:
    FinanceOfficer:
      skills:
        - accounting-bot
        - stock-study
      model: claude-sonnet-4
      
    TechOfficer:
      skills:
        - coding-agent
        - github-cli
      model: gpt-5.4
      
    Monitor:
      skills:
        - stock-monitor
        - red-alert
      execution_mode: background
      
    Researcher:
      skills:
        - tavily-search
        - web-content-fetcher
        
    Analyst:
      skills:
        - data-analyst-pro
        - excel-xlsx
        
    Executor:
      skills:
        - desktop-control-win
        - webhook-send
        
    Captain:
      skills:
        - all
      coordination_mode: hierarchical

  monitoring:
    enabled: true
    metrics:
      - intent_classification_accuracy
      - routing_latency
      - agent_execution_time
      - fallback_rate
```

#### 步驟 6: 測試驗證

```typescript
// tests/intentgate/integration.test.ts

describe('IntentGate Integration', () => {
  let bridge: OpenClawIntentGateBridge;
  
  beforeAll(() => {
    bridge = new OpenClawIntentGateBridge();
  });
  
  test('should route finance queries to FinanceOfficer', async () => {
    const result = await bridge.process('記錄支出 100 元');
    expect(result.targetAgent).toBe('FinanceOfficer');
    expect(result.confidence).toBeGreaterThan(0.8);
  });
  
  test('should route tech queries to TechOfficer', async () => {
    const result = await bridge.process('寫一個 Python 函數');
    expect(result.targetAgent).toBe('TechOfficer');
  });
  
  test('should handle multi-intent queries', async () => {
    const result = await bridge.process(
      '研究台積電並設定股價監控'
    );
    expect(result.context.classification.subIntents.length).toBeGreaterThan(0);
  });
  
  test('should fallback to Captain for uncertain queries', async () => {
    const result = await bridge.process('???');
    expect(result.strategy).toBe('fallback');
    expect(result.targetAgent).toBe('Captain');
  });
});
```

### 6.3 遷移策略

```
現有系統                    IntentGate 系統
    │                            │
    ▼                            ▼
┌─────────┐                ┌─────────────┐
│ 用戶輸入 │ ─────────────▶│ IntentGate  │
└─────────┘                └──────┬──────┘
    │                             │
    │    並行運行（漸進遷移）       │
    ▼                             ▼
┌─────────┐                ┌─────────────┐
│ 舊路由   │                │ 新路由      │
│ 邏輯    │                │ (IntentGate)│
└────┬────┘                └──────┬──────┘
     │                            │
     └──────────┬─────────────────┘
                ▼
          ┌──────────┐
          │ 結果比較  │
          │ A/B Test │
          └────┬─────┘
               ▼
         ┌──────────┐
         │ 最終輸出  │
         └──────────┘
```

### 6.4 監控儀表板

```typescript
// monitoring/dashboard.ts

export class IntentGateDashboard {
  // 實時指標
  getRealtimeMetrics() {
    return {
      // 分類準確率
      classificationAccuracy: this.calculateAccuracy(),
      
      // 路由分佈
      routingDistribution: {
        FinanceOfficer: 25,
        TechOfficer: 30,
        Monitor: 15,
        Researcher: 10,
        Analyst: 10,
        Executor: 8,
        Captain: 2
      },
      
      // 延遲統計
      latencyStats: {
        p50: 120,
        p95: 350,
        p99: 800
      },
      
      // 降級率
      fallbackRate: 0.05,
      
      // 錯誤率
      errorRate: 0.02
    };
  }
  
  // 意圖熱圖
  getIntentHeatmap() {
    return {
      'finance.expense_tracking': { count: 150, avgConfidence: 0.92 },
      'tech.code_development': { count: 200, avgConfidence: 0.88 },
      'monitoring.stock_monitor': { count: 80, avgConfidence: 0.90 }
    };
  }
}
```

---

## 7. 附錄：參考資料

### 7.1 學術論文

1. **Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks**
   - Reimers & Gurevych (2019)
   - https://arxiv.org/abs/1908.10084

2. **Learning to Route in Similarity Graphs**
   - Baranchuk et al. (2019)
   - https://arxiv.org/abs/1905.10987

3. **Adaptive Intent Classification via Online Clustering**
   - Chen et al. (2024)

4. **CoRouter: Combining Semantic and LLM-based Routing**
   - Liu et al. (2024)

### 7.2 開源項目

1. **Oh-My-OpenAgent**
   - https://ohmyopenagent.com/
   - https://github.com/code-yeongyu/oh-my-openagent

2. **Semantic Router by Aurelio AI**
   - https://github.com/aurelio-labs/semantic-router

3. **LlamaIndex Routers**
   - https://docs.llamaindex.ai/en/stable/module_guides/querying/router/

4. **LangGraph**
   - https://langchain-ai.github.io/langgraph/

### 7.3 設計模式參考

1. **Multi-Agent Patterns That Actually Work**
   - https://medium.com/@michael.j.hamilton/multi-agent-patterns-that-actually-work-a-hands-on-guide-with-ag2-182a6e3909f7

2. **Semantic Routing and Intent Classification in AI Agent Systems**
   - https://notes.muthu.co/2025/11/semantic-routing-and-intent-classification-in-ai-agent-systems/

3. **Multi-Agent Orchestration: How to Coordinate AI Agents at Scale**
   - https://gurusup.com/blog/multi-agent-orchestration-guide

### 7.4 相關 Skills

| Skill 名稱 | 用途 | 集成方式 |
|-----------|------|---------|
| accounting-bot | 財務處理 | FinanceOfficer |
| coding-agent | 代碼開發 | TechOfficer |
| stock-monitor | 股票監控 | Monitor |
| tavily-search | 網頁搜索 | Researcher |
| data-analyst-pro | 數據分析 | Analyst |
| desktop-control-win | 桌面控制 | Executor |
| github-cli | GitHub 操作 | TechOfficer |
| pushover-notify | 通知推送 | Monitor |

---

## 總結

本研究報告為 OpenClaw + ClawTeam 設計了一套完整的 IntentGate 意圖分類系統，包括：

1. **核心機制**: 基於語義路由的智能分類
2. **分類標籤**: 覆蓋財務、技術、生活、監控、研究等領域
3. **角色映射**: 7人 ClawTeam 的職責分配和協作規則
4. **代碼框架**: 可直接實現的 TypeScript 代碼
5. **整合步驟**: 詳細的部署和遷移指南

該系統的關鍵優勢：
- **高準確率**: 語義理解而非關鍵詞匹配
- **可擴展性**: 易於添加新的意圖類別
- **靈活性**: 支持單一和複合意圖
- **容錯性**: 優雅的降級和備選機制

---

*報告完成時間: 2026-04-13*  
*版本: v1.0*  
*狀態: 可執行*
