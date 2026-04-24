"""
增強版策略引擎 - Enhanced Strategy Engine

多因子共振交易系統：
- K線形態信號 (權重 20%)
- 技術指標共振 (權重 30%)
- 市場情緒 (權重 20%)
- 趨勢判斷 (權重 20%)
- 板塊輪動 (權重 10%)

目標勝率: 65%+
進場條件: 至少4個因子確認

Author: FutuTradingBot AI Research Team
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.strategies.base import BaseStrategy, TradeSignal, SignalType
from src.indicators.technical import TechnicalIndicators
from src.indicators.candlestick_patterns import CandlestickAnalyzer, CandlestickPattern, PatternType
from src.analysis.market_regime import MarketRegimeDetector, MarketRegime, VolatilityRegime, RegimeState
from src.analysis.market_sentiment import MarketSentimentAnalyzer, MarketSentimentAnalysis, MarketSentiment
from src.utils.logger import logger


class SignalFactor(Enum):
    """信號因子枚舉"""
    CANDLESTICK = "candlestick"         # K線形態
    TECHNICAL = "technical"             # 技術指標
    SENTIMENT = "sentiment"             # 市場情緒
    TREND = "trend"                     # 趨勢判斷
    SECTOR = "sector"                   # 板塊輪動


@dataclass
class FactorSignal:
    """因子信號"""
    factor: SignalFactor
    signal: str                         # bullish / bearish / neutral
    strength: float                     # 0-1
    confidence: float                   # 0-1
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiFactorScore:
    """多因子評分結果"""
    total_score: float                  # 總分 (-100 到 100)
    weighted_score: float               # 加權分數
    confirmed_factors: int              # 確認因子數量
    factor_signals: List[FactorSignal] = field(default_factory=list)
    
    def has_min_factors(self, min_factors: int = 4) -> bool:
        """檢查是否達到最少確認因子數"""
        return self.confirmed_factors >= min_factors
    
    def is_strong_signal(self, threshold: float = 60.0) -> bool:
        """檢查是否為強信號"""
        return abs(self.weighted_score) >= threshold


@dataclass
class VolatilityAdjustment:
    """波動率調整參數"""
    position_scale: float = 1.0         # 倉位縮放
    stop_loss_mult: float = 1.0         # 止損倍數調整
    take_profit_mult: float = 2.0       # 止盈倍數調整
    max_positions: float = 1.0          # 最大持倉數調整


class EnhancedStrategy(BaseStrategy):
    """
    增強版多因子共振策略
    
    整合多種信號源，通過加權評分系統產生高質量交易信號
    """
    
    # 因子權重配置
    FACTOR_WEIGHTS = {
        SignalFactor.CANDLESTICK: 0.20,   # K線形態 20%
        SignalFactor.TECHNICAL: 0.30,     # 技術指標 30%
        SignalFactor.SENTIMENT: 0.20,     # 市場情緒 20%
        SignalFactor.TREND: 0.20,         # 趨勢判斷 20%
        SignalFactor.SECTOR: 0.10         # 板塊輪動 10%
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化增強策略
        
        Args:
            config: 策略配置字典
        """
        default_config = {
            # 進場條件
            'min_confirmed_factors': 4,     # 最少確認因子數
            'min_score_threshold': 60.0,    # 最低分數閾值
            'max_score_threshold': -60.0,   # 最高負分閾值 (用於做空)
            
            # 風險控制
            'base_position_pct': 0.02,      # 基礎倉位比例
            'max_position_pct': 0.05,       # 最大倉位比例
            'stop_loss_pct': 0.03,          # 基礎止損比例
            'take_profit_pct': 0.06,        # 基礎止盈比例
            
            # 波動率適應
            'volatility_adjustment': True,  # 啟用波動率調整
            
            # 時間框架
            'primary_timeframe': '1h',
            'confirmation_timeframes': ['15m', '4h'],
            
            # 冷卻期
            'cooldown_periods': 5,          # 進場後冷卻K線數
            
            # 板塊數據
            'enable_sector_analysis': False,
        }
        
        if config:
            default_config.update(config)
        
        super().__init__(name="EnhancedMultiFactor", config=default_config)
        
        # 初始化分析器
        self.candlestick_analyzer = CandlestickAnalyzer()
        self.regime_detector = MarketRegimeDetector()
        self.sentiment_analyzer = MarketSentimentAnalyzer()
        
        # 狀態管理
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.cooldown_counters: Dict[str, int] = {}
        self.factor_history: List[MultiFactorScore] = []
        self.sector_data: Dict[str, pd.DataFrame] = {}
        
        logger.info(f"增強策略初始化完成，配置: {self.config}")
    
    def initialize(self):
        """初始化策略"""
        super().initialize()
        logger.info("增強策略已初始化，等待交易信號...")
    
    def on_data(self, data: Dict[str, Any]) -> Optional[TradeSignal]:
        """
        處理行情數據，產生交易信號
        
        Args:
            data: 行情數據字典
                - code: 股票代碼
                - df: K線數據DataFrame
                - sector_data: 板塊數據 (可選)
                
        Returns:
            TradeSignal or None
        """
        code = data.get('code')
        df = data.get('df')
        
        if df is None or df.empty or len(df) < 20:
            return None
        
        # 更新板塊數據
        if 'sector_data' in data:
            self.sector_data = data['sector_data']
        
        # 檢查冷卻期
        if self._is_in_cooldown(code):
            return None
        
        # 檢查現有持倉
        if code in self.positions:
            return self._check_exit_conditions(code, df)
        
        # 執行多因子分析
        factor_score = self._analyze_factors(code, df)
        
        # 記錄因子歷史
        self.factor_history.append(factor_score)
        if len(self.factor_history) > 100:
            self.factor_history = self.factor_history[-50:]
        
        # 檢查進場條件
        if self._should_enter(factor_score):
            return self._generate_entry_signal(code, df, factor_score)
        
        return None
    
    def _analyze_factors(self, code: str, df: pd.DataFrame) -> MultiFactorScore:
        """
        分析所有因子信號
        
        Returns:
            MultiFactorScore: 多因子評分結果
        """
        factor_signals = []
        
        # 1. K線形態分析
        candlestick_signal = self._analyze_candlestick(df)
        factor_signals.append(candlestick_signal)
        
        # 2. 技術指標分析
        technical_signal = self._analyze_technical(df)
        factor_signals.append(technical_signal)
        
        # 3. 市場情緒分析
        sentiment_signal = self._analyze_sentiment(df)
        factor_signals.append(sentiment_signal)
        
        # 4. 趨勢判斷
        trend_signal = self._analyze_trend(df)
        factor_signals.append(trend_signal)
        
        # 5. 板塊輪動分析
        sector_signal = self._analyze_sector(code)
        factor_signals.append(sector_signal)
        
        # 計算綜合評分
        return self._calculate_multi_factor_score(factor_signals)
    
    def _analyze_candlestick(self, df: pd.DataFrame) -> FactorSignal:
        """分析K線形態因子"""
        # 獲取最新K線形態
        pattern = self.candlestick_analyzer.detect_at_index(df, len(df) - 1)
        
        if pattern is None or pattern.pattern_type == PatternType.NONE:
            return FactorSignal(
                factor=SignalFactor.CANDLESTICK,
                signal='neutral',
                strength=0.0,
                confidence=0.5,
                details={'pattern': 'none'}
            )
        
        # 根據形態確定信號
        if pattern.is_bullish() and pattern.overall_score >= 60:
            signal = 'bullish'
            strength = pattern.overall_score / 100
        elif pattern.is_bearish() and pattern.overall_score >= 60:
            signal = 'bearish'
            strength = pattern.overall_score / 100
        else:
            signal = 'neutral'
            strength = 0.0
        
        return FactorSignal(
            factor=SignalFactor.CANDLESTICK,
            signal=signal,
            strength=strength,
            confidence=pattern.confidence,
            details={
                'pattern': pattern.pattern_type.value,
                'score': pattern.overall_score,
                'description': pattern.description
            }
        )
    
    def _analyze_technical(self, df: pd.DataFrame) -> FactorSignal:
        """分析技術指標因子"""
        ti = TechnicalIndicators(df)
        
        signals = []
        
        # MACD信號
        macd = ti.calculate_macd()
        if macd.dif.iloc[-1] > macd.dea.iloc[-1] and macd.macd.iloc[-1] > 0:
            signals.append(('macd', 1.0))
        elif macd.dif.iloc[-1] < macd.dea.iloc[-1] and macd.macd.iloc[-1] < 0:
            signals.append(('macd', -1.0))
        else:
            signals.append(('macd', 0.0))
        
        # RSI信號
        rsi = ti.calculate_rsi()
        rsi_value = rsi.rsi_12.iloc[-1]
        if 40 <= rsi_value <= 60:
            signals.append(('rsi', 0.5 if rsi_value > 50 else -0.5))
        elif rsi_value < 30:
            signals.append(('rsi', 1.0))  # 超賣，看漲
        elif rsi_value > 70:
            signals.append(('rsi', -1.0))  # 超買，看跌
        else:
            signals.append(('rsi', 0.0))
        
        # 布林帶信號
        boll = ti.calculate_boll()
        close = df['close'].iloc[-1]
        if close > boll.middle.iloc[-1]:
            signals.append(('boll', 0.5))
        elif close < boll.middle.iloc[-1]:
            signals.append(('boll', -0.5))
        else:
            signals.append(('boll', 0.0))
        
        # EMA排列
        ema = ti.calculate_ema()
        if ema.ema_5.iloc[-1] > ema.ema_10.iloc[-1] > ema.ema_20.iloc[-1]:
            signals.append(('ema', 1.0))
        elif ema.ema_5.iloc[-1] < ema.ema_10.iloc[-1] < ema.ema_20.iloc[-1]:
            signals.append(('ema', -1.0))
        else:
            signals.append(('ema', 0.0))
        
        # 成交量確認
        volume = ti.calculate_volume_analysis()
        if volume.volume_ratio.iloc[-1] > 1.5:
            signals.append(('volume', 0.5))
        else:
            signals.append(('volume', 0.0))
        
        # 計算綜合技術信號
        total_score = sum(s[1] for s in signals)
        max_score = len(signals)
        
        normalized_score = total_score / max_score
        
        if normalized_score > 0.3:
            signal = 'bullish'
            strength = min(normalized_score, 1.0)
        elif normalized_score < -0.3:
            signal = 'bearish'
            strength = min(abs(normalized_score), 1.0)
        else:
            signal = 'neutral'
            strength = 0.0
        
        return FactorSignal(
            factor=SignalFactor.TECHNICAL,
            signal=signal,
            strength=strength,
            confidence=min(abs(normalized_score) + 0.5, 1.0),
            details={
                'individual_signals': signals,
                'total_score': total_score,
                'normalized_score': normalized_score
            }
        )
    
    def _analyze_sentiment(self, df: pd.DataFrame) -> FactorSignal:
        """分析市場情緒因子"""
        sentiment_analysis = self.sentiment_analyzer.analyze(df)
        
        # 基於恐懼/貪婪指數判斷
        fgi = sentiment_analysis.indicators.fear_greed_index
        
        if fgi < 25:  # 極度恐懼 -> 反向看漲
            signal = 'bullish'
            strength = (25 - fgi) / 25 * 0.8
        elif fgi < 40:  # 恐懼 -> 謹慎看漲
            signal = 'bullish'
            strength = (40 - fgi) / 40 * 0.5
        elif fgi > 75:  # 極度貪婪 -> 反向看跌
            signal = 'bearish'
            strength = (fgi - 75) / 25 * 0.8
        elif fgi > 60:  # 貪婪 -> 謹慎看跌
            signal = 'bearish'
            strength = (fgi - 60) / 40 * 0.5
        else:
            signal = 'neutral'
            strength = 0.0
        
        # 資金流確認
        if sentiment_analysis.money_flow.is_positive():
            if signal == 'bullish':
                strength = min(strength * 1.2, 1.0)
        else:
            if signal == 'bearish':
                strength = min(strength * 1.2, 1.0)
        
        return FactorSignal(
            factor=SignalFactor.SENTIMENT,
            signal=signal,
            strength=strength,
            confidence=0.7,
            details={
                'fear_greed_index': fgi,
                'market_phase': sentiment_analysis.phase.value,
                'money_flow': sentiment_analysis.money_flow.flow_strength
            }
        )
    
    def _analyze_trend(self, df: pd.DataFrame) -> FactorSignal:
        """分析趨勢因子"""
        regime_state = self.regime_detector.detect(df)
        
        # 根據市場狀態判斷趨勢
        if regime_state.regime.value in ['trending_up']:
            signal = 'bullish'
            strength = regime_state.confidence
        elif regime_state.regime.value in ['trending_down']:
            signal = 'bearish'
            strength = regime_state.confidence
        elif regime_state.regime.value == 'high_volatility':
            signal = 'neutral'
            strength = 0.0
        else:
            signal = 'neutral'
            strength = 0.3
        
        # 趨勢強度調整
        if regime_state.features:
            trend_strength = regime_state.features.trend_strength / 100
            if signal == 'bullish':
                strength = min(strength * trend_strength * 1.5, 1.0)
            elif signal == 'bearish':
                strength = min(strength * trend_strength * 1.5, 1.0)
        
        return FactorSignal(
            factor=SignalFactor.TREND,
            signal=signal,
            strength=strength,
            confidence=regime_state.confidence,
            details={
                'regime': regime_state.regime.value,
                'volatility_regime': regime_state.volatility_regime.value,
                'trend_strength': regime_state.features.trend_strength if regime_state.features else 0
            }
        )
    
    def _analyze_sector(self, code: str) -> FactorSignal:
        """分析板塊輪動因子"""
        if not self.config['enable_sector_analysis'] or not self.sector_data:
            return FactorSignal(
                factor=SignalFactor.SECTOR,
                signal='neutral',
                strength=0.0,
                confidence=0.5,
                details={'enabled': False}
            )
        
        # 找到股票所屬板塊
        sector_momentum = self.sentiment_analyzer.track_sector_rotation(self.sector_data)
        
        if not sector_momentum:
            return FactorSignal(
                factor=SignalFactor.SECTOR,
                signal='neutral',
                strength=0.0,
                confidence=0.5,
                details={'no_data': True}
            )
        
        # 找到最強板塊
        top_sector = sector_momentum[0]
        
        # 簡化處理：假設股票屬於最強板塊
        if top_sector.momentum > 2.0:  # 強勁上漲
            signal = 'bullish'
            strength = min(top_sector.momentum / 5.0, 1.0)
        elif top_sector.momentum < -2.0:  # 強勁下跌
            signal = 'bearish'
            strength = min(abs(top_sector.momentum) / 5.0, 1.0)
        else:
            signal = 'neutral'
            strength = 0.0
        
        return FactorSignal(
            factor=SignalFactor.SECTOR,
            signal=signal,
            strength=strength,
            confidence=0.6,
            details={
                'top_sector': top_sector.sector_name,
                'momentum': top_sector.momentum,
                'rank': top_sector.rank
            }
        )
    
    def _calculate_multi_factor_score(
        self,
        factor_signals: List[FactorSignal]
    ) -> MultiFactorScore:
        """
        計算多因子綜合評分
        
        Returns:
            MultiFactorScore: 多因子評分結果
        """
        weighted_score = 0.0
        confirmed_factors = 0
        
        for signal in factor_signals:
            weight = self.FACTOR_WEIGHTS.get(signal.factor, 0.1)
            
            if signal.signal == 'bullish':
                factor_score = signal.strength * 100 * weight
                confirmed_factors += 1
            elif signal.signal == 'bearish':
                factor_score = -signal.strength * 100 * weight
                confirmed_factors += 1
            else:
                factor_score = 0
            
            weighted_score += factor_score
        
        # 計算總分 (未加權)
        total_score = sum(
            s.strength * 100 if s.signal == 'bullish' else -s.strength * 100 if s.signal == 'bearish' else 0
            for s in factor_signals
        ) / len(factor_signals) if factor_signals else 0
        
        return MultiFactorScore(
            total_score=round(total_score, 2),
            weighted_score=round(weighted_score, 2),
            confirmed_factors=confirmed_factors,
            factor_signals=factor_signals
        )
    
    def _should_enter(self, factor_score: MultiFactorScore) -> bool:
        """
        判斷是否應該進場
        
        條件:
        1. 至少4個因子確認
        2. 加權分數達到閾值
        """
        min_factors = self.config['min_confirmed_factors']
        min_score = self.config['min_score_threshold']
        
        # 檢查最少因子數
        if not factor_score.has_min_factors(min_factors):
            return False
        
        # 檢查分數閾值 (看多或看空)
        if factor_score.weighted_score >= min_score:
            return True
        if factor_score.weighted_score <= -min_score:
            return True
        
        return False
    
    def _generate_entry_signal(
        self,
        code: str,
        df: pd.DataFrame,
        factor_score: MultiFactorScore
    ) -> TradeSignal:
        """生成進場信號"""
        current_price = df['close'].iloc[-1]
        
        # 確定方向
        is_long = factor_score.weighted_score > 0
        signal_type = SignalType.BUY if is_long else SignalType.SELL
        
        # 計算倉位大小 (基於波動率調整)
        position_size = self._calculate_position_size(df, factor_score)
        
        # 計算止損止盈
        stop_loss, take_profit = self._calculate_exit_levels(
            df, current_price, is_long
        )
        
        # 構建信號詳情
        factor_details = []
        for fs in factor_score.factor_signals:
            factor_details.append(
                f"{fs.factor.value}:{fs.signal}({fs.strength:.2f})"
            )
        
        signal = TradeSignal(
            code=code,
            signal=signal_type,
            price=current_price,
            qty=position_size,
            reason=f"多因子共振 | 加權分數:{factor_score.weighted_score:.1f} | "
                   f"確認因子:{factor_score.confirmed_factors}/5 | "
                   f"{'看多' if is_long else '看空'}",
            metadata={
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'factor_score': factor_score.weighted_score,
                'confirmed_factors': factor_score.confirmed_factors,
                'factor_details': factor_details,
                'position_size': position_size
            }
        )
        
        # 記錄進場
        self._record_entry(code, signal, is_long)
        
        logger.info(
            f"進場信號 | {code} | {'買入' if is_long else '賣出'} | "
            f"價格:{current_price:.2f} | 分數:{factor_score.weighted_score:.1f}"
        )
        
        return signal
    
    def _check_exit_conditions(
        self,
        code: str,
        df: pd.DataFrame
    ) -> Optional[TradeSignal]:
        """檢查出場條件"""
        if code not in self.positions:
            return None
        
        position = self.positions[code]
        current_price = df['close'].iloc[-1]
        entry_price = position['entry_price']
        is_long = position['is_long']
        
        # 計算盈虧比例
        pnl_pct = (current_price - entry_price) / entry_price
        if not is_long:
            pnl_pct = -pnl_pct
        
        stop_loss = position['stop_loss']
        take_profit = position['take_profit']
        
        exit_reason = None
        exit_type = None
        
        # 檢查止損
        if (is_long and current_price <= stop_loss) or (not is_long and current_price >= stop_loss):
            exit_reason = f"止損觸發 | 價格:{current_price:.2f} | 虧損:{pnl_pct*100:.2f}%"
            exit_type = 'stop_loss'
        
        # 檢查止盈
        elif (is_long and current_price >= take_profit) or (not is_long and current_price <= take_profit):
            exit_reason = f"止盈觸發 | 價格:{current_price:.2f} | 盈利:{pnl_pct*100:.2f}%"
            exit_type = 'take_profit'
        
        # 檢查趨勢反轉 (因子分數大幅逆轉)
        factor_score = self._analyze_factors(code, df)
        if factor_score.confirmed_factors >= 3:
            if is_long and factor_score.weighted_score < -40:
                exit_reason = f"趨勢反轉 | 新分數:{factor_score.weighted_score:.1f}"
                exit_type = 'trend_reversal'
            elif not is_long and factor_score.weighted_score > 40:
                exit_reason = f"趨勢反轉 | 新分數:{factor_score.weighted_score:.1f}"
                exit_type = 'trend_reversal'
        
        if exit_reason:
            signal = TradeSignal(
                code=code,
                signal=SignalType.SELL if is_long else SignalType.BUY,
                price=current_price,
                qty=position['qty'],
                reason=exit_reason,
                metadata={
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'pnl_pct': pnl_pct,
                    'exit_type': exit_type
                }
            )
            
            self._record_exit(code, signal)
            return signal
        
        return None
    
    def _calculate_position_size(
        self,
        df: pd.DataFrame,
        factor_score: MultiFactorScore
    ) -> int:
        """
        計算倉位大小
        
        考慮波動率調整
        """
        base_pct = self.config['base_position_pct']
        
        # 波動率調整
        if self.config['volatility_adjustment']:
            adjustment = self._get_volatility_adjustment(df)
            adjusted_pct = base_pct * adjustment.position_scale
        else:
            adjusted_pct = base_pct
        
        # 根據因子強度調整
        strength_multiplier = min(abs(factor_score.weighted_score) / 60, 1.5)
        final_pct = min(adjusted_pct * strength_multiplier, self.config['max_position_pct'])
        
        # 假設賬戶價值為100萬計算股數
        account_value = 1000000
        position_value = account_value * final_pct
        
        # 獲取當前價格
        current_price = df['close'].iloc[-1]
        position_size = int(position_value / current_price)
        
        return max(position_size, 0)
    
    def _calculate_exit_levels(
        self,
        df: pd.DataFrame,
        entry_price: float,
        is_long: bool
    ) -> Tuple[float, float]:
        """
        計算出場價位
        
        Returns:
            (止損價, 止盈價)
        """
        # 波動率調整
        if self.config['volatility_adjustment']:
            adjustment = self._get_volatility_adjustment(df)
            sl_mult = adjustment.stop_loss_mult
            tp_mult = adjustment.take_profit_mult
        else:
            sl_mult = 1.0
            tp_mult = 2.0
        
        sl_pct = self.config['stop_loss_pct'] * sl_mult
        tp_pct = self.config['take_profit_pct'] * tp_mult
        
        if is_long:
            stop_loss = entry_price * (1 - sl_pct)
            take_profit = entry_price * (1 + tp_pct)
        else:
            stop_loss = entry_price * (1 + sl_pct)
            take_profit = entry_price * (1 - tp_pct)
        
        return round(stop_loss, 4), round(take_profit, 4)
    
    def _get_volatility_adjustment(self, df: pd.DataFrame) -> VolatilityAdjustment:
        """
        獲取波動率調整參數
        
        根據波動率區間調整倉位和止損止盈
        """
        regime_state = self.regime_detector.detect(df)
        
        adjustments = {
            VolatilityRegime.LOW: VolatilityAdjustment(
                position_scale=1.5,
                stop_loss_mult=1.5,
                take_profit_mult=3.0,
                max_positions=1.5
            ),
            VolatilityRegime.MEDIUM: VolatilityAdjustment(
                position_scale=1.0,
                stop_loss_mult=1.0,
                take_profit_mult=2.0,
                max_positions=1.0
            ),
            VolatilityRegime.HIGH: VolatilityAdjustment(
                position_scale=0.5,
                stop_loss_mult=0.7,
                take_profit_mult=1.5,
                max_positions=0.6
            ),
            VolatilityRegime.EXTREME: VolatilityAdjustment(
                position_scale=0.0,
                stop_loss_mult=0.5,
                take_profit_mult=1.0,
                max_positions=0.0
            )
        }
        
        return adjustments.get(
            regime_state.volatility_regime,
            adjustments[VolatilityRegime.MEDIUM]
        )
    
    def _is_in_cooldown(self, code: str) -> bool:
        """檢查是否處於冷卻期"""
        if code in self.cooldown_counters:
            self.cooldown_counters[code] -= 1
            if self.cooldown_counters[code] <= 0:
                del self.cooldown_counters[code]
                return False
            return True
        return False
    
    def _record_entry(
        self,
        code: str,
        signal: TradeSignal,
        is_long: bool
    ):
        """記錄進場"""
        self.positions[code] = {
            'entry_price': signal.metadata['entry_price'],
            'qty': signal.qty,
            'is_long': is_long,
            'entry_time': datetime.now(),
            'stop_loss': signal.metadata['stop_loss'],
            'take_profit': signal.metadata['take_profit']
        }
        
        self.cooldown_counters[code] = self.config['cooldown_periods']
    
    def _record_exit(self, code: str, signal: TradeSignal):
        """記錄出場"""
        if code in self.positions:
            pnl_pct = signal.metadata.get('pnl_pct', 0)
            logger.info(
                f"出場記錄 | {code} | 價格:{signal.price:.2f} | "
                f"盈虧:{pnl_pct*100:.2f}% | 原因:{signal.reason}"
            )
            del self.positions[code]
            self.cooldown_counters[code] = self.config['cooldown_periods']
    
    def on_order_update(self, order: Dict[str, Any]):
        """處理訂單更新"""
        logger.debug(f"訂單更新: {order}")
    
    def on_position_update(self, position: Dict[str, Any]):
        """處理持倉更新"""
        logger.debug(f"持倉更新: {position}")
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """獲取策略統計"""
        return {
            'active_positions': len(self.positions),
            'positions': list(self.positions.keys()),
            'cooldown_codes': list(self.cooldown_counters.keys()),
            'recent_factor_scores': [
                {
                    'score': fs.weighted_score,
                    'factors': fs.confirmed_factors
                }
                for fs in self.factor_history[-5:]
            ]
        }
