# NQ100 成份股爬蟲

## 功能

- 從 NASDAQ 官方 API 獲取 NQ100 指數成份股（101隻）
- 使用 yfinance 獲取市值數據計算權重
- 提取前50大權重成份股
- 保存到 PostgreSQL `constituents` 表
- 每日自動更新機制

## 文件說明

| 文件 | 說明 |
|------|------|
| `nq100_constituents.py` | 主爬蟲腳本（302行） |
| `scheduler.py` | 每日定時更新排程器 |
| `test_fetch.py` | 測試腳本（不連數據庫） |
| `.env` | 數據庫配置 |

## 使用方法

### 1. 安裝依賴

```bash
pip install yfinance requests pandas psycopg2 python-dotenv
```

### 2. 配置數據庫

編輯 `.env` 文件：

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sixloop
DB_USER=postgres
DB_PASSWORD=your_password
```

### 3. 手動運行

```bash
python nq100_constituents.py
```

### 4. 測試（不連數據庫）

```bash
python test_fetch.py
```

### 5. 啟動自動更新

```bash
# Windows
scheduler_service.bat

# Linux/Mac
./scheduler_service.sh
```

## 資料表結構

```sql
CREATE TABLE constituents (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    weight DECIMAL(10, 4),
    market_cap BIGINT,
    market_cap_str VARCHAR(50),
    last_sale_price VARCHAR(20),
    net_change VARCHAR(20),
    percentage_change VARCHAR(20),
    report_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, report_date)
);
```

## 更新頻率

- 每日 09:30, 14:00, 21:00 自動更新
- 手動運行隨時更新

## 數據來源

- **成份股列表**: NASDAQ 官方 API (https://api.nasdaq.com/api/quote/list-type/nasdaq100)
- **市值數據**: yfinance (Yahoo Finance)
- **權重計算**: 基於市值比例

## 測試結果

```
✅ 成功獲取 101 隻 NQ100 成份股
✅ 成功獲取 101 隻股票的市值數據
✅ 提取前 50 隻（按權重排序）

前5大成份股:
1. NVDA  - NVIDIA Corporation    - 權重: 13.00% - 市值: $4.85T
2. GOOGL - Alphabet Inc. Class A - 權重: 10.79% - 市值: $4.03T
3. GOOG  - Alphabet Inc. Class C - 權重: 10.73% - 市值: $4.01T
4. AAPL  - Apple Inc.            - 權重: 10.49% - 市值: $3.91T
5. MSFT  - Microsoft Corporation - 權重: 8.47%  - 市值: $3.16T
```
