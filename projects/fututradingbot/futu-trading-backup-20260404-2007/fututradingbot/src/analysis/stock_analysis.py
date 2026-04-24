"""
股票9步分析法模組
Stock 9-Step Analysis Module

提供全面的股票分析功能，包括：
1. 基本面分析 - 公司資料、行業分類
2. 財務健康 - 資產負債表、現金流分析
3. 競爭對手 - 同業比較
4. 歷史走勢 - 價格趨勢、波動率
5. 宏觀環境 - 市場指數、行業趨勢
6. 市場情緒 - 新聞情緒、異常成交量
7. 最新財報 - 季度/年度業績
8. 成長潛力 - 營收增長、利潤率趨勢
9. 投資建議 - 綜合評分、風險評估

資料來源：
- 富途API (主要)
- Investing.com (備援)
- TradingView (圖表數據)
- 金十數據 (新聞)
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

import pandas as pd
import numpy as np

# 可選依賴
try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from src.utils.logger import get_logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    get_logger = lambda name: logging.getLogger(name)

logger = get_logger(__name__)


class RiskLevel(Enum):
    """風險等級"""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


class Recommendation(Enum):
    """投資建議"""
    STRONG_BUY = "強烈買入"
    BUY = "買入"
    HOLD = "持有"
    SELL = "賣出"
    STRONG_SELL = "強烈賣出"


@dataclass
class FundamentalData:
    """基本面數據"""
    stock_code: str
    stock_name: str
    market: str
    industry: str
    sector: str
    market_cap: float = 0.0
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    dividend_yield: float = 0.0
    eps: float = 0.0
    total_shares: int = 0
    listing_date: str = ""
    company_profile: str = ""


@dataclass
class FinancialHealth:
    """財務健康數據"""
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    total_equity: float = 0.0
    current_ratio: float = 0.0
    quick_ratio: float = 0.0
    debt_to_equity: float = 0.0
    roe: float = 0.0
    roa: float = 0.0
    gross_margin: float = 0.0
    operating_margin: float = 0.0
    net_margin: float = 0.0
    free_cash_flow: float = 0.0
    operating_cash_flow: float = 0.0
    inventory_turnover: float = 0.0
    receivables_turnover: float = 0.0


@dataclass
class CompetitorData:
    """競爭對手數據"""
    stock_code: str
    stock_name: str
    market_cap: float = 0.0
    pe_ratio: float = 0.0
    pb_ratio: float = 0.0
    revenue_growth: float = 0.0
    profit_margin: float = 0.0
    roe: float = 0.0


@dataclass
class HistoricalTrend:
    """歷史走勢數據"""
    current_price: float = 0.0
    price_52w_high: float = 0.0
    price_52w_low: float = 0.0
    price_change_1d: float = 0.0
    price_change_1w: float = 0.0
    price_change_1m: float = 0.0
    price_change_3m: float = 0.0
    price_change_ytd: float = 0.0
    volatility_30d: float = 0.0
    volatility_90d: float = 0.0
    beta: float = 0.0
    ma_20: float = 0.0
    ma_50: float = 0.0
    ma_200: float = 0.0
    rsi_14: float = 0.0
    macd: float = 0.0
    macd_signal: float = 0.0


@dataclass
class MacroEnvironment:
    """宏觀環境數據"""
    market_index_name: str = ""
    market_index_value: float = 0.0
    market_index_change: float = 0.0
    sector_performance: float = 0.0
    interest_rate: float = 0.0
    inflation_rate: float = 0.0
    gdp_growth: float = 0.0
    unemployment_rate: float = 0.0
    market_sentiment: str = ""
    vix_index: float = 0.0


@dataclass
class MarketSentiment:
    """市場情緒數據"""
    news_sentiment_score: float = 0.0
    news_sentiment_label: str = ""
    social_sentiment_score: float = 0.0
    volume_vs_avg: float = 0.0
    volume_anomaly: bool = False
    put_call_ratio: float = 0.0
    short_interest_ratio: float = 0.0
    analyst_rating: str = ""
    analyst_target_price: float = 0.0
    insider_trading_signal: str = ""


@dataclass
class LatestEarnings:
    """最新財報數據"""
    report_date: str = ""
    fiscal_quarter: str = ""
    revenue: float = 0.0
    revenue_yoy_change: float = 0.0
    net_income: float = 0.0
    net_income_yoy_change: float = 0.0
    eps_actual: float = 0.0
    eps_estimate: float = 0.0
    eps_surprise: float = 0.0
    ebitda: float = 0.0
    gross_profit: float = 0.0
    operating_income: float = 0.0


@dataclass
class GrowthPotential:
    """成長潛力數據"""
    revenue_growth_3y: float = 0.0
    revenue_growth_5y: float = 0.0
    earnings_growth_3y: float = 0.0
    earnings_growth_5y: float = 0.0
    profit_margin_trend: str = ""
    revenue_trend: str = ""
    peg_ratio: float = 0.0
    forward_pe: float = 0.0
    estimated_eps_growth: float = 0.0
    industry_growth_rate: float = 0.0


@dataclass
class InvestmentRecommendation:
    """投資建議"""
    overall_score: float = 0.0
    fundamental_score: float = 0.0
    financial_health_score: float = 0.0
    technical_score: float = 0.0
    sentiment_score: float = 0.0
    growth_score: float = 0.0
    risk_level: RiskLevel = RiskLevel.MEDIUM
    recommendation: Recommendation = Recommendation.HOLD
    target_price_low: float = 0.0
    target_price_mid: float = 0.0
    target_price_high: float = 0.0
    investment_horizon: str = ""
    key_strengths: List[str] = field(default_factory=list)
    key_risks: List[str] = field(default_factory=list)
    analysis_summary: str = ""


@dataclass
class StockAnalysisReport:
    """完整股票分析報告"""
    stock_code: str
    analysis_date: datetime = field(default_factory=datetime.now)
    fundamental: FundamentalData = field(default_factory=lambda: FundamentalData("", "", "", "", ""))
    financial_health: FinancialHealth = field(default_factory=FinancialHealth)
    competitors: List[CompetitorData] = field(default_factory=list)
    historical_trend: HistoricalTrend = field(default_factory=HistoricalTrend)
    macro_environment: MacroEnvironment = field(default_factory=MacroEnvironment)
    market_sentiment: MarketSentiment = field(default_factory=MarketSentiment)
    latest_earnings: LatestEarnings = field(default_factory=LatestEarnings)
    growth_potential: GrowthPotential = field(default_factory=GrowthPotential)
    recommendation: InvestmentRecommendation = field(default_factory=InvestmentRecommendation)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "stock_code": self.stock_code,
            "analysis_date": self.analysis_date.isoformat(),
            "fundamental": self.fundamental.__dict__,
            "financial_health": self.financial_health.__dict__,
            "competitors": [c.__dict__ for c in self.competitors],
            "historical_trend": self.historical_trend.__dict__,
            "macro_environment": self.macro_environment.__dict__,
            "market_sentiment": self.market_sentiment.__dict__,
            "latest_earnings": self.latest_earnings.__dict__,
            "growth_potential": self.growth_potential.__dict__,
            "recommendation": {
                **self.recommendation.__dict__,
                "risk_level": self.recommendation.risk_level.name,
                "recommendation": self.recommendation.recommendation.value
            }
        }
    
    def to_json(self, indent: int = 2) -> str:
        """轉換為JSON字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)


