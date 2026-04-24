# ClawHub Plugins 推薦清單 - 適合 ClawTeam

> **來源**: https://clawhub.ai/plugins
> **日期**: 2026-04-05
> **用途**: ClawTeam 多 Agent 交易系統

---

## 🎯 必裝 Plugins（高優先級）

### 1. 多 Agent & 協作

| Plugin 名稱 | 類型 | 用途 | 安裝 |
|-----------|------|------|------|
| **Nexus Hub Channel** | Code | Nexus Hub 2.0 channel plugin - A2A dispatch, room summary, Control Plane | `npx clawhub@latest install nexus-channel` |
| **KongBrain** | Code | Graph-backed persistent memory - SurrealDB + vector embeddings | `npx clawhub@latest install kongbrain` |
| **DeepLake** | Code | Cloud-backed persistent shared memory for AI agents | `npx clawhub@latest install deeplake` |
| **Hivemind** | Code | Cloud-backed persistent shared memory | `npx clawhub@latest install hivemind` |

### 2. 記憶 & 知識管理

| Plugin 名稱 | 類型 | 用途 | 安裝 |
|-----------|------|------|------|
| **Finch Smart Memory** | Code | LLM-powered extraction, hybrid ANN search, tier lifecycle, WAL, Mem0 | `npx clawhub@latest install @onenomad/finch-smart-memory` |
| **Smart Memory** | Code | Smart memory plugin - LLM extraction, ANN search, procedural rules | `npx clawhub@latest install @mattstvartak/finch-smart-memory` |
| **Memrok** | Code | Memory with judgment - persistent, structured, intelligent memory layer | `npx clawhub@latest install memrok` |
| **LLM Knowledge Bases** | Code | Turn raw research into living Markdown knowledge base (Obsidian) | `npx clawhub@latest install llm-knowledge-bases-plugin` |

### 3. 金融 & 交易

| Plugin 名稱 | 類型 | 用途 | 安裝 |
|-----------|------|------|------|
| **AIGroup Financial Services** | Bundle | Financial modeling, analysis, and deliverables suite | `npx clawhub@latest install aigroup-financial-services-openclaw` |
| **AIGroup Lead Discovery** | Bundle | Lead-discovery and company-intelligence suite | `npx clawhub@latest install aigroup-lead-discovery-openclaw` |
| **Financialclaw** | Code | Personal finance plugin - expenses, income, recurring payments, receipt OCR | `npx clawhub@latest install financialclaw` |
| **ArbiLink** | Code | Arbitrum Agent Plugin - read balances, check gas, query tokens, smart contracts | `npx clawhub@latest install arbilink` |

### 4. 通訊 & Channel

| Plugin 名稱 | 類型 | 用途 | 安裝 |
|-----------|------|------|------|
| **Google Chat Pub/Sub Listener** | Code | Listen to Google Chat spaces via Workspace Events + Pub/Sub | `npx clawhub@latest install @teyou/openclaw-googlechatpubsub` |
| **Rocketchat Openclaw** | Code | Open-source Rocket.Chat channel plugin | `npx clawhub@latest install rocketchat-openclaw` |
| **Zulip Bridge** | Code | OpenClaw Zulip channel plugin | `npx clawhub@latest install @openclaw/zulip` |
| **Claw Voice Call** | Code | Phone call plugin with managed or self-hosted voice backends | `npx clawhub@latest install claw-voice-call` |

### 5. Google Workspace

| Plugin 名稱 | 類型 | 用途 | 安裝 |
|-----------|------|------|------|
| **OpenClaw Google Workspace** | Code | All-in-one Google Workspace - Gmail, Calendar, Drive, shared OAuth | `npx clawhub@latest install openclaw-google-workspace` |

### 6. 安全 & 訪問控制

| Plugin 名稱 | 類型 | 用途 | 安裝 |
|-----------|------|------|------|
| **Fine Grained Tool Access Control** | Code | Fine-grained access control for OpenClaw tool calls | `npx clawhub@latest install fg-tool-access-control` |

### 7. 區塊鏈

| Plugin 名稱 | 類型 | 用途 | 安裝 |
|-----------|------|------|------|
| **ClawNetwork Node** | Code | Run a ClawNetwork blockchain node inside OpenClaw | `npx clawhub@latest install @clawlabz/clawnetwork` |

### 8. 其他實用工具

| Plugin 名稱 | 類型 | 用途 | 安裝 |
|-----------|------|------|------|
| **Openclaw Hedra** | Code | Hedra AI video and image generation - talking avatars, video generation | `npx clawhub@latest install @onenomad/openclaw-hedra` |
| **OpenClaw ShortDrama** | Code | Shortdrama workflow as native tool | `npx clawhub@latest install openclaw-shortdrama-plugin` |
| **S2 汉字空间调色盘** | Code | S2 Spatial Palette Engine - Hanzi rendering from telemetry | `npx clawhub@latest install s2-hanzi-ambient-renderer` |
| **Zentao to Code** | Bundle | 禅道代码定位 - 管理禅道项目到 Git 仓库和本地代码目录的映射 | `npx clawhub@latest install zentao-to-code` |

---

## 📋 按用途推薦

### 🧠 記憶系統（ClawTeam 共享記憶）
```bash
# 核心記憶 plugins
npx clawhub@latest install kongbrain
npx clawhub@latest install deeplake
npx clawhub@latest install @onenomad/finch-smart-memory
npx clawhub@latest install memrok
```

### 💰 金融交易（TradingBot）
```bash
# 金融交易 plugins
npx clawhub@latest install aigroup-financial-services-openclaw
npx clawhub@latest install financialclaw
npx clawhub@latest install arbilink
```

### 🤝 多 Agent 協作
```bash
# 多 Agent plugins
npx clawhub@latest install nexus-channel
npx clawhub@latest install hivemind
npx clawhub@latest install @openclaw/zulip
```

### 📊 知識管理
```bash
# 知識庫 plugins
npx clawhub@latest install llm-knowledge-bases-plugin
npx clawhub@latest install @mattstvartak/finch-smart-memory
```

### 🔐 安全控制
```bash
# 安全 plugins
npx clawhub@latest install fg-tool-access-control
```

---

## 🚀 快速安裝核心 Plugins

```bash
# 一鍵安裝 ClawTeam 核心 plugins
npx clawhub@latest install kongbrain deeplake nexus-channel aigroup-financial-services-openclaw financialclaw memrok
```

---

## 💡 使用建議

### 第一階段：基礎設施
1. **KongBrain** 或 **DeepLake** - 建立共享記憶系統
2. **Nexus Hub Channel** - 多 Agent 協作基礎設施

### 第二階段：金融功能
3. **AIGroup Financial Services** - 金融建模分析
4. **Financialclaw** - 個人財務管理

### 第三階段：知識管理
5. **LLM Knowledge Bases** - 建立 Obsidian 知識庫
6. **Memrok** - 智能記憶層

### 第四階段：安全與擴展
7. **Fine Grained Tool Access Control** - 工具訪問控制
8. **其他專用 plugins** - 根據需求選擇

---

## 🔗 相關連結

- **Plugins 頁面**: https://clawhub.ai/plugins
- **Skills 頁面**: https://clawhub.ai/skills
- **安裝指令**: `npx clawhub@latest install <plugin-name>`

---

*最後更新: 2026-04-05*
