# Claw Code 專案研究筆記

> **研究日期**: 2026-04-15  
> **專案來源**: GitHub - ultraworkers/claw-code  
> **研究目的**: 學習 AI Coding Agent 框架設計

---

## 專案概覽

**Claw Code** 是一個開源的 AI Coding Agent 框架，由 ultraworkers 團隊開發，是 Claude Code 的 clean-room 重寫版本。

| 屬性 | 詳情 |
|------|------|
| **GitHub** | https://github.com/ultraworkers/claw-code |
| **語言** | Rust (72.9%) + Python (27.1%) |
| **Stars** | 超過 100K（史上最快達到 100K stars 的 repo） |
| **核心** | Rust 實現的 CLI agent harness |
| **Discord** | https://discord.gg/5TUQKqFWd |

---

## 核心哲學 (PHILOSOPHY.md)

> "If you only look at the generated files in this repository, you are looking at the wrong layer."

### 關鍵理念

1. **人類設定方向，Claws 執行勞動**
   - 人類提供清晰指令
   - 多個 coding agents 並行協調
   - 通知路由移出 agent context window
   - 規劃、執行、審查、重試循環自動化

2. **真正的人機介面不是終端機，而是 Discord**
   - 人可以從手機輸入一句話
   - 離開、睡覺、做其他事情
   - Claws 讀取指令、分解任務、分配角色、編寫代碼、運行測試、爭論失敗、恢復、推送

3. **瓶頸不再是打字速度**
   - 當 agent 系統可以在幾小時內重建代碼庫時，稀缺資源變成：
     - 架構清晰度
     - 任務分解
     - 判斷力
     - 品味
     - 對值得構建事物的信念
     - 知道哪些部分可以並行化，哪些必須保持約束

4. **人類的工作不是比機器打字快**
   - 而是決定什麼值得存在

---

## 生態系統工具鏈

| 工具 | 用途 | GitHub |
|------|------|--------|
| **oh-my-codex** | 工作流層，將短指令轉為結構化執行 | Yeachan-Heo/oh-my-codex |
| **clawhip** | 事件和通知路由器 | Yeachan-Heo/clawhip |
| **oh-my-openagent** | 多 agent 協調 | code-yeongyu/oh-my-openagent |
| **oh-my-claudecode** | Claude Code 相關 | Yeachan-Heo/oh-my-claudecode |

### 各組件職責

- **oh-my-codex**: 規劃關鍵詞、執行模式、持久驗證循環、並行多 agent 工作流
- **clawhip**: 監控 git commits、tmux sessions、GitHub issues/PRs、agent 生命周期事件、頻道交付
- **oh-my-openagent**: 規劃、交接、分歧解決、驗證循環

---

## 技術架構

### Rust Workspace 結構

```
rust/
├── Cargo.toml              # Workspace root
└── crates/
    ├── api/                # Provider clients + streaming + request preflight
    ├── commands/           # Shared slash-command registry + help rendering
    ├── compat-harness/     # TS manifest extraction harness
    ├── mock-anthropic-service/  # Deterministic local Anthropic-compatible mock
    ├── plugins/            # Plugin metadata, manager, install/enable/disable
    ├── runtime/            # Session, config, permissions, MCP, prompts, auth
    ├── rusty-claude-cli/   # Main CLI binary (`claw`)
    ├── telemetry/          # Session tracing and usage telemetry
    └── tools/              # Built-in tools, skill resolution, tool search
```

### Crate 詳細職責

| Crate | 職責 |
|-------|------|
| **api** | provider clients, SSE streaming, request/response types, auth (API key + bearer-token) |
| **commands** | slash command 定義、解析、help text 生成 |
| **compat-harness** | 從上游 TS source 提取 tool/prompt manifests |
| **mock-anthropic-service** | 確定性的 /v1/messages mock，用於 CLI parity tests |
| **plugins** | plugin metadata, install/enable/disable/update flows |
| **runtime** | ConversationRuntime, config loading, session persistence, permission policy, MCP client |
| **rusty-claude-cli** | REPL, one-shot prompt, direct CLI subcommands, streaming display |
| **telemetry** | session trace events and telemetry payloads |
| **tools** | tool specs + execution: Bash, ReadFile, WriteFile, EditFile, GlobSearch, GrepSearch, WebSearch, WebFetch, Agent, TodoWrite, NotebookEdit, Skill, ToolSearch |

### 統計

- ~20K lines of Rust
- 9 crates in workspace
- Binary name: `claw`
- Default model: claude-opus-4-6
- Default permissions: danger-full-access

---

## 核心功能

### 已實現功能 (✅)

| 功能 | 狀態 |
|------|------|
| Anthropic / OpenAI-compatible provider flows + streaming | ✅ |
| Direct bearer-token auth via ANTHROPIC_AUTH_TOKEN | ✅ |
| Interactive REPL (rustyline) | ✅ |
| Tool system (bash, read, write, edit, grep, glob) | ✅ |
| Web tools (search, fetch) | ✅ |
| Sub-agent / agent surfaces | ✅ |
| Todo tracking | ✅ |
| Notebook editing | ✅ |
| CLAUDE.md / project memory | ✅ |
| Config file hierarchy (.claw.json + merged config sections) | ✅ |
| Permission system | ✅ |
| MCP server lifecycle + inspection | ✅ |
| Session persistence + resume | ✅ |
| Cost / usage / stats surfaces | ✅ |
| Git integration | ✅ |
| Markdown terminal rendering (ANSI) | ✅ |
| Model aliases (opus/sonnet/haiku) | ✅ |
| Direct CLI subcommands | ✅ |
| Slash commands | ✅ |
| Hooks | ✅ |
| Plugin management surfaces | ✅ |
| Skills inventory / install surfaces | ✅ |
| Machine-readable JSON output | ✅ |

