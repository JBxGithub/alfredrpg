"""
TQQQ/SQQQ Pair Trading Backtest - 3 Years Historical Data
回測引擎 - 使用2023-2026年歷史數據

TQQQ (3x做多NASDAQ) 和 SQQQ (3x做空NASDAQ) 是反向相關的ETF
這個回測使用價差回歸策略，利用兩者的負相關性進行統計套利
"""

import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import logger


@dataclass
class BacktestTrade:
    """交易記錄"""
    entry_time: datetime
    exit_time: Optional[datetime]
    pair_id: str
    primary_asset: str
    hedge_asset: str
    direction: str  # 'long_tqqq' or 'long_sqqq'
    entry_price_primary: float
    entry_price_hedge: float
    exit_price_primary: Optional[float]
    exit_price_hedge: Optional[float]
    qty_primary: int
    qty_hedge: int
    pnl: float = 0.0
    pnl_pct: float = 0.0
    exit_reason: str = ""


@dataclass
class BacktestResult:
    """回測結果"""
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
    volatility: float
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    trades: List[BacktestTrade] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'start_date': str(self.start_date),
            'end_date': str(self.end_date),
            'initial_capital': float(self.initial_capital),
            'final_capital': float(self.final_capital),
            'total_return_pct': float(self.total_return_pct),
            'total_trades': int(self.total_trades),
            'winning_trades': int(self.winning_trades),
            'losing_trades': int(self.losing_trades),
            'win_rate': float(self.win_rate),
            'avg_profit': float(self.avg_profit),
            'avg_loss': float(self.avg_loss),
            'profit_factor': float(self.profit_factor),
            'max_drawdown': float(self.max_drawdown),
            'max_drawdown_pct': float(self.max_drawdown_pct),
            'sharpe_ratio': float(self.sharpe_ratio),
            'volatility': float(self.volatility),
        }


