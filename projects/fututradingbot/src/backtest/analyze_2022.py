import yfinance as yf
import pandas as pd
import numpy as np

# 獲取數據
ticker = yf.Ticker('TQQQ')
df = ticker.history(period='5y')
df.columns = [col.lower().replace(' ', '_') for col in df.columns]
df = df.reset_index()
date_col = [c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()][0]
df = df.rename(columns={date_col: 'timestamp'})
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')

# 篩選2022年數據
df_2022 = df[(df.index >= '2022-03-27') & (df.index <= '2023-03-27')].copy()

# 計算指標
lookback = 60
rsi_period = 14

df_2022['price_ma'] = df_2022['close'].rolling(window=lookback).mean()
df_2022['price_std'] = df_2022['close'].rolling(window=lookback).std()
df_2022['zscore'] = (df_2022['close'] - df_2022['price_ma']) / df_2022['price_std']

delta = df_2022['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
rs = gain / loss
df_2022['rsi'] = 100 - (100 / (1 + rs))

exp1 = df_2022['close'].ewm(span=12, adjust=False).mean()
exp2 = df_2022['close'].ewm(span=26, adjust=False).mean()
df_2022['macd'] = exp1 - exp2
df_2022['macd_signal'] = df_2022['macd'].ewm(span=9, adjust=False).mean()
df_2022['macd_hist'] = df_2022['macd'] - df_2022['macd_signal']
df_2022['macd_hist_prev'] = df_2022['macd_hist'].shift(1)

# 檢查條件
print('=== 2022年度 TQQQ 數據分析 ===')
print(f'總數據點: {len(df_2022)}')
print(f'\nZ-Score 統計:')
zscore_min = df_2022['zscore'].min()
zscore_max = df_2022['zscore'].max()
zscore_lt_neg2 = (df_2022['zscore'] < -2.0).sum()
zscore_gt_2 = (df_2022['zscore'] > 2.0).sum()
print(f'  最小值: {zscore_min:.2f}')
print(f'  最大值: {zscore_max:.2f}')
print(f'  Z-Score < -2.0 的天數: {zscore_lt_neg2}')
print(f'  Z-Score > 2.0 的天數: {zscore_gt_2}')

print(f'\nRSI 統計:')
rsi_min = df_2022['rsi'].min()
rsi_max = df_2022['rsi'].max()
rsi_lt_30 = (df_2022['rsi'] < 30).sum()
rsi_gt_70 = (df_2022['rsi'] > 70).sum()
print(f'  最小值: {rsi_min:.2f}')
print(f'  最大值: {rsi_max:.2f}')
print(f'  RSI < 30 的天數: {rsi_lt_30}')
print(f'  RSI > 70 的天數: {rsi_gt_70}')

# 檢查MACD金叉/死叉
df_2022['macd_golden_cross'] = (df_2022['macd_hist_prev'] < 0) & (df_2022['macd_hist'] >= 0)
df_2022['macd_death_cross'] = (df_2022['macd_hist_prev'] > 0) & (df_2022['macd_hist'] <= 0)

print(f'\nMACD 統計:')
golden_cross = df_2022['macd_golden_cross'].sum()
death_cross = df_2022['macd_death_cross'].sum()
print(f'  金叉天數: {golden_cross}')
print(f'  死叉天數: {death_cross}')

# 檢查同時滿足條件的天數
long_condition = (df_2022['zscore'] < -2.0) & (df_2022['rsi'] < 30) & df_2022['macd_golden_cross']
short_condition = (df_2022['zscore'] > 2.0) & (df_2022['rsi'] > 70) & df_2022['macd_death_cross']

long_count = long_condition.sum()
short_count = short_condition.sum()

print(f'\n最終進場條件:')
print(f'  做多條件滿足天數: {long_count}')
print(f'  做空條件滿足天數: {short_count}')

# 顯示滿足條件的日期
if long_count > 0:
    print(f'\n  做多信號日期:')
    for date in df_2022[long_condition].index:
        print(f'    {date.strftime("%Y-%m-%d")}')
        
if short_count > 0:
    print(f'\n  做空信號日期:')
    for date in df_2022[short_condition].index:
        print(f'    {date.strftime("%Y-%m-%d")}')

# 檢查各條件組合
print(f'\n條件組合分析:')
print(f'  Z-Score < -2.0 且 RSI < 30: {((df_2022["zscore"] < -2.0) & (df_2022["rsi"] < 30)).sum()}')
print(f'  Z-Score > 2.0 且 RSI > 70: {((df_2022["zscore"] > 2.0) & (df_2022["rsi"] > 70)).sum()}')
print(f'  Z-Score < -2.0 且 MACD金叉: {((df_2022["zscore"] < -2.0) & df_2022["macd_golden_cross"]).sum()}')
print(f'  Z-Score > 2.0 且 MACD死叉: {((df_2022["zscore"] > 2.0) & df_2022["macd_death_cross"]).sum()}')
