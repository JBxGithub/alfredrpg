"""
六循環系統回測引擎 - V3 優化版
基於靚仔建議:
1. 用 QQQ 變化計算止損 (2% QQQ = ~6% TQQQ)
2. 強制 7 天周期重新評估
3. 保持 10% 止盈不變
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import json
import os

class SixLoopBacktestV3:
    """六循環回測 V3 - 靚仔優化版"""
    
    def __init__(self, start_date='2019-01-01', end_date='2024-12-31', initial_capital=100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = 0
        self.entry_price = 0
        self.entry_qqq_price = 0  # 記錄入場時 QQQ 價格
        self.entry_date = None
        self.holding_days = 0
        self.trades = []
        
        # 優化後參數
        self.qqq_stop_loss = 0.02      # QQQ 跌 2% 即止損 (TQQQ ~6%)
        self.take_profit_pct = 0.10    # 保持 10% 止盈
        self.max_holding_days = 7      # 強制 7 天重新評估
        self.max_position_pct = 0.95
        
    def fetch_data(self):
        """獲取歷史數據"""
        print(f"獲取數據: {self.start_date} 至 {self.end_date}")
        
        qqq = yf.Ticker("QQQ")
        self.qqq_data = qqq.history(start=self.start_date, end=self.end_date)
        
        tqqq = yf.Ticker("TQQQ")
        self.tqqq_data = tqqq.history(start=self.start_date, end=self.end_date)
        
        print(f"QQQ數據: {len(self.qqq_data)} 天")
        print(f"TQQQ數據: {len(self.tqqq_data)} 天")
        
        return self.qqq_data, self.tqqq_data
    
    def calculate_indicators(self, data, idx):
        """計算技術指標"""
        if idx < 50:
            return None
        
        window = data.iloc[max(0, idx-200):idx+1]
        current_price = data['Close'].iloc[idx]
        
        # 移動平均線
        ma20 = window['Close'].iloc[-20:].mean()
        ma50 = window['Close'].iloc[-50:].mean()
        ma200 = window['Close'].mean() if len(window) >= 200 else ma50
        
        # RSI
        delta = window['Close'].diff()
        gain = (delta.where(delta > 0, 0)).iloc[-14:].mean()
        loss = (-delta.where(delta < 0, 0)).iloc[-14:].mean()
        rs = gain / loss if loss != 0 else 1
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        ema12 = window['Close'].ewm(span=12).mean().iloc[-1]
        ema26 = window['Close'].ewm(span=26).mean().iloc[-1]
        macd = ema12 - ema26
        
        # 波動率
        high_low = window['High'] - window['Low']
        atr = high_low.iloc[-14:].mean()
        
        # 價格動量
        momentum_20 = (current_price - window['Close'].iloc[-20]) / window['Close'].iloc[-20]
        
        return {
            'price': current_price,
            'ma20': ma20,
            'ma50': ma50,
            'ma200': ma200,
            'rsi': rsi,
            'macd': macd,
            'atr': atr,
            'momentum_20': momentum_20
        }
    
    def calculate_absolute_score(self, indicators):
        """計算Absolute評分"""
        if not indicators:
            return 50
        
        scores = []
        
        # 價格 vs MA20
        scores.append(70 if indicators['price'] > indicators['ma20'] else 30)
        
        # 價格 vs MA50
        scores.append(80 if indicators['price'] > indicators['ma50'] else 20)
        
        # 價格 vs MA200
        scores.append(90 if indicators['price'] > indicators['ma200'] else 10)
        
        # 動量
        if indicators['momentum_20'] > 0.05:
            scores.append(80)
        elif indicators['momentum_20'] > 0:
            scores.append(60)
        else:
            scores.append(40)
        
        # MACD
        scores.append(70 if indicators['macd'] > 0 else 30)
        
        return np.mean(scores)
    
    def calculate_reference_score(self, indicators):
        """計算Reference評分"""
        if not indicators:
            return 50
        
        scores = []
        
        # RSI
        rsi = indicators['rsi']
        if rsi < 30:
            scores.append(80)
        elif rsi > 70:
            scores.append(20)
        else:
            scores.append(50)
        
        # 波動率
        atr_pct = indicators['atr'] / indicators['price']
        if atr_pct < 0.02:
            scores.append(70)
        elif atr_pct > 0.05:
            scores.append(30)
        else:
            scores.append(50)
        
        # 其他指標
        scores.extend([70, 60, 50, 55])
        
        return np.mean(scores)
    
    def generate_signal(self, abs_score, ref_score, current_position, holding_days):
        """生成交易信號 - 加入 7 天周期"""
        final_score = abs_score * 0.6 + ref_score * 0.4
        
        # 有倉位時
        if current_position > 0:
            # 強制 7 天重新評估
            if holding_days >= self.max_holding_days:
                # 重新評估：如果評分仍然高，繼續持有
                if final_score > 50:
                    return 'HOLD_REEVALUATE', final_score
                else:
                    return 'SELL_REEVALUATE', final_score
            
            # 正常賣出條件
            if final_score < 40:
                return 'SELL', final_score
            else:
                return 'HOLD', final_score
        else:
            # 無倉位時
            if final_score > 60:
                return 'BUY', final_score
            else:
                return 'HOLD', final_score
    
    def run_backtest(self):
        """運行回測"""
        print("\n" + "="*60)
        print("六循環系統回測 - V3 (靚仔優化版)")
        print("="*60)
        print(f"止損: QQQ -2% (TQQQ ~-6%)")
        print(f"止盈: TQQQ +10%")
        print(f"最長持倉: 7 天")
        
        self.fetch_data()
        
        # 對齊數據
        common_dates = self.qqq_data.index.intersection(self.tqqq_data.index)
        qqq_aligned = self.qqq_data.loc[common_dates]
        tqqq_aligned = self.tqqq_data.loc[common_dates]
        
        print(f"\n回測期間: {common_dates[0]} 至 {common_dates[-1]}")
        print(f"總交易日: {len(common_dates)}")
        
        daily_results = []
        
        for i in range(len(common_dates)):
            date = common_dates[i]
            qqq_price = qqq_aligned['Close'].iloc[i]
            tqqq_price = tqqq_aligned['Close'].iloc[i]
            
            # 計算指標
            indicators = self.calculate_indicators(qqq_aligned, i)
            
            if indicators:
                abs_score = self.calculate_absolute_score(indicators)
                ref_score = self.calculate_reference_score(indicators)
                signal, final_score = self.generate_signal(
                    abs_score, ref_score, self.positions, self.holding_days
                )
            else:
                abs_score = ref_score = final_score = 50
                signal = 'HOLD'
            
            # ===== 核心改進：用 QQQ 變化計算止損 =====
            if self.positions > 0:
                # 計算 QQQ 從入場以來的變化
                qqq_change_pct = (qqq_price - self.entry_qqq_price) / self.entry_qqq_price
                
                # 止損：QQQ 跌 2% (TQQQ 理論上跌 ~6%)
                if qqq_change_pct <= -self.qqq_stop_loss:
                    signal = 'SELL_QQQ_STOP'
                
                # 止盈：TQQQ 漲 10%
                tqqq_pnl_pct = (tqqq_price - self.entry_price) / self.entry_price
                if tqqq_pnl_pct >= self.take_profit_pct:
                    signal = 'SELL_PROFIT'
                
                # 增加持倉天數
                self.holding_days += 1
            
            # 執行交易
            if signal in ['BUY'] and self.positions == 0:
                shares = int(self.capital * self.max_position_pct / tqqq_price)
                if shares > 0:
                    self.positions = shares
                    self.entry_price = tqqq_price
                    self.entry_qqq_price = qqq_price  # 記錄 QQQ 入場價
                    self.entry_date = date
                    self.holding_days = 0
                    
                    self.trades.append({
                        'date': date,
                        'action': 'BUY',
                        'tqqq_price': tqqq_price,
                        'qqq_price': qqq_price,
                        'shares': shares,
                        'abs_score': abs_score,
                        'ref_score': ref_score,
                        'final_score': final_score
                    })
                    
            elif 'SELL' in signal and self.positions > 0:
                pnl = (tqqq_price - self.entry_price) * self.positions
                self.capital += pnl
                
                qqq_change = (qqq_price - self.entry_qqq_price) / self.entry_qqq_price
                tqqq_change = (tqqq_price - self.entry_price) / self.entry_price
                
                self.trades.append({
                    'date': date,
                    'action': signal,
                    'tqqq_price': tqqq_price,
                    'qqq_price': qqq_price,
                    'shares': self.positions,
                    'pnl': pnl,
                    'qqq_change_pct': qqq_change,
                    'tqqq_change_pct': tqqq_change,
                    'holding_days': self.holding_days,
                    'abs_score': abs_score,
                    'ref_score': ref_score,
                    'final_score': final_score
                })
                
                self.positions = 0
                self.entry_price = 0
                self.entry_qqq_price = 0
                self.holding_days = 0
            
            # 計算持倉價值
            position_value = self.positions * tqqq_price if self.positions > 0 else 0
            portfolio_value = self.capital + position_value
            
            daily_results.append({
                'date': date,
                'qqq_price': qqq_price,
                'tqqq_price': tqqq_price,
                'absolute_score': abs_score,
                'reference_score': ref_score,
                'final_score': final_score,
                'signal': signal,
                'capital': self.capital,
                'positions': self.positions,
                'position_value': position_value,
                'portfolio_value': portfolio_value,
                'holding_days': self.holding_days if self.positions > 0 else 0
            })
        
        self.daily_results = pd.DataFrame(daily_results)
        return self.daily_results
    
    def calculate_metrics(self):
        """計算回測指標"""
        print("\n" + "="*60)
        print("回測結果 - V3 (靚仔優化版)")
        print("="*60)
        
        # 基本指標
        final_value = self.daily_results['portfolio_value'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # 年化收益
        years = (self.daily_results['date'].iloc[-1] - self.daily_results['date'].iloc[0]).days / 365.25
        annualized_return = ((final_value / self.initial_capital) ** (1/years) - 1) * 100
        
        # 最大回撤
        self.daily_results['cummax'] = self.daily_results['portfolio_value'].cummax()
        self.daily_results['drawdown'] = (self.daily_results['portfolio_value'] - self.daily_results['cummax']) / self.daily_results['cummax']
        max_drawdown = self.daily_results['drawdown'].min() * 100
        
        # 波動率
        daily_returns = self.daily_results['portfolio_value'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        
        # 夏普比率
        sharpe_ratio = (daily_returns.mean() * 252 - 0.02) / (daily_returns.std() * np.sqrt(252))
        
        # 交易統計
        buy_trades = [t for t in self.trades if t['action'] == 'BUY']
        sell_trades = [t for t in self.trades if 'SELL' in t['action']]
        winning_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('pnl', 0) <= 0]
        
        win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0
        
        avg_win = np.mean([t['tqqq_change_pct'] for t in winning_trades]) * 100 if winning_trades else 0
        avg_loss = np.mean([t['tqqq_change_pct'] for t in losing_trades]) * 100 if losing_trades else 0
        
        # 平均持倉時間
        avg_holding_days = np.mean([t.get('holding_days', 0) for t in sell_trades]) if sell_trades else 0
        
        # 輸出結果
        print(f"\n【基本指標】")
        print(f"初始資金: ${self.initial_capital:,.2f}")
        print(f"最終價值: ${final_value:,.2f}")
        print(f"總回報: {total_return:.2f}%")
        print(f"年化回報: {annualized_return:.2f}%")
        print(f"年化波動率: {volatility:.2f}%")
        print(f"最大回撤: {max_drawdown:.2f}%")
        
        print(f"\n【風險調整收益】")
        print(f"夏普比率: {sharpe_ratio:.2f}")
        
        print(f"\n【交易統計】")
        print(f"總交易次數: {len(sell_trades)}")
        print(f"勝率: {win_rate:.1f}%")
        print(f"盈利交易: {len(winning_trades)}")
        print(f"虧損交易: {len(losing_trades)}")
        print(f"平均盈利: {avg_win:.2f}%")
        print(f"平均虧損: {avg_loss:.2f}%")
        print(f"平均持倉時間: {avg_holding_days:.1f} 天")
        
        # 止損類型分析
        qqq_stops = [t for t in sell_trades if 'QQQ_STOP' in t['action']]
        profit_stops = [t for t in sell_trades if 'PROFIT' in t['action']]
        reeval_stops = [t for t in sell_trades if 'REEVALUATE' in t['action']]
        
        print(f"\n【賣出類型分析】")
        print(f"QQQ止損 (2%): {len(qqq_stops)} 次")
        print(f"止盈 (10%): {len(profit_stops)} 次")
        print(f"7天重估: {len(reeval_stops)} 次")
        
        # 對比買入持有
        buy_hold_shares = self.initial_capital / self.tqqq_data['Close'].iloc[0]
        buy_hold_value = buy_hold_shares * self.tqqq_data['Close'].iloc[-1]
        buy_hold_return = (buy_hold_value - self.initial_capital) / self.initial_capital * 100
        
        print(f"\n【策略對比】")
        print(f"策略回報: {total_return:.2f}%")
        print(f"買入持有回報: {buy_hold_return:.2f}%")
        print(f"超額收益: {total_return - buy_hold_return:.2f}%")
        
        # 保存指標
        self.metrics = {
            'version': 'V3_靚仔優化版',
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return_pct': total_return,
            'annualized_return_pct': annualized_return,
            'volatility_pct': volatility,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': len(sell_trades),
            'win_rate': win_rate,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'avg_holding_days': avg_holding_days,
            'qqq_stops': len(qqq_stops),
            'profit_stops': len(profit_stops),
            'reeval_stops': len(reeval_stops),
            'buy_hold_return_pct': buy_hold_return,
            'outperformance': total_return - buy_hold_return
        }
        
        return self.metrics
    
    def save_results(self):
        """保存回測結果"""
        os.makedirs('backtest/results', exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.daily_results.to_csv(f'backtest/results/v3_daily_{timestamp}.csv', index=False)
        
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_df.to_csv(f'backtest/results/v3_trades_{timestamp}.csv', index=False)
        
        with open(f'backtest/results/v3_metrics_{timestamp}.json', 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)
        
        print(f"\n結果已保存: backtest/results/v3_*_{timestamp}.*")

def main():
    backtest = SixLoopBacktestV3(
        start_date='2019-01-01',
        end_date='2024-12-31',
        initial_capital=100000
    )
    
    backtest.run_backtest()
    backtest.calculate_metrics()
    backtest.save_results()
    
    print("\n✅ V3 回測完成！")

if __name__ == '__main__':
    main()