### CLI 命令結構

```bash
claw [OPTIONS] [COMMAND]

Flags:
  --model MODEL
  --output-format text|json
  --permission-mode MODE
  --dangerously-skip-permissions
  --allowedTools TOOLS
  --resume [SESSION.jsonl|session-id|latest]
  --version, -V

Top-level commands:
  prompt <text>
  help
  version
  status
  sandbox
  dump-manifests
  bootstrap-plan
  agents
  mcp
  skills
  system-prompt
  init
```

### REPL Slash Commands

**Session / visibility:**
/help, /status, /sandbox, /cost, /resume, /session, /version, /usage, /stats

**Workspace / git:**
/compact, /clear, /config, /memory, /init, /diff, /commit, /pr, /issue, /export, /hooks, /files, /release-notes

**Discovery / debugging:**
/mcp, /agents, /skills, /doctor, /tasks, /context, /desktop

**Automation / analysis:**
/review, /advisor, /insights, /security-review, /subagent, /team, /telemetry, /providers, /cron

**Plugin management:**
/plugin (aliases: /plugins, /marketplace)

---

## 認證與 Provider 支援

### 支援的 Provider

| Provider | Protocol | Auth env var(s) | Base URL env var |
|----------|----------|-----------------|------------------|
| Anthropic (direct) | Anthropic Messages API | ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN | ANTHROPIC_BASE_URL |
| xAI | OpenAI-compatible | XAI_API_KEY | XAI_BASE_URL |
| OpenAI-compatible | OpenAI Chat Completions | OPENAI_API_KEY | OPENAI_BASE_URL |
| DashScope (Alibaba) | OpenAI-compatible | DASHSCOPE_API_KEY | DASHSCOPE_BASE_URL |

### Model Aliases

| Alias | Resolves To | Provider | Max output tokens | Context window |
|-------|-------------|----------|-------------------|----------------|
| opus | claude-opus-4-6 | Anthropic | 32,000 | 200,000 |
| sonnet | claude-sonnet-4-6 | Anthropic | 64,000 | 200,000 |
| haiku | claude-haiku-4-5-20251213 | Anthropic | 64,000 | 200,000 |
| grok / grok-3 | grok-3 | xAI | 64,000 | 131,072 |
| grok-mini / grok-3-mini | grok-3-mini | xAI | 64,000 | 131,072 |

---

## 安裝與使用

### 構建步驟

```bash
# 1. Clone and build
git clone https://github.com/ultraworkers/claw-code
cd claw-code/rust
cargo build --workspace

# 2. Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Verify with doctor
./target/debug/claw doctor

# 4. Run a prompt
./target/debug/claw prompt "say hello"
```

### Windows PowerShell 注意事項

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
.\target\debug\claw.exe prompt "say hello"
```

### 重要警告

⚠️ `cargo install claw-code` 會安裝錯誤的東西！crates.io 上的 claw-code crate 是一個已棄用的 stub。

正確安裝上游 binary：
```bash
cargo install agent-code  # 安裝 'agent.exe' (Windows) / 'agent' (Unix)
```

---

## 學習重點與啟發

### 1. 架構設計

- **Clean-room rewrite**: 不複製原始碼，只重現架構
- **Rust + Python 混合**: Rust 負責高性能運行時，Python 負責 agent orchestration
- **Workspace 組織**: 9 個 crates 清晰分離職責

### 2. 多 Agent 協調

- 使用 Discord 作為主要人機介面
- 通知路由移出 agent context window
- 規劃、執行、審查、重試循環自動化

### 3. 工具系統

- 內建工具: Bash, ReadFile, WriteFile, EditFile, GlobSearch, GrepSearch
- Web 工具: WebSearch, WebFetch
- Agent 工具: Agent, TodoWrite, NotebookEdit, Skill, ToolSearch

### 4. 配置系統

- 層次化配置: ~/.claw/settings.json, .claw/settings.json, .claw/settings.local.json
- 支援自定義 model aliases
- 多 provider 支援

### 5. 與 OpenClaw 的關聯

Claw Code 展示了一個完整的 AI Coding Agent 框架應該具備的要素：
- 清晰的工具系統
- 多 agent 協調能力
- 靈活的配置管理
- 豐富的 slash commands
- Plugin 和 Skill 系統

這些設計理念可以參考應用於 OpenClaw 的技能開發和系統優化。

---

## 相關資源

- **主倉庫**: https://github.com/ultraworkers/claw-code
- **官方網站**: https://claw-code.codes/
- **Discord**: https://discord.gg/5TUQKqFWd
- **Twitter/X**: https://x.com/realsigridjin/status/2039472968624185713

---

## 參考文件

| 文件 | 用途 |
|------|------|
| USAGE.md | 構建、認證、CLI、session、parity-harness 工作流 |
| rust/README.md | crate 級別詳情 |
| PARITY.md | Rust-port parity 狀態和遷移筆記 |
| ROADMAP.md | 活躍路線圖和清理待辦 |
| PHILOSOPHY.md | 項目意圖和系統設計框架 |
| docs/container.md | container-first 工作流 |

---

*記錄時間: 2026-04-15 10:45 AM*  
*研究員: 呀鬼 (Alfred)*
