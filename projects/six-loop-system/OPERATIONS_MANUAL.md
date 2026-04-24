# 六循環系統操作手冊

> **版本**: v1.2  
> **更新日期**: 2026-04-23 23:10  
> **適用對象**: 靚仔 (Burt)  
> **系統狀態**: ✅ V9.4 最終版 - 回撤優化完成，推薦部署

---

## 📋 目錄

1. [系統概述](#系統概述)
2. [系統架構](#系統架構)
3. [快速啟動](#快速啟動)
4. [日常操作](#日常操作)
5. [監控與告警](#監控與告警)
6. [故障排除](#故障排除)
7. [安全注意事項](#安全注意事項)
8. [附錄](#附錄)

---

## 系統概述

六循環系統是一個自動化交易引擎，實現「感知 → 處理 → 決策 → 執行 → 成就 → 學習 → 循環」的閉環交易流程。

### 核心特點
- **分析標的**: NQ 100 (使用 QQQ 作為 Futu OpenD 代理)
- **交易標的**: TQQQ (3x 槓桿 QQQ)
- **數據源**: Futu OpenD (主要) + investing.com/Yahoo (備份)
- **決策引擎**: Absolute (60%) + Reference (40%) 評分系統
- **風險管理**: 多層次風險控制 (止損/止盈/倉位/日虧損限制)

---

## 系統架構

```
┌─────────────────────────────────────────────────────────┐
│                    六系統循環架構                          │
│              感知 → 處理 → 決策 → 執行 → 成就 → 學習 → 循環  │
└─────────────────────────────────────────────────────────┘

    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   系統 1    │     │   系統 2    │     │   系統 3    │
    │   感知層   │────►│  數據處理   │────►│   決策層   │
    │  Node-RED  │     │  Node-RED  │     │   Python   │
    │ +PostgreSQL│     │ +PostgreSQL│     │            │
    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │•Futu OpenD  │     │•Absolute   │     │•信號生成    │
    │•investing   │     │ 計算(權重)  │     │•風險檢查    │
    │•tradingview │     │•Reference  │     │•錯誤保護    │
    │•jin10.com   │     │ 計算(權重)  │     │•決策輸出    │
    │•DeFiLlama   │     │•綜合評分   │     │             │
    │•ACLED/USGS  │     │ (0-100)    │     │             │
    └─────────────┘     └─────────────┘     └─────────────┘
                                                  │
                                                  ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   系統 6    │     │   系統 5    │     │   系統 4    │
    │   學習層   │◄────│  成就激勵   │◄────│   執行層   │
    │Self-     │     │ Alfredrpg  │     │FutuTrading │
    │Improving │     │ (每日記錄)  │     │    Bot     │
    │(每週優化) │     │             │     │            │
    └─────────────┘     └─────────────┘     └─────────────┘
```

### 核心組件
| 組件 | 功能 | 狀態檢查 | 命令 |
|------|------|----------|------|
| Futu OpenD | 數據源 (QQQ) | 端口 11111 | `Test-NetConnection -ComputerName 127.0.0.1 -Port 11111` |
| Node-RED | Flow 自動化 | http://localhost:1880 | `Invoke-RestMethod -Uri http://localhost:1880/flows` |
| PostgreSQL | 數據存儲 | 端口 5432 | `python check_data.py` |
| Python 決策引擎 | 信號生成 | 手動運行 | `python decision-engine\main.py` |

---

## 快速啟動

### 每日啟動檢查清單

```powershell
# 1. 進入專案目錄
cd C:\Users\BurtClaw\openclaw_workspace\projects\six-loop-system

# 2. 運行部署準備檢查
python deploy_prep.py

# 3. 檢查系統狀態
python cron\six_loop_monitor.py

# 4. 檢查數據流
python check_data.py

# 5. 如需要，啟動 Futu 數據饋送器
python futu-adapter\futu_opend_feed_v2.py
```

---

## 日常操作

### 1. 系統啟動流程

#### Step 1: 啟動 Futu OpenD
1. 打開富途牛牛桌面版
2. 進入「系統設置」→「OpenD」
3. 點擊「啟動 OpenD」
4. 確認端口 11111 已開啟

```powershell
# 驗證 OpenD 連接
Test-NetConnection -ComputerName 127.0.0.1 -Port 11111
```

#### Step 2: 檢查系統健康
```powershell
# 運行系統監控
python cron\six_loop_monitor.py

# 預期輸出:
# ✅ 數據庫: 最新數據 X 秒前
# ✅ Node-RED: 4 個 Flows 運行中
# ✅ Futu OpenD: 端口 11111 開啟
```

#### Step 3: 啟動數據饋送器 (如未運行)
```powershell
# 檢查是否已有饋送器運行
Get-Process python | Where-Object {$_.CommandLine -like "*futu_opend_feed*"}

# 如無運行，啟動饋送器
python futu-adapter\futu_opend_feed_v2.py
```

### 2. 數據流監控

```powershell
# 檢查數據寫入狀態
python check_data.py

# 預期輸出:
# 今日 Futu 數據: 1,600+ 條
# 最新: 14:32:15 (0.5 分鐘前)
# 最早: 09:30:00
#
# 今日數據來源統計:
#   futu_opend: 1,677 條
#   simulated: 1,772 條
#   yahoo_finance: 92 條
```

### 3. 任務管理

```powershell
# 初始化所有任務 (首次使用)
python task_manager.py init

# 查看任務進度報告
python task_manager.py report

# 預期輸出:
# ============================================================
# 六循環系統任務進度報告
# ============================================================
# 總任務數: 13
# 已完成: 4 (30.8%)
# 進行中: 0
# 待辦: 9
# ============================================================
```

### 4. 生成交易決策

```powershell
# 運行決策引擎
python decision-engine\main.py

# 查看決策歷史 (通過數據庫)
# 數據庫: trading_db.decisions 表
```

### 5. 成就系統

```powershell
# 查看成就狀態
python achievement_test.py

# 預期輸出:
# 📊 統計:
#    總交易數: 3
#    盈利交易: 2
#    虧損交易: 1
#    勝率: 66.7%
#    總盈虧: $275.50
#
# 🏆 徽章:
#    • 每日大師
```

---

## 監控與告警

### 自動監控

系統已設置自動監控，每 5 分鐘檢查：
- ✅ Futu OpenD 連接 (端口 11111)
- ✅ 數據庫數據流 (最新數據時間)
- ✅ Node-RED Flows (4 個 Flows 運行狀態)

### 手動監控命令

```powershell
# 系統整體監控
python cron\six_loop_monitor.py

# 數據流檢查
python check_data.py

# 部署準備檢查
python deploy_prep.py

# 安全檢查
python security_check.py
```

### 告警級別與處理

| 級別 | 說明 | 處理方式 | 通知方式 |
|------|------|----------|----------|
| ℹ️ Info | 信息通知 | 記錄即可 | 日誌 |
| ⚠️ Warning | 警告 | 檢查系統 | 日誌 + 可選通知 |
| ❌ Error | 錯誤 | 立即處理 | WhatsApp |
| 🚨 Critical | 嚴重 | 停止交易 | WhatsApp + 緊急處理 |

### 告警歷史查看

```powershell
# 查看告警日誌
cat logs\alerts.json | ConvertFrom-Json | Select-Object -ExpandProperty alerts | Select-Object -Last 10
```

---

## 故障排除

### 常見問題速查表

| 問題 | 檢查命令 | 解決方案 |
|------|----------|----------|
| Futu 無法連接 | `Test-NetConnection 127.0.0.1 -Port 11111` | 啟動富途牛牛 OpenD |
| 無數據寫入 | `python check_data.py` | 重啟 `futu_opend_feed_v2.py` |
| Node-RED 異常 | `Invoke-RestMethod http://localhost:1880/flows` | 重啟 Node-RED 服務 |
| 數據庫連接失敗 | `python deploy_prep.py` | 檢查 PostgreSQL 服務 |

### 問題 1: Futu OpenD 無法連接

**症狀**: 
- 端口 11111 無法連接
- `six_loop_monitor.py` 顯示 ❌ Futu OpenD

**診斷**:
```powershell
# 測試連接
Test-NetConnection -ComputerName 127.0.0.1 -Port 11111

# 檢查進程
Get-Process | Where-Object {$_.ProcessName -like "*futu*"}
```

**解決步驟**:
1. 打開富途牛牛桌面版
2. 進入「系統設置」→「OpenD」
3. 點擊「啟動 OpenD」
4. 等待 10 秒後再次測試連接

### 問題 2: 數據未寫入數據庫

**症狀**: 
- `check_data.py` 顯示 "今日 Futu 數據: 0 條"
- 或最新數據時間滯後 > 10 分鐘

**診斷**:
```powershell
# 檢查饋送器是否運行
Get-Process python | Where-Object {$_.CommandLine -like "*futu_opend_feed*"}

# 查看錯誤日誌
cat logs\futu_*.log -Tail 20
```

**解決步驟**:
1. 檢查 Futu OpenD 是否運行 (見問題 1)
2. 重啟 Futu 饋送器:
   ```powershell
   # 停止現有饋送器
   Get-Process python | Where-Object {$_.CommandLine -like "*futu_opend_feed*"} | Stop-Process
   
   # 重新啟動
   python futu-adapter\futu_opend_feed_v2.py
   ```
3. 等待 30 秒後再次檢查數據

### 問題 3: Node-RED Flow 停止

**症狀**: 
- 無法訪問 http://localhost:1880
- `six_loop_monitor.py` 顯示 ❌ Node-RED

**診斷**:
```powershell
# 檢查 Node-RED 服務
Get-Service | Where-Object {$_.Name -like "*node-red*"}

# 測試 API
Invoke-RestMethod -Uri http://localhost:1880/flows -TimeoutSec 5
```

**解決步驟**:
1. 重啟 Node-RED 服務 (通過服務管理器)
2. 或重新部署 Flows:
   ```powershell
   # 導入 Flows
   node-red flows\flow1-futu-opend.json
   ```

### 問題 4: 決策引擎異常

**症狀**: 
- 無法生成決策
- 決策結果明顯錯誤

**診斷**:
```powershell
# 檢查數據充足性
python check_data.py

# 檢查評分數據
# 查詢數據庫: SELECT * FROM absolute_scores ORDER BY timestamp DESC LIMIT 5;
```

**解決步驟**:
1. 確保數據流正常 (見問題 2)
2. 檢查 Node-RED Flow 7/8 是否運行
3. 手動運行決策引擎查看錯誤:
   ```powershell
   python decision-engine\main.py
   ```

### 問題 5: 系統整體異常

**緊急恢復流程**:
```powershell
# 1. 停止所有 Python 進程
Get-Process python | Stop-Process

# 2. 檢查系統狀態
python deploy_prep.py

# 3. 按順序重新啟動
#    a. 確保 Futu OpenD 運行
#    b. 啟動數據饋送器
python futu-adapter\futu_opend_feed_v2.py

# 4. 驗證恢復
python cron\six_loop_monitor.py
```

---

## 安全注意事項

### ⚠️ 重要提醒

1. **API 密鑰安全**
   - ✅ `.gitignore` 已配置，不會提交敏感文件
   - 使用環境變量存儲敏感信息
   - 定期更換密鑰 (建議每 3 個月)

2. **風險限制 (已配置)**
   | 限制項 | 閾值 | 說明 |
   |--------|------|------|
   | 日虧損限制 | $500 | 達到後暫停交易 |
   | 最大倉位 | 1000 股 | TQQQ 最大持倉 |
   | 止損 | 2% | 自動止損觸發 |
   | 止盈 | 3% | 自動止盈觸發 |
   | 總持倉風險 | 4% | 超過後減倉 |

3. **交易前檢查清單**
   - [ ] Futu OpenD 運行正常 (端口 11111)
   - [ ] 數據流穩定 (>100 條/小時)
   - [ ] 系統監控無告警
   - [ ] 風險限制已設置
   - [ ] 備用數據源就緒

### 緊急停止程序

⚠️ **如遇緊急情況，立即執行**:

```powershell
# 1. 停止所有 Python 進程 (包括數據饋送器)
Get-Process python | Stop-Process

# 2. 記錄停止原因
echo "緊急停止: $(Get-Date) - [原因]" >> logs/emergency_stop.log

# 3. 通知管理員
# 通過 WhatsApp 或其他方式通知
```

### 數據備份

```powershell
# 手動備份數據庫
pg_dump -h localhost -p 5432 -U postgres trading_db > backup/trading_db_$(Get-Date -Format 'yyyyMMdd').sql

# 備份 Flows
copy flows\*.json backup\flows_$(Get-Date -Format 'yyyyMMdd')\
```

---

## 附錄

### A. 常用命令速查

```powershell
# 系統檢查
python deploy_prep.py              # 部署準備檢查
python cron\six_loop_monitor.py     # 系統監控
python check_data.py               # 數據流檢查
python security_check.py           # 安全檢查

# 測試
python e2e_test.py                 # 端到端測試
python risk_management_test.py     # 風險管理測試
python achievement_test.py         # 成就系統測試

# 任務管理
python task_manager.py init        # 初始化任務
python task_manager.py report      # 查看進度

# 數據饋送
python futu-adapter\futu_opend_feed_v2.py  # 啟動饋送器
```

### B. 文件清單

| 文件 | 用途 |
|------|------|
| `SYSTEM_ARCHITECTURE.md` | 系統架構文檔 |
| `SIX_LOOP_IMPROVEMENT_PLAN.md` | 完善計劃 |
| `OPERATIONS_MANUAL.md` | 本操作手冊 |
| `config/symbols.yaml` | 標的配置 |
| `.gitignore` | Git 忽略配置 |

### C. 監控日誌位置

```
logs/
├── monitor_*.log          # 系統監控日誌
├── e2e_test_*.json        # 端到端測試報告
├── risk_test_*.json       # 風險測試報告
├── security_check_*.json  # 安全檢查報告
├── deployment_prep_*.json # 部署準備報告
├── tasks/                 # 任務記錄
│   └── phase*_*.json
└── alerts.json            # 告警歷史
```

### D. 聯繫支持

- **系統負責人**: 呀鬼 (Alfred)
- **用戶/決策者**: 靚仔 (Burt)
- **專案路徑**: `~/openclaw_workspace/projects/six-loop-system/`
- **狀態文件**: `project-states/Six-Loop-System-STATUS.md`

---

## 更新日誌

| 日期 | 版本 | 更新內容 |
|------|------|----------|
| 2026-04-20 | v1.0 | 初始版本 |
| 2026-04-20 | v1.1 | 更新 Phase 4 完成內容，添加詳細操作指南 |
| 2026-04-22 | v1.2 | 更新時間戳，系統狀態維持正常 |
| 2026-04-22 | v1.3 | 更新時間戳，完成 Node-RED Flows 建立 |

---

*最後更新: 2026-04-22 09:32*  
*系統狀態: ✅ 所有 Phase 完成 - 已就緒*
