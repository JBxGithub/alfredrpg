"""
Plan B 交易案例分析
詳細列出代表性交易
"""

import pandas as pd
import numpy as np

# 讀取交易記錄
trades = pd.read_csv('backtest/results/v8_planb_trades_20260421_001353.csv')
trades['date'] = pd.to_datetime(trades['date'], utc=True)

print("="*80)
print("Plan B 交易案例分析")
print("="*80)

# 分開買入同賣出
buy_trades = trades[trades['action'].str.contains('BUY')].copy()
sell_trades = trades[trades['action'].str.contains('SELL')].copy()

print(f"\n總交易: {len(buy_trades)} 次開倉, {len(sell_trades)} 次平倉")

# ===== 案例 1: 最佳多單盈利 =====
print("\n" + "="*80)
print("【案例 1】最佳多單盈利")
print("="*80)

long_trades = sell_trades[sell_trades['action'].str.contains('LONG')].copy()
long_trades['pnl'] = pd.to_numeric(long_trades['net_pnl'], errors='coerce')
best_long = long_trades.loc[long_trades['pnl'].idxmax()]

print(f"\n開倉日期: {buy_trades[buy_trades['action']=='BUY_LONG'].iloc[0]['date']}")
print(f"平倉日期: {best_long['date']}")
print(f"標的: {best_long['symbol']}")
print(f"入場價: ${best_long['price'] / (1 + best_long['etf_change']):.2f}")
print(f"平倉價: ${best_long['price']:.2f}")
print(f"持倉天數: {best_long['holding_days']}")
print(f"ETF變化: {best_long['etf_change']*100:.2f}%")
print(f"淨盈利: ${best_long['net_pnl']:,.2f}")
print(f"賣出原因: {best_long['stop_reason']}")

# ===== 案例 2: 最佳空單盈利 =====
print("\n" + "="*80)
print("【案例 2】最佳空單盈利")
print("="*80)

short_trades = sell_trades[sell_trades['action'].str.contains('SHORT')].copy()
short_trades['pnl'] = pd.to_numeric(short_trades['net_pnl'], errors='coerce')
if len(short_trades) > 0 and short_trades['pnl'].max() > 0:
    best_short = short_trades.loc[short_trades['pnl'].idxmax()]
    
    print(f"\n平倉日期: {best_short['date']}")
    print(f"標的: {best_short['symbol']}")
    print(f"入場價: ${best_short['price'] / (1 - best_short['etf_change']):.2f}")
    print(f"平倉價: ${best_short['price']:.2f}")
    print(f"持倉天數: {best_short['holding_days']}")
    print(f"ETF變化: {best_short['etf_change']*100:.2f}% (空單盈利)")
    print(f"淨盈利: ${best_short['net_pnl']:,.2f}")
    print(f"賣出原因: {best_short['stop_reason']}")
else:
    print("\n無盈利空單 (5年牛市中空單主要係止損)")

# ===== 案例 3: 最大多單虧損 =====
print("\n" + "="*80)
print("【案例 3】最大多單虧損")
print("="*80)

worst_long = long_trades.loc[long_trades['pnl'].idxmin()]

print(f"\n平倉日期: {worst_long['date']}")
print(f"標的: {worst_long['symbol']}")
print(f"入場價: ${worst_long['price'] / (1 + worst_long['etf_change']):.2f}")
print(f"平倉價: ${worst_long['price']:.2f}")
print(f"持倉天數: {worst_long['holding_days']}")
print(f"ETF變化: {worst_long['etf_change']*100:.2f}%")
print(f"淨虧損: ${worst_long['net_pnl']:,.2f}")
print(f"賣出原因: {worst_long['stop_reason']}")

# ===== 案例 4: 最長持倉多單 =====
print("\n" + "="*80)
print("【案例 4】最長持倉多單 (牛市續持)")
print("="*80)

longest_long = long_trades.loc[long_trades['holding_days'].idxmax()]

print(f"\n平倉日期: {longest_long['date']}")
print(f"標的: {longest_long['symbol']}")
print(f"持倉天數: {longest_long['holding_days']} 天")
print(f"入場價: ${longest_long['price'] / (1 + longest_long['etf_change']):.2f}")
print(f"平倉價: ${longest_long['price']:.2f}")
print(f"ETF變化: {longest_long['etf_change']*100:.2f}%")
print(f"淨盈利: ${longest_long['net_pnl']:,.2f}")
print(f"賣出原因: {longest_long['stop_reason']}")

# ===== 案例 5: 典型空單止損 =====
print("\n" + "="*80)
print("【案例 5】典型空單止損 (牛市中做空被止損)")
print("="*80)

