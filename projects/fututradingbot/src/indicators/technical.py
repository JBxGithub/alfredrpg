"""
富途交易機器人 - 技術指標模組
Technical Indicators Module for Futu Trading Bot

提供常用技術指標計算：
- MACD (DIF, DEA, MACD柱)
- BOLL (布林帶: 上軌、中軌、下軌)
- EMA (指數移動平均線 - 多週期)
- VMACD (量價MACD)
- RSI (相對強弱指標)
- 成交量分析
- K線形態分析 (整合)

Author: FutuTradingBot AI Research Team
Version: 1.1.0
"""

import pandas as pd
import numpy as np
from typing import Optional, Union, List, Dict, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# 導入K線形態分析
from src.indicators.candlestick_patterns import (
    CandlestickAnalyzer, CandlestickPattern, PatternType
)


class TrendDirection(Enum):
    """趨勢方向枚舉"""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


@dataclass
class MACDResult:
    """MACD計算結果"""
    dif: pd.Series      # 差離值 (快線 - 慢線)
    dea: pd.Series      # 訊號線 (DIF的EMA)
    macd: pd.Series     # MACD柱 (DIF - DEA) * 2
    
    def to_dataframe(self) -> pd.DataFrame:
        """轉換為DataFrame"""
        return pd.DataFrame({
            'DIF': self.dif,
            'DEA': self.dea,
            'MACD': self.macd
        })


@dataclass
class BOLLResult:
    """布林帶計算結果"""
    upper: pd.Series    # 上軌 (中軌 + 2 * 標準差)
    middle: pd.Series   # 中軌 (移動平均線)
    lower: pd.Series    # 下軌 (中軌 - 2 * 標準差)
    bandwidth: pd.Series  # 帶寬 (上軌 - 下軌) / 中軌
    
    def to_dataframe(self) -> pd.DataFrame:
        """轉換為DataFrame"""
        return pd.DataFrame({
            'UPPER': self.upper,
            'MIDDLE': self.middle,
            'LOWER': self.lower,
            'BANDWIDTH': self.bandwidth
        })


@dataclass
class EMAResult:
    """EMA計算結果 (多週期)"""
    ema_5: pd.Series    # 5日EMA
    ema_10: pd.Series   # 10日EMA
    ema_20: pd.Series   # 20日EMA
    ema_60: pd.Series   # 60日EMA
    
    def to_dataframe(self) -> pd.DataFrame:
        """轉換為DataFrame"""
        return pd.DataFrame({
            'EMA5': self.ema_5,
            'EMA10': self.ema_10,
            'EMA20': self.ema_20,
            'EMA60': self.ema_60
        })


@dataclass
class VMACDResult:
    """量價MACD計算結果"""
    dif: pd.Series      # 量價DIF
    dea: pd.Series      # 量價DEA
    vmacd: pd.Series    # 量價MACD柱
    
    def to_dataframe(self) -> pd.DataFrame:
        """轉換為DataFrame"""
        return pd.DataFrame({
            'VMACD_DIF': self.dif,
            'VMACD_DEA': self.dea,
            'VMACD': self.vmacd
        })


@dataclass
class RSIResult:
    """RSI計算結果"""
    rsi_6: pd.Series    # 6日RSI
    rsi_12: pd.Series   # 12日RSI
    rsi_24: pd.Series   # 24日RSI
    
    def to_dataframe(self) -> pd.DataFrame:
        """轉換為DataFrame"""
        return pd.DataFrame({
            'RSI6': self.rsi_6,
            'RSI12': self.rsi_12,
            'RSI24': self.rsi_24
        })


@dataclass
class VolumeAnalysisResult:
    """成交量分析結果"""
    volume: pd.Series           # 成交量
    volume_ma_5: pd.Series      # 5日均量
    volume_ma_10: pd.Series     # 10日均量
    volume_ma_20: pd.Series     # 20日均量
    volume_ratio: pd.Series     # 量比 (當日成交量 / 前5日平均成交量)
    obv: pd.Series              # OBV能量潮
    
    def to_dataframe(self) -> pd.DataFrame:
        """轉換為DataFrame"""
        return pd.DataFrame({
            'VOLUME': self.volume,
            'VOL_MA5': self.volume_ma_5,
            'VOL_MA10': self.volume_ma_10,
            'VOL_MA20': self.volume_ma_20,
            'VOL_RATIO': self.volume_ratio,
            'OBV': self.obv
        })


