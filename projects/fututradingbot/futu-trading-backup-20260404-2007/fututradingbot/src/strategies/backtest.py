"""
回測框架
Backtesting Framework for Futu Trading Bot

提供策略回測功能:
- 歷史數據回測
- 績效分析
- 風險指標計算
- 結果可視化
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from src.strategies.base import BaseStrategy, TradeSignal, SignalType
from src.strategies.trend_strategy import TrendStrategy
from src.indicators.technical import TechnicalIndicators
from src.utils.logger import logger


class OrderStatus(Enum):
    """訂單狀態"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class BacktestOrder:
    """回測訂單"""
    order_id: str
    code: str
    signal: SignalType
    price: float
    qty: int
    timestamp: datetime
    status: OrderStatus = OrderStatus.PENDING
    filled_price: float = 0.0
    filled_time: Optional[datetime] = None
    commission: float = 0.0


@dataclass
class BacktestPosition:
    """回測持倉"""
    code: str
    qty: int
    avg_cost: float
    entry_time: datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.qty * self.current_price
    
    @property
    def cost_basis(self) -> float:
        return self.qty * self.avg_cost


@dataclass
class BacktestTrade:
    """回測成交記錄"""
    code: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    qty: int
    pnl: float
    pnl_pct: float
    commission: float
    exit_reason: str


