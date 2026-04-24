# FutuTradingBot 實盤部署檢查清單

> **專案**: FutuTradingBot (FTB-001)  
> **日期**: 2026-04-11  
> **環境**: REAL (NASDAQ)  
> **實盤密碼**: 011087 + Enter

---

## 🚨 部署前必讀

**⚠️ 警告**: 實盤交易涉及真實資金，請確保以下所有檢查項目均已通過，並理解所有風險。

---

## ✅ 一、API 連接設定檢查

### 1.1 OpenD 連接配置
| 檢查項目 | 配置值 | 狀態 | 備註 |
|---------|--------|------|------|
| OpenD Host | 127.0.0.1 | ⬜ | 確認 OpenD 已啟動 |
| OpenD Port | 11111 | ⬜ | 默認端口 |
| WebSocket Port | 8765 | ⬜ | Realtime Bridge 使用 |

**檔案位置**: `src/config/settings.py` (OpenDConfig)

### 1.2 交易環境設定
| 檢查項目 | 當前值 | 目標值 | 狀態 |
|---------|--------|--------|------|
| 交易環境 | SIMULATE | **REAL** | ⚠️ 需修改 |
| 解鎖密碼 | ${FUTU_UNLOCK_PASSWORD} | 011087 | ⬜ 需設定 |

**檔案位置**: `config/config.yaml` (trading.default_trd_env)

### 1.3 環境變數檢查
```bash
# 確認 .env 檔案已正確配置
FUTU_UNLOCK_PASSWORD=011087
FUTU_TRD_ACCOUNT=your_account_id
```

**檔案位置**: `config/.env`

---

## ✅ 二、風險控制設定檢查

### 2.1 核心風險限制 (必須符合要求)
| 風險項目 | 當前配置 | 要求 | 狀態 | 檔案位置 |
|---------|---------|------|------|---------|
| **單筆最大風險** | 1.0% | **≤1%** | ✅ | strategy-panel/backend/config.py |
| **每日最大虧損** | 2.0% | **≤2%** | ✅ | strategy-panel/backend/config.py |
| **總持倉風險** | ≤4% (max_positions=3) | **≤4%** | ✅ | strategy-panel/backend/config.py |
| **單一股票最大倉位** | 20% | 監控用 | ⬜ | config/risk_config.json |
| **總倉位上限** | 80% | 監控用 | ⬜ | config/risk_config.json |

### 2.2 風險控制開關
| 控制項目 | 狀態 | 備註 |
|---------|------|------|
| enable_position_risk | ✅ true | 倉位風控啟用 |
| enable_trade_risk | ✅ true | 交易風控啟用 |
| enable_capital_risk | ✅ true | 資金風控啟用 |
| auto_stop_on_critical | ✅ true | 嚴重風險自動停止 |

**檔案位置**: `config/risk_config.json`

### 2.3 實盤額外風險設定
| 檢查項目 | 建議值 | 狀態 |
|---------|--------|------|
| 每日最大交易次數 | 10 (實盤建議) | ⬜ 待確認 |
| 單筆最大金額 | $10,000 (初始) | ⬜ 待確認 |
| 價格異常閾值 | 5% | ✅ |
| 強制停止回撤 | 15% | ✅ |

---

## ✅ 三、MTF 參數檢查

### 3.1 時間框架權重配置
| 時間框架 | 權重 | 狀態 | 備註 |
|---------|------|------|------|
| 月線 (Monthly) | 40% | ✅ | 符合要求 |
| 週線 (Weekly) | 35% | ✅ | 符合要求 |
| 日線 (Daily) | 25% | ✅ | 符合要求 |
| **總和** | **100%** | ✅ | 驗證通過 |

**檔案位置**: `strategy-panel/backend/config.py` (DEFAULT_CONFIG.mtf)

### 3.2 MTF 功能開關
| 功能 | 狀態 | 備註 |
|------|------|------|
| MTF 啟用 | ✅ enabled: true | |
| MACD-V 整合 | ✅ macd_v_enabled: true | |
| 背離檢測 | ✅ divergence_enabled: true | |
| 最低評分閾值 | 60分 | ✅ |

---

## ✅ 四、策略配置檢查

### 4.1 活躍策略確認
| 策略名稱 | MTF整合 | 狀態 | 用途 |
|---------|---------|------|------|
| TQQQLongShortStrategy | ✅ | 活躍 | 主要策略 |
| ZScoreStrategy | ✅ | 活躍 | 均值回歸 |
| TrendStrategy | ✅ | 活躍 | 趨勢跟隨 |
| BreakoutStrategy | ✅ | 活躍 | 突破交易 |
| MomentumStrategy | ✅ | 活躍 | 動量交易 |
| FlexibleArbitrageStrategy | ✅ | 活躍 | 靈活套利 |

### 4.2 Z-Score 策略參數 (主要策略)
| 參數 | 當前值 | 狀態 |
|------|--------|------|
| Z-Score 進場閾值 | ±1.65 | ✅ |
| Z-Score 出場閾值 | ±0.5 | ✅ |
| Z-Score 止損閾值 | ±3.5 | ✅ |
| 回望期 | 60日 | ✅ |
| RSI 超買 | 70 | ✅ |
| RSI 超賣 | 30 | ✅ |
| 止盈 | 5% | ✅ |
| 止損 | 3% | ✅ |
| 時間止損 | 7天 | ✅ |
| 單筆倉位 | 50% | ✅ |

