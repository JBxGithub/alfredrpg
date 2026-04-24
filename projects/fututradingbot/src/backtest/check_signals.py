import yfinance as yf
import pandas as pd
import numpy as np

# 獲取TQQQ數據
ticker = yf.Ticker('TQQQ')
df = ticker.history(period='3y')
df.columns = [col.lower().replace(' ', '_') for col in df.columns]

# 過濾2023年
df_2023 = df[(df.index >= '2023-01-01') & (df.index <= '2023-12-31')]
print(f'2023年數據點數: {len(df_2023)}')
print(f'日期範圍: {df_2023.index[0]} ~ {df_2023.index[-1]}')
print()

# 計算指標
lookback = 60
rsi_period = 14

df_2023['price_ma'] = df_2023['close'].rolling(window=lookback).mean()
df_2023['price_std'] = df_2023['close'].rolling(window=lookback).std()
df_2023['zscore'] = (df_2023['close'] - df_2023['price_ma']) / df_2023['price_std']

delta = df_2023['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
rs = gain / loss
df_2023['rsi'] = 100 - (100 / (1 + rs))

# 計算MACD
exp1 = df_2023['close'].ewm(span=12, adjust=False).mean()
exp2 = df_2023['close'].ewm(span=26, adjust=False).mean()
df_2023['macd'] = exp1 - exp2
df_2023['macd_signal'] = df_2023['macd'].ewm(span=9, adjust=False).mean()
df_2023['macd_hist'] = df_2023['macd'] - df_2023['macd_signal']
df_2023['prev_macd_hist'] = df_2023['macd_hist'].shift(1)

# 檢查Z-Score和RSI範圍
z_min = df_2023['zscore'].min()
z_max = df_2023['zscore'].max()
z_below = (df_2023['zscore'] < -1.5).sum()
z_above = (df_2023['zscore'] > 1.5).sum()

print('Z-Score統計:')
print(f'  最小值: {z_min:.2f}')
print(f'  最大值: {z_max:.2f}')
print(f'  小於-1.5的天數: {z_below}')
print(f'  大於1.5的天數: {z_above}')
print()

rsi_min = df_2023['rsi'].min()
rsi_max = df_2023['rsi'].max()
rsi_below = (df_2023['rsi'] < 35).sum()
rsi_above = (df_2023['rsi'] > 65).sum()

print('RSI統計:')
print(f'  最小值: {rsi_min:.2f}')
print(f'  最大值: {rsi_max:.2f}')
print(f'  小於35的天數: {rsi_below}')
print(f'  大於65的天數: {rsi_above}')
print()

# 檢查MACD金叉/死叉
golden_cross = (df_2023['prev_macd_hist'] < 0) & (df_2023['macd_hist'] >= 0)
death_cross = (df_2023['prev_macd_hist'] > 0) & (df_2023['macd_hist'] <= 0)
print(f'MACD金叉次數: {golden_cross.sum()}')
print(f'MACD死叉次數: {death_cross.sum()}')
print()

# 檢查組合條件
long_condition = (df_2023['zscore'] < -1.5) & (df_2023['rsi'] < 35) & golden_cross
short_condition = (df_2023['zscore'] > 1.5) & (df_2023['rsi'] > 65) & death_cross
print(f'做多信號次數(Z<-1.5 & RSI<35 & MACD金叉): {long_condition.sum()}')
print(f'做空信號次數(Z>1.5 & RSI>65 & MACD死叉): {short_condition.sum()}')

# 顯示有信號的日期
if long_condition.sum() > 0:
    print('\n做多信號日期:')
    for date in df_2023[long_condition].index:
        print(f'  {date.strftime("%Y-%m-%d")}')

if short_condition.sum() > 0:
    print('\n做空信號日期:')
    for date in df_2023[short_condition].index:
        print(f'  {date.strftime("%Y-%m-%d")}')
