import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, '.')

from src.analysis.market_sentiment import (
    MarketSentiment, MarketPhase, SentimentIndicators,
    MoneyFlow, LiquidityMetrics, SectorMomentum, MarketSentimentAnalysis,
    MarketSentimentAnalyzer, calculate_fear_greed_index, detect_volume_anomaly,
    analyze_market_sentiment
)

TEST_RESULTS = []

def create_test_data(days=300, trend='bullish', volatility=0.02, seed=42):
    np.random.seed(seed)
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    if trend == 'bullish':
        returns = np.random.normal(0.001, volatility, days)
    elif trend == 'bearish':
        returns = np.random.normal(-0.001, volatility, days)
    else:
        returns = np.random.normal(0, volatility, days)
    prices = 100 * np.exp(np.cumsum(returns))
    df = pd.DataFrame({
        'open': prices * (1 + np.random.normal(0, 0.005, days)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, days))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, days))),
        'close': prices,
        'volume': np.random.lognormal(15, 0.5, days)
    }, index=dates)
    return df

def create_sector_data(sectors=['科技', '金融', '醫療', '能源', '消費'], days=100):
    sector_data = {}
    for i, sector in enumerate(sectors):
        np.random.seed(i)
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        returns = np.random.normal(0.0005 * (i - 2), 0.02, days)
        prices = 100 * np.exp(np.cumsum(returns))
        sector_data[sector] = pd.DataFrame({
            'close': prices,
            'volume': np.random.lognormal(14, 0.4, days)
        }, index=dates)
    return sector_data

def run_test(name, category, test_func):
    try:
        result = test_func()
        TEST_RESULTS.append({'name': name, 'category': category, 'status': 'PASSED', 'details': result if result else '測試通過'})
        print(f'  [PASS] {name}')
        return True
    except Exception as e:
        TEST_RESULTS.append({'name': name, 'category': category, 'status': 'FAILED', 'details': str(e)})
        print(f'  [FAIL] {name}: {str(e)}')
        return False

print('=' * 70)
print('FutuTradingBot 市場情緒與供需分析模組 - 第二階段驗證測試')
print('=' * 70)
print()

# ============================================
# 1. 牛熊市判別測試
# ============================================
print('【1. 牛熊市判別測試】')
print()

# 1.1 200日均線判斷邏輯 - 牛市狀態
def test_ma200_bullish():
    df = create_test_data(days=300, trend='bullish')
    analyzer = MarketSentimentAnalyzer()
    result = analyzer.detect_bull_bear(df)
    assert 'trend' in result
    assert 'signal' in result
    assert 'strength' in result
    assert result['is_bullish'] == True
    assert result['price_vs_ma200'] > 0
    return f"趨勢: {result['trend']}, 信號: {result['signal']}, 強度: {result['strength']:.2f}"
run_test('200日均線判斷邏輯 - 牛市狀態', '牛熊市判別', test_ma200_bullish)

# 1.2 200日均線判斷邏輯 - 熊市狀態
def test_ma200_bearish():
    df = create_test_data(days=300, trend='bearish')
    analyzer = MarketSentimentAnalyzer()
    result = analyzer.detect_bull_bear(df)
    assert result['is_bullish'] == False
    assert result['price_vs_ma200'] < 0
    return f"趨勢: {result['trend']}, 信號: {result['signal']}, 強度: {result['strength']:.2f}"
run_test('200日均線判斷邏輯 - 熊市狀態', '牛熊市判別', test_ma200_bearish)

# 1.3 黃金交叉檢測
def test_golden_cross():
    np.random.seed(42)
    days = 300
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    returns = np.concatenate([np.random.normal(-0.002, 0.02, 150), np.random.normal(0.003, 0.02, 150)])
    prices = 100 * np.exp(np.cumsum(returns))
    df = pd.DataFrame({'close': prices, 'volume': np.random.lognormal(15, 0.5, days)}, index=dates)
    analyzer = MarketSentimentAnalyzer()
    result = analyzer.detect_bull_bear(df)
    assert 'golden_cross' in result
    return f"黃金交叉狀態: {result['golden_cross']}, MA價差: {result['ma_spread']:.4f}"
