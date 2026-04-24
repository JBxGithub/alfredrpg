# 富途 OpenAPI 連接方式研究筆記

## 系統架構

富途 OpenAPI 採用雙層架構：

```
┌─────────────────────────────────────────────┐
│           你的交易程式 (Python/Java/C++...)   │
│              ↓ Futu API SDK                 │
├─────────────────────────────────────────────┤
│           OpenD 網關程式                     │
│   (本地運行，TCP 協議，默認端口 11111)        │
│              ↓ 加密傳輸                      │
├─────────────────────────────────────────────┤
│           富途伺服器                         │
│              ↓                              │
├─────────────────────────────────────────────┤
│           交易所                             │
└─────────────────────────────────────────────┘
```

## OpenD 網關

### 下載與安裝

- **官方下載**: https://www.futunn.com/en/download/openAPI
- **支援系統**: Windows、MacOS、Ubuntu、CentOS
- **安裝方式**: 解壓即用

### 配置參數

| 配置項 | 說明 | 默認值 |
|--------|------|--------|
| IP | API 監聽 IP 地址 | 127.0.0.1 |
| Port | API 監聽端口 | 11111 |
| Log Level | 日誌級別 | info |
| Language | 語言 | zh |
| WebSocket IP | WebSocket 監聽地址 | 127.0.0.1 |
| WebSocket Port | WebSocket 監聽端口 | 22222 |

### 安全設定

- **RSA 加密私鑰**: 當監聽地址非本地時，必須配置私鑰才能使用交易接口
- **WebSocket SSL**: 當 WebSocket 監聽地址非本地時，需要配置 SSL 證書

## Python SDK

### 安裝

```bash
pip install futu-api
```

### 核心類別

#### 1. OpenQuoteContext - 行情上下文

```python
import futu as ft

# 創建行情連接
quote_ctx = ft.OpenQuoteContext(host="127.0.0.1", port=11111)

# 開啟異步數據接收
quote_ctx.start()

# 設置回調處理器
quote_ctx.set_handler(ft.TickerHandlerBase())

# 訂閱行情數據
quote_ctx.subscribe(code, [ft.SubType.QUOTE, ft.SubType.TICKER])

# 關閉連接
quote_ctx.close()
```

#### 2. 交易上下文

```python
# 港股交易
hk_trade_ctx = ft.OpenHKTradeContext(host="127.0.0.1", port=11111)

# 美股交易
us_trade_ctx = ft.OpenUSTradeContext(host="127.0.0.1", port=11111)

# A股通交易
a_trade_ctx = ft.OpenAQuoteContext(host="127.0.0.1", port=11111)
```

### 主要接口

#### 行情接口

| 接口 | 功能 | 頻率 |
|------|------|------|
| `get_trading_days` | 獲取交易日 | 低頻 |
| `get_stock_basicinfo` | 獲取股票基本信息 | 低頻 |
| `get_market_snapshot` | 獲取市場快照 | 低頻 |
| `get_stock_quote` | 獲取報價 | 訂閱後 |
| `get_rt_ticker` | 獲取逐筆 | 訂閱後 |
| `get_cur_kline` | 獲取K線 | 訂閱後 |
| `get_order_book` | 獲取買賣盤 | 訂閱後 |

#### 交易接口

| 接口 | 功能 |
|------|------|
| `unlock_trade` | 解鎖交易 |
| `accinfo_query` | 查詢賬戶資金 |
| `position_list_query` | 查詢持倉 |
| `order_list_query` | 查詢訂單列表 |
| `place_order` | 下單 |
| `modify_order` | 修改訂單 |
| `cancel_order` | 撤單 |

### 訂閱類型 (SubType)

```python
ft.SubType.QUOTE      # 報價
ft.SubType.TICKER     # 逐筆
ft.SubType.K_DAY      # 日K線
ft.SubType.K_1M       # 1分鐘K線
ft.SubType.ORDER_BOOK # 買賣盤
ft.SubType.RT_DATA    # 分時數據
ft.SubType.BROKER     # 經紀隊列
```

### 市場代碼 (Market)

```python
ft.Market.HK   # 香港
ft.Market.US   # 美國
ft.Market.SH   # 上海
ft.Market.SZ   # 深圳
```

### 交易環境 (TrdEnv)

```python
ft.TrdEnv.SIMULATE  # 模擬交易
ft.TrdEnv.REAL      # 實盤交易
```

## 連接流程

```
1. 啟動 OpenD 網關程式
   ↓
2. 在 OpenD 中登入富途帳號
   ↓
3. Python 程式連接 OpenD (host: 127.0.0.1, port: 11111)
   ↓
4. 創建行情/交易上下文
   ↓
5. 開始交易/獲取行情
```

## 注意事項

1. **必須先啟動 OpenD** 才能連接 API
2. **首次登入需要完成問卷調查和協議確認**
3. **實盤交易需要解鎖密碼**
4. **部分行情需要購買報價卡才能獲取**
5. **訂閱高頻數據會消耗訂閱額度**

## 參考資源

- [官方文檔](https://openapi.futunn.com/futu-api-doc/en/)
- [GitHub 文檔](https://github.com/FutunnOpen/futu-api-doc)
- [PyPI 頁面](https://pypi.org/project/futu-api/)
