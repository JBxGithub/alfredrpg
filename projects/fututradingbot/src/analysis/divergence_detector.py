"""
Divergence Detector Module
背離檢測模組

自動檢測價格與MACD-V指標之間的背離現象：
- 頂背離 (Top Divergence): 價格創新高但MACD-V未創新高，預示可能下跌
- 底背離 (Bottom Divergence): 價格創新低但MACD-V未創新低，預示可能上漲

背離是強烈的趨勢反轉預警信號，結合MTF分析可提高準確性。
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import pandas as pd
import numpy as np

# 可選依賴
try:
    from src.utils.logger import get_logger
    from src.indicators.macdv import MACDVResult, MACDVCalculator
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    get_logger = lambda name: logging.getLogger(name)
    MACDVResult = None
    MACDVCalculator = None

logger = get_logger(__name__)


class DivergenceType(Enum):
    """背離類型"""
    TOP = "top"                    # 頂背離
    BOTTOM = "bottom"              # 底背離
    HIDDEN_TOP = "hidden_top"      # 隱藏頂背離
    HIDDEN_BOTTOM = "hidden_bottom" # 隱藏底背離
    NONE = "none"                  # 無背離


class DivergenceStrength(Enum):
    """背離強度"""
    STRONG = "strong"      # 強背離
    MODERATE = "moderate"  # 中等背離
    WEAK = "weak"          # 弱背離


@dataclass
class DivergencePoint:
    """背離點數據"""
    timestamp: datetime            # 時間戳
    price: float                   # 價格
    indicator_value: float         # 指標值
    is_peak: bool                  # 是否為峰值
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "price": self.price,
            "indicator_value": self.indicator_value,
            "is_peak": self.is_peak
        }


@dataclass
class DivergenceSignal:
    """背離信號"""
    divergence_type: DivergenceType      # 背離類型
    strength: DivergenceStrength         # 背離強度
    confidence: float                    # 置信度 (0-100)
    
    # 背離點
    first_point: DivergencePoint         # 第一個點（較早）
    second_point: DivergencePoint        # 第二個點（較晚）
    
    # 價格和指標變化
    price_change_pct: float              # 價格變化百分比
    indicator_change_pct: float          # 指標變化百分比
    divergence_magnitude: float          # 背離幅度
    
    # 時間框架
    timeframe: str                       # 時間框架
    
    # 描述
    description: str                     # 背離描述
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.divergence_type.value,
            "strength": self.strength.value,
            "confidence": round(self.confidence, 2),
            "first_point": self.first_point.to_dict(),
            "second_point": self.second_point.to_dict(),
            "price_change_pct": round(self.price_change_pct, 4),
            "indicator_change_pct": round(self.indicator_change_pct, 4),
            "divergence_magnitude": round(self.divergence_magnitude, 4),
            "timeframe": self.timeframe,
            "description": self.description
        }


@dataclass
class DivergenceAnalysis:
    """背離分析結果"""
    has_divergence: bool                 # 是否存在背離
    signals: List[DivergenceSignal]      # 背離信號列表
    primary_signal: Optional[DivergenceSignal] = None  # 主要信號
    
    # 統計信息
    top_divergence_count: int = 0        # 頂背離數量
    bottom_divergence_count: int = 0     # 底背離數量
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_divergence": self.has_divergence,
            "signals": [s.to_dict() for s in self.signals],
            "primary_signal": self.primary_signal.to_dict() if self.primary_signal else None,
            "top_divergence_count": self.top_divergence_count,
            "bottom_divergence_count": self.bottom_divergence_count
        }


class DivergenceDetector:
    """
    背離檢測器
    
    檢測價格與MACD-V指標之間的背離現象。
    
    核心邏輯：
    1. 識別價格和指標的局部極值點（峰值/谷值）
    2. 比較相鄰極值點的價格和指標變化
    3. 判斷是否存在背離（價格和指標變化方向相反）
    4. 評估背離強度和置信度
    
    參數配置：
    - lookback_period: 回顧期（用於尋找極值點）
    - min_swings: 最小波動次數
    - divergence_threshold: 背離閾值
    """
    
    def __init__(self,
                 lookback_period: int = 30,
                 min_swings: int = 2,
                 divergence_threshold: float = 0.02):
        """
        初始化背離檢測器
        
        Args:
            lookback_period: 回顧期（尋找極值點的窗口）
            min_swings: 最小波動次數（至少需要2個峰值或谷值）
            divergence_threshold: 背離閾值（最小背離幅度）
        """
        self.lookback_period = lookback_period
        self.min_swings = min_swings
        self.divergence_threshold = divergence_threshold
        
        logger.info(f"背離檢測器初始化 - 回顧期:{lookback_period}, "
                   f"最小波動:{min_swings}, 閾值:{divergence_threshold}")
    
    def detect(self, 
               df: pd.DataFrame, 
               indicator: pd.Series,
               timeframe: str = 'daily') -> DivergenceAnalysis:
        """
        檢測背離
        
        Args:
            df: K線數據DataFrame，需包含 'high', 'low', 'close'
            indicator: 指標序列（如MACD-V）
            timeframe: 時間框架名稱
            
        Returns:
            DivergenceAnalysis: 背離分析結果
        """
        if df is None or df.empty or indicator is None or indicator.empty:
            return DivergenceAnalysis(has_divergence=False, signals=[])
        
        if len(df) < self.lookback_period * 2:
            return DivergenceAnalysis(has_divergence=False, signals=[])
        
        # 確保數據長度一致
        min_len = min(len(df), len(indicator))
        df = df.iloc[-min_len:].copy()
        indicator = indicator.iloc[-min_len:].copy()
        
        # 識別價格極值點
        price_peaks, price_valleys = self._find_extreme_points(df['high'], df['low'])
        
        # 識別指標極值點
        indicator_peaks, indicator_valleys = self._find_indicator_extremes(indicator)
        
        signals = []
        
        # 檢測頂背離（價格峰值）
        top_signals = self._check_divergence_at_peaks(
            df, indicator, price_peaks, indicator_peaks, timeframe
        )
        signals.extend(top_signals)
        
        # 檢測底背離（價格谷值）
        bottom_signals = self._check_divergence_at_valleys(
            df, indicator, price_valleys, indicator_valleys, timeframe
        )
        signals.extend(bottom_signals)
        
        # 按置信度排序
        signals.sort(key=lambda x: x.confidence, reverse=True)
        
        # 統計
        top_count = sum(1 for s in signals if s.divergence_type == DivergenceType.TOP)
        bottom_count = sum(1 for s in signals if s.divergence_type == DivergenceType.BOTTOM)
        
        return DivergenceAnalysis(
            has_divergence=len(signals) > 0,
            signals=signals,
            primary_signal=signals[0] if signals else None,
            top_divergence_count=top_count,
            bottom_divergence_count=bottom_count
        )
    
    def detect_macdv_divergence(self,
                                 df: pd.DataFrame,
                                 macdv_result: 'MACDVResult',
                                 timeframe: str = 'daily') -> DivergenceAnalysis:
        """
        檢測MACD-V背離
        
        使用MACD-V的柱狀圖進行背離檢測
        
        Args:
            df: K線數據
            macdv_result: MACD-V計算結果
            timeframe: 時間框架
            
        Returns:
            DivergenceAnalysis: 背離分析結果
        """
        # 使用MACD-V柱狀圖進行背離檢測
        return self.detect(df, macdv_result.histogram_v, timeframe)
    
    def _find_extreme_points(self, 
                             highs: pd.Series, 
                             lows: pd.Series) -> Tuple[List[int], List[int]]:
        """
        識別價格極值點
        
        使用局部極大值/極小值算法識別峰值和谷值
        
        Returns:
            (峰值索引列表, 谷值索引列表)
        """
        peaks = []
        valleys = []
        
        window = max(3, self.lookback_period // 10)
        
        for i in range(window, len(highs) - window):
            # 檢查峰值
            if highs.iloc[i] == highs.iloc[i-window:i+window+1].max():
                peaks.append(i)
            
            # 檢查谷值
            if lows.iloc[i] == lows.iloc[i-window:i+window+1].min():
                valleys.append(i)
        
        return peaks, valleys
    
    def _find_indicator_extremes(self, indicator: pd.Series) -> Tuple[List[int], List[int]]:
        """識別指標極值點"""
        peaks = []
        valleys = []
        
        window = max(3, self.lookback_period // 10)
        
        for i in range(window, len(indicator) - window):
            # 檢查峰值
            if indicator.iloc[i] == indicator.iloc[i-window:i+window+1].max():
                peaks.append(i)
            
            # 檢查谷值
            if indicator.iloc[i] == indicator.iloc[i-window:i+window+1].min():
                valleys.append(i)
        
        return peaks, valleys
    
    def _check_divergence_at_peaks(self,
                                    df: pd.DataFrame,
                                    indicator: pd.Series,
                                    price_peaks: List[int],
                                    indicator_peaks: List[int],
                                    timeframe: str) -> List[DivergenceSignal]:
        """
        在價格峰值處檢查頂背離
        
        頂背離：價格創新高，但指標未創新高
        """
        signals = []
        
        if len(price_peaks) < self.min_swings:
            return signals
        
        # 取最近的峰值進行比較
        for i in range(len(price_peaks) - 1, 0, -1):
            if len(signals) >= 3:  # 最多檢測3個背離
                break
            
            curr_idx = price_peaks[i]
            prev_idx = price_peaks[i-1]
            
            # 確保兩個峰值之間有足夠的距離
            if curr_idx - prev_idx < 5:
                continue
            
            curr_price = df['high'].iloc[curr_idx]
            prev_price = df['high'].iloc[prev_idx]
            
            # 找到對應的指標峰值
            curr_ind_peak = self._find_nearest_peak(curr_idx, indicator_peaks)
            prev_ind_peak = self._find_nearest_peak(prev_idx, indicator_peaks)
            
            if curr_ind_peak is None or prev_ind_peak is None:
                continue
            
            curr_ind = indicator.iloc[curr_ind_peak]
            prev_ind = indicator.iloc[prev_ind_peak]
            
            # 檢查頂背離條件
            price_change = (curr_price - prev_price) / prev_price
            ind_change = (curr_ind - prev_ind) / abs(prev_ind) if prev_ind != 0 else 0
            
            # 頂背離：價格上漲但指標下降
            if price_change > self.divergence_threshold and ind_change < -self.divergence_threshold:
                divergence_magnitude = price_change - ind_change
                
                # 確定背離強度
                if divergence_magnitude > 0.1:
                    strength = DivergenceStrength.STRONG
                    confidence = 85.0
                elif divergence_magnitude > 0.05:
                    strength = DivergenceStrength.MODERATE
                    confidence = 70.0
                else:
                    strength = DivergenceStrength.WEAK
                    confidence = 55.0
                
                signal = DivergenceSignal(
                    divergence_type=DivergenceType.TOP,
                    strength=strength,
                    confidence=confidence,
                    first_point=DivergencePoint(
                        timestamp=df.index[prev_idx],
                        price=prev_price,
                        indicator_value=prev_ind,
                        is_peak=True
                    ),
                    second_point=DivergencePoint(
                        timestamp=df.index[curr_idx],
                        price=curr_price,
                        indicator_value=curr_ind,
                        is_peak=True
                    ),
                    price_change_pct=price_change * 100,
                    indicator_change_pct=ind_change * 100,
                    divergence_magnitude=divergence_magnitude,
                    timeframe=timeframe,
                    description=f"頂背離: 價格上漲{price_change*100:.2f}%但指標下降{abs(ind_change)*100:.2f}%"
                )
                signals.append(signal)
        
        return signals
    
    def _check_divergence_at_valleys(self,
                                      df: pd.DataFrame,
                                      indicator: pd.Series,
                                      price_valleys: List[int],
                                      indicator_valleys: List[int],
                                      timeframe: str) -> List[DivergenceSignal]:
        """
        在價格谷值處檢查底背離
        
        底背離：價格創新低，但指標未創新低
        """
        signals = []
        
        if len(price_valleys) < self.min_swings:
            return signals
        
        # 取最近的谷值進行比較
        for i in range(len(price_valleys) - 1, 0, -1):
            if len(signals) >= 3:  # 最多檢測3個背離
                break
            
            curr_idx = price_valleys[i]
            prev_idx = price_valleys[i-1]
            
            # 確保兩個谷值之間有足夠的距離
            if curr_idx - prev_idx < 5:
                continue
            
            curr_price = df['low'].iloc[curr_idx]
            prev_price = df['low'].iloc[prev_idx]
            
            # 找到對應的指標谷值
            curr_ind_valley = self._find_nearest_valley(curr_idx, indicator_valleys)
            prev_ind_valley = self._find_nearest_valley(prev_idx, indicator_valleys)
            
            if curr_ind_valley is None or prev_ind_valley is None:
                continue
            
            curr_ind = indicator.iloc[curr_ind_valley]
            prev_ind = indicator.iloc[prev_ind_valley]
            
            # 檢查底背離條件
            price_change = (curr_price - prev_price) / prev_price
            ind_change = (curr_ind - prev_ind) / abs(prev_ind) if prev_ind != 0 else 0
            
            # 底背離：價格下跌但指標上升
            if price_change < -self.divergence_threshold and ind_change > self.divergence_threshold:
                divergence_magnitude = abs(price_change) + ind_change
                
                # 確定背離強度
                if divergence_magnitude > 0.1:
                    strength = DivergenceStrength.STRONG
                    confidence = 85.0
                elif divergence_magnitude > 0.05:
                    strength = DivergenceStrength.MODERATE
                    confidence = 70.0
                else:
                    strength = DivergenceStrength.WEAK
                    confidence = 55.0
                
                signal = DivergenceSignal(
                    divergence_type=DivergenceType.BOTTOM,
                    strength=strength,
                    confidence=confidence,
                    first_point=DivergencePoint(
                        timestamp=df.index[prev_idx],
                        price=prev_price,
                        indicator_value=prev_ind,
                        is_peak=False
                    ),
                    second_point=DivergencePoint(
                        timestamp=df.index[curr_idx],
                        price=curr_price,
                        indicator_value=curr_ind,
                        is_peak=False
                    ),
                    price_change_pct=price_change * 100,
                    indicator_change_pct=ind_change * 100,
                    divergence_magnitude=divergence_magnitude,
                    timeframe=timeframe,
                    description=f"底背離: 價格下跌{abs(price_change)*100:.2f}%但指標上升{ind_change*100:.2f}%"
                )
                signals.append(signal)
        
        return signals
    
    def _find_nearest_peak(self, idx: int, peaks: List[int]) -> Optional[int]:
        """找到最近的峰值索引"""
        if not peaks:
            return None
        
        nearest = min(peaks, key=lambda p: abs(p - idx))
        if abs(nearest - idx) <= 3:  # 允許3個單位的誤差
            return nearest
        return None
    
    def _find_nearest_valley(self, idx: int, valleys: List[int]) -> Optional[int]:
        """找到最近的谷值索引"""
        if not valleys:
            return None
        
        nearest = min(valleys, key=lambda v: abs(v - idx))
        if abs(nearest - idx) <= 3:  # 允許3個單位的誤差
            return nearest
        return None
    
    def detect_multi_timeframe(self,
                                monthly_df: Optional[pd.DataFrame] = None,
                                weekly_df: Optional[pd.DataFrame] = None,
                                daily_df: Optional[pd.DataFrame] = None,
                                monthly_macdv: Optional['MACDVResult'] = None,
                                weekly_macdv: Optional['MACDVResult'] = None,
                                daily_macdv: Optional['MACDVResult'] = None) -> Dict[str, DivergenceAnalysis]:
        """
        多時間框架背離檢測
        
        Args:
            monthly_df: 月線數據
            weekly_df: 週線數據
            daily_df: 日線數據
            monthly_macdv: 月線MACD-V結果
            weekly_macdv: 週線MACD-V結果
            daily_macdv: 日線MACD-V結果
            
        Returns:
            Dict[str, DivergenceAnalysis]: 各時間框架的背離分析
        """
        results = {}
        
        if monthly_df is not None and monthly_macdv is not None:
            results['monthly'] = self.detect_macdv_divergence(monthly_df, monthly_macdv, 'monthly')
        
        if weekly_df is not None and weekly_macdv is not None:
            results['weekly'] = self.detect_macdv_divergence(weekly_df, weekly_macdv, 'weekly')
        
        if daily_df is not None and daily_macdv is not None:
            results['daily'] = self.detect_macdv_divergence(daily_df, daily_macdv, 'daily')
        
        return results
    
    def get_combined_signal(self, 
                           mtf_divergence: Dict[str, DivergenceAnalysis]) -> Dict[str, Any]:
        """
        獲取綜合背離信號
        
        分析多時間框架的背離信號，給出綜合判斷
        
        Args:
            mtf_divergence: 多時間框架背離分析結果
            
        Returns:
            Dict: 綜合信號
        """
        top_signals = []
        bottom_signals = []
        
        for timeframe, analysis in mtf_divergence.items():
            if analysis.has_divergence and analysis.primary_signal:
                sig = analysis.primary_signal
                if sig.divergence_type == DivergenceType.TOP:
                    top_signals.append((timeframe, sig))
                elif sig.divergence_type == DivergenceType.BOTTOM:
                    bottom_signals.append((timeframe, sig))
        
        # 判斷綜合信號
        if len(top_signals) >= 2:
            return {
                "signal": "strong_sell",
                "confidence": max(s.confidence for _, s in top_signals),
                "description": f"多時間框架頂背離 ({len(top_signals)}個框架)",
                "timeframes": [tf for tf, _ in top_signals]
            }
        elif len(bottom_signals) >= 2:
            return {
                "signal": "strong_buy",
                "confidence": max(s.confidence for _, s in bottom_signals),
                "description": f"多時間框架底背離 ({len(bottom_signals)}個框架)",
                "timeframes": [tf for tf, _ in bottom_signals]
            }
        elif top_signals:
            return {
                "signal": "sell",
                "confidence": top_signals[0][1].confidence,
                "description": f"單一時間框架頂背離 ({top_signals[0][0]})",
                "timeframes": [top_signals[0][0]]
            }
        elif bottom_signals:
            return {
                "signal": "buy",
                "confidence": bottom_signals[0][1].confidence,
                "description": f"單一時間框架底背離 ({bottom_signals[0][0]})",
                "timeframes": [bottom_signals[0][0]]
            }
        else:
            return {
                "signal": "neutral",
                "confidence": 0.0,
                "description": "無明顯背離信號",
                "timeframes": []
            }


# ============ 便捷函數 ============

def detect_divergence(df: pd.DataFrame,
                      indicator: pd.Series,
                      lookback_period: int = 30,
                      timeframe: str = 'daily') -> DivergenceAnalysis:
    """
    便捷函數: 檢測背離
    
    Args:
        df: K線數據
        indicator: 指標序列
        lookback_period: 回顧期
        timeframe: 時間框架
        
    Returns:
        DivergenceAnalysis: 背離分析結果
    """
    detector = DivergenceDetector(lookback_period=lookback_period)
    return detector.detect(df, indicator, timeframe)


def detect_macdv_divergence(df: pd.DataFrame,
                            macdv_result: 'MACDVResult',
                            lookback_period: int = 30,
                            timeframe: str = 'daily') -> DivergenceAnalysis:
    """
    便捷函數: 檢測MACD-V背離
    
    Args:
        df: K線數據
        macdv_result: MACD-V結果
        lookback_period: 回顧期
        timeframe: 時間框架
        
    Returns:
        DivergenceAnalysis: 背離分析結果
    """
    detector = DivergenceDetector(lookback_period=lookback_period)
    return detector.detect_macdv_divergence(df, macdv_result, timeframe)


# ============ 單元測試 ============

if __name__ == "__main__":
    print("Divergence Detector 單元測試")
    print("=" * 60)
    
    # 創建測試數據（模擬頂背離）
    np.random.seed(42)
    
    def generate_divergence_data(days: int, divergence_type: str = "top") -> Tuple[pd.DataFrame, pd.Series]:
        """生成帶背離的測試數據"""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        if divergence_type == "top":
            # 頂背離：價格創新高，指標下降
            prices = np.concatenate([
                np.linspace(100, 120, days // 2),
                np.linspace(120, 130, days // 4),
                np.linspace(130, 125, days - days // 2 - days // 4)
            ])
            indicator = np.concatenate([
                np.linspace(50, 70, days // 2),
                np.linspace(70, 65, days // 4),
                np.linspace(65, 60, days - days // 2 - days // 4)
            ])
        else:  # bottom
            # 底背離：價格創新低，指標上升
            prices = np.concatenate([
                np.linspace(100, 80, days // 2),
                np.linspace(80, 70, days // 4),
                np.linspace(70, 75, days - days // 2 - days // 4)
            ])
            indicator = np.concatenate([
                np.linspace(50, 30, days // 2),
                np.linspace(30, 35, days // 4),
                np.linspace(35, 40, days - days // 2 - days // 4)
            ])
        
        prices += np.random.randn(days) * 1.0
        indicator += np.random.randn(days) * 0.5
        
        df = pd.DataFrame({
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, days)
        }, index=dates)
        
        return df, pd.Series(indicator, index=dates)
    
    # 測試1: 頂背離檢測
    print("\n測試1: 頂背離檢測")
    df_top, ind_top = generate_divergence_data(100, "top")
    detector = DivergenceDetector(lookback_period=20)
    result_top = detector.detect(df_top, ind_top, 'daily')
    
    print(f"  檢測到背離: {result_top.has_divergence}")
    print(f"  頂背離數量: {result_top.top_divergence_count}")
    print(f"  底背離數量: {result_top.bottom_divergence_count}")
    if result_top.primary_signal:
        print(f"  主要信號: {result_top.primary_signal.description}")
        print(f"  置信度: {result_top.primary_signal.confidence}")
    
    # 測試2: 底背離檢測
    print("\n測試2: 底背離檢測")
    df_bottom, ind_bottom = generate_divergence_data(100, "bottom")
    result_bottom = detector.detect(df_bottom, ind_bottom, 'daily')
    
    print(f"  檢測到背離: {result_bottom.has_divergence}")
    print(f"  頂背離數量: {result_bottom.top_divergence_count}")
    print(f"  底背離數量: {result_bottom.bottom_divergence_count}")
    if result_bottom.primary_signal:
        print(f"  主要信號: {result_bottom.primary_signal.description}")
        print(f"  置信度: {result_bottom.primary_signal.confidence}")
    
    print("\n" + "=" * 60)
    print("所有測試完成!")