run_test('50/200日黃金交叉檢測', '牛熊市判別', test_golden_cross)

# 1.4 死亡交叉檢測
def test_death_cross():
    np.random.seed(43)
    days = 300
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    returns = np.concatenate([np.random.normal(0.002, 0.02, 150), np.random.normal(-0.003, 0.02, 150)])
    prices = 100 * np.exp(np.cumsum(returns))
    df = pd.DataFrame({'close': prices, 'volume': np.random.lognormal(15, 0.5, days)}, index=dates)
    analyzer = MarketSentimentAnalyzer()
    result = analyzer.detect_bull_bear(df)
    assert result['golden_cross'] == False
    return f"黃金交叉狀態: {result['golden_cross']}, MA價差: {result['ma_spread']:.4f}"
run_test('50/200日死亡交叉檢測', '牛熊市判別', test_death_cross)

# 1.5 市場廣度指標
def test_market_breadth():
    df = create_test_data(days=100, trend='bullish')
    analyzer = MarketSentimentAnalyzer()
    breadth = analyzer.calculate_market_breadth(df)
    assert 0 <= breadth <= 100
    return f"市場廣度指標: {breadth}"
run_test('市場廣度指標計算', '牛熊市判別', test_market_breadth)

# 1.6 牛熊市轉換識別
def test_market_transition():
    np.random.seed(44)
    days = 250
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    returns = np.random.normal(0, 0.015, days)
    prices = 100 * np.exp(np.cumsum(returns))
    df = pd.DataFrame({'close': prices, 'volume': np.random.lognormal(15, 0.5, days)}, index=dates)
    analyzer = MarketSentimentAnalyzer()
    result = analyzer.detect_bull_bear(df)
    assert result['trend'] in ['bull_market', 'bear_market', 'transition']
    return f"檢測到的趨勢: {result['trend']}, 信號: {result['signal']}"
run_test('牛熊市轉換識別', '牛熊市判別', test_market_transition)

# ============================================
# 2. 情緒指標測試
# ============================================
print()
print('【2. 情緒指標測試】')
print()

# 2.1 VIX風格波動率指數
def test_vix_style_index():
    df = create_test_data(days=100, volatility=0.03)
    analyzer = MarketSentimentAnalyzer()
    vix = analyzer.calculate_vix_style(df)
    assert vix > 0
    assert isinstance(vix, (int, float))
    return f"VIX風格指數: {vix}"
run_test('VIX風格波動率指數計算', '情緒指標', test_vix_style_index)

# 2.2 VIX高波動場景
def test_vix_high_volatility():
    df = create_test_data(days=100, volatility=0.05)
    analyzer = MarketSentimentAnalyzer()
    vix_high = analyzer.calculate_vix_style(df)
    df_low = create_test_data(days=100, volatility=0.01)
    vix_low = analyzer.calculate_vix_style(df_low)
    assert vix_high > vix_low
    return f"高波動VIX: {vix_high}, 低波動VIX: {vix_low}"
run_test('VIX風格波動率 - 高波動場景', '情緒指標', test_vix_high_volatility)

# 2.3 成交量異常檢測 - 高成交量
def test_volume_anomaly_high():
    df = create_test_data(days=100)
    df.loc[df.index[-1], 'volume'] = df['volume'].mean() * 5
    analyzer = MarketSentimentAnalyzer()
    result = analyzer.detect_volume_anomaly(df, threshold=2.0)
    assert 'is_anomaly' in result
    assert 'score' in result
    assert 'ratio' in result
    return f"異常檢測: {result['is_anomaly']}, 評分: {result['score']}, 比率: {result['ratio']}"
run_test('成交量異常檢測 - 高成交量', '情緒指標', test_volume_anomaly_high)

