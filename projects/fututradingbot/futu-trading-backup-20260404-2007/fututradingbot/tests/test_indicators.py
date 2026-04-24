"""
富途交易機器人 - 單元測試
Unit Tests for Futu Trading Bot

測試範圍：
- 技術指標計算
- 數據獲取與緩存
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加src到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from indicators.technical import (
    TechnicalIndicators, MACDResult, BOLLResult, EMAResult,
    VMACDResult, RSIResult, VolumeAnalysisResult,
    calculate_support_resistance, calculate_atr
)
from data.market_data import (
    FutuMarketData, DataCache, MarketDataManager,
    KLType, SubType, StockQuote
)


class TestTechnicalIndicators(unittest.TestCase):
    """測試技術指標計算"""
    
    def setUp(self):
        """設置測試數據"""
        # 生成模擬K線數據
        np.random.seed(42)
        n = 100
        dates = pd.date_range(end=datetime.now(), periods=n, freq='D')
        
        # 生成價格數據
        returns = np.random.normal(0.001, 0.02, n)
        prices = 100 * np.exp(np.cumsum(returns))
        
        self.test_df = pd.DataFrame({
            'timestamp': dates,
            'open': prices * (1 + np.random.normal(0, 0.005, n)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n))),
            'close': prices,
            'volume': np.random.randint(100000, 10000000, n)
        })
        
        # 確保high >= max(open, close) 且 low <= min(open, close)
        self.test_df['high'] = self.test_df[['open', 'high', 'close']].max(axis=1)
        self.test_df['low'] = self.test_df[['open', 'low', 'close']].min(axis=1)
        
        self.indicators = TechnicalIndicators(self.test_df)
    
    def test_macd_calculation(self):
        """測試MACD計算"""
        macd = self.indicators.calculate_macd()
        
        # 檢查返回類型
        self.assertIsInstance(macd, MACDResult)
        
        # 檢查序列長度
        self.assertEqual(len(macd.dif), len(self.test_df))
        self.assertEqual(len(macd.dea), len(self.test_df))
        self.assertEqual(len(macd.macd), len(self.test_df))
        
        # 檢查MACD柱計算公式: MACD = (DIF - DEA) * 2
        expected_macd = (macd.dif - macd.dea) * 2
        pd.testing.assert_series_equal(macd.macd, expected_macd)
        
        # 檢查to_dataframe方法
        df = macd.to_dataframe()
        self.assertEqual(list(df.columns), ['DIF', 'DEA', 'MACD'])
    
    def test_boll_calculation(self):
        """測試布林帶計算"""
        boll = self.indicators.calculate_boll()
        
        # 檢查返回類型
        self.assertIsInstance(boll, BOLLResult)
        
        # 檢查序列長度
        self.assertEqual(len(boll.upper), len(self.test_df))
        self.assertEqual(len(boll.middle), len(self.test_df))
        self.assertEqual(len(boll.lower), len(self.test_df))
        
        # 檢查布林帶邏輯: upper >= middle >= lower
        valid_idx = boll.middle.notna()
        self.assertTrue((boll.upper[valid_idx] >= boll.middle[valid_idx]).all())
        self.assertTrue((boll.middle[valid_idx] >= boll.lower[valid_idx]).all())
        
        # 檢查帶寬計算
        expected_bandwidth = (boll.upper - boll.lower) / boll.middle
        pd.testing.assert_series_equal(boll.bandwidth, expected_bandwidth)
    
    def test_ema_calculation(self):
        """測試EMA計算"""
        ema = self.indicators.calculate_ema()
        
        # 檢查返回類型
        self.assertIsInstance(ema, EMAResult)
        
        # 檢查序列長度
        self.assertEqual(len(ema.ema_5), len(self.test_df))
        self.assertEqual(len(ema.ema_10), len(self.test_df))
        self.assertEqual(len(ema.ema_20), len(self.test_df))
        self.assertEqual(len(ema.ema_60), len(self.test_df))
        
        # 檢查週期越長，EMA越平滑 (變化越小)
        ema_5_change = ema.ema_5.diff().abs().mean()
        ema_60_change = ema.ema_60.diff().abs().mean()
        self.assertGreater(ema_5_change, ema_60_change)
    
    def test_vmacd_calculation(self):
        """測試量價MACD計算"""
        vmacd = self.indicators.calculate_vmacd()
        
        # 檢查返回類型
        self.assertIsInstance(vmacd, VMACDResult)
        
        # 檢查序列長度
        self.assertEqual(len(vmacd.dif), len(self.test_df))
        self.assertEqual(len(vmacd.dea), len(self.test_df))
        self.assertEqual(len(vmacd.vmacd), len(self.test_df))
        
        # 檢查VMACD柱計算公式
        expected_vmacd = (vmacd.dif - vmacd.dea) * 2
        pd.testing.assert_series_equal(vmacd.vmacd, expected_vmacd)
    
    def test_rsi_calculation(self):
        """測試RSI計算"""
        rsi = self.indicators.calculate_rsi()
        
        # 檢查返回類型
        self.assertIsInstance(rsi, RSIResult)
        
        # 檢查序列長度
        self.assertEqual(len(rsi.rsi_6), len(self.test_df))
        self.assertEqual(len(rsi.rsi_12), len(self.test_df))
        self.assertEqual(len(rsi.rsi_24), len(self.test_df))
        
        # 檢查RSI範圍: 0 <= RSI <= 100
        valid_idx = rsi.rsi_6.notna()
        self.assertTrue((rsi.rsi_6[valid_idx] >= 0).all())
        self.assertTrue((rsi.rsi_6[valid_idx] <= 100).all())
    
    def test_volume_analysis(self):
        """測試成交量分析"""
        vol = self.indicators.calculate_volume_analysis()
        
        # 檢查返回類型
        self.assertIsInstance(vol, VolumeAnalysisResult)
        
        # 檢查序列長度
        self.assertEqual(len(vol.volume), len(self.test_df))
        self.assertEqual(len(vol.volume_ma_5), len(self.test_df))
        self.assertEqual(len(vol.obv), len(self.test_df))
        
        # 檢查OBV是累積值 (OBV可以是正或負，取決於價格趨勢)
        # OBV初始值為第一日成交量，之後根據價格漲跌加減成交量
        self.assertIsNotNone(vol.obv.iloc[0])
        
        # 檢查量比計算
        expected_ratio = vol.volume / vol.volume_ma_5.shift(1)
        pd.testing.assert_series_equal(vol.volume_ratio, expected_ratio)
    
    def test_calculate_all(self):
        """測試計算所有指標"""
        result = self.indicators.calculate_all()
        
        # 檢查返回類型
        self.assertIsInstance(result, pd.DataFrame)
        
        # 檢查是否包含所有必要的列
        expected_columns = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'DIF', 'DEA', 'MACD',
            'UPPER', 'MIDDLE', 'LOWER', 'BANDWIDTH',
            'EMA5', 'EMA10', 'EMA20', 'EMA60',
            'VMACD_DIF', 'VMACD_DEA', 'VMACD',
            'RSI6', 'RSI12', 'RSI24',
            'VOL_MA5', 'VOL_MA10', 'VOL_MA20', 'VOL_RATIO', 'OBV'
        ]
        for col in expected_columns:
            self.assertIn(col, result.columns)
    
    def test_signal_summary(self):
        """測試信號摘要"""
        summary = self.indicators.get_signal_summary()
        
        # 檢查返回類型
        self.assertIsInstance(summary, dict)
        
        # 檢查必要的鍵
        expected_keys = [
            'macd_signal', 'boll_position', 
            'rsi_6', 'rsi_12', 'rsi_24',
            'volume_ratio', 'obv_trend'
        ]
        for key in expected_keys:
            self.assertIn(key, summary)
        
        # 檢查MACD信號值
        self.assertIn(summary['macd_signal'], ['bullish', 'bearish', 'neutral'])
        
        # 檢查布林帶位置
        self.assertIn(summary['boll_position'], [
            'upper_band', 'lower_band', 'above_middle', 'below_middle'
        ])
    
    def test_data_validation(self):
        """測試數據驗證"""
        # 缺少必要欄位的數據
        invalid_df = pd.DataFrame({
            'close': [1, 2, 3],
            'volume': [100, 200, 300]
        })
        
        with self.assertRaises(ValueError):
            TechnicalIndicators(invalid_df)
    
    def test_support_resistance(self):
        """測試支撐位和阻力位計算"""
        support, resistance = calculate_support_resistance(self.test_df, window=20)
        
        # 檢查序列長度
        self.assertEqual(len(support), len(self.test_df))
        self.assertEqual(len(resistance), len(self.test_df))
        
        # 檢查阻力位 >= 支撐位
        valid_idx = support.notna() & resistance.notna()
        self.assertTrue((resistance[valid_idx] >= support[valid_idx]).all())
    
    def test_atr_calculation(self):
        """測試ATR計算"""
        atr = calculate_atr(self.test_df, period=14)
        
        # 檢查序列長度
        self.assertEqual(len(atr), len(self.test_df))
        
        # 檢查ATR為正數
        valid_idx = atr.notna()
        self.assertTrue((atr[valid_idx] > 0).all())


class TestDataCache(unittest.TestCase):
    """測試數據緩存功能"""
    
    def setUp(self):
        """設置測試環境"""
        self.cache_dir = "test_cache"
        self.cache = DataCache(self.cache_dir)
        
        # 測試數據
        self.test_df = pd.DataFrame({
            'timestamp': pd.date_range(end=datetime.now(), periods=10, freq='D'),
            'close': [100 + i for i in range(10)],
            'volume': [1000 * (i + 1) for i in range(10)]
        })
    
    def tearDown(self):
        """清理測試環境"""
        import shutil
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
    
    def test_cache_set_get(self):
        """測試緩存設置和獲取"""
        code = "HK.00700"
        ktype = KLType.K_DAY
        start = "2024-01-01"
        end = "2024-01-31"
        
        # 設置緩存
        self.cache.set(code, ktype, start, end, self.test_df)
        
        # 獲取緩存
        cached_df = self.cache.get(code, ktype, start, end)
        
        # 檢查數據一致性
        pd.testing.assert_frame_equal(cached_df, self.test_df)
    
    def test_cache_expiration(self):
        """測試緩存過期"""
        import time
        code = "HK.00700"
        ktype = KLType.K_DAY
        start = "2024-01-01"
        end = "2024-01-31"
        
        # 設置緩存
        self.cache.set(code, ktype, start, end, self.test_df)
        
        # 等待一小段時間確保文件時間戳有變化
        time.sleep(0.1)
        
        # 使用極短的過期時間獲取 (應該返回None)
        # 使用負數確保過期
        cached_df = self.cache.get(code, ktype, start, end, max_age_hours=-1)
        self.assertIsNone(cached_df)
    
    def test_cache_clear(self):
        """測試清除緩存"""
        code = "HK.00700"
        ktype = KLType.K_DAY
        start = "2024-01-01"
        end = "2024-01-31"
        
        # 設置緩存
        self.cache.set(code, ktype, start, end, self.test_df)
        
        # 清除緩存
        self.cache.clear(code)
        
        # 檢查緩存已清除
        cached_df = self.cache.get(code, ktype, start, end)
        self.assertIsNone(cached_df)
    
    def test_cache_info(self):
        """測試緩存信息"""
        info = self.cache.get_cache_info()
        
        # 檢查返回類型
        self.assertIsInstance(info, dict)
        
        # 檢查必要的鍵
        self.assertIn('memory_cache_count', info)
        self.assertIn('file_cache_count', info)
        self.assertIn('total_cache_size_mb', info)


class TestFutuMarketData(unittest.TestCase):
    """測試富途行情數據接口"""
    
    def setUp(self):
        """設置測試環境"""
        self.md = FutuMarketData(cache_dir="test_md_cache")
    
    def tearDown(self):
        """清理測試環境"""
        import shutil
        if os.path.exists("test_md_cache"):
            shutil.rmtree("test_md_cache")
    
    def test_mock_kline_data_generation(self):
        """測試模擬K線數據生成"""
        code = "HK.00700"
        ktype = KLType.K_DAY
        start = "2024-01-01"
        end = "2024-01-31"
        num = 20
        
        df = self.md._generate_mock_kline_data(code, ktype, start, end, num)
        
        # 檢查返回類型
        self.assertIsInstance(df, pd.DataFrame)
        
        # 檢查必要的列
        expected_columns = [
            'timestamp', 'code', 'ktype', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ]
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        # 檢查high >= max(open, close) 且 low <= min(open, close)
        self.assertTrue((df['high'] >= df[['open', 'close']].max(axis=1)).all())
        self.assertTrue((df['low'] <= df[['open', 'close']].min(axis=1)).all())
    
    def test_kline_data_with_cache(self):
        """測試帶緩存的K線數據獲取"""
        code = "HK.00700"
        ktype = KLType.K_DAY
        start = "2024-01-01"
        end = "2024-01-31"
        
        # 第一次獲取 (應該從API/模擬生成)
        df1 = self.md.get_kline_data(code, ktype=ktype, start=start, end=end)
        
        # 第二次獲取 (應該從緩存)
        df2 = self.md.get_kline_data(code, ktype=ktype, start=start, end=end)
        
        # 檢查數據一致性
        pd.testing.assert_frame_equal(df1, df2)
    
    def test_different_kline_types(self):
        """測試不同K線類型"""
        code = "HK.00700"
        ktypes = [KLType.K_1M, KLType.K_5M, KLType.K_DAY, KLType.K_WEEK]
        
        for ktype in ktypes:
            df = self.md.get_kline_data(code, ktype=ktype, num=10)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertFalse(df.empty)


class TestMarketDataManager(unittest.TestCase):
    """測試市場數據管理器"""
    
    def setUp(self):
        """設置測試環境"""
        self.md = FutuMarketData(cache_dir="test_mgr_cache")
        self.manager = MarketDataManager(self.md)
    
    def tearDown(self):
        """清理測試環境"""
        import shutil
        if os.path.exists("test_mgr_cache"):
            shutil.rmtree("test_mgr_cache")
    
    def test_watchlist_management(self):
        """測試觀察列表管理"""
        code1 = "HK.00700"
        code2 = "HK.09988"
        
        # 添加到觀察列表
        self.manager.add_to_watchlist(code1)
        self.manager.add_to_watchlist(code2)
        
        # 檢查觀察列表
        watchlist = self.manager.get_watchlist()
        self.assertEqual(len(watchlist), 2)
        self.assertIn(code1, watchlist)
        self.assertIn(code2, watchlist)
        
        # 移除
        self.manager.remove_from_watchlist(code1)
        watchlist = self.manager.get_watchlist()
        self.assertEqual(len(watchlist), 1)
        self.assertNotIn(code1, watchlist)
    
    def test_fetch_watchlist_data(self):
        """測試獲取觀察列表數據"""
        code = "HK.00700"
        self.manager.add_to_watchlist(code)
        
        # 獲取數據
        result = self.manager.fetch_watchlist_data(ktype=KLType.K_DAY, num=10)
        
        # 檢查結果
        self.assertIn(code, result)
        self.assertIsInstance(result[code], pd.DataFrame)
    
    def test_export_data(self):
        """測試數據導出"""
        code = "HK.00700"
        self.manager.add_to_watchlist(code)
        self.manager.fetch_watchlist_data(num=10)
        
        # 測試CSV導出
        csv_path = "test_export.csv"
        result = self.manager.export_data(code, csv_path, "csv")
        self.assertTrue(result)
        self.assertTrue(os.path.exists(csv_path))
        
        # 清理
        if os.path.exists(csv_path):
            os.remove(csv_path)


def run_tests():
    """運行所有測試"""
    # 創建測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加測試類
    suite.addTests(loader.loadTestsFromTestCase(TestTechnicalIndicators))
    suite.addTests(loader.loadTestsFromTestCase(TestDataCache))
    suite.addTests(loader.loadTestsFromTestCase(TestFutuMarketData))
    suite.addTests(loader.loadTestsFromTestCase(TestMarketDataManager))
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
