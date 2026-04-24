# OpenClaw 交易系統完整架構設計

## 系統名稱
**ClawTrade Pro** - OpenClaw 智能交易系統

## 設計原則
1. **單一職責** - 每個 Skill 只做一件事
2. **依賴注入** - Core Skill 提供基礎能力，其他 Skill 依賴使用
3. **事件驅動** - 自動觸發機制（HEARTBEAT + Cron）
4. **數據優先** - Futu API 為主，Investing.com 為輔
5. **風險至上** - 所有交易必須經過風險檢查

---

## 系統架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│                        ClawTrade Pro                            │
│                     OpenClaw Trading System                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    用戶交互層                              │  │
│  │  WhatsApp │ 命令行 │ Dashboard │ 語音                    │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │                    指令解析層                              │  │
│  │  /position │ /signal │ /order │ /risk │ /report          │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │                    Skills 層                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │ trading-core│  │ tqqq-momentum│  │risk-manager │      │  │
│  │  │  (核心)      │  │  (策略)      │  │  (風控)      │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │  arbitrage  │  │   pairs     │  │  notifier   │      │  │
│  │  │  (套利)      │  │ (配對交易)   │  │  (通知)      │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │                    數據層                                  │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │  Futu API   │  │ Investing   │  │  Database   │      │  │
│  │  │  (主要)      │  │  (輔助)      │  │  (本地)      │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    觸發機制層                              │  │
│  │  HEARTBEAT │ Cron Jobs │ Webhooks │ Event Listeners      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Skills 詳細設計

### 1. trading-core (核心 Skill)

**職責：** 提供基礎交易能力，所有其他 Skill 的依賴

**功能：**
- Futu API 連接管理
- 實時行情獲取
- 歷史數據查詢
- 賬戶信息查詢
- 持倉管理
- 下單/撤單

**接口：**
```python
class TradingCore:
    def connect() -> bool
    def disconnect()
    def get_realtime_quote(symbol: str) -> Dict
    def get_historical_kline(symbol, start, end, ktype) -> DataFrame
    def get_account_info() -> Dict
    def get_positions() -> List[Dict]
    def place_order(symbol, side, qty, price) -> Dict
    def cancel_order(order_id) -> bool
```

**數據源：**
- 主要：Futu API (實時報價、歷史K線、交易執行)
- 輔助：Investing.com (市場概覽、經濟日曆)

---

### 2. tqqq-momentum (策略 Skill)

**職責：** TQQQ 動量交易策略

**策略邏輯：**
- RSI < 30 + MA 金叉 + MACD > Signal = BUY
- RSI > 70 + MA 死叉 + MACD < Signal = SELL
- 需滿足 2/3 條件

**自動觸發：**
- HEARTBEAT: 每5分鐘檢查 (市場時間)
- Cron: 09:30-16:00 ET, 每5分鐘

**風險控制：**
- 單筆最大 25% 資金
- 自動止損 -5%
- 自動止盈 +10%

**接口：**
```python
class TQQQMomentumStrategy:
    def calculate_indicators(df) -> df
    def generate_signal(df) -> Dict
    def backtest(start_date, end_date) -> Dict
```

---

### 3. risk-manager (風控 Skill)

**職責：** 實時風險監控和管理

**風險規則：**
- 單一標的最大 25% 資金
- 總持倉最大 80% 資金
- 日虧損最大 $500
- 保證金使用率最大 70%
- 自動止損 -5%
- 自動止盈 +10%

**自動觸發：**
- HEARTBEAT: 每分鐘檢查 (市場時間)
- 緊急情況立即處理

**接口：**
```python
class RiskManager:
    def check_position_limit(symbol, qty) -> (bool, reason)
    def check_daily_loss_limit(current_pnl) -> bool
    def check_margin_usage() -> bool
    def calculate_stop_loss(entry_price, position) -> price
    def calculate_take_profit(entry_price, position) -> price
```

---

### 4. whatsapp-notifier (通知 Skill)

**職責：** WhatsApp 實時通知

**通知類型：**
- 交易信號生成
- 訂單執行確認
- 止損/止盈觸發
- 風險警報
- 日報/週報

**觸發方式：**
- 事件驅動（其他 Skill 觸發）
- 定時報告（每日收盤後）

**接口：**
```python
class WhatsAppNotifier:
    def send_signal_alert(signal) -> bool
    def send_order_confirmation(order) -> bool
    def send_risk_alert(alert) -> bool
    def send_daily_report(stats) -> bool
```

---

### 5. arbitrage-detector (套利 Skill) - 未來擴展

**職責：** 檢測套利機會

**策略：**
- 期現套利（需要期貨賬戶資金）
- 跨市場套利
- ETF 折溢價套利

---

### 6. pairs-trading (配對交易 Skill) - 未來擴展

**職責：** 股票對交易

**策略：**
- 相關性分析
- 均值回歸交易
- 統計套利

---

## 數據流設計

### 實時數據流
```
Futu API → trading-core → [策略 Skills] → risk-manager → 交易決策 → 下單
                ↓
         whatsapp-notifier (通知)
```

### 歷史數據流
```
Futu API → trading-core → Database → 回測 → 策略優化
```

### 市場數據流
```
Investing.com → trading-core → 市場情緒分析 → 策略調整
```

---

## 觸發機制設計

### HEARTBEAT 配置

