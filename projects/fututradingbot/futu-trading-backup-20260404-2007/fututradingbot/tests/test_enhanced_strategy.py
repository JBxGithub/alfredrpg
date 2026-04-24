"""
增強版策略測試腳本 - Test Enhanced Strategy

測試項目:
1. K線形態識別準確性
2. 情緒指標計算
3. 多因子共振邏輯
4. 策略信號生成

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import unittest

from src.indicators.candlestick_patterns import (
    CandlestickAnalyzer, PatternType, CandlestickPattern,
    detect_doji, detect_hammer, detect_shooting_star, detect_marubozu,
    detect_engulfing, detect_harami, detect_morning_star, detect_evening_star,
    calculate_pattern_strength
)
from src.analysis.market_sentiment import (
    MarketSentimentAnalyzer, MarketSentiment, MarketPhase,
    calculate_fear_greed_index, detect_volume_anomaly
)
from src.strategies.enhanced_strategy import (
    EnhancedStrategy, SignalFactor, MultiFactorScore, FactorSignal
)
from src.indicators.technical import TechnicalIndicators


class TestCandlestickPatterns(unittest.TestCase):
    """測試K線形態識別"""
    
    def setUp(self):
        self.analyzer = CandlestickAnalyzer()
    
    def test_doji_detection(self):
        """測試十字星識別"""
        # 創建十字星數據
        df = pd.DataFrame({
            'open': [100.0, 101.0, 100.5],
            'high': [102.0, 103.0, 101.0],
            'low': [98.0, 99.0, 100.0],
            'close': [100.02, 101.02, 100.52],  # 開盤≈收盤
            'volume': [1000, 1200, 1100]
        })
        
        pattern = self.analyzer.detect_at_index(df, 2)
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_type, PatternType.DOJI)
        print(f"✓ 十字星識別測試通過: {pattern.description}")
    
    def test_hammer_detection(self):
        """測試錘子線識別"""
        df = pd.DataFrame({
            'open': [100.0, 100.0, 100.0],
            'high': [101.0, 101.0, 100.5],
            'low': [99.0, 99.0, 95.0],  # 長下影線
            'close': [100.5, 100.5, 100.2],  # 小實體在頂部
            'volume': [1000, 1200, 1500]
        })
        
        pattern = self.analyzer.detect_at_index(df, 2)
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_type, PatternType.HAMMER)
        print(f"✓ 錘子線識別測試通過: {pattern.description}")
    
    def test_shooting_star_detection(self):
        """測試射擊之星識別"""
        df = pd.DataFrame({
            'open': [100.0, 100.0, 100.0],
            'high': [101.0, 101.0, 105.0],  # 長上影線
            'low': [99.0, 99.0, 99.5],
            'close': [99.5, 99.5, 99.8],  # 小實體在底部
            'volume': [1000, 1200, 1500]
        })
        
        pattern = self.analyzer.detect_at_index(df, 2)
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_type, PatternType.SHOOTING_STAR)
        print(f"✓ 射擊之星識別測試通過: {pattern.description}")
    
    def test_marubozu_detection(self):
        """測試光頭光腳識別"""
        df = pd.DataFrame({
            'open': [100.0, 100.0, 100.0],
            'high': [102.0, 102.0, 105.0],
            'low': [100.0, 100.0, 100.0],  # 無下影線
            'close': [101.9, 101.9, 104.9],  # 接近最高價
            'volume': [1000, 1200, 1500]
        })
        
        pattern = self.analyzer.detect_at_index(df, 2)
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_type, PatternType.MARUBOZU_BULLISH)
        print(f"✓ 光頭光腳陽線識別測試通過: {pattern.description}")
    
    def test_engulfing_detection(self):
        """測試吞沒形態識別"""
        df = pd.DataFrame({
            'open': [102.0, 101.0, 99.0],  # 第一根陰線
            'high': [103.0, 102.0, 103.0],
            'low': [100.0, 99.0, 98.0],
            'close': [100.5, 99.5, 102.5],  # 第二根陽線吞沒第一根
            'volume': [1000, 1200, 2000]
        })
        
        pattern = self.analyzer.detect_at_index(df, 2)
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_type, PatternType.ENGULFING_BULLISH)
        print(f"✓ 看漲吞沒識別測試通過: {pattern.description}")
    
    def test_morning_star_detection(self):
        """測試晨星形態識別"""
        df = pd.DataFrame({
            'open': [105.0, 100.0, 99.5],  # 第一根大陰線
            'high': [106.0, 101.0, 103.0],
            'low': [100.0, 99.0, 99.0],  # 中間小實體
            'close': [100.0, 99.8, 102.5],  # 第三根大陽線
            'volume': [2000, 1000, 2500]
        })
        
        pattern = self.analyzer.detect_at_index(df, 2)
        self.assertIsNotNone(pattern)
        self.assertEqual(pattern.pattern_type, PatternType.MORNING_STAR)
        print(f"✓ 晨星形態識別測試通過: {pattern.description}")
    
    def test_pattern_scoring(self):
        """測試形態評分系統"""
        df = pd.DataFrame({
            'open': [100.0] * 30,
            'high': [102.0] * 30,
            'low': [98.0] * 30,
            'close': [100.0 + i * 0.1 for i in range(30)],  # 上升趨勢
            'volume': [1000 + i * 10 for i in range(30)]
        })
        
        # 在最後一根創建錘子線
        df.loc[29, 'low'] = 95.0
        df.loc[29, 'close'] = 100.5
        
        pattern = self.analyzer.detect_at_index(df, 29)
        self.assertIsNotNone(pattern)
        self.assertGreater(pattern.overall_score, 0)
        self.assertGreaterEqual(pattern.position_score, 0)
        self.assertGreaterEqual(pattern.volume_score, 0)
        self.assertGreaterEqual(pattern.trend_score, 0)
        print(f"✓ 形態評分系統測試通過: 總分={pattern.overall_score:.2f}")


class TestMarketSentiment(unittest.TestCase):
    """測試市場情緒分析"""
    
    def setUp(self):
        self.analyzer = MarketSentimentAnalyzer()
    
    def test_fear_greed_index(self):
        """測試恐懼/貪婪指數計算"""
        # 創建上升趨勢數據 (應該顯示貪婪)
        df = pd.DataFrame({
            'open': [100.0 + i * 0.5 for i in range(30)],
            'high': [102.0 + i * 0.5 for i in range(30)],
            'low': [98.0 + i * 0.5 for i in range(30)],
            'close': [101.0 + i * 0.6 for i in range(30)],
            'volume': [1000 + i * 50 for i in range(30)]
        })
        
        fgi = calculate_fear_greed_index(df)
        self.assertGreaterEqual(fgi, 0)
        self.assertLessEqual(fgi, 100)
        print(f"✓ 恐懼/貪婪指數測試通過: FGI={fgi:.2f}")
    
    def test_volume_anomaly_detection(self):
        """測試成交量異常檢測"""
        df = pd.DataFrame({
            'open': [100.0] * 30,
            'high': [102.0] * 30,
            'low': [98.0] * 30,
            'close': [100.0] * 30,
            'volume': [1000] * 29 + [5000]  # 最後一根成交量異常
        })
        
        anomaly = detect_volume_anomaly(df, threshold=2.0)
        self.assertTrue(anomaly['is_anomaly'])
        self.assertGreater(anomaly['ratio'], 2.0)
        print(f"✓ 成交量異常檢測測試通過: 異常={anomaly['is_anomaly']}, 比率={anomaly['ratio']:.2f}")
    
    def test_bull_bear_detection(self):
        """測試牛熊市判別"""
        # 牛市數據 (價格在200日均線之上)
        df = pd.DataFrame({
            'open': [100.0 + i * 0.2 for i in range(250)],
            'high': [102.0 + i * 0.2 for i in range(250)],
            'low': [98.0 + i * 0.2 for i in range(250)],
            'close': [101.0 + i * 0.2 for i in range(250)],
            'volume': [1000] * 250
        })
        
        result = self.analyzer.detect_bull_bear(df)
        self.assertIn('trend', result)
        self.assertIn('signal', result)
        self.assertIn('strength', result)
        print(f"✓ 牛熊市判別測試通過: 趨勢={result['trend']}, 信號={result['signal']}")
    
    def test_market_breadth(self):
        """測試市場廣度計算"""
        df = pd.DataFrame({
            'open': [100.0] * 30,
            'high': [102.0] * 30,
            'low': [98.0] * 30,
            'close': [100.0 + i * 0.1 for i in range(30)],
            'volume': [1000] * 30
        })
        
        breadth = self.analyzer.calculate_market_breadth(df)
        self.assertGreaterEqual(breadth, 0)
        self.assertLessEqual(breadth, 100)
        print(f"✓ 市場廣度測試通過: 廣度={breadth:.2f}")
    
    def test_money_flow_analysis(self):
        """測試資金流向分析"""
        df = pd.DataFrame({
            'open': [100.0] * 30,
            'high': [102.0] * 30,
            'low': [98.0] * 30,
            'close': [100.0 + i * 0.1 for i in range(30)],  # 上升趨勢
            'volume': [1000 + i * 10 for i in range(30)]
        })
        
        money_flow = self.analyzer.analyze_money_flow(df)
        self.assertIsNotNone(money_flow)
        self.assertTrue(money_flow.is_positive())  # 上升趨勢應該有資金流入
        print(f"✓ 資金流向分析測試通過: 淨流入={money_flow.net_inflow:.2f}")
    
    def test_liquidity_score(self):
        """測試流動性評分"""
        df = pd.DataFrame({
            'open': [100.0] * 30,
            'high': [102.0] * 30,
            'low': [98.0] * 30,
            'close': [100.0] * 30,
            'volume': [1000 + i * 10 for i in range(30)]
        })
        
        liquidity = self.analyzer.calculate_liquidity_score(df)
        self.assertGreaterEqual(liquidity.liquidity_score, 0)
        self.assertLessEqual(liquidity.liquidity_score, 100)
        print(f"✓ 流動性評分測試通過: 評分={liquidity.liquidity_score:.2f}")


class TestEnhancedStrategy(unittest.TestCase):
    """測試增強版策略引擎"""
    
    def setUp(self):
        self.strategy = EnhancedStrategy(config={
            'min_confirmed_factors': 4,
            'min_score_threshold': 60.0,
            'base_position_pct': 0.02,
            'stop_loss_pct': 0.03,
            'take_profit_pct': 0.06
        })
    
    def test_factor_weights(self):
        """測試因子權重配置"""
        weights = self.strategy.FACTOR_WEIGHTS
        self.assertEqual(len(weights), 5)
        self.assertEqual(sum(weights.values()), 1.0)
        print(f"✓ 因子權重配置測試通過: {weights}")
    
    def test_candlestick_factor_analysis(self):
        """測試K線形態因子分析"""
        df = pd.DataFrame({
            'open': [100.0] * 30,
            'high': [102.0] * 30,
            'low': [98.0] * 30,
            'close': [100.0 + i * 0.1 for i in range(30)],
            'volume': [1000] * 30
        })
        
        # 在最後一根創建看漲形態
        df.loc[29, 'low'] = 95.0
        df.loc[29, 'close'] = 101.0
        
        signal = self.strategy._analyze_candlestick(df)
        self.assertIsNotNone(signal)
        self.assertIn(signal.signal, ['bullish', 'bearish', 'neutral'])
        print(f"✓ K線形態因子分析測試通過: 信號={signal.signal}, 強度={signal.strength:.2f}")
    
    def test_technical_factor_analysis(self):
        """測試技術指標因子分析"""
        df = pd.DataFrame({
            'open': [100.0 + i * 0.2 for i in range(50)],
            'high': [102.0 + i * 0.2 for i in range(50)],
            'low': [98.0 + i * 0.2 for i in range(50)],
            'close': [101.0 + i * 0.2 for i in range(50)],
            'volume': [1000 + i * 10 for i in range(50)]
        })
        
        signal = self.strategy._analyze_technical(df)
        self.assertIsNotNone(signal)
        self.assertIn(signal.signal, ['bullish', 'bearish', 'neutral'])
        print(f"✓ 技術指標因子分析測試通過: 信號={signal.signal}, 強度={signal.strength:.2f}")
    
    def test_sentiment_factor_analysis(self):
        """測試市場情緒因子分析"""
        df = pd.DataFrame({
            'open': [100.0] * 30,
            'high': [102.0] * 30,
            'low': [98.0] * 30,
            'close': [100.0 + i * 0.1 for i in range(30)],
            'volume': [1000] * 30
        })
        
        signal = self.strategy._analyze_sentiment(df)
        self.assertIsNotNone(signal)
        self.assertIn(signal.signal, ['bullish', 'bearish', 'neutral'])
        print(f"✓ 市場情緒因子分析測試通過: 信號={signal.signal}, 強度={signal.strength:.2f}")
    
    def test_trend_factor_analysis(self):
        """測試趨勢因子分析"""
        df = pd.DataFrame({
            'open': [100.0 + i * 0.2 for i in range(50)],
            'high': [102.0 + i * 0.2 for i in range(50)],
            'low': [98.0 + i * 0.2 for i in range(50)],
            'close': [101.0 + i * 0.2 for i in range(50)],
            'volume': [1000] * 50
        })
        
        signal = self.strategy._analyze_trend(df)
        self.assertIsNotNone(signal)
        self.assertIn(signal.signal, ['bullish', 'bearish', 'neutral'])
        print(f"✓ 趨勢因子分析測試通過: 信號={signal.signal}, 強度={signal.strength:.2f}")
    
    def test_multi_factor_scoring(self):
        """測試多因子評分計算"""
        # 創建測試因子信號
        factor_signals = [
            FactorSignal(SignalFactor.CANDLESTICK, 'bullish', 0.8, 0.9),
            FactorSignal(SignalFactor.TECHNICAL, 'bullish', 0.7, 0.8),
            FactorSignal(SignalFactor.SENTIMENT, 'bullish', 0.6, 0.7),
            FactorSignal(SignalFactor.TREND, 'bullish', 0.9, 0.85),
            FactorSignal(SignalFactor.SECTOR, 'neutral', 0.0, 0.5)
        ]
        
        score = self.strategy._calculate_multi_factor_score(factor_signals)
        self.assertIsNotNone(score)
        self.assertGreater(score.weighted_score, 0)  # 看多信號應該有正分數
        self.assertEqual(score.confirmed_factors, 4)  # 4個看多因子
        self.assertTrue(score.has_min_factors(4))
        print(f"✓ 多因子評分計算測試通過: 加權分數={score.weighted_score:.2f}, 確認因子={score.confirmed_factors}")
    
    def test_entry_decision(self):
        """測試進場決策邏輯"""
        # 創建強看多評分
        strong_bullish = MultiFactorScore(
            total_score=75.0,
            weighted_score=70.0,
            confirmed_factors=4,
            factor_signals=[]
        )
        
        weak_signal = MultiFactorScore(
            total_score=30.0,
            weighted_score=25.0,
            confirmed_factors=2,
            factor_signals=[]
        )
        
        self.assertTrue(self.strategy._should_enter(strong_bullish))
        self.assertFalse(self.strategy._should_enter(weak_signal))
        print(f"✓ 進場決策邏輯測試通過")
    
    def test_volatility_adjustment(self):
        """測試波動率調整"""
        df = pd.DataFrame({
            'open': [100.0] * 50,
            'high': [102.0] * 50,
            'low': [98.0] * 50,
            'close': [100.0] * 50,
            'volume': [1000] * 50
        })
        
        adjustment = self.strategy._get_volatility_adjustment(df)
        self.assertIsNotNone(adjustment)
        self.assertGreater(adjustment.position_scale, 0)
        print(f"✓ 波動率調整測試通過: 倉位縮放={adjustment.position_scale:.2f}")
    
    def test_on_data_processing(self):
        """測試數據處理流程"""
        df = pd.DataFrame({
            'open': [100.0 + i * 0.1 for i in range(50)],
            'high': [102.0 + i * 0.1 for i in range(50)],
            'low': [98.0 + i * 0.1 for i in range(50)],
            'close': [101.0 + i * 0.1 for i in range(50)],
            'volume': [1000] * 50
        })
        
        data = {
            'code': 'TEST.HK',
            'df': df
        }
        
        # 測試數據處理 (不會產生信號，因為數據不夠強)
        signal = self.strategy.on_data(data)
        # 可能返回None或信號，取決於數據
        print(f"✓ 數據處理流程測試通過")


class TestIntegration(unittest.TestCase):
    """整合測試"""
    
    def test_full_pipeline(self):
        """測試完整流程"""
        print("\n=== 開始整合測試 ===")
        
        # 創建測試數據
        np.random.seed(42)
        n_days = 100
        
        # 生成帶趨勢的價格數據
        trend = np.linspace(0, 20, n_days)
        noise = np.random.randn(n_days) * 2
        
        df = pd.DataFrame({
            'open': 100 + trend + noise,
            'high': 102 + trend + noise + np.abs(np.random.randn(n_days)),
            'low': 98 + trend + noise - np.abs(np.random.randn(n_days)),
            'close': 101 + trend + noise,
            'volume': np.random.randint(800, 1500, n_days)
        })
        
        # 1. 測試K線形態分析
        analyzer = CandlestickAnalyzer()
        patterns = analyzer.analyze(df)
        print(f"  檢測到 {len(patterns)} 個K線形態")
        
        # 2. 測試技術指標
        ti = TechnicalIndicators(df)
        all_indicators = ti.calculate_all()
        print(f"  技術指標計算完成，共 {len(all_indicators.columns)} 列")
        
        # 3. 測試市場情緒分析
        sentiment_analyzer = MarketSentimentAnalyzer()
        sentiment = sentiment_analyzer.analyze(df)
        print(f"  市場情緒: {sentiment.sentiment.value}, FGI: {sentiment.indicators.fear_greed_index:.2f}")
        
        # 4. 測試策略引擎
        strategy = EnhancedStrategy()
        data = {'code': 'TEST.HK', 'df': df}
        signal = strategy.on_data(data)
        
        if signal:
            print(f"  產生交易信號: {signal.signal.value} @ {signal.price:.2f}")
        else:
            print(f"  無交易信號產生")
        
        print("=== 整合測試完成 ===\n")


def run_tests():
    """運行所有測試"""
    print("\n" + "="*60)
    print("  增強版策略測試套件")
    print("="*60 + "\n")
    
    # 創建測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加測試類
    suite.addTests(loader.loadTestsFromTestCase(TestCandlestickPatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestMarketSentiment))
    suite.addTests(loader.loadTestsFromTestCase(TestEnhancedStrategy))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 輸出摘要
    print("\n" + "="*60)
    print("  測試摘要")
    print("="*60)
    print(f"  總測試數: {result.testsRun}")
    print(f"  通過: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失敗: {len(result.failures)}")
    print(f"  錯誤: {len(result.errors)}")
    print("="*60 + "\n")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
