"""
風險管理器 V9.4 - 最終優化版
基於 V9 Asymmetric，優化執行層降低回撤

核心改進:
1. 倉位上限: 90% (vs V9 原版 95%)
2. 盈利保護: +10%減倉50%, +20%再減30%
3. 不對稱參數: 多單穩健(-3%/-3%/+15%/7天), 空單敏捷(-2%/-2%/+10%/3天)
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "trading_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "PostgresqL")
}

# V9.4 風險參數
RISK_LIMITS = {
    # 倉位管理
    "max_position_percent": 90.0,  # 90% 倉位上限
    
    # 盈利減倉
    "profit_level_1": 10.0,        # +10%
    "reduce_1": 50.0,              # 減倉 50%
    "profit_level_2": 20.0,        # +20%
    "reduce_2": 30.0,              # 再減 30%
    
    # 多單止損 (穩健)
    "long_stop_loss": 3.0,         # -3%
    "long_trailing": 3.0,          # 回落 -3%
    "long_take_profit": 15.0,      # +15%
    "long_reeval": 7,              # 7天重估
    
    # 空單止損 (敏捷)
    "short_stop_loss": 2.0,        # +2%
    "short_trailing": 2.0,         # 反彈 +2%
    "short_take_profit": 10.0,     # +10%
    "short_reeval": 3,             # 3天重估
    
    # 其他限制
    "max_daily_loss_percent": 2.0,
    "max_total_risk_percent": 4.0,
    "max_positions": 3
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


class RiskManagerV9_4:
    """風險管理器 V9.4 - 最終優化版"""
    
    def __init__(self, account_balance: float):
        self.account_balance = account_balance
        self.risk_limits = RISK_LIMITS
    
    def calculate_position_size(self, available_capital: float) -> int:
        """計算倉位大小 - V9.4: 90% 上限"""
        max_position_value = available_capital * (self.risk_limits["max_position_percent"] / 100)
        return max_position_value
    
    def check_profit_taking(self, entry_price: float, current_price: float, 
                           profit_1_done: bool, profit_2_done: bool) -> Dict[str, Any]:
        """檢查盈利減倉條件"""
        etf_change = (current_price - entry_price) / entry_price * 100
        
        # 盈利減倉 2: +20% 再減 30%
        if etf_change >= self.risk_limits["profit_level_2"] and not profit_2_done:
            return {
                "action": "REDUCE_2",
                "reduce_percent": self.risk_limits["reduce_2"],
                "reason": f"+{etf_change:.1f}% >= +{self.risk_limits['profit_level_2']:.0f}%, 再減{self.risk_limits['reduce_2']:.0f}%"
            }
        
        # 盈利減倉 1: +10% 減倉 50%
        if etf_change >= self.risk_limits["profit_level_1"] and not profit_1_done:
            return {
                "action": "REDUCE_1",
                "reduce_percent": self.risk_limits["reduce_1"],
                "reason": f"+{etf_change:.1f}% >= +{self.risk_limits['profit_level_1']:.0f}%, 減倉{self.risk_limits['reduce_1']:.0f}%"
            }
        
        return {"action": "HOLD", "reduce_percent": 0, "reason": None}
    
    def check_stop_loss(self, entry_qqq_price: float, current_qqq_price: float,
                       extreme_qqq_price: float, is_long: bool) -> Dict[str, Any]:
        """檢查止損條件 - V9.4 不對稱"""
        qqq_change = (current_qqq_price - entry_qqq_price) / entry_qqq_price * 100
        
        if is_long:  # 多單 (穩健)
            # 日間止損: -3%
            if qqq_change <= -self.risk_limits["long_stop_loss"]:
                return {
                    "action": "STOP_LOSS",
                    "reason": f"多單止損: QQQ {qqq_change:.1f}% <= -{self.risk_limits['long_stop_loss']:.0f}%"
                }
            
            # 回落止損: -3%
            if extreme_qqq_price > 0:
                trailing_change = (current_qqq_price - extreme_qqq_price) / extreme_qqq_price * 100
                if trailing_change <= -self.risk_limits["long_trailing"]:
                    return {
                        "action": "TRAILING_STOP",
                        "reason": f"多單回落: {trailing_change:.1f}% <= -{self.risk_limits['long_trailing']:.0f}%"
                    }
        
        else:  # 空單 (敏捷)
            # 日間止損: +2% (更嚴格)
            if qqq_change >= self.risk_limits["short_stop_loss"]:
                return {
                    "action": "STOP_LOSS",
                    "reason": f"空單止損: QQQ +{qqq_change:.1f}% >= +{self.risk_limits['short_stop_loss']:.0f}%"
                }
            
            # 反彈止損: +2% (更嚴格)
            if extreme_qqq_price > 0:
                trailing_change = (current_qqq_price - extreme_qqq_price) / extreme_qqq_price * 100
                if trailing_change >= self.risk_limits["short_trailing"]:
                    return {
                        "action": "TRAILING_STOP",
                        "reason": f"空單反彈: +{trailing_change:.1f}% >= +{self.risk_limits['short_trailing']:.0f}%"
                    }
        
        return {"action": "HOLD", "reason": None}
    
    def check_take_profit(self, entry_price: float, current_price: float, is_long: bool) -> Dict[str, Any]:
        """檢查止盈條件 - V9.4 不對稱"""
        if is_long:
            etf_change = (current_price - entry_price) / entry_price * 100
            if etf_change >= self.risk_limits["long_take_profit"]:
                return {
                    "action": "TAKE_PROFIT",
                    "reason": f"多單止盈: +{etf_change:.1f}% >= +{self.risk_limits['long_take_profit']:.0f}%"
                }
        else:
            etf_change = (entry_price - current_price) / entry_price * 100
            if etf_change >= self.risk_limits["short_take_profit"]:
                return {
                    "action": "TAKE_PROFIT",
                    "reason": f"空單止盈: +{etf_change:.1f}% >= +{self.risk_limits['short_take_profit']:.0f}%"
                }
        
        return {"action": "HOLD", "reason": None}
    
    def check_reeval(self, holding_days: int, final_score: float, is_long: bool) -> Dict[str, Any]:
        """檢查重估條件 - V9.4 不對稱"""
        if is_long:
            if holding_days >= self.risk_limits["long_reeval"]:
                if final_score > 60:  # 續持
                    return {"action": "CONTINUE", "reason": "牛市續持多單"}
                else:  # 賣出
                    return {"action": "REEVAL_SELL", "reason": "多單7天重估賣出"}
        else:
            if holding_days >= self.risk_limits["short_reeval"]:
                if final_score < 40:  # 續持
                    return {"action": "CONTINUE", "reason": "熊市續持空單"}
                else:  # 賣出
                    return {"action": "REEVAL_SELL", "reason": "空單3天重估賣出"}
        
        return {"action": "HOLD", "reason": None}
    
    def get_daily_pnl(self) -> float:
        """獲取當日盈虧"""
        today = datetime.utcnow().date()
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COALESCE(SUM(pnl), 0) as daily_pnl
                    FROM trades
                    WHERE DATE(timestamp) = %s
                """, (today,))
                result = cur.fetchone()
                return float(result["daily_pnl"]) if result else 0
    
    def check_daily_loss(self) -> Dict[str, Any]:
        """檢查日虧損限制"""
        daily_pnl = self.get_daily_pnl()
        daily_loss_percent = abs(daily_pnl) / self.account_balance * 100
        
        if daily_pnl < 0 and daily_loss_percent > self.risk_limits["max_daily_loss_percent"]:
            return {
                "passed": False,
                "reason": f"日虧損 {daily_loss_percent:.2f}% 超過限制 {self.risk_limits['max_daily_loss_percent']}%",
                "daily_pnl": daily_pnl
            }
        
        return {"passed": True, "reason": None, "daily_pnl": daily_pnl}
    
    def check_max_positions(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """檢查最大持倉數"""
        if len(positions) >= self.risk_limits["max_positions"]:
            return {
                "passed": False,
                "reason": f"持倉數 {len(positions)} 超過限制 {self.risk_limits['max_positions']}"
            }
        return {"passed": True, "reason": None}
    
    def check_error_pause(self) -> Dict[str, Any]:
        """檢查錯誤暫停"""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) as error_count
                    FROM decisions
                    WHERE error_flag = TRUE
                    AND timestamp > NOW() - INTERVAL '1 day'
                """)
                result = cur.fetchone()
                error_count = result["error_count"] if result else 0
                
                if error_count > 0:
                    return {
                        "passed": False,
                        "reason": f"錯誤暫停: 過去24小時有 {error_count} 個錯誤"
                    }
        
        return {"passed": True, "reason": None}
    
    def check_all(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """執行所有風險檢查"""
        checks = [
            self.check_error_pause(),
            self.check_daily_loss(),
            self.check_max_positions(positions)
        ]
        
        failed_checks = [c for c in checks if not c["passed"]]
        if failed_checks:
            return {
                "passed": False,
                "reason": failed_checks[0]["reason"],
                "check_details": checks
            }
        
        return {
            "passed": True,
            "reason": None,
            "check_details": checks
        }
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """獲取風險摘要"""
        return {
            "version": "V9.4_Final",
            "max_position": f"{self.risk_limits['max_position_percent']:.0f}%",
            "profit_taking": f"+{self.risk_limits['profit_level_1']:.0f}%減{self.risk_limits['reduce_1']:.0f}%, +{self.risk_limits['profit_level_2']:.0f}%再減{self.risk_limits['reduce_2']:.0f}%",
            "long_params": f"-{self.risk_limits['long_stop_loss']:.0f}%/-{self.risk_limits['long_trailing']:.0f}%/+{self.risk_limits['long_take_profit']:.0f}%/{self.risk_limits['long_reeval']}天",
            "short_params": f"+{self.risk_limits['short_stop_loss']:.0f}%/+{self.risk_limits['short_trailing']:.0f}%/+{self.risk_limits['short_take_profit']:.0f}%/{self.risk_limits['short_reeval']}天"
        }


if __name__ == '__main__':
    # 測試
    rm = RiskManagerV9_4(100000)
    print("V9.4 風險管理器")
    print(rm.get_risk_summary())
