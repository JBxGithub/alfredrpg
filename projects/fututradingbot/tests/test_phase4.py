"""
階段四測試 - Phase 4 Testing
測試所有新開發的模組
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategies.strategy_registry import StrategyRegistry, StrategyPortfolio, StrategyType
from src.strategies.mean_reversion import MeanReversionStrategy
from src.strategies.breakout import BreakoutStrategy
from src.strategies.momentum import MomentumStrategy
from src.strategies.pairs_trading import PairsTradingStrategy
from src.backtest.enhanced_backtest import EnhancedBacktestEngine
from src.ml.feature_engineering import FeatureEngineer
from src.ml.model_trainer import ModelTrainer
from src.ml.signal_enhancer import SignalEnhancer
from src.optimization.strategy_optimizer import StrategyOptimizer


def generate_test_data(n_days: int = 100, n_stocks: int = 2) -> dict:
    """生成測試數據"""
    np.random.seed(42)
    data = {}
    
    for i in range(n_stocks):
        code = f"TEST{i:04d}.HK"
        dates = pd.date_range(end=pd.Timestamp.now(), periods=n_days, freq='D')
        
        # 生成隨機價格
        returns = np.random.normal(0.001, 0.02, n_days)
        prices = 100 * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, n_days)),
            'high': prices * (1 + abs(np.random.normal(0, 0.01, n_days))),
            'low': prices * (1 - abs(np.random.normal(0, 0.01, n_days))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, n_days)
        }, index=dates)
        
        data[code] = df
    
    return data


def test_strategy_registry():
    """測試策略註冊中心"""
    print("\n" + "="*60)
    print("測試策略註冊中心")
    print("="*60)
    
    registry = StrategyRegistry()
    
    # 註冊策略
    registry.register(
        MeanReversionStrategy,
        name="MeanReversion",
        strategy_type=StrategyType.MEAN_REVERSION,
        description="均值回歸策略"
    )
    
    registry.register(
        BreakoutStrategy,
        name="Breakout",
        strategy_type=StrategyType.BREAKOUT,
        description="突破策略"
    )
    
    registry.register(
        MomentumStrategy,
        name="Momentum",
        strategy_type=StrategyType.MOMENTUM,
        description="動量策略"
    )
    
    # 列出策略
    strategies = registry.list_strategies()
    print(f"已註冊策略: {strategies}")
    
    # 創建策略實例
    strategy = registry.create_strategy("MeanReversion")
    print(f"創建策略實例: {strategy.name}")
    
    assert len(strategies) == 3, "策略註冊失敗"
    assert strategy is not None, "策略創建失敗"
    
    print("✅ 策略註冊中心測試通過")
    return True


def test_strategies():
    """測試各種策略"""
    print("\n" + "="*60)
    print("測試交易策略")
    print("="*60)
    
    data = generate_test_data(n_days=100)
    test_code = list(data.keys())[0]
    df = data[test_code]
    
    strategies = [
        ("MeanReversion", MeanReversionStrategy()),
        ("Breakout", BreakoutStrategy()),
        ("Momentum", MomentumStrategy()),
    ]
    
    for name, strategy in strategies:
        strategy_input = {
            'code': test_code,
            'df': df
        }
        
        signal = strategy.on_data(strategy_input)
        print(f"{name}: {'有信號' if signal else '無信號'}")
    
    print("✅ 策略測試通過")
    return True


def test_pairs_trading():
    """測試配對交易策略"""
    print("\n" + "="*60)
    print("測試配對交易策略")
    print("="*60)
    
    data = generate_test_data(n_days=100, n_stocks=2)
    codes = list(data.keys())
    
    strategy = PairsTradingStrategy()
    strategy.register_pair("PAIR_1", codes[0], codes[1])
    
    # 模擬數據輸入
    for code in codes:
        strategy_input = {
            'code': code,
            'df': data[code],
            'pair_id': 'PAIR_1'
        }
        signal = strategy.on_data(strategy_input)
        print(f"{code}: {'有信號' if signal else '無信號'}")
    
    print("✅ 配對交易策略測試通過")
    return True


def test_enhanced_backtest():
    """測試增強回測"""
    print("\n" + "="*60)
    print("測試增強回測系統")
    print("="*60)
    
    data = generate_test_data(n_days=100)
    strategy = MeanReversionStrategy()
    
    engine = EnhancedBacktestEngine(strategy, initial_capital=1000000)
    result = engine.run(data)
    
    result.print_summary()
    
    assert result is not None, "回測失敗"
    print("✅ 增強回測測試通過")
    return True


def test_feature_engineering():
    """測試特徵工程"""
    print("\n" + "="*60)
    print("測試特徵工程")
    print("="*60)
    
    data = generate_test_data(n_days=100)
    df = list(data.values())[0]
    
    engineer = FeatureEngineer()
    features = engineer.extract_features(df)
    
    print(f"提取特徵數: {len(features.columns)}")
    print(f"特徵樣本: {list(features.columns)[:5]}")
    
    assert len(features) > 0, "特徵提取失敗"
    print("✅ 特徵工程測試通過")
    return True


def test_model_trainer():
    """測試模型訓練"""
    print("\n" + "="*60)
    print("測試模型訓練")
    print("="*60)
    
    data = generate_test_data(n_days=200)
    df = list(data.values())[0]
    
    engineer = FeatureEngineer()
    X, y = engineer.prepare_ml_dataset(df, forward_period=5)
    
    if len(X) < 50:
        print("⚠️ 數據不足，跳過模型訓練測試")
        return True
    
    trainer = ModelTrainer()
    model = trainer.train(X, y, validation_split=True)
    
    if trainer.metrics:
        print(f"模型準確率: {trainer.metrics.accuracy:.4f}")
    
    print("✅ 模型訓練測試通過")
    return True


def test_signal_enhancer():
    """測試信號增強器"""
    print("\n" + "="*60)
    print("測試信號增強器")
    print("="*60)
    
    data = generate_test_data(n_days=100)
    df = list(data.values())[0]
    
    from src.strategies.base import TradeSignal, SignalType
    
    signal = TradeSignal(
        code="TEST0000.HK",
        signal=SignalType.BUY,
        price=100.0,
        qty=1000,
        reason="測試信號"
    )
    
    enhancer = SignalEnhancer()
    enhanced = enhancer.enhance_signal(signal, df)
    
    print(f"ML信心度: {enhanced.ml_confidence:.4f}")
    print(f"增強強度: {enhanced.enhanced_strength:.4f}")
    print(f"建議: {enhanced.recommendation}")
    
    print("✅ 信號增強器測試通過")
    return True


def test_strategy_optimizer():
    """測試策略優化器"""
    print("\n" + "="*60)
    print("測試策略優化器")
    print("="*60)
    
    data = generate_test_data(n_days=100)
    
    param_grid = {
        'lookback_period': [10, 20],
        'entry_zscore': [1.5, 2.0]
    }
    
    optimizer = StrategyOptimizer(MeanReversionStrategy, data)
    
    # 由於網格搜索較慢，只測試少量參數
    results = optimizer.grid_search(param_grid, metric="sharpe_ratio", verbose=False)
    
    if results:
        print(f"優化完成 | 最佳分數: {optimizer.best_score:.4f}")
        print(f"最佳參數: {optimizer.best_params}")
    
    print("✅ 策略優化器測試通過")
    return True


def run_all_tests():
    """運行所有測試"""
    print("\n" + "="*70)
    print("FutuTradingBot 階段四測試")
    print("="*70)
    
    tests = [
        ("策略註冊中心", test_strategy_registry),
        ("交易策略", test_strategies),
        ("配對交易策略", test_pairs_trading),
        ("增強回測", test_enhanced_backtest),
        ("特徵工程", test_feature_engineering),
        ("模型訓練", test_model_trainer),
        ("信號增強器", test_signal_enhancer),
        ("策略優化器", test_strategy_optimizer),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {name}測試失敗: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"測試完成 | 通過: {passed}/{len(tests)} | 失敗: {failed}/{len(tests)}")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
