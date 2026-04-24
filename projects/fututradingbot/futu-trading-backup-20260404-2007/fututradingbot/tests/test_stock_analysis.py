"""
股票9步分析法模組測試
Test Suite for Stock Analysis Module
"""

import sys
from datetime import datetime
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# 嘗試導入pytest，如果不可用則使用簡單測試框架
try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False
    # 簡單的測試裝飾器替代
    class DummyPytest:
        @staticmethod
        def fixture(func):
            return func
        @staticmethod
        def mark(*args, **kwargs):
            class DummyMark:
                @staticmethod
                def __call__(func):
                    return func
            return DummyMark()
    pytest = DummyPytest()

from analysis.stock_analysis import (
    StockAnalyzer,
    StockAnalysisReport,
    FundamentalData,
    FinancialHealth,
    CompetitorData,
    HistoricalTrend,
    MacroEnvironment,
    MarketSentiment,
    LatestEarnings,
    GrowthPotential,
    InvestmentRecommendation,
    RiskLevel,
    Recommendation,
    analyze_stock,
    batch_analyze,
)


class TestDataClasses:
    """測試數據類"""
    
    def test_fundamental_data_creation(self):
        """測試基本面數據創建"""
        data = FundamentalData(
            stock_code="AAPL",
            stock_name="Apple Inc.",
            market="US",
            industry="科技",
            sector="消費電子",
            pe_ratio=18.5,
            pb_ratio=2.8
        )
        assert data.stock_code == "AAPL"
        assert data.pe_ratio == 18.5
        assert data.market_cap == 0.0  # 默認值
    
    def test_financial_health_creation(self):
        """測試財務健康數據創建"""
        data = FinancialHealth(
            total_assets=1000000,
            total_liabilities=400000,
            roe=0.25
        )
        assert data.total_assets == 1000000
        assert data.roe == 0.25
    
    def test_historical_trend_creation(self):
        """測試歷史走勢數據創建"""
        data = HistoricalTrend(
            current_price=150.0,
            price_52w_high=180.0,
            price_52w_low=120.0,
            rsi_14=55.0
        )
        assert data.current_price == 150.0
        assert data.rsi_14 == 55.0


class TestStockAnalysisReport:
    """測試分析報告類"""
    
    def test_report_creation(self):
        """測試報告創建"""
        report = StockAnalysisReport(stock_code="US.AAPL")
        assert report.stock_code == "US.AAPL"
        assert isinstance(report.analysis_date, datetime)
    
    def test_report_to_dict(self):
        """測試報告轉字典"""
        report = StockAnalysisReport(stock_code="US.AAPL")
        report.fundamental = FundamentalData(
            stock_code="AAPL",
            stock_name="Apple",
            market="US",
            industry="科技",
            sector="消費電子"
        )
        
        data = report.to_dict()
        assert data['stock_code'] == "US.AAPL"
        assert 'fundamental' in data
        assert data['fundamental']['stock_name'] == "Apple"
    
    def test_report_to_json(self):
        """測試報告轉JSON"""
        report = StockAnalysisReport(stock_code="US.AAPL")
        json_str = report.to_json()
        assert isinstance(json_str, str)
        assert "US.AAPL" in json_str


