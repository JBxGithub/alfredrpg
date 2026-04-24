"""
MTF (Multi-Timeframe) Analyzer Module with MACD-V Integration
多時間框架分析器模組 (MACD-V整合版)

提供多時間框架（月線/週線/日線）的技術分析，整合MACD-V和背離檢測，
形成三維分析框架：
1. MTF一致性評分
2. MACD-V成交量加權信號
3. 背離檢測預警

權重分配:
- 月線 (Monthly): 40% - 長期趨勢判斷
- 週線 (Weekly): 35% - 中期趨勢判斷
- 日線 (Daily): 25% - 短期趨勢判斷

整合評分邏輯:
- 三維共振看多: 100分 (強烈買入)
- MTF看多 + MACD-V看多: 85分 (買入)
- MTF看多 + 背離預警: 75分 (謹慎買入)
- 趨勢不明確: 50分 (觀望)
- 反向信號: 0-25分 (賣出/減倉)
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

import pandas as pd
import numpy as np

# 可選依賴
try:
    from src.utils.logger import get_logger
    from src.indicators.macdv import MACDVCalculator, MACDVResult, TimeframeMACDV, MACDVSignal
    from src.analysis.divergence_detector import DivergenceDetector, DivergenceAnalysis, DivergenceType
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    get_logger = lambda name: logging.getLogger(name)
    MACDVCalculator = None
    MACDVResult = None
    TimeframeMACDV = None
    MACDVSignal = None
    DivergenceDetector = None
    DivergenceAnalysis = None
    DivergenceType = None

logger = get_logger(__name__)


class TrendDirection(Enum):
    """趨勢方向"""
    BULL = "bull"      # 看多（與一致性評分模組兼容）
    BEAR = "bear"      # 看空（與一致性評分模組兼容）
    NEUTRAL = "neutral"  # 中性（與一致性評分模組兼容）
    BULLISH = 1      # 看多（向後兼容）
    BEARISH = -1     # 看空（向後兼容）


@dataclass
class TimeframeAnalysis:
    """單一時間框架分析結果"""
    timeframe: str           # 時間框架名稱 (monthly/weekly/daily)
    trend: TrendDirection    # 趨勢方向
    trend_score: float       # 趨勢強度分數 (0-100)
    ema_alignment: bool      # EMA排列是否多頭/空頭
    price_vs_ema: float      # 價格相對EMA的位置
    macd_signal: float       # MACD信號強度
    rsi_value: float         # RSI值
    support_resistance: Dict[str, float] = field(default_factory=dict)  # 支撐阻力位
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeframe": self.timeframe,
            "trend": self.trend.name,
            "trend_score": self.trend_score,
            "ema_alignment": self.ema_alignment,
            "price_vs_ema": self.price_vs_ema,
            "macd_signal": self.macd_signal,
            "rsi_value": self.rsi_value,
            "support_resistance": self.support_resistance
        }


@dataclass
class MTFConsistencyScore:
    """MTF一致性評分結果"""
    overall_score: float                    # 總體一致性評分 (0-100)
    weighted_score: float                   # 加權評分
    monthly_score: float                    # 月線評分
    weekly_score: float                     # 週線評分
    daily_score: float                      # 日線評分
    monthly_trend: TrendDirection           # 月線趨勢
    weekly_trend: TrendDirection            # 週線趨勢
    daily_trend: TrendDirection             # 日線趨勢
    consistency_level: str                  # 一致性等級
    recommendation: str                     # 交易建議
    details: Dict[str, Any] = field(default_factory=dict)  # 詳細資訊
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "weighted_score": self.weighted_score,
            "monthly_score": self.monthly_score,
            "weekly_score": self.weekly_score,
            "daily_score": self.daily_score,
            "monthly_trend": self.monthly_trend.name,
            "weekly_trend": self.weekly_trend.name,
            "daily_trend": self.daily_trend.name,
            "consistency_level": self.consistency_level,
            "recommendation": self.recommendation,
            "details": self.details
        }


@dataclass
class IntegratedMTFScore:
    """整合MTF評分結果 (包含MACD-V和背離檢測)"""
    # 基礎MTF評分
    mtf_score: MTFConsistencyScore          # MTF一致性評分
    
    # MACD-V評分
    macdv_score: float                      # MACD-V綜合評分 (0-100)
    macdv_monthly: Optional[Dict] = None    # 月線MACD-V
    macdv_weekly: Optional[Dict] = None     # 週線MACD-V
    macdv_daily: Optional[Dict] = None      # 日線MACD-V
    
    # 背離檢測
    divergence_analysis: Optional[DivergenceAnalysis] = None  # 背離分析
    has_divergence: bool = False            # 是否存在背離
    divergence_signal: str = "none"         # 背離信號類型
    
    # 整合評分
    integrated_score: float = 0.0           # 整合評分 (0-100)
    final_recommendation: str = ""          # 最終建議
    confidence: float = 0.0                 # 置信度
    
    # 三維分析結果
    dimension_scores: Dict[str, float] = field(default_factory=dict)  # 各維度評分
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mtf_score": self.mtf_score.to_dict(),
            "macdv_score": self.macdv_score,
            "macdv_monthly": self.macdv_monthly,
            "macdv_weekly": self.macdv_weekly,
            "macdv_daily": self.macdv_daily,
            "divergence": {
                "has_divergence": self.has_divergence,
                "signal": self.divergence_signal,
                "analysis": self.divergence_analysis.to_dict() if self.divergence_analysis else None
            },
            "integrated_score": self.integrated_score,
            "final_recommendation": self.final_recommendation,
            "confidence": self.confidence,
            "dimension_scores": self.dimension_scores
        }


class MTFAnalyzer:
    """
    多時間框架分析器
    
    分析月線、週線、日線三個時間框架的技術指標，
    計算一致性評分，用於過濾交易信號。
    
    權重配置:
    - monthly_weight: 月線權重 (默認 0.40)
    - weekly_weight: 週線權重 (默認 0.35)
    - daily_weight: 日線權重 (默認 0.25)
    """
    
    # 權重配置
    WEIGHTS = {
        'monthly': 0.40,   # 月線 40% - 長期趨勢最重要
        'weekly': 0.35,    # 週線 35% - 中期趨勢次要
        'daily': 0.25      # 日線 25% - 短期趨勢參考
    }
    
    # EMA 週期配置
    EMA_PERIODS = {
        'monthly': [6, 12, 24],    # 月線: 6月、12月、24月EMA
        'weekly': [10, 20, 50],    # 週線: 10週、20週、50週EMA
        'daily': [20, 50, 200]     # 日線: 20日、50日、200日EMA
    }
    
    def __init__(self, 
                 monthly_weight: float = 0.40,
                 weekly_weight: float = 0.35,
                 daily_weight: float = 0.25):
        """
        初始化MTF分析器
        
        Args:
            monthly_weight: 月線權重 (默認 0.40)
            weekly_weight: 週線權重 (默認 0.35)
            daily_weight: 日線權重 (默認 0.25)
        """
        # 驗證權重總和為1
        total_weight = monthly_weight + weekly_weight + daily_weight
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"權重總和必須等於1.0，當前為 {total_weight}")
        
        self.WEIGHTS = {
            'monthly': monthly_weight,
            'weekly': weekly_weight,
            'daily': daily_weight
        }
        
        logger.info(f"MTF分析器已初始化 - 權重: 月線{monthly_weight:.0%}/週線{weekly_weight:.0%}/日線{daily_weight:.0%}")
    
    def analyze(self,
                monthly_data: Optional[pd.DataFrame] = None,
                weekly_data: Optional[pd.DataFrame] = None,
                daily_data: Optional[pd.DataFrame] = None) -> MTFConsistencyScore:
        """
        執行多時間框架分析
        
        Args:
            monthly_data: 月線K線數據 DataFrame with columns: ['open', 'high', 'low', 'close', 'volume']
            weekly_data: 週線K線數據 DataFrame with columns: ['open', 'high', 'low', 'close', 'volume']
            daily_data: 日線K線數據 DataFrame with columns: ['open', 'high', 'low', 'close', 'volume']
            
        Returns:
            MTFConsistencyScore: MTF一致性評分結果
        """
        logger.info("開始MTF多時間框架分析...")
        
        # 分析各時間框架
        monthly_analysis = self._analyze_timeframe(monthly_data, 'monthly') if monthly_data is not None else None
        weekly_analysis = self._analyze_timeframe(weekly_data, 'weekly') if weekly_data is not None else None
        daily_analysis = self._analyze_timeframe(daily_data, 'daily') if daily_data is not None else None
        
        # 計算一致性評分
        score = self._calculate_consistency_score(
            monthly_analysis, weekly_analysis, daily_analysis
        )
        
        logger.info(f"MTF分析完成 - 一致性評分: {score.overall_score:.1f}/100, 建議: {score.recommendation}")
        
        return score
    
    def _analyze_timeframe(self, df: pd.DataFrame, timeframe: str) -> TimeframeAnalysis:
        """
        分析單一時間框架
        
        Args:
            df: K線數據
            timeframe: 時間框架名稱
            
        Returns:
            TimeframeAnalysis: 分析結果
        """
        if df is None or df.empty:
            raise ValueError(f"{timeframe}數據為空")
        
        # 確保數據格式正確
        df = df.copy()
        for col in ['open', 'high', 'low', 'close']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 計算EMA
        ema_periods = self.EMA_PERIODS[timeframe]
        for period in ema_periods:
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        
        # 獲取最新數據
        latest = df.iloc[-1]
        current_price = latest['close']
        
        # 1. 判斷EMA排列 (多頭/空頭排列)
        ema_values = [latest[f'ema_{p}'] for p in ema_periods]
        ema_bullish = all(ema_values[i] > ema_values[i+1] for i in range(len(ema_values)-1))
        ema_bearish = all(ema_values[i] < ema_values[i+1] for i in range(len(ema_values)-1))
        
        # 2. 計算價格相對EMA位置
        ema_mid = latest[f'ema_{ema_periods[1]}']  # 中間週期EMA
        price_vs_ema = (current_price / ema_mid - 1) * 100
        
        # 3. 計算MACD
        macd, macd_signal = self._calculate_macd(df['close'])
        macd_histogram = macd - macd_signal
        
        # 4. 計算RSI
        rsi = self._calculate_rsi(df['close'])
        
        # 5. 判斷趨勢方向
        trend = self._determine_trend(
            current_price, ema_values, ema_bullish, ema_bearish, 
            macd, macd_signal, rsi
        )
        
        # 6. 計算趨勢強度分數
        trend_score = self._calculate_trend_score(
            trend, ema_bullish, ema_bearish, price_vs_ema, 
            macd_histogram, rsi
        )
        
        # 7. 計算支撐阻力位
        support_resistance = self._calculate_support_resistance(df)
        
        analysis = TimeframeAnalysis(
            timeframe=timeframe,
            trend=trend,
            trend_score=trend_score,
            ema_alignment=ema_bullish if trend == TrendDirection.BULLISH else ema_bearish,
            price_vs_ema=price_vs_ema,
            macd_signal=macd_histogram,
            rsi_value=rsi,
            support_resistance=support_resistance
        )
        
        return analysis
    
    def _determine_trend(self, current_price: float, ema_values: List[float],
                         ema_bullish: bool, ema_bearish: bool,
                         macd: float, macd_signal: float, rsi: float) -> TrendDirection:
        """
        判斷趨勢方向
        
        綜合考慮:
        - EMA排列
        - 價格與EMA關係
        - MACD信號
        - RSI值
        """
        bullish_signals = 0
        bearish_signals = 0
        
        # EMA排列信號
        if ema_bullish:
            bullish_signals += 2
        elif ema_bearish:
            bearish_signals += 2
        
        # 價格與EMA關係
        if current_price > ema_values[1]:  # 價格在中期EMA之上
            bullish_signals += 1
        elif current_price < ema_values[1]:
            bearish_signals += 1
        
        # MACD信號
        if macd > macd_signal and macd > 0:
            bullish_signals += 2
        elif macd < macd_signal and macd < 0:
            bearish_signals += 2
        elif macd > macd_signal:
            bullish_signals += 1
        elif macd < macd_signal:
            bearish_signals += 1
        
        # RSI信號
        if rsi > 60:
            bullish_signals += 1
        elif rsi < 40:
            bearish_signals += 1
        
        # 判斷最終趨勢
        if bullish_signals >= 4 and bullish_signals > bearish_signals + 1:
            return TrendDirection.BULLISH
        elif bearish_signals >= 4 and bearish_signals > bullish_signals + 1:
            return TrendDirection.BEARISH
        else:
            return TrendDirection.NEUTRAL
    
    def _calculate_trend_score(self, trend: TrendDirection, ema_bullish: bool,
                               ema_bearish: bool, price_vs_ema: float,
                               macd_histogram: float, rsi: float) -> float:
        """
        計算趨勢強度分數 (0-100)
        
        基於多個技術指標計算趨勢的強度
        """
        score = 50.0  # 基礎分數
        
        if trend == TrendDirection.BULLISH:
            score = 70.0
            # EMA多頭排列加分
            if ema_bullish:
                score += 15
            # 價格遠離EMA加分
            if price_vs_ema > 5:
                score += 5
            # MACD柱狀圖向上加分
            if macd_histogram > 0:
                score += 5
            # RSI在強勢區加分
            if 50 < rsi < 70:
                score += 5
        
        elif trend == TrendDirection.BEARISH:
            score = 30.0
            # EMA空頭排列減分
            if ema_bearish:
                score -= 15
            # 價格遠離EMA減分
            if price_vs_ema < -5:
                score -= 5
            # MACD柱狀圖向下減分
            if macd_histogram < 0:
                score -= 5
            # RSI在弱勢區減分
            if 30 < rsi < 50:
                score -= 5
        
        else:  # NEUTRAL
            score = 50.0
            # 根據指標微調
            if ema_bullish:
                score += 10
            elif ema_bearish:
                score -= 10
        
        # 確保分數在0-100範圍內
        return max(0.0, min(100.0, score))
    
    def _calculate_consistency_score(self,
                                     monthly: Optional[TimeframeAnalysis],
                                     weekly: Optional[TimeframeAnalysis],
                                     daily: Optional[TimeframeAnalysis]) -> MTFConsistencyScore:
        """
        計算一致性評分 (修正版)
        
        修正內容:
        1. 修正權重配置: 月線40% > 週線35% > 日線25%
        2. 修正一致性獎懲邏輯: 排除NEUTRAL趨勢的一致性獎勵
        3. 修正週線衝突處理: 週線與日線相反時嚴重減分
        4. 修正逆月線大勢處理: 一票否決，評分大幅減分
        
        核心邏輯:
        1. 計算每個時間框架的加權分數 (新權重)
        2. 判斷趨勢一致性 (排除NEUTRAL)
        3. 應用一致性獎懲機制
        4. 給出最終評分和建議
        """
        # 獲取各時間框架的趨勢和分數
        monthly_trend = monthly.trend if monthly else TrendDirection.NEUTRAL
        weekly_trend = weekly.trend if weekly else TrendDirection.NEUTRAL
        daily_trend = daily.trend if daily else TrendDirection.NEUTRAL
        
        monthly_score = monthly.trend_score if monthly else 50.0
        weekly_score = weekly.trend_score if weekly else 50.0
        daily_score = daily.trend_score if daily else 50.0
        
        # 計算加權分數 (使用修正後的權重)
        weighted_score = (
            monthly_score * self.WEIGHTS['monthly'] +
            weekly_score * self.WEIGHTS['weekly'] +
            daily_score * self.WEIGHTS['daily']
        )
        
        # 計算一致性評分 (0-100)
        # 基於三個時間框架趨勢的一致性
        trends = [monthly_trend, weekly_trend, daily_trend]
        bullish_count = sum(1 for t in trends if t == TrendDirection.BULLISH)
        bearish_count = sum(1 for t in trends if t == TrendDirection.BEARISH)
        neutral_count = sum(1 for t in trends if t == TrendDirection.NEUTRAL)
        
        # 檢查是否所有趨勢都明確 (非NEUTRAL)
        all_defined = all(t != TrendDirection.NEUTRAL for t in trends)
        
        # 修正：一致性獎懲機制 (排除NEUTRAL情況的獎勵)
        consistency_multiplier = 1.0
        
        if all_defined:
            # 所有時間框架都有明確趨勢
            if monthly_trend == weekly_trend == daily_trend:
                # 三線完全一致 - 強烈獎勵
                consistency_multiplier = 1.25
                if monthly_trend == TrendDirection.BULLISH:
                    consistency_score = 100.0
                    level = "強烈一致看多"
                    recommendation = "強烈買入 (Strong Buy)"
                else:  # BEARISH
                    consistency_score = 0.0
                    level = "強烈一致看空"
                    recommendation = "強烈賣出 (Strong Sell)"
            elif monthly_trend == daily_trend and weekly_trend != monthly_trend:
                # 日線月線一致，但週線不一致 - 輕微減分
                consistency_multiplier = 0.85
                if monthly_trend == TrendDirection.BULLISH:
                    consistency_score = 65.0
                    level = "偏多但週線分歧"
                else:  # BEARISH
                    consistency_score = 35.0
                    level = "偏空但週線分歧"
                recommendation = "觀望 (Neutral)"
            elif monthly_trend != daily_trend:
                # 逆月線大勢 - 嚴重減分 (一票否決機制)
                consistency_multiplier = 0.3
                if monthly_trend == TrendDirection.BULLISH:
                    # 月線看多，日線看空 - 偏空但逆大勢
                    consistency_score = 30.0
                else:
                    # 月線看空，日線看多 - 偏多但逆大勢
                    consistency_score = 70.0
                level = "逆月線大勢"
                recommendation = "觀望 (Neutral) - 逆大勢風險高"
            else:
                # 其他不一致情況
                consistency_multiplier = 0.9
                consistency_score = 50.0
                level = "趨勢部分一致"
                recommendation = "觀望 (Neutral)"
        else:
            # 有時間框架為NEUTRAL
            if neutral_count == 3:
                # 三個都中性 - 無獎勵無懲罰
                consistency_multiplier = 0.8
                consistency_score = 50.0
                level = "無明確趨勢"
                recommendation = "觀望 (Neutral)"
            elif monthly_trend == daily_trend and monthly_trend != TrendDirection.NEUTRAL:
                # 僅日線月線一致 (週線NEUTRAL) - 微弱加分
                consistency_multiplier = 1.05
                if monthly_trend == TrendDirection.BULLISH:
                    consistency_score = 60.0
                    level = "輕度偏多"
                else:  # BEARISH
                    consistency_score = 40.0
                    level = "輕度偏空"
                recommendation = "觀望 (Neutral)"
            else:
                # 趨勢不明確 - 減分
                consistency_multiplier = 0.75
                consistency_score = 45.0
                level = "趨勢不明確"
                recommendation = "觀望 (Neutral)"
        
        # 應用一致性乘數到加權分數
        adjusted_weighted_score = weighted_score * consistency_multiplier
        
        # 最終評分 = 調整後加權分數和一致性評分的加權平均
        # 調整後加權分數佔60%，一致性評分佔40%
        final_score = adjusted_weighted_score * 0.6 + consistency_score * 0.4
        
        # 確保分數在0-100範圍內
        final_score = max(0.0, min(100.0, final_score))
        
        # 根據最終評分調整建議 (如果還沒有明確建議)
        if recommendation == "觀望 (Neutral)" or "觀望" in recommendation:
            if final_score >= 75:
                recommendation = "買入 (Buy)"
                level = "一致看多"
            elif final_score <= 25:
                recommendation = "賣出 (Sell)"
                level = "一致看空"
        
        # 構建詳細資訊
        details = {
            "trend_alignment": {
                "monthly": monthly_trend.name,
                "weekly": weekly_trend.name,
                "daily": daily_trend.name,
                "bullish_count": bullish_count,
                "bearish_count": bearish_count,
                "neutral_count": neutral_count,
                "all_defined": all_defined
            },
            "weights_applied": self.WEIGHTS,
            "score_breakdown": {
                "base_weighted_score": weighted_score,
                "consistency_multiplier": consistency_multiplier,
                "adjusted_weighted_score": adjusted_weighted_score,
                "consistency_component": consistency_score,
                "final_score": final_score
            },
            "consistency_rules_applied": {
                "all_aligned_bonus": all_defined and monthly_trend == weekly_trend == daily_trend,
                "weekly_divergence_penalty": all_defined and monthly_trend == daily_trend and weekly_trend != monthly_trend,
                "against_monthly_penalty": monthly_trend != daily_trend and monthly_trend != TrendDirection.NEUTRAL,
                "neutral_present": not all_defined
            }
        }
        
        # 添加各時間框架詳細分析
        if monthly:
            details["monthly_analysis"] = monthly.to_dict()
        if weekly:
            details["weekly_analysis"] = weekly.to_dict()
        if daily:
            details["daily_analysis"] = daily.to_dict()
        
        return MTFConsistencyScore(
            overall_score=final_score,
            weighted_score=adjusted_weighted_score,
            monthly_score=monthly_score,
            weekly_score=weekly_score,
            daily_score=daily_score,
            monthly_trend=monthly_trend,
            weekly_trend=weekly_trend,
            daily_trend=daily_trend,
            consistency_level=level,
            recommendation=recommendation,
            details=details
        )
    
    def _calculate_macd(self, prices: pd.Series, 
                        fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float]:
        """計算MACD指標"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal_line = macd.ewm(span=signal, adjust=False).mean()
        return float(macd.iloc[-1]), float(macd_signal_line.iloc[-1])
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """計算RSI指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty else 50.0
    
    def _calculate_support_resistance(self, df: pd.DataFrame) -> Dict[str, float]:
        """計算支撐阻力位"""
        if len(df) < 20:
            return {}
        
        recent = df.tail(20)
        
        # 簡單支撐阻力計算 (最近20期的最高/最低)
        resistance = recent['high'].max()
        support = recent['low'].min()
        
        # 樞紐點
        pivot = (recent['high'].iloc[-1] + recent['low'].iloc[-1] + recent['close'].iloc[-1]) / 3
        
        return {
            "resistance": float(resistance),
            "support": float(support),
            "pivot": float(pivot)
        }
    
    def _calculate_consistency_score_v2(self,
                                        monthly: Optional[TimeframeAnalysis],
                                        weekly: Optional[TimeframeAnalysis],
                                        daily: Optional[TimeframeAnalysis]) -> Dict[str, Any]:
        """
        計算多時間框架一致性評分 v2（權重感知算法）
        
        評分邏輯：
        1. 基礎加權分數（0-100）- 月線40%/週線35%/日線25%
        2. 趨勢方向一致性獎懲（-30% ~ +25%）
        3. 強度一致性獎懲（-15% ~ +15%）
        4. 最終評分（0-100）
        
        Args:
            monthly: 月線分析結果
            weekly: 週線分析結果
            daily: 日線分析結果
            
        Returns:
            Dict: 包含 overall_score, weighted_score, multipliers, details
        """
        
        # 轉換趨勢方向為新枚舉格式
        def convert_trend(trend):
            if trend == TrendDirection.BULLISH:
                return TrendDirection.BULL
            elif trend == TrendDirection.BEARISH:
                return TrendDirection.BEAR
            return TrendDirection.NEUTRAL
        
        # 獲取趨勢強度（使用 trend_score）
        monthly_strength = monthly.trend_score if monthly else 50.0
        weekly_strength = weekly.trend_score if weekly else 50.0
        daily_strength = daily.trend_score if daily else 50.0
        
        # 獲取ADX值（從 support_resistance 或估計）
        monthly_adx = monthly.support_resistance.get('adx', monthly_strength * 0.35) if monthly else 20.0
        weekly_adx = weekly.support_resistance.get('adx', weekly_strength * 0.35) if weekly else 20.0
        daily_adx = daily.support_resistance.get('adx', daily_strength * 0.35) if daily else 20.0
        
        # ========== 步驟1: 基礎加權分數 ==========
        # 權重配置：月線40%/週線35%/日線25%
        base_score = (
            daily_strength * 0.25 +
            weekly_strength * 0.35 +
            monthly_strength * 0.40
        )
        
        # ========== 步驟2: 趨勢方向一致性評估 ==========
        monthly_trend = convert_trend(monthly.trend) if monthly else TrendDirection.NEUTRAL
        weekly_trend = convert_trend(weekly.trend) if weekly else TrendDirection.NEUTRAL
        daily_trend = convert_trend(daily.trend) if daily else TrendDirection.NEUTRAL
        
        trend_consistency_multiplier = self._calculate_trend_consistency_v2(
            daily_trend, weekly_trend, monthly_trend
        )
        
        # ========== 步驟3: 強度一致性評估 ==========
        strength_consistency_multiplier = self._calculate_strength_consistency_v2(
            daily_adx, weekly_adx, monthly_adx
        )
        
        # ========== 步驟4: 計算最終評分 ==========
        final_score = base_score * trend_consistency_multiplier * strength_consistency_multiplier
        final_score = round(min(100, max(0, final_score)), 2)
        
        return {
            'overall_score': final_score,
            'base_score': base_score,
            'weighted_score': final_score,  # 向後兼容
            'trend_consistency_multiplier': trend_consistency_multiplier,
            'strength_consistency_multiplier': strength_consistency_multiplier,
            'monthly_score': monthly_strength,
            'weekly_score': weekly_strength,
            'daily_score': daily_strength,
            'monthly_trend': monthly_trend,
            'weekly_trend': weekly_trend,
            'daily_trend': daily_trend,
            'details': {
                'base_score': base_score,
                'trend_multiplier': trend_consistency_multiplier,
                'strength_multiplier': strength_consistency_multiplier,
                'monthly_adx': monthly_adx,
                'weekly_adx': weekly_adx,
                'daily_adx': daily_adx
            }
        }
    
    def _calculate_trend_consistency_v2(self,
                                        daily_trend: TrendDirection,
                                        weekly_trend: TrendDirection,
                                        monthly_trend: TrendDirection) -> float:
        """
        計算趨勢方向一致性乘數 v2
        
        一致性等級：
        - 三線同向（日=週=月）：+25% (x1.25)
        - 日週一致，月線中性：+15% (x1.15)
        - 日月一致，週線中性：+10% (x1.10)
        - 週月一致，日線反向：-20% (x0.80) - 逆日線
        - 日週一致，逆月線：-30% (x0.70) - 嚴重警告
        - 三線不一致：-25% (x0.75)
        """
        
        # 三線完全一致
        if daily_trend == weekly_trend == monthly_trend:
            if daily_trend != TrendDirection.NEUTRAL:
                return 1.25  # 強趨勢一致性
            else:
                return 0.90  # 三線皆中性，減分
        
        # 檢查是否逆月線（最嚴重錯誤）
        if monthly_trend != TrendDirection.NEUTRAL:
            if daily_trend != monthly_trend:
                if weekly_trend == daily_trend:
                    return 0.70  # 日週一致但逆月線 - 嚴重警告
                else:
                    return 0.75  # 僅日線逆月線
        
        # 檢查日週一致性
        if daily_trend == weekly_trend and daily_trend != TrendDirection.NEUTRAL:
            if monthly_trend == TrendDirection.NEUTRAL:
                return 1.15  # 日週一致，月線中性
            return 1.10  # 日週一致，月線不同向
        
        # 檢查日月一致性
        if daily_trend == monthly_trend and daily_trend != TrendDirection.NEUTRAL:
            return 1.10  # 日月一致
        
        # 檢查週月一致性（日線反向）
        if weekly_trend == monthly_trend and weekly_trend != TrendDirection.NEUTRAL:
            if daily_trend != weekly_trend:
                return 0.80  # 週月一致但日線反向 - 逆日線信號
        
        # 其他不一致情況
        return 0.85
    
    def _calculate_strength_consistency_v2(self,
                                           daily_adx: float,
                                           weekly_adx: float,
                                           monthly_adx: float) -> float:
        """
        計算趨勢強度一致性乘數 v2
        
        評估ADX在各時間框架的一致性：
        - 強度遞減合理（月>週>日）：+15% (x1.15)
        - 強度遞增（日>週>月）：+5% (x1.05) - 趨勢加速
        - 強度差異過大（>30點）：-15% (x0.85)
        - 週線強度不足（<20）：-10% (x0.90)
        - 月線強度不足（<15）：-15% (x0.85)
        """
        
        multiplier = 1.0
        
        # 檢查強度遞減模式（正常情況：長期>中期>短期）
        if monthly_adx >= weekly_adx >= daily_adx:
            # 強度合理遞減
            if monthly_adx - daily_adx < 20:
                multiplier += 0.15  # 強度接近，趨勢穩定
            else:
                multiplier += 0.10  # 強度差異較大但仍合理
        
        # 檢查強度遞增模式（趨勢加速）
        elif daily_adx > weekly_adx > monthly_adx:
            multiplier += 0.05  # 趨勢正在加速形成
        
        # 檢查強度差異過大
        adx_values = [daily_adx, weekly_adx, monthly_adx]
        adx_range = max(adx_values) - min(adx_values)
        if adx_range > 30:
            multiplier -= 0.15  # 強度差異過大，趨勢不穩定
        elif adx_range > 20:
            multiplier -= 0.05  # 中度差異
        
        # 檢查關鍵時間框架強度
        if weekly_adx < 20:
            multiplier -= 0.10  # 週線趨勢不明確
        
        if monthly_adx < 15:
            multiplier -= 0.15  # 月線無明確趨勢
        elif monthly_adx < 20:
            multiplier -= 0.05  # 月線趨勢較弱
        
        return max(0.70, min(1.20, multiplier))
    
    def analyze_integrated(self,
                           monthly_data: Optional[pd.DataFrame] = None,
                           weekly_data: Optional[pd.DataFrame] = None,
                           daily_data: Optional[pd.DataFrame] = None,
                           enable_macdv: bool = True,
                           enable_divergence: bool = True) -> IntegratedMTFScore:
        """
        執行整合MTF分析（包含MACD-V和背離檢測）
        
        三維分析框架：
        1. MTF一致性評分 (40%)
        2. MACD-V成交量加權信號 (35%)
        3. 背離檢測預警 (25%)
        
        Args:
            monthly_data: 月線數據
            weekly_data: 週線數據
            daily_data: 日線數據
            enable_macdv: 是否啟用MACD-V分析
            enable_divergence: 是否啟用背離檢測
            
        Returns:
            IntegratedMTFScore: 整合評分結果
        """
        logger.info("開始整合MTF分析 (MACD-V + 背離檢測)...")
        
        # 1. 基礎MTF分析
        mtf_score = self.analyze(monthly_data, weekly_data, daily_data)
        
        # 2. MACD-V分析
        macdv_results = {}
        macdv_score = 50.0
        if enable_macdv and MACDVCalculator is not None:
            try:
                macdv_calc = MACDVCalculator()
                macdv_results = macdv_calc.calculate_multi_timeframe(
                    monthly_data, weekly_data, daily_data
                )
                macdv_score = self._calculate_macdv_score(macdv_results)
                logger.info(f"MACD-V分析完成 - 綜合評分: {macdv_score:.1f}")
            except Exception as e:
                logger.warning(f"MACD-V分析失敗: {e}")
        
        # 3. 背離檢測
        divergence_analysis = None
        has_divergence = False
        divergence_signal = "none"
        if enable_divergence and DivergenceDetector is not None and daily_data is not None:
            try:
                div_detector = DivergenceDetector(lookback_period=30)
                if 'daily' in macdv_results:
                    divergence_analysis = div_detector.detect_macdv_divergence(
                        daily_data, macdv_results['daily'].macdv_result, 'daily'
                    )
                    has_divergence = divergence_analysis.has_divergence
                    if divergence_analysis.primary_signal:
                        divergence_signal = divergence_analysis.primary_signal.divergence_type.value
                logger.info(f"背離檢測完成 - 檢測到背離: {has_divergence}")
            except Exception as e:
                logger.warning(f"背離檢測失敗: {e}")
        
        # 4. 計算整合評分
        integrated_score, final_recommendation, confidence, dimension_scores = self._calculate_integrated_score(
            mtf_score, macdv_score, divergence_analysis
        )
        
        logger.info(f"整合分析完成 - 綜合評分: {integrated_score:.1f}, 建議: {final_recommendation}")
        
        return IntegratedMTFScore(
            mtf_score=mtf_score,
            macdv_score=macdv_score,
            macdv_monthly=macdv_results.get('monthly').to_dict() if 'monthly' in macdv_results else None,
            macdv_weekly=macdv_results.get('weekly').to_dict() if 'weekly' in macdv_results else None,
            macdv_daily=macdv_results.get('daily').to_dict() if 'daily' in macdv_results else None,
            divergence_analysis=divergence_analysis,
            has_divergence=has_divergence,
            divergence_signal=divergence_signal,
            integrated_score=integrated_score,
            final_recommendation=final_recommendation,
            confidence=confidence,
            dimension_scores=dimension_scores
        )
    
    def _calculate_macdv_score(self, macdv_results: Dict[str, Any]) -> float:
        """
        計算MACD-V綜合評分
        
        基於各時間框架的MACD-V信號強度計算加權評分
        """
        if not macdv_results:
            return 50.0
        
        scores = []
        weights = {'monthly': 0.40, 'weekly': 0.35, 'daily': 0.25}
        
        for timeframe, result in macdv_results.items():
            if hasattr(result, 'macdv_result'):
                # 將信號強度轉換為0-100分數
                strength = result.macdv_result.signal_strength
                # 轉換為0-100範圍 (-100~100 -> 0~100)
                score = (strength + 100) / 2
                weight = weights.get(timeframe, 0.25)
                scores.append(score * weight)
        
        return sum(scores) if scores else 50.0
    
    def _calculate_integrated_score(self,
                                    mtf_score: MTFConsistencyScore,
                                    macdv_score: float,
                                    divergence_analysis: Optional[DivergenceAnalysis]) -> Tuple[float, str, float, Dict[str, float]]:
        """
        計算整合評分
        
        權重分配：
        - MTF一致性: 40%
        - MACD-V信號: 35%
        - 背離預警: 25%
        
        背離調整：
        - 頂背離: -15分
        - 底背離: +15分
        - 無背離: 0分
        """
        # 基礎評分
        mtf_component = mtf_score.overall_score * 0.40
        macdv_component = macdv_score * 0.35
        
        # 背離評分 (0-100，50為中性)
        divergence_score = 50.0
        divergence_adjustment = 0.0
        if divergence_analysis and divergence_analysis.has_divergence and divergence_analysis.primary_signal:
            sig = divergence_analysis.primary_signal
            if sig.divergence_type == DivergenceType.TOP:
                divergence_score = 30.0  # 偏空
                divergence_adjustment = -15.0
            elif sig.divergence_type == DivergenceType.BOTTOM:
                divergence_score = 70.0  # 偏多
                divergence_adjustment = +15.0
            elif sig.divergence_type == DivergenceType.HIDDEN_TOP:
                divergence_score = 40.0
                divergence_adjustment = -10.0
            elif sig.divergence_type == DivergenceType.HIDDEN_BOTTOM:
                divergence_score = 60.0
                divergence_adjustment = +10.0
        
        divergence_component = divergence_score * 0.25
        
        # 計算整合評分
        base_score = mtf_component + macdv_component + divergence_component
        integrated_score = base_score + divergence_adjustment
        
        # 限制在0-100範圍
        integrated_score = max(0.0, min(100.0, integrated_score))
        
        # 確定最終建議
        if integrated_score >= 80:
            recommendation = "強烈買入 (Strong Buy)"
            confidence = 0.90
        elif integrated_score >= 65:
            recommendation = "買入 (Buy)"
            confidence = 0.75
        elif integrated_score >= 50:
            recommendation = "偏多觀望 (Bullish Neutral)"
            confidence = 0.60
        elif integrated_score >= 35:
            recommendation = "偏空觀望 (Bearish Neutral)"
            confidence = 0.60
        elif integrated_score >= 20:
            recommendation = "賣出 (Sell)"
            confidence = 0.75
        else:
            recommendation = "強烈賣出 (Strong Sell)"
            confidence = 0.90
        
        # 背離警告
        if divergence_analysis and divergence_analysis.has_divergence:
            if divergence_analysis.primary_signal.divergence_type == DivergenceType.TOP:
                recommendation += " ⚠️頂背離預警"
            elif divergence_analysis.primary_signal.divergence_type == DivergenceType.BOTTOM:
                recommendation += " ⚠️底背離機會"
        
        dimension_scores = {
            "mtf": round(mtf_score.overall_score, 2),
            "macdv": round(macdv_score, 2),
            "divergence": round(divergence_score, 2),
            "mtf_weighted": round(mtf_component, 2),
            "macdv_weighted": round(macdv_component, 2),
            "divergence_weighted": round(divergence_component, 2),
            "divergence_adjustment": divergence_adjustment
        }
        
        return integrated_score, recommendation, confidence, dimension_scores
    
    def validate_signal(self, score: MTFConsistencyScore, 
                        min_score: float = 70.0) -> Tuple[bool, str]:
        """
        驗證交易信號是否通過MTF過濾
        
        Args:
            score: MTF一致性評分
            min_score: 最低通過分數 (默認70)
            
        Returns:
            (是否通過, 原因說明)
        """
        if score.overall_score >= min_score:
            return True, f"MTF評分 {score.overall_score:.1f} >= {min_score}，信號通過過濾"
        else:
            return False, f"MTF評分 {score.overall_score:.1f} < {min_score}，信號被過濾"
    
    def validate_integrated_signal(self, 
                                   integrated_score: IntegratedMTFScore,
                                   min_score: float = 65.0) -> Tuple[bool, str]:
        """
        驗證整合信號是否通過過濾
        
        Args:
            integrated_score: 整合評分結果
            min_score: 最低通過分數 (默認65)
            
        Returns:
            (是否通過, 原因說明)
        """
        if integrated_score.integrated_score >= min_score:
            return True, f"整合評分 {integrated_score.integrated_score:.1f} >= {min_score}，信號通過過濾"
        else:
            return False, f"整合評分 {integrated_score.integrated_score:.1f} < {min_score}，信號被過濾"


# ============ 便捷函數 ============

def analyze_mtf(monthly_data: Optional[pd.DataFrame] = None,
                weekly_data: Optional[pd.DataFrame] = None,
                daily_data: Optional[pd.DataFrame] = None,
                monthly_weight: float = 0.40,
                weekly_weight: float = 0.35,
                daily_weight: float = 0.25) -> MTFConsistencyScore:
    """
    便捷函數: 執行MTF多時間框架分析
    
    Args:
        monthly_data: 月線數據
        weekly_data: 週線數據
        daily_data: 日線數據
        monthly_weight: 月線權重
        weekly_weight: 週線權重
        daily_weight: 日線權重
        
    Returns:
        MTFConsistencyScore: MTF一致性評分
    """
    analyzer = MTFAnalyzer(monthly_weight, weekly_weight, daily_weight)
    return analyzer.analyze(monthly_data, weekly_data, daily_data)


# ============ 單元測試 ============

if __name__ == "__main__":
    print("MTF Analyzer 單元測試")
    print("=" * 60)
    
    # 創建測試數據
    np.random.seed(42)
    
    # 生成模擬K線數據 (強上升趨勢)
    def generate_trend_data(days: int, trend: str = "up") -> pd.DataFrame:
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        if trend == "up":
            prices = 100 + np.cumsum(np.random.randn(days) * 0.5 + 0.3)
        elif trend == "down":
            prices = 100 + np.cumsum(np.random.randn(days) * 0.5 - 0.3)
        else:
            prices = 100 + np.cumsum(np.random.randn(days) * 0.5)
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.randn(days) * 0.01),
            'high': prices * (1 + abs(np.random.randn(days)) * 0.02),
            'low': prices * (1 - abs(np.random.randn(days)) * 0.02),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, days)
        }, index=dates)
        
        return df
    
    # 測試1: 三個時間框架都看多
    print("\n測試1: 三個時間框架都看多 (強烈買入)")
    monthly_up = generate_trend_data(60, "up")
    weekly_up = generate_trend_data(100, "up")
    daily_up = generate_trend_data(200, "up")
    
    analyzer = MTFAnalyzer()
    score1 = analyzer.analyze(monthly_up, weekly_up, daily_up)
    print(f"  一致性評分: {score1.overall_score:.1f}/100")
    print(f"  加權評分: {score1.weighted_score:.1f}")
    print(f"  月線趨勢: {score1.monthly_trend.name}")
    print(f"  週線趨勢: {score1.weekly_trend.name}")
    print(f"  日線趨勢: {score1.daily_trend.name}")
    print(f"  一致性等級: {score1.consistency_level}")
    print(f"  建議: {score1.recommendation}")
    
    # 測試2: 三個時間框架都看空的
    print("\n測試2: 三個時間框架都看空的 (強烈賣出)")
    monthly_down = generate_trend_data(60, "down")
    weekly_down = generate_trend_data(100, "down")
    daily_down = generate_trend_data(200, "down")
    
    score2 = analyzer.analyze(monthly_down, weekly_down, daily_down)
    print(f"  一致性評分: {score2.overall_score:.1f}/100")
    print(f"  加權評分: {score2.weighted_score:.1f}")
    print(f"  月線趨勢: {score2.monthly_trend.name}")
    print(f"  週線趨勢: {score2.weekly_trend.name}")
    print(f"  日線趨勢: {score2.daily_trend.name}")
    print(f"  一致性等級: {score2.consistency_level}")
    print(f"  建議: {score2.recommendation}")
    
    # 測試3: 混合趨勢
    print("\n測試3: 混合趨勢 (月線多/週線空/日線多)")
    score3 = analyzer.analyze(monthly_up, weekly_down, daily_up)
    print(f"  一致性評分: {score3.overall_score:.1f}/100")
    print(f"  加權評分: {score3.weighted_score:.1f}")
    print(f"  月線趨勢: {score3.monthly_trend.name}")
    print(f"  週線趨勢: {score3.weekly_trend.name}")
    print(f"  日線趨勢: {score3.daily_trend.name}")
    print(f"  一致性等級: {score3.consistency_level}")
    print(f"  建議: {score3.recommendation}")
    
    # 測試4: 權重驗證
    print("\n測試4: 權重驗證")
    print(f"  月線權重: {analyzer.WEIGHTS['monthly']:.0%}")
    print(f"  週線權重: {analyzer.WEIGHTS['weekly']:.0%}")
    print(f"  日線權重: {analyzer.WEIGHTS['daily']:.0%}")
    total = sum(analyzer.WEIGHTS.values())
    print(f"  總和: {total:.0%} (應為100%)")
    assert abs(total - 1.0) < 0.001, "權重總和必須為1.0"
    print("  ✓ 權重驗證通過")
    
    # 測試5: 信號驗證
    print("\n測試5: 信號驗證功能")
    passed, reason = analyzer.validate_signal(score1, min_score=70.0)
    print(f"  強烈看多信號驗證: {'通過' if passed else '未通過'} - {reason}")
    
    passed, reason = analyzer.validate_signal(score2, min_score=70.0)
    print(f"  強烈看空信號驗證: {'通過' if passed else '未通過'} - {reason}")
    
    print("\n" + "=" * 60)
    print("所有測試完成!")