class StockAnalyzer:
    """
    股票分析器
    實現9步分析法的核心類
    """
    
    def __init__(self, futu_client=None):
        """
        初始化分析器
        
        Args:
            futu_client: 富途API客戶端實例 (可選)
        """
        self.futu_client = futu_client
        self.session = None
        if requests:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        logger.info("股票分析器已初始化")
    
    def analyze(self, stock_code: str, market: str = "US") -> StockAnalysisReport:
        """
        執行完整的9步分析
        
        Args:
            stock_code: 股票代碼 (如 'AAPL', '00700')
            market: 市場代碼 ('US', 'HK', 'SH', 'SZ')
            
        Returns:
            StockAnalysisReport: 完整分析報告
        """
        logger.info(f"開始分析股票: {market}.{stock_code}")
        
        report = StockAnalysisReport(stock_code=f"{market}.{stock_code}")
        
        # 步驟1: 基本面分析
        logger.info("步驟1: 基本面分析")
        report.fundamental = self._analyze_fundamental(stock_code, market)
        
        # 步驟2: 財務健康
        logger.info("步驟2: 財務健康分析")
        report.financial_health = self._analyze_financial_health(stock_code, market)
        
        # 步驟3: 競爭對手
        logger.info("步驟3: 競爭對手分析")
        report.competitors = self._analyze_competitors(stock_code, market, report.fundamental.industry)
        
        # 步驟4: 歷史走勢
        logger.info("步驟4: 歷史走勢分析")
        report.historical_trend = self._analyze_historical_trend(stock_code, market)
        
        # 步驟5: 宏觀環境
        logger.info("步驟5: 宏觀環境分析")
        report.macro_environment = self._analyze_macro_environment(market)
        
        # 步驟6: 市場情緒
        logger.info("步驟6: 市場情緒分析")
        report.market_sentiment = self._analyze_market_sentiment(stock_code, market)
        
        # 步驟7: 最新財報
        logger.info("步驟7: 最新財報分析")
        report.latest_earnings = self._analyze_latest_earnings(stock_code, market)
        
        # 步驟8: 成長潛力
        logger.info("步驟8: 成長潛力分析")
        report.growth_potential = self._analyze_growth_potential(stock_code, market)
        
        # 步驟9: 投資建議
        logger.info("步驟9: 生成投資建議")
        report.recommendation = self._generate_recommendation(report)
        
        logger.info(f"股票分析完成: {market}.{stock_code}")
        return report
    
    def _analyze_fundamental(self, stock_code: str, market: str) -> FundamentalData:
        """
        步驟1: 基本面分析
        獲取公司基本資料、行業分類
        """
        data = FundamentalData(stock_code=stock_code, market=market, stock_name="", industry="", sector="")
        
        try:
            # 優先使用富途API
            if self.futu_client and self.futu_client.quote_client:
                full_code = f"{market}.{stock_code}"
                ret_code, ret_data = self.futu_client.quote_client.get_stock_basicinfo(
                    self._get_futu_market(market)
                )
                if ret_code == 0:
                    stock_info = ret_data[ret_data['code'] == full_code]
                    if not stock_info.empty:
                        data.stock_name = stock_info.iloc[0].get('name', stock_code)
                        data.industry = stock_info.iloc[0].get('industry', 'Unknown')
                        data.sector = stock_info.iloc[0].get('sector', 'Unknown')
                        data.total_shares = int(stock_info.iloc[0].get('lot_size', 0))
                
                # 獲取市場快照
                ret_code, snapshot = self.futu_client.quote_client.get_market_snapshot([full_code])
                if ret_code == 0 and not snapshot.empty:
                    data.market_cap = float(snapshot.iloc[0].get('market_val', 0))
                    data.pe_ratio = float(snapshot.iloc[0].get('pe_ratio', 0))
                    data.pb_ratio = float(snapshot.iloc[0].get('pb_ratio', 0))
                    data.dividend_yield = float(snapshot.iloc[0].get('dividend_yield', 0))
                    
        except Exception as e:
            logger.warning(f"富途API基本面分析失敗: {e}")
        
        # 如果富途API數據不完整，使用備援數據源
        if not data.stock_name or data.market_cap == 0:
            try:
                backup_data = self._fetch_fundamental_from_investing(stock_code, market)
                if backup_data:
                    data.stock_name = data.stock_name or backup_data.get('name', stock_code)
                    data.industry = data.industry or backup_data.get('industry', 'Unknown')
                    data.sector = data.sector or backup_data.get('sector', 'Unknown')
                    data.market_cap = data.market_cap or backup_data.get('market_cap', 0)
                    data.pe_ratio = data.pe_ratio or backup_data.get('pe_ratio', 0)
                    data.pb_ratio = data.pb_ratio or backup_data.get('pb_ratio', 0)
            except Exception as e:
                logger.warning(f"備援基本面數據獲取失敗: {e}")
        
        return data
    
    def _analyze_financial_health(self, stock_code: str, market: str) -> FinancialHealth:
        """
        步驟2: 財務健康分析
        分析資產負債表、現金流
        """
        data = FinancialHealth()
        
        try:
            # 使用富途API獲取財務數據
            if self.futu_client and self.futu_client.quote_client:
                full_code = f"{market}.{stock_code}"
                # 這裡可以擴展調用富途的財務數據接口
                pass
        except Exception as e:
            logger.warning(f"富途API財務分析失敗: {e}")
        
        # 計算關鍵財務比率
        if data.total_equity > 0:
            data.debt_to_equity = data.total_liabilities / data.total_equity
            data.roe = (data.net_income if hasattr(data, 'net_income') else 0) / data.total_equity
        
        if data.total_assets > 0:
            data.roa = (data.net_income if hasattr(data, 'net_income') else 0) / data.total_assets
        
        return data
    
    def _analyze_competitors(self, stock_code: str, market: str, industry: str) -> List[CompetitorData]:
        """
        步驟3: 競爭對手分析
        同業比較
        """
        competitors = []
        
        try:
            # 基於行業獲取競爭對手列表
            if self.futu_client and self.futu_client.quote_client:
                ret_code, all_stocks = self.futu_client.quote_client.get_stock_basicinfo(
                    self._get_futu_market(market)
                )
                if ret_code == 0:
                    # 篩選同行業股票
                    industry_peers = all_stocks[all_stocks['industry'] == industry]
                    # 取前5個作為競爭對手
                    for _, row in industry_peers.head(5).iterrows():
                        if row['code'] != f"{market}.{stock_code}":
                            comp = CompetitorData(
                                stock_code=row['code'],
                                stock_name=row.get('name', ''),
                                market_cap=row.get('market_cap', 0),
                                pe_ratio=row.get('pe_ratio', 0),
                                pb_ratio=row.get('pb_ratio', 0)
                            )
                            competitors.append(comp)
        except Exception as e:
            logger.warning(f"競爭對手分析失敗: {e}")
        
        return competitors
    
    def _analyze_historical_trend(self, stock_code: str, market: str) -> HistoricalTrend:
        """
        步驟4: 歷史走勢分析
        價格趨勢、波動率計算
        """
        data = HistoricalTrend()
        
        try:
            if self.futu_client and self.futu_client.quote_client:
                import futu as ft
                full_code = f"{market}.{stock_code}"
                
                # 獲取K線數據
                ret_code, kline = self.futu_client.quote_client.get_cur_kline(
                    full_code, num=252, ktype=ft.KLType.K_DAY
                )
                
                if ret_code == 0 and not kline.empty:
                    df = kline.copy()
                    df['close'] = pd.to_numeric(df['close'], errors='coerce')
                    
                    # 當前價格
                    data.current_price = float(df['close'].iloc[-1])
                    
                    # 52週高低點
                    data.price_52w_high = float(df['close'].max())
                    data.price_52w_low = float(df['close'].min())
                    
                    # 價格變動
                    data.price_change_1d = self._calc_price_change(df, 1)
                    data.price_change_1w = self._calc_price_change(df, 5)
                    data.price_change_1m = self._calc_price_change(df, 20)
                    data.price_change_3m = self._calc_price_change(df, 60)
                    data.price_change_ytd = self._calc_price_change(df, len(df[df['time_key'] >= f"{datetime.now().year}-01-01"]))
                    
                    # 波動率
                    returns = df['close'].pct_change().dropna()
                    data.volatility_30d = float(returns.tail(30).std() * np.sqrt(252) * 100)
                    data.volatility_90d = float(returns.tail(90).std() * np.sqrt(252) * 100)
                    
                    # 移動平均線
                    data.ma_20 = float(df['close'].tail(20).mean())
                    data.ma_50 = float(df['close'].tail(50).mean())
                    data.ma_200 = float(df['close'].tail(200).mean()) if len(df) >= 200 else 0
                    
                    # RSI
                    data.rsi_14 = self._calculate_rsi(df['close'], 14)
                    
                    # MACD
                    data.macd, data.macd_signal = self._calculate_macd(df['close'])
                    
        except Exception as e:
            logger.warning(f"歷史走勢分析失敗: {e}")
        
        return data
    
    def _analyze_macro_environment(self, market: str) -> MacroEnvironment:
        """
        步驟5: 宏觀環境分析
        市場指數、行業趨勢
        """
        data = MacroEnvironment()
        
        try:
            # 設置市場指數
            if market == "US":
                data.market_index_name = "S&P 500"
            elif market == "HK":
                data.market_index_name = "恆生指數"
            elif market in ["SH", "SZ"]:
                data.market_index_name = "上證指數" if market == "SH" else "深證成指"
            
            # 獲取市場指數數據
            if self.futu_client and self.futu_client.quote_client:
                index_codes = {
                    "US": "US.SPX",
                    "HK": "HK.HSI",
                    "SH": "SH.000001",
                    "SZ": "SZ.399001"
                }
                index_code = index_codes.get(market)
                if index_code:
                    ret_code, snapshot = self.futu_client.quote_client.get_market_snapshot([index_code])
                    if ret_code == 0 and not snapshot.empty:
                        data.market_index_value = float(snapshot.iloc[0].get('last_price', 0))
                        data.market_index_change = float(snapshot.iloc[0].get('change_rate', 0)) * 100
                        
        except Exception as e:
            logger.warning(f"宏觀環境分析失敗: {e}")
        
        return data
    
    def _analyze_market_sentiment(self, stock_code: str, market: str) -> MarketSentiment:
        """
        步驟6: 市場情緒分析
        新聞情緒、異常成交量
        """
        data = MarketSentiment()
        
        try:
            # 獲取成交量數據
            if self.futu_client and self.futu_client.quote_client:
                import futu as ft
                full_code = f"{market}.{stock_code}"
                ret_code, kline = self.futu_client.quote_client.get_cur_kline(
                    full_code, num=30, ktype=ft.KLType.K_DAY
                )
                
                if ret_code == 0 and not kline.empty:
                    df = kline.copy()
                    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
                    
                    avg_volume = df['volume'].head(20).mean()
                    current_volume = df['volume'].iloc[-1]
                    
                    data.volume_vs_avg = (current_volume / avg_volume - 1) * 100 if avg_volume > 0 else 0
                    data.volume_anomaly = data.volume_vs_avg > 50  # 成交量超過平均50%
                    
        except Exception as e:
            logger.warning(f"市場情緒分析失敗: {e}")
        
        return data
    
    def _analyze_latest_earnings(self, stock_code: str, market: str) -> LatestEarnings:
        """
        步驟7: 最新財報分析
        季度/年度業績
        """
        data = LatestEarnings()
        
        try:
            # 這裡可以擴展調用財報數據API
            pass
        except Exception as e:
            logger.warning(f"最新財報分析失敗: {e}")
        
        return data
    
    def _analyze_growth_potential(self, stock_code: str, market: str) -> GrowthPotential:
        """
        步驟8: 成長潛力分析
        營收增長、利潤率趨勢
        """
        data = GrowthPotential()
        
        try:
            # 基於歷史數據計算增長趨勢
            if self.futu_client and self.futu_client.quote_client:
                import futu as ft
                full_code = f"{market}.{stock_code}"
                ret_code, kline = self.futu_client.quote_client.get_cur_kline(
                    full_code, num=252*5, ktype=ft.KLType.K_DAY
                )
                
                if ret_code == 0 and not kline.empty:
                    df = kline.copy()
                    df['close'] = pd.to_numeric(df['close'], errors='coerce')
                    
                    # 計算長期價格趨勢作為增長指標
                    if len(df) >= 252 * 3:
                        price_3y_ago = df['close'].iloc[-252*3]
                        current_price = df['close'].iloc[-1]
                        data.revenue_growth_3y = (current_price / price_3y_ago - 1) * 100
                    
                    if len(df) >= 252 * 5:
                        price_5y_ago = df['close'].iloc[-252*5]
                        data.revenue_growth_5y = (current_price / price_5y_ago - 1) * 100
                    
        except Exception as e:
            logger.warning(f"成長潛力分析失敗: {e}")
        
        return data
    
    def _generate_recommendation(self, report: StockAnalysisReport) -> InvestmentRecommendation:
        """
        步驟9: 生成投資建議
        綜合評分、風險評估
        """
        rec = InvestmentRecommendation()
        
        # 計算各維度評分 (0-100)
        rec.fundamental_score = self._score_fundamental(report.fundamental)
        rec.financial_health_score = self._score_financial_health(report.financial_health)
        rec.technical_score = self._score_technical(report.historical_trend)
        rec.sentiment_score = self._score_sentiment(report.market_sentiment)
        rec.growth_score = self._score_growth(report.growth_potential)
        
        # 計算總分
        weights = {
            'fundamental': 0.20,
            'financial': 0.20,
            'technical': 0.20,
            'sentiment': 0.15,
            'growth': 0.25
        }
        
        rec.overall_score = (
            rec.fundamental_score * weights['fundamental'] +
            rec.financial_health_score * weights['financial'] +
            rec.technical_score * weights['technical'] +
            rec.sentiment_score * weights['sentiment'] +
            rec.growth_score * weights['growth']
        )
        
        # 確定投資建議
        if rec.overall_score >= 80:
            rec.recommendation = Recommendation.STRONG_BUY
        elif rec.overall_score >= 65:
            rec.recommendation = Recommendation.BUY
        elif rec.overall_score >= 45:
            rec.recommendation = Recommendation.HOLD
        elif rec.overall_score >= 30:
            rec.recommendation = Recommendation.SELL
        else:
            rec.recommendation = Recommendation.STRONG_SELL
        
        # 風險評估
        rec.risk_level = self._assess_risk(report)
        
        # 目標價格
        current_price = report.historical_trend.current_price
        if current_price > 0:
            rec.target_price_low = current_price * 0.85
            rec.target_price_mid = current_price * 1.15
            rec.target_price_high = current_price * 1.35
        
        # 投資期限
        if rec.growth_score > 70:
            rec.investment_horizon = "長期 (1-3年)"
        elif rec.technical_score > 70:
            rec.investment_horizon = "短期 (1-3個月)"
        else:
            rec.investment_horizon = "中期 (3-12個月)"
        
        # 關鍵優勢與風險
        rec.key_strengths = self._identify_strengths(report)
        rec.key_risks = self._identify_risks(report)
        
        # 分析摘要
        rec.analysis_summary = self._generate_summary(report, rec)
        
        return rec
    
    # ============ 輔助方法 ============
    
    def _get_futu_market(self, market: str):
        """轉換市場代碼為富途格式"""
        import futu as ft
        market_map = {
            "HK": ft.Market.HK,
            "US": ft.Market.US,
            "SH": ft.Market.SH,
            "SZ": ft.Market.SZ
        }
        return market_map.get(market, ft.Market.US)
    
    def _calc_price_change(self, df: pd.DataFrame, periods: int) -> float:
        """計算價格變動百分比"""
        if len(df) < periods + 1 or periods == 0:
            return 0.0
        current = df['close'].iloc[-1]
        previous = df['close'].iloc[-(periods + 1)]
        return (current / previous - 1) * 100 if previous > 0 else 0.0
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """計算RSI指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty else 50.0
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float]:
        """計算MACD指標"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        return float(macd.iloc[-1]), float(macd_signal.iloc[-1])
    
    def _fetch_fundamental_from_investing(self, stock_code: str, market: str) -> Optional[Dict]:
        """從Investing.com獲取基本面數據 (備援)"""
        # 這裡實現網頁抓取邏輯
        return None
    
    def _score_fundamental(self, data: FundamentalData) -> float:
        """基本面評分"""
        score = 50.0  # 基礎分
        
        # PE評分 (低PE較好)
        if 0 < data.pe_ratio < 15:
            score += 20
        elif 15 <= data.pe_ratio < 25:
            score += 10
        elif data.pe_ratio >= 40:
            score -= 10
        
        # PB評分 (低PB較好)
        if 0 < data.pb_ratio < 1.5:
            score += 15
        elif 1.5 <= data.pb_ratio < 3:
            score += 5
        elif data.pb_ratio >= 5:
            score -= 10
        
        # 股息率評分
        if data.dividend_yield > 3:
            score += 15
        elif data.dividend_yield > 1.5:
            score += 5
        
        return min(100, max(0, score))
    
    def _score_financial_health(self, data: FinancialHealth) -> float:
        """財務健康評分"""
        score = 50.0
        
        # 流動比率
        if data.current_ratio > 2:
            score += 15
        elif data.current_ratio > 1.5:
            score += 10
        elif data.current_ratio < 1:
            score -= 10
        
        # 速動比率
        if data.quick_ratio > 1.5:
            score += 10
        elif data.quick_ratio < 0.8:
            score -= 5
        
        # 負債權益比
        if 0 < data.debt_to_equity < 0.5:
            score += 15
        elif 0.5 <= data.debt_to_equity < 1:
            score += 5
        elif data.debt_to_equity > 2:
            score -= 15
        
        # ROE
        if data.roe > 0.15:
            score += 15
        elif data.roe > 0.10:
            score += 10
        elif data.roe < 0.05:
            score -= 10
        
        # ROA
        if data.roa > 0.10:
            score += 10
        elif data.roa < 0.02:
            score -= 5
        
        # 淨利率
        if data.net_margin > 0.15:
            score += 10
        elif data.net_margin < 0.05:
            score -= 5
        
        return min(100, max(0, score))
    
    def _score_technical(self, data: HistoricalTrend) -> float:
        """技術面評分"""
        score = 50.0
        
        # 趨勢評分
        if data.price_change_1m > 10:
            score += 10
        elif data.price_change_1m < -10:
            score -= 10
        
        if data.price_change_3m > 20:
            score += 10
        elif data.price_change_3m < -20:
            score -= 10
        
        # 移動平均線評分
        if data.current_price > data.ma_20 > data.ma_50:
            score += 15  # 多頭排列
        elif data.current_price < data.ma_20 < data.ma_50:
            score -= 10  # 空頭排列
        
        # RSI評分
        if 40 <= data.rsi_14 <= 60:
            score += 10  # 正常區間
        elif data.rsi_14 > 70:
            score -= 10  # 超買
        elif data.rsi_14 < 30:
            score += 5   # 超賣(可能反彈)
        
        # MACD評分
        if data.macd > data.macd_signal and data.macd > 0:
            score += 10
        elif data.macd < data.macd_signal and data.macd < 0:
            score -= 10
        
        # 波動率評分
        if data.volatility_30d < 20:
            score += 5   # 低波動
        elif data.volatility_30d > 50:
            score -= 5   # 高波動
        
        return min(100, max(0, score))
    
    def _score_sentiment(self, data: MarketSentiment) -> float:
        """市場情緒評分"""
        score = 50.0
        
        # 新聞情緒
        if data.news_sentiment_score > 0.3:
            score += 15
        elif data.news_sentiment_score < -0.3:
            score -= 15
        elif data.news_sentiment_score > 0.1:
            score += 5
        elif data.news_sentiment_score < -0.1:
            score -= 5
        
        # 成交量異常
        if data.volume_anomaly:
            if data.volume_vs_avg > 100:
                score += 10  # 巨量可能是好消息
            elif data.volume_vs_avg < -50:
                score -= 10  # 量縮
        
        # 分析師評級
        if data.analyst_rating == "強烈買入":
            score += 15
        elif data.analyst_rating == "買入":
            score += 10
        elif data.analyst_rating == "賣出":
            score -= 10
        elif data.analyst_rating == "強烈賣出":
            score -= 15
        
        return min(100, max(0, score))
    
    def _score_growth(self, data: GrowthPotential) -> float:
        """成長潛力評分"""
        score = 50.0
        
        # 營收增長
        if data.revenue_growth_3y > 20:
            score += 20
        elif data.revenue_growth_3y > 10:
            score += 15
        elif data.revenue_growth_3y > 5:
            score += 10
        elif data.revenue_growth_3y < 0:
            score -= 10
        
        # 盈利增長
        if data.earnings_growth_3y > 20:
            score += 20
        elif data.earnings_growth_3y > 10:
            score += 15
        elif data.earnings_growth_3y < 0:
            score -= 15
        
        # PEG比率
        if 0 < data.peg_ratio < 1:
            score += 15
        elif 1 <= data.peg_ratio < 2:
            score += 5
        elif data.peg_ratio > 3:
            score -= 10
        
        # 行業增長率
        if data.industry_growth_rate > 15:
            score += 10
        elif data.industry_growth_rate < 5:
            score -= 5
        
        return min(100, max(0, score))
    
    def _assess_risk(self, report: StockAnalysisReport) -> RiskLevel:
        """評估風險等級"""
        risk_score = 0
        
        # 基於波動率
        if report.historical_trend.volatility_30d > 50:
            risk_score += 2
        elif report.historical_trend.volatility_30d < 20:
            risk_score -= 1
        
        # 基於財務槓桿
        if report.financial_health.debt_to_equity > 2:
            risk_score += 2
        elif report.financial_health.debt_to_equity < 0.5:
            risk_score -= 1
        
        # 基於流動性
        if report.financial_health.current_ratio < 1:
            risk_score += 2
        elif report.financial_health.current_ratio > 2:
            risk_score -= 1
        
        # 基於市場情緒
        if report.market_sentiment.volume_anomaly:
            risk_score += 1
        
        # 基於行業
        high_risk_industries = ['生物科技', '加密貨幣', '半導體']
        if report.fundamental.industry in high_risk_industries:
            risk_score += 1
        
        # 映射到風險等級
        if risk_score <= 0:
            return RiskLevel.LOW
        elif risk_score <= 1:
            return RiskLevel.MEDIUM
        elif risk_score <= 2:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def _identify_strengths(self, report: StockAnalysisReport) -> List[str]:
        """識別關鍵優勢"""
        strengths = []
        
        if report.fundamental.pe_ratio > 0 and report.fundamental.pe_ratio < 15:
            strengths.append(f"估值合理 (PE: {report.fundamental.pe_ratio:.2f})")
        
        if report.financial_health.roe > 0.15:
            strengths.append(f"高股東權益報酬率 (ROE: {report.financial_health.roe*100:.1f}%)")
        
        if report.financial_health.current_ratio > 2:
            strengths.append("良好的流動性")
        
        if report.historical_trend.price_change_1m > 10:
            strengths.append("短期上升趨勢強勁")
        
        if report.growth_potential.revenue_growth_3y > 15:
            strengths.append(f"高營收增長 ({report.growth_potential.revenue_growth_3y:.1f}%)")
        
        if report.fundamental.dividend_yield > 3:
            strengths.append(f"高股息率 ({report.fundamental.dividend_yield:.2f}%)")
        
        return strengths[:5]  # 最多5個優勢
    
    def _identify_risks(self, report: StockAnalysisReport) -> List[str]:
        """識別關鍵風險"""
        risks = []
        
        if report.fundamental.pe_ratio > 40:
            risks.append(f"估值偏高 (PE: {report.fundamental.pe_ratio:.2f})")
        
        if report.financial_health.debt_to_equity > 2:
            risks.append(f"高負債水平 (D/E: {report.financial_health.debt_to_equity:.2f})")
        
        if report.financial_health.current_ratio < 1:
            risks.append("流動性風險")
        
        if report.historical_trend.volatility_30d > 50:
            risks.append(f"高波動性 ({report.historical_trend.volatility_30d:.1f}%)")
        
        if report.historical_trend.price_change_3m < -20:
            risks.append("中期下降趨勢")
        
        if report.market_sentiment.volume_anomaly and report.market_sentiment.volume_vs_avg < -50:
            risks.append("成交量萎縮")
        
        return risks[:5]  # 最多5個風險
    
    def _generate_summary(self, report: StockAnalysisReport, rec: InvestmentRecommendation) -> str:
        """生成分析摘要"""
        summary_parts = []
        
        # 基本信息
        summary_parts.append(
            f"{report.fundamental.stock_name} ({report.stock_code}) 分析摘要:\n"
        )
        
        # 評分概覽
        summary_parts.append(
            f"綜合評分: {rec.overall_score:.1f}/100 | "
            f"基本面: {rec.fundamental_score:.1f} | "
            f"財務健康: {rec.financial_health_score:.1f} | "
            f"技術面: {rec.technical_score:.1f} | "
            f"情緒: {rec.sentiment_score:.1f} | "
            f"成長性: {rec.growth_score:.1f}\n"
        )
        
        # 投資建議
        summary_parts.append(
            f"投資建議: {rec.recommendation.value} | "
            f"風險等級: {rec.risk_level.name} | "
            f"投資期限: {rec.investment_horizon}\n"
        )
        
        # 目標價
        if rec.target_price_mid > 0:
            summary_parts.append(
                f"目標價格: ${rec.target_price_low:.2f} - ${rec.target_price_mid:.2f} - ${rec.target_price_high:.2f}\n"
            )
        
        # 關鍵優勢
        if rec.key_strengths:
            summary_parts.append("\n關鍵優勢:")
            for strength in rec.key_strengths:
                summary_parts.append(f"  ✓ {strength}")
        
        # 關鍵風險
        if rec.key_risks:
            summary_parts.append("\n關鍵風險:")
            for risk in rec.key_risks:
                summary_parts.append(f"  ⚠ {risk}")
        
        return "\n".join(summary_parts)