**檔案位置**: `config/strategy_config.yaml` (zscore_strategy)

---

## ✅ 五、日誌記錄設定檢查

### 5.1 日誌配置
| 項目 | 配置 | 狀態 |
|------|------|------|
| 日誌級別 | INFO | ✅ |
| 檔案日誌 | 啟用 | ✅ |
| 控制台輸出 | 啟用 | ✅ |
| 日誌保留 | 30天 | ✅ |
| 交易日誌 | CSV格式 | ✅ |

**檔案位置**: `src/utils/logger_config.py`

### 5.2 實盤監控要求
| 項目 | 狀態 | 備註 |
|------|------|------|
| 實時價格記錄 | ⬜ | 確認啟用 |
| 交易信號記錄 | ⬜ | 確認啟用 |
| 風險事件記錄 | ⬜ | 確認啟用 |
| 每日盈虧記錄 | ⬜ | 確認啟用 |

---

## ✅ 六、部署前最終檢查

### 6.1 系統狀態確認
- [ ] OpenD 已啟動並運行
- [ ] API 連接測試通過
- [ ] 賬戶資金已確認
- [ ] 交易密碼已準備 (011087)

### 6.2 資金確認
| 項目 | 金額 | 狀態 |
|------|------|------|
| 初始注資 | HK$10,000 / US$1,280 | ⬜ 確認已到位 |
| 月費訂閱 | ~HK$468 (Nasdaq Basic) | ⬜ 確認已付費 |
| 測試資金 | US$2,000-3,000 | ⬜ 確認可用 |

### 6.3 緊急應對
| 項目 | 狀態 | 備註 |
|------|------|------|
| 緊急平倉按鈕 | ⬜ 測試 | Dashboard功能 |
| 交易停止開關 | ⬜ 測試 | RiskManager功能 |
| 手動介入流程 | ⬜ 確認 | 主人需了解 |

---

## ✅ 七、部署步驟

### Step 1: 環境準備
```bash
# 1. 啟動 OpenD
# 2. 確認連接狀態
python -c "from src.api.futu_client import FutuAPIClient; c = FutuAPIClient(); print(c.connect_quote())"
```

### Step 2: 配置修改
1. 修改 `config/config.yaml`:
   ```yaml
   trading:
     default_trd_env: "REAL"  # 從 SIMULATE 改為 REAL
   ```

2. 設定環境變數:
   ```bash
   export FUTU_UNLOCK_PASSWORD="011087"
   ```

### Step 3: 風險參數最終確認
- [ ] 單筆風險 ≤1%
- [ ] 每日虧損 ≤2%
- [ ] 持倉數量 ≤3

### Step 4: 啟動系統
```bash
# 啟動 Realtime Bridge
python src/realtime_bridge.py

# 啟動 Dashboard
python src/dashboard/app.py

# 訪問 http://127.0.0.1:8080
# 密碼: futu2024
```

### Step 5: 實盤解鎖
1. 在 Dashboard 點擊「解鎖交易」
2. 輸入密碼: **011087**
3. 按 **Enter** 確認

---

## ✅ 八、部署後監控

### 8.1 首小時監控 (關鍵)
| 時間 | 檢查項目 | 狀態 |
|------|---------|------|
| T+0 | 價格數據正常接收 | ⬜ |
| T+5min | 交易信號正常生成 | ⬜ |
| T+15min | 風險監控正常運作 | ⬜ |
| T+30min | 日誌記錄正常 | ⬜ |
| T+60min | 系統整體穩定 | ⬜ |

### 8.2 每日檢查
- [ ] 檢查前日交易記錄
- [ ] 確認風險事件記錄
- [ ] 驗證資金變動正確
- [ ] 檢查系統日誌無異常

---

## ✅ 九、風險聲明

### 9.1 已知風險
1. **市場風險**: TQQQ 為3倍槓桿ETF，波動極大
2. **策略風險**: 回測勝率 46.43%，存在連續虧損可能
3. **技術風險**: 系統故障可能導致非預期交易
4. **流動性風險**: 極端市場條件下可能無法成交

### 9.2 風險緩解
- ✅ 嚴格止損 (3%)
- ✅ 時間止損 (7天)
- ✅ 倉位控制 (50%單筆)
- ✅ 每日虧損限制 (2%)
- ✅ 自動風控停止

---

## ✅ 十、聯絡與支援

| 項目 | 資訊 |
|------|------|
| 專案狀態 | `project-states/FutuTradingBot-STATUS.md` |
| 系統架構 | `projects/fututradingbot/SYSTEM_ARCHITECTURE.md` |
| 交易日誌 | `projects/fututradingbot/logs/` |
| 風控配置 | `projects/fututradingbot/config/risk_config.json` |

---

## 📝 簽核

| 角色 | 姓名 | 簽名 | 日期 |
|------|------|------|------|
| 策略確認 | 呀鬼 | ______ | ______ |
| 風控確認 | 呀鬼 | ______ | ______ |
| 技術確認 | 呀鬼 | ______ | ______ |
| 最終批准 | 靚仔 | ______ | ______ |

---

**⚠️ 重要提醒**: 
- 首次實盤建議使用最小倉位測試
- 建議先運行1-2週觀察系統穩定性
- 任何異常立即切換回 SIMULATE 模式

---

*最後更新: 2026-04-11*  
*版本: v1.0*  
*狀態: 待部署*
