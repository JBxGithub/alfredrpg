# 富途交易機器人 (FutuTradingBot)

## 項目結構

```
fututradingbot/
├── src/
│   ├── indicators/
│   │   └── technical.py      # 技術指標模組
│   └── data/
│       └── market_data.py    # 資料獲取模組
├── tests/
│   └── test_indicators.py    # 單元測試
└── README.md
```

## 功能模組

### 1. 技術指標模組 (src/indicators/technical.py)

提供以下技術指標計算：

- **MACD**: DIF、DEA、MACD柱
- **BOLL**: 上軌、中軌、下軌、帶寬
- **EMA**: 5日、10日、20日、60日指數移動平均線
- **VMACD**: 量價MACD (DIF、DEA、VMACD柱)
- **RSI**: 6日、12日、24日相對強弱指標
- **成交量分析**: 均量、量比、OBV能量潮
- **支撐位/阻力位**: 滾動高低點計算
- **ATR**: 平均真實波幅

### 2. 資料獲取模組 (src/data/market_data.py)

提供以下功能：

- **富途API連接**: 連接OpenD服務獲取行情
- **K線數據獲取**: 支持1分鐘到月線多種週期
- **數據緩存**: 本地文件和內存雙層緩存
- **實時行情訂閱**: 支持多種訂閱類型
- **觀察列表管理**: 批量獲取多股票數據

## 安裝依賴

```powershell
# 必要依賴
pip install pandas numpy

# 富途API (可選，用於實際交易)
pip install futu-api

# 測試
pip install unittest
```

## 使用方法

### 技術指標計算

```python
import pandas as pd
from src.indicators.technical import TechnicalIndicators

# 準備K線數據
df = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# 創建指標計算器
indicators = TechnicalIndicators(df)

# 計算MACD
macd = indicators.calculate_macd()
print(macd.dif, macd.dea, macd.macd)

# 計算布林帶
boll = indicators.calculate_boll()
print(boll.upper, boll.middle, boll.lower)

# 計算所有指標
all_indicators = indicators.calculate_all()

# 獲取信號摘要
summary = indicators.get_signal_summary()
print(summary)
```

### 資料獲取

```python
from src.data.market_data import FutuMarketData, KLType

# 初始化行情接口
md = FutuMarketData(host="127.0.0.1", port=11111)

# 連接API
md.connect()

# 獲取K線數據
df = md.get_kline_data(
    code="HK.00700",
    ktype=KLType.K_DAY,
    start="2024-01-01",
    end="2024-12-31"
)

# 獲取實時報價
quote = md.get_stock_quote("HK.00700")

# 訂閱實時行情
md.subscribe_realtime("HK.00700", callback=lambda x: print(x))
```

## 運行測試

### Windows PowerShell

```powershell
# 進入項目目錄
cd C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

# 運行所有測試
python -m pytest tests/test_indicators.py -v

# 或使用unittest
python tests/test_indicators.py

# 運行特定測試類
python -m unittest tests.test_indicators.TestTechnicalIndicators -v

# 運行特定測試方法
python -m unittest tests.test_indicators.TestTechnicalIndicators.test_macd_calculation -v
```

### 測試覆蓋範圍

- ✅ MACD計算測試
- ✅ 布林帶計算測試
- ✅ EMA多週期計算測試
- ✅ VMACD量價計算測試
- ✅ RSI相對強弱指標測試
- ✅ 成交量分析測試
- ✅ 數據緩存測試
- ✅ 富途API接口測試
- ✅ 觀察列表管理測試

## 類型註解

所有函數和類都包含完整的Python類型註解，支持IDE自動補全和類型檢查。

## 注意事項

1. 使用富途API前需要啟動OpenD服務
2. 未安裝futu-api時會返回模擬數據
3. 緩存默認有效期為24小時
4. 所有計算使用pandas實現，無需ta-lib
