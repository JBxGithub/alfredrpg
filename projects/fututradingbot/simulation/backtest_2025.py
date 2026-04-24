"""
Z-Score 策略回測模組
測試 2025 年數據表現
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Backtest")


class PaperBacktest:
    """
    模擬交易回測系統
    
    測試 Z-Score 策略在歷史數據上的表現
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        zscore_threshold: float = 1.6,
        position_pct: float = 0.5,
        commission_rate: float = 0.001
    ):
        self.initial_capital = initial_capital
        self.zscore_threshold = zscore_threshold
        self.position_pct = position_pct
        self.commission_rate = commission_rate
        
        # 賬戶狀態
        self.cash = initial_capital
        self.position = None  # None, 'long', 'short'
        self.position_size = 0
        self.entry_price = 0.0
        
        # 交易記錄
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []
        
        logger.info(f"回測初始化: 資金=${initial_capital:,.2f}, Z-Score閾值={zscore_threshold}")
    
    def calculate_zscore(self, prices: pd.Series, period: int = 60) -> float:
        """計算 Z-Score"""
        if len(prices) < period:
            return 0.0
        
        recent_prices = prices[-period:]
        mean = recent_prices[:-1].mean()
        std = recent_prices[:-1].std()
        
        if std == 0:
            return 0.0
        
        current_price = prices.iloc[-1]
        zscore = (current_price - mean) / std
        return zscore
    
    def run_backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        執行回測
        
        Args:
            data: DataFrame with columns ['date', 'open', 'high', 'low', 'close', 'volume']
            
        Returns:
            回測結果摘要
        """
        logger.info(f"開始回測: {len(data)} 個數據點")
        logger.info(f"日期範圍: {data['date'].iloc[0]} 至 {data['date'].iloc[-1]}")
        
        for i in range(60, len(data)):
            current = data.iloc[i]
            date = current['date']
            price = current['close']
            
            # 計算 Z-Score
            prices_so_far = data['close'][:i+1]
            zscore = self.calculate_zscore(prices_so_far)
            
            # 檢查交易信號
            signal = self._check_signal(zscore)
            
            # 執行交易
            if signal == 'buy' and self.position is None:
                self._open_long(date, price)
            elif signal == 'sell' and self.position is None:
                self._open_short(date, price)
            elif signal == 'close' and self.position is not None:
                self._close_position(date, price)
            
            # 記錄權益曲線
            equity = self._calculate_equity(price)
            self.equity_curve.append({
                'date': date,
                'equity': equity,
                'zscore': zscore,
                'price': price,
                'position': self.position
            })
        
        # 平倉最後持倉
        if self.position is not None:
            final_price = data['close'].iloc[-1]
            final_date = data['date'].iloc[-1]
            self._close_position(final_date, final_price)
        
        return self._generate_report()
    
    def _check_signal(self, zscore: float) -> str:
        """檢查交易信號"""
        if zscore < -self.zscore_threshold:
            return 'buy'  # 做多
        elif zscore > self.zscore_threshold:
            return 'sell'  # 做空
        elif abs(zscore) < 0.5 and self.position is not None:
            return 'close'  # 平倉
        return 'hold'
    
    def _open_long(self, date: str, price: float):
        """開多倉"""
        position_value = self.cash * self.position_pct
        self.position_size = int(position_value / price)
        cost = self.position_size * price
        commission = cost * self.commission_rate
        
        self.cash -= (cost + commission)
        self.position = 'long'
        self.entry_price = price
        
        self.trades.append({
            'date': date,
            'action': 'BUY',
            'direction': 'long',
            'price': price,
            'size': self.position_size,
            'commission': commission,
            'pnl': -commission
        })
        
        logger.info(f"[{date}] 做多 {self.position_size} 股 @ ${price:.2f}")
    
    def _open_short(self, date: str, price: float):
        """開空倉"""
        position_value = self.cash * self.position_pct
        self.position_size = int(position_value / price)
        proceeds = self.position_size * price
        commission = proceeds * self.commission_rate
        
        self.cash += (proceeds - commission)
        self.position = 'short'
        self.entry_price = price
        
        self.trades.append({
            'date': date,
            'action': 'SELL',
            'direction': 'short',
            'price': price,
            'size': self.position_size,
            'commission': commission,
            'pnl': -commission
        })
        
        logger.info(f"[{date}] 做空 {self.position_size} 股 @ ${price:.2f}")
    
    def _close_position(self, date: str, price: float):
        """平倉"""
        if self.position == 'long':
            proceeds = self.position_size * price
            commission = proceeds * self.commission_rate
            pnl = (price - self.entry_price) * self.position_size - commission
            self.cash += (proceeds - commission)
            
        elif self.position == 'short':
            cost = self.position_size * price
            commission = cost * self.commission_rate
            pnl = (self.entry_price - price) * self.position_size - commission
            self.cash -= (cost + commission)
        
        self.trades.append({
            'date': date,
            'action': 'CLOSE',
            'direction': self.position,
            'price': price,
            'size': self.position_size,
            'commission': commission,
            'pnl': pnl
        })
        
        logger.info(f"[{date}] 平倉 {self.position} @ ${price:.2f}, 盈虧: ${pnl:+.2f}")
        
        self.position = None
        self.position_size = 0
        self.entry_price = 0.0
    
    def _calculate_equity(self, current_price: float) -> float:
        """計算當前權益"""
        if self.position is None:
            return self.cash
        
        if self.position == 'long':
            position_value = self.position_size * current_price
            return self.cash + position_value
        else:  # short
            liability = self.position_size * current_price
            return self.cash - liability
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成回測報告"""
        if not self.equity_curve:
            return {'error': 'No data'}
        
        equity_df = pd.DataFrame(self.equity_curve)
        
        # 基本指標
        final_equity = equity_df['equity'].iloc[-1]
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # 計算最大回撤
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
        max_drawdown = equity_df['drawdown'].min()
        
        # 交易統計
        total_trades = len([t for t in self.trades if t['action'] == 'CLOSE'])
        winning_trades = len([t for t in self.trades if t['action'] == 'CLOSE' and t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in self.trades)
        total_commission = sum(t['commission'] for t in self.trades)
        
        report = {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return_pct': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'max_drawdown_pct': max_drawdown,
            'total_pnl': total_pnl,
            'total_commission': total_commission,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
        
        # 輸出報告
        logger.info("=" * 60)
        logger.info("回測報告")
        logger.info("=" * 60)
        logger.info(f"初始資金: ${self.initial_capital:,.2f}")
        logger.info(f"最終權益: ${final_equity:,.2f}")
        logger.info(f"總回報: {total_return:+.2f}%")
        logger.info(f"交易次數: {total_trades}")
        logger.info(f"勝率: {win_rate:.1f}%")
        logger.info(f"最大回撤: {max_drawdown:.2f}%")
        logger.info(f"總盈虧: ${total_pnl:+.2f}")
        logger.info(f"總手續費: ${total_commission:.2f}")
        logger.info("=" * 60)
        
        return report


def run_2025_backtest():
    """執行 2025 年回測"""
    logger.info("開始 2025 年 Z-Score 策略回測")
    logger.info("策略參數: Z-Score 閾值 = 1.6")
    
    # 創建模擬數據（實際使用時應加載真實歷史數據）
    dates = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
    np.random.seed(42)
    
    # 生成模擬 TQQQ 價格數據
    initial_price = 70.0
    returns = np.random.normal(0.001, 0.02, len(dates))
    prices = initial_price * (1 + returns).cumprod()
    
    data = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.normal(0, 0.001, len(dates))),
        'high': prices * (1 + abs(np.random.normal(0, 0.01, len(dates)))),
        'low': prices * (1 - abs(np.random.normal(0, 0.01, len(dates)))),
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, len(dates))
    })
    
    # 執行回測
    backtest = PaperBacktest(
        initial_capital=100000.0,
        zscore_threshold=1.6,
        position_pct=0.5,
        commission_rate=0.001
    )
    
    report = backtest.run_backtest(data)
    
    return report


if __name__ == "__main__":
    report = run_2025_backtest()
    
    # 保存報告
    import json
    with open('backtest_2025_report.json', 'w') as f:
        json.dump({k: v for k, v in report.items() if k not in ['trades', 'equity_curve']}, f, indent=2)
    
    logger.info("回測報告已保存至 backtest_2025_report.json")
