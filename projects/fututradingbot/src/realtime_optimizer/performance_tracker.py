"""
表現追踪器 - Performance Tracker

實時監控交易表現，評估策略效果
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json

from src.utils.logger import logger


@dataclass
class TradeRecord:
    """交易記錄"""
    trade_id: str
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    quantity: int = 0
    direction: str = ""  # 'long' or 'short'
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: str = ""  # 'stop_loss', 'take_profit', 'signal', 'manual'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'entry_time': self.entry_time.isoformat(),
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'direction': self.direction,
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'exit_reason': self.exit_reason
        }


@dataclass
class PerformanceMetrics:
    """表現指標"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    
    # 最近表現 (滾動窗口)
    recent_win_rate: float = 0.0  # 最近10筆
    recent_avg_pnl: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'avg_profit': self.avg_profit,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'total_pnl': self.total_pnl,
            'total_pnl_pct': self.total_pnl_pct,
            'recent_win_rate': self.recent_win_rate,
            'recent_avg_pnl': self.recent_avg_pnl
        }


class PerformanceTracker:
    """
    表現追踪器
    
    實時追踪：
    - 每筆交易結果
    - 勝率變化
    - 盈虧比
    - 最大回撤
    - 夏普比率
    """
    
    def __init__(self, window_size: int = 10):
        """
        初始化
        
        Args:
            window_size: 滾動窗口大小（用於最近表現計算）
        """
        self.window_size = window_size
        self.trades: List[TradeRecord] = []
        self.recent_trades: deque = deque(maxlen=window_size)
        self.metrics = PerformanceMetrics()
        self.equity_curve: List[float] = []
        self.start_time: Optional[datetime] = None
        
    def start(self):
        """開始追踪"""
        self.start_time = datetime.now()
        self.equity_curve = [1.0]  # 起始權益 = 1.0 (100%)
        logger.info("表現追踪器已啟動")
    
    def record_trade(self, trade: TradeRecord):
        """
        記錄交易
        
        Args:
            trade: 交易記錄
        """
        self.trades.append(trade)
        self.recent_trades.append(trade)
        
        # 更新權益曲線
        current_equity = self.equity_curve[-1] * (1 + trade.pnl_pct)
        self.equity_curve.append(current_equity)
        
        # 更新指標
        self._update_metrics()
        
        logger.info(f"交易記錄: {trade.symbol} {trade.direction} PnL={trade.pnl:.2f}")
    
    def _update_metrics(self):
        """更新表現指標"""
        if not self.trades:
            return
        
        closed_trades = [t for t in self.trades if t.exit_time is not None]
        if not closed_trades:
            return
        
        # 基本統計
        self.metrics.total_trades = len(closed_trades)
        self.metrics.winning_trades = sum(1 for t in closed_trades if t.pnl > 0)
        self.metrics.losing_trades = sum(1 for t in closed_trades if t.pnl <= 0)
        
        # 勝率
        self.metrics.win_rate = self.metrics.winning_trades / self.metrics.total_trades
        
        # 平均盈虧
        profits = [t.pnl for t in closed_trades if t.pnl > 0]
        losses = [t.pnl for t in closed_trades if t.pnl <= 0]
        
        self.metrics.avg_profit = np.mean(profits) if profits else 0
        self.metrics.avg_loss = np.mean(losses) if losses else 0
        
        # 盈虧比
        total_profit = sum(profits)
        total_loss = abs(sum(losses))
        self.metrics.profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # 總盈虧
        self.metrics.total_pnl = sum(t.pnl for t in closed_trades)
        self.metrics.total_pnl_pct = sum(t.pnl_pct for t in closed_trades)
        
        # 最大回撤
        self.metrics.max_drawdown = self._calculate_max_drawdown()
        
        # 最近表現
        if len(self.recent_trades) >= 5:
            recent_list = list(self.recent_trades)
            recent_wins = sum(1 for t in recent_list if t.pnl > 0)
            self.metrics.recent_win_rate = recent_wins / len(recent_list)
            self.metrics.recent_avg_pnl = np.mean([t.pnl for t in recent_list])
    
    def _calculate_max_drawdown(self) -> float:
        """計算最大回撤"""
        if len(self.equity_curve) < 2:
            return 0.0
        
        equity = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max
        return abs(np.min(drawdown))
    
    def get_metrics(self) -> PerformanceMetrics:
        """獲取當前表現指標"""
        return self.metrics
    
    def get_trade_summary(self) -> Dict[str, Any]:
        """獲取交易摘要"""
        return {
            'total_trades': len(self.trades),
            'closed_trades': len([t for t in self.trades if t.exit_time]),
            'open_trades': len([t for t in self.trades if not t.exit_time]),
            'metrics': self.metrics.to_dict(),
            'current_equity': self.equity_curve[-1] if self.equity_curve else 1.0,
            'running_time': str(datetime.now() - self.start_time) if self.start_time else None
        }
    
    def should_adjust_strategy(self) -> bool:
        """
        判斷是否需要調整策略
        
        Returns:
            bool: 是否需要調整
        """
        # 條件1: 最近勝率顯著下降
        if len(self.recent_trades) >= 5:
            if self.metrics.recent_win_rate < 0.3:  # 最近勝率 < 30%
                logger.warning(f"最近勝率過低: {self.metrics.recent_win_rate:.2%}")
                return True
        
        # 條件2: 連續虧損
        recent_list = list(self.recent_trades)
        consecutive_losses = 0
        for trade in reversed(recent_list):
            if trade.pnl <= 0:
                consecutive_losses += 1
            else:
                break
        
        if consecutive_losses >= 3:
            logger.warning(f"連續虧損 {consecutive_losses} 筆")
            return True
        
        # 條件3: 最大回撤超標
        if self.metrics.max_drawdown > 0.10:  # 10%
            logger.warning(f"最大回撤超標: {self.metrics.max_drawdown:.2%}")
            return True
        
        return False
    
    def get_adjustment_suggestions(self) -> Dict[str, Any]:
        """
        獲取調整建議
        
        Returns:
            調整建議字典
        """
        suggestions = {
            'reduce_position_size': False,
            'tighten_stop_loss': False,
            'widen_stop_loss': False,
            'reduce_trade_frequency': False,
            'reasons': []
        }
        
        # 建議1: 降低倉位
        if self.metrics.recent_win_rate < 0.4:
            suggestions['reduce_position_size'] = True
            suggestions['reasons'].append('最近勝率偏低，建議降低倉位')
        
        # 建議2: 收緊止損
        if self.metrics.avg_loss < -self.metrics.avg_profit * 2:
            suggestions['tighten_stop_loss'] = True
            suggestions['reasons'].append('虧損金額過大，建議收緊止損')
        
        # 建議3: 放寬止損（如果頻繁止損）
        stop_loss_exits = [t for t in self.trades if t.exit_reason == 'stop_loss']
        if len(stop_loss_exits) > len(self.trades) * 0.6:  # 60% 止損出場
            suggestions['widen_stop_loss'] = True
            suggestions['reasons'].append('頻繁止損，建議放寬止損位')
        
        # 建議4: 降低交易頻率
        if self.metrics.total_trades > 20 and self.metrics.win_rate < 0.4:
            suggestions['reduce_trade_frequency'] = True
            suggestions['reasons'].append('交易過於頻繁且勝率低')
        
        return suggestions
