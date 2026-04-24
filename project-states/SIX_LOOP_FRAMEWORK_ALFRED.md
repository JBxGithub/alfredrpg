# Six-Loop System Framework (Alfred 版)

> **適用對象**: 呀鬼 (Alfred) - 系統維護者/執行者  
> **版本**: v1.1  
> **更新日期**: 2026-04-23 23:10  
> **狀態**: ✅ V9.4 最終版 - 回撤優化完成

---

## 🎯 系統核心架構

### 六循環數據流

```
┌─────────────────────────────────────────────────────────────┐
│                        六循環系統架構                          │
├─────────────────────────────────────────────────────────────┤
│  感知層 → 處理層 → 決策層 → 執行層 → 成就層 → 學習層 → 循環   │
└─────────────────────────────────────────────────────────────┘

[感知層]                    [處理層]                    [決策層]
  │                          │                          │
  ▼                          ▼                          ▼
┌─────────────┐          ┌─────────────┐          ┌─────────────┐
│Futu OpenD   │─────────▶│Absolute     │─────────▶│Signal       │
│(US.QQQ)     │          │Calculator   │          │Generator    │
│Port: 11111  │          │Node-RED     │          │Python       │
└─────────────┘          └─────────────┘          └─────────────┘
      │                        │                          │
      │                  ┌─────────────┐                  │
      │                  │Reference    │                  │
      └─────────────────▶│Calculator   │──────────────────┘
                         └─────────────┘

[執行層]                    [成就層]                    [學習層]
  │                          │                          │
  ▼                          ▼                          ▼
┌─────────────┐          ┌─────────────┐          ┌─────────────┐
│FutuTrading  │─────────▶│Alfredrpg    │─────────▶│Self-        │
│Bot          │          │Daily Close  │          │Improving    │
│TQQQ Executor│          │Badges       │          │Weekly Review│
└─────────────┘          └─────────────┘          └─────────────┘
```

---

## 🔧 技術棧詳情

### 感知層 (Data Ingestion)

| 組件 | 技術 | 配置 | 狀態 |
|------|------|------|------|
| **Primary** | Futu OpenD API | `US.QQQ` @ 127.0.0.1:11111 | ✅ Active |
| **Backup 1** | investing.com | NQ 100 Index | 🟡 Standby |
| **Backup 2** | Yahoo Finance | `^NDX` | 🟡 Standby |
| **Storage** | PostgreSQL | `trading_db` @ localhost:5432 | ✅ Active |

**Key Files:**
- `futu-adapter/futu_opend_feed_v2.py` - 主數據饋送器
- `futu-adapter/backup_data_feed.py` - 備份數據源
- `config/symbols.yaml` - 標的配置

### 處理層 (Data Processing)

| 組件 | 技術 | 頻率 | 狀態 |
|------|------|------|------|
| **Absolute Calc** | Node-RED Flow 7 | 每分鐘 | ✅ Active |
| **Reference Calc** | Node-RED Flow 8 | 每分鐘 | ✅ Active |
| **Data Cache** | PostgreSQL | 實時 | ✅ Active |

**Weight Configuration:**
```yaml
absolute_weights:
  nq200ma: 30
  nq50ma: 30
  nq20ema50ema: 20
  mtf: 10
  market_phase: 10

reference_weights:
  components_breadth: 20
  components_risk: 10
  technical_rsi: 15
  technical_atr: 10
  technical_zscore: 10
  technical_macd: 5
  technical_divergence: 5
  money_flow_futures: 15
  money_flow_etf: 10
```

### 決策層 (Decision Engine)

| 組件 | 技術 | 邏輯 | 狀態 |
|------|------|------|------|
| **Score Calc** | Python | `final = abs*0.6 + ref*0.4` | ✅ Active |
| **Signal Gen** | Python | `>=70:BUY, <=30:SELL` | ✅ Active |
| **Risk Check** | Python | Multi-layer validation | ✅ Active |

**Decision Matrix:**
```python
if final_score >= 70:
    signal = "BUY"
    confidence = (final_score - 70) / 30
elif final_score <= 30:
    signal = "SELL"
    confidence = (30 - final_score) / 30
else:
    signal = "HOLD"
    confidence = 0
```

### 執行層 (Execution)

| 組件 | 技術 | 配置 | 狀態 |
|------|------|------|------|
| **Executor** | FutuTradingBot | TQQQ | 🟡 Ready |
| **Risk Mgr** | Python | Limits below | ✅ Active |

