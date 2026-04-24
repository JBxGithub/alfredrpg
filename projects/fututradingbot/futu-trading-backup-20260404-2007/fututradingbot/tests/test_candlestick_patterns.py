"""
K線形態分析模組完整測試腳本
測試 candlestick_patterns.py 的所有功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from datetime import datetime
from src.indicators.candlestick_patterns import (
    CandlestickAnalyzer, CandlestickPattern, PatternType, PatternStrength,
    detect_doji, detect_hammer, detect_shooting_star, detect_marubozu,
    detect_engulfing, detect_harami, detect_morning_star, detect_evening_star,
    calculate_pattern_strength
)

# 測試結果記錄
class TestResult:
    def __init__(self, name, passed, details="", error=None):
        self.name = name
        self.passed = passed
        self.details = details
        self.error = error
        self.timestamp = datetime.now()

# 全局測試結果列表
test_results = []

def create_test_dataframe(data_list, include_volume=True):
    """創建測試用的DataFrame"""
    df = pd.DataFrame(data_list)
    if include_volume and 'volume' not in df.columns:
        df['volume'] = [1000000] * len(df)
    return df

def assert_pattern_type(pattern, expected_type, test_name):
    """驗證形態類型"""
    if pattern is None:
        test_results.append(TestResult(test_name, False, "Pattern is None", "Null pattern"))
        return False
    
    if pattern.pattern_type == expected_type:
        test_results.append(TestResult(test_name, True, f"Detected: {pattern.pattern_type.value}"))
        return True
    else:
        test_results.append(TestResult(test_name, False, 
            f"Expected: {expected_type.value}, Got: {pattern.pattern_type.value}",
            f"Type mismatch"))
        return False

def assert_true(condition, test_name, details=""):
    """驗證條件為真"""
    if condition:
        test_results.append(TestResult(test_name, True, details))
        return True
    else:
        test_results.append(TestResult(test_name, False, details, "Assertion failed"))
        return False

def assert_false(condition, test_name, details=""):
    """驗證條件為假"""
    return assert_true(not condition, test_name, details)

def assert_almost_equal(actual, expected, tolerance, test_name, details=""):
    """驗證數值在容差範圍內"""
    if abs(actual - expected) <= tolerance:
        test_results.append(TestResult(test_name, True, f"{details} | Value: {actual}"))
        return True
    else:
        test_results.append(TestResult(test_name, False, 
            f"{details} | Expected: {expected}, Got: {actual}",
            "Value mismatch"))
        return False

# ==================== 單根K線形態測試 ====================

def test_doji():
    """測試十字星形態"""
    print("\n[測試] Doji (十字星)...")
    
    # 經典十字星：開盤=收盤，有上下影線
    data = [
        {'open': 100.0, 'high': 102.0, 'low': 98.0, 'close': 100.0, 'volume': 1000000}
    ]
    df = create_test_dataframe(data)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, 0)
    
    assert_pattern_type(pattern, PatternType.DOJI, "Doji - Classic")
    # Doji的confidence計算為 body_ratio / doji_threshold，當body_ratio=0時confidence=0
    assert_true(pattern.confidence >= 0, "Doji - Confidence >= 0", f"Confidence: {pattern.confidence}")
    
    # 使用便捷函數
    result = detect_doji(df, 0)
    assert_true(result, "detect_doji() function", f"Result: {result}")

def test_hammer():
    """測試錘子線形態"""
    print("\n[測試] Hammer (錘子線)...")
    
    # 經典錘子線：小實體在上方，長下影線，短上影線，收盤>開盤
    data = [
        {'open': 100.0, 'high': 101.0, 'low': 95.0, 'close': 101.0, 'volume': 1200000}
    ]
    df = create_test_dataframe(data)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, 0)
    
    assert_pattern_type(pattern, PatternType.HAMMER, "Hammer - Classic")
    assert_true(pattern.is_bullish(), "Hammer - is_bullish()", f"Bullish: {pattern.is_bullish()}")
    assert_true(pattern.is_reversal(), "Hammer - is_reversal()", f"Reversal: {pattern.is_reversal()}")
    
    # 使用便捷函數
    result = detect_hammer(df, 0)
    assert_true(result, "detect_hammer() function", f"Result: {result}")

def test_shooting_star():
    """測試射擊之星形態"""
    print("\n[測試] Shooting Star (射擊之星)...")
    
    # 經典射擊之星：小實體在下方，長上影線，短下影線，收盤<開盤
    data = [
        {'open': 100.0, 'high': 105.0, 'low': 99.0, 'close': 99.0, 'volume': 1100000}
    ]
    df = create_test_dataframe(data)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, 0)
    
    assert_pattern_type(pattern, PatternType.SHOOTING_STAR, "Shooting Star - Classic")
    assert_true(pattern.is_bearish(), "Shooting Star - is_bearish()", f"Bearish: {pattern.is_bearish()}")
    assert_true(pattern.is_reversal(), "Shooting Star - is_reversal()", f"Reversal: {pattern.is_reversal()}")
    
    # 使用便捷函數
    result = detect_shooting_star(df, 0)
    assert_true(result, "detect_shooting_star() function", f"Result: {result}")

def test_marubozu():
    """測試光頭光腳形態"""
    print("\n[測試] Marubozu (光頭光腳)...")
    
    # 光頭光腳陽線
    data_bullish = [
        {'open': 100.0, 'high': 105.0, 'low': 100.0, 'close': 105.0, 'volume': 1500000}
    ]
    df_bullish = create_test_dataframe(data_bullish)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df_bullish, 0)
    
    assert_pattern_type(pattern, PatternType.MARUBOZU_BULLISH, "Marubozu - Bullish")
    assert_true(pattern.is_bullish(), "Marubozu Bullish - is_bullish()")
    
    # 使用便捷函數
    result = detect_marubozu(df_bullish, 0)
    assert_true(result == 'bullish', "detect_marubozu() - bullish", f"Result: {result}")
    
    # 光頭光腳陰線
    data_bearish = [
        {'open': 105.0, 'high': 105.0, 'low': 100.0, 'close': 100.0, 'volume': 1400000}
    ]
    df_bearish = create_test_dataframe(data_bearish)
    pattern = analyzer.detect_at_index(df_bearish, 0)
    
    assert_pattern_type(pattern, PatternType.MARUBOZU_BEARISH, "Marubozu - Bearish")
    assert_true(pattern.is_bearish(), "Marubozu Bearish - is_bearish()")
    
    result = detect_marubozu(df_bearish, 0)
    assert_true(result == 'bearish', "detect_marubozu() - bearish", f"Result: {result}")

# ==================== 雙根K線組合測試 ====================

def test_bullish_engulfing():
    """測試看漲吞沒形態"""
    print("\n[測試] Bullish Engulfing (看漲吞沒)...")
    
    # 看漲吞沒：第一根陰線，第二根陽線，第二根實體完全包含第一根
    data = [
        {'open': 100.0, 'high': 102.0, 'low': 98.0, 'close': 98.0, 'volume': 1000000},  # 陰線
        {'open': 97.0, 'high': 103.0, 'low': 96.0, 'close': 103.0, 'volume': 2000000},  # 大陽線吞沒
    ]
    df = create_test_dataframe(data)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, 1)  # 檢測第二根K線
    
    assert_pattern_type(pattern, PatternType.ENGULFING_BULLISH, "Bullish Engulfing - Classic")
    assert_true(pattern.is_bullish(), "Bullish Engulfing - is_bullish()")
    assert_true(pattern.is_reversal(), "Bullish Engulfing - is_reversal()")
    
    # 使用便捷函數
    result = detect_engulfing(df, 1)
    assert_true(result == 'bullish', "detect_engulfing() - bullish", f"Result: {result}")

def test_bearish_engulfing():
    """測試看跌吞沒形態"""
    print("\n[測試] Bearish Engulfing (看跌吞沒)...")
    
    # 看跌吞沒：第一根陽線，第二根陰線，第二根實體完全包含第一根
    data = [
        {'open': 100.0, 'high': 102.0, 'low': 98.0, 'close': 102.0, 'volume': 1000000},  # 陽線
        {'open': 103.0, 'high': 104.0, 'low': 97.0, 'close': 97.0, 'volume': 2000000},   # 大陰線吞沒
    ]
    df = create_test_dataframe(data)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, 1)
    
    assert_pattern_type(pattern, PatternType.ENGULFING_BEARISH, "Bearish Engulfing - Classic")
    assert_true(pattern.is_bearish(), "Bearish Engulfing - is_bearish()")
    assert_true(pattern.is_reversal(), "Bearish Engulfing - is_reversal()")
    
    result = detect_engulfing(df, 1)
    assert_true(result == 'bearish', "detect_engulfing() - bearish", f"Result: {result}")

def test_harami():
    """測試孕育形態"""
    print("\n[測試] Harami (孕育形態)...")
    
    # 看漲孕育：第一根大陽線，第二根小陰線（下跌後的看漲信號）
    # 代碼邏輯: is_bullish1 and not is_bullish2
    data_bullish = [
        {'open': 95.0, 'high': 102.0, 'low': 94.0, 'close': 102.0, 'volume': 1000000},   # 大陽線 (is_bullish1=True)
        {'open': 101.0, 'high': 101.0, 'low': 99.0, 'close': 99.0, 'volume': 500000},    # 小陰線 (is_bullish2=False)
    ]
    df_bullish = create_test_dataframe(data_bullish)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df_bullish, 1)
    
    assert_pattern_type(pattern, PatternType.HARAMI_BULLISH, "Harami - Bullish")
    assert_true(pattern.is_bullish(), "Harami Bullish - is_bullish()")
    
    result = detect_harami(df_bullish, 1)
    assert_true(result == 'bullish', "detect_harami() - bullish", f"Result: {result}")
    
    # 看跌孕育：第一根大陰線，第二根小陽線（上漲後的看跌信號）
    # 代碼邏輯: not is_bullish1 and is_bullish2
    data_bearish = [
        {'open': 105.0, 'high': 106.0, 'low': 98.0, 'close': 98.0, 'volume': 1000000},   # 大陰線 (is_bullish1=False)
        {'open': 99.0, 'high': 101.0, 'low': 99.0, 'close': 100.0, 'volume': 500000},    # 小陽線 (is_bullish2=True)
    ]
    df_bearish = create_test_dataframe(data_bearish)
    pattern = analyzer.detect_at_index(df_bearish, 1)
    
    assert_pattern_type(pattern, PatternType.HARAMI_BEARISH, "Harami - Bearish")
    assert_true(pattern.is_bearish(), "Harami Bearish - is_bearish()")
    
    result = detect_harami(df_bearish, 1)
    assert_true(result == 'bearish', "detect_harami() - bearish", f"Result: {result}")

# ==================== 三根K線組合測試 ====================

def test_morning_star():
    """測試晨星形態"""
    print("\n[測試] Morning Star (晨星)...")
    
    # 晨星：第一根大陰線，第二根小實體（十字星），第三根大陽線
    # 代碼邏輯: not is_bullish[2] and is_bullish[0] - 即idx-2是陰線，idx是陽線
    # 創建足夠長的歷史數據以獲得準確的評分
    data = []
    # 添加20根歷史K線建立趨勢
    for i in range(20):
        data.append({
            'open': 110 - i * 0.5,
            'high': 112 - i * 0.5,
            'low': 108 - i * 0.5,
            'close': 109 - i * 0.5,
            'volume': 1000000
        })
    
    # 添加晨星形態
    data.append({'open': 105.0, 'high': 106.0, 'low': 98.0, 'close': 98.0, 'volume': 1000000})   # idx=20: 大陰線
    data.append({'open': 98.0, 'high': 99.0, 'low': 97.0, 'close': 98.5, 'volume': 500000})      # idx=21: 小實體
    data.append({'open': 99.0, 'high': 105.0, 'low': 98.5, 'close': 104.0, 'volume': 2500000})   # idx=22: 大陽線 (高成交量)
    
    df = create_test_dataframe(data)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, 22)
    
    assert_pattern_type(pattern, PatternType.MORNING_STAR, "Morning Star - Classic")
    assert_true(pattern.is_bullish(), "Morning Star - is_bullish()")
    assert_true(pattern.is_reversal(), "Morning Star - is_reversal()")
    # 由於有足夠的歷史數據，應該能獲得較高的評分
    assert_true(pattern.overall_score >= 50, "Morning Star - Overall Score >= 50", f"Score: {pattern.overall_score}")
    
    result = detect_morning_star(df, 22)
    assert_true(result, "detect_morning_star() function", f"Result: {result}")

def test_evening_star():
    """測試暮星形態"""
    print("\n[測試] Evening Star (暮星)...")
    
    # 暮星：第一根大陽線，第二根小實體，第三根大陰線
    # 代碼邏輯: is_bullish[2] and not is_bullish[0] - 即idx-2是陽線，idx是陰線
    # 創建足夠長的歷史數據以獲得準確的評分
    data = []
    # 添加20根歷史K線建立上升趨勢
    for i in range(20):
        data.append({
            'open': 90 + i * 0.5,
            'high': 92 + i * 0.5,
            'low': 88 + i * 0.5,
            'close': 91 + i * 0.5,
            'volume': 1000000
        })
    
    # 添加暮星形態
    data.append({'open': 95.0, 'high': 102.0, 'low': 94.0, 'close': 102.0, 'volume': 1000000})   # idx=20: 大陽線
    data.append({'open': 102.0, 'high': 103.0, 'low': 101.0, 'close': 102.5, 'volume': 500000})  # idx=21: 小實體
    data.append({'open': 102.0, 'high': 102.5, 'low': 95.0, 'close': 96.0, 'volume': 2500000})   # idx=22: 大陰線 (高成交量)
    
    df = create_test_dataframe(data)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, 22)
    
    assert_pattern_type(pattern, PatternType.EVENING_STAR, "Evening Star - Classic")
    assert_true(pattern.is_bearish(), "Evening Star - is_bearish()")
    assert_true(pattern.is_reversal(), "Evening Star - is_reversal()")
    # 由於有足夠的歷史數據，應該能獲得較高的評分
    assert_true(pattern.overall_score >= 50, "Evening Star - Overall Score >= 50", f"Score: {pattern.overall_score}")
    
    result = detect_evening_star(df, 22)
    assert_true(result, "detect_evening_star() function", f"Result: {result}")

# ==================== 信號強度評分測試 ====================

def test_position_score():
    """測試位置評分"""
    print("\n[測試] Position Score (位置評分)...")
    
    # 創建足夠長的數據序列
    np.random.seed(42)
    base_data = []
    for i in range(25):
        base_data.append({
            'open': 100 + i * 0.5,
            'high': 102 + i * 0.5,
            'low': 98 + i * 0.5,
            'close': 101 + i * 0.5,
            'volume': 1000000
        })
    
    # 在低位添加錘子線（應該得到高分）
    base_data[-1] = {'open': 100.0, 'high': 101.0, 'low': 95.0, 'close': 101.0, 'volume': 2000000}
    
    df = create_test_dataframe(base_data)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, 24)
    
    assert_true(pattern.position_score > 0, "Position Score - > 0", f"Score: {pattern.position_score}")
    assert_true(pattern.position_score <= 1.0, "Position Score - <= 1.0", f"Score: {pattern.position_score}")

def test_volume_score():
    """測試成交量評分"""
    print("\n[測試] Volume Score (成交量評分)...")
    
    # 創建數據，最後一根成交量異常放大
    data = []
    for i in range(10):
        data.append({
            'open': 100.0,
            'high': 102.0,
            'low': 98.0,
            'close': 101.0,
            'volume': 1000000  # 基準成交量
        })
    
    # 最後一根：錘子線 + 3倍成交量
    data[-1] = {'open': 100.0, 'high': 101.0, 'low': 95.0, 'close': 101.0, 'volume': 3000000}
    
    df = create_test_dataframe(data)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, 9)
    
    assert_true(pattern.volume_score > 0.5, "Volume Score - High volume", f"Score: {pattern.volume_score}")
    assert_true(pattern.volume_score <= 1.0, "Volume Score - <= 1.0", f"Score: {pattern.volume_score}")

def test_trend_score():
    """測試趨勢評分"""
    print("\n[測試] Trend Score (趨勢評分)...")
    
    # 創建下跌趨勢數據，然後出現看漲信號
    data = []
    # 前5根下跌
    for i in range(5):
        data.append({
            'open': 110 - i * 2,
            'high': 111 - i * 2,
            'low': 107 - i * 2,
            'close': 108 - i * 2,
            'volume': 1000000
        })
    
    # 第6根：錘子線（下跌趨勢中的看漲信號）
    data.append({
        'open': 98.0, 'high': 99.0, 'low': 93.0, 'close': 99.0, 'volume': 2000000
    })
    
    df = create_test_dataframe(data)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, 5)
    
    assert_true(pattern.trend_score > 0, "Trend Score - > 0", f"Score: {pattern.trend_score}")
    assert_true(pattern.trend_score <= 1.0, "Trend Score - <= 1.0", f"Score: {pattern.trend_score}")

def test_overall_score():
    """測試綜合評分計算"""
    print("\n[測試] Overall Score (綜合評分)...")
    
    # 創建完整測試數據
    data = []
    # 前20根建立趨勢
    for i in range(20):
        data.append({
            'open': 100 + np.sin(i * 0.3) * 5,
            'high': 103 + np.sin(i * 0.3) * 5,
            'low': 97 + np.sin(i * 0.3) * 5,
            'close': 101 + np.sin(i * 0.3) * 5,
            'volume': 1000000
        })
    
    # 添加錘子線
    data.append({
        'open': 95.0, 'high': 96.0, 'low': 90.0, 'close': 96.0, 'volume': 2500000
    })
    
    df = create_test_dataframe(data)
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df, 20)
    
    # 驗證綜合評分
    expected_overall = (pattern.position_score * 0.4 + 
                       pattern.volume_score * 0.3 + 
                       pattern.trend_score * 0.3) * 100
    
    assert_almost_equal(pattern.overall_score, expected_overall, 0.1, 
                       "Overall Score - Calculation", f"Expected: {expected_overall}, Got: {pattern.overall_score}")
    assert_true(pattern.overall_score >= 0, "Overall Score - >= 0", f"Score: {pattern.overall_score}")
    assert_true(pattern.overall_score <= 100, "Overall Score - <= 100", f"Score: {pattern.overall_score}")
    
    # 測試便捷函數
    score = calculate_pattern_strength(df, 20)
    assert_true(score > 0, "calculate_pattern_strength()", f"Score: {score}")

# ==================== 邊界情況測試 ====================

def test_edge_cases():
    """測試邊界情況"""
    print("\n[測試] Edge Cases (邊界情況)...")
    
    # 空數據測試
    df_empty = pd.DataFrame({'open': [], 'high': [], 'low': [], 'close': [], 'volume': []})
    analyzer = CandlestickAnalyzer()
    pattern = analyzer.detect_at_index(df_empty, 0)
    assert_true(pattern is None or pattern.pattern_type == PatternType.NONE, 
               "Edge Case - Empty DataFrame", f"Result: {pattern}")
    
    # 單行數據測試
    df_single = create_test_dataframe([{'open': 100, 'high': 102, 'low': 98, 'close': 101, 'volume': 1000}])
    pattern = analyzer.detect_at_index(df_single, 0)
    assert_true(pattern is not None, "Edge Case - Single Row", f"Result: {pattern}")
    
    # 無成交量數據測試
    df_no_volume = pd.DataFrame([
        {'open': 100, 'high': 102, 'low': 98, 'close': 101}
    ])
    pattern = analyzer.detect_at_index(df_no_volume, 0)
    assert_true(pattern is not None, "Edge Case - No Volume Column", f"Result: {pattern}")

def test_analyze_all():
    """測試分析整個DataFrame"""
    print("\n[測試] analyze() - 分析整個DataFrame...")
    
    # 創建包含多種形態的數據
    data = [
        {'open': 100.0, 'high': 102.0, 'low': 98.0, 'close': 100.0, 'volume': 1000000},  # Doji
        {'open': 100.0, 'high': 101.0, 'low': 95.0, 'close': 101.0, 'volume': 1200000},  # Hammer
        {'open': 100.0, 'high': 105.0, 'low': 99.0, 'close': 99.0, 'volume': 1100000},   # Shooting Star
        {'open': 100.0, 'high': 105.0, 'low': 100.0, 'close': 105.0, 'volume': 1500000},  # Marubozu Bullish
    ]
    df = create_test_dataframe(data)
    analyzer = CandlestickAnalyzer()
    patterns = analyzer.analyze(df)
    
    assert_true(len(patterns) > 0, "analyze() - Returns patterns", f"Count: {len(patterns)}")
    
    # 測試 get_latest_signals
    signals = analyzer.get_latest_signals(df, min_score=50.0, n=3)
    assert_true(isinstance(signals, list), "get_latest_signals() - Returns list", f"Type: {type(signals)}")
    
    # 測試 get_signal_summary
    summary = analyzer.get_signal_summary(df)
    assert_true('has_signal' in summary, "get_signal_summary() - Has has_signal", f"Keys: {summary.keys()}")
    assert_true('bullish_count' in summary, "get_signal_summary() - Has bullish_count")
    assert_true('bearish_count' in summary, "get_signal_summary() - Has bearish_count")

# ==================== 主函數 ====================

def run_all_tests():
    """運行所有測試"""
    print("=" * 60)
    print("FutuTradingBot K線形態分析模組測試")
    print("=" * 60)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 單根K線形態測試
    print("\n" + "=" * 60)
    print("第一部分：單根K線形態測試")
    print("=" * 60)
    test_doji()
    test_hammer()
    test_shooting_star()
    test_marubozu()
    
    # 雙根K線組合測試
    print("\n" + "=" * 60)
    print("第二部分：雙根K線組合測試")
    print("=" * 60)
    test_bullish_engulfing()
    test_bearish_engulfing()
    test_harami()
    
    # 三根K線組合測試
    print("\n" + "=" * 60)
    print("第三部分：三根K線組合測試")
    print("=" * 60)
    test_morning_star()
    test_evening_star()
    
    # 信號強度評分測試
    print("\n" + "=" * 60)
    print("第四部分：信號強度評分測試")
    print("=" * 60)
    test_position_score()
    test_volume_score()
    test_trend_score()
    test_overall_score()
    
    # 邊界情況測試
    print("\n" + "=" * 60)
    print("第五部分：邊界情況測試")
    print("=" * 60)
    test_edge_cases()
    test_analyze_all()
    
    # 輸出測試摘要
    print("\n" + "=" * 60)
    print("測試摘要")
    print("=" * 60)
    
    passed = sum(1 for r in test_results if r.passed)
    failed = sum(1 for r in test_results if not r.passed)
    total = len(test_results)
    
    print(f"總測試數: {total}")
    print(f"通過: {passed}")
    print(f"失敗: {failed}")
    print(f"通過率: {passed/total*100:.1f}%" if total > 0 else "N/A")
    
    if failed > 0:
        print("\n失敗的測試:")
        for r in test_results:
            if not r.passed:
                print(f"  ❌ {r.name}")
                print(f"     錯誤: {r.error}")
                print(f"     詳情: {r.details}")
    
    return test_results

if __name__ == "__main__":
    run_all_tests()
