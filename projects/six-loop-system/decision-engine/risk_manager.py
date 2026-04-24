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

RISK_LIMITS = {
    "max_single_risk_percent": 1.0,
    "max_daily_loss_percent": 2.0,
    "max_total_risk_percent": 4.0,
    "max_positions": 3
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


class RiskManager:
    def __init__(self, account_balance: float):
        self.account_balance = account_balance

    def calculate_position_risk(self, entry_price: float, stop_loss_price: float) -> float:
        if stop_loss_price == 0 or entry_price == 0:
            return 0
        risk_percent = abs(entry_price - stop_loss_price) / entry_price * 100
        return risk_percent

    def calculate_total_position_risk(self, positions: List[Dict[str, Any]]) -> float:
        total_risk = 0
        for pos in positions:
            entry = pos.get("entry_price", 0)
            stop = pos.get("stop_loss_price", 0)
            size = pos.get("size", 0)
            if entry > 0 and stop > 0:
                risk = self.calculate_position_risk(entry, stop) * (size / entry)
                total_risk += risk
        return total_risk

    def get_daily_pnl(self) -> float:
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

    def check_single_position_risk(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        for pos in positions:
            entry = pos.get("entry_price", 0)
            stop = pos.get("stop_loss_price", 0)
            if entry > 0 and stop > 0:
                risk = self.calculate_position_risk(entry, stop)
                if risk > RISK_LIMITS["max_single_risk_percent"]:
                    return {
                        "passed": False,
                        "reason": f"Single position risk {risk:.2f}% exceeds limit {RISK_LIMITS['max_single_risk_percent']}%"
                    }
        return {"passed": True, "reason": None}

    def check_daily_loss(self) -> Dict[str, Any]:
        daily_pnl = self.get_daily_pnl()
        daily_loss_percent = abs(daily_pnl) / self.account_balance * 100
        if daily_pnl < 0 and daily_loss_percent > RISK_LIMITS["max_daily_loss_percent"]:
            return {
                "passed": False,
                "reason": f"Daily loss {daily_loss_percent:.2f}% exceeds limit {RISK_LIMITS['max_daily_loss_percent']}%",
                "daily_pnl": daily_pnl
            }
        return {"passed": True, "reason": None, "daily_pnl": daily_pnl}

    def check_total_risk(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_risk = self.calculate_total_position_risk(positions)
        if total_risk > RISK_LIMITS["max_total_risk_percent"]:
            return {
                "passed": False,
                "reason": f"Total position risk {total_risk:.2f}% exceeds limit {RISK_LIMITS['max_total_risk_percent']}%",
                "total_risk": total_risk
            }
        return {"passed": True, "reason": None, "total_risk": total_risk}

    def check_max_positions(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(positions) >= RISK_LIMITS["max_positions"]:
            return {
                "passed": False,
                "reason": f"Position count {len(positions)} exceeds limit {RISK_LIMITS['max_positions']}"
            }
        return {"passed": True, "reason": None}

    def check_error_pause(self) -> Dict[str, Any]:
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
                        "reason": f"Error pause active: {error_count} errors in last 24 hours"
                    }
        return {"passed": True, "reason": None}

    def check_all(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        checks = [
            self.check_error_pause(),
            self.check_single_position_risk(positions),
            self.check_daily_loss(),
            self.check_total_risk(positions),
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

    def calculate_position_size(self, current_positions: List[Dict[str, Any]], 
                             account_balance: float) -> float:
        current_risk = self.calculate_total_position_risk(current_positions)
        available_risk = RISK_LIMITS["max_total_risk_percent"] - current_risk
        if available_risk <= 0:
            return 0
        available_capital = account_balance * (available_risk / 100)
        position_size = available_capital / (1 / RISK_LIMITS["max_single_risk_percent"])
        return min(position_size, account_balance * 0.33)


def emergency_pause() -> Dict[str, Any]:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO decisions 
                (absolute_score, reference_score, final_score, signal, risk_check_passed, error_flag, error_message)
                VALUES (0, 0, 0, 'HOLD', FALSE, TRUE, 'Emergency pause triggered')
                RETURNING id
            """)
            decision_id = cur.fetchone()["id"]
            conn.commit()
            return {
                "success": True,
                "decision_id": decision_id,
                "message": "Emergency pause activated"
            }


if __name__ == "__main__":
    rm = RiskManager(100000)
    result = rm.check_all([
        {"entry_price": 45.00, "stop_loss_price": 43.50, "size": 1000}
    ])
    print(result)