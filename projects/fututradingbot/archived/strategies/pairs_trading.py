"""
配對交易策略 - Pairs Trading Strategy

基於兩個相關資產的價差進行統計套利
適用於相關性高的股票對

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass

from src.strategies.base import BaseStrategy, TradeSignal, SignalType
from src.utils.logger import logger


@dataclass
class PairsTradingConfig:
    """配對交易策略配置"""
    lookback_period: int = 60           # 回看週期
    entry_zscore: float = 2.0           # 進場Z分數閾值
    exit_zscore: float = 0.5            # 出場Z分數閾值
    stop_loss_zscore: float = 3.5       # 止損Z分數
    position_pct: float = 0.015         # 單邊倉位比例
    min_correlation: float = 0.7        # 最小相關性要求
    hedge_ratio_window: int = 20        # 對沖比率計算窗口


class PairsTradingStrategy(BaseStrategy):
    """
    配對交易策略
    
    核心邏輯:
    1. 選擇兩個高度相關的資產 (如行業內的競爭對手)
    2. 計算價差 (spread) 和 Z分數
    3. 當Z分數超過閾值時，做多低估資產，做空高估資產
    4. 當價差回歸時平倉
    
    注意: 此策略需要同時監控兩個資產
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'lookback_period': 60,
            'entry_zscore': 2.0,
            'exit_zscore': 0.5,
            'stop_loss_zscore': 3.5,
            'position_pct': 0.015,
            'min_correlation': 0.7,
            'hedge_ratio_window': 20
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name="PairsTrading", config=default_config)
        
        self.lookback_period = self.config['lookback_period']
        self.entry_zscore = self.config['entry_zscore']
        self.exit_zscore = self.config['exit_zscore']
        self.stop_loss_zscore = self.config['stop_loss_zscore']
        self.position_pct = self.config['position_pct']
        self.min_correlation = self.config['min_correlation']
        self.hedge_ratio_window = self.config['hedge_ratio_window']
        
        # 存儲兩個資產的數據
        self.asset_pairs: Dict[str, Tuple[str, str]] = {}  # pair_id -> (asset1, asset2)
        self.price_data: Dict[str, pd.DataFrame] = {}
        self.positions: Dict[str, Dict[str, Any]] = {}  # pair_id -> position
        
        logger.info(f"配對交易策略初始化 | 進場Z分數: {self.entry_zscore}, 最小相關性: {self.min_correlation}")
    
    def register_pair(self, pair_id: str, asset1: str, asset2: str):
        """註冊資產對"""
        self.asset_pairs[pair_id] = (asset1, asset2)
        logger.info(f"資產對註冊: {pair_id} -> ({asset1}, {asset2})")
    
    def on_data(self, data: Dict[str, Any]) -> Optional[TradeSignal]:
        """
        處理行情數據
        
        注意: 配對交易需要同時更新兩個資產的數據
        """
        code = data.get('code')
        df = data.get('df')
        pair_id = data.get('pair_id')
        
        if df is None or len(df) < self.lookback_period:
            return None
        
        # 更新價格數據
        self.price_data[code] = df
        
        # 如果沒有指定pair_id，嘗試找到包含該code的pair
        if pair_id is None:
            for pid, (a1, a2) in self.asset_pairs.items():
                if code in (a1, a2):
                    pair_id = pid
                    break
        
        if pair_id is None or pair_id not in self.asset_pairs:
            return None
        
        asset1, asset2 = self.asset_pairs[pair_id]
        
        # 確保兩個資產都有數據
        if asset1 not in self.price_data or asset2 not in self.price_data:
            return None
        
        # 檢查現有持倉
        if pair_id in self.positions:
            return self._check_exit(pair_id, asset1, asset2)
        
        # 計算價差和Z分數
        zscore, correlation, hedge_ratio = self._calculate_spread_zscore(asset1, asset2)
        
        if zscore is None or correlation < self.min_correlation:
            return None
        
        price1 = self.price_data[asset1]['close'].iloc[-1]
        price2 = self.price_data[asset2]['close'].iloc[-1]
        
        # Z分數為正: asset2相對高估，做空asset2，做多asset1
        if zscore > self.entry_zscore:
            qty = self._calculate_position_size(price1)
            
            signal = TradeSignal(
                code=asset1,  # 做多低估的asset1
                signal=SignalType.BUY,
                price=price1,
                qty=qty,
                reason=f"配對交易 | Z分數: {zscore:.2f} | 做多{asset1}, 對沖做空{asset2}",
                metadata={
                    'pair_id': pair_id,
                    'zscore': zscore,
                    'correlation': correlation,
                    'hedge_ratio': hedge_ratio,
                    'paired_asset': asset2,
                    'paired_action': 'SELL',
                    'strategy': 'pairs_trading'
                }
            )
            
            self._record_entry(pair_id, asset1, asset2, signal, hedge_ratio, 'long_spread')
            return signal
        
        # Z分數為負: asset1相對高估，做空asset1，做多asset2
        if zscore < -self.entry_zscore:
            qty = self._calculate_position_size(price2)
            
            signal = TradeSignal(
                code=asset2,  # 做多低估的asset2
                signal=SignalType.BUY,
                price=price2,
                qty=qty,
                reason=f"配對交易 | Z分數: {zscore:.2f} | 做多{asset2}, 對沖做空{asset1}",
                metadata={
                    'pair_id': pair_id,
                    'zscore': zscore,
                    'correlation': correlation,
                    'hedge_ratio': hedge_ratio,
                    'paired_asset': asset1,
                    'paired_action': 'SELL',
                    'strategy': 'pairs_trading'
                }
            )
            
            self._record_entry(pair_id, asset2, asset1, signal, hedge_ratio, 'short_spread')
            return signal
        
        return None
    
    def _calculate_spread_zscore(self, asset1: str, asset2: str) -> Tuple[Optional[float], float, float]:
        """計算價差Z分數"""
        df1 = self.price_data[asset1]
        df2 = self.price_data[asset2]
        
        # 對齊數據
        min_len = min(len(df1), len(df2))
        if min_len < self.lookback_period:
            return None, 0, 1.0
        
        prices1 = df1['close'].iloc[-self.lookback_period:].values
        prices2 = df2['close'].iloc[-self.lookback_period:].values
        
        # 計算對沖比率 (線性回歸係數)
        hedge_ratio = self._calculate_hedge_ratio(prices1, prices2)
        
        # 計算價差
        spread = prices1 - hedge_ratio * prices2
        
        # 計算Z分數
        spread_mean = np.mean(spread)
        spread_std = np.std(spread)
        
        if spread_std == 0:
            return None, 0, hedge_ratio
        
        current_spread = spread[-1]
        zscore = (current_spread - spread_mean) / spread_std
        
        # 計算相關性
        correlation = np.corrcoef(prices1, prices2)[0, 1]
        
        return round(zscore, 2), round(correlation, 2), hedge_ratio
    
    def _calculate_hedge_ratio(self, prices1: np.ndarray, prices2: np.ndarray) -> float:
        """計算對沖比率"""
        # 使用簡單線性回歸: price1 = alpha + beta * price2
        # beta = cov(price1, price2) / var(price2)
        
        if len(prices1) < self.hedge_ratio_window:
            return 1.0
        
        p1 = prices1[-self.hedge_ratio_window:]
        p2 = prices2[-self.hedge_ratio_window:]
        
        covariance = np.cov(p1, p2)[0, 1]
        variance = np.var(p2)
        
        if variance == 0:
            return 1.0
        
        hedge_ratio = covariance / variance
        
        return round(hedge_ratio, 4)
    
    def _check_exit(self, pair_id: str, asset1: str, asset2: str) -> Optional[TradeSignal]:
        """檢查出場條件"""
        if pair_id not in self.positions:
            return None
        
        position = self.positions[pair_id]
        
        # 重新計算Z分數
        zscore, correlation, _ = self._calculate_spread_zscore(asset1, asset2)
        
        if zscore is None:
            return None
        
        exit_reason = None
        
        # Z分數回歸出場
        if abs(zscore) <= self.exit_zscore:
            exit_reason = f"價差回歸 | Z分數: {zscore:.2f}"
        
        # 止損出場
        elif abs(zscore) >= self.stop_loss_zscore:
            exit_reason = f"Z分數止損 | Z分數: {zscore:.2f}"
        
        # 相關性下降出場
        elif correlation < self.min_correlation - 0.2:
            exit_reason = f"相關性下降 | 當前: {correlation:.2f}"
        
        if exit_reason:
            primary_asset = position['primary_asset']
            current_price = self.price_data[primary_asset]['close'].iloc[-1]
            
            signal = TradeSignal(
                code=primary_asset,
                signal=SignalType.SELL if position['direction'] == 'long_spread' else SignalType.BUY,
                price=current_price,
                qty=position['qty'],
                reason=exit_reason,
                metadata={
                    'pair_id': pair_id,
                    'exit_zscore': zscore,
                    'paired_asset': position['hedge_asset']
                }
            )
            
            del self.positions[pair_id]
            return signal
        
        return None
    
    def _calculate_position_size(self, price: float) -> int:
        """計算倉位大小"""
        account_value = 1000000
        position_value = account_value * self.position_pct
        return max(int(position_value / price), 0)
    
    def _record_entry(
        self,
        pair_id: str,
        primary_asset: str,
        hedge_asset: str,
        signal: TradeSignal,
        hedge_ratio: float,
        direction: str
    ):
        """記錄進場"""
        self.positions[pair_id] = {
            'primary_asset': primary_asset,
            'hedge_asset': hedge_asset,
            'entry_price': signal.price,
            'qty': signal.qty,
            'hedge_ratio': hedge_ratio,
            'direction': direction,
            'entry_time': pd.Timestamp.now()
        }
    
    def on_order_update(self, order: Dict[str, Any]):
        """處理訂單更新"""
        pass
    
    def on_position_update(self, position: Dict[str, Any]):
        """處理持倉更新"""
        pass
    
    def get_pair_analysis(self, pair_id: str) -> Optional[Dict[str, Any]]:
        """獲取資產對分析"""
        if pair_id not in self.asset_pairs:
            return None
        
        asset1, asset2 = self.asset_pairs[pair_id]
        
        if asset1 not in self.price_data or asset2 not in self.price_data:
            return None
        
        zscore, correlation, hedge_ratio = self._calculate_spread_zscore(asset1, asset2)
        
        return {
            'pair_id': pair_id,
            'asset1': asset1,
            'asset2': asset2,
            'zscore': zscore,
            'correlation': correlation,
            'hedge_ratio': hedge_ratio,
            'has_position': pair_id in self.positions
        }
