"""
FutuTradingBot 專業級回測系統
完整模擬 MTF + 風險管理 + 交易執行
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, List
from datetime import datetime, date
from dataclasses import dataclass, asdict

from trading_engine import TradingEngine
from indicators import TechnicalIndicators


@dataclass
class TradeRecord:
    """交易記錄"""
    entry_date: date
    exit_date: date
    direction: str
    entry_price: float
    exit_price: float
    position_size: int
    pnl: float
    pnl_pct: float
    exit_reason: str
    holding_days: int


class ProfessionalBacktest:
    """專業級回測器"""
    
    def __init__(self, start_date: str = '2019-01-01', 
                 end_date: str = '2024-12-31',
                 initial_capital: float = 100000):
        self.start_date = pd.to_datetime(start_date).tz_localize('America/New_York')
        self.end_date = pd.to_datetime(end_date).tz_localize('America/New_York')
        self.initial_capital = initial_capital
        
        self.engine = TradingEngine(initial_capital)
        self.trades: List[TradeRecord] = []
        self.daily_nav: List[Dict] = []
        
    def run(self) -> Dict:
        """
        執行回測
        
        Returns:
            dict with backtest results
        """
        print(f"開始回測: {self.start_date.date()} 至 {self.end_date.date()}")
        print(f"初始資金: ${self.initial_capital:,.2f}")
        print("=" * 60)
        
        # 獲取交易日列表
        qqq_data = self.engine.fetch_data('QQQ', period='6y', interval='1d')
        trading_days = qqq_data.index[
            (qqq_data.index >= self.start_date) & 
            (qqq_data.index <= self.end_date)
        ]
        
        print(f"總交易日: {len(trading_days)}")
        
        for i, current_date in enumerate(trading_days):
            current_date = current_date.date()
            
            # 每日運行
            result = self.engine.run_daily(current_date)
            
            # 記錄 NAV
            risk_report = result.get('risk_report', {})
            self.daily_nav.append({
                'date': current_date,
                'nav': risk_report.get('current_capital', self.initial_capital),
                'daily_pnl': risk_report.get('daily_pnl', 0),
                'position': self.engine.position
            })
            
            # 記錄交易
            for action in result.get('actions', []):
                if action['action'] == 'exit':
                    details = action['details']
                    # 找到對應的入場記錄
                    # 簡化處理: 使用當前持倉信息
                    trade = TradeRecord(
                        entry_date=self.engine.entry_date,
                        exit_date=current_date,
                        direction=self.engine.position or 'unknown',
                        entry_price=self.engine.entry_price,
                        exit_price=details['exit_price'],
                        position_size=self.engine.position_size,
                        pnl=details['pnl'],
                        pnl_pct=details['pnl_pct'],
                        exit_reason=details['reason'],
                        holding_days=details['holding_days']
                    )
                    self.trades.append(trade)
            
            # 進度顯示
            if (i + 1) % 252 == 0:  # 每年
                year = current_date.year
                nav = risk_report.get('current_capital', self.initial_capital)
                print(f"{year}年末: ${nav:,.2f}")
        
        print("=" * 60)
        
        # 計算結果
        return self.calculate_metrics()
    
    def calculate_metrics(self) -> Dict:
        """
        計算回測指標
        
        Returns:
            dict with performance metrics
        """
        if not self.daily_nav:
            return {'error': '無回測數據'}
        
        nav_df = pd.DataFrame(self.daily_nav)
        nav_df['date'] = pd.to_datetime(nav_df['date'])
        nav_df = nav_df.sort_values('date')
        
        # 基本指標
        final_nav = nav_df['nav'].iloc[-1]
        total_return = (final_nav - self.initial_capital) / self.initial_capital
        
        # 年化回報
        years = (nav_df['date'].iloc[-1] - nav_df['date'].iloc[0]).days / 365.25
        annualized_return = (final_nav / self.initial_capital) ** (1/years) - 1
        
        # 最大回撤
        nav_df['peak'] = nav_df['nav'].cummax()
        nav_df['drawdown'] = (nav_df['nav'] - nav_df['peak']) / nav_df['peak']
        max_drawdown = nav_df['drawdown'].min()
        
        # 夏普比率 (假設無風險利率 2%)
        daily_returns = nav_df['nav'].pct_change().dropna()
        excess_returns = daily_returns - 0.02/252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / excess_returns.std() if excess_returns.std() != 0 else 0
        
        # 交易統計
        if self.trades:
            trades_df = pd.DataFrame([asdict(t) for t in self.trades])
            
            total_trades = len(trades_df)
            winning_trades = len(trades_df[trades_df['pnl'] > 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            avg_profit = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if len(trades_df[trades_df['pnl'] < 0]) > 0 else 0
            
            avg_holding_days = trades_df['holding_days'].mean()
            
            long_trades = len(trades_df[trades_df['direction'] == 'long'])
            short_trades = len(trades_df[trades_df['direction'] == 'short'])
        else:
            total_trades = 0
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
            avg_holding_days = 0
            long_trades = 0
            short_trades = 0
        
        # 與 Buy & Hold 比較
        try:
            tqqq_data = self.engine.fetch_data('TQQQ', period='6y', interval='1d')
            tqqq_start = tqqq_data['Close'].iloc[0]
            tqqq_end = tqqq_data['Close'].iloc[-1]
            buy_hold_return = (tqqq_end - tqqq_start) / tqqq_start
            outperformance = total_return - buy_hold_return
        except:
            buy_hold_return = 0
            outperformance = 0
        
        results = {
            'version': 'Professional_MTF',
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'initial_capital': self.initial_capital,
            'final_nav': final_nav,
            'total_return_pct': total_return * 100,
            'annualized_return_pct': annualized_return * 100,
            'max_drawdown_pct': max_drawdown * 100,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': total_trades,
            'win_rate': win_rate * 100,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'avg_holding_days': avg_holding_days,
            'long_trades': long_trades,
            'short_trades': short_trades,
            'buy_hold_return_pct': buy_hold_return * 100,
            'outperformance_pct': outperformance * 100
        }
        
        # 打印結果
        self.print_results(results)
        
        return results
    
    def print_results(self, results: Dict):
        """打印回測結果"""
        print("\n" + "=" * 60)
        print("回測結果 - Professional MTF 策略")
        print("=" * 60)
        
        print(f"\n【基本指標】")
        print(f"初始資金: ${results['initial_capital']:,.2f}")
        print(f"最終資產: ${results['final_nav']:,.2f}")
        print(f"總回報率: {results['total_return_pct']:.2f}%")
        print(f"年化回報率: {results['annualized_return_pct']:.2f}%")
        print(f"最大回撤: {results['max_drawdown_pct']:.2f}%")
        print(f"夏普比率: {results['sharpe_ratio']:.2f}")
        
        print(f"\n【交易統計】")
        print(f"總交易: {results['total_trades']} 次")
        print(f"  多單: {results['long_trades']} 次")
        print(f"  空單: {results['short_trades']} 次")
        print(f"勝率: {results['win_rate']:.1f}%")
        print(f"平均盈利: ${results['avg_profit']:,.2f}")
        print(f"平均虧損: ${results['avg_loss']:,.2f}")
        print(f"平均持倉: {results['avg_holding_days']:.1f} 天")
        
        print(f"\n【策略對比】")
        print(f"策略回報: {results['total_return_pct']:.2f}%")
        print(f"Buy & Hold: {results['buy_hold_return_pct']:.2f}%")
        print(f"超額收益: {results['outperformance_pct']:+.2f}%")
        
        print("=" * 60)
    
    def save_results(self, filename: str = None):
        """
        保存回測結果
        
        Args:
            filename: 輸出文件名
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'backtest_professional_{timestamp}.json'
        
        results = self.calculate_metrics()
        
        # 保存指標
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        # 保存交易記錄
        if self.trades:
            trades_df = pd.DataFrame([asdict(t) for t in self.trades])
            trades_file = filename.replace('.json', '_trades.csv')
            trades_df.to_csv(trades_file, index=False)
        
        # 保存 NAV
        nav_df = pd.DataFrame(self.daily_nav)
        nav_file = filename.replace('.json', '_nav.csv')
        nav_df.to_csv(nav_file, index=False)
        
        print(f"\n結果已保存:")
        print(f"  指標: {filename}")
        if self.trades:
            print(f"  交易: {trades_file}")
        print(f"  NAV: {nav_file}")


if __name__ == '__main__':
    print("Professional Backtest 系統")
    print("=" * 60)
    
    # 運行回測
    backtest = ProfessionalBacktest(
        start_date='2019-01-01',
        end_date='2024-12-31',
        initial_capital=100000
    )
    
    results = backtest.run()
    backtest.save_results()
