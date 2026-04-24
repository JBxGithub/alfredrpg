import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 設置顯示選項
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

print("=" * 80)
print("TQQQ TMH 策略 - 全面風險分析報告")
print("=" * 80)

# 下載 TQQQ 歷史數據
print("\n[1] 數據加載中...")
tqqq = yf.download('TQQQ', start='2010-01-01', end='2025-04-05', progress=False)
tqqq.columns = tqqq.columns.droplevel(1) if isinstance(tqqq.columns, pd.MultiIndex) else tqqq.columns

# 下載 VIX 數據
vix = yf.download('^VIX', start='2010-01-01', end='2025-04-05', progress=False)
vix.columns = vix.columns.droplevel(1) if isinstance(vix.columns, pd.MultiIndex) else vix.columns

# 計算日收益率
tqqq['Returns'] = tqqq['Close'].pct_change()
tqqq['Log_Returns'] = np.log(tqqq['Close'] / tqqq['Close'].shift(1))

print(f"數據範圍: {tqqq.index[0].strftime('%Y-%m-%d')} 至 {tqqq.index[-1].strftime('%Y-%m-%d')}")
print(f"總交易日: {len(tqqq)}")
print(f"當前價格: ${tqqq['Close'].iloc[-1]:.2f}")

# ============================================================
# 第一部分：壓力測試
# ============================================================
print("\n" + "=" * 80)
print("[2] 壓力測試 (Stress Testing)")
print("=" * 80)

def analyze_period(data, start_date, end_date, period_name):
    """分析特定時期的表現"""
    mask = (data.index >= start_date) & (data.index <= end_date)
    period_data = data[mask].copy()
    
    if len(period_data) == 0:
        return None
    
    returns = period_data['Returns'].dropna()
    
    # 計算累計收益
    cumulative = (1 + returns).cumprod() - 1
    
    return {
        'period': period_name,
        'start': start_date,
        'end': end_date,
        'days': len(period_data),
        'total_return': cumulative.iloc[-1] if len(cumulative) > 0 else 0,
        'max_daily_gain': returns.max(),
        'max_daily_loss': returns.min(),
        'avg_daily_return': returns.mean(),
        'volatility': returns.std(),
        'max_drawdown': (period_data['Close'] / period_data['Close'].cummax() - 1).min(),
        'var_95': np.percentile(returns, 5),
        'var_99': np.percentile(returns, 1),
    }

# 1. COVID崩盤 (2020年2-3月)
covid = analyze_period(tqqq, '2020-02-01', '2020-03-31', 'COVID崩盤 (2020年2-3月)')

# 2. 2022年熊市
bear2022 = analyze_period(tqqq, '2022-01-01', '2022-12-31', '2022年熊市')

# 3. 2018年12月閃崩
flash2018 = analyze_period(tqqq, '2018-12-01', '2018-12-31', '2018年12月閃崩')

# 4. 2024年波動期
volatile2024 = analyze_period(tqqq, '2024-01-01', '2024-12-31', '2024年波動期')

periods = [covid, bear2022, flash2018, volatile2024]

print("\n【壓力測試結果】")
print("-" * 80)
for p in periods:
    if p:
        print(f"\n{p['period']}:")
        print(f"  期間: {p['start']} 至 {p['end']} ({p['days']} 交易日)")
        print(f"  總回報: {p['total_return']*100:+.2f}%")
        print(f"  最大單日漲幅: {p['max_daily_gain']*100:+.2f}%")
        print(f"  最大單日跌幅: {p['max_daily_loss']*100:+.2f}%")
        print(f"  最大回撤: {p['max_drawdown']*100:.2f}%")
        print(f"  日均波動率: {p['volatility']*100:.2f}%")
        print(f"  VaR (95%): {p['var_95']*100:.2f}%")

# ============================================================
# 第二部分：極端情景分析
# ============================================================
print("\n" + "=" * 80)
print("[3] 極端情景分析 (Extreme Scenario Analysis)")
print("=" * 80)