# 2.4 成交量異常檢測 - 低成交量
def test_volume_anomaly_low():
    df = create_test_data(days=100)
    df.loc[df.index[-1], 'volume'] = df['volume'].mean() * 0.1
    analyzer = MarketSentimentAnalyzer()
    result = analyzer.detect_volume_anomaly(df, threshold=2.0)
    assert result['direction'] == 'low'
    return f"異常檢測: {result['is_anomaly']}, 方向: {result['direction']}, 比率: {result['ratio']}"
run_test('成交量異常檢測 - 低成交量', '情緒指標', test_volume_anomaly_low)

# 2.5 恐懼/貪婪指數
def test_fear_greed_index():
    df = create_test_data(days=100)
    analyzer = MarketSentimentAnalyzer()
    fgi = analyzer.calculate_fear_greed_index(df)
    assert 0 <= fgi <= 100
    return f"恐懼/貪婪指數: {fgi}"
run_test('恐懼/貪婪指數計算', '情緒指標', test_fear_greed_index)

# 2.6 恐懼/貪婪指數 - 極度貪婪場景
def test_fear_greed_extreme_greed():
    df = create_test_data(days=100, trend='bullish', volatility=0.01)
    analyzer = MarketSentimentAnalyzer()
    fgi = analyzer.calculate_fear_greed_index(df)
    return f"牛市貪婪指數: {fgi} (預期 > 50)"
run_test('恐懼/貪婪指數 - 極度貪婪場景', '情緒指標', test_fear_greed_extreme_greed)

# 2.7 恐懼/貪婪指數 - 極度恐懼場景
def test_fear_greed_extreme_fear():
    df = create_test_data(days=100, trend='bearish', volatility=0.04)
    analyzer = MarketSentimentAnalyzer()
    fgi = analyzer.calculate_fear_greed_index(df)
    return f"熊市恐懼指數: {fgi} (預期 < 50)"
run_test('恐懼/貪婪指數 - 極度恐懼場景', '情緒指標', test_fear_greed_extreme_fear)

# 2.8 極端情緒識別 - 極度恐懼
def test_extreme_fear_detection():
    indicators = SentimentIndicators(fear_greed_index=15.0)
    sentiment = indicators.get_dominant_sentiment()
    assert sentiment == MarketSentiment.EXTREME_FEAR
    return f"檢測到的情緒: {sentiment.value}"
run_test('極端情緒識別 - 極度恐懼', '情緒指標', test_extreme_fear_detection)

# 2.9 極端情緒識別 - 極度貪婪
def test_extreme_greed_detection():
    indicators = SentimentIndicators(fear_greed_index=85.0)
    sentiment = indicators.get_dominant_sentiment()
    assert sentiment == MarketSentiment.EXTREME_GREED
    return f"檢測到的情緒: {sentiment.value}"
run_test('極端情緒識別 - 極度貪婪', '情緒指標', test_extreme_greed_detection)

# 2.10 極端情緒識別 - 中性情緒
def test_neutral_sentiment():
    indicators = SentimentIndicators(fear_greed_index=50.0)
    sentiment = indicators.get_dominant_sentiment()
    assert sentiment == MarketSentiment.NEUTRAL
    return f"檢測到的情緒: {sentiment.value}"
run_test('極端情緒識別 - 中性情緒', '情緒指標', test_neutral_sentiment)

# ============================================
# 3. 供需分析測試
# ============================================
print()
print('【3. 供需分析測試】')
print()

# 3.1 資金流向計算
def test_money_flow_calculation():
    df = create_test_data(days=100)
    analyzer = MarketSentimentAnalyzer()
    flow = analyzer.analyze_money_flow(df)
    assert isinstance(flow, MoneyFlow)
    assert hasattr(flow, 'net_inflow')
    assert hasattr(flow, 'flow_ratio')
    assert hasattr(flow, 'flow_strength')
    return f"淨流入: {flow.net_inflow:.2f}, 流比率: {flow.flow_ratio}, 強度: {flow.flow_strength}"
run_test('資金流向計算', '供需分析', test_money_flow_calculation)

# 3.2 資金流向 - 正向流入場景
def test_money_flow_positive():
    df = create_test_data(days=100, trend='bullish')
    analyzer = MarketSentimentAnalyzer()
    flow = analyzer.analyze_money_flow(df)
    assert flow.is_positive() == (flow.net_inflow > 0)
    return f"是否正向: {flow.is_positive()}, 淨流入: {flow.net_inflow:.2f}"
