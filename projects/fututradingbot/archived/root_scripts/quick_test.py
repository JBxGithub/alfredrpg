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
