"""
FutuTradingBot - 2024年回測（靈活套利策略）
回測期間: 2024-01-01 至 2024-12-31
策略: 靈活套利策略 - 根據市場狀態動態調整方向
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import yfinance as yf
import warnings
import sys
import os

# 添加項目路徑
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot')

warnings.filterwarnings('ignore')


@dataclass
class MarketState:
    """市場狀態定義"""
    state: Literal["bull", "bear", "choppy"]  # 牛市、熊市、震盪
    primary_direction: Literal["long", "short", "both"]  # 主導方向
    zscore_threshold: float  # 動態Z-Score閾值
    position_pct: float  # 倉位比例
    
    def __str__(self):
        return f"{self.state.upper()} | {self.primary_direction} | Z:{self.zscore_threshold} | Pos:{self.position_pct}"


class FlexibleArbitrageStrategy:
    """
    靈活套利策略
    
    核心邏輯:
    1. 每日判斷市場狀態（200日均線 + VIX）
    2. 根據市場狀態動態調整:
       - 牛市: 主要做多，Z-Score閾值1.2
       - 熊市: 主要做空，Z-Score閾值1.2
       - 震盪: 雙向交易，Z-Score閾值1.5
    3. 持續交易，不論牛熊都有機會
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.name = "Flexible Arbitrage Strategy"
        self.version = "3.0.0"
        
        # 基礎參數
        self.take_profit_pct = 0.05  # 5%止盈
        self.stop_loss_pct = 0.03    # 3%止損
        self.time_stop_days = 5      # 5天時間止損
        self.exit_zscore = 0.3       # 出場Z-Score
        
        # 市場狀態判斷參數
        self.ma_period = 200         # 200日均線
        self.vix_bull_threshold = 20  # VIX牛市閾值
        self.vix_bear_threshold = 25  # VIX熊市閾值
        
        # Z-Score閾值範圍
        self.zscore_threshold_bull = 1.2
        self.zscore_threshold_bear = 1.2
        self.zscore_threshold_choppy = 1.5
        
        if config:
            self.__dict__.update(config)
        
        self.current_positions = []
        
        print(f"靈活套利策略初始化:")
        print(f"  止盈/止損: {self.take_profit_pct*100}%/{self.stop_loss_pct*100}%")
        print(f"  時間止損: {self.time_stop_days}天")
        print(f"  Z-Score閾值: 牛市/熊市={self.zscore_threshold_bull}, 震盪={self.zscore_threshold_choppy}")
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
        df = data.copy()
        
        # 計算Z-Score
        lookback = 60
        df['price_ma'] = df['close'].rolling(window=lookback).mean()
        df['price_std'] = df['close'].rolling(window=lookback).std()
        df['zscore'] = (df['close'] - df['price_ma']) / df['price_std']
        
        # 計算RSI
        rsi_period = 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 計算MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 計算200日均線
        df['ma200'] = df['close'].rolling(window=self.ma_period).mean()
        
        return df
    
    def determine_market_state(self, price: float, ma200: float, vix: Optional[float] = None) -> MarketState:
        """
        判斷市場狀態
        
        Args:
            price: 當前價格
            ma200: 200日均線
            vix: VIX指數（可選）
            
        Returns:
            MarketState: 市場狀態對象
        """
        # 如果MA200無效（NaN），默認使用震盪市策略（雙向交易）
        if pd.isna(ma200):
            return MarketState(
                state="choppy",
                primary_direction="both",
                zscore_threshold=self.zscore_threshold_choppy,
                position_pct=0.50
            )
        
        # 如果沒有VIX數據，只用價格和均線判斷
        if vix is None:
            # 簡化判斷：基於價格與200日均線的關係
            deviation = (price - ma200) / ma200
            
            if deviation > 0.05:  # 價格高於200日均線5%以上
                return MarketState(
                    state="bull",
                    primary_direction="long",
                    zscore_threshold=self.zscore_threshold_bull,
                    position_pct=0.70
                )
            elif deviation < -0.05:  # 價格低於200日均線5%以上
                return MarketState(
                    state="bear",
                    primary_direction="short",
                    zscore_threshold=self.zscore_threshold_bear,
                    position_pct=0.70
                )
            else:
                return MarketState(
                    state="choppy",
                    primary_direction="both",
                    zscore_threshold=self.zscore_threshold_choppy,
                    position_pct=0.50
                )
        
        # 有VIX數據時的判斷
        # 牛市條件: 價格在200日均線之上 + VIX低
        if price > ma200 and vix < self.vix_bull_threshold:
            return MarketState(
                state="bull",
                primary_direction="long",
                zscore_threshold=self.zscore_threshold_bull,
                position_pct=0.70
            )
        
        # 熊市條件: 價格在200日均線之下 + VIX高
        elif price < ma200 and vix > self.vix_bear_threshold:
            return MarketState(
                state="bear",
                primary_direction="short",
                zscore_threshold=self.zscore_threshold_bear,
                position_pct=0.70
            )
        
        # 震盪市: 其他情況
        else:
            return MarketState(
                state="choppy",
                primary_direction="both",
                zscore_threshold=self.zscore_threshold_choppy,
                position_pct=0.50
            )
    
    def generate_signal(self, data: pd.DataFrame, vix_data: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        生成交易信號
        
        進場條件:
        - 牛市: Z-Score < -1.2 做多
        - 熊市: Z-Score > 1.2 做空
        - 震盪: Z-Score < -1.5 做多 或 Z-Score > 1.5 做空
        """
        # 只需要足夠計算Z-Score的數據（60天回顧期）
        min_required_data = 70
        if len(data) < min_required_data:
            return None
        
        # 計算指標
        df = self.calculate_indicators(data)
        current = df.iloc[-1]
        
        # 檢查Z-Score有效性（MA200可以為NaN，會被視為震盪市）
        if pd.isna(current['zscore']):
            return None
        
        # 判斷市場狀態
        market_state = self.determine_market_state(
            price=current['close'],
            ma200=current['ma200'],
            vix=vix_data
        )
        
        zscore = current['zscore']
        
        # 做多條件檢查
        if market_state.primary_direction in ["long", "both"]:
            if zscore < -market_state.zscore_threshold:
                return {
                    'signal_type': 'buy',
                    'symbol': 'TQQQ',
                    'price': current['close'],
                    'confidence': min(abs(zscore) / 3, 0.95),
                    'reason': f"Z-Score({zscore:.2f})+{market_state.state}市做多",
                    'market_state': market_state.state,
                    'zscore_threshold': market_state.zscore_threshold,
                    'position_pct': market_state.position_pct
                }
        
        # 做空條件檢查
        if market_state.primary_direction in ["short", "both"]:
            if zscore > market_state.zscore_threshold:
                return {
                    'signal_type': 'sell',
                    'symbol': 'TQQQ',
                    'price': current['close'],
                    'confidence': min(abs(zscore) / 3, 0.95),
                    'reason': f"Z-Score({zscore:.2f})+{market_state.state}市做空",
                    'market_state': market_state.state,
                    'zscore_threshold': market_state.zscore_threshold,
                    'position_pct': market_state.position_pct
                }
        
        return None
    
    def check_exit(self, position: Dict[str, Any], current_data: pd.DataFrame, 
                   current_date: datetime = None) -> tuple[bool, str]:
        """檢查是否應該平倉"""
        if len(current_data) < 60:
            return False, ""
        
        # 計算當前指標
        df = self.calculate_indicators(current_data)
        current = df.iloc[-1]
        
        entry_price = position['entry_price']
        current_price = current['close']
        entry_time = position['entry_time']
        direction = position['direction']
        
        # 計算盈虧
        if direction == 'long':
            pnl_pct = (current_price - entry_price) / entry_price
        else:  # short
            pnl_pct = (entry_price - current_price) / entry_price
        
        zscore = current['zscore']
        
        # 止盈檢查
        if pnl_pct >= self.take_profit_pct:
            return True, f"止盈({pnl_pct*100:.2f}%)"
        
        # 止損檢查
        if pnl_pct <= -self.stop_loss_pct:
            return True, f"止損({pnl_pct*100:.2f}%)"
        
        # Z-Score回歸止盈
        if abs(zscore) < self.exit_zscore:
            return True, f"Z-Score回歸({zscore:.2f})"
        
        # 時間止損檢查
        if isinstance(entry_time, str):
            entry_time = datetime.fromisoformat(entry_time)
        
        if current_date is None:
            current_date = current_data.index[-1]
            if isinstance(current_date, pd.Timestamp):
                current_date = current_date.to_pydatetime()
        
        days_held = (current_date - entry_time).days
        if days_held >= self.time_stop_days:
            return True, f"時間止損({days_held}天)"
        
        return False, ""
    
    def get_position_size(self, capital: float, current_price: float, position_pct: float) -> int:
        """計算倉位大小"""
        position_value = capital * position_pct
        shares = int(position_value / current_price)
        return max(shares, 1)
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """獲取策略信息"""
        return {
            'name': self.name,
            'version': self.version,
            'take_profit_pct': self.take_profit_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'time_stop_days': self.time_stop_days,
            'exit_zscore': self.exit_zscore,
            'ma_period': self.ma_period,
            'vix_bull_threshold': self.vix_bull_threshold,
            'vix_bear_threshold': self.vix_bear_threshold,
            'market_state_rules': {
                'bull': {'zscore': self.zscore_threshold_bull, 'direction': 'long', 'position': 0.70},
                'bear': {'zscore': self.zscore_threshold_bear, 'direction': 'short', 'position': 0.70},
                'choppy': {'zscore': self.zscore_threshold_choppy, 'direction': 'both', 'position': 0.50}
            }
        }


@dataclass
class BacktestTrade:
    """回測交易記錄"""
    entry_date: datetime
    exit_date: Optional[datetime]
    direction: str
    entry_price: float
    exit_price: Optional[float]
    shares: int
    pnl: float
    pnl_pct: float
    exit_reason: str
    market_state: str


@dataclass
class BacktestResult:
    """回測結果"""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return_pct: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    max_drawdown_pct: float
    sharpe_ratio: float
    volatility: float
    trades: List[BacktestTrade] = field(default_factory=list)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)
    
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
            'max_drawdown_pct': float(self.max_drawdown_pct),
            'sharpe_ratio': float(self.sharpe_ratio),
            'volatility': float(self.volatility)
        }


class FlexibleArbitrageBacktestEngine:
    """靈活套利回測引擎"""
    
    def __init__(
        self,
        strategy: FlexibleArbitrageStrategy,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.001,
        slippage: float = 0.001
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        self.cash = initial_capital
        self.position = None
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[Dict] = []
        
    def fetch_data(self, symbol: str = 'TQQQ', period: str = '5y') -> pd.DataFrame:
        """從Yahoo Finance獲取數據"""
        print(f"📊 正在獲取 {symbol} 歷史數據...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        # 標準化列名
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # 處理索引
        df = df.reset_index()
        
        # 找到日期列
        date_col = None
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                date_col = col
                break
        
        if date_col:
            df = df.rename(columns={date_col: 'timestamp'})
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        
        print(f"✅ 獲取數據成功: {len(df)} 條記錄")
        print(f"   期間: {df.index[0]} ~ {df.index[-1]}")
        return df
    
    def run(
        self,
        data: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> BacktestResult:
        """執行回測"""
        
        # 準備數據
        df = data.copy()
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]
        
        df = df.sort_index()
        
        print(f"\n🚀 開始回測...")
        print(f"   期間: {df.index[0]} ~ {df.index[-1]}")
        print(f"   初始資金: ${self.initial_capital:,.2f}")
        print(f"   數據點數: {len(df)}")
        
        # 逐日回測
        for i in range(len(df)):
            current_date = df.index[i]
            current_data = df.iloc[:i+1].copy()
            current_price = df['close'].iloc[i]
            
            # 檢查平倉條件
            if self.position:
                should_exit, exit_reason = self.strategy.check_exit(
                    self.position, current_data, current_date
                )
                
                if should_exit:
                    self._close_position(current_date, current_price, exit_reason)
            
            # 檢查開倉條件（無持倉時）
            if not self.position:
                signal = self.strategy.generate_signal(current_data)
                
                if signal:
                    self._open_position(signal, current_date, current_data)
            
            # 記錄權益曲線
            self._record_equity(current_date, current_price)
        
        # 回測結束，平倉所有持倉
        if self.position:
            self._close_position(df.index[-1], df['close'].iloc[-1], "回測結束平倉")
        
        return self._generate_result(df)
    
    def _open_position(self, signal, timestamp: datetime, data: pd.DataFrame):
        """開倉"""
        current_price = data['close'].iloc[-1]
        
        # 考慮滑點
        signal_value = signal.get('signal_type', '').lower()
        
        if signal_value == 'buy':
            executed_price = current_price * (1 + self.slippage)
            direction = 'long'
        else:
            executed_price = current_price * (1 - self.slippage)
            direction = 'short'
        
        # 獲取倉位比例
        position_pct = signal.get('position_pct', 0.50)
        
        # 計算倉位大小
        shares = self.strategy.get_position_size(self.cash, executed_price, position_pct)
        
        if shares <= 0:
            return
        
        # 計算成本
        trade_value = executed_price * shares
        commission = trade_value * self.commission_rate
        total_cost = trade_value + commission
        
        if total_cost > self.cash:
            return
        
        # 扣除現金
        self.cash -= total_cost
        
        # 創建倉位
        market_state = signal.get('market_state', 'unknown')
        self.position = {
            'entry_time': timestamp,
            'entry_price': executed_price,
            'shares': shares,
            'direction': direction,
            'commission': commission,
            'market_state': market_state
        }
        
        print(f"   📈 開倉 [{direction.upper()}] {timestamp.strftime('%Y-%m-%d')} @ ${executed_price:.2f} x {shares}股 | 市場: {market_state}")
    
    def _close_position(self, timestamp: datetime, current_price: float, reason: str):
        """平倉"""
        if not self.position:
            return
        
        # 考慮滑點
        if self.position['direction'] == 'long':
            executed_price = current_price * (1 - self.slippage)
        else:
            executed_price = current_price * (1 + self.slippage)
        
        # 計算盈虧
        entry_price = self.position['entry_price']
        shares = self.position['shares']
        market_state = self.position.get('market_state', 'unknown')
        
        if self.position['direction'] == 'long':
            pnl = (executed_price - entry_price) * shares
            pnl_pct = (executed_price - entry_price) / entry_price
        else:  # short
            pnl = (entry_price - executed_price) * shares
            pnl_pct = (entry_price - executed_price) / entry_price
        
        # 扣除佣金
        commission = executed_price * shares * self.commission_rate
        pnl -= commission
        
        # 回收資金
        trade_value = executed_price * shares
        self.cash += trade_value - commission
        
        # 記錄交易
        trade = BacktestTrade(
            entry_date=self.position['entry_time'],
            exit_date=timestamp,
            direction=self.position['direction'],
            entry_price=entry_price,
            exit_price=executed_price,
            shares=shares,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason=reason,
            market_state=market_state
        )
        self.trades.append(trade)
        
        emoji = "✅" if pnl > 0 else "❌"
        print(f"   {emoji} 平倉 [{self.position['direction'].upper()}] {timestamp.strftime('%Y-%m-%d')} @ ${executed_price:.2f} | P&L: ${pnl:,.2f} ({pnl_pct*100:+.2f}%) | {reason}")
        
        # 清空倉位
        self.position = None
    
    def _record_equity(self, timestamp: datetime, current_price: float):
        """記錄權益曲線"""
        position_value = 0
        if self.position:
            if self.position['direction'] == 'long':
                position_value = current_price * self.position['shares']
            else:  # short
                position_value = self.position['entry_price'] * self.position['shares']
        
        total_equity = self.cash + position_value
        self.equity_curve.append({
            'timestamp': timestamp,
            'cash': self.cash,
            'position_value': position_value,
            'total_equity': total_equity
        })
    
    def _generate_result(self, df: pd.DataFrame) -> BacktestResult:
        """生成回測結果"""
        
        # 創建權益曲線DataFrame
        equity_df = pd.DataFrame(self.equity_curve)
        if not equity_df.empty:
            equity_df.set_index('timestamp', inplace=True)
        
        # 計算績效指標
        initial_capital = self.initial_capital
        final_capital = self.cash
        total_return_pct = ((final_capital - initial_capital) / initial_capital) * 100
        
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
        
        # 計算最大回撤
        if not equity_df.empty:
            equity_df['peak'] = equity_df['total_equity'].cummax()
            equity_df['drawdown'] = equity_df['total_equity'] - equity_df['peak']
            equity_df['drawdown_pct'] = (equity_df['drawdown'] / equity_df['peak']) * 100
            max_drawdown_pct = equity_df['drawdown_pct'].min()
            
            # 計算夏普比率
            equity_df['returns'] = equity_df['total_equity'].pct_change().dropna()
            if equity_df['returns'].std() > 0:
                risk_free_rate = 0.02
                excess_returns = equity_df['returns'] - risk_free_rate / 252
                sharpe_ratio = np.sqrt(252) * excess_returns.mean() / equity_df['returns'].std()
                volatility = equity_df['returns'].std() * np.sqrt(252) * 100
            else:
                sharpe_ratio = 0
                volatility = 0
        else:
            max_drawdown_pct = 0
            sharpe_ratio = 0
            volatility = 0
        
        return BacktestResult(
            start_date=df.index[0],
            end_date=df.index[-1],
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_return_pct=total_return_pct,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
            trades=self.trades,
            equity_curve=equity_df
        )


def run_backtest():
    """執行2024年度回測（靈活套利策略）"""
    
    print("="*70)
    print("TQQQ 靈活套利策略 - 2024年度回測")
    print("="*70)
    print("回測期間: 2024-01-01 至 2024-12-31")
    print("策略: 根據市場狀態動態調整方向（牛市做多/熊市做空/震盪雙向）")
    print("Z-Score閾值: 牛市/熊市=1.2, 震盪=1.5")
    print("="*70)
    
    # 策略配置
    config = {
        'take_profit_pct': 0.05,
        'stop_loss_pct': 0.03,
        'time_stop_days': 5,
        'exit_zscore': 0.3,
        'zscore_threshold_bull': 1.2,
        'zscore_threshold_bear': 1.2,
        'zscore_threshold_choppy': 1.5
    }
    
    # 創建策略
    strategy = FlexibleArbitrageStrategy(config)
    
    # 創建回測引擎
    engine = FlexibleArbitrageBacktestEngine(
        strategy=strategy,
        initial_capital=100000.0,
        commission_rate=0.001,
        slippage=0.001
    )
    
    # 獲取數據
    data = engine.fetch_data('TQQQ', period='5y')
    
    # 執行回測（2024年度）
    result = engine.run(
        data,
        start_date='2024-01-01',
        end_date='2024-12-31'
    )
    
    # 輸出結果
    print("\n" + "="*70)
    print("回測結果")
    print("="*70)
    print(f"回測期間: {result.start_date} ~ {result.end_date}")
    print(f"初始資金: ${result.initial_capital:,.2f}")
    print(f"最終資金: ${result.final_capital:,.2f}")
    print(f"總回報: {result.total_return_pct:.2f}%")
    print(f"總交易次數: {result.total_trades}")
    print(f"勝率: {result.win_rate:.2f}%")
    print(f"平均盈利: ${result.avg_profit:,.2f}")
    print(f"平均虧損: ${result.avg_loss:,.2f}")
    print(f"盈虧比: {result.profit_factor:.2f}")
    print(f"最大回撤: {result.max_drawdown_pct:.2f}%")
    print(f"夏普比率: {result.sharpe_ratio:.2f}")
    print(f"波動率: {result.volatility:.2f}%")
    print("="*70)
    
    # 顯示交易明細
    if result.trades:
        print("\n📋 交易明細:")
        print("-" * 70)
        for i, trade in enumerate(result.trades, 1):
            emoji = "✅" if trade.pnl > 0 else "❌"
            print(f"{i}. {emoji} [{trade.direction.upper()}] {trade.entry_date.strftime('%Y-%m-%d')} -> {trade.exit_date.strftime('%Y-%m-%d')} | "
                  f"P&L: ${trade.pnl:,.2f} ({trade.pnl_pct*100:+.2f}%) | {trade.exit_reason} | 市場: {trade.market_state}")
    
    # 保存結果
    save_results(result, strategy)
    
    return result


def save_results(result: BacktestResult, strategy: FlexibleArbitrageStrategy):
    """保存回測結果"""
    
    report_dir = 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot/reports'
    
    # 確保目錄存在
    os.makedirs(report_dir, exist_ok=True)
    
    # 保存JSON結果
    json_file = f'{report_dir}/backtest_2024_flexible.json'
    result_dict = {
        'summary': result.to_dict(),
        'strategy_config': strategy.get_strategy_info(),
        'trades': [
            {
                'entry_date': str(t.entry_date),
                'exit_date': str(t.exit_date),
                'direction': t.direction,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'shares': t.shares,
                'pnl': t.pnl,
                'pnl_pct': t.pnl_pct,
                'exit_reason': t.exit_reason,
                'market_state': t.market_state
            }
            for t in result.trades
        ]
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, default=str)
    
    print(f"\n📊 結果已保存: {json_file}")


if __name__ == '__main__':
    result = run_backtest()
