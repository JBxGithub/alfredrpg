# ClawHub Skills 推薦清單 - 適合 ClawTeam

> **來源**: https://clawhub.ai/
> **日期**: 2026-04-05
> **用途**: ClawTeam 多 Agent 交易系統

---

## 🎯 必裝 Skills（高優先級）

### 1. Multi-Agent 相關

| Skill 名稱 | 分數 | 用途 | 安裝指令 |
|-----------|------|------|----------|
| **multi-agent-coordinator** | 3.586 | 多 Agent 協調器 - 適合 Alfred 指揮 | `npx clawhub@latest install multi-agent-coordinator` |
| **multi-agent-roles** | 3.593 | 多 Agent 角色管理 - 定義 Robin/BatGirl/Catwoman 角色 | `npx clawhub@latest install multi-agent-roles` |
| **friday-multi-agent-orchestrator** | 3.444 | 多 Agent 編排器 - 進階協調功能 | `npx clawhub@latest install friday-multi-agent-orchestrator` |
| **multi-agent-chat** | 3.467 | 多 Agent 對話協議 - Agent 間通訊 | `npx clawhub@latest install multi-agent-chat` |

### 2. Trading 相關

| Skill 名稱 | 分數 | 用途 | 安裝指令 |
|-----------|------|------|----------|
| **auto-trading-strategy** | 3.480 | 自動交易策略 - BatGirl 的核心 | `npx clawhub@latest install auto-trading-strategy` |
| **trading-devbox** | 3.547 | 交易開發環境 - 開發測試用 | `npx clawhub@latest install trading-devbox` |
| **shadow-trading-dashboard** | 3.357 | 交易儀表板 - Catwoman 的監控 | `npx clawhub@latest install shadow-trading-dashboard` |
| **autonomous-trading-system** | 3.290 | 自主交易系統 - 完整方案 | `npx clawhub@latest install autonomous-trading-system` |
| **trading-automaton** | 3.351 | 交易自動化 - 訂單執行 | `npx clawhub@latest install trading-automaton` |

### 3. Webhook & 通知

| Skill 名稱 | 分數 | 用途 | 安裝指令 |
|-----------|------|------|----------|
| **webhook-send** | 3.492 | Webhook 發送 - Agent 間通訊 | `npx clawhub@latest install webhook-send` |
| **webhook-integration** | 3.472 | Webhook 整合 - 系統整合 | `npx clawhub@latest install webhook-integration` |
| **pushover-notify** | 3.501 | Pushover 通知 - 重要警報 | `npx clawhub@latest install pushover-notify` |
| **universal-notify** | 3.359 | 通用通知系統 - 多種通知渠道 | `npx clawhub@latest install universal-notify` |

### 4. 數據分析

| Skill 名稱 | 分數 | 用途 | 安裝指令 |
|-----------|------|------|----------|
| **data-analyst-pro** | 3.534 | 專業數據分析 - Robin 的核心 | `npx clawhub@latest install data-analyst-pro` |
| **data-anomaly-detector** | 3.473 | 數據異常檢測 - 風險監控 | `npx clawhub@latest install data-anomaly-detector` |
| **data-model-designer** | 3.499 | 數據模型設計 - 策略建模 | `npx clawhub@latest install data-model-designer` |

### 5. Dashboard & 監控

| Skill 名稱 | 分數 | 用途 | 安裝指令 |
|-----------|------|------|----------|
| **openclaw-dashboard** | 3.554 | OpenClaw 儀表板 - 系統監控 | `npx clawhub@latest install openclaw-dashboard` |
| **subagent-dashboard** | 3.383 | SubAgent 儀表板 - Agent 監控 | `npx clawhub@latest install subagent-dashboard` |
| **aic-dashboard** | 3.470 | AI Commander Dashboard - 指揮中心 | `npx clawhub@latest install aic-dashboard` |
| **monitoring** | 3.164 | 監控系統 - 系統健康 | `npx clawhub@latest install monitoring` |

---

## 📋 按角色推薦

### 🧐 Alfred (Orchestrator)
```bash
npx clawhub@latest install multi-agent-coordinator
npx clawhub@latest install friday-multi-agent-orchestrator
npx clawhub@latest install openclaw-dashboard
npx clawhub@latest install aic-dashboard
npx clawhub@latest install subagent-dashboard
```

### 📊 Robin (DataForge)
```bash
npx clawhub@latest install data-analyst-pro
npx clawhub@latest install data-anomaly-detector
npx clawhub@latest install data-model-designer
```

### 📈 BatGirl (SignalForge)
```bash
npx clawhub@latest install auto-trading-strategy
npx clawhub@latest install trading-devbox
npx clawhub@latest install data-anomaly-detector
```

### ⚡ Catwoman (TradeForge)
```bash
npx clawhub@latest install shadow-trading-dashboard
npx clawhub@latest install trading-automaton
npx clawhub@latest install autonomous-trading-system
npx clawhub@latest install pushover-notify
```

---

## 🚀 快速安裝所有推薦 Skills

```bash
# 一鍵安裝所有核心 skills
npx clawhub@latest install multi-agent-coordinator multi-agent-roles friday-multi-agent-orchestrator auto-trading-strategy data-analyst-pro webhook-send openclaw-dashboard shadow-trading-dashboard pushover-notify
```

---

## 💡 使用建議

1. **先安裝核心技能**: multi-agent-coordinator, auto-trading-strategy, data-analyst-pro
2. **再安裝輔助技能**: webhook, dashboard, notify
3. **最後安裝專用技能**: 根據各 Agent 職責選擇性安裝

---

*最後更新: 2026-04-05*