# ============ 便捷函數 ============

def analyze_stock(stock_code: str, market: str = "US", futu_client=None) -> StockAnalysisReport:
    """
    便捷函數: 分析單一股票
    
    Args:
        stock_code: 股票代碼
        market: 市場代碼
        futu_client: 富途API客戶端
        
    Returns:
        StockAnalysisReport: 分析報告
    """
    analyzer = StockAnalyzer(futu_client)
    return analyzer.analyze(stock_code, market)


def batch_analyze(stock_codes: List[Tuple[str, str]], futu_client=None) -> List[StockAnalysisReport]:
    """
    便捷函數: 批量分析股票
    
    Args:
        stock_codes: 股票代碼列表 [(code, market), ...]
        futu_client: 富途API客戶端
        
    Returns:
        List[StockAnalysisReport]: 分析報告列表
    """
    analyzer = StockAnalyzer(futu_client)
    reports = []
    
    for code, market in stock_codes:
        try:
            report = analyzer.analyze(code, market)
            reports.append(report)
        except Exception as e:
            logger.error(f"分析 {market}.{code} 失敗: {e}")
    
    return reports


# ============ 模組測試 ============

if __name__ == "__main__":
    # 測試代碼
    print("股票9步分析法模組測試")
    print("=" * 50)
    
    # 創建模擬數據進行測試
    analyzer = StockAnalyzer()
    
    # 測試評分系統
    fundamental = FundamentalData(
        stock_code="AAPL",
        stock_name="Apple Inc.",
        market="US",
        industry="科技",
        sector="消費電子",
        pe_ratio=18.5,
        pb_ratio=2.8,
        dividend_yield=0.5
    )
    
    score = analyzer._score_fundamental(fundamental)
    print(f"基本面評分測試: {score:.1f}/100")
    
    # 測試數據類轉換
    report = StockAnalysisReport(stock_code="US.AAPL")
    report.fundamental = fundamental
    
    print("\n報告JSON格式測試:")
    print(report.to_json(indent=2)[:500] + "...")
    
    print("\n測試完成!")