**Risk Limits (V9.4 更新):**
```yaml
risk_management:
  max_position_percent: 90%        # V9.4: 90% 倉位上限
  profit_taking:                   # V9.4: 盈利減倉
    level_1: +10% → reduce 50%
    level_2: +20% → reduce 30%
  long_params:                     # 多單穩健
    stop_loss: -3%
    trailing: -3%
    take_profit: +15%
    reeval: 7 days
  short_params:                    # 空單敏捷
    stop_loss: +2%
    trailing: +2%
    take_profit: +10%
    reeval: 3 days
  max_daily_loss: $500 (2%)
  max_total_risk: 4%
  max_positions: 3
  error_handling: pause_on_error
```

---

## 📊 監控與告警系統

### 自動監控 (Cron Jobs)

| 任務 | 頻率 | 腳本 | 通知 |
|------|------|------|------|
| **System Health** | 每 5 分鐘 | `cron/six_loop_monitor.py` | WhatsApp |
| **Daily Sync** | 每日 08:00 | `cron/daily-sync.ps1` | WhatsApp |
| **Data Quality** | 每小時 | Alert Manager | WhatsApp |

### 告警級別

```python
ALERT_LEVELS = {
    'INFO': {
        'emoji': 'ℹ️',
        'action': 'log_only',
        'notify': False
    },
    'WARNING': {
        'emoji': '⚠️',
        'action': 'check_system',
        'notify': True
    },
    'ERROR': {
        'emoji': '❌',
        'action': 'immediate_fix',
        'notify': True
    },
    'CRITICAL': {
        'emoji': '🚨',
        'action': 'stop_trading',
        'notify': True
    }
}
```

---

## 🧪 測試框架

### 端到端測試 (`e2e_test.py`)

```python
TEST_SUITE = [
    'test_database_connection',      # ✅ PostgreSQL connectivity
    'test_futu_opend_connection',    # ✅ Port 11111
    'test_futu_data_flow',           # ✅ Data ingestion
    'test_node_red_flows',           # ✅ 4 Flows running
    'test_data_quality',             # ✅ QQQ price range
    'test_risk_management_data',     # ✅ Risk calc data
    'test_backup_data_sources',      # ✅ Multiple sources
]
# Result: 7/7 passed (100%)
```

### 風險管理測試 (`risk_management_test.py`)

```python
RISK_TESTS = [
    'test_position_limits',          # ✅ Max position check
    'test_stop_loss',                # ✅ 2% SL trigger
    'test_take_profit',              # ✅ 3% TP trigger
    'test_daily_loss_limit',         # ✅ $500 limit
    'test_volatility_check',         # ✅ StdDev check
    'test_correlation_check',        # ✅ QQQ-NDX proxy
]
# Result: 6/6 passed (100%)
```

### 成就系統測試 (`achievement_test.py`)

```python
ACHIEVEMENT_TESTS = [
    'test_daily_tasks',              # ✅ 5 tasks
    'test_badge_award',              # ✅ Badge system
    'test_trade_logging',            # ✅ P&L tracking
    'test_streak_tracking',          # ✅ Consecutive days
]
# Result: All passed
```

---

## 🔐 安全框架

### 檢查清單 (`security_check.py`)

```python
SECURITY_CHECKS = [
    'check_env_files',               # ✅ .env files
    'check_gitignore',               # ✅ Sensitive data ignored
    'check_risk_limits',             # ✅ Limits configured
    'check_api_keys',                # ✅ No plaintext keys
    'check_database_security',       # ✅ DB config
    'check_backup_strategy',         # ✅ Backup plan
]
```

### 風險控制矩陣

| 風險類型 | 控制措施 | 自動化 | 狀態 |
|----------|----------|--------|------|
| **Data Loss** | Multi-source backup | ✅ | Active |
| **Over-trading** | Position limits | ✅ | Active |
| **Large Loss** | Daily loss limit | ✅ | Active |
| **System Error** | Error pause | ✅ | Active |
| **API Exposure** | .gitignore + env | ✅ | Active |

---

## 📝 任務管理框架

### Todo Enforcer 集成

```python
# Task Manager Configuration
TASK_MANAGER = {
    'total_tasks': 13,
    'phases': {
        'phase_1': {'name': 'Data Flow Fix', 'status': 'COMPLETED', 'tasks': 4},
        'phase_2': {'name': 'Task Management', 'status': 'COMPLETED', 'tasks': 3},
        'phase_3': {'name': 'E2E Testing', 'status': 'COMPLETED', 'tasks': 3},
        'phase_4': {'name': 'Production Ready', 'status': 'COMPLETED', 'tasks': 3},
    },
    'progress': '100%',
    'file': 'tasks/six_loop_tasks.json'
}
```

### AMS 整合

```python
# Alfred Memory System Integration
AMS_CONFIG = {
    'memory_storage': 'alfred_memory_system/data/alfred_memory.db',
    'context_monitor': True,
    'summarizer': True,
    'weekly_review': 'Monday 09:00',
    'task_logging': 'logs/tasks/'
}
```

---

## 🚀 部署流程

### 部署前檢查 (`deploy_prep.py`)

