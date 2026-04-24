"""
Professional Risk Manager - 專業級風險管理系統

Risk Management Rules:
- Single trade max risk: 1%
- Daily max loss: 2% → Stop trading for the day
- Consecutive 2 losses → Stop trading for the day
- VIX > 25: Reduce position by half
- VIX > 30: Exit all positions

Author: Professional Trading System
Version: 2.0.0 (Kimi K2.5 Compatible)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from pathlib import Path
import json


class RiskLevel(Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"
    CRITICAL = "critical"


class TradeAction(Enum):
    """Trading action recommendation"""
    FULL_POSITION = "full_position"      # Normal trading
    HALF_POSITION = "half_position"     # VIX 25-30
    NO_NEW_POSITION = "no_new_position"  # VIX > 30 or daily loss hit
    CLOSE_ALL = "close_all"            # Extreme risk
    STOP_TRADING = "stop_trading"      # Daily stop


@dataclass
class TradeResult:
    """Single trade result"""
    timestamp: datetime
    symbol: str
    entry_price: float
    quantity: int
    side: str  # LONG/SHORT
    pnl: float = 0.0
    pnl_percent: float = 0.0
    exited: bool = False
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    holding_period: int = 0  # days
    max_risk_taken: float = 0.0


@dataclass
class DailyStats:
    """Daily trading statistics"""
    date: date
    trade_count: int = 0
    win_count: int = 0
    loss_count: int = 0
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    trades: List[TradeResult] = field(default_factory=list)
    consecutive_losses: int = 0
    

@dataclass
class RiskLimits:
    """Professional risk limits"""
    # Position sizing
    max_risk_per_trade_percent: float = 1.0      # 1% max risk per trade
    max_daily_loss_percent: float = 2.0             # 2% daily loss limit
    max_consecutive_losses: int = 2                 # 2 consecutive losses stop
    
    # VIX-based position sizing
    vix_normal_threshold: float = 20.0             # Normal trading
    vix_caution_threshold: float = 25.0            # Half position
    vix_extreme_threshold: float = 30.0               # Exit all
    
    # Position adjustment factors
    normal_position_size: float = 1.0              # 100% position
    caution_position_size: float = 0.5             # 50% position
    extreme_position_size: float = 0.0               # 0% position
    
    # Trading hours
    trading_hours_start: str = "09:30"                  # Market open
    trading_hours_end: str = "15:45"                 # Market close
    

@dataclass
class RiskState:
    """Current risk state"""
    trading_enabled: bool = True
    action: TradeAction = TradeAction.FULL_POSITION
    current_vix: float = 0.0
    daily_loss_percent: float = 0.0
    consecutive_losses: int = 0
    today_pnl: float = 0.0
    today_trades: int = 0
    reason: str = ""


class ProfessionalRiskManager:
    """
    Professional Risk Manager with VIX-based position sizing
    
    Designed for Kimi K2.5 model compatibility
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.limits = RiskLimits()
        self.state = RiskState()
        
        # Historical data
        self.daily_stats: Dict[date, DailyStats] = {}
        self.current_capital: float = 100000.0  # Default starting capital
        self.peak_capital: float = 100000.0
        
        # Load config if provided
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load risk configuration from JSON"""
        try:
            path = Path(config_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                for key, value in config.items():
                    if hasattr(self.limits, key):
                        setattr(self.limits, key, value)
        except Exception as e:
            print(f"Config load error: {e}")
    
    def save_config(self, config_path: str):
        """Save risk configuration to JSON"""
        config = {
            "max_risk_per_trade_percent": self.limits.max_risk_per_trade_percent,
            "max_daily_loss_percent": self.limits.max_daily_loss_percent,
            "max_consecutive_losses": self.limits.max_consecutive_losses,
            "vix_normal_threshold": self.limits.vix_normal_threshold,
            "vix_caution_threshold": self.limits.vix_caution_threshold,
            "vix_extreme_threshold": self.limits.vix_extreme_threshold,
            "normal_position_size": self.limits.normal_position_size,
            "caution_position_size": self.limits.caution_position_size,
            "extreme_position_size": self.limits.extreme_position_size,
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    
    def update_capital(self, capital: float):
        """Update current capital"""
        self.current_capital = capital
        if capital > self.peak_capital:
            self.peak_capital = capital
    
    def update_vix(self, vix: float):
        """Update VIX and recalculate risk state"""
        self.state.current_vix = vix
        
        if vix >= self.limits.vix_extreme_threshold:
            self.state.action = TradeAction.CLOSE_ALL
            self.state.trading_enabled = False
            self.state.reason = f"VIX={vix:.1f} >= {self.limits.vix_extreme_threshold} - Extreme risk"
        
        elif vix >= self.limits.vix_caution_threshold:
            self.state.action = TradeAction.HALF_POSITION
            self.state.reason = f"VIX={vix:.1f} >= {self.limits.vix_caution_threshold} - Reduce position"
        
        elif vix >= self.limits.vix_normal_threshold:
            self.state.action = TradeAction.FULL_POSITION
            self.state.reason = f"VIX={vix:.1f} >= {self.limits.vix_normal_threshold} - Caution"
        
        else:
            self.state.action = TradeAction.FULL_POSITION
            self.state.trading_enabled = True
            self.state.reason = f"VIX={vix:.1f} < {self.limits.vix_normal_threshold} - Normal"
    
    def check_daily_stop(self) -> Tuple[bool, str]:
        """
        Check if daily stop conditions are met
        
        Returns:
            (should_stop, reason)
        """
        today = date.today()
        
        # Get today's stats
        if today not in self.daily_stats:
            return False, ""
        
        stats = self.daily_stats[today]
        
        # Check 1: Daily loss > 2%
        self.state.daily_loss_percent = (stats.total_pnl_percent)
        
        if abs(stats.total_pnl_percent) >= self.limits.max_daily_loss_percent:
            self.state.trading_enabled = False
            self.state.action = TradeAction.STOP_TRADING
            self.state.reason = f"Daily loss {stats.total_pnl_percent:.2f}% >= {self.limits.max_daily_loss_percent}%"
            return True, self.state.reason
        
        # Check 2: Consecutive 2 losses
        if stats.consecutive_losses >= self.limits.max_consecutive_losses:
            self.state.trading_enabled = False
            self.state.action = TradeAction.STOP_TRADING
            self.state.reason = f"Consecutive {stats.consecutive_losses} losses"
            return True, self.state.reason
        
        return False, ""
    
    def record_trade(self, trade: TradeResult):
        """Record a completed trade"""
        today = date.today()
        
        if today not in self.daily_stats:
            self.daily_stats[today] = DailyStats(date=today)
        
        stats = self.daily_stats[today]
        stats.trade_count += 1
        stats.trades.append(trade)
        
        if trade.pnl > 0:
            stats.win_count += 1
            if stats.consecutive_losses > 0:
                stats.consecutive_losses = 0
        else:
            stats.loss_count += 1
            stats.consecutive_losses += 1
        
        stats.total_pnl += trade.pnl
        stats.total_pnl_percent += trade.pnl_percent
        
        # Update state
        self.state.today_trades = stats.trade_count
        self.state.today_pnl = stats.total_pnl
        self.state.consecutive_losses = stats.consecutive_losses
        
        # Calculate current capital
        self.current_capital += trade.pnl
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital
        
        # Check daily stop after trade
        self.check_daily_stop()
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_percent: float,
        vix: Optional[float] = None
    ) -> Tuple[int, float]:
        """
        Calculate position size based on risk parameters
        
        Args:
            entry_price: Entry price
            stop_loss_percent: Stop loss percentage (e.g., 2.0 for 2%)
            vix: Current VIX value
            
        Returns:
            (quantity, risk_amount)
        """
        # Apply VIX adjustment
        position_factor = 1.0
        
        if vix is not None:
            if vix >= self.limits.vix_extreme_threshold:
                position_factor = self.limits.extreme_position_size
            elif vix >= self.limits.vix_caution_threshold:
                position_factor = self.limits.caution_position_size
        
        # Calculate max risk amount
        max_risk_amount = self.current_capital * (self.limits.max_risk_per_trade_percent / 100) * position_factor
        
        # Calculate quantity
        risk_per_share = entry_price * (stop_loss_percent / 100)
        
        if risk_per_share > 0:
            quantity = int(max_risk_amount / risk_per_share)
        else:
            quantity = 0
        
        # Ensure valid quantity
        quantity = max(0, quantity)
        
        # Actual risk taken
        risk_taken = quantity * risk_per_share
        risk_percent = (risk_taken / self.current_capital * 100) if self.current_capital > 0 else 0
        
        return quantity, risk_taken
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        atr_multiplier: float = 2.0
    ) -> Tuple[float, float]:
        """
        Calculate stop loss price
        
        Args:
            entry_price: Entry price
            atr: Average True Range
            atr_multiplier: ATR multiplier for stop
            
        Returns:
            (stop_loss_price, stop_loss_percent)
        """
        stop_distance = atr * atr_multiplier
        stop_loss_price = entry_price - stop_distance
        stop_loss_percent = (stop_distance / entry_price) * 100
        
        return stop_loss_price, stop_loss_percent
    
    def get_risk_state(self) -> Dict[str, Any]:
        """Get current risk state"""
        return {
            "trading_enabled": self.state.trading_enabled,
            "action": self.state.action.value,
            "current_vix": self.state.current_vix,
            "daily_loss_percent": self.state.daily_loss_percent,
            "consecutive_losses": self.state.consecutive_losses,
            "today_pnl": self.state.today_pnl,
            "today_trades": self.state.today_trades,
            "reason": self.state.reason,
            "capital": self.current_capital,
            "peak_capital": self.peak_capital,
        }
    
    def get_position_multiplier(self) -> float:
        """Get position size multiplier based on current conditions"""
        if self.state.current_vix >= self.limits.vix_extreme_threshold:
            return 0.0
        elif self.state.current_vix >= self.limits.vix_caution_threshold:
            return self.limits.caution_position_size
        else:
            return self.limits.normal_position_size
    
    def canEnter(self, vix: Optional[float] = None) -> Tuple[bool, str]:
        """
        Check if can enter new position
        
        Returns:
            (can_enter, reason)
        """
        # Check trading enabled
        if not self.state.trading_enabled:
            return False, f"Trading disabled: {self.state.reason}"
        
        # Check VIX
        if vix is not None:
            if vix >= self.limits.vix_extreme_threshold:
                return False, f"VIX={vix:.1f} >= {self.limits.vix_extreme_threshold} - No entries"
        
        # Check daily loss
        if abs(self.state.daily_loss_percent) >= self.limits.max_daily_loss_percent:
            return False, f"Daily loss {self.state.daily_loss_percent:.2f}% >= {self.limits.max_daily_loss_percent}%"
        
        # Check consecutive losses
        if self.state.consecutive_losses >= self.limits.max_consecutive_losses:
            return False, f"Consecutive {self.state.consecutive_losses} losses"
        
        return True, "OK"
    
    def reset_daily(self):
        """Reset daily statistics (call at start of new day)"""
        today = date.today()
        if today not in self.daily_stats:
            self.daily_stats[today] = DailyStats(date=today)
        
        # Reset daily state
        self.state.today_trades = 0
        self.state.today_pnl = 0.0
        self.state.daily_loss_percent = 0.0
        self.state.trading_enabled = True
        self.state.action = TradeAction.FULL_POSITION
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """Get daily trading summary"""
        today = date.today()
        
        if today in self.daily_stats:
            stats = self.daily_stats[today]
            return {
                "date": str(stats.date),
                "trade_count": stats.trade_count,
                "win_count": stats.win_count,
                "loss_count": stats.loss_count,
                "win_rate": stats.win_count / stats.trade_count if stats.trade_count > 0 else 0,
                "total_pnl": stats.total_pnl,
                "total_pnl_percent": stats.total_pnl_percent,
                "consecutive_losses": stats.consecutive_losses,
            }
        
        return {
            "date": str(today),
            "trade_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "total_pnl_percent": 0,
            "consecutive_losses": 0,
        }
    
    def should_close_position(self, vix: float) -> Tuple[bool, str]:
        """
        Check if should close existing position due to VIX
        
        Returns:
            (should_close, reason)
        """
        if vix >= self.limits.vix_extreme_threshold:
            return True, f"VIX={vix:.1f} >= {self.limits.vix_extreme_threshold} - Extreme risk"
        
        return False, ""


def create_risk_manager(config_path: Optional[str] = None) -> ProfessionalRiskManager:
    """Factory function to create risk manager"""
    return ProfessionalRiskManager(config_path)