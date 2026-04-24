"""
風險管理系統 - Risk Management System with Partial Take Profit
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import json
from pathlib import Path


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskEventType(Enum):
    POSITION_LIMIT_EXCEEDED = "position_limit_exceeded"
    TOTAL_POSITION_LIMIT_EXCEEDED = "total_position_limit_exceeded"
    SECTOR_CONCENTRATION_EXCEEDED = "sector_concentration_exceeded"
    DAILY_TRADE_LIMIT_EXCEEDED = "daily_trade_limit_exceeded"
    ORDER_SIZE_EXCEEDED = "order_size_exceeded"
    PRICE_ANOMALY_DETECTED = "price_anomaly_detected"
    DAILY_LOSS_LIMIT_EXCEEDED = "daily_loss_limit_exceeded"
    DRAWDOWN_LIMIT_EXCEEDED = "drawdown_limit_exceeded"
    MARGIN_CALL_WARNING = "margin_call_warning"
    MARGIN_CALL_CRITICAL = "margin_call_critical"
    PARTIAL_PROFIT_TAKEN = "partial_profit_taken"
    STOP_LOSS_ADJUSTED = "stop_loss_adjusted"


@dataclass
class RiskEvent:
    event_type: RiskEventType
    level: RiskLevel
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    symbol: Optional[str] = None
    action_taken: Optional[str] = None


@dataclass
class PartialProfitLevel:
    profit_pct: float
    close_pct: float
    triggered: bool = False
    triggered_at: Optional[datetime] = None
    closed_qty: int = 0
    profit_amount: float = 0.0


@dataclass
class Position:
    symbol: str
    quantity: int
    avg_price: float
    market_price: float
    sector: Optional[str] = None
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    original_qty: int = 0
    partial_profit_levels: List[PartialProfitLevel] = field(default_factory=list)
    stop_loss_price: float = 0.0
    cost_price: float = 0.0
    total_closed_qty: int = 0
    total_profit_taken: float = 0.0
    
    def __post_init__(self):
        self.market_value = self.quantity * self.market_price
        self.unrealized_pnl = (self.market_price - self.avg_price) * self.quantity
        if self.avg_price > 0:
            self.unrealized_pnl_pct = (self.market_price - self.avg_price) / self.avg_price
        if self.original_qty == 0:
            self.original_qty = self.quantity
        if self.cost_price == 0:
            self.cost_price = self.avg_price
        if self.stop_loss_price == 0:
            self.stop_loss_price = self.avg_price


@dataclass
class PartialProfitAction:
    symbol: str
    level_index: int
    close_qty: int
    current_price: float
    profit_pct: float
    profit_amount: float
    new_stop_loss: float
    reason: str


@dataclass
class RiskLimits:
    max_single_position_value: float = 100000.0
    max_single_position_percent: float = 20.0
    max_total_position_value: float = 500000.0
    max_total_position_percent: float = 80.0
    max_sector_concentration_percent: float = 40.0
    max_daily_trades: int = 20
    max_order_value: float = 50000.0
    max_order_quantity: int = 1000
    price_volatility_threshold: float = 5.0
    price_spike_threshold: float = 10.0
    max_daily_loss: float = 50000.0
    max_drawdown_percent: float = 10.0
    max_drawdown_percent_hard: float = 15.0
    margin_warning_percent: float = 80.0
    margin_critical_percent: float = 90.0
    enable_partial_profit: bool = True
    partial_profit_levels: List[Dict[str, float]] = field(default_factory=lambda: [
        {"profit_pct": 0.02, "close_pct": 0.30},
        {"profit_pct": 0.04, "close_pct": 0.30},
    ])
    breakeven_stop_loss: bool = True
    enable_position_risk: bool = True
    enable_trade_risk: bool = True
    enable_capital_risk: bool = True
    auto_stop_on_critical: bool = True


class RiskManager:
    """
    風險管理器 - 包含部分獲利機制
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.limits = RiskLimits()
        self.positions: Dict[str, Position] = {}
        self.daily_stats = {
            "date": date.today(),
            "trade_count": 0,
            "daily_pnl": 0.0,
            "orders": []
        }
        self.risk_events: List[RiskEvent] = []
        self.peak_capital: float = 0.0
        self.current_capital: float = 0.0
        self.margin_used: float = 0.0
        self.margin_available: float = 0.0
        self._trading_enabled: bool = True
        self.partial_profit_state: Dict[str, Dict[str, Any]] = {}
        self.price_history: Dict[str, List[Dict[str, Any]]] = {}
        
        if config_path:
            self._load_config(config_path)
        
        print("風險管理器初始化完成 (含部分獲利功能)")
    
    def _load_config(self, config_path: str):
        """加載風險配置文件"""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                for key, value in config.items():
                    if hasattr(self.limits, key):
                        setattr(self.limits, key, value)
                print(f"已加載風險配置文件: {config_path}")
        except Exception as e:
            print(f"加載風險配置文件失敗: {e}")
    
    def update_capital(self, total_capital: float, margin_used: float = 0.0, margin_available: float = 0.0):
        """更新資金狀況"""
        self.current_capital = total_capital
        self.margin_used = margin_used
        self.margin_available = margin_available
        if total_capital > self.peak_capital:
            self.peak_capital = total_capital
    
    def update_positions(self, positions: List[Position]):
        """更新持倉信息，保留部分獲利狀態"""
        for position in positions:
            if position.symbol in self.positions:
                existing = self.positions[position.symbol]
                position.partial_profit_levels = existing.partial_profit_levels
                position.stop_loss_price = existing.stop_loss_price
                position.cost_price = existing.cost_price
                position.total_closed_qty = existing.total_closed_qty
                position.total_profit_taken = existing.total_profit_taken
                position.original_qty = existing.original_qty
        
        self.positions = {p.symbol: p for p in positions}
    
    def check_partial_profit(self, symbol: str, current_price: float) -> Optional[PartialProfitAction]:
        """
        檢查是否需要執行部分獲利
        
        邏輯：
        - 第一階段：盈利達到 2% 時，平倉 30%
        - 第二階段：盈利達到 4% 時，再平倉 30%
        - 剩餘 40% 等待止盈或止損
        """
        if not self.limits.enable_partial_profit:
            return None
        
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        
        if position.quantity <= 0:
            return None
        
        # 初始化部分獲利階段
        if not position.partial_profit_levels:
            position.partial_profit_levels = [
                PartialProfitLevel(
                    profit_pct=level["profit_pct"],
                    close_pct=level["close_pct"]
                )
                for level in self.limits.partial_profit_levels
            ]
        
        # 計算當前盈利百分比
        profit_pct = (current_price - position.avg_price) / position.avg_price if position.avg_price > 0 else 0
        
        # 檢查每個獲利階段
        for i, level in enumerate(position.partial_profit_levels):
            if level.triggered:
                continue  # 已觸發過，跳過
            
            if profit_pct >= level.profit_pct:
                # 計算建議平倉數量
                close_qty = int(position.original_qty * level.close_pct)
                close_qty = min(close_qty, position.quantity)
                
                if close_qty <= 0:
                    continue
                
                profit_amount = (current_price - position.avg_price) * close_qty
                new_stop_loss = position.cost_price if self.limits.breakeven_stop_loss else position.stop_loss_price
                
                action = PartialProfitAction(
                    symbol=symbol,
                    level_index=i,
                    close_qty=close_qty,
                    current_price=current_price,
                    profit_pct=profit_pct,
                    profit_amount=profit_amount,
                    new_stop_loss=new_stop_loss,
                    reason=f"達到第{i+1}階段獲利目標: 盈利 {profit_pct*100:.2f}% >= {level.profit_pct*100:.2f}%"
                )
                
                print(f"[部分獲利] {symbol} 觸發第{i+1}階段: 盈利 {profit_pct*100:.2f}%, 建議平倉 {close_qty} 股")
                return action
        
        return None
    
    def apply_partial_profit(self, symbol: str, level_index: int, closed_qty: int, 
                            close_price: float, realized_profit: float) -> bool:
        """
        應用部分獲利結果，更新持倉狀態
        每次部分獲利後，調整止損位至成本價（保本）
        """
        if symbol not in self.positions:
            print(f"[部分獲利] 持倉不存在: {symbol}")
            return False
        
        position = self.positions[symbol]
        
        if level_index >= len(position.partial_profit_levels):
            print(f"[部分獲利] 無效的階段索引: {level_index}")
            return False
        
        level = position.partial_profit_levels[level_index]
        
        # 標記該階段為已觸發，避免重複執行
        level.triggered = True
        level.triggered_at = datetime.now()
        level.closed_qty = closed_qty
        level.profit_amount = realized_profit
        
        # 更新持倉統計
        position.total_closed_qty += closed_qty
        position.total_profit_taken += realized_profit
        position.quantity -= closed_qty
        
        # 調整止損至成本價（保本）
        old_stop_loss = position.stop_loss_price
        if self.limits.breakeven_stop_loss:
            position.stop_loss_price = position.cost_price
        
        # 記錄風險事件
        event = RiskEvent(
            event_type=RiskEventType.PARTIAL_PROFIT_TAKEN,
            level=RiskLevel.LOW,
            message=f"{symbol} 執行第{level_index+1}階段部分獲利: 平倉 {closed_qty} 股, 獲利 ${realized_profit:,.2f}",
            timestamp=datetime.now(),
            symbol=symbol,
            details={
                "level_index": level_index,
                "closed_qty": closed_qty,
                "close_price": close_price,
                "realized_profit": realized_profit,
                "remaining_qty": position.quantity,
                "old_stop_loss": old_stop_loss,
                "new_stop_loss": position.stop_loss_price
            },
            action_taken=f"stop_loss_adjusted_to_{position.stop_loss_price}"
        )
        self._record_event(event)
        
        print(f"[部分獲利] {symbol} 第{level_index+1}階段執行完成: 平倉 {closed_qty} 股, 剩餘 {position.quantity} 股, 止損調整至 {position.stop_loss_price:.2f}")
        return True
    
    def check_stop_loss(self, symbol: str, current_price: float) -> Tuple[bool, Optional[str]]:
        """檢查是否觸發止損"""
        if symbol not in self.positions:
            return False, None
        
        position = self.positions[symbol]
        
        if position.quantity <= 0:
            return False, None
        
        if current_price <= position.stop_loss_price:
            return True, f"價格 {current_price:.2f} 觸及止損價 {position.stop_loss_price:.2f}"
        
        return False, None
    
    def get_partial_profit_status(self, symbol: str) -> Optional[Dict[str, Any]]:
        """獲取部分獲利狀態"""
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        
        return {
            "symbol": symbol,
            "original_qty": position.original_qty,
            "current_qty": position.quantity,
            "total_closed_qty": position.total_closed_qty,
            "total_profit_taken": position.total_profit_taken,
            "cost_price": position.cost_price,
            "avg_price": position.avg_price,
            "stop_loss_price": position.stop_loss_price,
            "levels": [
                {
                    "index": i,
                    "profit_pct": level.profit_pct * 100,
                    "close_pct": level.close_pct * 100,
                    "triggered": level.triggered,
                    "triggered_at": level.triggered_at.isoformat() if level.triggered_at else None,
                    "closed_qty": level.closed_qty,
                    "profit_amount": level.profit_amount
                }
                for i, level in enumerate(position.partial_profit_levels)
            ]
        }
    
    def _record_event(self, event: RiskEvent):
        """記錄風險事件"""
        self.risk_events.append(event)
        print(f"[風控-{event.level.value.upper()}] {event.message}")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """獲取風險摘要"""
        total_position_value = sum(p.market_value for p in self.positions.values())
        
        drawdown = 0.0
        if self.peak_capital > 0:
            drawdown = (self.peak_capital - self.current_capital) / self.peak_capital * 100
        
        margin_ratio = 0.0
        if self.margin_available + self.margin_used > 0:
            margin_ratio = self.margin_used / (self.margin_available + self.margin_used) * 100
        
        return {
            "trading_enabled": self._trading_enabled,
            "total_capital": self.current_capital,
            "peak_capital": self.peak_capital,
            "drawdown_percent": drawdown,
            "daily_pnl": self.daily_stats["daily_pnl"],
            "daily_trade_count": self.daily_stats["trade_count"],
            "total_position_value": total_position_value,
            "position_count": len(self.positions),
            "margin_used": self.margin_used,
            "margin_available": self.margin_available,
            "margin_ratio": margin_ratio,
            "partial_profit_enabled": self.limits.enable_partial_profit,
            "recent_events": [
                {
                    "type": e.event_type.value,
                    "level": e.level.value,
                    "message": e.message,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in self.risk_events[-10:]
            ]
        }