```bash
# 1. Prerequisites
✅ Python >= 3.8
✅ All packages installed
✅ File structure complete
✅ Database accessible
✅ External services running
✅ Security checks passed

# 2. Start Services
$ python futu-adapter/futu_opend_feed_v2.py
$ python cron/six_loop_monitor.py

# 3. Verify
$ python check_data.py
$ python e2e_test.py
```

### 啟動順序

```
1. Futu OpenD (manual)
   └── Verify: Test-NetConnection 127.0.0.1 -Port 11111

2. Data Feed (auto/manual)
   └── python futu-adapter/futu_opend_feed_v2.py
   └── Verify: python check_data.py

3. Node-RED Flows (service)
   └── Verify: Invoke-RestMethod http://localhost:1880/flows

4. Monitoring (auto)
   └── python cron/six_loop_monitor.py

5. Decision Engine (on-demand)
   └── python decision-engine/main.py
```

---

## 📂 文件結構

```
projects/six-loop-system/
├── Core Documentation
│   ├── SYSTEM_ARCHITECTURE.md      # System design
│   ├── SIX_LOOP_IMPROVEMENT_PLAN.md # 4-phase roadmap
│   ├── OPERATIONS_MANUAL.md         # User guide
│   └── SYSTEM_TEST_REPORT.md        # Test results
│
├── Configuration
│   ├── config/
│   │   └── symbols.yaml             # Symbol mappings
│   └── .gitignore                   # Security
│
├── Data Layer
│   ├── futu-adapter/
│   │   ├── futu_opend_feed_v2.py   # Main feed
│   │   ├── backup_data_feed.py     # Backup sources
│   │   └── test_*.py               # Test scripts
│   └── sql/                         # DB schemas
│
├── Automation
│   ├── cron/
│   │   ├── six_loop_monitor.py     # Health monitor
│   │   ├── daily-sync.ps1          # Daily tasks
│   │   └── six-loop-monitor.yaml   # Cron config
│   └── task_manager.py             # Todo Enforcer
│
├── Testing
│   ├── e2e_test.py                 # End-to-end
│   ├── risk_management_test.py     # Risk tests
│   ├── achievement_test.py         # Achievement
│   ├── security_check.py           # Security
│   └── deploy_prep.py              # Deployment
│
├── Monitoring
│   ├── alert_manager.py            # Alerts
│   ├── task_logger.py              # Task logging
│   ├── check_data.py               # Data check
│   └── ams_integration.py          # AMS sync
│
└── Logs & Data
    ├── logs/                        # All logs
    ├── tasks/                       # Task states
    └── data/                        # Runtime data
```

---

## 🎯 關鍵指標 (KPIs)

### 系統健康度

| 指標 | 目標 | 當前 | 狀態 |
|------|------|------|------|
| **Data Flow Uptime** | >99% | 100% | ✅ |
| **Decision Latency** | <5s | ~2s | ✅ |
| **Risk Check Pass** | 100% | 100% | ✅ |
| **Test Coverage** | >80% | 100% | ✅ |

### 數據質量

| 指標 | 目標 | 當前 | 狀態 |
|------|------|------|------|
| **Daily Records** | >1000 | 1677 | ✅ |
| **Data Freshness** | <5min | ~0.5min | ✅ |
| **Backup Sources** | >=2 | 2 | ✅ |
| **QQQ-NDX Correlation** | >0.99 | ~0.995 | ✅ |

---

## 🔧 維護任務

### 每日 (Daily)
- [ ] Run `six_loop_monitor.py`
- [ ] Check `check_data.py` output
- [ ] Verify Futu OpenD connection
- [ ] Review alert logs

### 每週 (Weekly)
- [ ] Run full test suite
- [ ] Review task progress
- [ ] Check disk space
- [ ] Backup database

### 每月 (Monthly)
- [ ] Security audit
- [ ] Dependency updates
- [ ] Performance review
- [ ] Documentation update

---

## 📞 升級路徑

### Phase 5+ (Future)
- [ ] ML-based signal enhancement
- [ ] Multi-asset support
- [ ] Real-time dashboard
- [ ] Mobile notifications
- [ ] Advanced risk models

---

## 🔗 相關資源

- **Status**: `project-states/Six-Loop-System-STATUS.md`
- **User Framework**: `project-states/SIX_LOOP_FRAMEWORK_USER.md`
- **Alfred Framework**: `project-states/SIX_LOOP_FRAMEWORK_ALFRED.md` (this file)
- **Operations**: `projects/six-loop-system/OPERATIONS_MANUAL.md`
- **Memory**: `memory/2026-04-20-six-loop-summary.md`

---

*Framework Version: v1.0*  
*Last Updated: 2026-04-22 09:32*  
*System Status: ✅ All Phases Complete - Production Ready*