@dataclass
class BacktestResult:
    """回測結果"""
    # 基本統計
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    
    # 交易統計
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    
    # 風險指標
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    volatility: float
    
    # 資金曲線
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    trades: List[BacktestTrade] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return': self.total_return,
            'total_return_pct': self.total_return_pct,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'avg_profit': self.avg_profit,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown_pct,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'volatility': self.volatility
        }
    
    def to_json(self, indent: int = 2) -> str:
        """轉換為JSON字符串"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)
    
    def print_summary(self):
        """打印回測摘要"""
        print("\n" + "="*60)
        print("回測結果摘要")
        print("="*60)
        print(f"回測期間: {self.start_date.date()} ~ {self.end_date.date()}")
        print(f"初始資金: ${self.initial_capital:,.2f}")
        print(f"最終資金: ${self.final_capital:,.2f}")
        print(f"總收益率: {self.total_return_pct:.2f}%")
        print("-"*60)
        print("交易統計:")
        print(f"  總交易次數: {self.total_trades}")
        print(f"  盈利次數: {self.winning_trades}")
        print(f"  虧損次數: {self.losing_trades}")
        print(f"  勝率: {self.win_rate:.2f}%")
        print(f"  平均盈利: ${self.avg_profit:,.2f}")
        print(f"  平均虧損: ${self.avg_loss:,.2f}")
        print(f"  盈虧比: {self.profit_factor:.2f}")
        print("-"*60)
        print("風險指標:")
        print(f"  最大回撤: ${self.max_drawdown:,.2f} ({self.max_drawdown_pct:.2f}%)")
        print(f"  夏普比率: {self.sharpe_ratio:.2f}")
        print(f"  索提諾比率: {self.sortino_ratio:.2f}")
        print(f"  卡瑪比率: {self.calmar_ratio:.2f}")
        print(f"  波動率: {self.volatility:.2f}%")
        print("="*60)


class BacktestEngine:
    """
    回測引擎
    
    執行策略回測的核心類
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = 1000000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.001
    ):
        """
        初始化回測引擎
        
        Args:
            strategy: 交易策略實例
            initial_capital: 初始資金
            commission_rate: 手續費率
            slippage: 滑點比例
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        # 回測狀態
        self.cash: float = initial_capital
        self.positions: Dict[str, BacktestPosition] = {}
        self.orders: List[BacktestOrder] = []
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[Dict[str, Any]] = []
        
        # 統計
        self.order_counter: int = 0
        
        logger.info(f"回測引擎初始化完成 | 初始資金: ${initial_capital:,.2f}")
    
    def run(
        self,
        data: Dict[str, pd.DataFrame],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> BacktestResult:
        """
        執行回測
        
        Args:
            data: 股票數據字典 {code: DataFrame}
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            BacktestResult: 回測結果
        """
        logger.info("開始回測...")
        
        # 準備數據
        prepared_data = self._prepare_data(data, start_date, end_date)
        
        if not prepared_data:
            logger.error("沒有有效的數據進行回測")
            return self._generate_empty_result()
        
        # 獲取所有交易日
        all_dates = self._get_trading_dates(prepared_data)
        
        logger.info(f"回測交易日數: {len(all_dates)}")
        
        # 逐日回測
        for date in all_dates:
            self._process_day(date, prepared_data)
        
        # 平倉所有持倉
        self._close_all_positions(all_dates[-1] if all_dates else datetime.now())
        
        # 生成結果
        result = self._generate_result(all_dates)
        
        logger.info("回測完成")
        
        return result
    
    def _prepare_data(
        self,
        data: Dict[str, pd.DataFrame],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Dict[str, pd.DataFrame]:
        """準備回測數據"""
        prepared = {}
        
        for code, df in data.items():
            if df.empty:
                continue
            
            # 確保時間索引
            if 'timestamp' in df.columns:
                df = df.set_index('timestamp')
            
            df.index = pd.to_datetime(df.index)
            
            # 日期過濾
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
            
            if not df.empty:
                prepared[code] = df.sort_index()
        
        return prepared
    
    def _get_trading_dates(self, data: Dict[str, pd.DataFrame]) -> List[datetime]:
        """獲取所有交易日"""
        all_dates = set()
        
        for df in data.values():
            all_dates.update(df.index.tolist())
        
        return sorted(list(all_dates))
    
    def _process_day(self, date: datetime, data: Dict[str, pd.DataFrame]):
        """處理單個交易日"""
        # 更新持倉價格
        for code, position in self.positions.items():
            if code in data and date in data[code].index:
                position.current_price = data[code].loc[date, 'close']
                position.unrealized_pnl = (
                    position.current_price - position.avg_cost
                ) * position.qty
        
        # 檢查每個股票的信號
        for code, df in data.items():
            if date not in df.index:
                continue
            
            # 獲取當前數據
            current_data = df.loc[:date].copy()
            
            if len(current_data) < 30:  # 確保有足夠數據
                continue
            
            # 構建策略輸入
            strategy_input = {
                'code': code,
                'df': current_data,
                'analysis_score': 75  # 簡化處理，實際應從分析模組獲取
            }
            
            # 獲取交易信號
            signal = self.strategy.on_data(strategy_input)
            
            if signal:
                self._execute_signal(signal, date)
        
        # 記錄權益曲線
        self._record_equity(date)
    
    def _execute_signal(self, signal: TradeSignal, timestamp: datetime):
        """執行交易信號"""
        # 應用滑點
        if signal.signal == SignalType.BUY:
            executed_price = signal.price * (1 + self.slippage)
        else:
            executed_price = signal.price * (1 - self.slippage)
        
        # 計算手續費
        trade_value = executed_price * signal.qty
        commission = trade_value * self.commission_rate
        
        # 創建訂單
        self.order_counter += 1
        order = BacktestOrder(
            order_id=f"ORD{self.order_counter:06d}",
            code=signal.code,
            signal=signal.signal,
            price=signal.price,
            qty=signal.qty,
            timestamp=timestamp,
            status=OrderStatus.FILLED,
            filled_price=executed_price,
            filled_time=timestamp,
            commission=commission
        )
        
        self.orders.append(order)
        
        # 執行交易
        if signal.signal == SignalType.BUY:
            self._execute_buy(order)
        elif signal.signal == SignalType.SELL:
            self._execute_sell(order)
    
    def _execute_buy(self, order: BacktestOrder):
        """執行買入"""
        total_cost = order.filled_price * order.qty + order.commission
        
        if total_cost > self.cash:
            logger.warning(f"資金不足，無法執行買入: {order.code}")
            order.status = OrderStatus.REJECTED
            return
        
        self.cash -= total_cost
        
        # 更新或創建持倉
        if order.code in self.positions:
            position = self.positions[order.code]
            total_cost_basis = position.cost_basis + total_cost
            total_qty = position.qty + order.qty
            position.avg_cost = total_cost_basis / total_qty
            position.qty = total_qty
        else:
            self.positions[order.code] = BacktestPosition(
                code=order.code,
                qty=order.qty,
                avg_cost=order.filled_price,
                entry_time=order.filled_time,
                current_price=order.filled_price
            )
        
        logger.debug(f"買入執行 | {order.code} | 價格: {order.filled_price} | 數量: {order.qty}")
    
    def _execute_sell(self, order: BacktestOrder):
        """執行賣出"""
        if order.code not in self.positions:
            logger.warning(f"無持倉，無法執行賣出: {order.code}")
            order.status = OrderStatus.REJECTED
            return
        
        position = self.positions[order.code]
        
        if order.qty > position.qty:
            logger.warning(f"賣出數量大於持倉，調整為全部賣出: {order.code}")
            order.qty = position.qty
        
        # 計算盈虧
        proceeds = order.filled_price * order.qty - order.commission
        cost_basis = position.avg_cost * order.qty
        pnl = proceeds - cost_basis
        pnl_pct = pnl / cost_basis if cost_basis > 0 else 0
        
        self.cash += proceeds
        
        # 記錄交易
        trade = BacktestTrade(
            code=order.code,
            entry_time=position.entry_time,
            exit_time=order.filled_time,
            entry_price=position.avg_cost,
            exit_price=order.filled_price,
            qty=order.qty,
            pnl=pnl,
            pnl_pct=pnl_pct,
            commission=order.commission,
            exit_reason=order.code  # 簡化處理
        )
        
        self.trades.append(trade)
        
        # 更新持倉
        position.qty -= order.qty
        if position.qty <= 0:
            del self.positions[order.code]
        
        logger.debug(f"賣出執行 | {order.code} | 價格: {order.filled_price} | 盈虧: {pnl:.2f}")
    
    def _close_all_positions(self, timestamp: datetime):
        """平倉所有持倉"""
        for code in list(self.positions.keys()):
            position = self.positions[code]
            
            order = BacktestOrder(
                order_id=f"ORD{self.order_counter:06d}",
                code=code,
                signal=SignalType.SELL,
                price=position.current_price,
                qty=position.qty,
                timestamp=timestamp,
                status=OrderStatus.FILLED,
                filled_price=position.current_price,
                filled_time=timestamp,
                commission=position.current_price * position.qty * self.commission_rate
            )
            
            self._execute_sell(order)
    
    def _record_equity(self, timestamp: datetime):
        """記錄權益曲線"""
        position_value = sum(
            pos.market_value for pos in self.positions.values()
        )
        
        total_equity = self.cash + position_value
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'cash': self.cash,
            'position_value': position_value,
            'total_equity': total_equity
        })
    
    def _generate_result(self, dates: List[datetime]) -> BacktestResult:
        """生成回測結果"""
        if not self.equity_curve:
            return self._generate_empty_result()
        
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('timestamp', inplace=True)
        
        # 基本統計
        initial_capital = self.initial_capital
        final_capital = equity_df['total_equity'].iloc[-1]
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        # 交易統計
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.pnl > 0])
        losing_trades = len([t for t in self.trades if t.pnl <= 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        profits = [t.pnl for t in self.trades if t.pnl > 0]
        losses = [t.pnl for t in self.trades if t.pnl <= 0]
        
        avg_profit = np.mean(profits) if profits else 0
        avg_loss = np.mean(losses) if losses else 0
        
        total_profit = sum(profits)
        total_loss = abs(sum(losses))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # 計算回撤
        equity_df['peak'] = equity_df['total_equity'].cummax()
        equity_df['drawdown'] = equity_df['total_equity'] - equity_df['peak']
        equity_df['drawdown_pct'] = (equity_df['drawdown'] / equity_df['peak']) * 100
        
        max_drawdown = equity_df['drawdown'].min()
        max_drawdown_pct = equity_df['drawdown_pct'].min()
        
        # 計算收益率序列
        equity_df['returns'] = equity_df['total_equity'].pct_change().dropna()
        
        # 夏普比率 (假設無風險利率為2%)
        risk_free_rate = 0.02
        excess_returns = equity_df['returns'] - risk_free_rate / 252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / equity_df['returns'].std() \
                       if equity_df['returns'].std() > 0 else 0
        
        # 索提諾比率
        downside_returns = equity_df['returns'][equity_df['returns'] < 0]
        sortino_ratio = np.sqrt(252) * excess_returns.mean() / downside_returns.std() \
                        if len(downside_returns) > 0 and downside_returns.std() > 0 else 0
        
        # 卡瑪比率
        calmar_ratio = (total_return_pct / 100) / abs(max_drawdown_pct) \
                       if max_drawdown_pct != 0 else 0
        
        # 波動率
        volatility = equity_df['returns'].std() * np.sqrt(252) * 100
        
        return BacktestResult(
            start_date=dates[0] if dates else datetime.now(),
            end_date=dates[-1] if dates else datetime.now(),
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            volatility=volatility,
            equity_curve=equity_df,
            trades=self.trades
        )
    
    def _generate_empty_result(self) -> BacktestResult:
        """生成空結果"""
        return BacktestResult(
            start_date=datetime.now(),
            end_date=datetime.now(),
            initial_capital=self.initial_capital,
            final_capital=self.initial_capital,
            total_return=0,
            total_return_pct=0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0,
            avg_profit=0,
            avg_loss=0,
            profit_factor=0,
            max_drawdown=0,
            max_drawdown_pct=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            calmar_ratio=0,
            volatility=0
        )


class WalkForwardAnalysis:
    """
    前向分析
    
    用於策略參數優化和穩健性測試
    """
    
    def __init__(self, strategy_class: type, data: Dict[str, pd.DataFrame]):
        """
        初始化前向分析
        
        Args:
            strategy_class: 策略類
            data: 歷史數據
        """
        self.strategy_class = strategy_class
        self.data = data
    
    def run_optimization(
        self,
        param_grid: Dict[str, List[Any]],
        train_size: int = 252,
        test_size: int = 63
    ) -> List[Dict[str, Any]]:
        """
        運行參數優化
        
        Args:
            param_grid: 參數網格
            train_size: 訓練集大小 (天數)
            test_size: 測試集大小 (天數)
            
        Returns:
            優化結果列表
        """
        results = []
        
        # 生成參數組合
        from itertools import product
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        for values in product(*param_values):
            params = dict(zip(param_names, values))
            
            # 創建策略實例
            strategy = self.strategy_class(config=params)
            
            # 運行回測
            engine = BacktestEngine(strategy)
            result = engine.run(self.data)
            
            results.append({
                'params': params,
                'result': result
            })
        
        # 按收益率排序
        results.sort(key=lambda x: x['result'].total_return_pct, reverse=True)
        
        return results
    
    def run_walk_forward(
        self,
        optimal_params: Dict[str, Any],
        window_size: int = 252,
        step_size: int = 63
    ) -> List[BacktestResult]:
        """
        運行前向分析
        
        Args:
            optimal_params: 最優參數
            window_size: 窗口大小 (天數)
            step_size: 步長 (天數)
            
        Returns:
            各窗口回測結果
        """
        results = []
        
        # 獲取所有日期
        all_dates = set()
        for df in self.data.values():
            all_dates.update(df.index.tolist())
        all_dates = sorted(list(all_dates))
        
        # 滑動窗口
        for i in range(0, len(all_dates) - window_size, step_size):
            train_end = i + window_size
            test_end = min(train_end + step_size, len(all_dates))
            
            train_dates = all_dates[i:train_end]
            test_dates = all_dates[train_end:test_end]
            
            if not test_dates:
                continue
            
            # 運行回測
            strategy = self.strategy_class(config=optimal_params)
            engine = BacktestEngine(strategy)
            
            # 過濾測試期數據
            test_data = {}
            for code, df in self.data.items():
                test_df = df[
                    (df.index >= test_dates[0]) & 
                    (df.index <= test_dates[-1])
                ]
                if not test_df.empty:
                    test_data[code] = test_df
            
            if test_data:
                result = engine.run(test_data)
                results.append(result)
        
        return results