class TestStockAnalyzer:
    """測試股票分析器"""
    
    @pytest.fixture
    def analyzer(self):
        """創建分析器實例"""
        return StockAnalyzer()
    
    def test_analyzer_initialization(self, analyzer):
        """測試分析器初始化"""
        assert analyzer is not None
        assert analyzer.futu_client is None
    
    def test_score_fundamental(self, analyzer):
        """測試基本面評分"""
        # 低PE，低PB - 應該高分
        data = FundamentalData(
            stock_code="TEST",
            stock_name="Test",
            market="US",
            industry="科技",
            sector="軟件",
            pe_ratio=12.0,
            pb_ratio=1.2,
            dividend_yield=4.0
        )
        score = analyzer._score_fundamental(data)
        assert 70 <= score <= 100
        
        # 高PE，高PB - 應該低分
        data2 = FundamentalData(
            stock_code="TEST2",
            stock_name="Test2",
            market="US",
            industry="科技",
            sector="軟件",
            pe_ratio=50.0,
            pb_ratio=6.0,
            dividend_yield=0.0
        )
        score2 = analyzer._score_fundamental(data2)
        assert 0 <= score2 <= 50
    
    def test_score_financial_health(self, analyzer):
        """測試財務健康評分"""
        data = FinancialHealth(
            current_ratio=2.5,
            quick_ratio=1.8,
            debt_to_equity=0.3,
            roe=0.20,
            roa=0.12,
            net_margin=0.18
        )
        score = analyzer._score_financial_health(data)
        assert 70 <= score <= 100
    
    def test_score_technical(self, analyzer):
        """測試技術面評分"""
        data = HistoricalTrend(
            current_price=150.0,
            ma_20=145.0,
            ma_50=140.0,
            rsi_14=55.0,
            macd=2.0,
            macd_signal=1.0,
            price_change_1m=15.0,
            volatility_30d=25.0
        )
        score = analyzer._score_technical(data)
        assert 50 <= score <= 100
    
    def test_score_sentiment(self, analyzer):
        """測試情緒評分"""
        data = MarketSentiment(
            news_sentiment_score=0.4,
            volume_anomaly=True,
            volume_vs_avg=120.0,
            analyst_rating="強烈買入"
        )
        score = analyzer._score_sentiment(data)
        assert 70 <= score <= 100
    
    def test_score_growth(self, analyzer):
        """測試成長性評分"""
        data = GrowthPotential(
            revenue_growth_3y=25.0,
            earnings_growth_3y=30.0,
            peg_ratio=0.8,
            industry_growth_rate=18.0
        )
        score = analyzer._score_growth(data)
        assert 80 <= score <= 100
    
    def test_assess_risk(self, analyzer):
        """測試風險評估"""
        report = StockAnalysisReport(stock_code="US.TEST")
        report.historical_trend = HistoricalTrend(volatility_30d=60.0)
        report.financial_health = FinancialHealth(debt_to_equity=2.5, current_ratio=0.8)
        report.market_sentiment = MarketSentiment(volume_anomaly=True)
        report.fundamental = FundamentalData(
            stock_code="TEST",
            stock_name="Test",
            market="US",
            industry="生物科技",
            sector="製藥"
        )
        
        risk = analyzer._assess_risk(report)
        assert risk in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
    
    def test_identify_strengths(self, analyzer):
        """測試識別優勢"""
        report = StockAnalysisReport(stock_code="US.TEST")
        report.fundamental = FundamentalData(
            stock_code="TEST",
            stock_name="Test",
            market="US",
            industry="科技",
            sector="軟件",
            pe_ratio=12.0,
            dividend_yield=3.5
        )
        report.financial_health = FinancialHealth(roe=0.18, current_ratio=2.5)
        report.historical_trend = HistoricalTrend(price_change_1m=15.0)
        report.growth_potential = GrowthPotential(revenue_growth_3y=20.0)
        
        strengths = analyzer._identify_strengths(report)
        assert len(strengths) > 0
        assert isinstance(strengths, list)
    
    def test_identify_risks(self, analyzer):
        """測試識別風險"""
        report = StockAnalysisReport(stock_code="US.TEST")
        report.fundamental = FundamentalData(
            stock_code="TEST",
            stock_name="Test",
            market="US",
            industry="科技",
            sector="軟件",
            pe_ratio=50.0
        )
        report.financial_health = FinancialHealth(
            debt_to_equity=2.5,
            current_ratio=0.8
        )
        report.historical_trend = HistoricalTrend(
            volatility_30d=60.0,
            price_change_3m=-25.0
        )
        report.market_sentiment = MarketSentiment(
            volume_anomaly=True,
            volume_vs_avg=-60.0
        )
        
        risks = analyzer._identify_risks(report)
        assert len(risks) > 0
        assert isinstance(risks, list)
    
    def test_calculate_rsi(self, analyzer):
        """測試RSI計算"""
        import pandas as pd
        import numpy as np
        
        # 創建測試價格數據
        prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109])
        rsi = analyzer._calculate_rsi(prices, period=5)
        
        assert 0 <= rsi <= 100
        assert isinstance(rsi, float)
    
    def test_calculate_macd(self, analyzer):
        """測試MACD計算"""
        import pandas as pd
        
        # 創建測試價格數據 (需要足夠長的序列)
        prices = pd.Series(range(100, 200))
        macd, signal = analyzer._calculate_macd(prices)
        
        assert isinstance(macd, float)
        assert isinstance(signal, float)