class TQQQSQQQBacktestEngine:
    """TQQQ/SQQQ配對交易回測引擎
    
    策略邏輯:
    - TQQQ (3x做多NASDAQ) 和 SQQQ (3x做空NASDAQ) 是天然負相關
    - 當兩者價格偏離其歷史關係時進行套利
    - 使用價差Z分數判斷進出場時機
    """
    
    def __init__(
        self,
        entry_zscore: float = 2.0,
        exit_zscore: float = 0.5,
        stop_loss_zscore: float = 3.5,
        position_pct: float = 0.1,
        lookback_period: int = 60,
        initial_capital: float = 1000000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.001
    ):
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
        self.stop_loss_zscore = stop_loss_zscore
        self.position_pct = position_pct
        self.lookback_period = lookback_period
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        self.cash: float = initial_capital
        self.position: Optional[Dict[str, Any]] = None  # 當前持倉
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[Dict[str, Any]] = []
        
    def load_historical_data(
        self,
        tqqq_data: pd.DataFrame,
        sqqq_data: pd.DataFrame,
        start_date: str = "2023-01-01",
        end_date: str = "2026-03-27"
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """加載並過濾歷史數據"""
        # 確保索引是datetime
        if 'timestamp' in tqqq_data.columns:
            tqqq_data = tqqq_data.set_index('timestamp')
        if 'timestamp' in sqqq_data.columns:
            sqqq_data = sqqq_data.set_index('timestamp')
            
        tqqq_data.index = pd.to_datetime(tqqq_data.index)
        sqqq_data.index = pd.to_datetime(sqqq_data.index)
        
        # 過濾日期範圍
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        tqqq_filtered = tqqq_data[(tqqq_data.index >= start_dt) & (tqqq_data.index <= end_dt)].copy()
        sqqq_filtered = sqqq_data[(sqqq_data.index >= start_dt) & (sqqq_data.index <= end_dt)].copy()
        
        # 對齊兩個數據集
        common_dates = tqqq_filtered.index.intersection(sqqq_filtered.index)
        tqqq_filtered = tqqq_filtered.loc[common_dates].sort_index()
        sqqq_filtered = sqqq_filtered.loc[common_dates].sort_index()
        
        logger.info(f"Loaded historical data: {len(common_dates)} trading days")
        logger.info(f"Period: {common_dates[0]} to {common_dates[-1]}")
        
        return tqqq_filtered, sqqq_filtered
    
    def run_backtest(
        self,
        tqqq_data: pd.DataFrame,
        sqqq_data: pd.DataFrame
    ) -> BacktestResult:
        """執行回測"""
        logger.info("=" * 60)
        logger.info("Starting TQQQ/SQQQ Pair Trading Backtest")
        logger.info("=" * 60)
        
        # 獲取交易日列表
        dates = tqqq_data.index.tolist()
        
        for i, date in enumerate(dates):
            # 確保有足夠的歷史數據
            if i < self.lookback_period:
                continue
                
            # 獲取當前數據窗口
            current_tqqq = tqqq_data.iloc[:i+1]
            current_sqqq = sqqq_data.iloc[:i+1]
            
            # 檢查是否有持倉需要平倉
            if self.position is not None:
                self._check_exit(date, current_tqqq, current_sqqq)
            else:
                # 檢查是否滿足進場條件
                self._check_entry(date, current_tqqq, current_sqqq)
            
            # 記錄權益曲線
            self._record_equity(date, tqqq_data, sqqq_data)
        
        # 回測結束，平倉所有持倉
        if self.position is not None:
            self._close_position(dates[-1], tqqq_data, sqqq_data, "回測結束平倉")
        
        return self._generate_result(dates)
    
    def _calculate_spread_zscore(
        self,
        tqqq_df: pd.DataFrame,
        sqqq_df: pd.DataFrame
    ) -> Tuple[Optional[float], float]:
        """計算價差Z分數
        
        對於TQQQ/SQQQ，我們使用價格比率而非價差
        因為它們是反向ETF，價格比率更能反映偏離程度
        """
        if len(tqqq_df) < self.lookback_period or len(sqqq_df) < self.lookback_period:
            return None, 0.0
        
        tqqq_prices = tqqq_df['close'].iloc[-self.lookback_period:].values
        sqqq_prices = sqqq_df['close'].iloc[-self.lookback_period:].values
        
        # 計算價格比率 (TQQQ/SQQQ)
        ratio = tqqq_prices / sqqq_prices
        
        # 計算Z分數
        ratio_mean = np.mean(ratio)
        ratio_std = np.std(ratio)
        
        if ratio_std == 0:
            return None, ratio_mean
        
        current_ratio = ratio[-1]
        zscore = (current_ratio - ratio_mean) / ratio_std
        
        return round(zscore, 2), ratio_mean
    
    def _check_entry(
        self,
        date: datetime,
        tqqq_df: pd.DataFrame,
        sqqq_df: pd.DataFrame
    ):
        """檢查進場條件"""
        zscore, ratio_mean = self._calculate_spread_zscore(tqqq_df, sqqq_df)
        
        if zscore is None:
            return
        
        tqqq_price = tqqq_df['close'].iloc[-1]
        sqqq_price = sqqq_df['close'].iloc[-1]
        
        # Z分數為正: TQQQ相對SQQQ高估，做多SQQQ (預期TQQQ回調或SQQQ上漲)
        if zscore > self.entry_zscore:
            self._enter_position(
                date, "SQQQ", "TQQQ",
                sqqq_price, tqqq_price,
                'long_sqqq', zscore
            )
        
        # Z分數為負: SQQQ相對TQQQ高估，做多TQQQ (預期SQQQ回調或TQQQ上漲)
        elif zscore < -self.entry_zscore:
            self._enter_position(
                date, "TQQQ", "SQQQ",
                tqqq_price, sqqq_price,
                'long_tqqq', zscore
            )
    
    def _check_exit(
        self,
        date: datetime,
        tqqq_df: pd.DataFrame,
        sqqq_df: pd.DataFrame
    ):
        """檢查出場條件"""
        if self.position is None:
            return
        
        zscore, _ = self._calculate_spread_zscore(tqqq_df, sqqq_df)
        
        if zscore is None:
            return
        
        exit_reason = None
        
        # Z分數回歸出場
        if abs(zscore) <= self.exit_zscore:
            exit_reason = f"價差回歸 | Z分數: {zscore:.2f}"
        
        # 止損出場
        elif abs(zscore) >= self.stop_loss_zscore:
            exit_reason = f"Z分數止損 | Z分數: {zscore:.2f}"
        
        if exit_reason:
            self._close_position(date, tqqq_df, sqqq_df, exit_reason)
    
    def _enter_position(
        self,
        date: datetime,
        primary_asset: str,
        hedge_asset: str,
        primary_price: float,
        hedge_price: float,
        direction: str,
        zscore: float
    ):
        """建立倉位"""
        # 計算倉位大小 (使用10%資金)
        position_value = self.initial_capital * self.position_pct
        
        # 考慮滑點
        primary_entry = primary_price * (1 + self.slippage)
        
        qty_primary = max(int(position_value / primary_entry), 1)
        
        # 計算交易成本
        primary_cost = primary_entry * qty_primary
        commission = primary_cost * self.commission_rate
        total_cost = primary_cost + commission
        
        if total_cost > self.cash:
            logger.warning(f"Insufficient cash for entry at {date}")
            return
        
        self.cash -= total_cost
        
        self.position = {
            'primary_asset': primary_asset,
            'hedge_asset': hedge_asset,
            'entry_price_primary': primary_entry,
            'entry_price_hedge': hedge_price,
            'qty_primary': qty_primary,
            'direction': direction,
            'entry_time': date,
            'entry_zscore': zscore
        }
        
        logger.info(f"[ENTRY] {date} | {direction} | Asset: {primary_asset} @ {primary_entry:.2f} | "
                   f"Qty: {qty_primary} | Z: {zscore:.2f}")
    
    def _close_position(
        self,
        date: datetime,
        tqqq_df: pd.DataFrame,
        sqqq_df: pd.DataFrame,
        exit_reason: str
    ):
        """平倉"""
        if self.position is None:
            return
        
        position = self.position
        
        # 獲取出場價格
        if position['primary_asset'] == "TQQQ":
            primary_exit = tqqq_df.loc[date, 'close'] * (1 - self.slippage)
        else:
            primary_exit = sqqq_df.loc[date, 'close'] * (1 - self.slippage)
        
        # 計算盈虧
        cost_basis = position['entry_price_primary'] * position['qty_primary']
        proceeds = primary_exit * position['qty_primary']
        commission = proceeds * self.commission_rate
        
        pnl = proceeds - cost_basis - commission
        pnl_pct = (pnl / cost_basis) * 100 if cost_basis > 0 else 0
        
        # 更新現金
        self.cash += proceeds - commission
        
        # 記錄交易
        trade = BacktestTrade(
            entry_time=position['entry_time'],
            exit_time=date,
            pair_id="TQQQ_SQQQ",
            primary_asset=position['primary_asset'],
            hedge_asset=position['hedge_asset'],
            direction=position['direction'],
            entry_price_primary=position['entry_price_primary'],
            entry_price_hedge=position['entry_price_hedge'],
            exit_price_primary=primary_exit,
            exit_price_hedge=None,
            qty_primary=position['qty_primary'],
            qty_hedge=0,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason=exit_reason
        )
        self.trades.append(trade)
        
        logger.info(f"[EXIT] {date} | {position['direction']} | PnL: ${pnl:,.2f} ({pnl_pct:.2f}%) | {exit_reason}")
        
        self.position = None
    
    def _record_equity(
        self,
        date: datetime,
        tqqq_data: pd.DataFrame,
        sqqq_data: pd.DataFrame
    ):
        """記錄權益曲線"""
        position_value = 0.0
        
        if self.position is not None:
            if self.position['primary_asset'] == "TQQQ":
                current_price = tqqq_data.loc[date, 'close']
            else:
                current_price = sqqq_data.loc[date, 'close']
            
            position_value = current_price * self.position['qty_primary']
        
        total_equity = self.cash + position_value
        
        self.equity_curve.append({
            'timestamp': date,
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
        
        initial_capital = self.initial_capital
        final_capital = equity_df['total_equity'].iloc[-1]
        total_return_pct = ((final_capital - initial_capital) / initial_capital) * 100
        
        # 交易統計
        closed_trades = self.trades
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
        
        # 計算回撤
        equity_df['peak'] = equity_df['total_equity'].cummax()
        equity_df['drawdown'] = equity_df['total_equity'] - equity_df['peak']
        equity_df['drawdown_pct'] = (equity_df['drawdown'] / equity_df['peak']) * 100
        max_drawdown = equity_df['drawdown'].min()
        max_drawdown_pct = equity_df['drawdown_pct'].min()
        
        # 計算夏普比率
        equity_df['returns'] = equity_df['total_equity'].pct_change().dropna()
        risk_free_rate = 0.02  # 假設無風險利率2%
        excess_returns = equity_df['returns'] - risk_free_rate / 252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / equity_df['returns'].std() if equity_df['returns'].std() > 0 else 0
        
        # 計算波動率
        volatility = equity_df['returns'].std() * np.sqrt(252) * 100
        
        return BacktestResult(
            start_date=dates[0] if dates else datetime.now(),
            end_date=dates[-1] if dates else datetime.now(),
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return=final_capital - initial_capital,
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
            volatility=volatility,
            equity_curve=equity_df,
            trades=closed_trades
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
            volatility=0
        )


def generate_realistic_mock_data(days: int = 800) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """生成更真實的模擬歷史數據 (2023-2026)
    
    特點:
    - TQQQ和SQQQ呈現負相關
    - 包含趨勢、波動聚集和均值回歸
    - 模擬真實市場的波動率變化
    """
    np.random.seed(42)
    
    # 基礎價格 (接近真實水平)
    base_tqqq = 38.0
    base_sqqq = 28.0
    
    # 生成日期序列 (3年交易日)
    end_date = datetime(2026, 3, 27)
    dates = pd.date_range(end=end_date, periods=days, freq='B')  # 工作日
    
    # 生成市場基礎走勢 (模擬 NASDAQ)
    # 使用GARCH-like的波動聚集
    market_returns = np.zeros(days)
    volatility = np.zeros(days)
    volatility[0] = 0.012
    
    for i in range(1, days):
        # GARCH(1,1)風格的波動率
        volatility[i] = np.sqrt(0.000001 + 0.1 * market_returns[i-1]**2 + 0.85 * volatility[i-1]**2)
        market_returns[i] = np.random.normal(0.0003, volatility[i])
    
    # 添加一些趨勢和事件
    # 2023年: 上升趨勢
    market_returns[:100] += 0.0005
    # 2024年中: 回調
    market_returns[300:350] -= 0.001
    # 2025年: 震盪
    market_returns[450:550] *= 1.5
    
    # TQQQ: 3x 槓桿做多 (每日再平衡效應)
    tqqq_returns = market_returns * 3 + np.random.normal(0, 0.003, days)
    # 槓桿衰減效應
    for i in range(1, days):
        tqqq_returns[i] -= 0.0001 * abs(market_returns[i])  # 小幅衰減
    tqqq_prices = base_tqqq * np.exp(np.cumsum(tqqq_returns))
    
    # SQQQ: 3x 槓桿做空
    sqqq_returns = -market_returns * 3 + np.random.normal(0, 0.003, days)
    # 槓桿衰減效應
    for i in range(1, days):
        sqqq_returns[i] -= 0.0001 * abs(market_returns[i])  # 小幅衰減
    sqqq_prices = base_sqqq * np.exp(np.cumsum(sqqq_returns))
    
    # 生成OHLC數據
    tqqq_data = []
    sqqq_data = []
    
    for i, date in enumerate(dates):
        # TQQQ
        close_tqqq = tqqq_prices[i]
        daily_vol = abs(np.random.normal(0, 0.015))
        high_tqqq = close_tqqq * (1 + daily_vol)
        low_tqqq = close_tqqq * (1 - daily_vol)
        open_tqqq = tqqq_prices[i-1] if i > 0 else close_tqqq * (1 + np.random.normal(0, 0.005))
        
        tqqq_data.append({
            'timestamp': date,
            'open': max(open_tqqq, low_tqqq),
            'high': max(high_tqqq, open_tqqq, close_tqqq),
            'low': min(low_tqqq, open_tqqq, close_tqqq),
            'close': close_tqqq,
            'volume': int(np.random.uniform(50000000, 150000000))
        })
        
        # SQQQ
        close_sqqq = sqqq_prices[i]
        daily_vol = abs(np.random.normal(0, 0.015))
        high_sqqq = close_sqqq * (1 + daily_vol)
        low_sqqq = close_sqqq * (1 - daily_vol)
        open_sqqq = sqqq_prices[i-1] if i > 0 else close_sqqq * (1 + np.random.normal(0, 0.005))
        
        sqqq_data.append({
            'timestamp': date,
            'open': max(open_sqqq, low_sqqq),
            'high': max(high_sqqq, open_sqqq, close_sqqq),
            'low': min(low_sqqq, open_sqqq, close_sqqq),
            'close': close_sqqq,
            'volume': int(np.random.uniform(30000000, 80000000))
        })
    
    df_tqqq = pd.DataFrame(tqqq_data).set_index('timestamp')
    df_sqqq = pd.DataFrame(sqqq_data).set_index('timestamp')
    
    return df_tqqq, df_sqqq


def run_backtest_report():
    """執行回測並生成報告"""
    logger.info("=" * 70)
    logger.info("TQQQ/SQQQ Pair Trading Backtest - 3 Years (2023-2026)")
    logger.info("=" * 70)
    
    # 策略參數
    entry_zscore = 2.0
    exit_zscore = 0.5
    stop_loss_zscore = 3.5
    position_pct = 0.1
    lookback_period = 60
    
    logger.info(f"Strategy Parameters:")
    logger.info(f"  Entry Z-Score: {entry_zscore}")
    logger.info(f"  Exit Z-Score: {exit_zscore}")
    logger.info(f"  Stop Loss Z-Score: {stop_loss_zscore}")
    logger.info(f"  Position Size: {position_pct*100}%")
    logger.info(f"  Lookback Period: {lookback_period} days")
    
    # 初始化回測引擎
    engine = TQQQSQQQBacktestEngine(
        entry_zscore=entry_zscore,
        exit_zscore=exit_zscore,
        stop_loss_zscore=stop_loss_zscore,
        position_pct=position_pct,
        lookback_period=lookback_period,
        initial_capital=1000000.0,
        commission_rate=0.001,
        slippage=0.001
    )
    
    # 生成模擬歷史數據
    logger.info("\nGenerating realistic historical data...")
    tqqq_data, sqqq_data = generate_realistic_mock_data(days=800)
    
    # 執行回測
    result = engine.run_backtest(tqqq_data, sqqq_data)
    
    # 打印結果
    logger.info("\n" + "=" * 70)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 70)
    logger.info(f"Period: {result.start_date.date()} to {result.end_date.date()}")
    logger.info(f"Initial Capital: ${result.initial_capital:,.2f}")
    logger.info(f"Final Capital: ${result.final_capital:,.2f}")
    logger.info(f"Total Return: {result.total_return_pct:.2f}%")
    logger.info(f"Total Trades: {result.total_trades}")
    logger.info(f"Winning Trades: {result.winning_trades}")
    logger.info(f"Losing Trades: {result.losing_trades}")
    logger.info(f"Win Rate: {result.win_rate:.2f}%")
    logger.info(f"Average Profit: ${result.avg_profit:,.2f}")
    logger.info(f"Average Loss: ${result.avg_loss:,.2f}")
    logger.info(f"Profit Factor: {result.profit_factor:.2f}")
    logger.info(f"Max Drawdown: {result.max_drawdown_pct:.2f}%")
    logger.info(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    logger.info(f"Volatility (Annual): {result.volatility:.2f}%")
    logger.info("=" * 70)
    
    # 保存結果
    output_dir = Path(project_root) / "reports"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存JSON結果
    result_file = output_dir / f"backtest_result_{timestamp}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False, default=str)
    
    # 保存權益曲線
    equity_file = output_dir / f"equity_curve_{timestamp}.csv"
    result.equity_curve.to_csv(equity_file)
    
    # 保存交易記錄
    if result.trades:
        trades_data = []
        for trade in result.trades:
            trades_data.append({
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'direction': trade.direction,
                'primary_asset': trade.primary_asset,
                'entry_price': trade.entry_price_primary,
                'exit_price': trade.exit_price_primary,
                'pnl': trade.pnl,
                'pnl_pct': trade.pnl_pct,
                'exit_reason': trade.exit_reason
            })
        trades_df = pd.DataFrame(trades_data)
        trades_file = output_dir / f"trades_{timestamp}.csv"
        trades_df.to_csv(trades_file, index=False)
        
        # 打印交易明細
        logger.info("\nTrade Details:")
        logger.info("-" * 70)
        for i, trade in enumerate(result.trades[:10], 1):  # 只顯示前10筆
            logger.info(f"{i}. {trade.entry_time.date()} -> {trade.exit_time.date()} | "
                       f"{trade.direction} | PnL: ${trade.pnl:,.2f} ({trade.pnl_pct:.2f}%) | "
                       f"{trade.exit_reason}")
        if len(result.trades) > 10:
            logger.info(f"... and {len(result.trades) - 10} more trades")
    
    logger.info(f"\nResults saved to:")
    logger.info(f"  - {result_file}")
    logger.info(f"  - {equity_file}")
    if result.trades:
        logger.info(f"  - {trades_file}")
    
    return result


if __name__ == "__main__":
    result = run_backtest_report()
