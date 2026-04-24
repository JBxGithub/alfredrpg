import pandas as pd
import numpy as np

# 讀取數據
data = pd.read_csv('qqq_tqqq_analysis.csv')

print('=== 方向性策略分析 ===')
print('策略: 做空 TQQQ + 做多 QQQ (押注 TQQQ 持續跑輸)')
print()

# 假設初始資金分配
initial_capital = 10000
qqq_allocation = 0.5  # 50% 做多 QQQ
tqqq_allocation = 0.5  # 50% 做空 TQQQ

# 計算每日收益
qqq_shares = (initial_capital * qqq_allocation) / data['close_QQQ'].iloc[0]
tqqq_shares = (initial_capital * tqqq_allocation) / data['close_TQQQ'].iloc[0]

data['qqq_value'] = qqq_shares * data['close_QQQ']
data['tqqq_short_value'] = initial_capital * tqqq_allocation - (tqqq_shares * (data['close_TQQQ'] - data['close_TQQQ'].iloc[0]))
data['total_value'] = data['qqq_value'] + data['tqqq_short_value']

# 計算收益
data['daily_return'] = data['total_value'].pct_change()

print(f'初始資金: ${initial_capital:,.2f}')
print(f'最終價值: ${data["total_value"].iloc[-1]:,.2f}')
print(f'總收益: ${data["total_value"].iloc[-1] - initial_capital:,.2f} ({(data["total_value"].iloc[-1]/initial_capital - 1)*100:.2f}%)')
print(f'持有期間: {len(data)} 天')
print()

# 風險指標
cumulative = (1 + data['daily_return'].fillna(0)).cumprod()
rolling_max = cumulative.expanding().max()
drawdown = (cumulative - rolling_max) / rolling_max

print('風險指標:')
print(f'  最大日內回撤: {drawdown.min()*100:.2f}%')
print(f'  日收益波動: {data["daily_return"].std()*100:.2f}%')
print(f'  夏普比率 (假設無風險利率0%): {(data["daily_return"].mean() / data["daily_return"].std()) * np.sqrt(252):.2f}')
print()

# 與單純持有 QQQ 比較
qqq_buy_hold = (data['close_QQQ'].iloc[-1] / data['close_QQQ'].iloc[0] - 1) * 100
strategy_return = (data['total_value'].iloc[-1] / initial_capital - 1) * 100

print('策略比較:')
print(f'  本策略收益: {strategy_return:.2f}%')
print(f'  單純持有 QQQ: {qqq_buy_hold:.2f}%')
print(f'  超額收益: {strategy_return - qqq_buy_hold:.2f}%')
