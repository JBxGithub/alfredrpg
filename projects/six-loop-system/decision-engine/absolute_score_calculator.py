import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "trading_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "PostgresqL")
}

WEIGHTS = {
    "nq200ma": 30,
    "nq50ma": 30,
    "ema_crossover": 20,
    "mtf": 10,
    "market_phase": 10
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def get_latest_market_data() -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    price,
                    ma50,
                    ma200,
                    ema20,
                    ema50,
                    timestamp
                FROM nq100_technical_indicators 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            row = cur.fetchone()

            if row:
                cur.execute("""
                    SELECT close, timestamp 
                    FROM nq100_technical_indicators 
                    ORDER BY timestamp DESC 
                    LIMIT 200
                """)
                historical = cur.fetchall()

    if not row:
        return None

    return {
        "current": row,
        "historical": historical if 'historical' in locals() else []
    }


def get_mtf_trend_direction() -> Tuple[int, str]:
    tf_trends: Dict[str, str] = {}
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for tf_table, tf_name in [("nq100_daily", "daily"), ("nq100_4h", "4h"), ("nq100_1h", "1h")]:
                try:
                    cur.execute(f"""
                        SELECT ma50, ma200 
                        FROM {tf_table} 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """)
                    tf_row = cur.fetchone()

                    if tf_row and tf_row["ma50"] and tf_row["ma200"]:
                        tf_trends[tf_name] = "bull" if tf_row["ma50"] > tf_row["ma200"] else "bear"
                except Exception:
                    continue

    if not tf_trends:
        return 50, "sideways"

    trends = list(tf_trends.values())
    if all(t == "bull" for t in trends):
        return 100, "strong_bull"
    elif trends.count("bull") >= 2:
        return 70, "bull"
    elif trends.count("bear") >= 2:
        return 30, "bear"
    elif all(t == "bear" for t in trends):
        return 0, "strong_bear"
    return 50, "sideways"


def _score_nq100_vs_ma(price: float, ma: float) -> int:
    if price is None or ma is None or ma == 0:
        return 50
    pct_above = ((price - ma) / ma) * 100
    if pct_above >= 10:
        return 100
    elif pct_above >= 5:
        return 85
    elif pct_above >= 2:
        return 70
    elif pct_above >= 0:
        return 60
    elif pct_above >= -2:
        return 40
    elif pct_above >= -5:
        return 25
    elif pct_above >= -10:
        return 10
    return 0


def _score_ema_crossover(ema20: float, ema50: float) -> int:
    if ema20 is None or ema50 is None:
        return 50
    if ema20 > ema50:
        diff_pct = ((ema20 - ema50) / ema50) * 100
        if diff_pct >= 2:
            return 100
        elif diff_pct >= 1:
            return 80
        elif diff_pct >= 0.5:
            return 65
        return 55
    else:
        diff_pct = ((ema50 - ema20) / ema20) * 100
        if diff_pct >= 2:
            return 0
        elif diff_pct >= 1:
            return 20
        elif diff_pct >= 0.5:
            return 35
        return 45


def _detect_market_phase(historical: list) -> Tuple[int, str]:
    if len(historical) < 20:
        return 50, "unknown"

    recent_prices = [r["close"] for r in historical[:20]]
    if len(recent_prices) < 20:
        return 50, "unknown"

    recent_std = (max(recent_prices) - min(recent_prices)) / ((max(recent_prices) + min(recent_prices)) / 2)

    first_half = sum(recent_prices[:10]) / 10
    second_half = sum(recent_prices[10:20]) / 10
    price_change = ((second_half - first_half) / first_half) * 100

    if recent_std < 0.02 and price_change < 1:
        return 75, "accumulation"
    elif recent_std < 0.03 and price_change > 3:
        return 100, "markup"
    elif recent_std < 0.02 and price_change > 1:
        return 60, "distribution"
    elif recent_std < 0.03 and price_change < -3:
        return 0, "markdown"

    return 50, "sideways"


def calculate_absolute_components(market_data: Optional[Dict[str, Any]] = None
                                  ) -> Optional[Dict[str, Any]]:
    if market_data is None:
        market_data = get_latest_market_data()

    if not market_data or not market_data.get("current"):
        return None

    current = market_data["current"]

    nq200ma_score = _score_nq100_vs_ma(current["price"], current["ma200"])
    nq50ma_score = _score_nq100_vs_ma(current["price"], current["ma50"])
    ema_crossover_score = _score_ema_crossover(current["ema20"], current["ema50"])

    mtf_score, trend_direction = get_mtf_trend_direction()

    phase_score, market_phase = _detect_market_phase(market_data.get("historical", []))

    final_absolute_score = int(
        (nq200ma_score * WEIGHTS["nq200ma"] +
         nq50ma_score * WEIGHTS["nq50ma"] +
         ema_crossover_score * WEIGHTS["ema_crossover"] +
         mtf_score * WEIGHTS["mtf"] +
         phase_score * WEIGHTS["market_phase"]) / 100
    )

    return {
        "nq200ma_score": nq200ma_score,
        "nq50ma_score": nq50ma_score,
        "nq20ema50ema_score": ema_crossover_score,
        "mtf_score": mtf_score,
        "market_phase_score": phase_score,
        "final_absolute_score": final_absolute_score,
        "trend_direction": trend_direction,
        "market_phase": market_phase,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def save_absolute_score(scores: Dict[str, Any]) -> int:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO absolute_scores 
                (nq200ma_score, nq50ma_score, nq20ema50ema_score, mtf_score, 
                 market_phase_score, final_absolute_score, trend_direction, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                scores["nq200ma_score"],
                scores["nq50ma_score"],
                scores["nq20ema50ema_score"],
                scores["mtf_score"],
                scores["market_phase_score"],
                scores["final_absolute_score"],
                scores["trend_direction"],
                scores["timestamp"]
            ))
            result = cur.fetchone()
            conn.commit()
            return result["id"]


def calculate_and_save() -> Optional[Dict[str, Any]]:
    scores = calculate_absolute_components()
    if scores:
        save_absolute_score(scores)
    return scores


if __name__ == "__main__":
    result = calculate_and_save()
    if result:
        print(f"Final Absolute Score: {result['final_absolute_score']}")
        print(f"Components: NQ200MA={result['nq200ma_score']}, NQ50MA={result['nq50ma_score']}, "
              f"EMA={result['nq20ema50ema_score']}, MTF={result['mtf_score']}, "
              f"Phase={result['market_phase_score']}")
        print(f"Trend: {result['trend_direction']}, Phase: {result['market_phase']}")
    else:
        print("Failed to calculate absolute score - no market data available")