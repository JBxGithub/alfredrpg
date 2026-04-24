import yfinance as yf
import pandas as pd
import numpy as np

# 獲取2023年TQQQ數據
ticker = yf.Ticker('TQQQ')
df = ticker.history(period='5y')
df.columns = [col.lower().replace(' ', '_') for col in df.columns]

# 計算指標
df['price_ma'] = df['close'].rolling(window=60).mean()
df['price_std'] = df['close'].rolling(window=60).std()
df['zscore'] = (df['close'] - df['price_ma']) / df['price_std']

# RSI
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['rsi'] = 100 - (100 / (1 + rs))

# MACD
exp1 = df['close'].ewm(span=12, adjust=False).mean()
exp2 = df['close'].ewm(span=26, adjust=False).mean()
df['macd'] = exp1 - exp2
df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
df['macd_hist'] = df['macd'] - df['macd_signal']
df['macd_hist_prev'] = df['macd_hist'].shift(1)

# 過濾2023年
df_2023 = df[(df.index >= '2023-01-01') & (df.index <= '2023-12-31')]

print('=== 2023年TQQQ數據分析 ===')
print(f'總交易日: {len(df_2023)}')
print(f"價格範圍: ${df_2023['close'].min():.2f} - ${df_2023['close'].max():.2f}")
print()

# Z-Score統計
print('=== Z-Score統計 ===')
print(f"Z-Score < -2.0 的天數: {(df_2023['zscore'] < -2.0).sum()}")
print(f"Z-Score > 2.0 的天數: {(df_2023['zscore'] > 2.0).sum()}")
print(f"Z-Score範圍: {df_2023['zscore'].min():.2f} ~ {df_2023['zscore'].max():.2f}")
print()

# RSI統計
print('=== RSI統計 ===')
print(f"RSI < 30 的天數: {(df_2023['rsi'] < 30).sum()}")
print(f"RSI > 70 的天數: {(df_2023['rsi'] > 70).sum()}")
print(f"RSI範圍: {df_2023['rsi'].min():.2f} ~ {df_2023['rsi'].max():.2f}")
print()

# MACD金叉/死叉統計
golden_cross = (df_2023['macd_hist_prev'] < 0) & (df_2023['macd_hist'] >= 0)
death_cross = (df_2023['macd_hist_prev'] > 0) & (df_2023['macd_hist'] <= 0)
print('=== MACD交叉統計 ===')
print(f'MACD金叉天數: {golden_cross.sum()}')
print(f'MACD死叉天數: {death_cross.sum()}')
print()

# 組合條件統計
long_condition = (df_2023['zscore'] < -2.0) & (df_2023['rsi'] < 30) & golden_cross
short_condition = (df_2023['zscore'] > 2.0) & (df_2023['rsi'] > 70) & death_cross
print('=== 組合進場條件統計 ===')
print(f'做多條件滿足天數: {long_condition.sum()}')
print(f'做空條件滿足天數: {short_condition.sum()}')
