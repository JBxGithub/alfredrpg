"""
FutuTradingBot 專業級風險管理模組
嚴格遵守: 單筆1%, 每日2%, 連續虧損2筆停手, VIX調整
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from datetime import datetime, date


class RiskManager:
    """風險管理器"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # 風險參數
        self.max_risk_per_trade = 0.01  # 單筆最大風險 1%
        self.max_daily_loss = 0.02      # 每日最大虧損 2%
        self.max_consecutive_losses = 2  # 連續虧損2筆停手
        self.max_open_positions = 3     # 最大同時持倉
        self.max_total_risk = 0.04      # 總風險上限 4%
        
        # VIX 調整
        self.vix_threshold_high = 25    # VIX > 25 風險減半
        self.vix_threshold_extreme = 30  # VIX > 30 全部平倉
        
        # 狀態追蹤
        self.daily_pnl = 0
        self.current_date = None
        self.consecutive_losses = 0
        self.open_positions = []
        self.daily_loss_reached = False
        self.trading_halted = False
        self.halt_reason = None
        self.halt_until = None
    
    def reset_daily(self, current_date: date):
        """重置每日狀態"""
        if self.current_date != current_date:
            self.daily_pnl = 0
            self.current_date = current_date
            self.daily_loss_realted = False
            
            # 檢查是否解除停市
            if self.trading_halted and self.halt_until:
                if current_date >= self.halt_until:
                    self.trading_halted = False
                    self.halt_reason = None
                    self.halt_until = None
                    self.consecutive_losses = 0
                    print(f"[{current_date}] 交易恢復")
    
    def check_vix_adjustment(self, vix: float) -> Dict:
        """
        檢查 VIX 調整
        
        Returns:
            dict with adjustment factors
        """
        if vix > self.vix_threshold_extreme:
            return {
                'halt_trading': True,
                'position_size_factor': 0,
                'risk_factor': 0,
                'reason': f'VIX極端高 ({vix:.1f} > 30)，全部平倉停市'
            }
        elif vix > self.vix_threshold_high:
            return {
                'halt_trading': False,
                'position_size_factor': 0.5,
                'risk_factor': 0.5,
                'reason': f'VIX高 ({vix:.1f} > 25)，風險減半'
            }
        else:
            return {
                'halt_trading': False,
                'position_size_factor': 1.0,
                'risk_factor': 1.0,
                'reason': 'VIX正常'
            }
    
    def can_trade(self, current_date: date, vix: float) -> Tuple[bool, str]:
        """
        檢查是否可以交易
        
        Returns:
            (can_trade, reason)
        """
        self.reset_daily(current_date)
        
        # 檢查停市狀態
        if self.trading_halted:
            return False, f'交易已停市: {self.halt_reason}'
        
        # 檢查 VIX
        vix_adj = self.check_vix_adjustment(vix)
        if vix_adj['halt_trading']:
            self.trading_halted = True
            self.halt_reason = vix_adj['reason']
            self.halt_until = current_date  # 當日停市
            return False, vix_adj['reason']
        
        # 檢查每日虧損限制
        if self.daily_pnl <= -self.current_capital * self.max_daily_loss:
            self.daily_loss_reached = True
            return False, f'每日虧損達限 ({self.daily_pnl:,.0f})'
        
        # 檢查連續虧損
        if self.consecutive_losses >= self.max_consecutive_losses:
            self.trading_halted = True
            self.halt_reason = f'連續虧損 {self.consecutive_losses} 筆'
            self.halt_until = current_date  # 當日停市
            return False, self.halt_reason
        
        # 檢查持倉數量
        if len(self.open_positions) >= self.max_open_positions:
            return False, f'持倉達上限 ({len(self.open_positions)}/{self.max_open_positions})'
        
        return True, '可以交易'
    
    def calculate_position_size(self, entry_price: float, stop_loss_price: float, 
                               vix: float = 20) -> Dict:
        """
        計算倉位大小
        
        公式: 倉位 = (帳戶資金 × 風險%) ÷ (入場價 - 止損價)
        
        Args:
            entry_price: 入場價格
            stop_loss_price: 止損價格
            vix: VIX 值
            
        Returns:
            dict with position details
        """
        # 檢查 VIX 調整
        vix_adj = self.check_vix_adjustment(vix)
        risk_pct = self.max_risk_per_trade * vix_adj['risk_factor']
        
        # 計算風險金額
        risk_amount = self.current_capital * risk_pct
        
        # 計算每單位風險
        price_risk = abs(entry_price - stop_loss_price)
        if price_risk == 0:
            return {'valid': False, 'reason': '止損價等於入場價'}
        
        # 計算倉位
        position_size = risk_amount / price_risk
        
        # 計算總投資金額
        total_investment = position_size * entry_price
        
        # 檢查總風險
        current_total_risk = sum(pos['risk_amount'] for pos in self.open_positions)
        if current_total_risk + risk_amount > self.current_capital * self.max_total_risk:
            return {
                'valid': False,
                'reason': f'總風險達上限 (當前: {current_total_risk:,.0f}, 新增: {risk_amount:,.0f})'
            }
        
        return {
            'valid': True,
            'position_size': int(position_size),
            'total_investment': total_investment,
            'risk_amount': risk_amount,
            'risk_pct': risk_pct * 100,
            'price_risk': price_risk,
            'vix_adjustment': vix_adj['reason']
        }
    
    def record_trade(self, trade_result: Dict):
        """
        記錄交易結果
        
        Args:
            trade_result: dict with 'pnl', 'date', etc.
        """
        pnl = trade_result.get('pnl', 0)
        self.daily_pnl += pnl
        self.current_capital += pnl
        
        # 更新連續虧損
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # 更新持倉
        if trade_result.get('action') == 'open':
            self.open_positions.append(trade_result)
        elif trade_result.get('action') == 'close':
            # 移除對應持倉
            self.open_positions = [p for p in self.open_positions 
                                  if p.get('id') != trade_result.get('position_id')]
    
    def get_risk_report(self) -> Dict:
        """
        獲取風險報告
        
        Returns:
            dict with risk metrics
        """
        current_total_risk = sum(pos['risk_amount'] for pos in self.open_positions)
        
        return {
            'current_capital': self.current_capital,
            'initial_capital': self.initial_capital,
            'total_return_pct': (self.current_capital - self.initial_capital) / self.initial_capital * 100,
            'daily_pnl': self.daily_pnl,
            'daily_loss_limit': -self.current_capital * self.max_daily_loss,
            'daily_loss_remaining': self.current_capital * self.max_daily_loss + self.daily_pnl,
            'consecutive_losses': self.consecutive_losses,
            'max_consecutive_losses': self.max_consecutive_losses,
            'open_positions_count': len(self.open_positions),
            'max_open_positions': self.max_open_positions,
            'current_total_risk': current_total_risk,
            'max_total_risk': self.current_capital * self.max_total_risk,
            'trading_halted': self.trading_halted,
            'halt_reason': self.halt_reason,
            'halt_until': self.halt_until
        }
    
    def calculate_stop_loss(self, entry_price: float, atr: float, 
                           direction: str, multiplier: float = 1.5) -> float:
        """
        計算 ATR 止損
        
        Args:
            entry_price: 入場價格
            atr: ATR 值
            direction: 'long' 或 'short'
            multiplier: ATR 倍數 (默認1.5-2)
            
        Returns:
            stop loss price
        """
        stop_distance = atr * multiplier
        
        if direction == 'long':
            return entry_price - stop_distance
        else:  # short
            return entry_price + stop_distance
    
    def calculate_take_profit(self, entry_price: float, stop_loss_price: float,
                             risk_reward_ratio: float = 2.0) -> float:
        """
        計算止盈 (風險報酬比 1:2)
        
        Args:
            entry_price: 入場價格
            stop_loss_price: 止損價格
            risk_reward_ratio: 風險報酬比 (默認2)
            
        Returns:
            take profit price
        """
        risk = abs(entry_price - stop_loss_price)
        reward = risk * risk_reward_ratio
        
        if entry_price > stop_loss_price:  # long
            return entry_price + reward
        else:  # short
            return entry_price - reward


