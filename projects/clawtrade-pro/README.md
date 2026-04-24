# ClawTrade Pro - 獨立交易系統

> 項目位置: `projects/clawtrade-pro/`
> 
> 注意: 此專案依賴 `private skills/clawtrade-pro/` 的技能模組

---

## 專案結構

```
projects/clawtrade-pro/
├── main.py                  # 主程序入口
├── config/                  # 配置檔案
│   ├── trading.yaml         # 主交易配置
│   ├── strategies.yaml      # 策略配置
│   └── secrets.yaml.example # 機密配置模板
├── database/                # 數據庫模組
│   ├── db_manager.py        # 數據庫管理
│   └── schema.sql           # 數據庫結構
└── tests/                   # 測試檔案
```

## 依賴關係

此專案 **不是獨立** 的，它依賴以下技能模組：

| 依賴模組 | 來源位置 | 用途 |
|---------|---------|------|
| trading-core | `private skills/clawtrade-pro/trading-core/` | Futu API 封裝 |
| engine | `private skills/clawtrade-pro/engine/` | 策略引擎 |
| risk | `private skills/clawtrade-pro/risk/` | 風險管理 |
| heartbeat | `private skills/clawtrade-pro/automation/heartbeat/` | 心跳監控 |
| cron_jobs | `private skills/clawtrade-pro/automation/cron_jobs/` | 定時任務 |
| strategies | `private skills/clawtrade-pro/strategies/` | 交易策略 |

## 使用方法

### 1. 確保技能模組就緒

```bash
# 檢查 private skills 是否存在
ls "../private skills/clawtrade-pro/"
```

### 2. 配置環境

```bash
# 複製機密配置模板
cp config/secrets.yaml.example config/secrets.yaml

# 編輯配置
nano config/secrets.yaml
nano config/trading.yaml
nano config/strategies.yaml
```

### 3. 運行系統

```bash
# 實盤交易
python main.py --mode live

# 回測模式
python main.py --mode backtest --symbol TQQQ

# 僅生成信號（不交易）
python main.py --mode signal --symbol TQQQ
```

## 配置說明

### trading.yaml
```yaml
# 交易標的配置
symbols:
  TQQQ:
    enabled: true
    strategy: tqqq_momentum
    
# 風險參數
risk:
  max_position: 0.25      # 最大倉位 25%
  stop_loss: 0.05         # 止損 5%
  
# 通知設置
notifications:
  whatsapp: true
  pushover: false
```

### strategies.yaml
```yaml
# 策略參數
strategies:
  tqqq_momentum:
    zscore_threshold: 1.65
    rsi_overbought: 70
    rsi_oversold: 30
    lookback_days: 60
```

## 開發指南

### 添加新策略

1. 在 `private skills/clawtrade-pro/strategies/` 創建策略類
2. 繼承 `BaseStrategy`
3. 實現 `generate_signal()` 方法
4. 在 `config/strategies.yaml` 註冊

### 修改主程序

編輯 `main.py`：
- `ClawTradePro` 類：主系統邏輯
- `_load_config()`：配置加載
- `run()`：主循環
- `execute_signal()`：信號執行

## 常見問題

### ImportError: No module named 'trading_core'

**原因**: 路徑未正確添加

**解決**: 確保 `private skills/clawtrade-pro/` 存在，且 `main.py` 中的路徑正確

### ModuleNotFoundError: No module named 'risk_manager'

**原因**: 模組名或路徑錯誤

**解決**: 檢查 `private skills/clawtrade-pro/risk/` 是否存在 `risk_manager.py`

## 更新記錄

| 日期 | 更新內容 |
|------|---------|
| 2026-04-09 | 更新路徑指向 `private skills/clawtrade-pro/`，添加本 README |

## 相關文檔

- 技能詳細文檔: `../private skills/clawtrade-pro/SKILL.md`
- 研究報告: `../private skills/clawtrade-pro/research/`
- 系統設計: `../private skills/clawtrade-pro/docs/`
