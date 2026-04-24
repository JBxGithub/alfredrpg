import os
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "trading_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "PostgresqL")
}

WEIGHTS = {
    "absolute": 0.6,
    "reference": 0.4
}

SIGNAL_THRESHOLDS = {
    "buy": 70,
    "sell": 30
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def get_latest_absolute_score() -> Optional[Dict[str, Any]]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT nq200ma_score, nq50ma_score, nq20ema50ema_score,
                           mtf_score, market_phase_score, final_absolute_score,
                           trend_direction, timestamp
                    FROM absolute_scores
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                row = cur.fetchone()
                if not row:
                    logger.warning("No absolute scores found in database")
                    return None
                logger.info(f"Retrieved absolute score: {row['final_absolute_score']}")
                return dict(row)
    except psycopg2.Error as e:
        logger.error(f"Database error fetching absolute scores: {e}")
        return None


def get_latest_reference_score() -> Optional[Dict[str, Any]]:
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT components_breadth_score, components_risk_score,
                           technical_rsi_score, technical_atr_score,
                           technical_zscore_score, technical_macd_score,
                           technical_divergence_score, money_flow_futures_score,
                           money_flow_etf_score, final_reference_score, timestamp
                    FROM reference_scores
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                row = cur.fetchone()
                if not row:
                    logger.warning("No reference scores found in database")
                    return None
                logger.info(f"Retrieved reference score: {row['final_reference_score']}")
                return dict(row)
    except psycopg2.Error as e:
        logger.error(f"Database error fetching reference scores: {e}")
        return None


def calculate_absolute_score_components(absolute_data: Dict[str, Any]) -> float:
    ABSOLUTE_WEIGHTS = {
        "nq200ma": 0.30,
        "nq50ma": 0.30,
        "nq20ema50ema": 0.20,
        "mtf": 0.10,
        "market_phase": 0.10
    }
    score = (
        absolute_data.get("nq200ma_score", 0) * ABSOLUTE_WEIGHTS["nq200ma"] +
        absolute_data.get("nq50ma_score", 0) * ABSOLUTE_WEIGHTS["nq50ma"] +
        absolute_data.get("nq20ema50ema_score", 0) * ABSOLUTE_WEIGHTS["nq20ema50ema"] +
        absolute_data.get("mtf_score", 0) * ABSOLUTE_WEIGHTS["mtf"] +
        absolute_data.get("market_phase_score", 0) * ABSOLUTE_WEIGHTS["market_phase"]
    )
    return round(score, 2)


def calculate_reference_score_components(reference_data: Dict[str, Any]) -> float:
    REFERENCE_WEIGHTS = {
        "components_breadth": 0.20,
        "components_risk": 0.10,
        "technical_rsi": 0.15,
        "technical_atr": 0.10,
        "technical_zscore": 0.10,
        "technical_macd": 0.05,
        "technical_divergence": 0.05,
        "money_flow_futures": 0.15,
        "money_flow_etf": 0.10
    }
    score = (
        reference_data.get("components_breadth_score", 0) * REFERENCE_WEIGHTS["components_breadth"] +
        reference_data.get("components_risk_score", 0) * REFERENCE_WEIGHTS["components_risk"] +
        reference_data.get("technical_rsi_score", 0) * REFERENCE_WEIGHTS["technical_rsi"] +
        reference_data.get("technical_atr_score", 0) * REFERENCE_WEIGHTS["technical_atr"] +
        reference_data.get("technical_zscore_score", 0) * REFERENCE_WEIGHTS["technical_zscore"] +
        reference_data.get("technical_macd_score", 0) * REFERENCE_WEIGHTS["technical_macd"] +
        reference_data.get("technical_divergence_score", 0) * REFERENCE_WEIGHTS["technical_divergence"] +
        reference_data.get("money_flow_futures_score", 0) * REFERENCE_WEIGHTS["money_flow_futures"] +
        reference_data.get("money_flow_etf_score", 0) * REFERENCE_WEIGHTS["money_flow_etf"]
    )
    return round(score, 2)


def get_latest_scores() -> Optional[Dict[str, Any]]:
    absolute_data = get_latest_absolute_score()
    reference_data = get_latest_reference_score()

    if not absolute_data or not reference_data:
        logger.error("Missing score data - cannot calculate final score")
        return None

    recalculated_absolute = calculate_absolute_score_components(absolute_data)
    recalculated_reference = calculate_reference_score_components(reference_data)

    logger.info(f"Recalculated absolute: {recalculated_absolute}, reference: {recalculated_reference}")

    return {
        "absolute_score": absolute_data["final_absolute_score"],
        "absolute_components": absolute_data,
        "reference_score": reference_data["final_reference_score"],
        "reference_components": reference_data,
        "recalculated_absolute": recalculated_absolute,
        "recalculated_reference": recalculated_reference
    }


def calculate_final_score(absolute_score: int, reference_score: int) -> float:
    final = (absolute_score * WEIGHTS["absolute"]) + (reference_score * WEIGHTS["reference"])
    logger.info(f"Final score: {final} = {absolute_score}*0.6 + {reference_score}*0.4")
    return round(final, 2)


def generate_signal(final_score: float) -> str:
    if final_score >= SIGNAL_THRESHOLDS["buy"]:
        return "BUY"
    elif final_score <= SIGNAL_THRESHOLDS["sell"]:
        return "SELL"
    return "HOLD"


def save_decision(absolute_score: int, reference_score: int, final_score: float,
                  signal: str, risk_check_passed: bool, error_flag: bool = False,
                  error_message: Optional[str] = None) -> int:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO decisions 
                (absolute_score, reference_score, final_score, signal, risk_check_passed, error_flag, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (absolute_score, reference_score, final_score, signal, risk_check_passed, error_flag, error_message))
            decision_id = cur.fetchone()["id"]
            conn.commit()
            return decision_id


def make_decision(current_positions: List[Dict[str, Any]], account_balance: float) -> Dict[str, Any]:
    from risk_manager import RiskManager

    try:
        logger.info("Starting decision engine")
        logger.info(f"Current positions: {len(current_positions)}, account balance: {account_balance}")

        risk_manager = RiskManager(account_balance)

        scores = get_latest_scores()
        if not scores:
            logger.error("No scores available - returning HOLD")
            return {
                "signal": "HOLD",
                "final_score": 0,
                "absolute_score": 0,
                "reference_score": 0,
                "risk_check_passed": False,
                "error_flag": True,
                "error_message": "No scores available",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

        absolute_score = scores["absolute_score"]
        reference_score = scores["reference_score"]
        final_score = calculate_final_score(absolute_score, reference_score)
        signal = generate_signal(final_score)

        logger.info(f"Scores - Absolute: {absolute_score}, Reference: {reference_score}, Final: {final_score}")
        logger.info(f"Signal before risk check: {signal}")

        risk_check_result = risk_manager.check_all(current_positions)

        if not risk_check_result["passed"]:
            signal = "HOLD"
            error_flag = True
            error_message = risk_check_result["reason"]
            logger.warning(f"Risk check failed: {error_message}")
        else:
            error_flag = False
            error_message = None
            logger.info("Risk check passed")

        decision_id = save_decision(
            absolute_score, reference_score, final_score, signal,
            risk_check_result["passed"], error_flag, error_message
        )

        position_size = 0
        if signal == "BUY" and risk_check_result["passed"]:
            position_size = risk_manager.calculate_position_size(current_positions, account_balance)
            logger.info(f"Recommended position size: {position_size}")

        result = {
            "decision_id": decision_id,
            "signal": signal,
            "final_score": round(final_score, 2),
            "absolute_score": absolute_score,
            "reference_score": reference_score,
            "recalculated_absolute": scores.get("recalculated_absolute"),
            "recalculated_reference": scores.get("recalculated_reference"),
            "risk_check_passed": risk_check_result["passed"],
            "error_flag": error_flag,
            "error_message": error_message,
            "recommended_position_size": position_size,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        logger.info(f"Decision complete: {signal} with score {final_score}")
        return result

    except Exception as e:
        logger.error(f"Decision engine error: {e}")
        logger.error(traceback.format_exc())
        try:
            decision_id = save_decision(0, 0, 0, "HOLD", False, True, str(e))
        except:
            decision_id = 0
        return {
            "decision_id": decision_id,
            "signal": "HOLD",
            "final_score": 0,
            "absolute_score": 0,
            "reference_score": 0,
            "risk_check_passed": False,
            "error_flag": True,
            "error_message": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Decision Engine Integration Test")
    print("=" * 60)

    print("\n[1] Weights Verification:")
    print(f"    Absolute Weight: {WEIGHTS['absolute']} (60%)")
    print(f"    Reference Weight: {WEIGHTS['reference']} (40%)")
    print(f"    Total: {WEIGHTS['absolute'] + WEIGHTS['reference']}")

    print("\n[2] Absolute Score Component Weights:")
    print(f"    NQ200MA: 30%")
    print(f"    NQ50MA: 30%")
    print(f"    NQ20EMA50EMA: 20%")
    print(f"    MTF: 10%")
    print(f"    Market Phase: 10%")
    print(f"    Total: 100%")

    print("\n[3] Reference Score Component Weights:")
    print(f"    Components Breadth: 20%")
    print(f"    Components Risk: 10%")
    print(f"    Technical RSI: 15%")
    print(f"    Technical ATR: 10%")
    print(f"    Technical Z-Score: 10%")
    print(f"    Technical MACD: 5%")
    print(f"    Technical Divergence: 5%")
    print(f"    Money Flow Futures: 15%")
    print(f"    Money Flow ETF: 10%")
    print(f"    Total: 100%")

    print("\n[4] Score Calculation Test:")
    test_absolute = 75
    test_reference = 80
    test_final = calculate_final_score(test_absolute, test_reference)
    print(f"    Absolute Score: {test_absolute}")
    print(f"    Reference Score: {test_reference}")
    print(f"    Final Score: {test_absolute}*0.6 + {test_reference}*0.4 = {test_final}")

    print("\n[5] Signal Thresholds:")
    print(f"    BUY threshold: >={SIGNAL_THRESHOLDS['buy']}")
    print(f"    SELL threshold: <={SIGNAL_THRESHOLDS['sell']}")
    print(f"    HOLD: between {SIGNAL_THRESHOLDS['sell']} and {SIGNAL_THRESHOLDS['buy']}")

    print("\n[6] Testing signal generation:")
    for score in [25, 50, 75]:
        signal = generate_signal(score)
        print(f"    Score {score} -> {signal}")

    print("\n[7] Component Score Calculation Test:")
    test_absolute_data = {
        "nq200ma_score": 80,
        "nq50ma_score": 75,
        "nq20ema50ema_score": 70,
        "mtf_score": 85,
        "market_phase_score": 60
    }
    test_reference_data = {
        "components_breadth_score": 75,
        "components_risk_score": 80,
        "technical_rsi_score": 65,
        "technical_atr_score": 70,
        "technical_zscore_score": 60,
        "technical_macd_score": 75,
        "technical_divergence_score": 80,
        "money_flow_futures_score": 70,
        "money_flow_etf_score": 85
    }
    abs_calc = calculate_absolute_score_components(test_absolute_data)
    ref_calc = calculate_reference_score_components(test_reference_data)
    print(f"    Absolute Components -> Score: {abs_calc}")
    print(f"    Reference Components -> Score: {ref_calc}")

    print("\n[8] Live Decision Test:")
    try:
        decision = make_decision([], 100000)
        print(f"    Decision: {decision}")
    except Exception as e:
        print(f"    Note: {e}")
        print("    (Database connection may not be available)")

    print("\n" + "=" * 60)
    print("Integration Test Complete")
    print("=" * 60)