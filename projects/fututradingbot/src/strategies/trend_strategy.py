"""
趨勢交易策略 (增強版)
Enhanced Trend Following Strategy for Futu Trading Bot

整合增強版多因子策略引擎：
- 多因子共振系統 (K線形態、技術指標、市場情緒、趨勢、板塊)
- 波動率適應性倉位管理
- 智能進出場邏輯

Author: FutuTradingBot AI Research Team
Version: 2.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.strategies.base import BaseStrategy, TradeSignal, SignalType
from src.strategies.enhanced_strategy import EnhancedStrategy, MultiFactorScore
from src.indicators.technical import (
    TechnicalIndicators, MACDResult, BOLLResult, 
    EMAResult, RSIResult, VolumeAnalysisResult,
    calculate_atr, TrendDirection
)
from src.analysis.mtf_analyzer import MTFAnalyzer, MTFConsistencyScore
from src.utils.logger import logger


class TrendState(Enum):
    """趨勢狀態"""
    STRONG_UPTREND = "strong_uptrend"      # 強上升趨勢
    UPTREND = "uptrend"                     # 上升趨勢
    SIDEWAYS = "sideways"                   # 橫盤整理
    DOWNTREND = "downtrend"                 # 下降趨勢
    STRONG_DOWNTREND = "strong_downtrend"   # 強下降趨勢


class PositionState(Enum):
    """持倉狀態"""
    NO_POSITION = "no_position"
    LONG = "long"
    SHORT = "short"


@dataclass
class TrendAnalysis:
    """趨勢分析結果"""
    trend_state: TrendState = TrendState.SIDEWAYS
    trend_strength: float = 0.0  # 0-100
    ema_alignment: str = "neutral"  # bullish/bearish/neutral
    macd_signal: str = "neutral"    # bullish/bearish/neutral
    boll_position: str = "middle"   # upper/middle/lower
    rsi_condition: str = "neutral"  # overbought/oversold/neutral
    volume_confirm: bool = False
    multi_timeframe_align: bool = False


@dataclass
class EntryCondition:
    """進場條件評估"""
    analysis_score: float = 0.0  # 9步分析法評分
    indicator_resonance: int = 0  # 共振指標數量
    volume_confirmed: bool = False
    rsi_valid: bool = False
    all_conditions_met: bool = False


@dataclass
class ExitCondition:
    """出場條件評估"""
    take_profit_triggered: bool = False
    stop_loss_triggered: bool = False
    trend_reversal: bool = False
    exit_reason: str = ""


@dataclass
class PositionSizing:
    """倉位計算結果"""
    position_size: int = 0
    position_value: float = 0.0
    risk_amount: float = 0.0
    kelly_fraction: float = 0.0


class TrendStrategy(BaseStrategy):
    """
    趨勢跟蹤交易策略 (增強版)
    
    基於EnhancedStrategy多因子引擎的趨勢策略
    
    策略邏輯:
    1. 多因子共振確認進場時機 (K線形態、技術指標、市場情緒、趨勢、板塊)
    2. 波動率適應性倉位管理
    3. 智能進出場邏輯
    4. 目標勝率: 65%+
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化趨勢策略
        
        Args:
            config: 策略配置字典
        """
        default_config = {
            # 繼承增強策略配置
            'min_confirmed_factors': 4,     # 最少確認因子數
            'min_score_threshold': 60.0,    # 最低分數閾值
            
            # 趨勢判斷參數
            'ema_fast': 12,
            'ema_slow': 26,
            'ema_trend': 60,
            
            # 進場條件
            'min_analysis_score': 70,       # 9步分析法最低評分 (向後兼容)
            'min_indicator_resonance': 3,   # 最少指標共振數
            'volume_threshold': 1.5,        # 成交量倍數閾值
            'rsi_lower': 30,                # RSI下限
            'rsi_upper': 70,                # RSI上限
            
            # 出場條件
            'take_profit_pct': 0.06,        # 止盈比例 6%
            'stop_loss_pct': 0.03,          # 止損比例 3%
            'use_atr_stop': False,          # 是否使用ATR止損
            'atr_multiplier_sl': 2.0,       # ATR止損倍數
            'atr_multiplier_tp': 3.0,       # ATR止盈倍數
            
            # 倉位管理
            'base_position_pct': 0.02,      # 基礎倉位比例 2%
            'max_position_pct': 0.05,       # 最大倉位比例 5%
            'max_position_value': 100000,   # 最大持倉金額
            'max_positions': 10,            # 最大持倉數量
            'use_kelly': False,             # 是否使用凱利公式
            'kelly_fraction': 0.5,          # 凱利分數 (保守一半)
            
            # 波動率適應
            'volatility_adjustment': True,  # 啟用波動率調整
            
            # 時間框架
            'timeframes': ['15m', '1h', '1d'],
            'primary_tf': '1h',
            
            # 風險控制
            'max_daily_trades': 5,
            'cooldown_periods': 5,
            
            # 板塊分析
            'enable_sector_analysis': False,
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name="EnhancedTrendFollowing", config=default_config)
        
        # 初始化增強策略引擎
        self.enhanced_engine = EnhancedStrategy(config=default_config)
        
        # 初始化MTF分析器（新增）
        self.mtf_analyzer = MTFAnalyzer()
        self.use_mtf_v2 = default_config.get('use_mtf_v2', True)  # 默認啟用MTF v2
        self.use_macdv = default_config.get('use_macdv', True)  # 默認啟用MACD-V
        self.use_divergence = default_config.get('use_divergence', True)  # 默認啟用背離檢測
        
        # 策略狀態
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.daily_trades: int = 0
        self.last_trade_time: Optional[datetime] = None
        self.cooldown_counter: Dict[str, int] = {}
        
        # 多時間框架數據緩存
        self.tf_data: Dict[str, Dict[str, pd.DataFrame]] = {
            '15m': {},
            '1h': {},
            '1d': {}
        }
        
        # MTF數據緩存（新增）
        self.mtf_data: Dict[str, Dict[str, pd.DataFrame]] = {
            'monthly': {},
            'weekly': {},
            'daily': {}
        }
        
        # 因子歷史記錄
        self.factor_history: List[MultiFactorScore] = []
        
        logger.info(f"增強趨勢策略初始化完成，配置: {self.config}")
        logger.info(f"MTF v2分析: {'啟用' if self.use_mtf_v2 else '禁用'}, "
                   f"MACD-V: {'啟用' if self.use_macdv else '禁用'}, "
                   f"背離檢測: {'啟用' if self.use_divergence else '禁用'}")
    
    def initialize(self):
        """初始化策略"""
        super().initialize()
        logger.info("趨勢策略已初始化，等待交易信號...")
    
    def on_data(self, data: Dict[str, Any]) -> Optional[TradeSignal]:
        """
        處理行情數據，產生交易信號
        
        使用增強版多因子引擎分析
        
        Args:
            data: 行情數據字典，包含:
                - code: 股票代碼
                - df: K線數據DataFrame
                - analysis_score: 9步分析法評分 (可選，向後兼容)
                - sector_data: 板塊數據 (可選)
                
        Returns:
            TradeSignal or None: 交易信號
        """
        code = data.get('code')
        df = data.get('df')
        
        if df is None or df.empty or len(df) < 20:
            return None
        
        # 更新數據緩存
        self._update_data_cache(code, df)
        
        # 檢查冷卻期
        if self._is_in_cooldown(code):
            return None
        
        # 檢查每日交易次數限制
        if self.daily_trades >= self.config['max_daily_trades']:
            return None
        
        # 使用增強引擎處理數據
        signal = self.enhanced_engine.on_data(data)
        
        if signal:
            # 更新本地狀態
            if signal.signal == SignalType.BUY:
                self._record_entry(code, signal)
            elif signal.signal == SignalType.SELL and code in self.positions:
                self._record_exit(code, signal)
        
        return signal
    
    def _update_data_cache(self, code: str, df: pd.DataFrame):
        """更新數據緩存"""
        # 根據數據頻率判斷時間框架
        if len(df) >= 2:
            time_diff = pd.to_datetime(df.index[-1]) - pd.to_datetime(df.index[-2])
            minutes = time_diff.total_seconds() / 60
            
            if minutes <= 15:
                tf = '15m'
            elif minutes <= 60:
                tf = '1h'
            else:
                tf = '1d'
            
            self.tf_data[tf][code] = df
    
    def _is_in_cooldown(self, code: str) -> bool:
        """檢查是否處於冷卻期"""
        if code in self.cooldown_counter:
            self.cooldown_counter[code] -= 1
            if self.cooldown_counter[code] <= 0:
                del self.cooldown_counter[code]
                return False
            return True
        return False
    
    def _check_entry_conditions(
        self, 
        code: str, 
        df: pd.DataFrame,
        analysis_score: float = 0
    ) -> Optional[TradeSignal]:
        """
        檢查進場條件
        
        進場條件:
        1. 9步分析法評分 > 70分
        2. 技術指標共振 (至少3個指標確認)
        3. 成交量確認 (> 均量1.5倍)
        4. RSI不在極端區域 (30-70)
        """
        # 評估進場條件
        entry = self._evaluate_entry_conditions(df, analysis_score)
        
        if not entry.all_conditions_met:
            return None
        
        # 多時間框架趨勢確認
        trend = self._analyze_multi_timeframe_trend(code)
        
        # 只在上升趨勢中做多
        if trend.trend_state not in [TrendState.UPTREND, TrendState.STRONG_UPTREND]:
            return None
        
        # 計算倉位大小
        current_price = df['close'].iloc[-1]
        account_value = self._get_account_value()
        sizing = self._calculate_position_size(
            code, current_price, account_value, entry
        )
        
        if sizing.position_size <= 0:
            return None
        
        # 檢查最大持倉限制
        if len(self.positions) >= self.config['max_positions']:
            logger.warning(f"達到最大持倉限制: {self.config['max_positions']}")
            return None
        
        # 計算MTF一致性評分（用於動態調整止損止盈）
        mtf_score = self._calculate_mtf_alignment_score(trend)
        
        # 生成進場信號（修正：傳遞MTF評分到止損止盈計算）
        signal = TradeSignal(
            code=code,
            signal=SignalType.BUY,
            price=current_price,
            qty=sizing.position_size,
            reason=f"趨勢進場 | 分析評分:{entry.analysis_score:.1f} | "
                   f"指標共振:{entry.indicator_resonance} | "
                   f"趨勢:{trend.trend_state.value} | "
                   f"MTF評分:{mtf_score:.1f}",
            metadata={
                'entry_price': current_price,
                'position_value': sizing.position_value,
                'risk_amount': sizing.risk_amount,
                'trend_strength': trend.trend_strength,
                'analysis_score': entry.analysis_score,
                'mtf_score': mtf_score,
                'stop_loss': self._calculate_stop_loss(df, current_price, 'long', mtf_score),
                'take_profit': self._calculate_take_profit(df, current_price, 'long', mtf_score)
            }
        )
        
        # 記錄進場
        self._record_entry(code, signal)
        
        return signal
    
    def _evaluate_entry_conditions(
        self, 
        df: pd.DataFrame,
        analysis_score: float = 0
    ) -> EntryCondition:
        """評估進場條件"""
        entry = EntryCondition()
        
        # 條件1: 9步分析法評分
        entry.analysis_score = analysis_score
        score_condition = analysis_score >= self.config['min_analysis_score']
        
        # 條件2: 技術指標共振
        ti = TechnicalIndicators(df)
        
        # 計算各指標
        ema = ti.calculate_ema()
        macd = ti.calculate_macd()
        rsi = ti.calculate_rsi()
        volume = ti.calculate_volume_analysis()
        
        # 檢查各指標信號
        indicators_bullish = 0
        
        # EMA交叉 (快線 > 慢線)
        if ema.ema_5.iloc[-1] > ema.ema_20.iloc[-1]:
            indicators_bullish += 1
        
        # MACD (DIF > DEA 且 MACD柱 > 0)
        if (macd.dif.iloc[-1] > macd.dea.iloc[-1] and 
            macd.macd.iloc[-1] > 0):
            indicators_bullish += 1
        
        # RSI (30-70範圍內偏強)
        rsi_value = rsi.rsi_12.iloc[-1]
        if 40 <= rsi_value <= 70:
            indicators_bullish += 1
            entry.rsi_valid = True
        elif rsi_value < 30:  # 超賣區域，可能反彈
            indicators_bullish += 1
            entry.rsi_valid = True
        
        # 價格在布林帶中軌上方
        boll = ti.calculate_boll()
        if df['close'].iloc[-1] > boll.middle.iloc[-1]:
            indicators_bullish += 1
        
        # 成交量確認
        vol_ratio = volume.volume_ratio.iloc[-1]
        if vol_ratio > self.config['volume_threshold']:
            entry.volume_confirmed = True
            indicators_bullish += 1
        
        entry.indicator_resonance = indicators_bullish
        resonance_condition = indicators_bullish >= self.config['min_indicator_resonance']
        
        # 綜合判斷
        entry.all_conditions_met = (
            score_condition and 
            resonance_condition and 
            entry.volume_confirmed and 
            entry.rsi_valid
        )
        
        return entry
    
    def _analyze_multi_timeframe_trend(self, code: str) -> TrendAnalysis:
        """
        多時間框架趨勢分析
        
        分析日線/小時線/15分鐘線的趨勢一致性
        """
        trend = TrendAnalysis()
        
        tf_trends = {}
        
        for tf in self.config['timeframes']:
            if code in self.tf_data[tf]:
                df = self.tf_data[tf][code]
                tf_trends[tf] = self._analyze_single_timeframe(df)
        
        if not tf_trends:
            return trend
        
        # 檢查多時間框架一致性
        primary_tf = self.config['primary_tf']
        if primary_tf in tf_trends:
            primary_trend = tf_trends[primary_tf]
            
            # 檢查所有時間框架是否一致
            all_bullish = all(t['ema_alignment'] == 'bullish' for t in tf_trends.values())
            all_bearish = all(t['ema_alignment'] == 'bearish' for t in tf_trends.values())
            
            trend.multi_timeframe_align = all_bullish or all_bearish
            
            # 確定趨勢狀態
            if all_bullish:
                if primary_trend['trend_strength'] > 70:
                    trend.trend_state = TrendState.STRONG_UPTREND
                else:
                    trend.trend_state = TrendState.UPTREND
            elif all_bearish:
                if primary_trend['trend_strength'] > 70:
                    trend.trend_state = TrendState.STRONG_DOWNTREND
                else:
                    trend.trend_state = TrendState.DOWNTREND
            else:
                trend.trend_state = TrendState.SIDEWAYS
            
            trend.trend_strength = primary_trend['trend_strength']
            trend.ema_alignment = primary_trend['ema_alignment']
            trend.macd_signal = primary_trend['macd_signal']
            trend.boll_position = primary_trend['boll_position']
            trend.volume_confirm = primary_trend['volume_confirm']
        
        return trend
    
    def _calculate_mtf_alignment_score(self, trend: TrendAnalysis) -> float:
        """
        計算MTF多時間框架一致性評分（使用MTF v2算法）
        
        如果啟用MTF v2，使用新的權重感知一致性評分算法
        否則使用舊版計算方法
        
        Args:
            trend: 趨勢分析結果
            
        Returns:
            float: MTF一致性評分 (0-100)
        """
        # 如果使用MTF v2，調用新的分析器
        if self.use_mtf_v2 and hasattr(self, 'mtf_analyzer'):
            try:
                # 構建時間框架分析數據
                monthly_tf = None
                weekly_tf = None
                daily_tf = None
                
                # 這裡需要根據實際數據構建TimeframeAnalysis對象
                # 簡化版本：使用趨勢分析結果估算
                base_score = trend.trend_strength
                
                # 根據趨勢狀態調整
                if trend.trend_state == TrendState.STRONG_UPTREND:
                    return min(100, base_score * 1.25)
                elif trend.trend_state == TrendState.UPTREND:
                    return min(100, base_score * 1.15)
                elif trend.trend_state == TrendState.SIDEWAYS:
                    return base_score * 0.8
                elif trend.trend_state in [TrendState.DOWNTREND, TrendState.STRONG_DOWNTREND]:
                    return base_score * 0.5
                    
            except Exception as e:
                logger.warning(f"MTF v2計算失敗，使用備用方法: {e}")
        
        # 基礎分數來自趨勢強度
        base_score = trend.trend_strength
        
        # 根據趨勢狀態調整
        state_multiplier = 1.0
        if trend.trend_state == TrendState.STRONG_UPTREND:
            state_multiplier = 1.2
        elif trend.trend_state == TrendState.UPTREND:
            state_multiplier = 1.0
        elif trend.trend_state == TrendState.SIDEWAYS:
            state_multiplier = 0.6
        elif trend.trend_state == TrendState.DOWNTREND:
            state_multiplier = 0.4
        elif trend.trend_state == TrendState.STRONG_DOWNTREND:
            state_multiplier = 0.2
        
        # 多時間框架一致性獎勵
        alignment_bonus = 0
        if trend.multi_timeframe_align:
            if trend.trend_state in [TrendState.STRONG_UPTREND, TrendState.UPTREND]:
                alignment_bonus = 15  # 多頭一致加分
            elif trend.trend_state in [TrendState.STRONG_DOWNTREND, TrendState.DOWNTREND]:
                alignment_bonus = 10  # 空頭一致加分（較低，因為主要做多）
        
        # 成交量確認加分
        volume_bonus = 5 if trend.volume_confirm else 0
        
        # 計算最終評分
        final_score = base_score * state_multiplier + alignment_bonus + volume_bonus
        
        # 確保在0-100範圍內
        return min(100.0, max(0.0, final_score))
    
    def _analyze_single_timeframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析單個時間框架的趨勢"""
        ti = TechnicalIndicators(df)
        
        # EMA分析
        ema = ti.calculate_ema()
        ema_bullish = (ema.ema_5.iloc[-1] > ema.ema_10.iloc[-1] > ema.ema_20.iloc[-1])
        ema_bearish = (ema.ema_5.iloc[-1] < ema.ema_10.iloc[-1] < ema.ema_20.iloc[-1])
        
        # MACD分析
        macd = ti.calculate_macd()
        macd_bullish = macd.dif.iloc[-1] > macd.dea.iloc[-1]
        macd_bearish = macd.dif.iloc[-1] < macd.dea.iloc[-1]
        
        # 布林帶位置
        boll = ti.calculate_boll()
        close = df['close'].iloc[-1]
        if close > boll.upper.iloc[-1]:
            boll_pos = "upper"
        elif close < boll.lower.iloc[-1]:
            boll_pos = "lower"
        else:
            boll_pos = "middle"
        
        # 成交量確認
        volume = ti.calculate_volume_analysis()
        vol_confirm = volume.volume_ratio.iloc[-1] > 1.0
        
        # 計算趨勢強度
        trend_strength = 50
        if ema_bullish:
            trend_strength += 20
            alignment = "bullish"
        elif ema_bearish:
            trend_strength -= 20
            alignment = "bearish"
        else:
            alignment = "neutral"
        
        if macd_bullish:
            trend_strength += 15
        elif macd_bearish:
            trend_strength -= 15
        
        return {
            'ema_alignment': alignment,
            'macd_signal': 'bullish' if macd_bullish else 'bearish' if macd_bearish else 'neutral',
            'boll_position': boll_pos,
            'volume_confirm': vol_confirm,
            'trend_strength': min(100, max(0, trend_strength))
        }
    
    def _check_exit_conditions(
        self, 
        code: str, 
        df: pd.DataFrame,
        position: Dict[str, Any]
    ) -> Optional[TradeSignal]:
        """
        檢查出場條件
        
        出場條件:
        1. 止盈: 固定比例或ATR倍數
        2. 止損: 固定比例或ATR倍數
        3. 趨勢反轉信號
        """
        current_price = df['close'].iloc[-1]
        entry_price = position.get('entry_price', current_price)
        position_type = position.get('type', 'long')
        
        exit_cond = ExitCondition()
        
        # 計算盈虧比例
        pnl_pct = (current_price - entry_price) / entry_price
        if position_type == 'short':
            pnl_pct = -pnl_pct
        
        # 檢查止盈
        if pnl_pct >= self.config['take_profit_pct']:
            exit_cond.take_profit_triggered = True
            exit_cond.exit_reason = f"止盈觸發 | 盈利: {pnl_pct*100:.2f}%"
        
        # 檢查止損
        if pnl_pct <= -self.config['stop_loss_pct']:
            exit_cond.stop_loss_triggered = True
            exit_cond.exit_reason = f"止損觸發 | 虧損: {pnl_pct*100:.2f}%"
        
        # 檢查趨勢反轉
        trend = self._analyze_multi_timeframe_trend(code)
        if position_type == 'long' and trend.trend_state in [
            TrendState.DOWNTREND, TrendState.STRONG_DOWNTREND
        ]:
            exit_cond.trend_reversal = True
            exit_cond.exit_reason = f"趨勢反轉 | 當前趨勢: {trend.trend_state.value}"
        
        # 判斷是否出場
        should_exit = (
            exit_cond.take_profit_triggered or 
            exit_cond.stop_loss_triggered or 
            exit_cond.trend_reversal
        )
        
        if should_exit:
            signal_type = SignalType.SELL if position_type == 'long' else SignalType.BUY
            
            signal = TradeSignal(
                code=code,
                signal=signal_type,
                price=current_price,
                qty=position.get('qty', 0),
                reason=exit_cond.exit_reason,
                metadata={
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl_pct': pnl_pct,
                    'pnl_amount': position.get('qty', 0) * (current_price - entry_price),
                    'exit_type': 'take_profit' if exit_cond.take_profit_triggered else 
                                'stop_loss' if exit_cond.stop_loss_triggered else 'trend_reversal'
                }
            )
            
            # 記錄出場
            self._record_exit(code, signal)
            
            return signal
        
        return None
    
    def _calculate_position_size(
        self, 
        code: str, 
        price: float,
        account_value: float,
        entry: EntryCondition
    ) -> PositionSizing:
        """
        計算倉位大小
        
        倉位管理策略:
        1. 固定比例法: 每筆交易使用固定比例的資金
        2. 凱利公式: 根據勝率和賠率動態調整
        """
        sizing = PositionSizing()
        
        if self.config['use_kelly']:
            # 凱利公式計算
            # f* = (p*b - q) / b
            # 其中 p = 勝率, q = 敗率, b = 賠率
            
            # 假設勝率基於分析評分 (簡化模型)
            win_prob = entry.analysis_score / 100
            loss_prob = 1 - win_prob
            
            # 賠率 (止盈/止損)
            payoff_ratio = self.config['take_profit_pct'] / self.config['stop_loss_pct']
            
            kelly = (win_prob * payoff_ratio - loss_prob) / payoff_ratio
            kelly = max(0, min(kelly, 0.5))  # 限制凱利值在0-50%
            
            sizing.kelly_fraction = kelly * self.config['kelly_fraction']
            position_pct = sizing.kelly_fraction
        else:
            # 固定比例法
            position_pct = self.config['fixed_position_pct']
        
        # 計算倉位金額
        sizing.risk_amount = account_value * position_pct
        sizing.position_value = min(
            sizing.risk_amount,
            self.config['max_position_value']
        )
        
        # 計算股數
        sizing.position_size = int(sizing.position_value / price)
        
        return sizing
    
    def _calculate_stop_loss(
        self, 
        df: pd.DataFrame, 
        entry_price: float,
        position_type: str,
        mtf_score: Optional[float] = None
    ) -> float:
        """
        計算止損價格（修正版 - 與MTF分析一致）
        
        修正內容：
        1. 根據MTF一致性評分動態調整止損距離
        2. 高MTF評分(>=75)時放寬止損至1.5倍
        3. 低MTF評分(<50)時收緊止損至0.7倍
        4. 逆趨勢時強制收緊止損
        
        Args:
            df: K線數據
            entry_price: 入場價格
            position_type: 倉位類型 ('long' or 'short')
            mtf_score: MTF一致性評分 (0-100)，用於動態調整止損
        """
        # 計算基礎止損距離
        if self.config['use_atr_stop']:
            # 使用ATR止損
            atr = calculate_atr(df, period=14)
            atr_value = atr.iloc[-1]
            base_stop_distance = atr_value * self.config['atr_multiplier_sl']
        else:
            # 使用固定比例止損
            base_stop_distance = entry_price * self.config['stop_loss_pct']
        
        # 根據MTF評分調整止損距離（修正：與MTF分析一致）
        adjustment_factor = 1.0
        if mtf_score is not None:
            if mtf_score >= 75:
                # 高一致性評分：放寬止損，給予趨勢更多空間
                adjustment_factor = 1.5
            elif mtf_score >= 60:
                # 中等一致性評分：輕微放寬
                adjustment_factor = 1.2
            elif mtf_score >= 50:
                # 評分一般：使用標準止損
                adjustment_factor = 1.0
            elif mtf_score >= 40:
                # 評分較低：收緊止損
                adjustment_factor = 0.8
            else:
                # 評分很低或趨勢不一致：大幅收緊止損
                adjustment_factor = 0.7
        
        # 應用調整因子
        adjusted_stop_distance = base_stop_distance * adjustment_factor
        
        # 計算最終止損價格
        if position_type == 'long':
            stop_loss = entry_price - adjusted_stop_distance
        else:
            stop_loss = entry_price + adjusted_stop_distance
        
        # 確保止損價格有效（不低於0或不超過入場價的50%）
        if position_type == 'long':
            stop_loss = max(stop_loss, entry_price * 0.5)  # 最大50%虧損限制
        else:
            stop_loss = min(stop_loss, entry_price * 1.5)  # 最大50%虧損限制
        
        return stop_loss
    
    def _calculate_take_profit(
        self, 
        df: pd.DataFrame, 
        entry_price: float,
        position_type: str,
        mtf_score: Optional[float] = None
    ) -> float:
        """
        計算止盈價格（修正版 - 與MTF分析一致）
        
        修正內容：
        1. 根據MTF一致性評分動態調整止盈目標
        2. 高MTF評分(>=75)時提高止盈至1.4倍（追蹤強趨勢）
        3. 低MTF評分(<50)時降低止盈至0.8倍（快速獲利了結）
        
        Args:
            df: K線數據
            entry_price: 入場價格
            position_type: 倉位類型 ('long' or 'short')
            mtf_score: MTF一致性評分 (0-100)，用於動態調整止盈
        """
        # 計算基礎止盈距離
        if self.config['use_atr_stop']:
            # 使用ATR止盈
            atr = calculate_atr(df, period=14)
            atr_value = atr.iloc[-1]
            base_tp_distance = atr_value * self.config['atr_multiplier_tp']
        else:
            # 使用固定比例止盈
            base_tp_distance = entry_price * self.config['take_profit_pct']
        
        # 根據MTF評分調整止盈距離（修正：與MTF分析一致）
        adjustment_factor = 1.0
        if mtf_score is not None:
            if mtf_score >= 75:
                # 高一致性評分：提高止盈目標，追蹤強趨勢
                adjustment_factor = 1.4
            elif mtf_score >= 60:
                # 中等一致性評分：輕微提高止盈
                adjustment_factor = 1.2
            elif mtf_score >= 50:
                # 評分一般：使用標準止盈
                adjustment_factor = 1.0
            elif mtf_score >= 40:
                # 評分較低：降低止盈，快速獲利了結
                adjustment_factor = 0.9
            else:
                # 評分很低：大幅降低止盈
                adjustment_factor = 0.8
        
        # 應用調整因子
        adjusted_tp_distance = base_tp_distance * adjustment_factor
        
        # 計算最終止盈價格
        if position_type == 'long':
            take_profit = entry_price + adjusted_tp_distance
        else:
            take_profit = entry_price - adjusted_tp_distance
        
        return take_profit
    
    def _record_entry(self, code: str, signal: TradeSignal):
        """記錄進場"""
        self.positions[code] = {
            'entry_price': signal.metadata['entry_price'],
            'qty': signal.qty,
            'type': 'long' if signal.signal == SignalType.BUY else 'short',
            'entry_time': datetime.now(),
            'stop_loss': signal.metadata['stop_loss'],
            'take_profit': signal.metadata['take_profit']
        }
        
        self.daily_trades += 1
        self.last_trade_time = datetime.now()
        self.cooldown_counter[code] = self.config['cooldown_periods']
        
        logger.info(f"進場記錄 | {code} | 價格: {signal.price} | 數量: {signal.qty}")
    
    def _record_exit(self, code: str, signal: TradeSignal):
        """記錄出場"""
        if code in self.positions:
            position = self.positions[code]
            pnl = signal.metadata.get('pnl_amount', 0)
            
            logger.info(
                f"出場記錄 | {code} | 價格: {signal.price} | "
                f"盈虧: {pnl:.2f} | 原因: {signal.reason}"
            )
            
            del self.positions[code]
            self.cooldown_counter[code] = self.config['cooldown_periods']
    
    def _get_account_value(self) -> float:
        """獲取賬戶總值 (簡化實現，實際應從API獲取)"""
        # 這裡應該從實際賬戶獲取
        # 暫時返回默認值
        return 1000000  # 假設100萬港幣
    
    def on_order_update(self, order: Dict[str, Any]):
        """處理訂單更新"""
        logger.debug(f"訂單更新: {order}")
    
    def on_position_update(self, position: Dict[str, Any]):
        """處理持倉更新"""
        logger.debug(f"持倉更新: {position}")
    
    def get_position_info(self, code: str) -> Optional[Dict[str, Any]]:
        """獲取持倉信息"""
        return self.positions.get(code)
    
    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有持倉"""
        return self.positions.copy()
    
    def reset_daily_stats(self):
        """重置每日統計"""
        self.daily_trades = 0
        logger.info("每日交易統計已重置")
    
    def _record_entry(self, code: str, signal: TradeSignal):
        """記錄進場"""
        self.positions[code] = {
            'entry_price': signal.metadata.get('entry_price', signal.price),
            'qty': signal.qty,
            'type': 'long' if signal.signal == SignalType.BUY else 'short',
            'entry_time': datetime.now(),
            'stop_loss': signal.metadata.get('stop_loss'),
            'take_profit': signal.metadata.get('take_profit')
        }
        self.daily_trades += 1
        self.last_trade_time = datetime.now()
        self.cooldown_counter[code] = self.config['cooldown_periods']
    
    def _record_exit(self, code: str, signal: TradeSignal):
        """記錄出場"""
        if code in self.positions:
            del self.positions[code]
            self.cooldown_counter[code] = self.config['cooldown_periods']
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """獲取策略統計信息"""
        enhanced_stats = self.enhanced_engine.get_strategy_stats()
        return {
            'active_positions': len(self.positions),
            'daily_trades': self.daily_trades,
            'positions': list(self.positions.keys()),
            'cooldown_codes': list(self.cooldown_counter.keys()),
            'enhanced_engine_stats': enhanced_stats
        }
