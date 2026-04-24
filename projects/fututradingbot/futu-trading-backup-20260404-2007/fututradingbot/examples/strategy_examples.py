"""
策略使用示例
Strategy Usage Examples

展示如何使用趨勢策略和回測框架
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.strategies.trend_strategy import TrendStrategy, TrendState
from src.strategies.backtest import BacktestEngine, WalkForwardAnalysis
from src.strategies.strategy_config import StrategyConfigManager
from src.strategies.base import SignalType


def example_1_basic_strategy_usage():
    """示例1: 基本策略使用"""
    print("="*60)
    print("示例1: 基本策略使用")
    print("="*60)
    
    # 創建策略實例
    config = {
        'min_analysis_score': 70,
        'take_profit_pct': 0.05,
        'stop_loss_pct': 0.03,
        'fixed_position_pct': 0.02
    }
    
    strategy = TrendStrategy(config=config)
    strategy.initialize()
    
    # 創建模擬數據
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    
    prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 100)))
    df = pd.DataFrame({
        'open': prices * (1 + np.random.normal(0, 0.005, 100)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, 100))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, 100))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    }, index=dates)
    
    # 確保 high >= max(open, close) 且 low <= min(open, close)
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    # 模擬數據輸入
    data = {
        'code': 'TEST.HK',
        'df': df,
        'analysis_score': 75
    }
    
    # 獲取交易信號
    signal = strategy.on_data(data)
    
    if signal:
        print(f"交易信號: {signal.signal.value}")
        print(f"價格: {signal.price}")
        print(f"數量: {signal.qty}")
        print(f"原因: {signal.reason}")
    else:
        print("無交易信號")
    
    print()


def example_2_backtest():
    """示例2: 回測使用"""
    print("="*60)
    print("示例2: 回測使用")
    print("="*60)
    
    # 創建策略
    strategy = TrendStrategy()
    strategy.initialize()
    
    # 創建模擬數據
    np.random.seed(42)
    data = {}
    
    for code in ['AAPL.US', 'TSLA.US']:
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        n = len(dates)
        
        returns = np.random.normal(0.0005, 0.02, n)
        prices = 100 * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, n)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, n)
        }, index=dates)
        
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        data[code] = df
    
    # 創建回測引擎
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=1000000,
        commission_rate=0.001,
        slippage=0.001
    )
    
    # 運行回測
    result = engine.run(data)
    
    # 打印結果
    result.print_summary()
    print()


def example_3_strategy_config():
    """示例3: 策略配置管理"""
    print("="*60)
    print("示例3: 策略配置管理")
    print("="*60)
    
    # 創建配置管理器
    config_manager = StrategyConfigManager(
        config_path='config/strategy_config.yaml'
    )
    
    # 獲取配置
    trend_config = config_manager.get_trend_strategy_config()
    print("趨勢策略配置:")
    for key, value in trend_config.items():
        print(f"  {key}: {value}")
    
    print()
    
    # 更新配置
    config_manager.update_trend_config(
        take_profit_pct=0.06,
        stop_loss_pct=0.025
    )
    
    # 驗證配置
    is_valid, errors = config_manager.validate_config()
    print(f"配置驗證: {'通過' if is_valid else '失敗'}")
    if errors:
        print("錯誤:")
        for error in errors:
            print(f"  - {error}")
    
    print()


def example_4_multi_timeframe_analysis():
    """示例4: 多時間框架分析"""
    print("="*60)
    print("示例4: 多時間框架分析")
    print("="*60)
    
    strategy = TrendStrategy()
    
    # 創建多時間框架數據
    code = 'TEST.HK'
    np.random.seed(42)
    
    # 日線數據
    daily_dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
    daily_prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 60)))
    daily_df = pd.DataFrame({
        'open': daily_prices * (1 + np.random.normal(0, 0.005, 60)),
        'high': daily_prices * (1 + np.abs(np.random.normal(0, 0.01, 60))),
        'low': daily_prices * (1 - np.abs(np.random.normal(0, 0.01, 60))),
        'close': daily_prices,
        'volume': np.random.randint(1000000, 10000000, 60)
    }, index=daily_dates)
    daily_df['high'] = daily_df[['open', 'high', 'close']].max(axis=1)
    daily_df['low'] = daily_df[['open', 'low', 'close']].min(axis=1)
    
    # 更新策略數據緩存
    strategy.tf_data['1d'][code] = daily_df
    
    # 分析趨勢
    trend = strategy._analyze_multi_timeframe_trend(code)
    
    print(f"趨勢狀態: {trend.trend_state.value}")
    print(f"趨勢強度: {trend.trend_strength}")
    print(f"EMA排列: {trend.ema_alignment}")
    print(f"MACD信號: {trend.macd_signal}")
    print(f"多時間框架一致性: {trend.multi_timeframe_align}")
    print()


def example_5_position_sizing():
    """示例5: 倉位計算"""
    print("="*60)
    print("示例5: 倉位計算")
    print("="*60)
    
    strategy = TrendStrategy()
    
    # 創建模擬數據
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    np.random.seed(42)
    
    prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 50)))
    df = pd.DataFrame({
        'open': prices * (1 + np.random.normal(0, 0.005, 50)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, 50))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, 50))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 50)
    }, index=dates)
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    # 評估進場條件
    from src.strategies.trend_strategy import EntryCondition
    entry = EntryCondition()
    entry.analysis_score = 80
    entry.indicator_resonance = 4
    entry.volume_confirmed = True
    entry.rsi_valid = True
    entry.all_conditions_met = True
    
    # 計算倉位
    current_price = df['close'].iloc[-1]
    account_value = 1000000
    
    sizing = strategy._calculate_position_size('TEST.HK', current_price, account_value, entry)
    
    print(f"當前價格: ${current_price:.2f}")
    print(f"賬戶總值: ${account_value:,.2f}")
    print(f"分析評分: {entry.analysis_score}")
    print()
    print("倉位計算結果:")
    print(f"  建議股數: {sizing.position_size}")
    print(f"  持倉市值: ${sizing.position_value:,.2f}")
    print(f"  風險金額: ${sizing.risk_amount:,.2f}")
    print()


def example_6_risk_management():
    """示例6: 風險管理"""
    print("="*60)
    print("示例6: 風險管理")
    print("="*60)
    
    strategy = TrendStrategy(config={
        'take_profit_pct': 0.05,
        'stop_loss_pct': 0.03,
        'use_atr_stop': True,
        'atr_multiplier_sl': 2.0,
        'atr_multiplier_tp': 3.0
    })
    
    # 創建模擬數據
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    np.random.seed(42)
    
    prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 50)))
    df = pd.DataFrame({
        'open': prices * (1 + np.random.normal(0, 0.005, 50)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.015, 50))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.015, 50))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 50)
    }, index=dates)
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    entry_price = df['close'].iloc[-1]
    
    # 計算止損止盈
    stop_loss = strategy._calculate_stop_loss(df, entry_price, 'long')
    take_profit = strategy._calculate_take_profit(df, entry_price, 'long')
    
    print(f"入場價格: ${entry_price:.2f}")
    print(f"止損價格: ${stop_loss:.2f} ({(stop_loss/entry_price-1)*100:.2f}%)")
    print(f"止盈價格: ${take_profit:.2f} ({(take_profit/entry_price-1)*100:.2f}%)")
    print(f"風險收益比: {abs(take_profit-entry_price)/abs(stop_loss-entry_price):.2f}")
    print()


def run_all_examples():
    """運行所有示例"""
    print("\n" + "="*60)
    print("FutuTradingBot 策略引擎使用示例")
    print("="*60 + "\n")
    
    example_1_basic_strategy_usage()
    example_2_backtest()
    example_3_strategy_config()
    example_4_multi_timeframe_analysis()
    example_5_position_sizing()
    example_6_risk_management()
    
    print("="*60)
    print("所有示例運行完成")
    print("="*60)


if __name__ == "__main__":
    run_all_examples()
