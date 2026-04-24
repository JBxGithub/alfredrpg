"""
檢查 V3 回撤詳情
驗證止損執行情況同除權問題
"""

import pandas as pd
import numpy as np

# 讀取 V3 結果
results = pd.read_csv('backtest/results/v3_daily_20260420_224644.csv')
results['date'] = pd.to_datetime(results['date'], utc=True)
trades = pd.read_csv('backtest/results/v3_trades_20260420_224644.csv')
trades['date'] = pd.to_datetime(trades['date'], utc=True)

print("="*70)
print("V3 回撤深度分析")
print("="*70)

# 計算回撤
results['cummax'] = results['portfolio_value'].cummax()
results['drawdown'] = (results['portfolio_value'] - results['cummax']) / results['cummax'] * 100

# 找出最大回撤
max_dd_idx = results['drawdown'].idxmin()
max_dd_date = results.loc[max_dd_idx, 'date']
max_dd_value = results.loc[max_dd_idx, 'drawdown']

print(f"\n【最大回撤事件】")
print(f"日期: {max_dd_date}")
print(f"回撤: {max_dd_value:.2f}%")
print(f"當時組合價值: ${results.loc[max_dd_idx, 'portfolio_value']:,.2f}")

# 找出回撤起點
peak_idx = results.loc[:max_dd_idx, 'portfolio_value'].idxmax()
peak_date = results.loc[peak_idx, 'date']
peak_value = results.loc[peak_idx, 'portfolio_value']

print(f"\n回撤起點: {peak_date}")
print(f"回撤終點: {max_dd_date}")
print(f"持續: {(max_dd_date - peak_date).days} 天")

# 分析回撤期間嘅交易
drawdown_period = results.loc[peak_idx:max_dd_idx]

print(f"\n【回撤期間市場數據】")
print(f"QQQ: ${drawdown_period['qqq_price'].iloc[0]:.2f} → ${drawdown_period['qqq_price'].iloc[-1]:.2f}")
print(f"TQQQ: ${drawdown_period['tqqq_price'].iloc[0]:.2f} → ${drawdown_period['tqqq_price'].iloc[-1]:.2f}")

qqq_change = (drawdown_period['qqq_price'].iloc[-1] / drawdown_period['qqq_price'].iloc[0] - 1) * 100
tqqq_change = (drawdown_period['tqqq_price'].iloc[-1] / drawdown_period['tqqq_price'].iloc[0] - 1) * 100

print(f"QQQ 變化: {qqq_change:.2f}%")
print(f"TQQQ 變化: {tqqq_change:.2f}%")

# 檢查除權
print(f"\n【檢查除權】")
tqqq_start = drawdown_period['tqqq_price'].iloc[0]
tqqq_end = drawdown_period['tqqq_price'].iloc[-1]
qqq_start = drawdown_period['qqq_price'].iloc[0]
qqq_end = drawdown_period['qqq_price'].iloc[-1]

# 理論上 TQQQ 應該係 QQQ 的 ~3x
expected_tqqq_change = qqq_change * 3
actual_vs_expected = tqqq_change / expected_tqqq_change if expected_tqqq_change != 0 else 0

print(f"QQQ 跌幅: {qqq_change:.2f}%")
print(f"預期 TQQQ 跌幅 (~3x): {expected_tqqq_change:.2f}%")
print(f"實際 TQQQ 跌幅: {tqqq_change:.2f}%")
print(f"實際/預期比例: {actual_vs_expected:.2f}")

if actual_vs_expected < 0.8 or actual_vs_expected > 1.2:
    print("⚠️  警告: 實際與預期偏差大，可能有除權或槓桿衰減！")
else:
    print("✅ 實際與預期接近，無明顯除權問題")

# 分析回撤期間嘅持倉狀態
print(f"\n【回撤期間持倉分析】")
holding_days = (drawdown_period['positions'] > 0).sum()
cash_days = (drawdown_period['positions'] == 0).sum()
print(f"有持倉: {holding_days} 天")
print(f"無持倉: {cash_days} 天")

