"""
Z-Score 策略測試 - 使用 2025 年數據
測試 Z-Score 策略在實際數據上嘅表現
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.strategies.zscore_strategy import ZScoreStrategy
from src.indicators.technical import calculate_zscore_advanced


def fetch_tqqq_data_2025():
    """獲取 TQQQ 2025 年數據"""
    print("正在獲取 TQQQ 2025 年數據...")
    
    ticker = yf.Ticker("TQQQ")
    df = ticker.history(start='2025-01-01', end='2025-12-31', interval='1d')
    
    if df.empty:
        raise ValueError("無法獲取 TQQQ 數據")
    
    # 移除時區信息
    df.index = df.index.tz_localize(None)
    df.reset_index(inplace=True)
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    
    print(f"獲取到 {len(df)} 條數據")
    print(f"日期範圍: {df['date'].iloc[0]} 至 {df['date'].iloc[-1]}")
    print(f"價格範圍: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    return df


def backtest_zscore_strategy(df, initial_capital=100000):
    """
    回測 Z-Score 策略
    
    Args:
        df: TQQQ 價格數據
        initial_capital: 初始資金
        
    Returns:
        回測結果
    """
    print("\n" + "=" * 60)
    print("開始 Z-Score 策略回測")
    print("=" * 60)
    
    # 初始化策略
    strategy = ZScoreStrategy(
        period=60,
        upper_threshold=2.0,
        lower_threshold=-2.0,
        exit_threshold=0.5,
        position_pct=0.5
    )
    
    # 計算 Z-Score
    result = calculate_zscore_advanced(df, period=60)
    df['zscore'] = result.zscore
    df['ma'] = result.ma
    
    # 回測變數
    cash = initial_capital
    position = None  # None, 'long', 'short'
    position_qty = 0
    position_entry_price = 0
    trades = []
    equity_curve = []
    
    # 逐日回測
    for i in range(60, len(df)):  # 從第60天開始（有足夠數據計算Z-Score）
        row = df.iloc[i]
        current_price = row['close']
        current_zscore = row['zscore']
        current_date = row['date']
        
        if pd.isna(current_zscore):
            continue
        
        # 記錄權益
        position_value = position_qty * current_price if position else 0
        total_equity = cash + position_value
        equity_curve.append({
            'date': current_date,
            'equity': total_equity,
            'cash': cash,
            'position_value': position_value,
            'zscore': current_zscore
        })
        
        # 檢查出場
        if position == 'long' and strategy.should_exit(current_zscore, 'long'):
            # 平多倉
            proceeds = position_qty * current_price
            pnl = proceeds - (position_qty * position_entry_price)
            cash += proceeds
            
            trades.append({
                'date': current_date,
                'action': 'SELL',
                'direction': 'long',
                'price': current_price,
                'qty': position_qty,
                'pnl': pnl,
                'pnl_pct': (pnl / (position_qty * position_entry_price)) * 100,
                'reason': 'Z-Score回歸'
            })
            
            print(f"  [{current_date.strftime('%Y-%m-%d')}] 平多倉 @ ${current_price:.2f} | PnL: ${pnl:.2f}")
            position = None
            position_qty = 0
            
        elif position == 'short' and strategy.should_exit(current_zscore, 'short'):
            # 平空倉
            cover_cost = position_qty * current_price
            entry_value = position_qty * position_entry_price
            pnl = entry_value - cover_cost
            cash += entry_value + pnl
            
            trades.append({
                'date': current_date,
                'action': 'BUY',
                'direction': 'short',
                'price': current_price,
                'qty': position_qty,
                'pnl': pnl,
                'pnl_pct': (pnl / entry_value) * 100,
                'reason': 'Z-Score回歸'
            })
            
            print(f"  [{current_date.strftime('%Y-%m-%d')}] 平空倉 @ ${current_price:.2f} | PnL: ${pnl:.2f}")
            position = None
            position_qty = 0
        
        # 檢查進場
        if position is None:
            # 做多信號
            if strategy.should_enter_long(current_zscore):
                position_qty = strategy.get_position_size(cash, current_price)
                if position_qty > 0:
                    cost = position_qty * current_price
                    cash -= cost
                    position = 'long'
                    position_entry_price = current_price
                    
                    trades.append({
                        'date': current_date,
                        'action': 'BUY',
                        'direction': 'long',
                        'price': current_price,
                        'qty': position_qty,
                        'pnl': 0,
                        'reason': f'Z-Score={current_zscore:.2f}'
                    })
                    
                    print(f"  [{current_date.strftime('%Y-%m-%d')}] 做多 {position_qty}股 @ ${current_price:.2f} | Z-Score={current_zscore:.2f}")
            
            # 做空信號
            elif strategy.should_enter_short(current_zscore):
                position_qty = strategy.get_position_size(cash, current_price)
                if position_qty > 0:
                    position = 'short'
                    position_entry_price = current_price
                    # 做空不需要立即支付，但保留保證金
                    
                    trades.append({
                        'date': current_date,
                        'action': 'SELL',
                        'direction': 'short',
                        'price': current_price,
                        'qty': position_qty,
                        'pnl': 0,
                        'reason': f'Z-Score={current_zscore:.2f}'
                    })
                    
                    print(f"  [{current_date.strftime('%Y-%m-%d')}] 做空 {position_qty}股 @ ${current_price:.2f} | Z-Score={current_zscore:.2f}")
    
    # 計算回測結果
    final_equity = equity_curve[-1]['equity'] if equity_curve else initial_capital
    total_return = final_equity - initial_capital
    total_return_pct = (total_return / initial_capital) * 100
    
    # 計算勝率
    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
    win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
    
    # 計算最大回撤
    equity_df = pd.DataFrame(equity_curve)
    equity_df['peak'] = equity_df['equity'].cummax()
    equity_df['drawdown'] = (equity_df['equity'] - equity_df['peak']) / equity_df['peak'] * 100
    max_drawdown = equity_df['drawdown'].min()
    
    return {
        'initial_capital': initial_capital,
        'final_equity': final_equity,
        'total_return': total_return,
        'total_return_pct': total_return_pct,
        'total_trades': len(trades),
        'winning_trades': len(winning_trades),
        'losing_trades': len(losing_trades),
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'trades': trades,
        'equity_curve': equity_curve
    }


def print_results(results):
    """打印回測結果"""
    print("\n" + "=" * 60)
    print("回測結果摘要")
    print("=" * 60)
    print(f"初始資金: ${results['initial_capital']:,.2f}")
    print(f"最終資金: ${results['final_equity']:,.2f}")
    print(f"總回報: ${results['total_return']:,.2f} ({results['total_return_pct']:.2f}%)")
    print(f"交易次數: {results['total_trades']}")
    print(f"勝率: {results['win_rate']:.2f}% ({results['winning_trades']}勝/{results['losing_trades']}負)")
    print(f"最大回撤: {results['max_drawdown']:.2f}%")
    
    if results['trades']:
        print("\n交易明細:")
        for trade in results['trades'][:10]:  # 顯示前10筆
            pnl_str = f"${trade.get('pnl', 0):.2f}" if trade.get('pnl') else "-"
            print(f"  {trade['date'].strftime('%Y-%m-%d')} | {trade['action']} | ${trade['price']:.2f} | PnL: {pnl_str}")
        
        if len(results['trades']) > 10:
            print(f"  ... 還有 {len(results['trades']) - 10} 筆交易")


def main():
    """主函數"""
    try:
        # 獲取數據
        df = fetch_tqqq_data_2025()
        
        # 執行回測
        results = backtest_zscore_strategy(df, initial_capital=100000)
        
        # 打印結果
        print_results(results)
        
        print("\n✅ Z-Score 策略測試完成！")
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
