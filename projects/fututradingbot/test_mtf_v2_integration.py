#!/usr/bin/env python3
"""
MTF Analyzer v2 整合測試
驗證新的權重感知一致性評分算法
"""

import sys
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot')

from src.analysis.mtf_analyzer import MTFAnalyzer, TrendDirection, TimeframeAnalysis


def test_mtf_v2_three_line_bullish():
    """測試案例1: 三線同向多頭"""
    print("=" * 60)
    print("測試1: 三線同向多頭 (強趨勢)")
    print("=" * 60)
    
    daily = TimeframeAnalysis(
        timeframe='daily',
        trend=TrendDirection.BULLISH,
        trend_score=75.0,
        ema_alignment=True,
        price_vs_ema=2.5,
        macd_signal=0.5,
        rsi_value=55.0,
        support_resistance={'support': 90, 'resistance': 110, 'adx': 28}
    )
    
    weekly = TimeframeAnalysis(
        timeframe='weekly',
        trend=TrendDirection.BULLISH,
        trend_score=80.0,
        ema_alignment=True,
        price_vs_ema=3.0,
        macd_signal=0.8,
        rsi_value=58.0,
        support_resistance={'support': 85, 'resistance': 115, 'adx': 32}
    )
    
    monthly = TimeframeAnalysis(
        timeframe='monthly',
        trend=TrendDirection.BULLISH,
        trend_score=85.0,
        ema_alignment=True,
        price_vs_ema=4.0,
        macd_signal=1.0,
        rsi_value=60.0,
        support_resistance={'support': 80, 'resistance': 120, 'adx': 35}
    )
    
    analyzer = MTFAnalyzer()
    result = analyzer._calculate_consistency_score_v2(monthly, weekly, daily)
    
    print(f"  Overall Score: {result['overall_score']}")
    print(f"  Base Score: {result['base_score']:.2f}")
    print(f"  Trend Multiplier: {result['trend_consistency_multiplier']}")
    print(f"  Strength Multiplier: {result['strength_consistency_multiplier']}")
    
    # 驗證: 三線同向應該有 x1.25 趨勢乘數
    assert result['trend_consistency_multiplier'] == 1.25, "三線同向應該有 1.25 趨勢乘數"
    # 驗證: 最終分數應該接近滿分
    assert result['overall_score'] >= 90, f"三線同向多頭應該高分, 但得到 {result['overall_score']}"
    
    print("  ✅ 測試通過!")
    return True


def test_mtf_v2_against_monthly():
    """測試案例2: 日週一致但逆月線 (嚴重警告)"""
    print()
    print("=" * 60)
    print("測試2: 日週一致但逆月線 (嚴重警告)")
    print("=" * 60)
    
    daily = TimeframeAnalysis(
        timeframe='daily',
        trend=TrendDirection.BULLISH,
        trend_score=70.0,
        ema_alignment=True,
        price_vs_ema=2.0,
        macd_signal=0.3,
        rsi_value=52.0,
        support_resistance={'support': 95, 'resistance': 105, 'adx': 25}
    )
    
    weekly = TimeframeAnalysis(
        timeframe='weekly',
        trend=TrendDirection.BULLISH,
        trend_score=75.0,
        ema_alignment=True,
        price_vs_ema=2.5,
        macd_signal=0.5,
        rsi_value=55.0,
        support_resistance={'support': 90, 'resistance': 110, 'adx': 28}
    )
    
    monthly = TimeframeAnalysis(
        timeframe='monthly',
        trend=TrendDirection.BEARISH,  # 逆月線!
        trend_score=80.0,
        ema_alignment=False,
        price_vs_ema=-3.0,
        macd_signal=-0.8,
        rsi_value=40.0,
        support_resistance={'support': 85, 'resistance': 115, 'adx': 30}
    )
    
    analyzer = MTFAnalyzer()
    result = analyzer._calculate_consistency_score_v2(monthly, weekly, daily)
    
    print(f"  Overall Score: {result['overall_score']}")
    print(f"  Base Score: {result['base_score']:.2f}")
    print(f"  Trend Multiplier: {result['trend_consistency_multiplier']}")
    print(f"  Strength Multiplier: {result['strength_consistency_multiplier']}")
    
    # 驗證: 逆月線應該有 x0.70 趨勢乘數 (嚴重懲罰)
    assert result['trend_consistency_multiplier'] == 0.70, "逆月線應該有 0.70 趨勢乘數"
    # 驗證: 最終分數應該被大幅扣分 (低於70分)
    assert result['overall_score'] < 70, f"逆月線應該低分, 但得到 {result['overall_score']}"
    
    print("  ✅ 測試通過!")
    return True


def test_mtf_v2_weekly_neutral():
    """測試案例3: 日週一致，月線中性"""
    print()
    print("=" * 60)
    print("測試3: 日週一致，月線中性")
    print("=" * 60)
    
    daily = TimeframeAnalysis(
        timeframe='daily',
        trend=TrendDirection.BULLISH,
        trend_score=65.0,
        ema_alignment=True,
        price_vs_ema=1.5,
        macd_signal=0.2,
        rsi_value=50.0,
        support_resistance={'support': 95, 'resistance': 105, 'adx': 22}
    )
    
    weekly = TimeframeAnalysis(
        timeframe='weekly',
        trend=TrendDirection.BULLISH,
        trend_score=70.0,
        ema_alignment=True,
        price_vs_ema=2.0,
        macd_signal=0.4,
        rsi_value=53.0,
        support_resistance={'support': 90, 'resistance': 110, 'adx': 25}
    )
    
    monthly = TimeframeAnalysis(
        timeframe='monthly',
        trend=TrendDirection.NEUTRAL,  # 中性
        trend_score=40.0,
        ema_alignment=False,
        price_vs_ema=0.5,
        macd_signal=0.0,
        rsi_value=50.0,
        support_resistance={'support': 85, 'resistance': 115, 'adx': 15}
    )
    
    analyzer = MTFAnalyzer()
    result = analyzer._calculate_consistency_score_v2(monthly, weekly, daily)
    
    print(f"  Overall Score: {result['overall_score']}")
    print(f"  Base Score: {result['base_score']:.2f}")
    print(f"  Trend Multiplier: {result['trend_consistency_multiplier']}")
    print(f"  Strength Multiplier: {result['strength_consistency_multiplier']}")
    
    # 驗證: 日週一致月線中性應該有 x1.15 趨勢乘數
    assert result['trend_consistency_multiplier'] == 1.15, "日週一致月線中性應該有 1.15 趨勢乘數"
    
    print("  ✅ 測試通過!")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MTF Analyzer v2 整合測試")
    print("=" * 60 + "\n")
    
    try:
        test_mtf_v2_three_line_bullish()
        test_mtf_v2_against_monthly()
        test_mtf_v2_weekly_neutral()
        
        print()
        print("=" * 60)
        print("✅ 所有測試通過!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
