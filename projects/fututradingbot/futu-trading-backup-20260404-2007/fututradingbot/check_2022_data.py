import yfinance as yf
import pandas as pd
import numpy as np

# 獲取2022年數據
ticker = yf.Ticker('TQQQ')
df = ticker.history(start='2022-01-01', end='2022-12-31')
df.columns = [col.lower().replace(' ', '_') for col in df.columns]

# 計算指標
lookback = 60
df['price_ma'] = df['close'].rolling(window=lookback).mean()
df['price_std'] = df['close'].rolling(window=lookback).std()
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

print('=== 2022年 TQQQ 數據分析 ===')
print(f'數據點數: {len(df)}')
print(f'\nZ-Score 統計:')
zscore_min = df['zscore'].min()
zscore_max = df['zscore'].max()
print(f'  最小值: {zscore_min:.2f}')
print(f'  最大值: {zscore_max:.2f}')
print(f'  絕對值>1.5的天數: {(abs(df["zscore"]) > 1.5).sum()}')
print(f'  絕對值>2.0的天數: {(abs(df["zscore"]) > 2.0).sum()}')

print(f'\nRSI 統計:')
rsi_min = df['rsi'].min()
rsi_max = df['rsi'].max()
print(f'  最小值: {rsi_min:.2f}')
print(f'  最大值: {rsi_max:.2f}')
print(f'  <35的天數: {(df["rsi"] < 35).sum()}')
print(f'  >65的天數: {(df["rsi"] > 65).sum()}')

# 檢查同時滿足條件的天數
df['macd_golden_cross'] = (df['macd_hist'].shift(1) < 0) & (df['macd_hist'] >= 0)
df['macd_death_cross'] = (df['macd_hist'].shift(1) > 0) & (df['macd_hist'] <= 0)

buy_condition = (df['zscore'] < -1.5) & (df['rsi'] < 35) & df['macd_golden_cross']
sell_condition = (df['zscore'] > 1.5) & (df['rsi'] > 65) & df['macd_death_cross']

print(f'\n信號統計:')
print(f'  MACD金叉天數: {df["macd_golden_cross"].sum()}')
print(f'  MACD死叉天數: {df["macd_death_cross"].sum()}')
print(f'  做多信號天數: {buy_condition.sum()}')
print(f'  做空信號天數: {sell_condition.sum()}')

# 顯示具體信號日期
if buy_condition.sum() > 0:
    print(f'\n做多信號日期:')
    for date in df[buy_condition].index:
        print(f'  {date.strftime("%Y-%m-%d")}')
if sell_condition.sum() > 0:
    print(f'\n做空信號日期:')
    for date in df[sell_condition].index:
        print(f'  {date.strftime("%Y-%m-%d")}')
