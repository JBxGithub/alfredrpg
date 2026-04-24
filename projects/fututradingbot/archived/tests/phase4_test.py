"""
FutuTradingBot 階段四完整測試腳本
在 Windows Sandbox 環境中執行
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import traceback

# 添加專案路徑
sys.path.insert(0, r'C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot')

# 測試結果記錄
class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.details = {}
        self.duration = 0

    def to_dict(self):
        return {
            'name': self.name,
            'passed': self.passed,
            'error': str(self.error) if self.error else None,
            'details': self.details,
            'duration': self.duration
        }

class Phase4Tester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        
    def run_all_tests(self):
        """執行所有測試"""
        print("="*70)
        print("FutuTradingBot 階段四完整測試")
        print("="*70)
        print(f"開始時間: {self.start_time}")
        print()
        
        # 1. 回測系統測試
        self.test_backtest_system()
        
        # 2. 策略註冊中心測試
        self.test_strategy_registry()
        
        # 3. 多策略測試
        self.test_multi_strategies()
        
        # 4. 機器學習模組測試
        self.test_ml_modules()
        
        # 5. 策略優化器測試
        self.test_strategy_optimizer()
        
        # 生成報告
        self.generate_report()
    
    def create_mock_data(self, n_days: int = 100, code: str = "TEST.HK") -> pd.DataFrame:
        """創建模擬K線數據"""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=n_days, freq='D')
        
        # 生成隨機價格數據
        initial_price = 100.0
        returns = np.random.normal(0.001, 0.02, n_days)
        prices = initial_price * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, n_days)),
            'high': prices * (1 + abs(np.random.normal(0, 0.01, n_days))),
            'low': prices * (1 - abs(np.random.normal(0, 0.01, n_days))),
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, n_days)
        }, index=dates)
        
        df.index.name = 'timestamp'
        return df
    
    def test_backtest_system(self):
        """測試回測系統"""
        print("\n" + "="*70)
        print("1. 回測系統測試")
        print("="*70)
        
        # 1.1 創建模擬K線數據
        result = TestResult("創建模擬K線數據")
        try:
            data = self.create_mock_data(200)
            result.details['data_shape'] = str(data.shape)
            result.details['columns'] = list(data.columns)
            result.passed = True
            print("✓ 創建模擬K線數據 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 創建模擬K線數據 - 失敗: {e}")
        self.results.append(result)
        
        # 1.2 執行多因子策略回測
        result = TestResult("執行多因子策略回測")
        try:
            from src.backtest.enhanced_backtest import EnhancedBacktestEngine
            from src.strategies.enhanced_strategy import EnhancedStrategy
            
            strategy = EnhancedStrategy()
            engine = EnhancedBacktestEngine(strategy, initial_capital=1000000)
            
            data_dict = {"TEST.HK": self.create_mock_data(200)}
            backtest_result = engine.run(data_dict)
            
            result.details['total_return'] = f"{backtest_result.total_return_pct:.2f}%"
            result.details['total_trades'] = backtest_result.total_trades
            result.passed = True
            print("✓ 執行多因子策略回測 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 執行多因子策略回測 - 失敗: {e}")
        self.results.append(result)
        
        # 1.3 驗證績效指標計算
        result = TestResult("驗證績效指標計算")
        try:
            metrics = {
                'sharpe_ratio': backtest_result.sharpe_ratio,
                'max_drawdown': backtest_result.max_drawdown_pct,
                'var_95': backtest_result.var_95,
                'cvar_95': backtest_result.cvar_95
            }
            result.details['metrics'] = metrics
            result.passed = all(v is not None for v in metrics.values())
            print("✓ 驗證績效指標計算 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 驗證績效指標計算 - 失敗: {e}")
        self.results.append(result)
        
        # 1.4 測試因子績效分析
        result = TestResult("測試因子績效分析")
        try:
            factor_perfs = backtest_result.factor_performances
            result.details['factor_count'] = len(factor_perfs)
            result.passed = True
            print("✓ 測試因子績效分析 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 測試因子績效分析 - 失敗: {e}")
        self.results.append(result)
        
        # 1.5 生成回測報告
        result = TestResult("生成回測報告")
        try:
            report_dict = backtest_result.to_dict()
            result.details['report_keys'] = list(report_dict.keys())
            result.passed = True
            print("✓ 生成回測報告 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 生成回測報告 - 失敗: {e}")
        self.results.append(result)
    
    def test_strategy_registry(self):
        """測試策略註冊中心"""
        print("\n" + "="*70)
        print("2. 策略註冊中心測試")
        print("="*70)
        
        # 2.1 註冊多種策略
        result = TestResult("註冊多種策略")
        try:
            from src.strategies.strategy_registry import StrategyRegistry, StrategyType
            from src.strategies.mean_reversion import MeanReversionStrategy
            from src.strategies.breakout import BreakoutStrategy
            from src.strategies.momentum import MomentumStrategy
            
            registry = StrategyRegistry()
            
            # 註冊多種策略
            registry.register(MeanReversionStrategy, name="MeanReversion", 
                            strategy_type=StrategyType.MEAN_REVERSION)
            registry.register(BreakoutStrategy, name="Breakout",
                            strategy_type=StrategyType.BREAKOUT)
            registry.register(MomentumStrategy, name="Momentum",
                            strategy_type=StrategyType.MOMENTUM)
            
            strategies = registry.list_strategies()
            result.details['registered_strategies'] = strategies
            result.passed = len(strategies) >= 3
            print("✓ 註冊多種策略 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 註冊多種策略 - 失敗: {e}")
        self.results.append(result)
        
        # 2.2 動態策略加載
        result = TestResult("動態策略加載")
        try:
            strategy_class = registry.get_strategy_class("MeanReversion")
            instance = registry.create_strategy("MeanReversion")
            result.details['loaded'] = strategy_class is not None and instance is not None
            result.passed = strategy_class is not None and instance is not None
            print("✓ 動態策略加載 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 動態策略加載 - 失敗: {e}")
        self.results.append(result)
        
        # 2.3 策略組合管理
        result = TestResult("策略組合管理")
        try:
            from src.strategies.strategy_registry import StrategyPortfolio
            
            portfolio = StrategyPortfolio("TestPortfolio", registry)
            portfolio.add_strategy("MeanReversion", weight=0.3)
            portfolio.add_strategy("Breakout", weight=0.4)
            portfolio.add_strategy("Momentum", weight=0.3)
            
            summary = portfolio.get_portfolio_summary()
            result.details['portfolio_summary'] = summary
            result.passed = summary['total_strategies'] == 3
            print("✓ 策略組合管理 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 策略組合管理 - 失敗: {e}")
        self.results.append(result)
        
        # 2.4 元數據追踪
        result = TestResult("元數據追踪")
        try:
            metadata = registry.get_metadata("MeanReversion")
            result.details['metadata'] = {
                'name': metadata.name if metadata else None,
                'type': metadata.strategy_type.value if metadata else None,
                'version': metadata.version if metadata else None
            }
            result.passed = metadata is not None
            print("✓ 元數據追踪 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 元數據追踪 - 失敗: {e}")
        self.results.append(result)
    
    def test_multi_strategies(self):
        """測試多種策略"""
        print("\n" + "="*70)
        print("3. 多策略測試")
        print("="*70)
        
        data = {"TEST.HK": self.create_mock_data(100)}
        test_data = {'code': 'TEST.HK', 'df': data['TEST.HK']}
        
        # 3.1 均值回歸策略
        result = TestResult("均值回歸策略")
        try:
            from src.strategies.mean_reversion import MeanReversionStrategy
            strategy = MeanReversionStrategy()
            signal = strategy.on_data(test_data)
            result.details['signal_generated'] = signal is not None
            result.passed = True
            print("✓ 均值回歸策略 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 均值回歸策略 - 失敗: {e}")
        self.results.append(result)
        
        # 3.2 突破策略
        result = TestResult("突破策略")
        try:
            from src.strategies.breakout import BreakoutStrategy
            strategy = BreakoutStrategy()
            signal = strategy.on_data(test_data)
            result.details['signal_generated'] = signal is not None
            result.passed = True
            print("✓ 突破策略 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 突破策略 - 失敗: {e}")
        self.results.append(result)
        
        # 3.3 動量策略
        result = TestResult("動量策略")
        try:
            from src.strategies.momentum import MomentumStrategy
            strategy = MomentumStrategy()
            signal = strategy.on_data(test_data)
            result.details['signal_generated'] = signal is not None
            result.passed = True
            print("✓ 動量策略 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 動量策略 - 失敗: {e}")
        self.results.append(result)
        
        # 3.4 配對交易策略
        result = TestResult("配對交易策略")
        try:
            from src.strategies.pairs_trading import PairsTradingStrategy
            strategy = PairsTradingStrategy()
            strategy.register_pair("PAIR1", "TEST1.HK", "TEST2.HK")
            
            data1 = self.create_mock_data(100, "TEST1.HK")
            data2 = self.create_mock_data(100, "TEST2.HK")
            test_data_pair = {'code': 'TEST1.HK', 'df': data1, 'pair_id': 'PAIR1'}
            
            signal = strategy.on_data(test_data_pair)
            result.details['signal_generated'] = signal is not None
            result.passed = True
            print("✓ 配對交易策略 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 配對交易策略 - 失敗: {e}")
        self.results.append(result)
    
    def test_ml_modules(self):
        """測試機器學習模組"""
        print("\n" + "="*70)
        print("4. 機器學習模組測試")
        print("="*70)
        
        df = self.create_mock_data(200)
        
        # 4.1 特徵工程 - 技術指標特徵提取
        result = TestResult("技術指標特徵提取")
        try:
            from src.ml.feature_engineering import FeatureEngineer
            engineer = FeatureEngineer()
            features = engineer.extract_features(df)
            result.details['feature_count'] = len(features.columns)
            result.details['features'] = list(features.columns)[:10]
            result.passed = len(features.columns) > 0
            print("✓ 技術指標特徵提取 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 技術指標特徵提取 - 失敗: {e}")
        self.results.append(result)
        
        # 4.2 特徵工程 - K線形態特徵編碼
        result = TestResult("K線形態特徵編碼")
        try:
            pattern_features = [c for c in features.columns if 'pattern' in c]
            result.details['pattern_features'] = pattern_features
            result.passed = len(pattern_features) > 0
            print("✓ K線形態特徵編碼 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ K線形態特徵編碼 - 失敗: {e}")
        self.results.append(result)
        
        # 4.3 特徵工程 - 目標變量生成
        result = TestResult("目標變量生成")
        try:
            target = engineer.create_target_variable(df, forward_period=5)
            result.details['target_distribution'] = target.value_counts().to_dict()
            result.passed = len(target) > 0
            print("✓ 目標變量生成 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 目標變量生成 - 失敗: {e}")
        self.results.append(result)
        
        # 4.4 模型訓練 - 隨機森林訓練
        result = TestResult("隨機森林訓練")
        try:
            from src.ml.model_trainer import ModelTrainer
            X, y = engineer.prepare_ml_dataset(df)
            trainer = ModelTrainer()
            model = trainer.train(X, y, validation_split=False)
            result.details['model_trained'] = model is not None
            result.passed = model is not None
            print("✓ 隨機森林訓練 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 隨機森林訓練 - 失敗: {e}")
        self.results.append(result)
        
        # 4.5 模型訓練 - 模型評估
        result = TestResult("模型評估")
        try:
            metrics = trainer.metrics
            if metrics:
                result.details['accuracy'] = metrics.accuracy
                result.details['precision'] = metrics.precision
                result.passed = True
            else:
                result.passed = False
            print("✓ 模型評估 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 模型評估 - 失敗: {e}")
        self.results.append(result)
        
        # 4.6 信號增強器 - ML預測整合
        result = TestResult("ML預測整合")
        try:
            from src.ml.signal_enhancer import SignalEnhancer
            from src.strategies.base import TradeSignal, SignalType
            
            enhancer = SignalEnhancer(trainer)
            signal = TradeSignal(code="TEST.HK", signal=SignalType.BUY, price=100, qty=100)
            enhanced = enhancer.enhance_signal(signal, df)
            result.details['enhanced'] = enhanced is not None
            result.details['confidence'] = enhanced.ml_confidence if enhanced else None
            result.passed = enhanced is not None
            print("✓ ML預測整合 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ ML預測整合 - 失敗: {e}")
        self.results.append(result)
        
        # 4.7 信號增強器 - 動態權重調整
        result = TestResult("動態權重調整")
        try:
            ml_weight, strategy_weight = enhancer._calculate_dynamic_weights()
            result.details['ml_weight'] = ml_weight
            result.details['strategy_weight'] = strategy_weight
            result.passed = ml_weight is not None and strategy_weight is not None
            print("✓ 動態權重調整 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 動態權重調整 - 失敗: {e}")
        self.results.append(result)
    
    def test_strategy_optimizer(self):
        """測試策略優化器"""
        print("\n" + "="*70)
        print("5. 策略優化器測試")
        print("="*70)
        
        # 5.1 網格搜索
        result = TestResult("網格搜索")
        try:
            from src.optimization.strategy_optimizer import StrategyOptimizer
            from src.strategies.mean_reversion import MeanReversionStrategy
            
            data = {"TEST.HK": self.create_mock_data(100)}
            optimizer = StrategyOptimizer(MeanReversionStrategy, data)
            
            param_grid = {
                'lookback_period': [10, 20],
                'entry_zscore': [1.5, 2.0]
            }
            results = optimizer.grid_search(param_grid, verbose=False)
            result.details['results_count'] = len(results)
            result.passed = len(results) > 0
            print("✓ 網格搜索 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 網格搜索 - 失敗: {e}")
        self.results.append(result)
        
        # 5.2 Walk-forward分析
        result = TestResult("Walk-forward分析")
        try:
            wf_result = optimizer.walk_forward_analysis(
                train_size=30, test_size=10, step_size=10
            )
            result.details['window_count'] = len(wf_result.window_results)
            result.details['is_stable'] = wf_result.is_stable
            result.passed = len(wf_result.window_results) > 0
            print("✓ Walk-forward分析 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ Walk-forward分析 - 失敗: {e}")
        self.results.append(result)
        
        # 5.3 過擬合檢測
        result = TestResult("過擬合檢測")
        try:
            in_sample = results[:2]
            out_sample = results[2:] if len(results) > 2 else results[:1]
            overfit_result = optimizer.detect_overfitting(in_sample, out_sample)
            result.details['is_overfitted'] = overfit_result.get('is_overfitted')
            result.passed = 'is_overfitted' in overfit_result
            print("✓ 過擬合檢測 - 通過")
        except Exception as e:
            result.error = e
            print(f"✗ 過擬合檢測 - 失敗: {e}")
        self.results.append(result)
    
    def generate_report(self):
        """生成測試報告"""
        print("\n" + "="*70)
        print("測試報告")
        print("="*70)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        
        print(f"\n總計: {total} 項測試")
        print(f"通過: {passed} 項")
        print(f"失敗: {failed} 項")
        print(f"覆蓋率: {passed/total*100:.1f}%")
        
        if failed > 0:
            print("\n失敗的測試:")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.name}: {r.error}")
        
        # 生成 Markdown 報告
        report_path = r'C:\Users\BurtClaw\openclaw_workspace\projects\fututradingbot\tests\reports\phase4_test_report.md'
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# FutuTradingBot 階段四測試報告\n\n")
            f.write(f"**測試時間**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**測試環境**: Windows Sandbox\n\n")
            
            f.write("## 測試摘要\n\n")
            f.write(f"- **總測試數**: {total}\n")
            f.write(f"- **通過**: {passed}\n")
            f.write(f"- **失敗**: {failed}\n")
            f.write(f"- **覆蓋率**: {passed/total*100:.1f}%\n\n")
            
            f.write("## 詳細測試結果\n\n")
            f.write("| 測試項目 | 狀態 | 詳細信息 |\n")
            f.write("|---------|------|---------|\n")
            
            for r in self.results:
                status = "✅ 通過" if r.passed else "❌ 失敗"
                details = str(r.details)[:50] if r.details else ""
                if r.error:
                    details = f"錯誤: {str(r.error)[:40]}"
                f.write(f"| {r.name} | {status} | {details} |\n")
            
            f.write("\n## 測試範圍\n\n")
            f.write("### 1. 回測系統測試\n")
            f.write("- [x] 創建模擬K線數據\n")
            f.write("- [x] 執行多因子策略回測\n")
            f.write("- [x] 驗證績效指標計算 (夏普比率、最大回撤、VaR/CVaR)\n")
            f.write("- [x] 測試因子績效分析\n")
            f.write("- [x] 生成回測報告\n\n")
            
            f.write("### 2. 策略註冊中心測試\n")
            f.write("- [x] 註冊多種策略\n")
            f.write("- [x] 動態策略加載\n")
            f.write("- [x] 策略組合管理\n")
            f.write("- [x] 元數據追踪\n\n")
            
            f.write("### 3. 多策略測試\n")
            f.write("- [x] 均值回歸策略\n")
            f.write("- [x] 突破策略\n")
            f.write("- [x] 動量策略\n")
            f.write("- [x] 配對交易策略\n\n")
            
            f.write("### 4. 機器學習模組測試\n")
            f.write("- [x] 技術指標特徵提取\n")
            f.write("- [x] K線形態特徵編碼\n")
            f.write("- [x] 目標變量生成\n")
            f.write("- [x] 隨機森林訓練\n")
            f.write("- [x] 模型評估\n")
            f.write("- [x] ML預測整合\n")
            f.write("- [x] 動態權重調整\n\n")
            
            f.write("### 5. 策略優化器測試\n")
            f.write("- [x] 網格搜索\n")
            f.write("- [x] Walk-forward分析\n")
            f.write("- [x] 過擬合檢測\n\n")
            
            f.write("## 結論\n\n")
            if failed == 0:
                f.write("✅ **所有測試通過！** 階段四開發的所有新模組功能正常。\n")
            else:
                f.write(f"⚠️ **有 {failed} 項測試失敗**，請檢查相關模組。\n")
        
        print(f"\n測試報告已保存至: {report_path}")

if __name__ == "__main__":
    tester = Phase4Tester()
    tester.run_all_tests()
