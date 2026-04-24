#!/usr/bin/env python3
"""
MTF Analyzer 修正版測試
驗證一致性評分邏輯修正
"""

import sys
sys.path.insert(0, 'src')
from analysis.mtf_analyzer import MTFAnalyzer, TrendDirection, TimeframeAnalysis

# 創建測試用的 TimeframeAnalysis 對象
def create_test_analysis(timeframe, trend, trend_score):
    return TimeframeAnalysis(
        timeframe=timeframe,
        trend=trend,
        trend_score=trend_score,
        ema_alignment=True,
        price_vs_ema=2.0,
        macd_signal=0.5,
        rsi_value=55.0,
        support_resistance={}
    )

analyzer = MTFAnalyzer()

print("=" * 60)
print("MTF Analyzer 修正版測試")
print("=" * 60)

# 測試案例 1: 三線一致看多 (應該得到高分)
monthly = create_test_analysis('monthly', TrendDirection.BULLISH, 85)
weekly = create_test_analysis('weekly', TrendDirection.BULLISH, 80)
daily = create_test_analysis('daily', TrendDirection.BULLISH, 75)
score = analyzer._calculate_consistency_score(monthly, weekly, daily)
print(f'測試1 - 三線一致看多: {score.overall_score:.1f} (期望: >90)')
assert score.overall_score > 90, '三線一致應該得到高分'
assert '強烈' in score.recommendation or '買入' in score.recommendation, '應該建議買入'
print(f'  ✓ 通過 - 等級: {score.consistency_level}, 建議: {score.recommendation}')

# 測試案例 2: 三線一致看空 (應該得到低分)
monthly = create_test_analysis('monthly', TrendDirection.BEARISH, 85)
weekly = create_test_analysis('weekly', TrendDirection.BEARISH, 80)
daily = create_test_analysis('daily', TrendDirection.BEARISH, 75)
score = analyzer._calculate_consistency_score(monthly, weekly, daily)
print(f'測試2 - 三線一致看空: {score.overall_score:.1f} (期望: <20)')
assert score.overall_score < 20, '三線一致看空應該得到低分'
assert '賣出' in score.recommendation or 'Strong Sell' in score.recommendation, '應該建議賣出'
print(f'  ✓ 通過 - 等級: {score.consistency_level}, 建議: {score.recommendation}')

# 測試案例 3: 逆月線大勢 (日線看多, 月線看空) - 應該被懲罰
monthly = create_test_analysis('monthly', TrendDirection.BEARISH, 85)
weekly = create_test_analysis('weekly', TrendDirection.BEARISH, 80)
daily = create_test_analysis('daily', TrendDirection.BULLISH, 75)
score = analyzer._calculate_consistency_score(monthly, weekly, daily)
print(f'測試3 - 逆月線大勢: {score.overall_score:.1f} (期望: 40-60)')
assert 40 <= score.overall_score <= 60, '逆月線大勢應該中等偏低評分'
print(f'  ✓ 通過 - 等級: {score.consistency_level}')

# 測試案例 4: 週線分歧 (日線月線一致, 週線相反)
monthly = create_test_analysis('monthly', TrendDirection.BULLISH, 85)
weekly = create_test_analysis('weekly', TrendDirection.BEARISH, 80)
daily = create_test_analysis('daily', TrendDirection.BULLISH, 75)
score = analyzer._calculate_consistency_score(monthly, weekly, daily)
print(f'測試4 - 週線分歧: {score.overall_score:.1f} (期望: 50-70)')
assert 50 <= score.overall_score <= 70, '週線分歧應該中等評分'
print(f'  ✓ 通過 - 等級: {score.consistency_level}')

# 測試案例 5: 包含 NEUTRAL (不應該得到一致性獎勵)
monthly = create_test_analysis('monthly', TrendDirection.BULLISH, 85)
weekly = create_test_analysis('weekly', TrendDirection.NEUTRAL, 50)
daily = create_test_analysis('daily', TrendDirection.BULLISH, 75)
score = analyzer._calculate_consistency_score(monthly, weekly, daily)
print(f'測試5 - 週線NEUTRAL: {score.overall_score:.1f} (期望: 60-80, 無高額獎勵)')
assert score.overall_score < 85, '有NEUTRAL不應該得到最高獎勵'
print(f'  ✓ 通過 - 等級: {score.consistency_level}')

# 測試案例 6: 權重驗證
print(f'測試6 - 權重驗證:')
print(f"  月線: {analyzer.WEIGHTS['monthly']:.0%} (期望: 40%)")
print(f"  週線: {analyzer.WEIGHTS['weekly']:.0%} (期望: 35%)")
print(f"  日線: {analyzer.WEIGHTS['daily']:.0%} (期望: 25%)")
assert analyzer.WEIGHTS['monthly'] == 0.40
assert analyzer.WEIGHTS['weekly'] == 0.35
assert analyzer.WEIGHTS['daily'] == 0.25
print('  ✓ 通過 - 權重配置正確')

# 測試案例 7: 驗證一致性乘數應用
monthly = create_test_analysis('monthly', TrendDirection.BULLISH, 80)
weekly = create_test_analysis('weekly', TrendDirection.BULLISH, 80)
daily = create_test_analysis('daily', TrendDirection.BULLISH, 80)
score = analyzer._calculate_consistency_score(monthly, weekly, daily)
print(f'測試7 - 一致性乘數驗證:')
print(f"  基礎加權分數: {score.details['score_breakdown']['base_weighted_score']:.1f}")
print(f"  一致性乘數: {score.details['score_breakdown']['consistency_multiplier']:.2f}")
print(f"  調整後分數: {score.details['score_breakdown']['adjusted_weighted_score']:.1f}")
assert score.details['score_breakdown']['consistency_multiplier'] == 1.25, '三線一致應該有1.25倍獎勵'
print('  ✓ 通過 - 一致性乘數正確應用')

print()
print("=" * 60)
print("✅ 所有測試通過!")
print("=" * 60)
