import yfinance as yf
import pandas as pd
import numpy as np

# 獲取2025年數據
ticker = yf.Ticker('TQQQ')
df = ticker.history(start='2024-10-01', end='2026-01-01', interval='1d')
df.index = df.index.tz_localize(None)
df.columns = [c.lower().replace(' ', '_') for c in df.columns]

# 計算Z-Score
lookback = 60
df['price_ma'] = df['close'].rolling(window=lookback).mean()
df['price_std'] = df['close'].rolling(window=lookback).std()
df['zscore'] = (df['close'] - df['price_ma']) / df['price_std']

# 計算RSI
rsi_period = 14
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
rs = gain / loss
df['rsi'] = 100 - (100 / (1 + rs))

# 計算MACD
exp1 = df['close'].ewm(span=12, adjust=False).mean()
exp2 = df['close'].ewm(span=26, adjust=False).mean()
df['macd'] = exp1 - exp2
df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
df['macd_hist'] = df['macd'] - df['macd_signal']

# 計算200日均線
df['ma200'] = df['close'].rolling(window=200).mean()

# 過濾2025年數據
df_2025 = df[df.index >= '2025-01-01']

print('=== TQQQ 2025年數據分析 ===')
print(f'數據點數: {len(df_2025)}')

print('\nZ-Score統計:')
zscore_min = df_2025['zscore'].min()
zscore_max = df_2025['zscore'].max()
print(f'  最小值: {zscore_min:.2f}')
print(f'  最大值: {zscore_max:.2f}')
print(f'  平均值: {df_2025["zscore"].mean():.2f}')
print(f'  標準差: {df_2025["zscore"].std():.2f}')
print(f'  <-2.0 次數: {(df_2025["zscore"] < -2.0).sum()}')
print(f'  >2.0 次數: {(df_2025["zscore"] > 2.0).sum()}')

print('\nRSI統計:')
rsi_min = df_2025['rsi'].min()
rsi_max = df_2025['rsi'].max()
print(f'  最小值: {rsi_min:.2f}')
print(f'  最大值: {rsi_max:.2f}')
print(f'  <30 次數: {(df_2025["rsi"] < 30).sum()}')
print(f'  >70 次數: {(df_2025["rsi"] > 70).sum()}')

print('\nMACD Hist統計:')
macd_min = df_2025['macd_hist'].min()
macd_max = df_2025['macd_hist'].max()
print(f'  最小值: {macd_min:.4f}')
print(f'  最大值: {macd_max:.4f}')

# 檢查進場條件
df_2025['prev_macd_hist'] = df_2025['macd_hist'].shift(1)

# 做多條件: Z-Score < -2.0 + RSI < 30 + MACD金叉
long_condition = (
    (df_2025['zscore'] < -2.0) & 
    (df_2025['rsi'] < 30) & 
    (df_2025['prev_macd_hist'] < 0) & 
    (df_2025['macd_hist'] >= 0)
)

# 做空條件: Z-Score > 2.0 + RSI > 70 + MACD死叉
short_condition = (
    (df_2025['zscore'] > 2.0) & 
    (df_2025['rsi'] > 70) & 
    (df_2025['prev_macd_hist'] > 0) & 
    (df_2025['macd_hist'] <= 0)
)

print('\n進場信號統計:')
print(f'  做多信號次數: {long_condition.sum()}')
print(f'  做空信號次數: {short_condition.sum()}')

# 顯示有信號的日期
if long_condition.sum() > 0:
    print('\n做多信號日期:')
    for date in df_2025[long_condition].index:
        row = df_2025.loc[date]
        print(f'  {date.strftime("%Y-%m-%d")}: Z={row["zscore"]:.2f}, RSI={row["rsi"]:.1f}')

if short_condition.sum() > 0:
    print('\n做空信號日期:')
    for date in df_2025[short_condition].index:
        row = df_2025.loc[date]
        print(f'  {date.strftime("%Y-%m-%d")}: Z={row["zscore"]:.2f}, RSI={row["rsi"]:.1f}')
