"""
策略引擎測試
Strategy Engine Tests
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.strategies.trend_strategy import (
    TrendStrategy, TrendState, EntryCondition, 
    PositionSizing, TrendAnalysis
)
from src.strategies.backtest import BacktestEngine, BacktestResult
from src.strategies.strategy_config import StrategyConfigManager
from src.strategies.base import SignalType


class TestTrendStrategy(unittest.TestCase):
    """測試趨勢策略"""
    
    def setUp(self):
        """測試前準備"""
        self.config = {
            'min_analysis_score': 70,
            'take_profit_pct': 0.05,
            'stop_loss_pct': 0.03,
            'fixed_position_pct': 0.02
        }
        self.strategy = TrendStrategy(config=self.config)
        
        # 創建模擬數據
        self.dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, 100)))
        self.df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, 100)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, 100))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, 100))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, 100)
        }, index=self.dates)
        
        self.df['high'] = self.df[['open', 'high', 'close']].max(axis=1)
        self.df['low'] = self.df[['open', 'low', 'close']].min(axis=1)
    
    def test_strategy_initialization(self):
        """測試策略初始化"""
        self.assertEqual(self.strategy.name, "TrendFollowing")
        self.assertEqual(self.strategy.config['min_analysis_score'], 70)
        self.assertEqual(self.strategy.config['take_profit_pct'], 0.05)
    
    def test_entry_conditions_evaluation(self):
        """測試進場條件評估"""
        entry = self.strategy._evaluate_entry_conditions(self.df, analysis_score=75)
        
        self.assertIsInstance(entry, EntryCondition)
        self.assertEqual(entry.analysis_score, 75)
        self.assertIsInstance(entry.indicator_resonance, int)
    
    def test_multi_timeframe_analysis(self):
        """測試多時間框架分析"""
        code = 'TEST.HK'
        self.strategy.tf_data['1d'][code] = self.df
        
        trend = self.strategy._analyze_multi_timeframe_trend(code)
        
        self.assertIsInstance(trend, TrendAnalysis)
        self.assertIsInstance(trend.trend_state, TrendState)
        self.assertGreaterEqual(trend.trend_strength, 0)
        self.assertLessEqual(trend.trend_strength, 100)
    
    def test_position_sizing(self):
        """測試倉位計算"""
        entry = EntryCondition()
        entry.analysis_score = 80
        entry.indicator_resonance = 4
        entry.volume_confirmed = True
        entry.rsi_valid = True
        entry.all_conditions_met = True
        
        current_price = self.df['close'].iloc[-1]
        account_value = 1000000
        
        sizing = self.strategy._calculate_position_size(
            'TEST.HK', current_price, account_value, entry
        )
        
        self.assertIsInstance(sizing, PositionSizing)
        self.assertGreaterEqual(sizing.position_size, 0)
        self.assertGreaterEqual(sizing.position_value, 0)
    
    def test_stop_loss_calculation(self):
        """測試止損計算"""
        entry_price = 100.0
        
        stop_loss = self.strategy._calculate_stop_loss(
            self.df, entry_price, 'long'
        )
        
        self.assertLess(stop_loss, entry_price)
    
    def test_take_profit_calculation(self):
        """測試止盈計算"""
        entry_price = 100.0
        
        take_profit = self.strategy._calculate_take_profit(
            self.df, entry_price, 'long'
        )
        
        self.assertGreater(take_profit, entry_price)


class TestBacktestEngine(unittest.TestCase):
    """測試回測引擎"""
    
    def setUp(self):
        """測試前準備"""
        self.strategy = TrendStrategy()
        
        # 創建模擬數據
        np.random.seed(42)
        self.data = {}
        
        for code in ['TEST1.HK', 'TEST2.HK']:
            dates = pd.date_range(start='2023-01-01', end='2023-06-01', freq='D')
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
            
            self.data[code] = df
    
    def test_backtest_initialization(self):
        """測試回測引擎初始化"""
        engine = BacktestEngine(
            strategy=self.strategy,
            initial_capital=1000000,
            commission_rate=0.001
        )
        
        self.assertEqual(engine.initial_capital, 1000000)
        self.assertEqual(engine.commission_rate, 0.001)
        self.assertEqual(engine.cash, 1000000)
    
    def test_backtest_run(self):
        """測試回測運行"""
        engine = BacktestEngine(
            strategy=self.strategy,
            initial_capital=1000000
        )
        
        result = engine.run(self.data)
        
        self.assertIsInstance(result, BacktestResult)
        self.assertEqual(result.initial_capital, 1000000)
        self.assertIsNotNone(result.equity_curve)


class TestStrategyConfig(unittest.TestCase):
    """測試策略配置"""
    
    def setUp(self):
        """測試前準備"""
        self.config_manager = StrategyConfigManager()
    
    def test_config_loading(self):
        """測試配置加載"""
        trend_config = self.config_manager.get_trend_strategy_config()
        
        self.assertIsInstance(trend_config, dict)
        self.assertIn('ema_fast', trend_config)
        self.assertIn('take_profit_pct', trend_config)
    
    def test_config_validation(self):
        """測試配置驗證"""
        is_valid, errors = self.config_manager.validate_config()
        
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(errors, list)
    
    def test_config_update(self):
        """測試配置更新"""
        original_config = self.config_manager.get_trend_strategy_config()
        original_tp = original_config['take_profit_pct']
        
        self.config_manager.update_trend_config(take_profit_pct=0.06)
        
        updated_config = self.config_manager.get_trend_strategy_config()
        self.assertEqual(updated_config['take_profit_pct'], 0.06)
        
        # 恢復原配置
        self.config_manager.update_trend_config(take_profit_pct=original_tp)


class TestIntegration(unittest.TestCase):
    """集成測試"""
    
    def test_full_workflow(self):
        """測試完整工作流程"""
        # 1. 加載配置
        config_manager = StrategyConfigManager()
        config = config_manager.get_trend_strategy_config()
        
        # 2. 創建策略
        strategy = TrendStrategy(config=config)
        strategy.initialize()
        
        # 3. 準備數據
        dates = pd.date_range(start='2023-01-01', end='2023-03-01', freq='D')
        np.random.seed(42)
        
        prices = 100 * np.exp(np.cumsum(np.random.normal(0.001, 0.02, len(dates))))
        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, len(dates))),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, len(dates)))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, len(dates)))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, len(dates))
        }, index=dates)
        df['high'] = df[['open', 'high', 'close']].max(axis=1)
        df['low'] = df[['open', 'low', 'close']].min(axis=1)
        
        data = {'TEST.HK': df}
        
        # 4. 運行回測
        engine = BacktestEngine(strategy=strategy, initial_capital=1000000)
        result = engine.run(data)
        
        # 5. 驗證結果
        self.assertIsNotNone(result)
        self.assertEqual(result.initial_capital, 1000000)
        self.assertIsNotNone(result.equity_curve)


def run_tests():
    """運行所有測試"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加測試類
    suite.addTests(loader.loadTestsFromTestCase(TestTrendStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestBacktestEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestStrategyConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