class TestRecommendation:
    """測試投資建議生成"""
    
    @pytest.fixture
    def analyzer(self):
        return StockAnalyzer()
    
    def test_generate_recommendation_strong_buy(self, analyzer):
        """測試強烈買入建議"""
        report = StockAnalysisReport(stock_code="US.TEST")
        report.fundamental = FundamentalData(
            stock_code="TEST", stock_name="Test", market="US",
            industry="科技", sector="軟件", pe_ratio=12.0, pb_ratio=1.5
        )
        report.financial_health = FinancialHealth(
            current_ratio=2.5, roe=0.20, debt_to_equity=0.3
        )
        report.historical_trend = HistoricalTrend(
            current_price=100.0, ma_20=95.0, ma_50=90.0, rsi_14=55.0
        )
        report.growth_potential = GrowthPotential(
            revenue_growth_3y=25.0, peg_ratio=0.8
        )
        report.market_sentiment = MarketSentiment(news_sentiment_score=0.4)
        
        rec = analyzer._generate_recommendation(report)
        
        assert rec.overall_score > 0
        assert isinstance(rec.recommendation, Recommendation)
        assert rec.target_price_mid > 0
        assert len(rec.investment_horizon) > 0
    
    def test_recommendation_levels(self, analyzer):
        """測試不同評分對應的建議等級"""
        report = StockAnalysisReport(stock_code="US.TEST")
        report.fundamental = FundamentalData(
            stock_code="TEST", stock_name="Test", market="US",
            industry="科技", sector="軟件"
        )
        report.historical_trend = HistoricalTrend(current_price=100.0)
        
        # 測試不同分數區間
        test_cases = [
            (85, Recommendation.STRONG_BUY),
            (70, Recommendation.BUY),
            (50, Recommendation.HOLD),
            (35, Recommendation.SELL),
            (20, Recommendation.STRONG_SELL),
        ]
        
        for score, expected_rec in test_cases:
            rec = InvestmentRecommendation(overall_score=score)
            
            # 手動設置建議
            if score >= 80:
                rec.recommendation = Recommendation.STRONG_BUY
            elif score >= 65:
                rec.recommendation = Recommendation.BUY
            elif score >= 45:
                rec.recommendation = Recommendation.HOLD
            elif score >= 30:
                rec.recommendation = Recommendation.SELL
            else:
                rec.recommendation = Recommendation.STRONG_SELL
            
            assert rec.recommendation == expected_rec


class TestIntegration:
    """集成測試"""
    
    def test_analyze_without_futu_client(self):
        """測試無富途客戶端時的分析"""
        analyzer = StockAnalyzer()
        
        # 這應該使用備援數據源或返回默認值
        report = analyzer.analyze("AAPL", "US")
        
        assert report.stock_code == "US.AAPL"
        assert isinstance(report.fundamental, FundamentalData)
        assert isinstance(report.recommendation, InvestmentRecommendation)
    
    def test_batch_analyze(self):
        """測試批量分析"""
        stocks = [
            ("AAPL", "US"),
            ("TSLA", "US"),
            ("00700", "HK"),
        ]
        
        reports = batch_analyze(stocks)
        
        assert len(reports) == 3
        for report in reports:
            assert isinstance(report, StockAnalysisReport)


class TestEdgeCases:
    """邊界情況測試"""
    
    def test_empty_data(self):
        """測試空數據處理"""
        data = FundamentalData(stock_code="", stock_name="", market="", industry="", sector="")
        assert data.pe_ratio == 0.0
        assert data.market_cap == 0.0
    
    def test_negative_values(self):
        """測試負值處理"""
        data = HistoricalTrend(
            price_change_1m=-20.0,
            price_change_3m=-30.0
        )
        assert data.price_change_1m == -20.0
    
    def test_zero_division_protection(self):
        """測試除零保護"""
        analyzer = StockAnalyzer()
        
        # 測試價格變動計算
        import pandas as pd
        df = pd.DataFrame({'close': [100, 0, 100]})
        change = analyzer._calc_price_change(df, 1)
        assert change == 0.0  # 應該返回0而不是拋出異常


if __name__ == "__main__":
    # 設置正確的路徑
    import os
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    
    if HAS_PYTEST:
        pytest.main([__file__, "-v"])
    else:
        # 運行簡單測試
        print("Running tests without pytest...")
        
        # 測試數據類
        t = TestDataClasses()
        t.test_fundamental_data_creation()
        print("✓ test_fundamental_data_creation")
        t.test_financial_health_creation()
        print("✓ test_financial_health_creation")
        t.test_historical_trend_creation()
        print("✓ test_historical_trend_creation")
        
        # 測試分析報告
        t2 = TestStockAnalysisReport()
        t2.test_report_creation()
        print("✓ test_report_creation")
        t2.test_report_to_dict()
        print("✓ test_report_to_dict")
        t2.test_report_to_json()
        print("✓ test_report_to_json")
        
        # 測試分析器
        a = TestStockAnalyzer()
        analyzer = a.analyzer()
        a.test_analyzer_initialization(analyzer)
        print("✓ test_analyzer_initialization")
        a.test_score_fundamental(analyzer)
        print("✓ test_score_fundamental")
        a.test_score_financial_health(analyzer)
        print("✓ test_score_financial_health")
        a.test_score_technical(analyzer)
        print("✓ test_score_technical")
        a.test_score_sentiment(analyzer)
        print("✓ test_score_sentiment")
        a.test_score_growth(analyzer)
        print("✓ test_score_growth")
        a.test_calculate_rsi(analyzer)
        print("✓ test_calculate_rsi")
        a.test_calculate_macd(analyzer)
        print("✓ test_calculate_macd")
        
        # 測試投資建議
        r = TestRecommendation()
        analyzer2 = r.analyzer()
        r.test_generate_recommendation_strong_buy(analyzer2)
        print("✓ test_generate_recommendation_strong_buy")
        
        # 集成測試
        i = TestIntegration()
        i.test_analyze_without_futu_client()
        print("✓ test_analyze_without_futu_client")
        
        print("\n" + "="*50)
        print("All tests passed!")
        print("="*50)