@dataclass
class CandlestickSignal:
    """K線形態信號結果"""
    pattern_type: str
    is_bullish: bool
    is_bearish: bool
    overall_score: float
    confidence: float
    description: str


class TechnicalIndicators:
    """
    技術指標計算類
    
    使用pandas實現常用技術指標計算
    支援股票K線數據輸入
    整合K線形態分析功能
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        初始化技術指標計算器
        
        Args:
            df: DataFrame包含K線數據，必須包含以下列：
                - close: 收盤價
                - high: 最高價
                - low: 最低價
                - open: 開盤價
                - volume: 成交量
        """
        self.df = df.copy()
        self._validate_data()
        self.candlestick_analyzer = CandlestickAnalyzer()
    
    def _validate_data(self) -> None:
        """驗證輸入數據格式"""
        required_columns = ['close', 'high', 'low', 'open', 'volume']
        missing = [col for col in required_columns if col not in self.df.columns]
        if missing:
            raise ValueError(f"缺少必要欄位: {missing}")
    
    def calculate_macd(
        self, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> MACDResult:
        """
        計算MACD指標
        
        Args:
            fast: 快線週期 (默認12)
            slow: 慢線週期 (默認26)
            signal: 訊號線週期 (默認9)
            
        Returns:
            MACDResult包含DIF、DEA、MACD柱
        """
        close = self.df['close']
        
        # 計算快線和慢線的EMA
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        
        # DIF = 快線 - 慢線
        dif = ema_fast - ema_slow
        
        # DEA = DIF的EMA
        dea = dif.ewm(span=signal, adjust=False).mean()
        
        # MACD柱 = (DIF - DEA) * 2
        macd = (dif - dea) * 2
        
        return MACDResult(dif=dif, dea=dea, macd=macd)
    
    def calculate_boll(
        self, 
        period: int = 20, 
        std_dev: float = 2.0
    ) -> BOLLResult:
        """
        計算布林帶指標
        
        Args:
            period: 移動平均週期 (默認20)
            std_dev: 標準差倍數 (默認2.0)
            
        Returns:
            BOLLResult包含上軌、中軌、下軌、帶寬
        """
        close = self.df['close']
        
        # 中軌 = 移動平均線
        middle = close.rolling(window=period).mean()
        
        # 標準差
        std = close.rolling(window=period).std()
        
        # 上軌 = 中軌 + 2 * 標準差
        upper = middle + std_dev * std
        
        # 下軌 = 中軌 - 2 * 標準差
        lower = middle - std_dev * std
        
        # 帶寬 = (上軌 - 下軌) / 中軌
        bandwidth = (upper - lower) / middle
        
        return BOLLResult(upper=upper, middle=middle, lower=lower, bandwidth=bandwidth)
    
    def calculate_ema(
        self, 
        periods: Optional[List[int]] = None
    ) -> EMAResult:
        """
        計算多週期EMA
        
        Args:
            periods: EMA週期列表，默認[5, 10, 20, 60]
            
        Returns:
            EMAResult包含各週期EMA
        """
        if periods is None:
            periods = [5, 10, 20, 60]
        
        close = self.df['close']
        
        # 計算各週期EMA
        ema_dict = {}
        for period in periods:
            ema_dict[f'ema_{period}'] = close.ewm(span=period, adjust=False).mean()
        
        return EMAResult(
            ema_5=ema_dict.get('ema_5', pd.Series(np.nan, index=close.index)),
            ema_10=ema_dict.get('ema_10', pd.Series(np.nan, index=close.index)),
            ema_20=ema_dict.get('ema_20', pd.Series(np.nan, index=close.index)),
            ema_60=ema_dict.get('ema_60', pd.Series(np.nan, index=close.index))
        )
    
    def calculate_vmacd(
        self, 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> VMACDResult:
        """
        計算量價MACD指標
        
        使用成交量加權價格計算
        
        Args:
            fast: 快線週期 (默認12)
            slow: 慢線週期 (默認26)
            signal: 訊號線週期 (默認9)
            
        Returns:
            VMACDResult包含量價DIF、DEA、VMACD柱
        """
        close = self.df['close']
        volume = self.df['volume']
        
        # 計算成交量加權價格 (VWAP-like)
        vol_price = close * volume
        
        # 計算快線和慢線的成交量加權EMA
        vol_ema_fast = vol_price.ewm(span=fast, adjust=False).mean()
        vol_ema_slow = vol_price.ewm(span=slow, adjust=False).mean()
        
        # 量價DIF
        dif = vol_ema_fast - vol_ema_slow
        
        # 量價DEA
        dea = dif.ewm(span=signal, adjust=False).mean()
        
        # 量價MACD柱
        vmacd = (dif - dea) * 2
        
        return VMACDResult(dif=dif, dea=dea, vmacd=vmacd)
    
    def calculate_rsi(
        self, 
        periods: Optional[List[int]] = None
    ) -> RSIResult:
        """
        計算RSI相對強弱指標
        
        Args:
            periods: RSI週期列表，默認[6, 12, 24]
            
        Returns:
            RSIResult包含各週期RSI
        """
        if periods is None:
            periods = [6, 12, 24]
        
        close = self.df['close']
        
        # 計算價格變化
        delta = close.diff()
        
        # 分離上漲和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        rsi_dict = {}
        for period in periods:
            # 計算平均上漲和下跌
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # 計算相對強度 (RS)
            rs = avg_gain / avg_loss
            
            # 計算RSI
            rsi = 100 - (100 / (1 + rs))
            rsi_dict[f'rsi_{period}'] = rsi
        
        return RSIResult(
            rsi_6=rsi_dict.get('rsi_6', pd.Series(np.nan, index=close.index)),
            rsi_12=rsi_dict.get('rsi_12', pd.Series(np.nan, index=close.index)),
            rsi_24=rsi_dict.get('rsi_24', pd.Series(np.nan, index=close.index))
        )
    
    def calculate_volume_analysis(self) -> VolumeAnalysisResult:
        """
        計算成交量分析指標
        
        Returns:
            VolumeAnalysisResult包含成交量相關指標
        """
        volume = self.df['volume']
        close = self.df['close']
        
        # 成交量移動平均
        volume_ma_5 = volume.rolling(window=5).mean()
        volume_ma_10 = volume.rolling(window=10).mean()
        volume_ma_20 = volume.rolling(window=20).mean()
        
        # 量比 = 當日成交量 / 前5日平均成交量
        volume_ratio = volume / volume_ma_5.shift(1)
        
        # OBV能量潮計算
        obv = pd.Series(index=volume.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return VolumeAnalysisResult(
            volume=volume,
            volume_ma_5=volume_ma_5,
            volume_ma_10=volume_ma_10,
            volume_ma_20=volume_ma_20,
            volume_ratio=volume_ratio,
            obv=obv
        )
    
    def detect_candlestick_patterns(
        self,
        idx: int = -1
    ) -> Optional[CandlestickSignal]:
        """
        檢測K線形態
        
        Args:
            idx: 檢測的索引位置，默認為最後一根K線
            
        Returns:
            CandlestickSignal or None
        """
        if idx < 0:
            idx = len(self.df) + idx
        
        pattern = self.candlestick_analyzer.detect_at_index(self.df, idx)
        
        if pattern is None or pattern.pattern_type == PatternType.NONE:
            return None
        
        return CandlestickSignal(
            pattern_type=pattern.pattern_type.value,
            is_bullish=pattern.is_bullish(),
            is_bearish=pattern.is_bearish(),
            overall_score=pattern.overall_score,
            confidence=pattern.confidence,
            description=pattern.description
        )
    
    def get_candlestick_summary(self) -> Dict[str, Any]:
        """
        獲取K線形態摘要
        
        Returns:
            K線形態摘要字典
        """
        summary = self.candlestick_analyzer.get_signal_summary(self.df)
        
        return {
            'has_signal': summary.get('has_signal', False),
            'bullish_count': summary.get('bullish_count', 0),
            'bearish_count': summary.get('bearish_count', 0),
            'avg_score': summary.get('avg_score', 0),
            'latest_pattern': summary.get('latest_pattern').pattern_type.value 
                if summary.get('latest_pattern') else None
        }
    
    def calculate_all(self) -> pd.DataFrame:
        """
        計算所有技術指標 (包含K線形態)
        
        Returns:
            DataFrame包含所有技術指標
        """
        # 計算各指標
        macd = self.calculate_macd()
        boll = self.calculate_boll()
        ema = self.calculate_ema()
        vmacd = self.calculate_vmacd()
        rsi = self.calculate_rsi()
        volume = self.calculate_volume_analysis()
        
        # 合併所有指標
        result = pd.concat([
            self.df,
            macd.to_dataframe(),
            boll.to_dataframe(),
            ema.to_dataframe(),
            vmacd.to_dataframe(),
            rsi.to_dataframe(),
            volume.to_dataframe()
        ], axis=1)
        
        # 添加K線形態列
        patterns = self.candlestick_analyzer.analyze(self.df)
        if patterns:
            pattern_scores = [0.0] * len(self.df)
            for p in patterns:
                if 0 <= p.index < len(pattern_scores):
                    pattern_scores[p.index] = p.overall_score if p.is_bullish() else -p.overall_score
            result['CANDLESTICK_SIGNAL'] = pattern_scores
        
        return result
    
    def get_signal_summary(self, n: int = 5) -> Dict[str, Union[str, float]]:
        """
        獲取最新n天的信號摘要
        
        Args:
            n: 取最近n天的數據
            
        Returns:
            信號摘要字典
        """
        macd = self.calculate_macd()
        boll = self.calculate_boll()
        rsi = self.calculate_rsi()
        volume = self.calculate_volume_analysis()
        
        latest_idx = -1
        
        summary = {
            'macd_signal': self._get_macd_signal(macd, latest_idx),
            'boll_position': self._get_boll_position(boll, latest_idx),
            'rsi_6': round(rsi.rsi_6.iloc[latest_idx], 2),
            'rsi_12': round(rsi.rsi_12.iloc[latest_idx], 2),
            'rsi_24': round(rsi.rsi_24.iloc[latest_idx], 2),
            'volume_ratio': round(volume.volume_ratio.iloc[latest_idx], 2),
            'obv_trend': self._get_obv_trend(volume, n)
        }
        
        return summary
    
    def _get_macd_signal(self, macd: MACDResult, idx: int) -> str:
        """獲取MACD信號"""
        dif = macd.dif.iloc[idx]
        dea = macd.dea.iloc[idx]
        macd_val = macd.macd.iloc[idx]
        
        if dif > dea and macd_val > 0:
            return "bullish"  # 看多
        elif dif < dea and macd_val < 0:
            return "bearish"  # 看空
        else:
            return "neutral"  # 中性
    
    def _get_boll_position(self, boll: BOLLResult, idx: int) -> str:
        """獲取布林帶位置"""
        close = self.df['close'].iloc[idx]
        upper = boll.upper.iloc[idx]
        lower = boll.lower.iloc[idx]
        middle = boll.middle.iloc[idx]
        
        if close >= upper:
            return "upper_band"  # 觸及上軌
        elif close <= lower:
            return "lower_band"  # 觸及下軌
        elif close > middle:
            return "above_middle"  # 中軌上方
        else:
            return "below_middle"  # 中軌下方
    
    def _get_obv_trend(self, volume: VolumeAnalysisResult, n: int) -> str:
        """獲取OBV趨勢"""
        obv = volume.obv
        if len(obv) < n:
            return "insufficient_data"
        
        recent_obv = obv.iloc[-n:]
        if recent_obv.iloc[-1] > recent_obv.iloc[0]:
            return "rising"  # 上升
        elif recent_obv.iloc[-1] < recent_obv.iloc[0]:
            return "falling"  # 下降
        else:
            return "flat"  # 持平


def calculate_support_resistance(
    df: pd.DataFrame, 
    window: int = 20
) -> Tuple[pd.Series, pd.Series]:
    """
    計算支撐位和阻力位
    
    Args:
        df: K線數據DataFrame
        window: 計算窗口
        
    Returns:
        (支撐位Series, 阻力位Series)
    """
    high = df['high']
    low = df['low']
    
    # 阻力位 = 滾動最高價
    resistance = high.rolling(window=window).max()
    
    # 支撐位 = 滾動最低價
    support = low.rolling(window=window).min()
    
    return support, resistance


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    計算ATR (平均真實波幅)
    
    Args:
        df: K線數據DataFrame
        period: 計算週期
        
    Returns:
        ATR序列
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # 計算真實波幅
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # 計算ATR
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_zscore(
    series: pd.Series, 
    period: int = 60,
    min_periods: int = None
) -> pd.Series:
    """
    計算Z-Score (標準分數)
    
    Z-Score = (當前價 - 移動平均價) / 標準差
    用於識別價格偏離程度，均值回歸策略核心指標
    
    Args:
        series: 價格序列 (通常為收盤價)
        period: 計算窗口 (默認60日)
        min_periods: 最小有效數據點數 (默認為 period 的一半)
        
    Returns:
        Z-Score序列
        
    Example:
        >>> zscore = calculate_zscore(df['close'], period=60)
        >>> # Z-Score > 2.0: 價格顯著偏高 (超買)
        >>> # Z-Score < -2.0: 價格顯著偏低 (超賣)
        >>> # Z-Score 接近 0: 價格接近均值
    """
    # 如果未指定 min_periods，使用 period 的一半
    if min_periods is None:
        min_periods = max(period // 2, 1)
    
    # 確保 min_periods 不超過 period
    min_periods = min(min_periods, period)
    
    # 計算移動平均
    ma = series.rolling(window=period, min_periods=min_periods).mean()
    
    # 計算標準差
    std = series.rolling(window=period, min_periods=min_periods).std()
    
    # 計算Z-Score
    zscore = (series - ma) / std
    
    return zscore


@dataclass
class ZScoreResult:
    """Z-Score計算結果"""
    zscore: pd.Series           # Z-Score值
    ma: pd.Series               # 移動平均線
    std: pd.Series              # 標準差
    upper_threshold: float      # 上閾值 (默認2.0)
    lower_threshold: float      # 下閾值 (默認-2.0)
    
    def to_dataframe(self) -> pd.DataFrame:
        """轉換為DataFrame"""
        return pd.DataFrame({
            'ZScore': self.zscore,
            'MA': self.ma,
            'Std': self.std
        })
    
    def get_signal(self) -> pd.Series:
        """
        獲取交易信號
        
        Returns:
            信號序列: 1 (超賣/做多), -1 (超買/做空), 0 (觀望)
        """
        signal = pd.Series(0, index=self.zscore.index)
        signal[self.zscore < self.lower_threshold] = 1   # 超賣，做多
        signal[self.zscore > self.upper_threshold] = -1  # 超買，做空
        return signal


def calculate_zscore_advanced(
    df: pd.DataFrame,
    price_col: str = 'close',
    period: int = 60,
    upper_threshold: float = 2.0,
    lower_threshold: float = -2.0
) -> ZScoreResult:
    """
    高級Z-Score計算 (含信號生成)
    
    Args:
        df: K線數據DataFrame
        price_col: 價格列名
        period: 計算窗口
        upper_threshold: 上閾值 (超買)
        lower_threshold: 下閾值 (超賣)
        
    Returns:
        ZScoreResult對象
        
    Example:
        >>> result = calculate_zscore_advanced(df, period=60)
        >>> signals = result.get_signal()
        >>> # signals == 1: 做多信號
        >>> # signals == -1: 做空信號
    """
    price = df[price_col]
    
    # 動態計算 min_periods（確保不超過 period）
    min_periods = min(max(period // 2, 1), period)
    
    # 計算Z-Score
    zscore = calculate_zscore(price, period=period, min_periods=min_periods)
    
    # 計算MA和Std（使用相同的 min_periods）
    ma = price.rolling(window=period, min_periods=min_periods).mean()
    std = price.rolling(window=period, min_periods=min_periods).std()
    
    return ZScoreResult(
        zscore=zscore,
        ma=ma,
        std=std,
        upper_threshold=upper_threshold,
        lower_threshold=lower_threshold
    )
