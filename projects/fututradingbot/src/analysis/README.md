# 股票9步分析法模組

## 概述

這個模組實現了一套完整的股票9步分析法，用於自動化股票研究和投資決策支持。

## 9步分析法

1. **基本面分析** - 獲取公司資料、行業分類
2. **財務健康** - 資產負債表、現金流分析
3. **競爭對手** - 同業比較
4. **歷史走勢** - 價格趨勢、波動率
5. **宏觀環境** - 市場指數、行業趨勢
6. **市場情緒** - 新聞情緒、異常成交量
7. **最新財報** - 季度/年度業績
8. **成長潛力** - 營收增長、利潤率趨勢
9. **投資建議** - 綜合評分、風險評估

## 資料來源

- **富途API** (主要) - 即時行情、K線數據、基本面數據
- **Investing.com** (備援) - 基本面數據備援
- **TradingView** (圖表數據) - 技術分析數據
- **金十數據** (新聞) - 市場新聞和情緒

## 安裝

```bash
# 確保已安裝依賴
pip install pandas numpy requests beautifulsoup4

# 如果需要富途API支持
pip install futu-api
```

## 快速開始

### 基本使用

```python
from src.analysis.stock_analysis import StockAnalyzer

# 創建分析器
analyzer = StockAnalyzer()

# 分析股票
report = analyzer.analyze("AAPL", market="US")

# 查看結果
print(f"綜合評分: {report.recommendation.overall_score:.1f}/100")
print(f"投資建議: {report.recommendation.recommendation.value}")
print(f"風險等級: {report.recommendation.risk_level.name}")
```

### 使用便捷函數

```python
from src.analysis.stock_analysis import analyze_stock, batch_analyze

# 分析單一股票
report = analyze_stock("AAPL", market="US")

# 批量分析
stocks = [("AAPL", "US"), ("TSLA", "US"), ("00700", "HK")]
reports = batch_analyze(stocks)
```

### 使用富途API

```python
from src.api.futu_client import FutuAPIClient
from src.analysis.stock_analysis import StockAnalyzer

# 連接富途API
futu_client = FutuAPIClient(host="127.0.0.1", port=11111)
futu_client.connect_quote()

# 使用富途數據進行分析
analyzer = StockAnalyzer(futu_client=futu_client)
report = analyzer.analyze("AAPL", market="US")

# 斷開連接
futu_client.disconnect_all()
```

## 評分系統

### 評分維度

| 維度 | 權重 | 說明 |
|------|------|------|
| 基本面 | 20% | PE、PB、股息率等 |
| 財務健康 | 20% | 流動比率、ROE、負債率等 |
| 技術面 | 20% | 趨勢、RSI、MACD等 |
| 市場情緒 | 15% | 新聞情緒、成交量等 |
| 成長性 | 25% | 營收增長、盈利增長等 |

### 投資建議等級

- **強烈買入** (80-100分)
- **買入** (65-79分)
- **持有** (45-64分)
- **賣出** (30-44分)
- **強烈賣出** (0-29分)

### 風險等級

- **VERY_LOW** - 極低風險
- **LOW** - 低風險
- **MEDIUM** - 中等風險
- **HIGH** - 高風險
- **VERY_HIGH** - 極高風險

## 數據類

### FundamentalData
基本面數據類，包含：
- `stock_code` - 股票代碼
- `stock_name` - 股票名稱
- `market` - 市場
- `industry` - 行業
- `sector` - 板塊
- `market_cap` - 市值
- `pe_ratio` - PE比率
- `pb_ratio` - PB比率
- `dividend_yield` - 股息率

### FinancialHealth
財務健康數據類，包含：
- `current_ratio` - 流動比率
- `quick_ratio` - 速動比率
- `debt_to_equity` - 負債權益比
- `roe` - 股東權益報酬率
- `roa` - 資產報酬率
- `net_margin` - 淨利率

### HistoricalTrend
歷史走勢數據類，包含：
- `current_price` - 當前價格
- `price_52w_high/low` - 52週高低點
- `price_change_*` - 各期間價格變動
- `volatility_*` - 波動率
- `ma_*` - 移動平均線
- `rsi_14` - RSI指標
- `macd` - MACD指標

### InvestmentRecommendation
投資建議數據類，包含：
- `overall_score` - 綜合評分
- `fundamental_score` - 基本面評分
- `financial_health_score` - 財務健康評分
- `technical_score` - 技術面評分
- `sentiment_score` - 情緒評分
- `growth_score` - 成長性評分
- `recommendation` - 投資建議
- `risk_level` - 風險等級
- `target_price_*` - 目標價格
- `key_strengths` - 關鍵優勢
- `key_risks` - 關鍵風險

## 報告導出

```python
# 導出為JSON
json_report = report.to_json(indent=2)

# 導出為字典
dict_report = report.to_dict()

# 保存到文件
with open("report.json", "w", encoding="utf-8") as f:
    f.write(report.to_json())
```

## 測試

```bash
# 運行測試
python tests/test_stock_analysis.py

# 或使用pytest
pytest tests/test_stock_analysis.py -v
```

## 示例

參見 `examples/stock_analysis_example.py` 獲取更多使用示例。

## 注意事項

1. 使用富途API需要啟動OpenD並連接
2. 部分數據可能需要付費訂閱
3. 投資建議僅供參考，不構成投資建議
4. 請自行承擔投資風險

## 授權

MIT License
