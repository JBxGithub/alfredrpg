"""
Professional Trading Engine - 專業級交易引擎

Complete trading system integration:
- Technical indicators (MACD, ADX, EMA, BOLL, VIX)
- Multi-timeframe analysis (MTF)
- Risk management (1% max risk, 2% daily stop)
- Professional entry/exit signals

Author: Professional Trading System  
Version: 2.0.0 (Kimi K2.5 Compatible)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import json
from pathlib import Path

from src.professional.indicators import (
    calculate_all_indicators, check_entry_signal, check_exit_signal,
    get_market_regime, get_vix_filter, TrendStrength
)
from src.professional.mtf_analyzer import (
    analyze_mtf, MTFResult, MTFSignal, get_mtf_with_vix, MTFTrend
)
from src.professional.risk_manager import (
    ProfessionalRiskManager, TradeResult, TradeAction, RiskLevel
)


class SignalType(Enum):
    """Trading signal types"""
    STRONG_BUY = "strong_buy"      # All conditions met
    BUY = "buy"                   # Entry conditions met
    HOLD = "hold"                 # No signal
    SELL = "sell"                 # Exit signal
    STRONG_SELL = "strong_sell"  # Emergency exit


@dataclass
class EntryConditions:
    """Entry condition check results"""
    adx_ok: bool = False
    plus_di_ok: bool = False
    macd_cross_ok: bool = False
    price_above_ema20_ok: bool = False
    volume_spike_ok: bool = False
    weekly_aligned: bool = False
    monthly_aligned: bool = False
    
    def all_met(self) -> bool:
        return all([
            self.adx_ok,
            self.plus_di_ok,
            self.macd_cross_ok,
            self.price_above_ema20_ok,
            self.volume_spike_ok,
            self.weekly_aligned,
            self.monthly_aligned
        ])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "adx_ok": self.adx_ok,
            "plus_di_ok": self.plus_di_ok,
            "macd_cross_ok": self.macd_cross_ok,
            "price_above_ema20_ok": self.price_above_ema20_ok,
            "volume_spike_ok": self.volume_spike_ok,
            "weekly_aligned": self.weekly_aligned,
            "monthly_aligned": self.monthly_aligned,
            "all_met": self.all_met()
        }


@dataclass
class TradeSignal:
    """Complete trading signal"""
    timestamp: datetime
    symbol: str
    signal_type: SignalType
    confidence: float  # 0-100%
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    position_size: Optional[int] = None
    reasons: List[str] = field(default_factory=list)
    entry_conditions: Optional[EntryConditions] = None
    mtf_result: Optional[MTFResult] = None
    indicators: Optional[Dict[str, Any]] = None
    vix: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "target_price": self.target_price,
            "risk_reward_ratio": self.risk_reward_ratio,
            "position_size": self.position_size,
            "reasons": self.reasons,
            "entry_conditions": self.entry_conditions.to_dict() if self.entry_conditions else None,
            "mtf_result": self.mtf_result.to_dict() if self.mtf_result else None,
            "vix": self.vix,
        }


@dataclass
class Position:
    """Active position"""
    symbol: str
    entry_price: float
    entry_time: datetime
    quantity: int
    stop_loss: float
    target: float
    atr_at_entry: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.entry_price
    
    @property
    def risk_amount(self) -> float:
        return (self.entry_price - self.stop_loss) * self.quantity
    
    @property
    def risk_percent(self) -> float:
        if self.market_value > 0:
            return (self.risk_amount / self.market_value) * 100
        return 0.0


class ProfessionalTradingEngine:
    """
    Professional Trading Engine
    
    Integrates:
    - Technical indicators
    - Multi-timeframe analysis
    - Risk management
    - Position sizing
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        risk_manager: Optional[ProfessionalRiskManager] = None
    ):
        self.config_path = config_path
        self.risk_manager = risk_manager or ProfessionalRiskManager()
        
        # Data caching
        self.daily_data: Optional[pd.DataFrame] = None
        self.weekly_data: Optional[pd.DataFrame] = None
        self.monthly_data: Optional[pd.DataFrame] = None
        
        # Current state
        self.current_vix: float = 0.0
        self.current_symbol: Optional[str] = None
        self.current_position: Optional[Position] = None
        
        # Signal history
        self.signal_history: List[TradeSignal] = []
        
        # Load config
        if config_path:
            self._load_config(config_path)
        
        # Default parameters
        self.target_risk_reward = 2.0  # R:R >= 2:1
        self.atr_stop_multiplier = 2.0   # 2 ATR for stop loss
        self.min_confidence = 70.0      # Minimum confidence %
    
    def _load_config(self, config_path: str):
        """Load configuration"""
        try:
            path = Path(config_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Update parameters
                if 'target_risk_reward' in config:
                    self.target_risk_reward = config['target_risk_reward']
                if 'atr_stop_multiplier' in config:
                    self.atr_stop_multiplier = config['atr_stop_multiplier']
                if 'min_confidence' in config:
                    self.min_confidence = config['min_confidence']
        except Exception as e:
            print(f"Config load error: {e}")
    
    def set_data(
        self,
        daily: Optional[pd.DataFrame] = None,
        weekly: Optional[pd.DataFrame] = None,
        monthly: Optional[pd.DataFrame] = None
    ):
        """Set OHLCV data for different timeframes"""
        self.daily_data = daily
        self.weekly_data = weekly
        self.monthly_data = monthly
    
    def set_vix(self, vix: float):
        """Set VIX value"""
        self.current_vix = vix
        self.risk_manager.update_vix(vix)
    
    def calculate_indicators(self) -> Dict[str, Any]:
        """Calculate all technical indicators"""
        if self.daily_data is None or len(self.daily_data) < 30:
            return {}
        
        return calculate_all_indicators(self.daily_data)
    
    def check_entry_conditions(
        self,
        indicators: Dict[str, Any],
        mtf_result: Optional[MTFResult] = None
    ) -> Tuple[EntryConditions, List[str]]:
        """
        Check all entry conditions
        
        Entry Requirements (ALL must be satisfied):
        1. ADX > 25 AND rising
        2. +DI > -DI  
        3. MACD bullish crossover
        4. Price > 20 EMA
        5. Volume > 1.5 × 20-day average
        6. Weekly aligned
        7. Not against monthly trend
        """
        conditions = EntryConditions()
        reasons = []
        
        # Check 1: ADX > 25
        adx = indicators['adx']
        current_adx = adx.adx.iloc[-1]
        conditions.adx_ok = current_adx > 25
        reasons.append(f"ADX={current_adx:.1f} {'✓' if conditions.adx_ok else '✗'} > 25")
        
        # Check 2: +DI > -DI
        conditions.plus_di_ok = adx.plus_di.iloc[-1] > adx.minus_di.iloc[-1]
        reasons.append(f"+DI {'✓' if conditions.plus_di_ok else '✗'} > -DI")
        
        # Check 3: MACD crossover
        macd = indicators['macd']
        conditions.macd_cross_ok = macd.crossover.iloc[-1] == 1
        reasons.append(f"MACD Cross {'✓' if conditions.macd_cross_ok else '✗'}")
        
        # Check 4: Price > 20 EMA
        close = indicators['close']
        ema = indicators['ema']
        conditions.price_above_ema20_ok = close.iloc[-1] > ema.ema_20.iloc[-1]
        reasons.append(f"Price {'✓' if conditions.price_above_ema20_ok else '✗'} > EMA20")
        
        # Check 5: Volume spike
        vol = indicators['volume']
        conditions.volume_spike_ok = vol.volume_spike.iloc[-1]
        reasons.append(f"Volume {'✓' if conditions.volume_spike_ok else '✗'} > 1.5x MA20")
        
        # Check 6: Weekly aligned
        if mtf_result and mtf_result.weekly:
            conditions.weekly_aligned = (
                mtf_result.weekly.trend == MTFTrend.BULLISH and
                mtf_result.weekly.is_trending
            )
        elif self.weekly_data is not None and len(self.weekly_data) > 20:
            # Quick weekly check
            weekly_indicators = calculate_all_indicators(self.weekly_data)
            if weekly_indicators:
                conditions.weekly_aligned = (
                    weekly_indicators['adx'].adx.iloc[-1] > 20 and
                    weekly_indicators['adx'].plus_di.iloc[-1] > weekly_indicators['adx'].minus_di.iloc[-1]
                )
        reasons.append(f"Weekly {'✓' if conditions.weekly_aligned else '✗'} aligned")
        
        # Check 7: Monthly trend (filter only)
        if mtf_result and mtf_result.monthly:
            conditions.monthly_aligned = mtf_result.monthly.trend != MTFTrend.BEARISH
        elif self.monthly_data is not None and len(self.monthly_data) > 10:
            monthly_indicators = calculate_all_indicators(self.monthly_data)
            if monthly_indicators:
                conditions.monthly_aligned = (
                    monthly_indicators['adx'].plus_di.iloc[-1] > monthly_indicators['adx'].minus_di.iloc[-1]
                )
        reasons.append(f"Monthly {'✓' if conditions.monthly_aligned else '✗'} not bearish")
        
        return conditions, reasons
    
    def generate_entry_signal(
        self,
        symbol: str,
        indicators: Optional[Dict[str, Any]] = None,
        mtf_result: Optional[MTFResult] = None
    ) -> Optional[TradeSignal]:
        """
        Generate entry signal
        
        Returns:
            TradeSignal if entry allowed, None otherwise
        """
        # Check risk manager
        can_enter, reason = self.risk_manager.canEnter(self.current_vix)
        if not can_enter:
            return None
        
        # Calculate indicators if not provided
        if indicators is None:
            indicators = self.calculate_indicators()
        
        if not indicators:
            return None
        
        # Check entry conditions
        conditions, reasons = self.check_entry_conditions(indicators, mtf_result)
        
        if not conditions.all_met():
            return None
        
        # Calculate confidence
        confidence = self._calculate_confidence(indicators, conditions)
        
        if confidence < self.min_confidence:
            return None
        
        # Get entry price
        entry_price = indicators['close'].iloc[-1]
        
        # Calculate stop loss (2 ATR)
        atr = indicators['atr'].iloc[-1]
        stop_loss = entry_price - (atr * self.atr_stop_multiplier)
        stop_loss_percent = (atr * self.atr_stop_multiplier / entry_price) * 100
        
        # Calculate target (2:1 R:R)
        target_price = entry_price + ((entry_price - stop_loss) * self.target_risk_reward)
        
        # Calculate position size
        position_size, risk_amount = self.risk_manager.calculate_position_size(
            entry_price,
            stop_loss_percent,
            self.current_vix
        )
        
        if position_size <= 0:
            return None
        
        # Create signal
        signal = TradeSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            signal_type=SignalType.BUY,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target_price=target_price,
            risk_reward_ratio=self.target_risk_reward,
            position_size=position_size,
            reasons=reasons,
            entry_conditions=conditions,
            mtf_result=mtf_result,
            indicators=indicators,
            vix=self.current_vix
        )
        
        self.signal_history.append(signal)
        return signal
    
    def _calculate_confidence(
        self,
        indicators: Dict[str, Any],
        conditions: EntryConditions
    ) -> float:
        """Calculate signal confidence (0-100%)"""
        base_confidence = 50.0
        
        # ADX contribution
        adx = indicators['adx'].adx.iloc[-1]
        if adx > 50:
            base_confidence += 15
        elif adx > 35:
            base_confidence += 10
        elif adx > 25:
            base_confidence += 5
        
        # Volume contribution
        vol_ratio = indicators['volume'].volume_ratio.iloc[-1]
        if vol_ratio > 2.0:
            base_confidence += 10
        elif vol_ratio > 1.5:
            base_confidence += 5
        
        # MACD histogram contribution
        histogram = indicators['macd'].histogram.iloc[-1]
        if histogram > 0:
            base_confidence += 5
        
        # VIX contribution
        if self.current_vix < 20:
            base_confidence += 10
        elif self.current_vix < 25:
            base_confidence += 5
        elif self.current_vix >= 30:
            base_confidence -= 20
        
        # Market regime
        regime = get_market_regime(indicators)
        if regime == "TRENDING":
            base_confidence += 10
        elif regime == "CONSOLIDATING":
            base_confidence -= 10
        
        return min(100, max(0, base_confidence))
    
    def check_exit_signal(
        self,
        position: Position,
        indicators: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        Check exit conditions
        
        Exit signals:
        1. MACD bearish crossover
        2. ADX < 20 (trend weakened)
        3. Stop loss hit
        4. VIX > 30 (emergency exit)
        """
        # Check VIX emergency exit
        if self.current_vix >= 30:
            return True, f"VIX={self.current_vix:.1f} >= 30 - Emergency exit"
        
        # Calculate indicators if not provided
        if indicators is None:
            indicators = self.calculate_indicators()
        
        if not indicators:
            return False, ""
        
        # Check MACD bearish crossover
        macd = indicators['macd']
        if macd.crossover.iloc[-1] == -1:
            return True, "MACD bearish crossover"
        
        # Check ADX weakening
        adx = indicators['adx'].adx.iloc[-1]
        if adx < 20:
            return True, f"ADX={adx:.1f} < 20 - Trend weakened"
        
        # Check stop loss
        current_price = indicators['close'].iloc[-1]
        if current_price <= position.stop_loss:
            return True, "Stop loss hit"
        
        # Check take profit (optional: trail stop)
        # Could implement trailing stop here
        
        return False, ""
    
    def open_position(
        self,
        symbol: str,
        entry_price: float,
        quantity: int,
        stop_loss: float,
        target: float,
        atr: float = 0.0
    ) -> Position:
        """Open a new position"""
        position = Position(
            symbol=symbol,
            entry_price=entry_price,
            entry_time=datetime.now(),
            quantity=quantity,
            stop_loss=stop_loss,
            target=target,
            atr_at_entry=atr
        )
        
        self.current_position = position
        self.current_symbol = symbol
        
        return position
    
    def close_position(
        self,
        exit_price: float,
        pnl: float = 0.0
    ) -> Optional[TradeResult]:
        """Close current position and record trade"""
        if self.current_position is None:
            return None
        
        position = self.current_position
        trade = TradeResult(
            timestamp=position.entry_time,
            symbol=position.symbol,
            entry_price=position.entry_price,
            quantity=position.quantity,
            side="LONG",
            pnl=pnl,
            pnl_percent=(pnl / (position.entry_price * position.quantity)) * 100 if position.market_value > 0 else 0,
            exited=True,
            exit_price=exit_price,
            exit_timestamp=datetime.now(),
            holding_period=(datetime.now() - position.entry_time).days,
            max_risk_taken=position.risk_percent
        )
        
        # Record trade
        self.risk_manager.record_trade(trade)
        
        # Clear position
        self.current_position = None
        self.current_symbol = None
        
        return trade
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current trading state"""
        return {
            "has_position": self.current_position is not None,
            "symbol": self.current_symbol,
            "current_vix": self.current_vix,
            "risk_state": self.risk_manager.get_risk_state(),
            "position": {
                "entry_price": self.current_position.entry_price,
                "quantity": self.current_position.quantity,
                "stop_loss": self.current_position.stop_loss,
                "target": self.current_position.target,
                "market_value": self.current_position.market_value,
                "risk_percent": self.current_position.risk_percent
            } if self.current_position else None
        }
    
    def analyze(
        self,
        symbol: str,
        daily: Optional[pd.DataFrame] = None,
        weekly: Optional[pd.DataFrame] = None,
        monthly: Optional[pd.DataFrame] = None,
        vix: float = 0.0
    ) -> Dict[str, Any]:
        """
        Complete analysis
        
        Args:
            symbol: Stock symbol
            daily: Daily OHLCV data
            weekly: Weekly OHLCV data
            monthly: Monthly OHLCV data
            vix: VIX value
            
        Returns:
            Complete analysis result
        """
        # Set data
        self.set_data(daily, weekly, monthly)
        self.set_vix(vix)
        
        # Calculate indicators
        indicators = self.calculate_indicators()
        
        # MTF analysis
        mtf_result = analyze_mtf(daily, weekly, monthly)
        
        # Apply VIX filter
        mtf_result_dict = get_mtf_with_vix(mtf_result, vix)
        
        # Generate entry signal
        entry_signal = self.generate_entry_signal(symbol, indicators, mtf_result)
        
        # Market regime
        regime = get_market_regime(indicators) if indicators else "UNKNOWN"
        
        # VIX filter
        vix_filter = get_vix_filter(vix)
        
        return {
            "symbol": symbol,
            "has_entry_signal": entry_signal is not None,
            "entry_signal": entry_signal.to_dict() if entry_signal else None,
            "mtf_result": mtf_result_dict,
            "market_regime": regime,
            "vix_filter": vix_filter,
            "risk_state": self.risk_manager.get_risk_state(),
            "indicators_summary": {
                "adx": indicators['adx'].adx.iloc[-1] if 'adx' in indicators else 0,
                "plus_di": indicators['adx'].plus_di.iloc[-1] if 'adx' in indicators else 0,
                "minus_di": indicators['adx'].minus_di.iloc[-1] if 'adx' in indicators else 0,
                "macd_histogram": indicators['macd'].histogram.iloc[-1] if 'macd' in indicators else 0,
                "ema_20": indicators['ema'].ema_20.iloc[-1] if 'ema' in indicators else 0,
                "volume_ratio": indicators['volume'].volume_ratio.iloc[-1] if 'volume' in indicators else 0,
                "atr": indicators['atr'].iloc[-1] if 'atr' in indicators else 0,
            } if indicators else {}
        }


def create_engine(
    config_path: Optional[str] = None,
    risk_manager: Optional[ProfessionalRiskManager] = None
) -> ProfessionalTradingEngine:
    """Factory function to create trading engine"""
    return ProfessionalTradingEngine(config_path, risk_manager)