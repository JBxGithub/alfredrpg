"""
FutuTradingBot 專業級技術指標模組
包含: ADX, +DI/-DI, MACD, EMA, BOLL, VIX, Volume (MACDV)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple


class TechnicalIndicators:
    """技術指標計算類"""
    
    @staticmethod
    def calculate_adx(data: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
        """
        計算 ADX (Average Directional Index)
        
        Args:
            data: DataFrame with 'High', 'Low', 'Close'
            period: ADX 周期 (默認14)
            
        Returns:
            dict with 'adx', 'plus_di', 'minus_di'
        """
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # +DM 和 -DM
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0)
        minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0)
        
        plus_dm = pd.Series(plus_dm, index=data.index)
        minus_dm = pd.Series(minus_dm, index=data.index)
        
        # 平滑處理
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        plus_di = 100 * plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr
        minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr
        
        # DX 和 ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(alpha=1/period, adjust=False).mean()
        
        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }
    
    @staticmethod
    def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """
        計算 MACD
        
        Args:
            data: Close price series
            fast: 快線周期 (默認12)
            slow: 慢線周期 (默認26)
            signal: 信號線周期 (默認9)
            
        Returns:
            dict with 'macd', 'signal', 'histogram'
        """
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_ema(data: pd.Series, periods: list = [9, 20, 50]) -> Dict[str, pd.Series]:
        """
        計算多周期 EMA
        
        Args:
            data: Close price series
            periods: EMA 周期列表 (默認 [9, 20, 50])
            
        Returns:
            dict with 'ema_9', 'ema_20', 'ema_50'
        """
        result = {}
        for period in periods:
            result[f'ema_{period}'] = data.ewm(span=period, adjust=False).mean()
        return result
    
    @staticmethod
    def calculate_bollinger(data: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """
        計算布林帶 (Bollinger Bands)
        
        Args:
            data: Close price series
            period: 周期 (默認20)
            std_dev: 標準差倍數 (默認2)
            
        Returns:
            dict with 'upper', 'middle', 'lower', 'bandwidth', 'percent_b'
        """
        middle = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        # 帶寬 (Bandwidth)
        bandwidth = (upper - lower) / middle
        
        # %B 指標
        percent_b = (data - lower) / (upper - lower)
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'bandwidth': bandwidth,
            'percent_b': percent_b
        }
    
    @staticmethod
    def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        計算 ATR (Average True Range)
        
        Args:
            data: DataFrame with 'High', 'Low', 'Close'
            period: ATR 周期 (默認14)
            
        Returns:
            ATR series
        """
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        
        return atr
    
    @staticmethod
    def calculate_volume_signal(data: pd.DataFrame, period: int = 20, threshold: float = 1.5) -> pd.Series:
        """
        計算成交量信號 (MACDV)
        
        Args:
            data: DataFrame with 'Volume'
            period: 平均周期 (默認20)
            threshold: 閾值倍數 (默認1.5)
            
        Returns:
            Boolean series indicating volume spike
        """
        volume_ma = data['Volume'].rolling(window=period).mean()
        volume_signal = data['Volume'] > (volume_ma * threshold)
        return volume_signal
    
    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        計算 RSI
        
        Args:
            data: Close price series
            period: RSI 周期 (默認14)
            
        Returns:
            RSI series
        """
        delta = data.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @classmethod
    def get_all_indicators(cls, data: pd.DataFrame) -> pd.DataFrame:
        """
        計算所有技術指標
        
        Args:
            data: DataFrame with 'Open', 'High', 'Low', 'Close', 'Volume'
            
        Returns:
            DataFrame with all indicators
        """
        df = data.copy()
        
        # ADX
        adx_data = cls.calculate_adx(df)
        df['adx'] = adx_data['adx']
        df['plus_di'] = adx_data['plus_di']
        df['minus_di'] = adx_data['minus_di']
        
        # MACD
        macd_data = cls.calculate_macd(df['Close'])
        df['macd'] = macd_data['macd']
        df['macd_signal'] = macd_data['signal']
        df['macd_histogram'] = macd_data['histogram']
        
        # EMA
        ema_data = cls.calculate_ema(df['Close'])
        df['ema_9'] = ema_data['ema_9']
        df['ema_20'] = ema_data['ema_20']
        df['ema_50'] = ema_data['ema_50']
        
        # Bollinger Bands
        boll_data = cls.calculate_bollinger(df['Close'])
        df['boll_upper'] = boll_data['upper']
        df['boll_middle'] = boll_data['middle']
        df['boll_lower'] = boll_data['lower']
        df['boll_bandwidth'] = boll_data['bandwidth']
        df['boll_percent_b'] = boll_data['percent_b']
        
        # ATR
        df['atr'] = cls.calculate_atr(df)
        
        # Volume Signal
        df['volume_signal'] = cls.calculate_volume_signal(df)
        
        # RSI
        df['rsi'] = cls.calculate_rsi(df['Close'])
        
        return df


class SignalGenerator:
    """交易信號生成器"""
    
    @staticmethod
    def check_trend_strength(adx: float) -> str:
        """
        檢查趨勢強度
        
        Returns:
            'no_trend', 'weak', 'strong', 'extreme'
        """
        if adx < 20:
            return 'no_trend'
        elif adx < 25:
            return 'weak'
        elif adx < 50:
            return 'strong'
        elif adx < 70:
            return 'very_strong'
        else:
            return 'extreme'
    
    @staticmethod
    def check_trend_direction(plus_di: float, minus_di: float) -> str:
        """
        檢查趨勢方向
        
        Returns:
            'bullish', 'bearish', 'neutral'
        """
        if plus_di > minus_di:
            return 'bullish'
        elif minus_di > plus_di:
            return 'bearish'
        else:
            return 'neutral'
    
    @staticmethod
    def check_macd_signal(macd: float, signal: float, prev_macd: float, prev_signal: float) -> str:
        """
        檢查 MACD 信號
        
        Returns:
            'golden_cross', 'death_cross', 'bullish', 'bearish', 'neutral'
        """
        # 金叉
        if prev_macd < prev_signal and macd > signal and macd > 0:
            return 'golden_cross'
        # 死叉
        elif prev_macd > prev_signal and macd < signal and macd < 0:
            return 'death_cross'
        # 多頭
        elif macd > signal and macd > 0:
            return 'bullish'
        # 空頭
        elif macd < signal and macd < 0:
            return 'bearish'
        else:
            return 'neutral'
    
    @staticmethod
    def check_ema_alignment(ema_9: float, ema_20: float, ema_50: float) -> str:
        """
        檢查 EMA 排列
        
        Returns:
            'bullish', 'bearish', 'mixed'
        """
        if ema_9 > ema_20 > ema_50:
            return 'bullish'
        elif ema_9 < ema_20 < ema_50:
            return 'bearish'
        else:
            return 'mixed'
    
    @staticmethod
    def check_bollinger_position(price: float, upper: float, lower: float, middle: float) -> str:
        """
        檢查價格在布林帶位置
        
        Returns:
            'upper', 'upper_middle', 'middle', 'lower_middle', 'lower'
        """
        if price >= upper:
            return 'upper'
        elif price > middle:
            return 'upper_middle'
        elif price == middle:
            return 'middle'
        elif price > lower:
            return 'lower_middle'
        else:
            return 'lower'


if __name__ == '__main__':
    # 測試
    print("TechnicalIndicators 模組已載入")
    print("可用指標: ADX, MACD, EMA, Bollinger, ATR, Volume Signal, RSI")