```markdown
# HEARTBEAT.md

## 每分鐘 (市場時間 09:30-16:00 ET)
- [ ] risk-manager: 檢查所有風險限制
- [ ] risk-manager: 監控止損止盈觸發
- [ ] trading-core: 更新持倉市值

## 每5分鐘 (市場時間)
- [ ] tqqq-momentum: 檢查動量信號
- [ ] trading-core: 更新市場數據緩存

## 每小時 (市場時間)
- [ ] trading-core: 生成交易摘要
- [ ] risk-manager: 檢查賬戶風險狀態

## 每日 (收盤後 16:30 ET)
- [ ] whatsapp-notifier: 發送日報
- [ ] trading-core: 計算當日盈虧
- [ ] risk-manager: 更新風險統計

## 每週 (週五收盤後)
- [ ] whatsapp-notifier: 發送週報
- [ ] tqqq-momentum: 回顧策略表現
- [ ] tqqq-momentum: 生成參數調整建議
```

### Cron Jobs 配置

```json
{
  "jobs": [
    {
      "name": "risk-check",
      "schedule": "* 9-16 * * 1-5",
      "timezone": "America/New_York",
      "action": "risk_manager.check_all_limits"
    },
    {
      "name": "tqqq-signal",
      "schedule": "*/5 9-16 * * 1-5",
      "timezone": "America/New_York",
      "action": "tqqq_momentum.check_signals"
    },
    {
      "name": "daily-report",
      "schedule": "30 16 * * 1-5",
      "timezone": "America/New_York",
      "action": "whatsapp_notifier.send_daily_report"
    }
  ]
}
```

---

## 用戶交互設計

### WhatsApp 指令

| 指令 | 功能 | 示例 |
|------|------|------|
| `/position [symbol]` | 查詢持倉 | `/position TQQQ` |
| `/account` | 查詢賬戶 | `/account` |
| `/signal [symbol]` | 手動檢查信號 | `/signal TQQQ` |
| `/order BUY/SELL symbol qty` | 下單 | `/order BUY TQQQ 100` |
| `/risk` | 查詢風險狀態 | `/risk` |
| `/report [daily/weekly]` | 生成報告 | `/report daily` |
| `/confirm` | 確認執行信號 | `/confirm` |
| `/ignore` | 忽略信號 | `/ignore` |

### 自動通知模板

**交易信號：**
```
🚨 TQQQ 交易信號

信號: BUY (強)
當前價: $52.35
RSI: 28.5 (超賣) ✅
MA20: $51.80 > MA50: $52.10 ✅
MACD: 0.15 > Signal: 0.08 ✅

建議: 買入 100 股
止損: $49.73 (-5%)
止盈: $57.59 (+10%)

回覆 /confirm 執行 或 /ignore 忽略
```

**訂單確認：**
```
✅ 訂單已執行

標的: TQQQ
方向: BUY
數量: 100
價格: $52.35
時間: 09:45:32 ET

持倉更新: 100 股 @ $52.35
```

**風險警報：**
```
⚠️ 風險警報

日虧損: -$450
限制: $500
剩餘: $50

建議: 暫停新交易
```

---

## 數據庫設計

### 價格數據表
```sql
CREATE TABLE price_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(18, 4),
    volume BIGINT,
    timestamp DATETIME(3),
    INDEX idx_symbol_time (symbol, timestamp)
);
```

### 交易記錄表
```sql
CREATE TABLE trade_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id VARCHAR(50),
    symbol VARCHAR(20),
    side VARCHAR(10),
    quantity INT,
    price DECIMAL(18, 4),
    status VARCHAR(20),
    timestamp DATETIME(3)
);
```

### 信號記錄表
```sql
CREATE TABLE signal_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    symbol VARCHAR(20),
    signal VARCHAR(20),
    strength VARCHAR(20),
    indicators JSON,
    executed BOOLEAN,
    timestamp DATETIME(3)
);
```

---

## 安全設計

### API 密鑰管理
- 使用 OpenClaw secrets 存儲 Futu 密碼
- 環境變量注入，不硬編碼

### 交易安全
- 所有訂單必須經過風險檢查
- 日虧損達到限制自動暫停
- 異常情況自動通知

### 數據安全
- 本地數據庫加密存儲
- 敏感操作日誌記錄

---

## 實施路線圖

### 第一階段（第1-2週）：基礎設施
- [ ] 實現 trading-core（Futu API 封裝）
- [ ] 實現 Investing.com 數據源
- [ ] 設置數據庫
- [ ] 測試連接和基礎功能

### 第二階段（第3-4週）：核心功能
- [ ] 實現 tqqq-momentum 策略
- [ ] 實現 risk-manager 風控
- [ ] 整合 HEARTBEAT 觸發
- [ ] 回測和參數優化

### 第三階段（第5-6週）：通知和交互
- [ ] 實現 whatsapp-notifier
- [ ] 設置 WhatsApp 指令
- [ ] 測試自動通知
- [ ] 生成報告功能

### 第四階段（第7-8週）：測試和上線
- [ ] 模擬交易測試
- [ ] 小資金實盤測試
- [ ] 監控和調整
- [ ] 文檔和培訓

---

## 技術棧

| 組件 | 技術 |
|------|------|
| 核心語言 | Python 3.11+ |
| API 連接 | Futu API SDK |
| 數據處理 | Pandas, NumPy |
| 技術指標 | TA-Lib |
| 數據庫 | SQLite / PostgreSQL |
| 通知 | OpenClaw WhatsApp |
| 調度 | OpenClaw HEARTBEAT + Cron |

---

## 風險聲明

⚠️ **重要提示：**
1. 本系統僅為輔助工具，不構成投資建議
2. 所有交易決策最終由用戶確認
3. 過去表現不代表未來收益
4. 槓桿交易風險極高，可能導致重大虧損
5. 請確保理解所有風險後再使用

---

*架構設計版本: 1.0*
*設計日期: 2026-04-04*
*設計師: OpenClaw Agent (Alfred)*
