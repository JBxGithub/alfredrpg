import pandas as pd
import numpy as np

# 讀取數據
qqq = pd.read_csv('qqq_history.csv')
tqqq = pd.read_csv('tqqq_history.csv')

# 合併數據
data = pd.merge(qqq[['time_key', 'close']], tqqq[['time_key', 'close']], 
                on='time_key', suffixes=('_QQQ', '_TQQQ'))

# 計算理論 TQQQ 價格（簡化模型：TQQQ = (QQQ/QQQ基準)³ × TQQQ基準）
qqq_baseline = data['close_QQQ'].iloc[0]
tqqq_baseline = data['close_TQQQ'].iloc[0]

data['theoretical_TQQQ'] = ((data['close_QQQ'] / qqq_baseline) ** 3) * tqqq_baseline

# 計算價差
data['spread'] = data['close_TQQQ'] - data['theoretical_TQQQ']
data['spread_ratio'] = data['spread'] / data['theoretical_TQQQ'] * 100

# 統計分析
print('=== QQQ/TQQQ 價差分析 ===')
print(f'數據天數: {len(data)}')
print(f'\n價差比率統計:')
print(f'  平均: {data["spread_ratio"].mean():.4f}%')
print(f'  標準差: {data["spread_ratio"].std():.4f}%')
print(f'  最大: {data["spread_ratio"].max():.4f}%')
print(f'  最小: {data["spread_ratio"].min():.4f}%')
print(f'  絕對值平均: {data["spread_ratio"].abs().mean():.4f}%')

# 計算不同閾值下的交易次數
thresholds = [0.5, 1.0, 1.5, 2.0, 3.0]
print(f'\n=== 不同閾值下的交易機會 ===')
for threshold in thresholds:
    signals = data[data['spread_ratio'].abs() > threshold]
    print(f'閾值 {threshold}%: {len(signals)} 次機會 ({len(signals)/len(data)*100:.1f}%)')

# 計算價差持續時間
data['signal'] = data['spread_ratio'].apply(lambda x: 'SELL_TQQQ' if x > 1 else ('BUY_TQQQ' if x < -1 else 'HOLD'))

# 檢查價差回歸情況
print(f'\n=== 價差回歸分析（閾值 1%） ===')
data['next_day_spread'] = data['spread_ratio'].shift(-1)
outliers = data[data['spread_ratio'].abs() > 1]
if len(outliers) > 0:
    reversion = outliers[outliers['spread_ratio'] * outliers['next_day_spread'] < 0]
    print(f'極端價差次數: {len(outliers)}')
    print(f'次日回歸次數: {len(reversion)} ({len(reversion)/len(outliers)*100:.1f}%)')

# 保存分析結果
data.to_csv('qqq_tqqq_analysis.csv', index=False)
print(f'\n分析結果已保存到 qqq_tqqq_analysis.csv')