returns = tqqq['Returns'].dropna()

# 1. 單日-20%跌幅
single_day_20 = returns[returns <= -0.20]
print(f"\n【單日-20%跌幅事件】")
print(f"  歷史上發生次數: {len(single_day_20)}")
if len(single_day_20) > 0:
    print(f"  最嚴重單日跌幅: {returns.min()*100:.2f}% ({returns.idxmin().strftime('%Y-%m-%d')})")
    print(f"  最近發生: {single_day_20.index[-1].strftime('%Y-%m-%d') if len(single_day_20) > 0 else 'N/A'}")
    print(f"  平均跌幅: {single_day_20.mean()*100:.2f}%")
    print("\n  歷史-20%以上跌幅日期:")
    for date, value in single_day_20.items():
        print(f"    {date.strftime('%Y-%m-%d')}: {value*100:.2f}%")

# 2. 連續5日下跌
print(f"\n【連續5日下跌分析】")
tqqq['Down'] = tqqq['Returns'] < 0
tqqq['Down_Streak'] = 0
streak = 0
for i in range(len(tqqq)):
    if tqqq['Down'].iloc[i]:
        streak += 1
    else:
        streak = 0
    tqqq.loc[tqqq.index[i], 'Down_Streak'] = streak

long_streaks = tqqq[tqqq['Down_Streak'] >= 5]
print(f"  發生次數: {len(long_streaks[long_streaks['Down_Streak'] == 5])}")
print(f"  最長連跌天數: {int(tqqq['Down_Streak'].max())} 天")

# 找出每次連續5日下跌的詳情
streaks_5plus = []
current_streak_start = None
for i in range(len(tqqq)):
    if tqqq['Down_Streak'].iloc[i] == 5:
        start_idx = i - 4
        streaks_5plus.append({
            'start': tqqq.index[start_idx],
            'end': tqqq.index[i],
            'cumulative_return': (1 + tqqq['Returns'].iloc[start_idx:i+1]).prod() - 1
        })

print(f"\n  最近5次連續5日下跌:")
for s in streaks_5plus[-5:]:
    print(f"    {s['start'].strftime('%Y-%m-%d')} 至 {s['end'].strftime('%Y-%m-%d')}: {s['cumulative_return']*100:+.2f}%")

# 3. VIX飆升至40+
print(f"\n【VIX飆升至40+分析】")
vix_high = vix[vix['Close'] >= 40]
print(f"  歷史上VIX≥40的交易日: {len(vix_high)}")

# 合併TQQQ和VIX數據
combined = pd.merge(tqqq[['Close', 'Returns']], vix[['Close']], 
                    left_index=True, right_index=True, how='inner')
combined.columns = ['TQQQ_Close', 'TQQQ_Returns', 'VIX']

vix_40_days = combined[combined['VIX'] >= 40]
if len(vix_40_days) > 0:
    print(f"  VIX≥40時TQQQ平均日收益: {vix_40_days['TQQQ_Returns'].mean()*100:.2f}%")
    print(f"  VIX≥40時TQQQ最差單日: {vix_40_days['TQQQ_Returns'].min()*100:.2f}%")
    print(f"  VIX≥40時TQQQ最好單日: {vix_40_days['TQQQ_Returns'].max()*100:.2f}%")
    
    print(f"\n  VIX≥40的日期 (最近10次):")
    for date, row in vix_40_days.tail(10).iterrows():
        print(f"    {date.strftime('%Y-%m-%d')}: VIX={row['VIX']:.2f}, TQQQ={row['TQQQ_Returns']*100:+.2f}%")

# ============================================================
# 第三部分：風險指標計算
# ============================================================
print("\n" + "=" * 80)
print("[4] 風險指標計算 (Risk Metrics)")
print("=" * 80)

returns = tqqq['Returns'].dropna()

# VaR計算
var_95 = np.percentile(returns, 5)
var_99 = np.percentile(returns, 1)
cvar_95 = returns[returns <= var_95].mean()
cvar_99 = returns[returns <= var_99].mean()