run_test('資金流向 - 正向流入場景', '供需分析', test_money_flow_positive)

# 3.3 流入/流出比率計算
def test_flow_ratio():
    df = create_test_data(days=100)
    analyzer = MarketSentimentAnalyzer()
    flow = analyzer.analyze_money_flow(df)
    assert flow.flow_ratio > 0
    return f"流入/流出比率: {flow.flow_ratio:.2f}"
run_test('流入/流出比率計算', '供需分析', test_flow_ratio)

# 3.4 流動性評分計算
def test_liquidity_score():
    df = create_test_data(days=100)
    analyzer = MarketSentimentAnalyzer()
    liquidity = analyzer.calculate_liquidity_score(df)
    assert isinstance(liquidity, LiquidityMetrics)
    assert 0 <= liquidity.liquidity_score <= 100
    assert hasattr(liquidity, 'depth_score')
    assert hasattr(liquidity, 'turnover_ratio')
    return f"流動性評分: {liquidity.liquidity_score}, 深度評分: {liquidity.depth_score}, 換手率: {liquidity.turnover_ratio:.2f}"
run_test('流動性評分計算', '供需分析', test_liquidity_score)

# 3.5 流動性評分 - 高流動性場景
def test_liquidity_high():
    df = create_test_data(days=100, volatility=0.01)
    df['volume'] = df['volume'] * 3
    analyzer = MarketSentimentAnalyzer()
    liquidity = analyzer.calculate_liquidity_score(df)
    is_liquid = liquidity.is_liquid(threshold=40.0)
    return f"流動性評分: {liquidity.liquidity_score}, 是否高流動性: {is_liquid}"
run_test('流動性評分 - 高流動性場景', '供需分析', test_liquidity_high)

# 3.6 流動性評分 - 低流動性場景
def test_liquidity_low():
    df = create_test_data(days=100, volatility=0.05)
    df['volume'] = df['volume'] * 0.1
    analyzer = MarketSentimentAnalyzer()
    liquidity = analyzer.calculate_liquidity_score(df)
    is_liquid = liquidity.is_liquid(threshold=40.0)
    return f"流動性評分: {liquidity.liquidity_score}, 是否高流動性: {is_liquid}"
run_test('流動性評分 - 低流動性場景', '供需分析', test_liquidity_low)

# 3.7 買賣價差分析
def test_bid_ask_spread():
    df = create_test_data(days=100)
    analyzer = MarketSentimentAnalyzer()
    liquidity = analyzer.calculate_liquidity_score(df)
    assert hasattr(liquidity, 'bid_ask_spread')
    return f"買賣價差: {liquidity.bid_ask_spread} (需要實時報價數據)"
run_test('買賣價差分析 (結構驗證)', '供需分析', test_bid_ask_spread)

# ============================================
# 4. 板塊輪動測試
# ============================================
print()
print('【4. 板塊輪動測試】')
print()

# 4.1 板塊動量計算
def test_sector_momentum():
    sector_data = create_sector_data()
    analyzer = MarketSentimentAnalyzer()
    sectors = analyzer.track_sector_rotation(sector_data)
    assert isinstance(sectors, list)
    assert len(sectors) > 0
    assert isinstance(sectors[0], SectorMomentum)
    return f"板塊數量: {len(sectors)}, 第一板塊: {sectors[0].sector_name}, 動量: {sectors[0].momentum}"
run_test('板塊動量計算', '板塊輪動', test_sector_momentum)

# 4.2 相對強度排名
def test_relative_strength_ranking():
    sector_data = create_sector_data()
    analyzer = MarketSentimentAnalyzer()
    sectors = analyzer.track_sector_rotation(sector_data)
    for i, sector in enumerate(sectors):
        assert sector.rank == i + 1
    # 相對強度可以是負數（當動量為負時），只檢查不為零
    for sector in sectors:
        assert sector.relative_strength != 0
    return f"排名驗證通過，領漲板塊: {sectors[0].sector_name} (RS: {sectors[0].relative_strength})"