class TrailingStopManager:
    """移動止損管理器"""
    
    def __init__(self, trailing_type: str = 'ema20'):
        self.trailing_type = trailing_type
        self.extreme_price = None
        self.current_stop = None
    
    def update_trailing_stop(self, current_price: float, ema20: float = None,
                            direction: str = 'long') -> Optional[float]:
        """
        更新移動止損
        
        Args:
            current_price: 當前價格
            ema20: 20 EMA (如使用EMA跟隨)
            direction: 'long' 或 'short'
            
        Returns:
            new stop loss price or None
        """
        if self.extreme_price is None:
            self.extreme_price = current_price
            return None
        
        # 更新極值
        if direction == 'long':
            if current_price > self.extreme_price:
                self.extreme_price = current_price
            
            # 使用 EMA20 或前低
            if self.trailing_type == 'ema20' and ema20:
                new_stop = ema20
            else:
                # 使用前一根K線低點 (簡化為當前價格回落一定百分比)
                new_stop = self.extreme_price * 0.97  # 回落3%
            
            if self.current_stop is None or new_stop > self.current_stop:
                self.current_stop = new_stop
                
        else:  # short
            if current_price < self.extreme_price:
                self.extreme_price = current_price
            
            if self.trailing_type == 'ema20' and ema20:
                new_stop = ema20
            else:
                new_stop = self.extreme_price * 1.03  # 反彈3%
            
            if self.current_stop is None or new_stop < self.current_stop:
                self.current_stop = new_stop
        
        return self.current_stop
    
    def check_exit(self, current_price: float, direction: str) -> bool:
        """
        檢查是否觸發移動止損
        
        Returns:
            True if should exit
        """
        if self.current_stop is None:
            return False
        
        if direction == 'long':
            return current_price <= self.current_stop
        else:
            return current_price >= self.current_stop


if __name__ == '__main__':
    print("RiskManager 模組已載入")
    print("核心規則:")
    print("- 單筆最大風險: 1%")
    print("- 每日最大虧損: 2%")
    print("- 連續虧損2筆: 當日停手")
    print("- VIX > 25: 風險減半")
    print("- VIX > 30: 全部平倉")