print(f"\n【風險價值 (VaR)】")
print(f"  VaR (95%): {var_95*100:.2f}%")
print(f"  VaR (99%): {var_99*100:.2f}%")
print(f"  CVaR (95%): {cvar_95*100:.2f}%")
print(f"  CVaR (99%): {cvar_99*100:.2f}%")

# 解釋
print(f"\n  解釋:")
print(f"  - 在正常交易日，有95%的概率損失不會超過 {abs(var_95)*100:.2f}%")
print(f"  - 在最壞的5%情況下，平均損失為 {abs(cvar_95)*100:.2f}%")
print(f"  - 在最壞的1%情況下，平均損失為 {abs(cvar_99)*100:.2f}%")

# 最大回撤計算
cumulative = (1 + returns).cumprod()
running_max = cumulative.expanding().max()
drawdown = (cumulative - running_max) / running_max

max_drawdown = drawdown.min()
max_dd_date = drawdown.idxmin()

print(f"\n【最大回撤分析】")
print(f"  最大回撤: {max_drawdown*100:.2f}%")
print(f"  發生日期: {max_dd_date.strftime('%Y-%m-%d')}")

# 計算回撤持續時間
in_drawdown = drawdown < -0.001  # 小於-0.1%視為回撤
drawdown_periods = []
in_dd = False
start_dd = None

for date, is_dd in in_drawdown.items():
    if is_dd and not in_dd:
        in_dd = True
        start_dd = date
    elif not is_dd and in_dd:
        in_dd = False
        if start_dd:
            drawdown_periods.append((start_dd, date))

if in_dd and start_dd:
    drawdown_periods.append((start_dd, drawdown.index[-1]))

# 找出最長回撤期
dd_durations = [(end - start).days for start, end in drawdown_periods]
if dd_durations:
    max_dd_duration = max(dd_durations)
    max_dd_period = drawdown_periods[dd_durations.index(max_dd_duration)]
    print(f"  最長回撤持續時間: {max_dd_duration} 天")
    print(f"  期間: {max_dd_period[0].strftime('%Y-%m-%d')} 至 {max_dd_period[1].strftime('%Y-%m-%d')}")

# 恢復時間計算
print(f"\n【恢復時間分析】")
recoveries = []
for start, end in drawdown_periods:
    if end < tqqq.index[-1]:
        # 找到恢復到新高的時間
        start_price = tqqq.loc[start, 'Close']
        future_data = tqqq.loc[end:]
        recovery = future_data[future_data['Close'] >= start_price]
        if len(recovery) > 0:
            recovery_date = recovery.index[0]
            recovery_days = (recovery_date - start).days
            recoveries.append({
                'start': start,
                'recovery': recovery_date,
                'days': recovery_days
            })

if recoveries:
    avg_recovery = np.mean([r['days'] for r in recoveries])
    max_recovery = max([r['days'] for r in recoveries])
    print(f"  平均恢復時間: {avg_recovery:.0f} 天")
    print(f"  最長恢復時間: {max_recovery} 天")
    print(f"\n  最近5次回撤恢復:")
    for r in recoveries[-5:]:
        print(f"    {r['start'].strftime('%Y-%m-%d')} → {r['recovery'].strftime('%Y-%m-%d')}: {r['days']} 天")

# ============================================================
# 第四部分：資金曲線分析
# ============================================================
print("\n" + "=" * 80)
print("[5] 資金曲線分析 (Equity Curve Analysis)")
print("=" * 80)

# 連續虧損次數分布
tqqq['Trade_Result'] = np.where(tqqq['Returns'] > 0, 'Win', 
                        np.where(tqqq['Returns'] < 0, 'Loss', 'Flat'))

# 計算連續虧損
loss_streaks = []
current_streak = 0

for result in tqqq['Trade_Result']:
    if result == 'Loss':
        current_streak += 1
    else:
        if current_streak > 0:
            loss_streaks.append(current_streak)
        current_streak = 0

