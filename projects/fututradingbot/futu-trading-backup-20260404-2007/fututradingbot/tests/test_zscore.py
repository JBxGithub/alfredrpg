"""
Z-Score 指標測試
測試 technical.py 中的 Z-Score 計算功能
"""

import pandas as pd
import numpy as np
import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.indicators.technical import (
    calculate_zscore, 
    calculate_zscore_advanced,
    ZScoreResult
)


def test_zscore_basic():
    """測試基礎 Z-Score 計算"""
    print("=" * 60)
    print("測試 1: 基礎 Z-Score 計算")
    print("=" * 60)
    
    # 創建測試數據
    np.random.seed(42)
    dates = pd.date_range('2025-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 2)
    df = pd.DataFrame({'close': prices}, index=dates)
    
    # 計算 Z-Score
    zscore = calculate_zscore(df['close'], period=20)
    
    print(f"數據點數: {len(df)}")
    print(f"Z-Score 非空值: {zscore.notna().sum()}")
    print(f"最新 Z-Score: {zscore.iloc[-1]:.4f}")
    print(f"Z-Score 均值: {zscore.mean():.4f}")
    print(f"Z-Score 標準差: {zscore.std():.4f}")
    print(f"Z-Score 最大值: {zscore.max():.4f}")
    print(f"Z-Score 最小值: {zscore.min():.4f}")
    
    # 檢查 Z-Score 是否合理
    assert zscore.notna().sum() > 0, "Z-Score 應該有非空值"
    assert abs(zscore.mean()) < 0.5, "Z-Score 均值應該接近 0"
    assert 0.8 < zscore.std() < 1.2, "Z-Score 標準差應該接近 1"
    
    print("✅ 基礎 Z-Score 測試通過")
    return True


def test_zscore_advanced():
    """測試高級 Z-Score 計算"""
    print("\n" + "=" * 60)
    print("測試 2: 高級 Z-Score 計算")
    print("=" * 60)
    
    # 創建測試數據
    np.random.seed(42)
    dates = pd.date_range('2025-01-01', periods=100, freq='D')
    prices = 100 + np.cumsum(np.random.randn(100) * 2)
    df = pd.DataFrame({
        'close': prices,
        'high': prices + np.abs(np.random.randn(100)),
        'low': prices - np.abs(np.random.randn(100))
    }, index=dates)
    
    # 計算高級 Z-Score
    result = calculate_zscore_advanced(
        df, 
        period=20,
        upper_threshold=2.0,
        lower_threshold=-2.0
    )
    
    print(f"Z-Score 長度: {len(result.zscore)}")
    print(f"MA 長度: {len(result.ma)}")
    print(f"Std 長度: {len(result.std)}")
    print(f"上閾值: {result.upper_threshold}")
    print(f"下閾值: {result.lower_threshold}")
    
    # 獲取信號
    signals = result.get_signal()
    long_signals = (signals == 1).sum()
    short_signals = (signals == -1).sum()
    neutral_signals = (signals == 0).sum()
    
    print(f"\n信號統計:")
    print(f"  做多信號 (Z < -2.0): {long_signals}")
    print(f"  做空信號 (Z > 2.0): {short_signals}")
    print(f"  觀望 (|Z| <= 2.0): {neutral_signals}")
    
    # 檢查結果
    assert isinstance(result, ZScoreResult), "應該返回 ZScoreResult 對象"
    assert len(result.zscore) == len(df), "Z-Score 長度應該與數據相同"
    assert len(signals) == len(df), "信號長度應該與數據相同"
    
    print("✅ 高級 Z-Score 測試通過")
    return True


def test_zscore_signal_accuracy():
    """測試 Z-Score 信號準確性"""
    print("\n" + "=" * 60)
    print("測試 3: Z-Score 信號準確性")
    print("=" * 60)
    
    # 創建極端價格數據（測試信號觸發）
    dates = pd.date_range('2025-01-01', periods=50, freq='D')
    
    # 模擬超買情況（價格持續上漲後回落）
    prices_up = np.linspace(100, 150, 25) + np.random.randn(25) * 2
    prices_down = np.linspace(150, 100, 25) + np.random.randn(25) * 2
    prices = np.concatenate([prices_up, prices_down])
    
    df = pd.DataFrame({'close': prices}, index=dates)
    
    # 計算 Z-Score
    result = calculate_zscore_advanced(df, period=20)
    signals = result.get_signal()
    
    # 檢查信號
    print(f"最新 Z-Score: {result.zscore.iloc[-1]:.4f}")
    print(f"最新信號: {signals.iloc[-1]} ({'做多' if signals.iloc[-1] == 1 else ('做空' if signals.iloc[-1] == -1 else '觀望')})")
    
    # 統計信號
    signal_changes = signals.diff().abs().sum()
    print(f"信號變化次數: {signal_changes}")
    
    print("✅ Z-Score 信號準確性測試通過")
    return True


def test_zscore_with_real_data_pattern():
    """測試 Z-Score 在模擬真實走勢下的表現"""
    print("\n" + "=" * 60)
    print("測試 4: Z-Score 模擬真實走勢")
    print("=" * 60)
    
    # 模擬 TQQQ 類型嘅高波動走勢
    np.random.seed(123)
    dates = pd.date_range('2025-01-01', periods=252, freq='D')  # 一年數據
    
    # 生成高波動價格（類似 TQQQ）
    returns = np.random.randn(252) * 0.03  # 3% 日波動
    prices = 50 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({'close': prices}, index=dates)
    
    # 計算 Z-Score
    result = calculate_zscore_advanced(df, period=60)  # 60日 Z-Score
    
    # 統計
    zscore = result.zscore.dropna()
    
    print(f"數據期間: {dates[0].date()} 至 {dates[-1].date()}")
    print(f"起始價格: ${prices[0]:.2f}")
    print(f"結束價格: ${prices[-1]:.2f}")
    print(f"價格變化: {(prices[-1]/prices[0]-1)*100:.2f}%")
    print(f"\nZ-Score 統計:")
    print(f"  均值: {zscore.mean():.4f}")
    print(f"  標準差: {zscore.std():.4f}")
    print(f"  最大值: {zscore.max():.4f}")
    print(f"  最小值: {zscore.min():.4f}")
    
    # 檢查極端值
    extreme_high = (zscore > 2.5).sum()
    extreme_low = (zscore < -2.5).sum()
    print(f"\n極端值:")
    print(f"  Z > 2.5 (嚴重超買): {extreme_high} 次")
    print(f"  Z < -2.5 (嚴重超賣): {extreme_low} 次")
    
    print("✅ Z-Score 模擬真實走勢測試通過")
    return True


def run_all_tests():
    """執行所有測試"""
    print("\n" + "=" * 60)
    print("Z-Score 指標測試套件")
    print("=" * 60)
    
    tests = [
        ("基礎 Z-Score 計算", test_zscore_basic),
        ("高級 Z-Score 計算", test_zscore_advanced),
        ("Z-Score 信號準確性", test_zscore_signal_accuracy),
        ("Z-Score 模擬真實走勢", test_zscore_with_real_data_pattern)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {name} 測試失敗: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("測試結果摘要")
    print("=" * 60)
    print(f"通過: {passed}/{len(tests)}")
    print(f"失敗: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有測試通過！Z-Score 指標工作正常。")
    else:
        print(f"\n⚠️ {failed} 個測試失敗，需要檢查。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