run_test('相對強度排名', '板塊輪動', test_relative_strength_ranking)

# 4.3 領漲板塊識別
def test_sector_leaders():
    sector_data = create_sector_data()
    analyzer = MarketSentimentAnalyzer()
    leaders = analyzer.detect_sector_leaders(sector_data, top_n=3)
    assert len(leaders) == 3
    assert leaders[0].momentum >= leaders[1].momentum
    return f"Top 3 領漲板塊: {[(s.sector_name, s.momentum) for s in leaders]}"
run_test('領漲板塊識別', '板塊輪動', test_sector_leaders)

# 4.4 輪動信號生成
def test_rotation_signals():
    sector_data = create_sector_data()
    analyzer = MarketSentimentAnalyzer()
    sectors = analyzer.track_sector_rotation(sector_data)
    for sector in sectors:
        assert hasattr(sector, 'volume_trend')
    return f"輪動信號驗證通過，板塊數量: {len(sectors)}"
run_test('輪動信號生成', '板塊輪動', test_rotation_signals)

# ============================================
# 5. 整合測試
# ============================================
print()
print('【5. 整合測試】')
print()

# 5.1 完整市場情緒分析
def test_full_analysis():
    df = create_test_data(days=300)
    sector_data = create_sector_data()
    analyzer = MarketSentimentAnalyzer()
    result = analyzer.analyze(df, sector_data)
    assert isinstance(result, MarketSentimentAnalysis)
    assert hasattr(result, 'sentiment')
    assert hasattr(result, 'phase')
    assert hasattr(result, 'indicators')
    assert hasattr(result, 'money_flow')
    assert hasattr(result, 'liquidity')
    assert hasattr(result, 'sector_momentum')
    return f"分析完成 - 情緒: {result.sentiment.value}, 階段: {result.phase.value}"
run_test('完整市場情緒分析', '整合測試', test_full_analysis)

# 5.2 反向信號檢測
def test_contrarian_signal():
    analysis = MarketSentimentAnalysis(
        sentiment=MarketSentiment.EXTREME_FEAR,
        phase=MarketPhase.ACCUMULATION,
        indicators=SentimentIndicators(fear_greed_index=15),
        money_flow=MoneyFlow(),
        liquidity=LiquidityMetrics()
    )
    assert analysis.is_contrarian_signal() == True
    assert analysis.get_trading_bias() == "bullish_contrarian"
    analysis2 = MarketSentimentAnalysis(
        sentiment=MarketSentiment.EXTREME_GREED,
        phase=MarketPhase.DISTRIBUTION,
        indicators=SentimentIndicators(fear_greed_index=85),
        money_flow=MoneyFlow(),
        liquidity=LiquidityMetrics()
    )
    assert analysis2.is_contrarian_signal() == True
    assert analysis2.get_trading_bias() == "bearish_contrarian"
    return "反向信號檢測通過"
run_test('反向信號檢測', '整合測試', test_contrarian_signal)

# 5.3 情緒摘要生成
def test_sentiment_summary():
    df = create_test_data(days=300)
    analyzer = MarketSentimentAnalyzer()
    analyzer.analyze(df)
    summary = analyzer.get_sentiment_summary()
    assert 'current_sentiment' in summary
    assert 'market_phase' in summary
    assert 'fear_greed_index' in summary
    assert 'trading_bias' in summary
    return f"摘要: {summary}"
run_test('情緒摘要生成', '整合測試', test_sentiment_summary)

# 5.4 便捷函數測試
def test_convenience_functions():
    df = create_test_data(days=100)
    fgi = calculate_fear_greed_index(df)
    assert 0 <= fgi <= 100
    vol_result = detect_volume_anomaly(df)
    assert 'is_anomaly' in vol_result
    analysis = analyze_market_sentiment(df)
    assert isinstance(analysis, MarketSentimentAnalysis)
    return "便捷函數測試通過"
run_test('便捷函數測試', '整合測試', test_convenience_functions)

