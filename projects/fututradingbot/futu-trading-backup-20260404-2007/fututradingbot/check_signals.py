import yfinance as yf
import pandas as pd
import numpy as np

# 獲取數據
ticker = yf.Ticker('TQQQ')
df = ticker.history(period='5y')
df.columns = [col.lower().replace(' ', '_') for col in df.columns]
df = df.reset_index()
df = df.rename(columns={'date': 'timestamp'})
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')

# 計算指標
lookback = 60
rsi_period = 14

df['price_ma'] = df['close'].rolling(window=lookback).mean()
df['price_std'] = df['close'].rolling(window=lookback).std()
df['zscore'] = (df['close'] - df['price_ma']) / df['price_std']

delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
rs = gain / loss
df['rsi'] = 100 - (100 / (1 + rs))

exp1 = df['close'].ewm(span=12, adjust=False).mean()
exp2 = df['close'].ewm(span=26, adjust=False).mean()
df['macd'] = exp1 - exp2
df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
df['macd_hist'] = df['macd'] - df['macd_signal']

# 2024年數據
df_2024 = df[df.index.year == 2024].copy()
print(f'2024年數據點: {len(df_2024)}')

# 檢查Z-Score極值
zscore_min = df_2024['zscore'].min()
zscore_max = df_2024['zscore'].max()
print(f'Z-Score範圍: {zscore_min:.2f} ~ {zscore_max:.2f}')

zscore_neg2 = (df_2024['zscore'] < -2.0).sum()
zscore_pos2 = (df_2024['zscore'] > 2.0).sum()
print(f'Z<-2.0 天數: {zscore_neg2}')
print(f'Z>2.0 天數: {zscore_pos2}')

# 檢查RSI極值
rsi_min = df_2024['rsi'].min()
rsi_max = df_2024['rsi'].max()
print(f'RSI範圍: {rsi_min:.2f} ~ {rsi_max:.2f}')

rsi_under30 = (df_2024['rsi'] < 30).sum()
rsi_over70 = (df_2024['rsi'] > 70).sum()
print(f'RSI<30 天數: {rsi_under30}')
print(f'RSI>70 天數: {rsi_over70}')

# 檢查同時滿足條件的天數
long_condition = (df_2024['zscore'] < -2.0) & (df_2024['rsi'] < 30)
short_condition = (df_2024['zscore'] > 2.0) & (df_2024['rsi'] > 70)
print(f'做多條件滿足: {long_condition.sum()} 天')
print(f'做空條件滿足: {short_condition.sum()} 天')

# 顯示具體日期
if long_condition.sum() > 0:
    print(f'\n做多信號日期:')
    for d in df_2024[long_condition].index:
        print(f'  {d}')
        
if short_condition.sum() > 0:
    print(f'\n做空信號日期:')
    for d in df_2024[short_condition].index:
        print(f'  {d}')