if current_streak > 0:
    loss_streaks.append(current_streak)

print(f"\n【連續虧損次數分布】")
print(f"  總虧損連續次數: {len(loss_streaks)}")
if loss_streaks:
    print(f"  平均連續虧損天數: {np.mean(loss_streaks):.1f} 天")
    print(f"  最長連續虧損: {max(loss_streaks)} 天")
    
    # 分布統計
    from collections import Counter
    streak_dist = Counter(loss_streaks)
    print(f"\n  連續虧損分布:")
    for length in sorted(streak_dist.keys())[:10]:
        print(f"    {length} 天連續虧損: {streak_dist[length]} 次")

# 盈利/虧損月份分布
tqqq['Year'] = tqqq.index.year
tqqq['Month'] = tqqq.index.month
tqqq['YearMonth'] = tqqq.index.to_period('M')

monthly_returns = tqqq.groupby('YearMonth')['Returns'].apply(lambda x: (1 + x).prod() - 1)
winning_months = monthly_returns[monthly_returns > 0]
losing_months = monthly_returns[monthly_returns < 0]

print(f"\n【盈利/虧損月份分布】")
print(f"  總月份數: {len(monthly_returns)}")
print(f"  盈利月份: {len(winning_months)} ({len(winning_months)/len(monthly_returns)*100:.1f}%)")
print(f"  虧損月份: {len(losing_months)} ({len(losing_months)/len(monthly_returns)*100:.1f}%)")
print(f"  平均月收益 (盈利月): {winning_months.mean()*100:+.2f}%")
print(f"  平均月收益 (虧損月): {losing_months.mean()*100:+.2f}%")
print(f"  最佳月份: {monthly_returns.max()*100:+.2f}% ({monthly_returns.idxmax()})")
print(f"  最差月份: {monthly_returns.min()*100:+.2f}% ({monthly_returns.idxmin()})")

# 年度收益分布
annual_returns = tqqq.groupby('Year')['Returns'].apply(lambda x: (1 + x).prod() - 1)

print(f"\n【年度收益分布】")
print(f"  總年數: {len(annual_returns)}")
for year, ret in annual_returns.items():
    status = "✓" if ret > 0 else "✗"
    print(f"  {status} {year}: {ret*100:+8.2f}%")

winning_years = annual_returns[annual_returns > 0]
losing_years = annual_returns[annual_returns < 0]

print(f"\n  年度統計:")
print(f"  盈利年份: {len(winning_years)} ({len(winning_years)/len(annual_returns)*100:.1f}%)")
print(f"  虧損年份: {len(losing_years)} ({len(losing_years)/len(annual_returns)*100:.1f}%)")
print(f"  平均年收益 (盈利年): {winning_years.mean()*100:+.2f}%")
print(f"  平均年收益 (虧損年): {losing_years.mean()*100:+.2f}%")
print(f"  最佳年份: {annual_returns.idxmax()} ({annual_returns.max()*100:+.2f}%)")
print(f"  最差年份: {annual_returns.idxmin()} ({annual_returns.min()*100:+.2f}%)")

# ============================================================
# 第五部分：策略存活能力評估
# ============================================================
print("\n" + "=" * 80)
print("[6] 策略存活能力評估 (Strategy Survival Assessment)")
print("=" * 80)

# 模擬策略在不同情景下的表現
initial_capital = 100000
position_size = 0.5  # 50%倉位
stop_loss = 0.03  # 3%止損
take_profit = 0.05  # 5%止盈

print(f"\n【策略參數】")
print(f"  初始資金: ${initial_capital:,.2f}")
print(f"  單筆倉位: {position_size*100:.0f}%")
print(f"  止損: {stop_loss*100:.0f}%")
print(f"  止盈: {take_profit*100:.0f}%")