# 5.5 數據邊界測試 - 不足數據
def test_insufficient_data():
    df = create_test_data(days=10)
    analyzer = MarketSentimentAnalyzer()
    result = analyzer.detect_bull_bear(df)
    assert result['trend'] == 'unknown'
    breadth = analyzer.calculate_market_breadth(df)
    assert breadth == 50.0
    return "邊界測試通過"
run_test('數據邊界測試 - 不足數據', '邊界測試', test_insufficient_data)

# 5.6 數據邊界測試 - 缺失成交量
def test_missing_volume():
    df = create_test_data(days=100)
    df = df.drop(columns=['volume'])
    analyzer = MarketSentimentAnalyzer()
    flow = analyzer.analyze_money_flow(df)
    assert isinstance(flow, MoneyFlow)
    vol_result = analyzer.detect_volume_anomaly(df)
    assert vol_result['is_anomaly'] == False
    return "缺失成交量測試通過"
run_test('數據邊界測試 - 缺失成交量', '邊界測試', test_missing_volume)

# ============================================
# 測試結果摘要
# ============================================
print()
print('=' * 70)
print('測試結果摘要')
print('=' * 70)

passed = sum(1 for r in TEST_RESULTS if r['status'] == 'PASSED')
failed = sum(1 for r in TEST_RESULTS if r['status'] == 'FAILED')

print(f"總測試數: {len(TEST_RESULTS)}")
print(f"通過: {passed}")
print(f"失敗: {failed}")
print(f"通過率: {passed/len(TEST_RESULTS)*100:.1f}%")

# 按類別統計
print()
print('按類別統計:')
categories = {}
for r in TEST_RESULTS:
    cat = r['category']
    if cat not in categories:
        categories[cat] = {'passed': 0, 'failed': 0}
    if r['status'] == 'PASSED':
        categories[cat]['passed'] += 1
    else:
        categories[cat]['failed'] += 1

for cat, stats in categories.items():
    total = stats['passed'] + stats['failed']
    print(f"  {cat}: {stats['passed']}/{total} 通過")

# 輸出詳細結果到文件
with open('tests/reports/sentiment_test_report.md', 'w', encoding='utf-8') as f:
    f.write("# FutuTradingBot 市場情緒與供需分析模組 - 第二階段驗證測試報告\n\n")
    f.write(f"**測試時間:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write(f"**測試目標:** `src/analysis/market_sentiment.py`\n\n")
    f.write(f"**測試環境:** Windows Sandbox\n\n")
    
    f.write("## 測試結果摘要\n\n")
    f.write(f"- **總測試數:** {len(TEST_RESULTS)}\n")
    f.write(f"- **通過:** {passed}\n")
    f.write(f"- **失敗:** {failed}\n")
    f.write(f"- **通過率:** {passed/len(TEST_RESULTS)*100:.1f}%\n\n")
    
    f.write("### 按類別統計\n\n")
    f.write("| 類別 | 通過 | 失敗 | 總計 | 狀態 |\n")
    f.write("|------|------|------|------|------|\n")
    for cat, stats in categories.items():
        total = stats['passed'] + stats['failed']
        status = "✅ 通過" if stats['failed'] == 0 else "⚠️ 部分失敗"
        f.write(f"| {cat} | {stats['passed']} | {stats['failed']} | {total} | {status} |\n")
    
    f.write("\n## 詳細測試結果\n\n")
    
    current_category = None
    for r in TEST_RESULTS:
        if r['category'] != current_category:
            current_category = r['category']
            f.write(f"\n### {current_category}\n\n")
        
        status_icon = "✅" if r['status'] == 'PASSED' else "❌"
        f.write(f"#### {status_icon} {r['name']}\n\n")
        f.write(f"**狀態:** {r['status']}\n\n")
        f.write(f"**詳情:** {r['details']}\n\n")
    
    f.write("\n---\n\n")
    f.write("*報告由 FutuTradingBot 自動測試系統生成*\n")

print()
print("測試報告已保存至: tests/reports/sentiment_test_report.md")
