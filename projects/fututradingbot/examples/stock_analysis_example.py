"""
股票9步分析法使用示例

這個示例展示了如何使用 stock_analysis 模組進行股票分析
"""

import sys
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from analysis.stock_analysis import (
    StockAnalyzer,
    analyze_stock,
    batch_analyze,
    StockAnalysisReport,
)


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("示例1: 基本使用 - 分析單一股票")
    print("=" * 60)
    
    # 創建分析器 (無富途API連接)
    analyzer = StockAnalyzer()
    
    # 分析蘋果股票
    report = analyzer.analyze("AAPL", market="US")
    
    # 輸出結果
    print(f"\n股票: {report.fundamental.stock_name} ({report.stock_code})")
    print(f"行業: {report.fundamental.industry}")
    print(f"PE比率: {report.fundamental.pe_ratio}")
    print(f"PB比率: {report.fundamental.pb_ratio}")
    print(f"\n綜合評分: {report.recommendation.overall_score:.1f}/100")
    print(f"投資建議: {report.recommendation.recommendation.value}")
    print(f"風險等級: {report.recommendation.risk_level.name}")
    
    if report.recommendation.target_price_mid > 0:
        print(f"\n目標價格:")
        print(f"  保守: ${report.recommendation.target_price_low:.2f}")
        print(f"  中性: ${report.recommendation.target_price_mid:.2f}")
        print(f"  樂觀: ${report.recommendation.target_price_high:.2f}")
    
    print("\n" + report.recommendation.analysis_summary)


def example_convenience_function():
    """便捷函數使用示例"""
    print("\n" + "=" * 60)
    print("示例2: 使用便捷函數")
    print("=" * 60)
    
    # 使用便捷函數分析股票
    report = analyze_stock("TSLA", market="US")
    
    print(f"\n股票: {report.stock_code}")
    print(f"綜合評分: {report.recommendation.overall_score:.1f}/100")
    print(f"投資建議: {report.recommendation.recommendation.value}")


def example_batch_analysis():
    """批量分析示例"""
    print("\n" + "=" * 60)
    print("示例3: 批量分析")
    print("=" * 60)
    
    # 定義要分析的股票列表
    stocks = [
        ("AAPL", "US"),
        ("MSFT", "US"),
        ("GOOGL", "US"),
        ("00700", "HK"),  # 騰訊
    ]
    
    # 批量分析
    reports = batch_analyze(stocks)
    
    print("\n批量分析結果:")
    print("-" * 60)
    print(f"{'股票代碼':<15} {'評分':<10} {'建議':<10} {'風險':<10}")
    print("-" * 60)
    
    for report in reports:
        print(f"{report.stock_code:<15} "
              f"{report.recommendation.overall_score:<10.1f} "
              f"{report.recommendation.recommendation.value:<10} "
              f"{report.recommendation.risk_level.name:<10}")


def example_with_futu_api():
    """使用富途API的示例"""
    print("\n" + "=" * 60)
    print("示例4: 使用富途API (需要OpenD連接)")
    print("=" * 60)
    
    try:
        from api.futu_client import FutuAPIClient
        
        # 連接富途API
        futu_client = FutuAPIClient(host="127.0.0.1", port=11111)
        
        if futu_client.connect_quote():
            print("✓ 成功連接到富途API")
            
            # 使用富途客戶端創建分析器
            analyzer = StockAnalyzer(futu_client=futu_client)
            
            # 分析股票
            report = analyzer.analyze("AAPL", market="US")
            
            print(f"\n分析結果:")
            print(f"股票名稱: {report.fundamental.stock_name}")
            print(f"市值: ${report.fundamental.market_cap:,.0f}")
            print(f"PE: {report.fundamental.pe_ratio:.2f}")
            
            # 斷開連接
            futu_client.disconnect_all()
            print("\n✓ 已斷開連接")
        else:
            print("✗ 無法連接到富途API，請確保OpenD已啟動")
            
    except ImportError:
        print("✗ 無法導入富途API模組")
    except Exception as e:
        print(f"✗ 錯誤: {e}")


def example_export_report():
    """導出報告示例"""
    print("\n" + "=" * 60)
    print("示例5: 導出分析報告")
    print("=" * 60)
    
    analyzer = StockAnalyzer()
    report = analyzer.analyze("AAPL", market="US")
    
    # 導出為JSON
    json_report = report.to_json(indent=2)
    
    # 保存到文件
    output_file = Path(__file__).parent / "analysis_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(json_report)
    
    print(f"\n✓ 報告已保存到: {output_file}")
    print(f"\n報告預覽 (前500字符):")
    print("-" * 60)
    print(json_report[:500] + "...")


def example_custom_analysis():
    """自定義分析示例"""
    print("\n" + "=" * 60)
    print("示例6: 自定義評分權重")
    print("=" * 60)
    
    from analysis.stock_analysis import (
        FundamentalData,
        FinancialHealth,
        HistoricalTrend,
        InvestmentRecommendation,
    )
    
    analyzer = StockAnalyzer()
    
    # 創建模擬數據
    fundamental = FundamentalData(
        stock_code="TEST",
        stock_name="Test Company",
        market="US",
        industry="科技",
        sector="軟件",
        pe_ratio=15.0,
        pb_ratio=2.0,
        dividend_yield=2.5
    )
    
    # 評分
    fundamental_score = analyzer._score_fundamental(fundamental)
    print(f"\n基本面評分: {fundamental_score:.1f}/100")
    
    financial = FinancialHealth(
        current_ratio=2.5,
        quick_ratio=1.8,
        debt_to_equity=0.5,
        roe=0.18,
        roa=0.12
    )
    
    financial_score = analyzer._score_financial_health(financial)
    print(f"財務健康評分: {financial_score:.1f}/100")
    
    # 自定義權重計算
    custom_weights = {
        'fundamental': 0.30,  # 更重視基本面
        'financial': 0.30,
        'technical': 0.15,
        'sentiment': 0.10,
        'growth': 0.15
    }
    
    # 模擬其他評分
    technical_score = 65.0
    sentiment_score = 55.0
    growth_score = 70.0
    
    overall = (
        fundamental_score * custom_weights['fundamental'] +
        financial_score * custom_weights['financial'] +
        technical_score * custom_weights['technical'] +
        sentiment_score * custom_weights['sentiment'] +
        growth_score * custom_weights['growth']
    )
    
    print(f"\n自定義權重綜合評分: {overall:.1f}/100")
    print(f"權重配置: 基本面{custom_weights['fundamental']*100:.0f}%, "
          f"財務{custom_weights['financial']*100:.0f}%, "
          f"技術{custom_weights['technical']*100:.0f}%, "
          f"情緒{custom_weights['sentiment']*100:.0f}%, "
          f"成長{custom_weights['growth']*100:.0f}%")


if __name__ == "__main__":
    print("\n")
    print("█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  股票9步分析法模組 - 使用示例".center(52) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60)
    
    # 運行所有示例
    example_basic_usage()
    example_convenience_function()
    example_batch_analysis()
    example_with_futu_api()
    example_export_report()
    example_custom_analysis()
    
    print("\n" + "=" * 60)
    print("所有示例執行完成!")
    print("=" * 60)
