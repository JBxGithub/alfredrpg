"""
Z-Score 策略回測 - 3年，閾值 1.65
回測期間: 2023-01-01 至 2026-01-01
策略: Z-Score Mean Reversion，閾值 upper=1.65, lower=-1.65
初始資金: $100,000
倉位: 50%（基於當前權益動態計算）
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import os
import sys

# 添加項目路徑
sys.path.insert(0, 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot')

import importlib.util
spec = importlib.util.spec_from_file_location("zscore_strategy", "C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot/src/backtest/zscore_backtest_2025_threshold_1.65.py")
zscore_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zscore_module)
ZScoreBacktestStrategy = zscore_module.ZScoreBacktestStrategy


def main():
    """主函數 - 3年回測"""
    print("="*70)
    print("Z-Score 策略回測 - 3年，閾值 1.65（修正版：動態權益倉位）")
    print("="*70)

    # 回測期間: 2023-2026年
    start_date = '2023-01-01'
    end_date = '2026-01-01'

    # 策略參數
    config = {
        'entry_zscore_upper': 1.65,      # 做空閾值
        'entry_zscore_lower': -1.65,     # 做多閾值
        'exit_zscore': 0.5,
        'position_pct': 0.50,           # 50%倉位（基於當前權益）
        'take_profit_pct': 0.05,        # 止盈5%
        'stop_loss_pct': 0.03,          # 止損3%
        'time_stop_days': 7,            # 時間止損7天
        'rsi_overbought': 70.0,         # RSI超買70
        'rsi_oversold': 30.0,           # RSI超賣30
        'initial_capital': 100000.0
    }

    # 創建回測引擎
    backtest = ZScoreBacktestStrategy(**config)

    # 獲取數據
    df = backtest.fetch_data(start_date, end_date)

    # 執行回測
    report = backtest.run_backtest(df, start_date, end_date)

    # 打印結果
    print("\n" + "="*70)
    print("3年回測結果摘要（修正版）")
    print("="*70)
    print(f"回測期間: {report['backtest_period']['start']} 至 {report['backtest_period']['end']}")
    print(f"策略名稱: {report['strategy_name']}")
    print(f"Z-Score閾值: upper={report['strategy_config']['entry_zscore_upper']}, lower={report['strategy_config']['entry_zscore_lower']}")
    print(f"RSI閾值: 超買={report['strategy_config']['rsi_overbought']}, 超賣={report['strategy_config']['rsi_oversold']}")
    print(f"時間止損: {report['strategy_config']['time_stop_days']}天")
    print(f"倉位計算: 基於當前權益的 {report['strategy_config']['position_pct']*100}%")
    print(f"初始資金: ${report['initial_capital']:,.2f}")
    print(f"最終資金: ${report['final_capital']:,.2f}")
    print(f"總回報: ${report['total_return']:,.2f} ({report['total_return_pct']:.2f}%)")
    print(f"交易次數: {report['total_trades']}")
    print(f"勝率: {report['win_rate']:.2f}% ({report['winning_trades']}勝/{report['losing_trades']}負)")
    print(f"做多交易: {report['long_trades']}次 (勝率: {report['long_win_rate']:.2f}%)")
    print(f"做空交易: {report['short_trades']}次 (勝率: {report['short_win_rate']:.2f}%)")
    print(f"平均盈利: ${report['avg_profit']:.2f}")
    print(f"平均虧損: ${report['avg_loss']:.2f}")
    print(f"盈虧比: {report['profit_factor']:.2f}")
    print(f"最大回撤: {report['max_drawdown_pct']:.2f}%")
    print(f"夏普比率: {report['sharpe_ratio']:.2f}")
    print("="*70)

    # 保存報告
    output_dir = 'C:/Users/BurtClaw/openclaw_workspace/projects/fututradingbot/reports'
    os.makedirs(output_dir, exist_ok=True)

    output_file = f"{output_dir}/zscore_backtest_3year_threshold_1.65_fixed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n報告已保存: {output_file}")

    return report


if __name__ == '__main__':
    main()
