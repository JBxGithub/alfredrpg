import yfinance as yf
import pandas as pd
import numpy as np

print('正在下載 TQQQ 歷史數據...')
tqqq = yf.download('TQQQ', start='2023-01-01', end='2026-01-01', progress=False)
print(f'數據下載完成: {len(tqqq)} 個交易日')

# 新參數
ZSCORE_THRESHOLD = 1.6
RSI_OVERBOUGHT = 60
RSI_OVERSOLD = 40
RSI_MONTHLY = 70

# 計算指標
def calculate_zscore(prices, lookback=60):
    mean = prices.rolling(window=lookback).mean()
    std = prices.rolling(window=lookback).std()
    return (prices - mean) / std

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 準備數據 - 處理MultiIndex
tqqq.columns = ['_'.join(col).strip() if col[1] else col[0] for col in tqqq.columns.values]
close_col = [c for c in tqqq.columns if 'Close' in c][0]
vol_col = [c for c in tqqq.columns if 'Volume' in c][0]

tqqq['zscore'] = calculate_zscore(tqqq[close_col])
tqqq['rsi_daily'] = calculate_rsi(tqqq[close_col], 14)
tqqq['rsi_monthly'] = calculate_rsi(tqqq[close_col], 30)
tqqq['volume_ma20'] = tqqq[vol_col].rolling(window=20).mean()

# 簡化回測
trades = []
position = None

for i in range(60, len(tqqq)):
    row = tqqq.iloc[i]
    
    if pd.isna(row['zscore']) or pd.isna(row['rsi_daily']) or pd.isna(row['rsi_monthly']):
        continue
    
    # 進場條件
    if position is None:
        volume_ok = row[vol_col] > row['volume_ma20'] * 0.5
        
        # 做多
        if row['zscore'] < -ZSCORE_THRESHOLD and row['rsi_daily'] < RSI_OVERSOLD and row['rsi_monthly'] < RSI_MONTHLY and volume_ok:
            position = {'type': 'long', 'entry': row[close_col], 'time': i}
        
        # 做空
        elif row['zscore'] > ZSCORE_THRESHOLD and row['rsi_daily'] > RSI_OVERBOUGHT and row['rsi_monthly'] > RSI_MONTHLY and volume_ok:
            position = {'type': 'short', 'entry': row[close_col], 'time': i}
    
    # 出場條件
    elif position:
        days_held = i - position['time']
        
        if position['type'] == 'long':
            pnl = (row[close_col] - position['entry']) / position['entry']
            exit_trade = False
            if pnl >= 0.05: exit_trade = True
            elif pnl <= -0.03: exit_trade = True
            elif row['zscore'] > -0.5: exit_trade = True
            elif days_held >= 3: exit_trade = True
            
            if exit_trade:
                trades.append({'dir': 'long', 'pnl': pnl})
                position = None
        
        else:  # short
            pnl = (position['entry'] - row[close_col]) / position['entry']
            exit_trade = False
            if pnl >= 0.05: exit_trade = True
            elif pnl <= -0.03: exit_trade = True
            elif row['zscore'] < 0.5: exit_trade = True
            elif days_held >= 3: exit_trade = True
            
            if exit_trade:
                trades.append({'dir': 'short', 'pnl': pnl})
                position = None

# 統計
if trades:
    df = pd.DataFrame(trades)
    longs = df[df['dir'] == 'long']
    shorts = df[df['dir'] == 'short']
    
    print('')
    print('=== 新參數回測結果 (RSI 60/40 + 月線70) ===')
    print(f'總交易: {len(df)} 筆')
    print(f'做多: {len(longs)} 筆, 勝率: {(longs.pnl > 0).mean()*100:.1f}%')
    print(f'做空: {len(shorts)} 筆, 勝率: {(shorts.pnl > 0).mean()*100:.1f}%')
    print(f'總勝率: {(df.pnl > 0).mean()*100:.1f}%')
    print(f'平均盈虧: {df.pnl.mean()*100:.2f}%')
    print(f'總回報: {df.pnl.sum()*100:.1f}%')
    
    # 保存結果
    df.to_csv('backtest_result_new_params.csv', index=False)
    print('')
    print('結果已保存至 backtest_result_new_params.csv')
else:
    print('無交易記錄')
