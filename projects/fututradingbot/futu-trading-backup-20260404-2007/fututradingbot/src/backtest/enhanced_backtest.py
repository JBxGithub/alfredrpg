"""
增強回測系統 - Enhanced Backtesting System
支持多因子策略回測、K線形態整合、市場情緒數據、波動率適應性回測
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import warnings

from src.strategies.base import BaseStrategy, TradeSignal, SignalType
from src.strategies.enhanced_strategy import EnhancedStrategy, MultiFactorScore, SignalFactor
from src.indicators.candlestick_patterns import CandlestickAnalyzer
from src.analysis.market_sentiment import MarketSentimentAnalyzer, MarketSentimentAnalysis
from src.utils.logger import logger

warnings.filterwarnings('ignore')


@dataclass
class FactorPerformance:
    """因子績效分析"""
    factor: SignalFactor
    win_rate: float
    avg_return: float
    sharpe_ratio: float
    trades_count: int
    contribution_score: float


@dataclass
class EnhancedBacktestResult:
    """增強回測結果"""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    volatility: float
    var_95: float
    cvar_95: float
    avg_trade_duration: timedelta = field(default_factory=lambda: timedelta(0))
    max_trade_duration: timedelta = field(default_factory=lambda: timedelta(0))
    min_trade_duration: timedelta = field(default_factory=lambda: timedelta(0))
    factor_performances: List[FactorPerformance] = field(default_factory=list)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    trades: List[Any] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'start_date': str(self.start_date),
            'end_date': str(self.end_date),
            'initial_capital': float(self.initial_capital),
            'final_capital': float(self.final_capital),
            'total_return_pct': float(self.total_return_pct),
            'total_trades': int(self.total_trades),
            'win_rate': float(self.win_rate),
            'sharpe_ratio': float(self.sharpe_ratio),
            'max_drawdown_pct': float(self.max_drawdown_pct),
        }
    
    def print_summary(self):
        print("\n" + "="*70)
        print("增強回測結果摘要")
        print("="*70)
        print(f"回測期間: {self.start_date} ~ {self.end_date}")
        print(f"總收益率: {self.total_return_pct:.2f}%")
        print(f"總交易次數: {self.total_trades} | 勝率: {self.win_rate:.2f}%")
        print(f"夏普比率: {self.sharpe_ratio:.2f} | 最大回撤: {self.max_drawdown_pct:.2f}%")
        print("="*70)


@dataclass
class TradeRecord:
    """交易記錄"""
    entry_time: datetime
    exit_time: Optional[datetime]
    code: str
    entry_price: float
    exit_price: Optional[float]
    qty: int
    is_long: bool
    pnl: float
    pnl_pct: float
    exit_reason: str


class EnhancedBacktestEngine:
    """增強回測引擎"""
    
    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = 1000000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.001
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.candlestick_analyzer = CandlestickAnalyzer()
        self.sentiment_analyzer = MarketSentimentAnalyzer()
        self.cash: float = initial_capital
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.trades: List[TradeRecord] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.order_counter: int = 0
        self.factor_history: List[Dict[str, Any]] = []
        
    def run(
        self,
        data: Dict[str, pd.DataFrame],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> EnhancedBacktestResult:
        """執行增強回測"""
        prepared_data = self._prepare_data(data, start_date, end_date)
        if not prepared_data:
            return self._generate_empty_result()
        
        all_dates = self._get_trading_dates(prepared_data)
        
        for date in all_dates:
            self._process_day(date, prepared_data)
        
        if all_dates:
            self._close_all_positions(all_dates[-1])
        
        return self._generate_result(all_dates)
    
    def _prepare_data(self, data, start_date, end_date):
        prepared = {}
        for code, df in data.items():
            if df.empty:
                continue
            df = df.copy()
            if 'timestamp' in df.columns:
                df = df.set_index('timestamp')
            df.index = pd.to_datetime(df.index)
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
            if not df.empty:
                prepared[code] = df.sort_index()
        return prepared
    
    def _get_trading_dates(self, data):
        all_dates = set()
        for df in data.values():
            all_dates.update(df.index.tolist())
        return sorted(list(all_dates))
    
    def _process_day(self, date, data):
        for code, position in self.positions.items():
            if code in data and date in data[code].index:
                position['current_price'] = data[code].loc[date, 'close']
        
        for code, df in data.items():
            if date not in df.index:
                continue
            current_data = df.loc[:date].copy()
            if len(current_data) < 30:
                continue
            
            sentiment = self.sentiment_analyzer.analyze(current_data)
            strategy_input = {'code': code, 'df': current_data, 'sentiment': sentiment}
            signal = self.strategy.on_data(strategy_input)
            
            if signal:
                if isinstance(self.strategy, EnhancedStrategy):
                    factor_score = self.strategy._analyze_factors(code, current_data)
                    self.factor_history.append({'date': date, 'code': code, 'factor_score': factor_score})
                self._execute_signal(signal, date)
        
        self._record_equity(date)
    
    def _execute_signal(self, signal, timestamp):
        if signal.signal == SignalType.BUY:
            executed_price = signal.price * (1 + self.slippage)
        else:
            executed_price = signal.price * (1 - self.slippage)
        
        trade_value = executed_price * signal.qty
        commission = trade_value * self.commission_rate
        
        if signal.signal == SignalType.BUY:
            self._execute_buy(signal, executed_price, commission, timestamp)
        elif signal.signal == SignalType.SELL:
            self._execute_sell(signal, executed_price, commission, timestamp)
    
    def _execute_buy(self, signal, executed_price, commission, timestamp):
        total_cost = executed_price * signal.qty + commission
        if total_cost > self.cash:
            return
        self.cash -= total_cost
        
        if signal.code in self.positions:
            position = self.positions[signal.code]
            total_cost_basis = position['entry_price'] * position['qty'] + executed_price * signal.qty
            total_qty = position['qty'] + signal.qty
            position['entry_price'] = total_cost_basis / total_qty
            position['qty'] = total_qty
        else:
            self.positions[signal.code] = {
                'entry_price': executed_price, 'qty': signal.qty, 'is_long': True,
                'entry_time': timestamp, 'current_price': executed_price
            }
            trade = TradeRecord(
                entry_time=timestamp, exit_time=None, code=signal.code,
                entry_price=executed_price, exit_price=None, qty=signal.qty,
                is_long=True, pnl=0, pnl_pct=0, exit_reason=''
            )
            self.trades.append(trade)
    
    def _execute_sell(self, signal, executed_price, commission, timestamp):
        position = None
        trade_record = None
        for trade in reversed(self.trades):
            if trade.code == signal.code and trade.exit_time is None:
                trade_record = trade
                if signal.code in self.positions:
                    position = self.positions[signal.code]
                break
        
        if not position:
            return
        
        qty = min(signal.qty, position['qty'])
        proceeds = executed_price * qty - commission
        cost_basis = position['entry_price'] * qty
        pnl = proceeds - cost_basis
        pnl_pct = pnl / cost_basis if cost_basis > 0 else 0
        self.cash += proceeds
        
        if trade_record:
            trade_record.exit_time = timestamp
            trade_record.exit_price = executed_price
            trade_record.pnl = pnl
            trade_record.pnl_pct = pnl_pct
            trade_record.exit_reason = signal.reason
        
        position['qty'] -= qty
        if position['qty'] <= 0:
            del self.positions[signal.code]
    
    def _close_all_positions(self, timestamp):
        for code in list(self.positions.keys()):
            position = self.positions[code]
            signal = TradeSignal(
                code=code, signal=SignalType.SELL, price=position['current_price'],
                qty=position['qty'], reason="回測結束平倉"
            )
            commission = position['current_price'] * position['qty'] * self.commission_rate
            self._execute_sell(signal, position['current_price'], commission, timestamp)
    
    def _record_equity(self, timestamp):
        position_value = sum(pos['current_price'] * pos['qty'] for pos in self.positions.values())
        total_equity = self.cash + position_value
        self.equity_curve.append({'timestamp': timestamp, 'cash': self.cash, 
                                  'position_value': position_value, 'total_equity': total_equity})
    
    def _generate_result(self, dates):
        if not self.equity_curve:
            return self._generate_empty_result()
        
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('timestamp', inplace=True)
        
        initial_capital = self.initial_capital
        final_capital = equity_df['total_equity'].iloc[-1]
        total_return_pct = ((final_capital - initial_capital) / initial_capital) * 100
        
        closed_trades = [t for t in self.trades if t.exit_time is not None]
        total_trades = len(closed_trades)
        winning_trades = len([t for t in closed_trades if t.pnl > 0])
        losing_trades = len([t for t in closed_trades if t.pnl <= 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        profits = [t.pnl for t in closed_trades if t.pnl > 0]
        losses = [t.pnl for t in closed_trades if t.pnl <= 0]
        avg_profit = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 0
        total_profit = sum(profits)
        total_loss = abs(sum(losses))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        equity_df['peak'] = equity_df['total_equity'].cummax()
        equity_df['drawdown'] = equity_df['total_equity'] - equity_df['peak']
        equity_df['drawdown_pct'] = (equity_df['drawdown'] / equity_df['peak']) * 100
        max_drawdown = equity_df['drawdown'].min()
        max_drawdown_pct = equity_df['drawdown_pct'].min()
        
        equity_df['returns'] = equity_df['total_equity'].pct_change().dropna()
        risk_free_rate = 0.02
        excess_returns = equity_df['returns'] - risk_free_rate / 252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / equity_df['returns'].std() if equity_df['returns'].std() > 0 else 0
        downside_returns = equity_df['returns'][equity_df['returns'] < 0]
        sortino_ratio = np.sqrt(252) * excess_returns.mean() / downside_returns.std() if len(downside_returns) > 0 and downside_returns.std() > 0 else 0
        calmar_ratio = (total_return_pct / 100) / abs(max_drawdown_pct) if max_drawdown_pct != 0 else 0
        volatility = equity_df['returns'].std() * np.sqrt(252) * 100
        var_95 = np.percentile(equity_df['returns'].dropna() * 100, 5)
        cvar_95 = equity_df['returns'][equity_df['returns'] <= var_95/100].mean() * 100
        
        factor_performances = self._analyze_factor_performance()
        
        return EnhancedBacktestResult(
            start_date=dates[0] if dates else datetime.now(),
            end_date=dates[-1] if dates else datetime.now(),
            initial_capital=initial_capital, final_capital=final_capital,
            total_return=final_capital - initial_capital, total_return_pct=total_return_pct,
            total_trades=total_trades, winning_trades=winning_trades, losing_trades=losing_trades,
            win_rate=win_rate, avg_profit=avg_profit, avg_loss=avg_loss, profit_factor=profit_factor,
            max_drawdown=max_drawdown, max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio, sortino_ratio=sortino_ratio, calmar_ratio=calmar_ratio,
            volatility=volatility, var_95=var_95, cvar_95=cvar_95,
            factor_performances=factor_performances, equity_curve=equity_df, trades=closed_trades
        )
    
    def _analyze_factor_performance(self):
        return []
    
    def _generate_empty_result(self):
        return EnhancedBacktestResult(
            start_date=datetime.now(), end_date=datetime.now(),
            initial_capital=self.initial_capital, final_capital=self.initial_capital,
            total_return=0, total_return_pct=0, total_trades=0, winning_trades=0, losing_trades=0,
            win_rate=0, avg_profit=0, avg_loss=0, profit_factor=0, max_drawdown=0, max_drawdown_pct=0,
            sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0, volatility=0, var_95=0, cvar_95=0
        )
