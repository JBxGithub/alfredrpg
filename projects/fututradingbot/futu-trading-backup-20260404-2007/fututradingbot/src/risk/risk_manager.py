"""
風險管理系統 - Risk Management System

提供全方位的交易風險控制，包括：
- 倉位風控：單一股票最大倉位、總倉位上限、行業集中度
- 交易風控：每日最大交易次數、單筆最大金額、價格異常檢測
- 資金風控：每日最大虧損、回撤控制、保證金監控
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import json
from pathlib import Path

from src.utils.logger import logger


class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskEventType(Enum):
    """風險事件類型"""
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


@dataclass
class RiskEvent:
    """風險事件"""
    event_type: RiskEventType
    level: RiskLevel
    message: str
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    symbol: Optional[str] = None
    action_taken: Optional[str] = None


@dataclass
class Position:
    """持倉信息"""
    symbol: str
    quantity: int
    avg_price: float
    market_price: float
    sector: Optional[str] = None
    market_value: float = 0.0
    unrealized_pnl: float = 0.0
    
    def __post_init__(self):
        self.market_value = self.quantity * self.market_price
        self.unrealized_pnl = (self.market_price - self.avg_price) * self.quantity


@dataclass
class RiskLimits:
    """風險限制配置"""
    # 倉位風控
    max_single_position_value: float = 100000.0  # 單一股票最大倉位價值
    max_single_position_percent: float = 20.0    # 單一股票最大倉位佔比(%)
    max_total_position_value: float = 500000.0   # 總倉位上限
    max_total_position_percent: float = 80.0     # 總倉位佔資金比例上限(%)
    max_sector_concentration_percent: float = 40.0  # 行業集中度上限(%)
    
    # 交易風控
    max_daily_trades: int = 20                   # 每日最大交易次數
    max_order_value: float = 50000.0             # 單筆最大金額
    max_order_quantity: int = 1000               # 單筆最大股數
    price_volatility_threshold: float = 5.0      # 價格波動異常閾值(%)
    price_spike_threshold: float = 10.0          # 價格暴漲暴跌閾值(%)
    
    # 資金風控
    max_daily_loss: float = 50000.0              # 每日最大虧損限制
    max_drawdown_percent: float = 10.0           # 最大回撤控制(%)
    max_drawdown_percent_hard: float = 15.0      # 強制停止回撤(%)
    margin_warning_percent: float = 80.0         # 保證金警告閾值(%)
    margin_critical_percent: float = 90.0        # 保證金危險閾值(%)
    
    # 控制開關
    enable_position_risk: bool = True
    enable_trade_risk: bool = True
    enable_capital_risk: bool = True
    auto_stop_on_critical: bool = True           # 嚴重風險時自動停止交易


class RiskManager:
    """
    風險管理器
    
    負責監控和控制交易風險，確保交易在安全範圍內進行。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化風險管理器
        
        Args:
            config_path: 風險配置文件路徑
        """
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
        
        # 價格歷史用於異常檢測
        self.price_history: Dict[str, List[Dict[str, Any]]] = {}
        
        if config_path:
            self._load_config(config_path)
        
        logger.info("風險管理器初始化完成")
    
    def _load_config(self, config_path: str):
        """加載風險配置文件"""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 更新風險限制
                for key, value in config.items():
                    if hasattr(self.limits, key):
                        setattr(self.limits, key, value)
                
                logger.info(f"已加載風險配置文件: {config_path}")
        except Exception as e:
            logger.error(f"加載風險配置文件失敗: {e}")
    
    def save_config(self, config_path: str):
        """保存風險配置到文件"""
        try:
            config = {
                "max_single_position_value": self.limits.max_single_position_value,
                "max_single_position_percent": self.limits.max_single_position_percent,
                "max_total_position_value": self.limits.max_total_position_value,
                "max_total_position_percent": self.limits.max_total_position_percent,
                "max_sector_concentration_percent": self.limits.max_sector_concentration_percent,
                "max_daily_trades": self.limits.max_daily_trades,
                "max_order_value": self.limits.max_order_value,
                "max_order_quantity": self.limits.max_order_quantity,
                "price_volatility_threshold": self.limits.price_volatility_threshold,
                "price_spike_threshold": self.limits.price_spike_threshold,
                "max_daily_loss": self.limits.max_daily_loss,
                "max_drawdown_percent": self.limits.max_drawdown_percent,
                "max_drawdown_percent_hard": self.limits.max_drawdown_percent_hard,
                "margin_warning_percent": self.limits.margin_warning_percent,
                "margin_critical_percent": self.limits.margin_critical_percent,
                "enable_position_risk": self.limits.enable_position_risk,
                "enable_trade_risk": self.limits.enable_trade_risk,
                "enable_capital_risk": self.limits.enable_capital_risk,
                "auto_stop_on_critical": self.limits.auto_stop_on_critical
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"風險配置已保存到: {config_path}")
        except Exception as e:
            logger.error(f"保存風險配置失敗: {e}")
    
    def update_capital(self, total_capital: float, margin_used: float = 0.0, margin_available: float = 0.0):
        """
        更新資金狀況
        
        Args:
            total_capital: 總資金
            margin_used: 已用保證金
            margin_available: 可用保證金
        """
        self.current_capital = total_capital
        self.margin_used = margin_used
        self.margin_available = margin_available
        
        # 更新峰值資金
        if total_capital > self.peak_capital:
            self.peak_capital = total_capital
    
    def update_positions(self, positions: List[Position]):
        """
        更新持倉信息
        
        Args:
            positions: 持倉列表
        """
        self.positions = {p.symbol: p for p in positions}
        
        # 檢查倉位風險
        if self.limits.enable_position_risk:
            self._check_position_risks()
    
    def _check_position_risks(self) -> List[RiskEvent]:
        """檢查倉位風險"""
        events = []
        
        if not self.positions or self.current_capital <= 0:
            return events
        
        total_position_value = sum(p.market_value for p in self.positions.values())
        
        # 檢查總倉位上限
        if total_position_value > self.limits.max_total_position_value:
            event = RiskEvent(
                event_type=RiskEventType.TOTAL_POSITION_LIMIT_EXCEEDED,
                level=RiskLevel.HIGH,
                message=f"總倉位價值 {total_position_value:,.2f} 超過限制 {self.limits.max_total_position_value:,.2f}",
                timestamp=datetime.now(),
                details={
                    "current_value": total_position_value,
                    "limit": self.limits.max_total_position_value
                }
            )
            events.append(event)
            self._record_event(event)
        
        # 檢查總倉位佔比
        total_position_percent = (total_position_value / self.current_capital) * 100
        if total_position_percent > self.limits.max_total_position_percent:
            event = RiskEvent(
                event_type=RiskEventType.TOTAL_POSITION_LIMIT_EXCEEDED,
                level=RiskLevel.HIGH,
                message=f"總倉位佔比 {total_position_percent:.2f}% 超過限制 {self.limits.max_total_position_percent}%",
                timestamp=datetime.now(),
                details={
                    "current_percent": total_position_percent,
                    "limit": self.limits.max_total_position_percent
                }
            )
            events.append(event)
            self._record_event(event)
        
        # 檢查單一股票倉位
        sector_values: Dict[str, float] = {}
        for symbol, position in self.positions.items():
            position_percent = (position.market_value / self.current_capital) * 100
            
            # 單一股票價值限制
            if position.market_value > self.limits.max_single_position_value:
                event = RiskEvent(
                    event_type=RiskEventType.POSITION_LIMIT_EXCEEDED,
                    level=RiskLevel.HIGH,
                    message=f"{symbol} 倉位價值 {position.market_value:,.2f} 超過限制",
                    timestamp=datetime.now(),
                    symbol=symbol,
                    details={
                        "market_value": position.market_value,
                        "limit": self.limits.max_single_position_value
                    }
                )
                events.append(event)
                self._record_event(event)
            
            # 單一股票佔比限制
            if position_percent > self.limits.max_single_position_percent:
                event = RiskEvent(
                    event_type=RiskEventType.POSITION_LIMIT_EXCEEDED,
                    level=RiskLevel.MEDIUM,
                    message=f"{symbol} 倉位佔比 {position_percent:.2f}% 超過限制",
                    timestamp=datetime.now(),
                    symbol=symbol,
                    details={
                        "percent": position_percent,
                        "limit": self.limits.max_single_position_percent
                    }
                )
                events.append(event)
                self._record_event(event)
            
            # 統計行業持倉
            if position.sector:
                sector_values[position.sector] = sector_values.get(position.sector, 0) + position.market_value
        
        # 檢查行業集中度
        for sector, value in sector_values.items():
            sector_percent = (value / total_position_value) * 100 if total_position_value > 0 else 0
            if sector_percent > self.limits.max_sector_concentration_percent:
                event = RiskEvent(
                    event_type=RiskEventType.SECTOR_CONCENTRATION_EXCEEDED,
                    level=RiskLevel.MEDIUM,
                    message=f"{sector} 行業集中度 {sector_percent:.2f}% 超過限制",
                    timestamp=datetime.now(),
                    details={
                        "sector": sector,
                        "percent": sector_percent,
                        "limit": self.limits.max_sector_concentration_percent
                    }
                )
                events.append(event)
                self._record_event(event)
        
        return events
    
    def check_trade_risk(self, symbol: str, quantity: int, price: float, side: str) -> Tuple[bool, Optional[RiskEvent]]:
        """
        檢查交易風險
        
        Args:
            symbol: 股票代碼
            quantity: 交易數量
            price: 交易價格
            side: 交易方向 (BUY/SELL)
            
        Returns:
            (是否通過, 風險事件)
        """
        if not self.limits.enable_trade_risk:
            return True, None
        
        order_value = quantity * price
        
        # 檢查交易是否被禁用
        if not self._trading_enabled:
            event = RiskEvent(
                event_type=RiskEventType.DAILY_TRADE_LIMIT_EXCEEDED,
                level=RiskLevel.CRITICAL,
                message="交易已被風控系統禁用",
                timestamp=datetime.now(),
                symbol=symbol,
                details={"reason": "trading_disabled"}
            )
            return False, event
        
        # 檢查每日交易次數
        if self.daily_stats["trade_count"] >= self.limits.max_daily_trades:
            event = RiskEvent(
                event_type=RiskEventType.DAILY_TRADE_LIMIT_EXCEEDED,
                level=RiskLevel.HIGH,
                message=f"每日交易次數 {self.daily_stats['trade_count']} 已達上限",
                timestamp=datetime.now(),
                symbol=symbol,
                details={"count": self.daily_stats["trade_count"], "limit": self.limits.max_daily_trades}
            )
            self._record_event(event)
            return False, event
        
        # 檢查單筆金額限制
        if order_value > self.limits.max_order_value:
            event = RiskEvent(
                event_type=RiskEventType.ORDER_SIZE_EXCEEDED,
                level=RiskLevel.HIGH,
                message=f"訂單金額 {order_value:,.2f} 超過限制",
                timestamp=datetime.now(),
                symbol=symbol,
                details={"order_value": order_value, "limit": self.limits.max_order_value}
            )
            self._record_event(event)
            return False, event
        
        # 檢查單筆數量限制
        if quantity > self.limits.max_order_quantity:
            event = RiskEvent(
                event_type=RiskEventType.ORDER_SIZE_EXCEEDED,
                level=RiskLevel.HIGH,
                message=f"訂單數量 {quantity} 超過限制",
                timestamp=datetime.now(),
                symbol=symbol,
                details={"quantity": quantity, "limit": self.limits.max_order_quantity}
            )
            self._record_event(event)
            return False, event
        
        # 檢查價格異常
        price_event = self._check_price_anomaly(symbol, price)
        if price_event and price_event.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return False, price_event
        
        return True, None
    
    def _check_price_anomaly(self, symbol: str, current_price: float) -> Optional[RiskEvent]:
        """檢查價格異常"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        history = self.price_history[symbol]
        
        # 添加當前價格到歷史
        history.append({
            "price": current_price,
            "timestamp": datetime.now()
        })
        
        # 只保留最近100個價格點
        if len(history) > 100:
            history = history[-100:]
        self.price_history[symbol] = history
        
        if len(history) < 5:
            return None
        
        # 計算價格變化率
        recent_prices = [h["price"] for h in history[-10:]]
        avg_price = sum(recent_prices) / len(recent_prices)
        price_change_percent = abs(current_price - avg_price) / avg_price * 100
        
        # 檢查價格暴漲暴跌
        if price_change_percent > self.limits.price_spike_threshold:
            event = RiskEvent(
                event_type=RiskEventType.PRICE_ANOMALY_DETECTED,
                level=RiskLevel.HIGH,
                message=f"{symbol} 價格異常波動 {price_change_percent:.2f}%",
                timestamp=datetime.now(),
                symbol=symbol,
                details={
                    "current_price": current_price,
                    "avg_price": avg_price,
                    "change_percent": price_change_percent
                }
            )
            self._record_event(event)
            return event
        
        # 檢查價格波動率
        if len(history) >= 20:
            volatility = self._calculate_volatility([h["price"] for h in history[-20:]])
            if volatility > self.limits.price_volatility_threshold:
                event = RiskEvent(
                    event_type=RiskEventType.PRICE_ANOMALY_DETECTED,
                    level=RiskLevel.MEDIUM,
                    message=f"{symbol} 價格波動率異常 {volatility:.2f}%",
                    timestamp=datetime.now(),
                    symbol=symbol,
                    details={"volatility": volatility}
                )
                self._record_event(event)
                return event
        
        return None
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """計算價格波動率"""
        if len(prices) < 2:
            return 0.0
        
        import math
        
        # 計算對數收益率
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                returns.append(math.log(prices[i] / prices[i-1]))
        
        if not returns:
            return 0.0
        
        # 計算標準差
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        std = math.sqrt(variance)
        
        # 年化波動率
        return std * math.sqrt(252) * 100
    
    def check_capital_risk(self, daily_pnl: float) -> List[RiskEvent]:
        """
        檢查資金風險
        
        Args:
            daily_pnl: 當日盈虧
            
        Returns:
            風險事件列表
        """
        events = []
        
        if not self.limits.enable_capital_risk:
            return events
        
        # 更新當日盈虧
        self.daily_stats["daily_pnl"] = daily_pnl
        
        # 檢查每日虧損限制
        if daily_pnl < -self.limits.max_daily_loss:
            event = RiskEvent(
                event_type=RiskEventType.DAILY_LOSS_LIMIT_EXCEEDED,
                level=RiskLevel.CRITICAL,
                message=f"當日虧損 {daily_pnl:,.2f} 超過限制 {self.limits.max_daily_loss:,.2f}",
                timestamp=datetime.now(),
                details={"daily_pnl": daily_pnl, "limit": self.limits.max_daily_loss}
            )
            events.append(event)
            self._record_event(event)
            
            # 觸發自動停止
            if self.limits.auto_stop_on_critical:
                self._trading_enabled = False
                event.action_taken = "trading_disabled"
                logger.critical("風控觸發：已自動停止交易")
        
        # 檢查回撤
        if self.peak_capital > 0 and self.current_capital > 0:
            drawdown = (self.peak_capital - self.current_capital) / self.peak_capital * 100
            
            if drawdown > self.limits.max_drawdown_percent_hard:
                event = RiskEvent(
                    event_type=RiskEventType.DRAWDOWN_LIMIT_EXCEEDED,
                    level=RiskLevel.CRITICAL,
                    message=f"當前回撤 {drawdown:.2f}% 超過硬限制 {self.limits.max_drawdown_percent_hard}%",
                    timestamp=datetime.now(),
                    details={"drawdown": drawdown, "limit": self.limits.max_drawdown_percent_hard}
                )
                events.append(event)
                self._record_event(event)
                
                if self.limits.auto_stop_on_critical:
                    self._trading_enabled = False
                    event.action_taken = "trading_disabled"
                    logger.critical("風控觸發：已自動停止交易")
            
            elif drawdown > self.limits.max_drawdown_percent:
                event = RiskEvent(
                    event_type=RiskEventType.DRAWDOWN_LIMIT_EXCEEDED,
                    level=RiskLevel.HIGH,
                    message=f"當前回撤 {drawdown:.2f}% 超過警告限制 {self.limits.max_drawdown_percent}%",
                    timestamp=datetime.now(),
                    details={"drawdown": drawdown, "limit": self.limits.max_drawdown_percent}
                )
                events.append(event)
                self._record_event(event)
        
        # 檢查保證金
        if self.margin_available + self.margin_used > 0:
            margin_ratio = self.margin_used / (self.margin_available + self.margin_used) * 100
            
            if margin_ratio > self.limits.margin_critical_percent:
                event = RiskEvent(
                    event_type=RiskEventType.MARGIN_CALL_CRITICAL,
                    level=RiskLevel.CRITICAL,
                    message=f"保證金使用率 {margin_ratio:.2f}% 達到危險水平",
                    timestamp=datetime.now(),
                    details={
                        "margin_ratio": margin_ratio,
                        "used": self.margin_used,
                        "available": self.margin_available
                    }
                )
                events.append(event)
                self._record_event(event)
            
            elif margin_ratio > self.limits.margin_warning_percent:
                event = RiskEvent(
                    event_type=RiskEventType.MARGIN_CALL_WARNING,
                    level=RiskLevel.MEDIUM,
                    message=f"保證金使用率 {margin_ratio:.2f}% 達到警告水平",
                    timestamp=datetime.now(),
                    details={
                        "margin_ratio": margin_ratio,
                        "used": self.margin_used,
                        "available": self.margin_available
                    }
                )
                events.append(event)
                self._record_event(event)
        
        return events
    
    def record_trade(self, symbol: str, quantity: int, price: float, side: str):
        """
        記錄交易
        
        Args:
            symbol: 股票代碼
            quantity: 交易數量
            price: 交易價格
            side: 交易方向
        """
        # 重置每日統計（如果是新的一天）
        today = date.today()
        if self.daily_stats["date"] != today:
            self.daily_stats = {
                "date": today,
                "trade_count": 0,
                "daily_pnl": 0.0,
                "orders": []
            }
        
        self.daily_stats["trade_count"] += 1
        self.daily_stats["orders"].append({
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "side": side,
            "timestamp": datetime.now().isoformat()
        })
    
    def _record_event(self, event: RiskEvent):
        """記錄風險事件"""
        self.risk_events.append(event)
        
        # 根據風險等級記錄日誌
        if event.level == RiskLevel.CRITICAL:
            logger.critical(f"[風控] {event.message}")
        elif event.level == RiskLevel.HIGH:
            logger.error(f"[風控] {event.message}")
        elif event.level == RiskLevel.MEDIUM:
            logger.warning(f"[風控] {event.message}")
        else:
            logger.info(f"[風控] {event.message}")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """獲取風險摘要"""
        total_position_value = sum(p.market_value for p in self.positions.values())
        
        # 計算回撤
        drawdown = 0.0
        if self.peak_capital > 0:
            drawdown = (self.peak_capital - self.current_capital) / self.peak_capital * 100
        
        # 計算保證金使用率
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
            "recent_events": [
                {
                    "type": e.event_type.value,
                    "level": e.level.value,
                    "message": e.message,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in self.risk_events[-10:]  # 最近10個事件
            ]
        }
    
    def enable_trading(self):
        """啟用交易"""
        self._trading_enabled = True
        logger.info("交易已啟用")
    
    def disable_trading(self):
        """禁用交易"""
        self._trading_enabled = False
        logger.warning("交易已禁用")
    
    def is_trading_enabled(self) -> bool:
        """檢查交易是否啟用"""
        return self._trading_enabled
    
    def clear_events(self):
        """清除風險事件記錄"""
        self.risk_events.clear()
        logger.info("風險事件記錄已清除")
    
    def get_events_by_level(self, level: RiskLevel) -> List[RiskEvent]:
        """獲取指定等級的風險事件"""
        return [e for e in self.risk_events if e.level == level]
    
    def reset_daily_stats(self):
        """重置每日統計"""
        self.daily_stats = {
            "date": date.today(),
            "trade_count": 0,
            "daily_pnl": 0.0,
            "orders": []
        }
        logger.info("每日統計已重置")