# 如果有持倉，分析具體情況
if holding_days > 0:
    holding_data = drawdown_period[drawdown_period['positions'] > 0]
    
    print(f"\n持倉期間詳情:")
    print(f"  平均持倉價值: ${holding_data['position_value'].mean():,.2f}")
    print(f"  最大持倉價值: ${holding_data['position_value'].max():,.2f}")
    print(f"  最小持倉價值: ${holding_data['position_value'].min():,.2f}")
    
    # 檢查有無止損應該觸發但未觸發
    # 需要重建交易記錄

# 檢查交易記錄
print(f"\n【回撤期間交易記錄】")
dd_trades = trades[(trades['date'] >= peak_date) & (trades['date'] <= max_dd_date)]

if len(dd_trades) > 0:
    print(f"期間交易次數: {len(dd_trades)}")
    for _, trade in dd_trades.iterrows():
        print(f"\n  {trade['date'].strftime('%Y-%m-%d')}: {trade['action']}")
        if 'tqqq_price' in trade:
            print(f"    TQQQ: ${trade['tqqq_price']:.2f}")
        if 'qqq_price' in trade:
            print(f"    QQQ: ${trade['qqq_price']:.2f}")
        if 'qqq_change_pct' in trade and not pd.isna(trade['qqq_change_pct']):
            print(f"    QQQ變化: {trade['qqq_change_pct']*100:.2f}%")
        if 'tqqq_change_pct' in trade and not pd.isna(trade['tqqq_change_pct']):
            print(f"    TQQQ變化: {trade['tqqq_change_pct']*100:.2f}%")
        if 'holding_days' in trade and not pd.isna(trade['holding_days']):
            print(f"    持倉天數: {trade['holding_days']}")
else:
    print("期間無交易記錄")

# 檢查所有大幅回撤 (>50%)
print(f"\n【所有大幅回撤期間 (>50%)】")
results['in_big_dd'] = results['drawdown'] < -50
big_dd_starts = results[results['in_big_dd'] & (~results['in_big_dd'].shift(1).fillna(False))]

for idx in big_dd_starts.index[:3]:
    dd_period = results.loc[idx:]
    dd_end_idx = dd_period[~dd_period['in_big_dd']].index[0] if len(dd_period[~dd_period['in_big_dd']]) > 0 else len(results)-1
    dd_end = results.loc[dd_end_idx]
    
    print(f"\n  回撤期間: {results.loc[idx, 'date'].strftime('%Y-%m-%d')} → {dd_end['date'].strftime('%Y-%m-%d')}")
    print(f"  最大回撤: {results.loc[idx:dd_end_idx, 'drawdown'].min():.2f}%")
    print(f"  持續天數: {(dd_end['date'] - results.loc[idx, 'date']).days} 天")
    
    # 檢查期間 QQQ 變化
    period_qqq_start = results.loc[idx, 'qqq_price']
    period_qqq_end = dd_end['qqq_price']
    period_qqq_change = (period_qqq_end / period_qqq_start - 1) * 100
    print(f"  QQQ 變化: {period_qqq_change:.2f}%")

print("\n" + "="*70)

# 檢查槓桿衰減 (Leverage Decay)
print("\n【槓桿衰測檢查】")
print("TQQQ 係 3x 每日重置槓桿 ETF，長期持有會有槓桿衰減")

# 計算理論 vs 實際
qqq_total_return = (results['qqq_price'].iloc[-1] / results['qqq_price'].iloc[0] - 1) * 100
tqqq_total_return = (results['tqqq_price'].iloc[-1] / results['tqqq_price'].iloc[0] - 1) * 100
expected_tqqq = qqq_total_return * 3

print(f"\n5年期間:")
print(f"QQQ 總回報: {qqq_total_return:.2f}%")
print(f"預期 TQQQ (3x): {expected_tqqq:.2f}%")
print(f"實際 TQQQ: {tqqq_total_return:.2f}%")
print(f"槓桿衰減損失: {expected_tqqq - tqqq_total_return:.2f}%")
