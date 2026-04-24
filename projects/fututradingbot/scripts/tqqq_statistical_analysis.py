"""
TQQQ Statistical Analysis Script
Analyzes TQQQ historical price data characteristics, market regimes, and statistical properties
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from scipy import stats
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.stats.diagnostic import het_arch
from arch import arch_model
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("=" * 80)
print("TQQQ Historical Price Data Statistical Analysis")
print("=" * 80)

# =============================================================================
# 1. Data Collection
# =============================================================================
print("\n[1] Downloading historical data...")

# Download TQQQ and QQQ data (max available period)
tqqq = yf.download("TQQQ", start="2010-02-11", progress=False)
qqq = yf.download("QQQ", start="2010-02-11", progress=False)

# Flatten multi-index columns if present
if isinstance(tqqq.columns, pd.MultiIndex):
    tqqq.columns = tqqq.columns.get_level_values(0)
if isinstance(qqq.columns, pd.MultiIndex):
    qqq.columns = qqq.columns.get_level_values(0)

print(f"TQQQ data range: {tqqq.index[0].strftime('%Y-%m-%d')} to {tqqq.index[-1].strftime('%Y-%m-%d')}")
print(f"Total trading days: {len(tqqq)}")

# Calculate returns
tqqq['Returns'] = tqqq['Close'].pct_change()
tqqq['Log_Returns'] = np.log(tqqq['Close'] / tqqq['Close'].shift(1))
qqq['Returns'] = qqq['Close'].pct_change()
qqq['Log_Returns'] = np.log(qqq['Close'] / qqq['Close'].shift(1))

# Align data for comparison
common_start = max(tqqq.index[0], qqq.index[0])
common_end = min(tqqq.index[-1], qqq.index[-1])
tqqq_aligned = tqqq.loc[common_start:common_end].copy()
qqq_aligned = qqq.loc[common_start:common_end].copy()

print(f"\nAligned data range: {common_start.strftime('%Y-%m-%d')} to {common_end.strftime('%Y-%m-%d')}")
print(f"Aligned trading days: {len(tqqq_aligned)}")

# =============================================================================
# 2. TQQQ vs QQQ Relationship Analysis
# =============================================================================
print("\n" + "=" * 80)
print("[2] TQQQ vs QQQ Relationship Analysis")
print("=" * 80)

# Calculate daily returns for comparison
tqqq_ret = tqqq_aligned['Returns'].dropna()
qqq_ret = qqq_aligned['Returns'].dropna()

# Ensure same length
min_len = min(len(tqqq_ret), len(qqq_ret))
tqqq_ret = tqqq_ret.iloc[-min_len:]
qqq_ret = qqq_ret.iloc[-min_len:]

# Leverage effect analysis (TQQQ is supposed to be 3x QQQ)
print("\n--- Leverage Effect Analysis ---")

# Rolling 30-day beta (leverage ratio)
window = 30
rolling_beta = pd.Series(index=tqqq_ret.index[window:], dtype=float)
for i in range(window, len(tqqq_ret)):
    y = tqqq_ret.iloc[i-window:i]
    x = qqq_ret.iloc[i-window:i]
    # Remove any NaN or infinite values
    mask = np.isfinite(y) & np.isfinite(x)
    if mask.sum() > 10:
        slope, intercept, r_value, p_value, std_err = stats.linregress(x[mask], y[mask])
        rolling_beta.iloc[i-window] = slope

print(f"Average realized leverage ratio: {rolling_beta.mean():.4f}")
print(f"Leverage ratio std dev: {rolling_beta.std():.4f}")
print(f"Leverage ratio range: {rolling_beta.min():.4f} - {rolling_beta.max():.4f}")

# Tracking Error Analysis
print("\n--- Tracking Error Analysis ---")
# Expected TQQQ return = 3 * QQQ return
expected_tqqq = 3 * qqq_ret
tracking_diff = tqqq_ret - expected_tqqq
tracking_error = tracking_diff.std() * np.sqrt(252)  # Annualized
print(f"Daily tracking error (annualized): {tracking_error:.4f} ({tracking_error*100:.2f}%)")
print(f"Mean tracking difference: {tracking_diff.mean()*100:.4f}%")
print(f"Tracking difference std: {tracking_diff.std()*100:.4f}%")

# Correlation analysis
correlation = tqqq_ret.corr(qqq_ret)
print(f"\nCorrelation with QQQ: {correlation:.4f}")

# Regression analysis
mask = np.isfinite(tqqq_ret) & np.isfinite(qqq_ret)
slope, intercept, r_value, p_value, std_err = stats.linregress(qqq_ret[mask], tqqq_ret[mask])
print(f"\nRegression: TQQQ = {slope:.4f} * QQQ + {intercept:.6f}")
print(f"R-squared: {r_value**2:.4f}")
print(f"P-value: {p_value:.2e}")

# Volatility comparison
tqqq_vol = tqqq_ret.std() * np.sqrt(252)
qqq_vol = qqq_ret.std() * np.sqrt(252)
print(f"\n--- Volatility Comparison ---")
print(f"TQQQ annualized volatility: {tqqq_vol:.4f} ({tqqq_vol*100:.2f}%)")
print(f"QQQ annualized volatility: {qqq_vol:.4f} ({qqq_vol*100:.2f}%)")
print(f"Volatility ratio (TQQQ/QQQ): {tqqq_vol/qqq_vol:.2f}x")

# =============================================================================
# 3. Volatility Characteristics Analysis
# =============================================================================
print("\n" + "=" * 80)
print("[3] Volatility Characteristics Analysis")
print("=" * 80)

returns = tqqq['Returns'].dropna()

# Realized Volatility (rolling)
windows = [5, 10, 20, 60]
print("\n--- Realized Volatility (Annualized) ---")
for w in windows:
    rv = returns.rolling(window=w).std() * np.sqrt(252)
    print(f"{w}-day RV: Mean={rv.mean():.4f}, Std={rv.std():.4f}, Max={rv.max():.4f}")

# Volatility Clustering - GARCH Test
print("\n--- Volatility Clustering (ARCH Test) ---")
# Test for ARCH effects
arch_test = het_arch(returns.dropna(), maxlag=5)
print(f"ARCH Test LM statistic: {arch_test[0]:.4f}")
print(f"ARCH Test p-value: {arch_test[1]:.4f}")
print(f"ARCH effects present: {'Yes' if arch_test[1] < 0.05 else 'No'}")

# GARCH(1,1) Model
print("\n--- GARCH(1,1) Model ---")
try:
    am = arch_model(returns.dropna() * 100, vol='Garch', p=1, q=1, rescale=False)
    res = am.fit(disp='off')
    print(f"GARCH(1,1) Parameters:")
    print(f"  omega (constant): {res.params['omega']:.6f}")
    print(f"  alpha (ARCH): {res.params['alpha[1]']:.4f}")
    print(f"  beta (GARCH): {res.params['beta[1]']:.4f}")
    print(f"  Persistence (alpha+beta): {res.params['alpha[1]'] + res.params['beta[1]']:.4f}")
    print(f"  Half-life: {np.log(0.5) / np.log(res.params['alpha[1]'] + res.params['beta[1]']):.2f} days")
    print(f"  Log-likelihood: {res.loglikelihood:.2f}")
    print(f"  AIC: {res.aic:.2f}")
    print(f"  BIC: {res.bic:.2f}")
except Exception as e:
    print(f"GARCH model fitting error: {e}")

# Volatility distribution
print("\n--- Return Distribution Statistics ---")
print(f"Mean daily return: {returns.mean()*100:.4f}%")
print(f"Std dev daily return: {returns.std()*100:.4f}%")
print(f"Skewness: {returns.skew():.4f}")
print(f"Kurtosis: {returns.kurtosis():.4f}")
print(f"Jarque-Bera test p-value: {stats.jarque_bera(returns.dropna())[1]:.2e}")

# VaR and CVaR
var_95 = np.percentile(returns, 5)
var_99 = np.percentile(returns, 1)
cvar_95 = returns[returns <= var_95].mean()
cvar_99 = returns[returns <= var_99].mean()
print(f"\n--- Risk Metrics ---")
print(f"VaR (95%): {var_95*100:.2f}%")
print(f"VaR (99%): {var_99*100:.2f}%")
print(f"CVaR/ES (95%): {cvar_95*100:.2f}%")
print(f"CVaR/ES (99%): {cvar_99*100:.2f}%")

# =============================================================================
# 4. Mean Reversion Analysis
# =============================================================================
print("\n" + "=" * 80)
print("[4] Mean Reversion Analysis")
print("=" * 80)

# ADF Test for stationarity
print("\n--- Stationarity Test (ADF) ---")
adf_result = adfuller(tqqq['Close'].dropna())
print(f"ADF Statistic (Price): {adf_result[0]:.4f}")
print(f"P-value: {adf_result[1]:.4f}")
print(f"Stationary: {'Yes' if adf_result[1] < 0.05 else 'No'}")

adf_result_ret = adfuller(returns.dropna())
print(f"\nADF Statistic (Returns): {adf_result_ret[0]:.4f}")
print(f"P-value: {adf_result_ret[1]:.4f}")
print(f"Stationary: {'Yes' if adf_result_ret[1] < 0.05 else 'No'}")

# Hurst Exponent
print("\n--- Hurst Exponent ---")
def hurst_exponent(ts, max_lag=100):
    lags = range(2, min(max_lag, len(ts)//4))
    tau = [np.std(np.subtract(ts[lag:], ts[:-lag])) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0]

hurst_price = hurst_exponent(tqqq['Close'].dropna().values)
hurst_returns = hurst_exponent(returns.dropna().values)
print(f"Hurst Exponent (Price): {hurst_price:.4f}")
print(f"Hurst Exponent (Returns): {hurst_returns:.4f}")
print(f"Interpretation:")
print(f"  H < 0.5: Mean-reverting")
print(f"  H = 0.5: Random walk")
print(f"  H > 0.5: Trending")

# Ornstein-Uhlenbeck Half-life
print("\n--- Ornstein-Uhlenbeck Half-life ---")
# For log prices
log_price = np.log(tqqq['Close'].dropna())
log_price_lag = log_price.shift(1)
delta_log_price = log_price.diff()

# Regression: delta_log_price = alpha + beta * log_price_lag
mask = np.isfinite(log_price_lag) & np.isfinite(delta_log_price)
slope_ou, intercept_ou, _, _, _ = stats.linregress(log_price_lag[mask], delta_log_price[mask])

half_life = -np.log(2) / slope_ou
print(f"OU Process Half-life: {half_life:.2f} days")
print(f"Mean reversion speed (kappa): {-slope_ou:.6f}")

# Autocorrelation Analysis
print("\n--- Autocorrelation Analysis ---")
lags = [1, 2, 3, 5, 10, 20]
for lag in lags:
    autocorr = returns.autocorr(lag=lag)
    print(f"Lag {lag}: {autocorr:.4f}")

# Ljung-Box test
from statsmodels.stats.diagnostic import acorr_ljungbox
lb_test = acorr_ljungbox(returns.dropna(), lags=10, return_df=True)
print(f"\nLjung-Box test (lag 1): {lb_test.iloc[0]['lb_stat']:.4f}, p-value: {lb_test.iloc[0]['lb_pvalue']:.4f}")
print(f"Ljung-Box test (lag 10): {lb_test.iloc[9]['lb_stat']:.4f}, p-value: {lb_test.iloc[9]['lb_pvalue']:.4f}")

# =============================================================================
# 5. Regime Detection
# =============================================================================
print("\n" + "=" * 80)
print("[5] Regime Detection (Bull/Bear/Sideways)")
print("=" * 80)

# Calculate rolling metrics for regime detection
tqqq['MA_50'] = tqqq['Close'].rolling(50).mean()
tqqq['MA_200'] = tqqq['Close'].rolling(200).mean()
tqqq['Vol_20'] = returns.rolling(20).std() * np.sqrt(252)

# Simple regime classification based on moving averages and volatility
def classify_regime(row):
    if pd.isna(row['MA_50']) or pd.isna(row['MA_200']) or pd.isna(row['Vol_20']):
        return 'Unknown'
    
    ma_ratio = row['MA_50'] / row['MA_200']
    vol = row['Vol_20']
    
    # High volatility threshold (75th percentile)
    vol_threshold = tqqq['Vol_20'].quantile(0.75)
    
    if ma_ratio > 1.05 and vol < vol_threshold:
        return 'Bull'
    elif ma_ratio < 0.95 or (ma_ratio < 1.0 and vol > vol_threshold):
        return 'Bear'
    else:
        return 'Sideways'

tqqq['Regime'] = tqqq.apply(classify_regime, axis=1)

# Regime statistics
print("\n--- Regime Distribution ---")
regime_counts = tqqq['Regime'].value_counts()
regime_pct = tqqq['Regime'].value_counts(normalize=True) * 100
for regime in ['Bull', 'Bear', 'Sideways']:
    if regime in regime_counts:
        print(f"{regime}: {regime_counts[regime]} days ({regime_pct[regime]:.1f}%)")

# Regime performance
print("\n--- Performance by Regime ---")
for regime in ['Bull', 'Bear', 'Sideways']:
    mask = tqqq['Regime'] == regime
    regime_returns = tqqq.loc[mask, 'Returns'].dropna()
    if len(regime_returns) > 0:
        print(f"\n{regime} Market:")
        print(f"  Mean daily return: {regime_returns.mean()*100:.4f}%")
        print(f"  Volatility: {regime_returns.std()*np.sqrt(252)*100:.2f}%")
        print(f"  Sharpe (annualized): {regime_returns.mean()/regime_returns.std()*np.sqrt(252):.4f}")
        print(f"  Max daily gain: {regime_returns.max()*100:.2f}%")
        print(f"  Max daily loss: {regime_returns.min()*100:.2f}%")

# Drawdown analysis
tqqq['Cumulative'] = (1 + tqqq['Returns'].fillna(0)).cumprod()
tqqq['Peak'] = tqqq['Cumulative'].cummax()
tqqq['Drawdown'] = (tqqq['Cumulative'] - tqqq['Peak']) / tqqq['Peak']

max_dd = tqqq['Drawdown'].min()
avg_dd = tqqq['Drawdown'][tqqq['Drawdown'] < 0].mean()
print(f"\n--- Drawdown Analysis ---")
print(f"Maximum drawdown: {max_dd*100:.2f}%")
print(f"Average drawdown (when in DD): {avg_dd*100:.2f}%")

# Find major drawdown periods
dd_periods = []
in_dd = False
start_idx = None
for i, dd in enumerate(tqqq['Drawdown']):
    if dd < -0.05 and not in_dd:  # 5% drawdown threshold
        in_dd = True
        start_idx = i
    elif dd > -0.01 and in_dd:  # Recovery to 1% drawdown
        in_dd = False
        if start_idx is not None:
            dd_periods.append((tqqq.index[start_idx], tqqq.index[i], tqqq['Drawdown'].iloc[start_idx:i].min()))

print(f"\nMajor drawdown periods (>5%):")
for start, end, max_dd_period in dd_periods[:5]:
    print(f"  {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}: {max_dd_period*100:.1f}%")

# =============================================================================
# 6. Seasonality and Time-of-Day Analysis
# =============================================================================
print("\n" + "=" * 80)
print("[6] Seasonality and Best Trading Times Analysis")
print("=" * 80)

# Monthly seasonality
tqqq['Month'] = tqqq.index.month
tqqq['Year'] = tqqq.index.year
tqqq['DayOfWeek'] = tqqq.index.dayofweek  # 0=Monday, 6=Sunday
tqqq['Quarter'] = tqqq.index.quarter

print("\n--- Monthly Returns ---")
monthly_returns = tqqq.groupby('Month')['Returns'].agg(['mean', 'std', 'count'])
monthly_returns['mean_pct'] = monthly_returns['mean'] * 100
monthly_returns['annualized_return'] = monthly_returns['mean'] * 252 * 100
monthly_returns['sharpe'] = monthly_returns['mean'] / monthly_returns['std'] * np.sqrt(252)

month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
for month in range(1, 13):
    if month in monthly_returns.index:
        mr = monthly_returns.loc[month]
        print(f"{month_names[month-1]}: Avg={mr['mean_pct']:.3f}%, "
              f"Ann={mr['annualized_return']:.1f}%, "
              f"Sharpe={mr['sharpe']:.3f}")

print("\n--- Day of Week Analysis ---")
dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
dow_returns = tqqq.groupby('DayOfWeek')['Returns'].agg(['mean', 'std', 'count'])
for dow in range(5):  # Monday to Friday
    if dow in dow_returns.index:
        dr = dow_returns.loc[dow]
        print(f"{dow_names[dow]}: Avg={dr['mean']*100:.3f}%, "
              f"Vol={dr['std']*np.sqrt(252)*100:.1f}%, "
              f"Sharpe={dr['mean']/dr['std']*np.sqrt(252):.3f}")

print("\n--- Quarterly Analysis ---")
quarterly_returns = tqqq.groupby('Quarter')['Returns'].agg(['mean', 'std'])
for q in range(1, 5):
    if q in quarterly_returns.index:
        qr = quarterly_returns.loc[q]
        print(f"Q{q}: Avg={qr['mean']*100:.3f}%, "
              f"Ann={qr['mean']*252*100:.1f}%, "
              f"Sharpe={qr['mean']/qr['std']*np.sqrt(252):.3f}")

# Intraday analysis (if we have OHLC data)
print("\n--- Intraday Patterns (Open vs Close) ---")
tqqq['Overnight_Return'] = tqqq['Open'] / tqqq['Close'].shift(1) - 1
tqqq['Intraday_Return'] = tqqq['Close'] / tqqq['Open'] - 1

overnight = tqqq['Overnight_Return'].dropna()
intraday = tqqq['Intraday_Return'].dropna()

print(f"Overnight return (close to open): {overnight.mean()*100:.4f}% avg, {overnight.std()*np.sqrt(252)*100:.2f}% vol")
print(f"Intraday return (open to close): {intraday.mean()*100:.4f}% avg, {intraday.std()*np.sqrt(252)*100:.2f}% vol")
print(f"Overnight Sharpe: {overnight.mean()/overnight.std()*np.sqrt(252):.3f}")
print(f"Intraday Sharpe: {intraday.mean()/intraday.std()*np.sqrt(252):.3f}")

# =============================================================================
# 7. Summary Statistics
# =============================================================================
print("\n" + "=" * 80)
print("[7] Key Statistical Summary")
print("=" * 80)

# Overall performance metrics
total_return = (tqqq['Close'].iloc[-1] / tqqq['Close'].iloc[0] - 1) * 100
cagr = ((tqqq['Close'].iloc[-1] / tqqq['Close'].iloc[0]) ** (252/len(tqqq)) - 1) * 100
annual_vol = returns.std() * np.sqrt(252) * 100
sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
sortino_ratio = returns.mean() / returns[returns < 0].std() * np.sqrt(252)
calmar_ratio = cagr / abs(max_dd * 100) if max_dd != 0 else np.inf

print(f"\n--- Performance Metrics ---")
print(f"Total return: {total_return:.1f}%")
print(f"CAGR: {cagr:.1f}%")
print(f"Annualized volatility: {annual_vol:.1f}%")
print(f"Sharpe ratio: {sharpe_ratio:.3f}")
print(f"Sortino ratio: {sortino_ratio:.3f}")
print(f"Calmar ratio: {calmar_ratio:.3f}")
print(f"Maximum drawdown: {max_dd*100:.1f}%")

# Best and worst periods
print(f"\n--- Extremes ---")
print(f"Best single day: {returns.max()*100:.2f}%")
print(f"Worst single day: {returns.min()*100:.2f}%")
print(f"Best month: {returns.groupby([returns.index.year, returns.index.month]).sum().max()*100:.2f}%")
print(f"Worst month: {returns.groupby([returns.index.year, returns.index.month]).sum().min()*100:.2f}%")

# Positive vs negative days
positive_days = (returns > 0).sum()
negative_days = (returns < 0).sum()
print(f"\n--- Win Rate ---")
print(f"Positive days: {positive_days} ({positive_days/len(returns)*100:.1f}%)")
print(f"Negative days: {negative_days} ({negative_days/len(returns)*100:.1f}%)")
print(f"Average gain (on up days): {returns[returns > 0].mean()*100:.2f}%")
print(f"Average loss (on down days): {returns[returns < 0].mean()*100:.2f}%")
print(f"Gain/Loss ratio: {abs(returns[returns > 0].mean()/returns[returns < 0].mean()):.2f}")

print("\n" + "=" * 80)
print("Analysis Complete!")
print("=" * 80)

# =============================================================================
# 8. Save results to CSV for further analysis
# =============================================================================
print("\n[8] Saving data for visualization...")

# Save processed data
tqqq.to_csv('tqqq_analysis_data.csv')
print("Data saved to: tqqq_analysis_data.csv")

# Create summary report
summary = {
    'Metric': [
        'Data Start Date', 'Data End Date', 'Total Trading Days',
        'Total Return (%)', 'CAGR (%)', 'Annualized Volatility (%)',
        'Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio',
        'Max Drawdown (%)', 'Average Leverage (vs QQQ)', 'Tracking Error (%)',
        'Skewness', 'Kurtosis', 'Hurst Exponent',
        'OU Half-life (days)', 'GARCH Persistence',
        'VaR 95% (%)', 'VaR 99% (%)', 'CVaR 95% (%)',
        'Win Rate (%)', 'Avg Gain (%)', 'Avg Loss (%)', 'Gain/Loss Ratio'
    ],
    'Value': [
        tqqq.index[0].strftime('%Y-%m-%d'), tqqq.index[-1].strftime('%Y-%m-%d'), len(tqqq),
        f"{total_return:.2f}", f"{cagr:.2f}", f"{annual_vol:.2f}",
        f"{sharpe_ratio:.3f}", f"{sortino_ratio:.3f}", f"{calmar_ratio:.3f}",
        f"{max_dd*100:.2f}", f"{rolling_beta.mean():.3f}", f"{tracking_error*100:.2f}",
        f"{returns.skew():.3f}", f"{returns.kurtosis():.3f}", f"{hurst_returns:.3f}",
        f"{half_life:.1f}", f"{res.params['alpha[1]'] + res.params['beta[1]']:.4f}" if 'res' in dir() else 'N/A',
        f"{var_95*100:.2f}", f"{var_99*100:.2f}", f"{cvar_95*100:.2f}",
        f"{positive_days/len(returns)*100:.1f}", f"{returns[returns > 0].mean()*100:.2f}",
        f"{returns[returns < 0].mean()*100:.2f}", f"{abs(returns[returns > 0].mean()/returns[returns < 0].mean()):.2f}"
    ]
}

summary_df = pd.DataFrame(summary)
summary_df.to_csv('tqqq_summary_stats.csv', index=False)
print("Summary saved to: tqqq_summary_stats.csv")

print("\nAll analysis complete! Files generated:")
print("  - tqqq_analysis_data.csv (full time series data)")
print("  - tqqq_summary_stats.csv (key statistics summary)")
