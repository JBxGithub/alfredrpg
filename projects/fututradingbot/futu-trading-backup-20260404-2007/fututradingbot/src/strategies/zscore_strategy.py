"""
Z-Score 交易策略模組
整合到 FutuTradingBot 交易系統

策略邏輯:
- Z-Score < -2.0: 超賣信號，做多
- Z-Score > 2.0: 超買信號，做空
- Z-Score 回歸 0: 平倉
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from src.indicators.technical import calculate_zscore_advanced
from src.data.market_data import MarketDataManager


class ZScoreStrategy:
    """
    Z-Score 均值回歸策略
    
    核心邏輯:
    1. 計算 60日 Z-Score
    2. Z-Score < -2.0: 進場做多
    3. Z-Score > 2.0: 進場做空
    4. Z-Score 回歸 0.5 以內: 平倉
    """
    
    def __init__(
        self,
        period: int = 60,
        upper_threshold: float = 1.6,
        lower_threshold: float = -1.6,
        exit_threshold: float = 0.5,
        position_pct: float = 0.5
    ):
        self.period = period
        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold
        self.exit_threshold = exit_threshold
        self.position_pct = position_pct
        
        self.name = "ZScore_MeanReversion"
        self.version = "1.0.0"
        
    def generate_signal(
        self, 
        df: pd.DataFrame,
        price_col: str = 'close'
    ) -> Dict[str, Any]:
        """
        生成交易信號
        
        Args:
            df: K線數據 DataFrame
            price_col: 價格列名
            
        Returns:
            信號字典
        """
        if len(df) < self.period:
            return {
                'signal': 0,
                'signal_text': '數據不足',
                'zscore': None,
                'strength': 0
            }
        
        # 計算 Z-Score
        result = calculate_zscore_advanced(
            df,
            price_col=price_col,
            period=self.period,
            upper_threshold=self.upper_threshold,
            lower_threshold=self.lower_threshold
        )
        
        # 獲取最新值
        latest_zscore = result.zscore.iloc[-1]
        latest_price = df[price_col].iloc[-1]
        latest_ma = result.ma.iloc[-1]
        
        # 判斷信號
        signal = 0
        signal_text = '觀望'
        strength = 0
        
        if pd.isna(latest_zscore):
            return {
                'signal': 0,
                'signal_text': '計算中',
                'zscore': None,
                'strength': 0
            }
        
        # 超賣信號 (做多)
        if latest_zscore < self.lower_threshold:
            signal = 1
            signal_text = '做多'
            strength = min(abs(latest_zscore) / 2.0, 1.0)  # 0-1 強度
            
        # 超買信號 (做空)
        elif latest_zscore > self.upper_threshold:
            signal = -1
            signal_text = '做空'
            strength = min(abs(latest_zscore) / 2.0, 1.0)
            
        # 回歸區間 (平倉)
        elif abs(latest_zscore) < self.exit_threshold:
            signal = 0
            signal_text = '平倉/觀望'
            strength = 0
        
        return {
            'signal': signal,
            'signal_text': signal_text,
            'zscore': round(latest_zscore, 2),
            'price': round(latest_price, 2),
            'ma': round(latest_ma, 2),
            'strength': round(strength, 2),
            'deviation': round((latest_price - latest_ma) / latest_ma * 100, 2),
            'threshold_upper': self.upper_threshold,
            'threshold_lower': self.lower_threshold
        }
    
    def should_enter_long(self, zscore: float) -> bool:
        """判斷是否應該做多進場"""
        return zscore < self.lower_threshold
    
    def should_enter_short(self, zscore: float) -> bool:
        """判斷是否應該做空進場"""
        return zscore > self.upper_threshold
    
    def should_exit(self, zscore: float, direction: str) -> bool:
        """
        判斷是否應該出場
        
        Args:
            zscore: 當前 Z-Score
            direction: 持倉方向 ('long' 或 'short')
            
        Returns:
            是否出場
        """
        if direction == 'long':
            # 做多倉位：Z-Score 回歸到 -0.5 以上
            return zscore > -self.exit_threshold
        elif direction == 'short':
            # 做空倉位：Z-Score 回歸到 0.5 以下
            return zscore < self.exit_threshold
        return False
    
    def get_position_size(self, capital: float, price: float) -> int:
        """
        計算倉位大小
        
        Args:
            capital: 可用資金
            price: 當前價格
            
        Returns:
            股數
        """
        position_value = capital * self.position_pct
        qty = int(position_value / price)
        return max(qty, 0)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略資訊"""
        return {
            'name': self.name,
            'version': self.version,
            'period': self.period,
            'upper_threshold': self.upper_threshold,
            'lower_threshold': self.lower_threshold,
            'exit_threshold': self.exit_threshold,
            'position_pct': self.position_pct
        }


class ZScoreRealtimeTrader:
    """
    Z-Score 實時交易器
    
    整合 MarketDataManager 進行實時交易
    """
    
    def __init__(
        self,
        strategy: Optional[ZScoreStrategy] = None,
        market_data: Optional[MarketDataManager] = None
    ):
        self.strategy = strategy or ZScoreStrategy()
        self.md = market_data or MarketDataManager()
        self.position = None  # 當前持倉
        
    def check_signal(self, code: str) -> Dict[str, Any]:
        """
        檢查交易信號
        
        Args:
            code: 股票代碼
            
        Returns:
            完整交易信號資訊
        """
        # 獲取最新數據
        df = self.md.get_latest_data(code)
        if df is None or df.empty:
            return {
                'code': code,
                'error': '無數據',
                'signal': 0
            }
        
        # 生成信號
        signal_data = self.strategy.generate_signal(df)
        signal_data['code'] = code
        signal_data['timestamp'] = datetime.now().isoformat()
        
        # 添加持倉建議
        if self.position is None:
            signal_data['action'] = '可開新倉'
        elif self.position['code'] == code:
            signal_data['action'] = '持倉中'
            # 檢查是否應該平倉
            if self.strategy.should_exit(signal_data['zscore'], self.position['direction']):
                signal_data['action'] = '建議平倉'
        else:
            signal_data['action'] = '觀望'
        
        return signal_data
    
    def execute_signal(self, signal_data: Dict[str, Any]) -> str:
        """
        執行交易信號
        
        Args:
            signal_data: 信號數據
            
        Returns:
            執行結果描述
        """
        signal = signal_data.get('signal', 0)
        code = signal_data.get('code', '')
        
        if signal == 1 and self.position is None:
            # 開做多倉
            self.position = {
                'code': code,
                'direction': 'long',
                'entry_price': signal_data['price'],
                'entry_time': datetime.now()
            }
            return f"做多 {code} @ ${signal_data['price']}"
            
        elif signal == -1 and self.position is None:
            # 開做空倉
            self.position = {
                'code': code,
                'direction': 'short',
                'entry_price': signal_data['price'],
                'entry_time': datetime.now()
            }
            return f"做空 {code} @ ${signal_data['price']}"
            
        elif signal == 0 and self.position is not None:
            # 平倉
            direction = self.position['direction']
            self.position = None
            return f"平倉 {code} ({direction}) @ ${signal_data['price']}"
        
        return "無操作"
    
    def get_status(self) -> Dict[str, Any]:
        """獲取交易器狀態"""
        return {
            'strategy': self.strategy.get_strategy_info(),
            'position': self.position,
            'has_position': self.position is not None
        }
