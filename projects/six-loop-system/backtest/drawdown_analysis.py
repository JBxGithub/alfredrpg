"""
回撤分析 - 找出最大回撤期間的問題
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime

# 讀取回測結果
results = pd.read_csv('backtest/results/optimized_daily_20260420_210814.csv')
results['date'] = pd.to_datetime(results['date'], utc=True)

print("="*70)
print("回撤深度分析")
print("="*70)

# 計算累計最高值同回撤
results['cummax'] = results['portfolio_value'].cummax()
results['drawdown'] = (results['portfolio_value'] - results['cummax']) / results['cummax'] * 100

# 找出最大回撤期間
max_dd_idx = results['drawdown'].idxmin()
max_dd_date = results.loc[max_dd_idx, 'date']
max_dd_value = results.loc[max_dd_idx, 'drawdown']

print(f"\n【最大回撤事件】")
print(f"日期: {max_dd_date}")
print(f"回撤幅度: {max_dd_value:.2f}%")
print(f"當時組合價值: ${results.loc[max_dd_idx, 'portfolio_value']:,.2f}")
print(f"前期最高值: ${results.loc[max_dd_idx, 'cummax']:,.2f}")

# 找出回撤開始點（最高點）
peak_idx = results.loc[:max_dd_idx, 'portfolio_value'].idxmax()
peak_date = results.loc[peak_idx, 'date']
peak_value = results.loc[peak_idx, 'portfolio_value']

print(f"\n回撤起點: {peak_date}")
print(f"回撤終點: {max_dd_date}")
print(f"回撤持續: {(max_dd_date - peak_date).days} 天")

# 分析回撤期間嘅市場情況
drawdown_period = results.loc[peak_idx:max_dd_idx]

print(f"\n【回撤期間市場表現】")
print(f"QQQ 價格變化: ${drawdown_period['qqq_price'].iloc[0]:.2f} → ${drawdown_period['qqq_price'].iloc[-1]:.2f}")
qqq_change = (drawdown_period['qqq_price'].iloc[-1] / drawdown_period['qqq_price'].iloc[0] - 1) * 100
print(f"QQQ 跌幅: {qqq_change:.2f}%")

print(f"\nTQQQ 價格變化: ${drawdown_period['tqqq_price'].iloc[0]:.2f} → ${drawdown_period['tqqq_price'].iloc[-1]:.2f}")
tqqq_change = (drawdown_period['tqqq_price'].iloc[-1] / drawdown_period['tqqq_price'].iloc[0] - 1) * 100
print(f"TQQQ 跌幅: {tqqq_change:.2f}%")

# 分析回撤期間嘅交易信號
print(f"\n【回撤期間策略行為】")
signals = drawdown_period['signal'].value_counts()
print(f"信號統計:")
for signal, count in signals.items():
    print(f"  {signal}: {count} 天")

# 檢查有無持倉
holding_days = (drawdown_period['positions'] > 0).sum()
no_holding_days = (drawdown_period['positions'] == 0).sum()
print(f"\n持倉狀態:")
print(f"  有持倉: {holding_days} 天")
print(f"  無持倉: {no_holding_days} 天")

# 如果有持倉，分析持倉表現
if holding_days > 0:
    holding_period = drawdown_period[drawdown_period['positions'] > 0]
    avg_entry = holding_period['tqqq_price'].iloc[0] if len(holding_period) > 0 else 0
    avg_exit = holding_period['tqqq_price'].iloc[-1] if len(holding_period) > 0 else 0
    print(f"\n持倉期間:")
    print(f"  入場價: ${avg_entry:.2f}")
    print(f"  出場價: ${avg_exit:.2f}")
    print(f"  持倉虧損: {(avg_exit/avg_entry - 1)*100:.2f}%")

# 分析評分變化
print(f"\n【評分分析】")
print(f"Absolute Score: {drawdown_period['absolute_score'].iloc[0]:.1f} → {drawdown_period['absolute_score'].iloc[-1]:.1f}")
print(f"Reference Score: {drawdown_period['reference_score'].iloc[0]:.1f} → {drawdown_period['reference_score'].iloc[-1]:.1f}")
print(f"Final Score: {drawdown_period['final_score'].iloc[0]:.1f} → {drawdown_period['final_score'].iloc[-1]:.1f}")

# 找出所有回撤超過30%的期間
print(f"\n【所有大幅回撤期間 (>30%)】")
results['in_drawdown'] = results['drawdown'] < -30
drawdown_starts = results[results['in_drawdown'] & (~results['in_drawdown'].shift(1).fillna(False))]

for idx in drawdown_starts.index[:5]:  # 只顯示前5個
    dd_period = results.loc[idx:]
    dd_end_idx = dd_period[~dd_period['in_drawdown']].index[0] if len(dd_period[~dd_period['in_drawdown']]) > 0 else len(results)-1
    dd_end = results.loc[dd_end_idx]
    
    print(f"\n  回撤期間: {results.loc[idx, 'date'].strftime('%Y-%m-%d')} → {dd_end['date'].strftime('%Y-%m-%d')}")
    print(f"  最大回撤: {results.loc[idx:dd_end_idx, 'drawdown'].min():.2f}%")
    print(f"  持續天數: {(dd_end['date'] - results.loc[idx, 'date']).days} 天")

print("\n" + "="*70)

# 保存分析結果
analysis = {
    'max_drawdown_date': str(max_dd_date),
    'max_drawdown_pct': float(max_dd_value),
    'peak_date': str(peak_date),
    'peak_value': float(peak_value),
    'drawdown_duration_days': int((max_dd_date - peak_date).days),
    'qqq_decline_pct': float(qqq_change),
    'tqqq_decline_pct': float(tqqq_change),
    'holding_days': int(holding_days),
    'cash_days': int(no_holding_days)
}

with open('backtest/results/drawdown_analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)

print("\n分析結果已保存到 backtest/results/drawdown_analysis.json")
