"""
市場情緒與供需分析模組 - Market Sentiment & Supply-Demand Analysis Module

提供全面的市場情緒分析功能：
- 牛熊市判別 (基於移動平均線)
- 情緒指標計算 (VIX風格、成交量異常、恐懼/貪婪指數)
- 供需分析 (資金流向、流動性評分)
- 板塊輪動追蹤

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class MarketSentiment(Enum):
    """市場情緒枚舉"""
    EXTREME_FEAR = "extreme_fear"      # 極度恐懼 (< 20)
    FEAR = "fear"                       # 恐懼 (20-40)
    NEUTRAL = "neutral"                 # 中性 (40-60)
    GREED = "greed"                     # 貪婪 (60-80)
    EXTREME_GREED = "extreme_greed"     # 極度貪婪 (> 80)


class MarketPhase(Enum):
    """市場階段枚舉"""
    ACCUMULATION = "accumulation"       # 積累期
    MARKUP = "markup"                   # 上升期
    DISTRIBUTION = "distribution"       # 派發期
    MARKDOWN = "markdown"               # 下降期


@dataclass
class SentimentIndicators:
    """情緒指標集合"""
    fear_greed_index: float = 50.0      # 恐懼/貪婪指數 (0-100)
    vix_style_index: float = 20.0       # VIX風格波動率指數
    volume_anomaly_score: float = 0.0   # 成交量異常評分
    breadth_indicator: float = 50.0     # 市場廣度指標
    momentum_score: float = 0.0         # 動能評分
    
    def get_dominant_sentiment(self) -> MarketSentiment:
        """獲取主導情緒"""
        if self.fear_greed_index < 20:
            return MarketSentiment.EXTREME_FEAR
        elif self.fear_greed_index < 40:
            return MarketSentiment.FEAR
        elif self.fear_greed_index < 60:
            return MarketSentiment.NEUTRAL
        elif self.fear_greed_index < 80:
            return MarketSentiment.GREED
        else:
            return MarketSentiment.EXTREME_GREED


@dataclass
class MoneyFlow:
    """資金流向數據"""
    net_inflow: float = 0.0             # 淨流入 (正數表示流入)
    inflow_volume: float = 0.0          # 流入量
    outflow_volume: float = 0.0         # 流出量
    flow_ratio: float = 1.0             # 流入/流出比率
    flow_strength: float = 0.0          # 資金流強度 (-1 到 1)
    
    def is_positive(self) -> bool:
        """是否為正向資金流"""
        return self.net_inflow > 0


@dataclass
class LiquidityMetrics:
    """流動性指標"""
    liquidity_score: float = 50.0       # 流動性評分 (0-100)
    bid_ask_spread: float = 0.0         # 買賣價差
    depth_score: float = 50.0           # 深度評分
    turnover_ratio: float = 0.0         # 換手率
    
    def is_liquid(self, threshold: float = 40.0) -> bool:
        """判斷是否具有足夠流動性"""
        return self.liquidity_score >= threshold


@dataclass
class SectorMomentum:
    """板塊動量數據"""
    sector_name: str = ""
    momentum: float = 0.0               # 動量值
    relative_strength: float = 1.0      # 相對強度
    volume_trend: float = 0.0           # 成交量趨勢
    rank: int = 0                       # 排名


@dataclass
class MarketSentimentAnalysis:
    """市場情緒分析結果"""
    sentiment: MarketSentiment
    phase: MarketPhase
    indicators: SentimentIndicators
    money_flow: MoneyFlow
    liquidity: LiquidityMetrics
    sector_momentum: List[SectorMomentum] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def is_contrarian_signal(self) -> bool:
        """是否為反向信號 (極度恐懼/貪婪時)"""
        return self.sentiment in [MarketSentiment.EXTREME_FEAR, MarketSentiment.EXTREME_GREED]
    
    def get_trading_bias(self) -> str:
        """獲取交易傾向"""
        if self.sentiment == MarketSentiment.EXTREME_FEAR:
            return "bullish_contrarian"
        elif self.sentiment == MarketSentiment.FEAR:
            return "cautious_bullish"
        elif self.sentiment == MarketSentiment.NEUTRAL:
            return "neutral"
        elif self.sentiment == MarketSentiment.GREED:
            return "cautious_bearish"
        else:
            return "bearish_contrarian"


class MarketSentimentAnalyzer:
    """
    市場情緒分析器
    
    整合多種情緒指標，提供全面的市場情緒評估
    """
    
    def __init__(
        self,
        lookback_period: int = 20,
        long_ma_period: int = 100,
        medium_ma_period: int = 50
    ):
        """
        初始化市場情緒分析器
        
        Args:
            lookback_period: 回看週期
            long_ma_period: 長期均線週期 (用於牛熊判斷)
            medium_ma_period: 中期均線週期
        """
        self.lookback_period = lookback_period
        self.long_ma_period = long_ma_period
        self.medium_ma_period = medium_ma_period
        
        # 歷史數據緩存
        self.price_history: pd.DataFrame = pd.DataFrame()
        self.sentiment_history: List[MarketSentimentAnalysis] = []
        self.sector_data: Dict[str, pd.DataFrame] = {}
    
    def analyze(
        self,
        df: pd.DataFrame,
        sector_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> MarketSentimentAnalysis:
        """
        執行全面的市場情緒分析
        
        Args:
            df: 價格數據DataFrame
            sector_data: 板塊數據字典 {sector_name: df}
            
        Returns:
            MarketSentimentAnalysis: 市場情緒分析結果
        """
        # 計算情緒指標
        indicators = self.calculate_sentiment_indicators(df)
        
        # 計算資金流向
        money_flow = self.analyze_money_flow(df)
        
        # 計算流動性
        liquidity = self.calculate_liquidity_score(df)
        
        # 檢測市場階段
        phase = self._detect_market_phase(df)
        
        # 分析板塊動量
        sector_momentum = []
        if sector_data:
            sector_momentum = self.track_sector_rotation(sector_data)
        
        analysis = MarketSentimentAnalysis(
            sentiment=indicators.get_dominant_sentiment(),
            phase=phase,
            indicators=indicators,
            money_flow=money_flow,
            liquidity=liquidity,
            sector_momentum=sector_momentum,
            timestamp=datetime.now()
        )
        
        self.sentiment_history.append(analysis)
        
        # 保持歷史記錄在合理範圍
        if len(self.sentiment_history) > 500:
            self.sentiment_history = self.sentiment_history[-250:]
        
        return analysis
    
    def detect_bull_bear(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        檢測牛熊市狀態
        
        基於 100日均線 和 50/100交叉 (黃金交叉/死亡交叉)
        
        Returns:
            牛熊市判斷結果字典
        """
        if len(df) < self.long_ma_period:
            return {'trend': 'unknown', 'signal': 'neutral', 'strength': 0.0}
        
        close = df['close']
        
        # 計算移動平均線
        ma_50 = close.ewm(span=self.medium_ma_period, adjust=False).mean()
        ma_100 = close.ewm(span=self.long_ma_period, adjust=False).mean()
        
        current_price = close.iloc[-1]
        current_ma50 = ma_50.iloc[-1]
        current_ma100 = ma_100.iloc[-1]
        
        # 判斷趨勢
        is_bullish = current_price > current_ma100
        golden_cross = current_ma50 > current_ma100
        
        # 計算趨勢強度
        price_vs_ma100 = (current_price - current_ma100) / current_ma100
        ma_spread = (current_ma50 - current_ma100) / current_ma100
        
        if is_bullish and golden_cross:
            trend = 'bull_market'
            signal = 'strong_bullish' if ma_spread > 0.05 else 'bullish'
            strength = min(abs(price_vs_ma100) * 10, 1.0)
        elif not is_bullish and not golden_cross:
            trend = 'bear_market'
            signal = 'strong_bearish' if ma_spread < -0.05 else 'bearish'
            strength = min(abs(price_vs_ma100) * 10, 1.0)
        else:
            trend = 'transition'
            signal = 'caution'
            strength = 0.3
        
        return {
            'trend': trend,
            'signal': signal,
            'strength': strength,
            'price_vs_ma100': price_vs_ma100,
            'ma_spread': ma_spread,
            'golden_cross': golden_cross,
            'is_bullish': is_bullish
        }
    
    def calculate_market_breadth(self, df: pd.DataFrame) -> float:
        """
        計算市場廣度指標 (騰落指標風格)
        
        基於價格相對於近期高低點的位置
        
        Returns:
            市場廣度指標 (0-100)
        """
        if len(df) < self.lookback_period:
            return 50.0
        
        close = df['close']
        
        # 計算近期新高/新低
        recent_high = close.rolling(window=self.lookback_period).max().iloc[-1]
        recent_low = close.rolling(window=self.lookback_period).min().iloc[-1]
        current = close.iloc[-1]
        
        if recent_high == recent_low:
            return 50.0
        
        # 計算在區間中的位置
        breadth = (current - recent_low) / (recent_high - recent_low) * 100
        
        return round(breadth, 2)
    
    def calculate_vix_style(self, df: pd.DataFrame, period: int = 20) -> float:
        """
        計算VIX風格波動率指數
        
        基於價格波動率的反向指標
        
        Args:
            df: 價格數據
            period: 計算週期
            
        Returns:
            VIX風格指數 (類似VIX的數值範圍)
        """
        if len(df) < period:
            return 20.0
        
        close = df['close']
        
        # 計算對數收益率
        log_returns = np.log(close / close.shift(1)).dropna()
        
        # 計算波動率 (年化)
        volatility = log_returns.rolling(window=period).std() * np.sqrt(252) * 100
        
        # VIX風格指數 (放大波動率影響)
        vix_style = volatility.iloc[-1] * 1.5
        
        return round(vix_style, 2)
    
    def detect_volume_anomaly(
        self,
        df: pd.DataFrame,
        threshold: float = 2.0
    ) -> Dict[str, Any]:
        """
        檢測成交量異常
        
        Args:
            df: 價格數據 (需包含volume列)
            threshold: 異常閾值倍數
            
        Returns:
            成交量異常檢測結果
        """
        if 'volume' not in df.columns or len(df) < self.lookback_period:
            return {'is_anomaly': False, 'score': 0.0, 'ratio': 1.0}
        
        volume = df['volume']
        
        # 計算平均成交量
        avg_volume = volume.rolling(window=self.lookback_period).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        
        if avg_volume == 0:
            return {'is_anomaly': False, 'score': 0.0, 'ratio': 1.0}
        
        volume_ratio = current_volume / avg_volume
        
        # 計算異常評分
        if volume_ratio > threshold:
            score = min((volume_ratio - threshold) / threshold * 50, 100)
            is_anomaly = True
        elif volume_ratio < 1 / threshold:
            score = min((1 / threshold - volume_ratio) / (1 / threshold) * 50, 100)
            is_anomaly = True
        else:
            score = 0.0
            is_anomaly = False
        
        return {
            'is_anomaly': is_anomaly,
            'score': round(score, 2),
            'ratio': round(volume_ratio, 2),
            'direction': 'high' if volume_ratio > 1 else 'low'
        }
    
    def calculate_fear_greed_index(self, df: pd.DataFrame) -> float:
        """
        計算恐懼/貪婪指數
        
        綜合多個指標計算市場情緒指數 (0-100)
        0 = 極度恐懼, 100 = 極度貪婪
        
        Returns:
            恐懼/貪婪指數
        """
        if len(df) < self.lookback_period:
            return 50.0
        
        close = df['close']
        
        # 1. 價格動量 (25%)
        price_change_1w = (close.iloc[-1] - close.iloc[-5]) / close.iloc[-5] if len(close) >= 5 else 0
        price_change_1m = (close.iloc[-1] - close.iloc[-20]) / close.iloc[-20] if len(close) >= 20 else 0
        momentum_score = np.clip((price_change_1w * 0.6 + price_change_1m * 0.4) * 500 + 50, 0, 100)
        
        # 2. 波動率 (25%)
        returns = close.pct_change().dropna()
        volatility = returns.rolling(window=self.lookback_period).std().iloc[-1] * np.sqrt(252)
        volatility_score = np.clip(100 - volatility * 200, 0, 100)
        
        # 3. 市場廣度 (25%)
        breadth = self.calculate_market_breadth(df)
        
        # 4. 成交量趨勢 (25%)
        volume_score = 50.0
        if 'volume' in df.columns:
            volume = df['volume']
            vol_ma = volume.rolling(window=self.lookback_period).mean()
            if vol_ma.iloc[-1] > 0:
                vol_ratio = volume.iloc[-1] / vol_ma.iloc[-1]
                volume_score = np.clip((vol_ratio - 0.5) * 50, 0, 100)
        
        # 綜合計算
        fear_greed = (
            momentum_score * 0.25 +
            volatility_score * 0.25 +
            breadth * 0.25 +
            volume_score * 0.25
        )
        
        return round(fear_greed, 2)
    
    def analyze_money_flow(self, df: pd.DataFrame) -> MoneyFlow:
        """
        分析資金流向
        
        基於價格和成交量計算資金流入流出
        
        Returns:
            MoneyFlow: 資金流向數據
        """
        if len(df) < 2 or 'volume' not in df.columns:
            return MoneyFlow()
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        # 計算典型價格
        typical_price = (high + low + close) / 3
        
        # 計算資金流
        money_flow = typical_price * volume
        
        # 計算正負資金流
        positive_flow = 0.0
        negative_flow = 0.0
        
        for i in range(1, min(len(df), self.lookback_period)):
            if typical_price.iloc[-i] > typical_price.iloc[-i-1]:
                positive_flow += money_flow.iloc[-i]
            else:
                negative_flow += money_flow.iloc[-i]
        
        # 計算資金流比率
        if negative_flow == 0:
            flow_ratio = 1.5 if positive_flow > 0 else 1.0
        else:
            flow_ratio = positive_flow / negative_flow
        
        # 計算資金流強度
        total_flow = positive_flow + negative_flow
        if total_flow > 0:
            flow_strength = (positive_flow - negative_flow) / total_flow
        else:
            flow_strength = 0.0
        
        return MoneyFlow(
            net_inflow=positive_flow - negative_flow,
            inflow_volume=positive_flow,
            outflow_volume=negative_flow,
            flow_ratio=round(flow_ratio, 2),
            flow_strength=round(flow_strength, 2)
        )
    
    def calculate_liquidity_score(self, df: pd.DataFrame) -> LiquidityMetrics:
        """
        計算流動性評分
        
        Returns:
            LiquidityMetrics: 流動性指標
        """
        if len(df) < self.lookback_period:
            return LiquidityMetrics()
        
        close = df['close']
        volume = df.get('volume', pd.Series(0, index=df.index))
        
        # 1. 計算換手率 (假設流通股本為固定值，用成交量/均量代替)
        avg_volume = volume.rolling(window=self.lookback_period).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        turnover_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # 2. 計算價格波動性 (反向指標)
        returns = close.pct_change().dropna()
        volatility = returns.rolling(window=self.lookback_period).std().iloc[-1]
        volatility_score = max(0, 100 - volatility * 1000)
        
        # 3. 計算深度評分 (基於成交量趨勢)
        volume_trend = 50.0
        if len(volume) >= self.lookback_period:
            vol_short = volume.iloc[-5:].mean()
            vol_long = volume.iloc[-self.lookback_period:].mean()
            if vol_long > 0:
                volume_trend = np.clip((vol_short / vol_long - 0.5) * 100, 0, 100)
        
        # 4. 綜合流動性評分
        liquidity_score = (
            min(turnover_ratio * 30, 40) +  # 換手率貢獻最多40分
            volatility_score * 0.3 +         # 波動性貢獻
            volume_trend * 0.3               # 成交量趨勢貢獻
        )
        
        return LiquidityMetrics(
            liquidity_score=round(liquidity_score, 2),
            bid_ask_spread=0.0,  # 需要實時報價數據
            depth_score=round(volume_trend, 2),
            turnover_ratio=round(turnover_ratio, 2)
        )
    
    def track_sector_rotation(
        self,
        sector_data: Dict[str, pd.DataFrame]
    ) -> List[SectorMomentum]:
        """
        追蹤板塊輪動
        
        Args:
            sector_data: 板塊數據字典 {sector_name: df}
            
        Returns:
            板塊動量列表 (按動量排序)
        """
        sectors = []
        
        for sector_name, df in sector_data.items():
            if len(df) < self.lookback_period:
                continue
            
            close = df['close']
            volume = df.get('volume', pd.Series(1, index=df.index))
            
            # 計算價格動量
            returns = (close.iloc[-1] - close.iloc[-self.lookback_period]) / close.iloc[-self.lookback_period]
            
            # 計算成交量趨勢
            vol_recent = volume.iloc[-5:].mean()
            vol_previous = volume.iloc[-10:-5].mean()
            volume_trend = (vol_recent - vol_previous) / vol_previous if vol_previous > 0 else 0
            
            sectors.append(SectorMomentum(
                sector_name=sector_name,
                momentum=round(returns * 100, 2),
                relative_strength=1.0,
                volume_trend=round(volume_trend * 100, 2),
                rank=0
            ))
        
        # 計算相對強度
        if len(sectors) > 1:
            avg_momentum = np.mean([s.momentum for s in sectors])
            for sector in sectors:
                sector.relative_strength = round(sector.momentum / avg_momentum if avg_momentum != 0 else 1.0, 2)
        
        # 排序並分配排名
        sectors.sort(key=lambda x: x.momentum, reverse=True)
        for i, sector in enumerate(sectors):
            sector.rank = i + 1
        
        return sectors
    
    def detect_sector_leaders(
        self,
        sector_data: Dict[str, pd.DataFrame],
        top_n: int = 3
    ) -> List[SectorMomentum]:
        """
        識別領漲板塊
        
        Args:
            sector_data: 板塊數據字典
            top_n: 返回前N個領漲板塊
            
        Returns:
            領漲板塊列表
        """
        sectors = self.track_sector_rotation(sector_data)
        return sectors[:top_n]
    
    def calculate_sentiment_indicators(self, df: pd.DataFrame) -> SentimentIndicators:
        """
        計算所有情緒指標
        
        Returns:
            SentimentIndicators: 情緒指標集合
        """
        fear_greed = self.calculate_fear_greed_index(df)
        vix_style = self.calculate_vix_style(df)
        volume_anomaly = self.detect_volume_anomaly(df)
        breadth = self.calculate_market_breadth(df)
        
        # 計算動能評分
        close = df['close']
        if len(close) >= 10:
            momentum = (close.iloc[-1] - close.iloc[-10]) / close.iloc[-10] * 100
        else:
            momentum = 0.0
        
        return SentimentIndicators(
            fear_greed_index=fear_greed,
            vix_style_index=vix_style,
            volume_anomaly_score=volume_anomaly.get('score', 0.0),
            breadth_indicator=breadth,
            momentum_score=round(momentum, 2)
        )
    
    def _detect_market_phase(self, df: pd.DataFrame) -> MarketPhase:
        """
        檢測市場階段 (積累/上升/派發/下降)
        
        基於價格和成交量的組合分析
        """
        if len(df) < self.lookback_period:
            return MarketPhase.ACCUMULATION
        
        close = df['close']
        volume = df.get('volume', pd.Series(0, index=df.index))
        
        # 計算趨勢
        price_change = (close.iloc[-1] - close.iloc[-self.lookback_period]) / close.iloc[-self.lookback_period]
        
        # 計算成交量趨勢
        vol_recent = volume.iloc[-5:].mean() if len(volume) >= 5 else volume.mean()
        vol_long = volume.iloc[-self.lookback_period:].mean()
        volume_trend = vol_recent / vol_long if vol_long > 0 else 1.0
        
        # 判斷階段
        if price_change > 0.05 and volume_trend > 1.1:
            return MarketPhase.MARKUP
        elif price_change > 0.05 and volume_trend < 0.9:
            return MarketPhase.DISTRIBUTION
        elif price_change < -0.05:
            return MarketPhase.MARKDOWN
        else:
            return MarketPhase.ACCUMULATION
    
    def get_sentiment_summary(self) -> Dict[str, Any]:
        """
        獲取情緒分析摘要
        
        Returns:
            情緒摘要字典
        """
        if not self.sentiment_history:
            return {'status': 'no_data'}
        
        latest = self.sentiment_history[-1]
        
        return {
            'current_sentiment': latest.sentiment.value,
            'market_phase': latest.phase.value,
            'fear_greed_index': latest.indicators.fear_greed_index,
            'vix_style': latest.indicators.vix_style_index,
            'money_flow_direction': 'inflow' if latest.money_flow.is_positive() else 'outflow',
            'liquidity_status': 'good' if latest.liquidity.is_liquid() else 'poor',
            'trading_bias': latest.get_trading_bias(),
            'is_contrarian_signal': latest.is_contrarian_signal()
        }


# 便捷函數
def calculate_fear_greed_index(df: pd.DataFrame) -> float:
    """計算恐懼/貪婪指數"""
    analyzer = MarketSentimentAnalyzer()
    return analyzer.calculate_fear_greed_index(df)


def detect_volume_anomaly(df: pd.DataFrame, threshold: float = 2.0) -> Dict[str, Any]:
    """檢測成交量異常"""
    analyzer = MarketSentimentAnalyzer()
    return analyzer.detect_volume_anomaly(df, threshold)


def analyze_market_sentiment(df: pd.DataFrame) -> MarketSentimentAnalysis:
    """分析市場情緒"""
    analyzer = MarketSentimentAnalyzer()
    return analyzer.analyze(df)
