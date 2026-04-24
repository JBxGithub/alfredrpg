"""
MACD-V (Volume-Weighted MACD) Indicator Module
MACD-V 成交量加權MACD指標模組

將成交量加權整合到MACD計算中，形成更可靠的趨勢確認指標。
成交量加權使MACD對大成交量價格變動更敏感，對小成交量變動較不敏感。

支援多時間框架：月線/週線/日線
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
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    get_logger = lambda name: logging.getLogger(name)

logger = get_logger(__name__)


class MACDVSignal(Enum):
    """MACD-V 信號類型"""
    STRONG_BUY = "strong_buy"      # 強烈買入
    BUY = "buy"                    # 買入
    NEUTRAL = "neutral"            # 中性
    SELL = "sell"                  # 賣出
    STRONG_SELL = "strong_sell"    # 強烈賣出


@dataclass
class MACDVResult:
    """MACD-V 計算結果"""
    # 標準MACD
    macd_line: pd.Series           # MACD線 (DIF)
    signal_line: pd.Series         # 信號線 (DEA)
    histogram: pd.Series           # MACD柱狀圖
    
    # 成交量加權MACD-V
    macd_v_line: pd.Series         # MACD-V線 (成交量加權DIF)
    signal_v_line: pd.Series       # MACD-V信號線
    histogram_v: pd.Series         # MACD-V柱狀圖
    
    # 成交量確認指標
    volume_confirmation: pd.Series # 成交量確認度 (0-1)
    volume_trend: pd.Series        # 成交量趨勢
    
    # 信號強度
    signal_strength: float         # 當前信號強度 (-100 到 100)
    current_signal: MACDVSignal    # 當前信號類型
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "current_macd": float(self.macd_line.iloc[-1]) if not self.macd_line.empty else 0.0,
            "current_signal": float(self.signal_line.iloc[-1]) if not self.signal_line.empty else 0.0,
            "current_histogram": float(self.histogram.iloc[-1]) if not self.histogram.empty else 0.0,
            "current_macd_v": float(self.macd_v_line.iloc[-1]) if not self.macd_v_line.empty else 0.0,
            "current_signal_v": float(self.signal_v_line.iloc[-1]) if not self.signal_v_line.empty else 0.0,
            "current_histogram_v": float(self.histogram_v.iloc[-1]) if not self.histogram_v.empty else 0.0,
            "volume_confirmation": float(self.volume_confirmation.iloc[-1]) if not self.volume_confirmation.empty else 0.0,
            "signal_strength": self.signal_strength,
            "current_signal": self.current_signal.value
        }


@dataclass
class TimeframeMACDV:
    """單一時間框架的MACD-V分析結果"""
    timeframe: str                 # 時間框架名稱
    macdv_result: MACDVResult      # MACD-V計算結果
    trend_alignment: float         # 趨勢一致性分數 (0-100)
    volume_quality: float          # 成交量質量評分 (0-100)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timeframe": self.timeframe,
            "macdv": self.macdv_result.to_dict(),
            "trend_alignment": self.trend_alignment,
            "volume_quality": self.volume_quality
        }


class MACDVCalculator:
    """
    MACD-V (成交量加權MACD) 計算器
    
    核心概念：
    1. 使用成交量加權價格計算MACD，使大成交量價格變動影響更大
    2. 計算成交量確認度，評估價格變動的可靠性
    3. 結合標準MACD和MACD-V，提供更全面的信號
    
    參數配置：
    - fast_period: 快線週期 (默認12)
    - slow_period: 慢線週期 (默認26)
    - signal_period: 信號線週期 (默認9)
    - volume_weight: 成交量加權係數 (默認0.3)
    """
    
    # 不同時間框架的默認參數
    TIMEFRAME_PARAMS = {
        'monthly': {'fast': 6, 'slow': 13, 'signal': 5},    # 月線：較短週期
        'weekly': {'fast': 12, 'slow': 26, 'signal': 9},    # 週線：標準週期
        'daily': {'fast': 12, 'slow': 26, 'signal': 9},     # 日線：標準週期
        '4h': {'fast': 12, 'slow': 26, 'signal': 9},        # 4小時：標準週期
        '1h': {'fast': 12, 'slow': 26, 'signal': 9}         # 1小時：標準週期
    }
    
    def __init__(self, 
                 fast_period: int = 12,
                 slow_period: int = 26, 
                 signal_period: int = 9,
                 volume_weight: float = 0.3):
        """
        初始化MACD-V計算器
        
        Args:
            fast_period: 快線EMA週期
            slow_period: 慢線EMA週期
            signal_period: 信號線EMA週期
            volume_weight: 成交量加權係數 (0-1)
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.volume_weight = volume_weight
        
        logger.info(f"MACD-V計算器初始化 - 快線:{fast_period}, 慢線:{slow_period}, "
                   f"信號線:{signal_period}, 成交量權重:{volume_weight}")
    
    def calculate(self, df: pd.DataFrame, timeframe: str = 'daily') -> MACDVResult:
        """
        計算MACD-V指標
        
        Args:
            df: K線數據DataFrame，需包含 'close', 'volume' 列
            timeframe: 時間框架名稱
            
        Returns:
            MACDVResult: MACD-V計算結果
        """
        if df is None or df.empty:
            raise ValueError("數據為空")
        
        if 'close' not in df.columns or 'volume' not in df.columns:
            raise ValueError("數據需包含 'close' 和 'volume' 列")
        
        # 獲取時間框架參數
        params = self.TIMEFRAME_PARAMS.get(timeframe, self.TIMEFRAME_PARAMS['daily'])
        fast = params['fast']
        slow = params['slow']
        signal = params['signal']
        
        close = df['close'].astype(float)
        volume = df['volume'].astype(float)
        
        # ========== 1. 計算標準MACD ==========
        macd_line, signal_line, histogram = self._calculate_standard_macd(close, fast, slow, signal)
        
        # ========== 2. 計算成交量加權MACD-V ==========
        macd_v_line, signal_v_line, histogram_v = self._calculate_volume_weighted_macd(
            close, volume, fast, slow, signal
        )
        
        # ========== 3. 計算成交量確認度 ==========
        volume_confirmation = self._calculate_volume_confirmation(volume, close, fast)
        
        # ========== 4. 計算成交量趨勢 ==========
        volume_trend = self._calculate_volume_trend(volume)
        
        # ========== 5. 計算信號強度 ==========
        signal_strength, current_signal = self._calculate_signal_strength(
            macd_line, signal_line, histogram,
            macd_v_line, signal_v_line, histogram_v,
            volume_confirmation
        )
        
        return MACDVResult(
            macd_line=macd_line,
            signal_line=signal_line,
            histogram=histogram,
            macd_v_line=macd_v_line,
            signal_v_line=signal_v_line,
            histogram_v=histogram_v,
            volume_confirmation=volume_confirmation,
            volume_trend=volume_trend,
            signal_strength=signal_strength,
            current_signal=current_signal
        )
    
    def _calculate_standard_macd(self, close: pd.Series, fast: int, slow: int, signal: int) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """計算標準MACD"""
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def _calculate_volume_weighted_macd(self, close: pd.Series, volume: pd.Series,
                                        fast: int, slow: int, signal: int) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        計算成交量加權MACD-V
        
        核心邏輯：
        1. 計算成交量加權價格變動
        2. 使用加權後的價格計算EMA
        3. 結合標準EMA和加權EMA
        """
        # 計算成交量加權係數
        volume_ma = volume.rolling(window=fast, min_periods=1).mean()
        volume_ratio = volume / volume_ma
        
        # 限制成交量比率的極端值
        volume_ratio = volume_ratio.clip(upper=3.0, lower=0.3)
        
        # 計算成交量加權價格
        # 公式: 加權價格 = 收盤價 * (1 + 成交量比率 * 權重係數)
        price_change = close.pct_change().fillna(0)
        weighted_change = price_change * volume_ratio * self.volume_weight
        weighted_price = close * (1 + weighted_change)
        
        # 混合標準價格和加權價格
        mixed_price = close * (1 - self.volume_weight) + weighted_price * self.volume_weight
        
        # 計算MACD-V
        ema_fast_v = mixed_price.ewm(span=fast, adjust=False).mean()
        ema_slow_v = mixed_price.ewm(span=slow, adjust=False).mean()
        macd_v_line = ema_fast_v - ema_slow_v
        signal_v_line = macd_v_line.ewm(span=signal, adjust=False).mean()
        histogram_v = macd_v_line - signal_v_line
        
        return macd_v_line, signal_v_line, histogram_v
    
    def _calculate_volume_confirmation(self, volume: pd.Series, close: pd.Series, period: int) -> pd.Series:
        """
        計算成交量確認度
        
        評估當前成交量是否支持價格變動：
        - 價格上漲 + 成交量放大 = 高確認度
        - 價格下跌 + 成交量放大 = 高確認度
        - 價格變動 + 成交量萎縮 = 低確認度
        """
        # 計算成交量移動平均
        volume_ma = volume.rolling(window=period, min_periods=1).mean()
        
        # 計算價格變動方向
        price_change = close.diff()
        
        # 計算成交量比率
        volume_ratio = volume / volume_ma
        
        # 確認度計算
        confirmation = pd.Series(0.5, index=volume.index)  # 基礎確認度
        
        # 價格上漲且成交量放大
        up_with_volume = (price_change > 0) & (volume_ratio > 1.2)
        confirmation[up_with_volume] = 0.5 + 0.5 * (volume_ratio[up_with_volume] - 1.2).clip(upper=1.0)
        
        # 價格下跌且成交量放大
        down_with_volume = (price_change < 0) & (volume_ratio > 1.2)
        confirmation[down_with_volume] = 0.5 + 0.5 * (volume_ratio[down_with_volume] - 1.2).clip(upper=1.0)
        
        # 價格變動但成交量萎縮
        low_volume = volume_ratio < 0.8
        confirmation[low_volume] = 0.5 * volume_ratio[low_volume]
        
        return confirmation.clip(0.0, 1.0)
    
    def _calculate_volume_trend(self, volume: pd.Series, period: int = 10) -> pd.Series:
        """計算成交量趨勢"""
        volume_ma_short = volume.rolling(window=period//2, min_periods=1).mean()
        volume_ma_long = volume.rolling(window=period, min_periods=1).mean()
        
        trend = (volume_ma_short / volume_ma_long - 1) * 100
        return trend
    
    def _calculate_signal_strength(self, macd_line: pd.Series, signal_line: pd.Series,
                                   histogram: pd.Series, macd_v_line: pd.Series,
                                   signal_v_line: pd.Series, histogram_v: pd.Series,
                                   volume_confirmation: pd.Series) -> Tuple[float, MACDVSignal]:
        """
        計算信號強度和類型
        
        綜合考慮：
        1. 標準MACD信號
        2. MACD-V信號
        3. 成交量確認度
        
        返回: (信號強度 -100到100, 信號類型)
        """
        if len(macd_line) < 2:
            return 0.0, MACDVSignal.NEUTRAL
        
        # 獲取最新值
        macd_val = macd_line.iloc[-1]
        signal_val = signal_line.iloc[-1]
        hist_val = histogram.iloc[-1]
        macd_v_val = macd_v_line.iloc[-1]
        signal_v_val = signal_v_line.iloc[-1]
        hist_v_val = histogram_v.iloc[-1]
        vol_conf = volume_confirmation.iloc[-1]
        
        # 計算標準MACD強度
        macd_strength = 0
        if macd_val > signal_val and hist_val > 0:
            macd_strength = min(50, abs(hist_val) * 10)
        elif macd_val < signal_val and hist_val < 0:
            macd_strength = -min(50, abs(hist_val) * 10)
        
        # 計算MACD-V強度
        macdv_strength = 0
        if macd_v_val > signal_v_val and hist_v_val > 0:
            macdv_strength = min(50, abs(hist_v_val) * 10)
        elif macd_v_val < signal_v_val and hist_v_val < 0:
            macdv_strength = -min(50, abs(hist_v_val) * 10)
        
        # 綜合強度 (加權平均)
        combined_strength = (macd_strength * 0.4 + macdv_strength * 0.6) * vol_conf
        
        # 確定信號類型
        if combined_strength > 60:
            signal_type = MACDVSignal.STRONG_BUY
        elif combined_strength > 30:
            signal_type = MACDVSignal.BUY
        elif combined_strength < -60:
            signal_type = MACDVSignal.STRONG_SELL
        elif combined_strength < -30:
            signal_type = MACDVSignal.SELL
        else:
            signal_type = MACDVSignal.NEUTRAL
        
        return combined_strength, signal_type
    
    def calculate_multi_timeframe(self, 
                                   monthly_df: Optional[pd.DataFrame] = None,
                                   weekly_df: Optional[pd.DataFrame] = None,
                                   daily_df: Optional[pd.DataFrame] = None) -> Dict[str, TimeframeMACDV]:
        """
        計算多時間框架MACD-V
        
        Args:
            monthly_df: 月線數據
            weekly_df: 週線數據
            daily_df: 日線數據
            
        Returns:
            Dict[str, TimeframeMACDV]: 各時間框架的MACD-V結果
        """
        results = {}
        
        if monthly_df is not None and not monthly_df.empty:
            macdv = self.calculate(monthly_df, 'monthly')
            results['monthly'] = TimeframeMACDV(
                timeframe='monthly',
                macdv_result=macdv,
                trend_alignment=self._calculate_trend_alignment(macdv),
                volume_quality=self._calculate_volume_quality(monthly_df)
            )
        
        if weekly_df is not None and not weekly_df.empty:
            macdv = self.calculate(weekly_df, 'weekly')
            results['weekly'] = TimeframeMACDV(
                timeframe='weekly',
                macdv_result=macdv,
                trend_alignment=self._calculate_trend_alignment(macdv),
                volume_quality=self._calculate_volume_quality(weekly_df)
            )
        
        if daily_df is not None and not daily_df.empty:
            macdv = self.calculate(daily_df, 'daily')
            results['daily'] = TimeframeMACDV(
                timeframe='daily',
                macdv_result=macdv,
                trend_alignment=self._calculate_trend_alignment(macdv),
                volume_quality=self._calculate_volume_quality(daily_df)
            )
        
        return results
    
    def _calculate_trend_alignment(self, macdv: MACDVResult) -> float:
        """計算趨勢一致性分數"""
        if len(macdv.macd_line) < 3:
            return 50.0
        
        # 檢查MACD和MACD-V方向是否一致
        macd_direction = 1 if macdv.histogram.iloc[-1] > 0 else -1
        macdv_direction = 1 if macdv.histogram_v.iloc[-1] > 0 else -1
        
        if macd_direction == macdv_direction:
            return 80.0 if macdv_direction == 1 else 20.0
        else:
            return 50.0
    
    def _calculate_volume_quality(self, df: pd.DataFrame) -> float:
        """計算成交量質量評分"""
        if 'volume' not in df.columns or len(df) < 20:
            return 50.0
        
        volume = df['volume']
        volume_ma = volume.rolling(window=20, min_periods=1).mean()
        
        # 計算成交量穩定性
        cv = volume.std() / volume.mean() if volume.mean() > 0 else 1.0
        
        # 穩定性越高，質量越好
        if cv < 0.3:
            return 90.0
        elif cv < 0.5:
            return 70.0
        elif cv < 0.8:
            return 50.0
        else:
            return 30.0


# ============ 便捷函數 ============

def calculate_macdv(df: pd.DataFrame, 
                    fast: int = 12, 
                    slow: int = 26, 
                    signal: int = 9,
                    volume_weight: float = 0.3,
                    timeframe: str = 'daily') -> MACDVResult:
    """
    便捷函數: 計算MACD-V指標
    
    Args:
        df: K線數據
        fast: 快線週期
        slow: 慢線週期
        signal: 信號線週期
        volume_weight: 成交量加權係數
        timeframe: 時間框架
        
    Returns:
        MACDVResult: MACD-V計算結果
    """
    calculator = MACDVCalculator(fast, slow, signal, volume_weight)
    return calculator.calculate(df, timeframe)


def get_macdv_signal_summary(macdv_result: MACDVResult) -> Dict[str, Any]:
    """
    獲取MACD-V信號摘要
    
    Args:
        macdv_result: MACD-V計算結果
        
    Returns:
        Dict: 信號摘要
    """
    return {
        "signal": macdv_result.current_signal.value,
        "strength": round(macdv_result.signal_strength, 2),
        "volume_confirmed": macdv_result.volume_confirmation.iloc[-1] > 0.6 if not macdv_result.volume_confirmation.empty else False,
        "macd_above_signal": macdv_result.macd_line.iloc[-1] > macdv_result.signal_line.iloc[-1] if not macdv_result.macd_line.empty else False,
        "macdv_above_signal": macdv_result.macd_v_line.iloc[-1] > macdv_result.signal_v_line.iloc[-1] if not macdv_result.macd_v_line.empty else False
    }


# ============ 單元測試 ============

if __name__ == "__main__":
    print("MACD-V Calculator 單元測試")
    print("=" * 60)
    
    # 創建測試數據
    np.random.seed(42)
    
    def generate_test_data(days: int, trend: str = "up") -> pd.DataFrame:
        """生成測試數據"""
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
    
    # 測試1: 單一時間框架計算
    print("\n測試1: 單一時間框架MACD-V計算")
    df = generate_test_data(200, "up")
    calculator = MACDVCalculator()
    result = calculator.calculate(df, 'daily')
    
    print(f"  標準MACD: {result.macd_line.iloc[-1]:.4f}")
    print(f"  MACD-V: {result.macd_v_line.iloc[-1]:.4f}")
    print(f"  成交量確認度: {result.volume_confirmation.iloc[-1]:.2%}")
    print(f"  信號強度: {result.signal_strength:.2f}")
    print(f"  當前信號: {result.current_signal.value}")
    
    # 測試2: 多時間框架計算
    print("\n測試2: 多時間框架MACD-V計算")
    monthly_df = generate_test_data(60, "up")
    weekly_df = generate_test_data(100, "up")
    daily_df = generate_test_data(200, "up")
    
    mtf_results = calculator.calculate_multi_timeframe(monthly_df, weekly_df, daily_df)
    
    for tf, tf_result in mtf_results.items():
        print(f"  {tf}: 信號={tf_result.macdv_result.current_signal.value}, "
              f"強度={tf_result.macdv_result.signal_strength:.2f}, "
              f"趨勢一致性={tf_result.trend_alignment:.1f}")
    
    # 測試3: 便捷函數
    print("\n測試3: 便捷函數測試")
    result2 = calculate_macdv(df)
    summary = get_macdv_signal_summary(result2)
    print(f"  信號摘要: {summary}")
    
    print("\n" + "=" * 60)
    print("所有測試完成!")
