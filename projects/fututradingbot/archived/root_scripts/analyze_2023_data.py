"""
分析2023年TQQQ數據，檢查Z-Score分佈和交易機會
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 獲取數據
print("📊 正在獲取 TQQQ 2023年數據...")
ticker = yf.Ticker('TQQQ')
df = ticker.history(period='3y')
df.columns = [col.lower().replace(' ', '_') for col in df.columns]
df = df.reset_index()
date_col = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()][0]
df = df.rename(columns={date_col: 'timestamp'})
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.set_index('timestamp')

# 過濾2023年
df_2023 = df[(df.index >= '2023-03-27') & (df.index <= '2024-03-27')].copy()

# 計算Z-Score
lookback = 60
df_2023['price_ma'] = df_2023['close'].rolling(window=lookback).mean()
df_2023['price_std'] = df_2023['close'].rolling(window=lookback).std()
df_2023['zscore'] = (df_2023['close'] - df_2023['price_ma']) / df_2023['price_std']

# 計算RSI
delta = df_2023['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df_2023['rsi'] = 100 - (100 / (1 + rs))

# 計算200日均線
df_2023['ma200'] = df_2023['close'].rolling(window=200).mean()
df_2023['market_state'] = np.where(
    df_2023['close'] > df_2023['ma200'] * 1.05, 'bull',
    np.where(df_2023['close'] < df_2023['ma200'] * 0.95, 'bear', 'sideways')
)

# 計算成交量均線
df_2023['volume_ma'] = df_2023['volume'].rolling(window=20).mean()

# 分析Z-Score分佈
print("\n" + "="*60)
print("📊 2023年 TQQQ Z-Score 分析")
print("="*60)
print(f"數據點數: {len(df_2023)}")
print(f"\nZ-Score 統計:")
print(f"  最小值: {df_2023['zscore'].min():.2f}")
print(f"  最大值: {df_2023['zscore'].max():.2f}")
print(f"  平均值: {df_2023['zscore'].mean():.2f}")
print(f"  標準差: {df_2023['zscore'].std():.2f}")

# 檢查不同閾值下的觸發次數
thresholds = [1.0, 1.5, 2.0, 2.5, 3.0]
print(f"\n📈 Z-Score 觸發次數分析:")
for threshold in thresholds:
    long_signals = (df_2023['zscore'] < -threshold).sum()
    short_signals = (df_2023['zscore'] > threshold).sum()
    print(f"  閾值 ±{threshold}: 做多信號 {long_signals} 次, 做空信號 {short_signals} 次")

# 檢查RSI條件
print(f"\n📈 RSI 觸發次數分析:")
print(f"  RSI < 35 (超賣): {(df_2023['rsi'] < 35).sum()} 次")
print(f"  RSI > 65 (超買): {(df_2023['rsi'] > 65).sum()} 次")

# 檢查市場狀態
print(f"\n📈 市場狀態分佈:")
print(df_2023['market_state'].value_counts())

# 檢查組合條件
print(f"\n📈 組合條件分析 (Z-Score ±2.0 + RSI):")
long_combo = ((df_2023['zscore'] < -2.0) & (df_2023['rsi'] < 35)).sum()
short_combo = ((df_2023['zscore'] > 2.0) & (df_2023['rsi'] > 65)).sum()
print(f"  做多條件 (Z<-2.0 & RSI<35): {long_combo} 次")
print(f"  做空條件 (Z>2.0 & RSI>65): {short_combo} 次")

# 檢查放寬條件
print(f"\n📈 放寬條件分析 (Z-Score ±1.5 + RSI):")
long_combo_15 = ((df_2023['zscore'] < -1.5) & (df_2023['rsi'] < 40)).sum()
short_combo_15 = ((df_2023['zscore'] > 1.5) & (df_2023['rsi'] > 60)).sum()
print(f"  做多條件 (Z<-1.5 & RSI<40): {long_combo_15} 次")
print(f"  做空條件 (Z>1.5 & RSI>60): {short_combo_15} 次")

# 檢查僅Z-Score條件
print(f"\n📈 僅Z-Score條件 (無RSI限制):")
long_zonly = (df_2023['zscore'] < -2.0).sum()
short_zonly = (df_2023['zscore'] > 2.0).sum()
print(f"  做多條件 (Z<-2.0): {long_zonly} 次")
print(f"  做空條件 (Z>2.0): {short_zonly} 次")

# 輸出樣本數據
print(f"\n📊 樣本數據 (最後10天):")
print(df_2023[['close', 'zscore', 'rsi', 'market_state']].tail(10))

print("\n" + "="*60)
print("💡 建議:")
print("="*60)
if long_combo == 0 and short_combo == 0:
    print("⚠️  當前策略條件過於嚴格，建議:")
    print("   1. 降低Z-Score閾值至 ±1.5")
    print("   2. 放寬RSI條件至 <40/>60")
    print("   3. 或移除RSI條件，僅使用Z-Score")
else:
    print("✅ 策略條件可以觸發交易")