if len(short_trades) > 0:
    worst_short = short_trades.loc[short_trades['pnl'].idxmin()]
    
    print(f"\n平倉日期: {worst_short['date']}")
    print(f"標的: {worst_short['symbol']}")
    print(f"入場價: ${worst_short['price'] / (1 - worst_short['etf_change']):.2f}")
    print(f"平倉價: ${worst_short['price']:.2f}")
    print(f"持倉天數: {worst_short['holding_days']}")
    print(f"ETF變化: {worst_short['etf_change']*100:.2f}% (空單虧損 = ETF上升)")
    print(f"淨虧損: ${worst_short['net_pnl']:,.2f}")
    print(f"賣出原因: {worst_short['stop_reason']}")
    print(f"\n分析: 牛市中嘗試做空，但被止損出場，有效控制虧損")

# ===== 案例 6: 7天重估續持後盈利 =====
print("\n" + "="*80)
print("【案例 6】7天重估續持後盈利")
print("="*80)

reeval_continues = long_trades[long_trades['action'] == 'SELL_LONG_REEVAL']
if len(reeval_continues) > 0:
    # 找一個重估後最終盈利的完整周期
    print("\n顯示重估賣出的多單:")
    for idx, trade in reeval_continues.head(3).iterrows():
        print(f"\n  日期: {trade['date']}")
        print(f"  盈利: ${trade['net_pnl']:,.2f}")
        print(f"  持倉: {trade['holding_days']} 天")
        print(f"  原因: {trade['stop_reason']}")

# ===== 年度分析 =====
print("\n" + "="*80)
print("【年度交易分析】")
print("="*80)

sell_trades['year'] = pd.to_datetime(sell_trades['date']).dt.year
sell_trades['pnl'] = pd.to_numeric(sell_trades['net_pnl'], errors='coerce')

yearly_stats = sell_trades.groupby('year').agg({
    'pnl': ['count', 'sum', 'mean'],
    'action': lambda x: len([a for a in x if 'LONG' in a])
}).round(2)

yearly_stats.columns = ['交易次數', '年度盈虧', '平均盈虧', '多單次數']

print("\n")
print(yearly_stats.to_string())

# ===== 月度表現 =====
print("\n" + "="*80)
print("【最佳/最差月份】")
print("="*80)

# 讀取每日數據計算月度回報
daily = pd.read_csv('backtest/results/v8_planb_daily_20260421_001353.csv')
daily['date'] = pd.to_datetime(daily['date'], utc=True)
daily['year_month'] = daily['date'].dt.to_period('M')
daily['daily_return'] = daily['portfolio_value'].pct_change()

monthly_returns = daily.groupby('year_month')['daily_return'].apply(lambda x: (1 + x).prod() - 1)

best_month = monthly_returns.idxmax()
worst_month = monthly_returns.idxmin()

print(f"\n最佳月份: {best_month} ({monthly_returns[best_month]*100:.2f}%)")
print(f"最差月份: {worst_month} ({monthly_returns[worst_month]*100:.2f}%)")

# ===== 關鍵時期分析 =====
print("\n" + "="*80)
print("【關鍵時期分析】")
print("="*80)

# 2020年3月疫情暴跌
covid_period = daily[(daily['date'] >= '2020-02-01') & (daily['date'] <= '2020-05-01')]
if len(covid_period) > 0:
    covid_start = covid_period['portfolio_value'].iloc[0]
    covid_end = covid_period['portfolio_value'].iloc[-1]
    covid_return = (covid_end / covid_start - 1) * 100
    covid_max = covid_period['portfolio_value'].max()
    covid_min = covid_period['portfolio_value'].min()
    covid_dd = (covid_min / covid_max - 1) * 100
    
    print(f"\n2020年2-5月 (疫情暴跌):")
    print(f"  期初價值: ${covid_start:,.2f}")
    print(f"  期末價值: ${covid_end:,.2f}")
    print(f"  期間回報: {covid_return:+.2f}%")
    print(f"  最大回撤: {covid_dd:.2f}%")
    print(f"  策略表現: 喺市場暴跌中可能做空獲利或及時止損")

# 2022年熊市
bear_period = daily[(daily['date'] >= '2022-01-01') & (daily['date'] <= '2022-12-31')]
if len(bear_period) > 0:
    bear_start = bear_period['portfolio_value'].iloc[0]
    bear_end = bear_period['portfolio_value'].iloc[-1]
    bear_return = (bear_end / bear_start - 1) * 100
    
    print(f"\n2022年全年 (熊市):")
    print(f"  期初價值: ${bear_start:,.2f}")
    print(f"  期末價值: ${bear_end:,.2f}")
    print(f"  年度回報: {bear_return:+.2f}%")
    print(f"  策略表現: 熊市中多空切換應該有較好表現")

print("\n" + "="*80)
print("案例分析完成")
print("="*80)