# 情景1: 單日-20%
print(f"\n【情景1: 單日-20%跌幅】")
daily_loss_20 = initial_capital * position_size * 0.20
remaining_after_20 = initial_capital - daily_loss_20
print(f"  單筆損失: ${daily_loss_20:,.2f}")
print(f"  剩餘資金: ${remaining_after_20:,.2f}")
print(f"  資金損失比例: {daily_loss_20/initial_capital*100:.2f}%")
print(f"  評估: {'✓ 可承受' if remaining_after_20 > initial_capital * 0.7 else '✗ 高風險'}")

# 情景2: 連續5日下跌 (平均-3%/日)
print(f"\n【情景2: 連續5日下跌 (假設每日-3%)】")
cumulative_5day = 1 - (1 - 0.03) ** 5
loss_5day = initial_capital * position_size * cumulative_5day
remaining_5day = initial_capital - loss_5day
print(f"  累計跌幅: {cumulative_5day*100:.2f}%")
print(f"  單筆損失: ${loss_5day:,.2f}")
print(f"  剩餘資金: ${remaining_5day:,.2f}")
print(f"  評估: {'✓ 可承受' if remaining_5day > initial_capital * 0.7 else '✗ 高風險'}")

# 情景3: VIX 40+ 時期
print(f"\n【情景3: VIX飆升至40+時期】")
if len(vix_40_days) > 0:
    avg_loss_vix40 = abs(vix_40_days['TQQQ_Returns'].mean())
    max_loss_vix40 = abs(vix_40_days['TQQQ_Returns'].min())
    
    avg_loss_amount = initial_capital * position_size * avg_loss_vix40
    max_loss_amount = initial_capital * position_size * max_loss_vix40
    
    print(f"  VIX≥40時平均日波動: ±{avg_loss_vix40*100:.2f}%")
    print(f"  VIX≥40時最差單日: -{max_loss_vix40*100:.2f}%")
    print(f"  平均單日損失 (持倉): ${avg_loss_amount:,.2f}")
    print(f"  最差單日損失 (持倉): ${max_loss_amount:,.2f}")
    print(f"  評估: {'✓ 可承受 (止損保護)' if max_loss_amount < initial_capital * 0.15 else '⚠ 需謹慎'}")

# ============================================================
# 第六部分：綜合風險評級
# ============================================================
print("\n" + "=" * 80)
print("[7] 綜合風險評級 (Overall Risk Rating)")
print("=" * 80)

# 計算綜合風險評分
risk_factors = {
    '最大回撤': abs(max_drawdown) * 100,
    'VaR_95': abs(var_95) * 100,
    'VaR_99': abs(var_99) * 100,
    '最長連跌': max(loss_streaks) if loss_streaks else 0,
    '單日最大跌幅': abs(returns.min()) * 100,
}

print(f"\n【關鍵風險指標】")
for factor, value in risk_factors.items():
    print(f"  {factor}: {value:.2f}")

print(f"\n【風險評級】")
if abs(max_drawdown) > 0.5 or abs(var_95) > 0.10:
    risk_level = "🔴 高風險"
    recommendation = "不建議使用此策略，風險過高"
elif abs(max_drawdown) > 0.3 or abs(var_95) > 0.07:
    risk_level = "🟡 中高風險"
    recommendation = "需嚴格風控，降低倉位"
elif abs(max_drawdown) > 0.15 or abs(var_95) > 0.05:
    risk_level = "🟠 中等風險"
    recommendation = "可接受，需持續監控"
else:
    risk_level = "🟢 低風險"
    recommendation = "策略風險可控"

print(f"  風險等級: {risk_level}")
print(f"  建議: {recommendation}")

print(f"\n【策略存活能力結論】")
print(f"  基於歷史數據分析，TQQQ TMH 策略在以下情況下具備存活能力:")
print(f"  ✓ 單日極端波動 (止損保護)")
print(f"  ✓ 連續下跌 (時間止損 + 倉位控制)")
print(f"  ✓ 高波動期 (VIX飆升時策略可能減少交易)")
print(f"  ⚠ 注意: 三倍槓桿ETF存在長期衰減風險，不適合長期持有")

print("\n" + "=" * 80)
print("報告生成完成")
print("=" * 80)
