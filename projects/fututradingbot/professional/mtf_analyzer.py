"""
FutuTradingBot 多時間框架 (MTF) 分析模組
月線 -> 周線 -> 日線 三層過濾
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from indicators import TechnicalIndicators


class MTFAnalyzer:
    """多時間框架分析器"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def analyze_monthly(self, data: pd.DataFrame) -> Dict:
        """
        月線分析 - 最終趨勢濾網 (放寬條件)
        
        Args:
            data: 月線數據
            
        Returns:
            dict with trend direction and strength
        """
        if len(data) < 20:
            return {'valid': False, 'reason': 'Insufficient monthly data'}
        
        # 計算指標
        df = self.indicators.get_all_indicators(data)
        latest = df.iloc[-1]
        
        # 趨勢判斷
        trend_direction = self.indicators.check_trend_direction(
            latest['plus_di'], 
            latest['minus_di']
        )
        
        trend_strength = self.indicators.check_trend_strength(latest['adx'])
        
        # EMA 排列
        ema_alignment = self.indicators.check_ema_alignment(
            latest['ema_9'],
            latest['ema_20'],
            latest['ema_50']
        )
        
        # 月線趨勢確認 (放寬: 只需價格在EMA20同側)
        monthly_trend = {
            'valid': True,
            'direction': trend_direction,
            'strength': trend_strength,
            'adx': latest['adx'],
            'ema_alignment': ema_alignment,
            'price_above_ema20': latest['Close'] > latest['ema_20'],
            'signal': 'bullish' if (latest['Close'] > latest['ema_20'] and 
                                   trend_direction == 'bullish') else 'bearish' if (latest['Close'] < latest['ema_20'] and 
                                                                                 trend_direction == 'bearish') else 'neutral'
        }
        
        return monthly_trend
    
    def analyze_weekly(self, data: pd.DataFrame) -> Dict:
        """
        周線分析 - 中級趨勢確認 (改為參考而非必須)
        
        Args:
            data: 周線數據
            
        Returns:
            dict with trend analysis
        """
        if len(data) < 10:
            return {'valid': False, 'reason': 'Insufficient weekly data'}
        
        df = self.indicators.get_all_indicators(data)
        latest = df.iloc[-1]
        
        # 趨勢判斷
        trend_direction = self.indicators.check_trend_direction(
            latest['plus_di'],
            latest['minus_di']
        )
        
        trend_strength = self.indicators.check_trend_strength(latest['adx'])
        
        # EMA 排列
        ema_alignment = self.indicators.check_ema_alignment(
            latest['ema_9'],
            latest['ema_20'],
            latest['ema_50']
        )
        
        # 周線條件：改為參考 (只需價格在EMA20同側)
        weekly_trend = {
            'valid': True,
            'direction': trend_direction,
            'strength': trend_strength,
            'adx': latest['adx'],
            'ema_alignment': ema_alignment,
            'price_above_ema20': latest['Close'] > latest['ema_20'],
            'adx_above_20': latest['adx'] > 20,
            # 與月線一致性檢查 (放寬)
            'signal': 'bullish' if (latest['Close'] > latest['ema_20'] and 
                                   trend_direction == 'bullish') else 'bearish' if (latest['Close'] < latest['ema_20'] and 
                                                                                 trend_direction == 'bearish') else 'neutral'
        }
        
        return weekly_trend
    
    def analyze_daily(self, data: pd.DataFrame) -> Dict:
        """
        日線分析 - 入場執行層 (放寬條件 + 分層信號)
        
        Args:
            data: 日線數據
            
        Returns:
            dict with detailed signals and signal strength
        """
        if len(data) < 50:
            return {'valid': False, 'reason': 'Insufficient daily data'}
        
        df = self.indicators.get_all_indicators(data)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # 計算所有條件
        daily_analysis = {
            'valid': True,
            'price': latest['Close'],
            'adx': latest['adx'],
            'adx_rising': latest['adx'] > prev['adx'],
            'plus_di': latest['plus_di'],
            'minus_di': latest['minus_di'],
            'macd': latest['macd'],
            'macd_signal': latest['macd_signal'],
            'macd_histogram': latest['macd_histogram'],
            'macd_golden_cross': prev['macd'] < prev['macd_signal'] and latest['macd'] > latest['macd_signal'],
            'macd_death_cross': prev['macd'] > prev['macd_signal'] and latest['macd'] < latest['macd_signal'],
            'macd_bullish': latest['macd'] > latest['macd_signal'] and latest['macd'] > 0,
            'macd_bearish': latest['macd'] < latest['macd_signal'] and latest['macd'] < 0,
            'ema_9': latest['ema_9'],
            'ema_20': latest['ema_20'],
            'ema_50': latest['ema_50'],
            'price_above_ema20': latest['Close'] > latest['ema_20'],
            'volume_signal': latest['volume_signal'],
            'rsi': latest['rsi'],
            'boll_position': self.indicators.check_bollinger_position(
                latest['Close'],
                latest['boll_upper'],
                latest['boll_lower'],
                latest['boll_middle']
            ),
            'atr': latest['atr']
        }
        
        # ===== 放寬後的多頭條件 =====
        # 核心條件 (必須)
        long_core = {
            'adx_above_20': latest['adx'] > 20,  # 放寬至20
            'plus_di_above_minus': latest['plus_di'] > latest['minus_di'],
            'price_above_ema20': latest['Close'] > latest['ema_20'],
        }
        
        # 次要條件 (加分)
        long_secondary = {
            'adx_above_25': latest['adx'] > 25,
            'adx_rising': latest['adx'] > prev['adx'],
            'macd_golden_cross': daily_analysis['macd_golden_cross'],
            'macd_bullish': daily_analysis['macd_bullish'],
            'volume_spike': latest['volume_signal'],
            'rsi_not_overbought': latest['rsi'] < 70
        }
        
        # 放寬後的空頭條件
        short_core = {
            'adx_above_20': latest['adx'] > 20,
            'minus_di_above_plus': latest['minus_di'] > latest['plus_di'],
            'price_below_ema20': latest['Close'] < latest['ema_20'],
        }
        
        short_secondary = {
            'adx_above_25': latest['adx'] > 25,
            'adx_rising': latest['adx'] > prev['adx'],
            'macd_death_cross': daily_analysis['macd_death_cross'],
            'macd_bearish': daily_analysis['macd_bearish'],
            'volume_spike': latest['volume_signal'],
            'rsi_not_oversold': latest['rsi'] > 30
        }
        
        # 計算分數
        long_core_score = sum(long_core.values())
        long_secondary_score = sum(long_secondary.values())
        short_core_score = sum(short_core.values())
        short_secondary_score = sum(short_secondary.values())
        
        daily_analysis['long_core'] = long_core
        daily_analysis['long_secondary'] = long_secondary
        daily_analysis['short_core'] = short_core
        daily_analysis['short_secondary'] = short_secondary
        
        daily_analysis['long_core_score'] = long_core_score
        daily_analysis['long_secondary_score'] = long_secondary_score
        daily_analysis['short_core_score'] = short_core_score
        daily_analysis['short_secondary_score'] = short_secondary_score
        
        # 舊版兼容
        daily_analysis['all_long_conditions_met'] = long_core_score == len(long_core) and long_secondary_score >= 4
        daily_analysis['all_short_conditions_met'] = short_core_score == len(short_core) and short_secondary_score >= 4
        
        return daily_analysis
    
    def get_mtf_signal(self, monthly_data: pd.DataFrame, 
                      weekly_data: pd.DataFrame, 
                      daily_data: pd.DataFrame) -> Dict:
        """
        綜合 MTF 信號
        
        規則:
        1. 月線: 最終趨勢濾網 (絕不逆月線大勢)
        2. 周線: ADX > 20 + 價格在20EMA同側
        3. 日線: 全部條件滿足才入場
        
        Returns:
            dict with final signal
        """
        monthly = self.analyze_monthly(monthly_data)
        weekly = self.analyze_weekly(weekly_data)
        daily = self.analyze_daily(daily_data)
        
        signal = {
            'monthly': monthly,
            'weekly': weekly,
            'daily': daily,
            'valid': monthly.get('valid', False) and weekly.get('valid', False) and daily.get('valid', False)
        }
        
        if not signal['valid']:
            signal['final_signal'] = 'invalid'
            signal['reason'] = 'Insufficient data'
            return signal
        
        # ===== MTF 綜合判斷 (放寬條件 + 分層信號) =====
        
        # 獲取日線分數
        long_core_score = daily.get('long_core_score', 0)
        long_secondary_score = daily.get('long_secondary_score', 0)
        short_core_score = daily.get('short_core_score', 0)
        short_secondary_score = daily.get('short_secondary_score', 0)
        
        # 強信號: 月線多頭 + 周線非空頭 + 日線核心條件全滿足 + 次要條件>=3
        if (monthly['signal'] == 'bullish' and 
            weekly['signal'] != 'bearish' and 
            long_core_score == 3 and 
            long_secondary_score >= 3):
            signal['final_signal'] = 'long'
            signal['strength'] = 'strong'
            signal['position_size'] = 0.95  # 滿倉
        
        # 中信號: 月線多頭 + 日線核心條件全滿足
        elif (monthly['signal'] == 'bullish' and 
              long_core_score == 3):
            signal['final_signal'] = 'long'
            signal['strength'] = 'medium'
            signal['position_size'] = 0.70  # 7成倉
        
        # 弱信號: 月線多頭 + 日線核心條件>=2
        elif (monthly['signal'] == 'bullish' and 
              long_core_score >= 2):
            signal['final_signal'] = 'long'
            signal['strength'] = 'weak'
            signal['position_size'] = 0.50  # 5成倉
        
        # 空頭強信號
        elif (monthly['signal'] == 'bearish' and 
              weekly['signal'] != 'bullish' and 
              short_core_score == 3 and 
              short_secondary_score >= 3):
            signal['final_signal'] = 'short'
            signal['strength'] = 'strong'
            signal['position_size'] = 0.95
        
        # 空頭中信號
        elif (monthly['signal'] == 'bearish' and 
              short_core_score == 3):
            signal['final_signal'] = 'short'
            signal['strength'] = 'medium'
            signal['position_size'] = 0.70
        
        # 空頭弱信號
        elif (monthly['signal'] == 'bearish' and 
              short_core_score >= 2):
            signal['final_signal'] = 'short'
            signal['strength'] = 'weak'
            signal['position_size'] = 0.50
        
        # 觀望
        else:
            signal['final_signal'] = 'neutral'
            signal['strength'] = 'none'
            
            # 分析原因
            reasons = []
            if monthly['signal'] == 'neutral':
                reasons.append(f"月線趨勢不明")
            elif monthly['signal'] == 'bullish' and long_core_score < 2:
                reasons.append(f"日線多頭核心條件不足 ({long_core_score}/3)")
            elif monthly['signal'] == 'bearish' and short_core_score < 2:
                reasons.append(f"日線空頭核心條件不足 ({short_core_score}/3)")
            
            signal['reason'] = '; '.join(reasons) if reasons else '等待更好入場時機'
        
        return signal
    
    def resample_data(self, data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        重採樣數據到不同時間框架
        
        Args:
            data: 原始數據 (日線)
            timeframe: 'W' (周線) 或 'M' (月線)
            
        Returns:
            resampled DataFrame
        """
        if timeframe == 'W':
            # 周線: 每周最後一個交易日
            resampled = data.resample('W').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
        elif timeframe == 'M':
            # 月線: 每月最後一個交易日
            resampled = data.resample('ME').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
        else:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        return resampled


if __name__ == '__main__':
    print("MTFAnalyzer 模組已載入")
    print("時間框架: 月線 -> 周線 -> 日線")
    print("核心規則: 絕不逆月線大勢")
