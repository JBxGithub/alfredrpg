# 富途交易機器人測試報告

## 測試執行方法

### 方法1: 使用 pytest (推薦)

```powershell
# 進入項目目錄
cd C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

# 安裝 pytest
pip install pytest

# 運行所有測試
pytest tests/test_indicators.py -v

# 運行特定測試類
pytest tests/test_indicators.py::TestTechnicalIndicators -v

# 運行特定測試方法
pytest tests/test_indicators.py::TestTechnicalIndicators::test_macd_calculation -v

# 生成測試覆蓋率報告
pytest tests/test_indicators.py --cov=src --cov-report=html
```

### 方法2: 使用 unittest

```powershell
# 進入項目目錄
cd C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

# 運行所有測試
python tests/test_indicators.py

# 或使用模塊方式
python -m unittest tests.test_indicators -v

# 運行特定測試類
python -m unittest tests.test_indicators.TestTechnicalIndicators -v

# 運行特定測試方法
python -m unittest tests.test_indicators.TestTechnicalIndicators.test_macd_calculation -v
```

### 方法3: 使用 Python 交互式測試

```powershell
# 進入項目目錄
cd C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot

# 啟動 Python
python

# 在 Python 中運行測試
>>> import sys
>>> sys.path.insert(0, 'src')
>>> from tests.test_indicators import run_tests
>>> run_tests()
```

## 測試模組說明

### TestTechnicalIndicators - 技術指標測試

| 測試方法 | 說明 |
|---------|------|
| test_macd_calculation | 測試MACD指標計算 (DIF, DEA, MACD柱) |
| test_boll_calculation | 測試布林帶計算 (上軌、中軌、下軌、帶寬) |
| test_ema_calculation | 測試EMA多週期計算 (5, 10, 20, 60日) |
| test_vmacd_calculation | 測試量價MACD計算 |
| test_rsi_calculation | 測試RSI相對強弱指標 (6, 12, 24日) |
| test_volume_analysis | 測試成交量分析 (均量、量比、OBV) |
| test_calculate_all | 測試計算所有指標 |
| test_signal_summary | 測試信號摘要功能 |
| test_data_validation | 測試數據驗證 |
| test_support_resistance | 測試支撐位/阻力位計算 |
| test_atr_calculation | 測試ATR平均真實波幅 |

### TestDataCache - 數據緩存測試

| 測試方法 | 說明 |
|---------|------|
| test_cache_set_get | 測試緩存設置和獲取 |
| test_cache_expiration | 測試緩存過期機制 |
| test_cache_clear | 測試清除緩存 |
| test_cache_info | 測試緩存信息獲取 |

### TestFutuMarketData - 富途行情數據測試

| 測試方法 | 說明 |
|---------|------|
| test_mock_kline_data_generation | 測試模擬K線數據生成 |
| test_kline_data_with_cache | 測試帶緩存的K線數據獲取 |
| test_different_kline_types | 測試不同K線類型 (1分鐘到月線) |

### TestMarketDataManager - 市場數據管理器測試

| 測試方法 | 說明 |
|---------|------|
| test_watchlist_management | 測試觀察列表管理 |
| test_fetch_watchlist_data | 測試獲取觀察列表數據 |
| test_export_data | 測試數據導出功能 |

## 預期測試結果

```
test_macd_calculation (tests.test_indicators.TestTechnicalIndicators) ... ok
test_boll_calculation (tests.test_indicators.TestTechnicalIndicators) ... ok
test_ema_calculation (tests.test_indicators.TestTechnicalIndicators) ... ok
test_vmacd_calculation (tests.test_indicators.TestTechnicalIndicators) ... ok
test_rsi_calculation (tests.test_indicators.TestTechnicalIndicators) ... ok
test_volume_analysis (tests.test_indicators.TestTechnicalIndicators) ... ok
test_calculate_all (tests.test_indicators.TestTechnicalIndicators) ... ok
test_signal_summary (tests.test_indicators.TestTechnicalIndicators) ... ok
test_data_validation (tests.test_indicators.TestTechnicalIndicators) ... ok
test_support_resistance (tests.test_indicators.TestTechnicalIndicators) ... ok
test_atr_calculation (tests.test_indicators.TestTechnicalIndicators) ... ok
test_cache_set_get (tests.test_indicators.TestDataCache) ... ok
test_cache_expiration (tests.test_indicators.TestDataCache) ... ok
test_cache_clear (tests.test_indicators.TestDataCache) ... ok
test_cache_info (tests.test_indicators.TestDataCache) ... ok
test_mock_kline_data_generation (tests.test_indicators.TestFutuMarketData) ... ok
test_kline_data_with_cache (tests.test_indicators.TestFutuMarketData) ... ok
test_different_kline_types (tests.test_indicators.TestFutuMarketData) ... ok
test_watchlist_management (tests.test_indicators.TestMarketDataManager) ... ok
test_fetch_watchlist_data (tests.test_indicators.TestMarketDataManager) ... ok
test_export_data (tests.test_indicators.TestMarketDataManager) ... ok

----------------------------------------------------------------------
Ran 22 tests in X.XXXs

OK
```

## 快速驗證腳本

創建 `quick_test.py` 進行快速驗證：

```python
"""快速驗證腳本"""
import sys
sys.path.insert(0, 'src')

import pandas as pd
import numpy as np
from datetime import datetime

# 生成測試數據
np.random.seed(42)
n = 100
dates = pd.date_range(end=datetime.now(), periods=n, freq='D')
returns = np.random.normal(0.001, 0.02, n)
prices = 100 * np.exp(np.cumsum(returns))

df = pd.DataFrame({
    'timestamp': dates,
    'open': prices * (1 + np.random.normal(0, 0.005, n)),
    'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n))),
    'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n))),
    'close': prices,
    'volume': np.random.randint(100000, 10000000, n)
})
df['high'] = df[['open', 'high', 'close']].max(axis=1)
df['low'] = df[['open', 'low', 'close']].min(axis=1)

# 測試技術指標
from indicators.technical import TechnicalIndicators

ind = TechnicalIndicators(df)
print("✓ TechnicalIndicators initialized")

macd = ind.calculate_macd()
print(f"✓ MACD calculated: DIF={macd.dif.iloc[-1]:.4f}")

boll = ind.calculate_boll()
print(f"✓ BOLL calculated: Upper={boll.upper.iloc[-1]:.2f}")

ema = ind.calculate_ema()
print(f"✓ EMA calculated: EMA5={ema.ema_5.iloc[-1]:.2f}")

vmacd = ind.calculate_vmacd()
print(f"✓ VMACD calculated: DIF={vmacd.dif.iloc[-1]:.4f}")

rsi = ind.calculate_rsi()
print(f"✓ RSI calculated: RSI6={rsi.rsi_6.iloc[-1]:.2f}")

vol = ind.calculate_volume_analysis()
print(f"✓ Volume analysis calculated: OBV={vol.obv.iloc[-1]:.0f}")

summary = ind.get_signal_summary()
print(f"✓ Signal summary: {summary}")

# 測試數據獲取
from data.market_data import FutuMarketData, KLType

md = FutuMarketData(cache_dir="test_cache")
print("✓ FutuMarketData initialized")

df_kline = md.get_kline_data("HK.00700", ktype=KLType.K_DAY, num=20)
print(f"✓ K-line data retrieved: {len(df_kline)} rows")

print("\n✅ All tests passed!")
```

運行快速驗證：
```powershell
cd C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot
python quick_test.py
```
