"""
六循環系統 - 每日收盤 V9.4 版本
新增：盈利減倉統計、V9.4 綜合評分
"""

import psycopg2
import json
import os
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from pathlib import Path

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "trading_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "PostgresqL")
}

ALFREDRPG_API_URL = os.getenv("ALFREDRPG_API_URL", "https://alfredrpg.net/api")
ALFREDRPG_API_KEY = os.getenv("ALFREDRPG_API_KEY", "")


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def calculate_daily_pnl(target_date: date) -> float:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(pnl), 0) as total_pnl
        FROM trades
        WHERE status = 'filled'
        AND DATE(timestamp) = %s
    """, (target_date,))
    row = cur.fetchone()
    pnl = float(row[0]) if row[0] else 0.0
    cur.close()
    conn.close()
    return pnl


def calculate_win_rate(lookback_days: int = 30) -> float:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
        FROM trades
        WHERE status = 'filled'
        AND timestamp > NOW() - INTERVAL '%s days'
    """, (lookback_days,))
    row = cur.fetchone()
    total = row[0] or 0
    wins = row[1] or 0
    win_rate = (wins / total * 100) if total > 0 else 0.0
    cur.close()
    conn.close()
    return round(win_rate, 2)


def calculate_max_drawdown(lookback_days: int = 30) -> float:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE(timestamp) as trade_date, SUM(COALESCE(pnl, 0)) as daily_pnl
        FROM trades
        WHERE status = 'filled'
        AND timestamp > NOW() - INTERVAL '%s days'
        GROUP BY DATE(timestamp)
        ORDER BY trade_date
    """, (lookback_days,))
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for row in cur.fetchall():
        daily_pnl = float(row[1]) if row[1] else 0.0
        cumulative += daily_pnl
        if cumulative > peak:
            peak = cumulative
        if peak > 0:
            dd = (peak - cumulative) / peak
            if dd > max_dd:
                max_dd = dd
    cur.close()
    conn.close()
    return round(max_dd * 100, 2)


def get_trade_stats(target_date: date) -> Dict:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins
        FROM trades
        WHERE status = 'filled'
        AND DATE(timestamp) = %s
    """, (target_date,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {
        "total_trades": row[0] or 0,
        "winning_trades": row[1] or 0
    }


def get_account_balance() -> float:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT config_value FROM system_config 
        WHERE config_name = 'account_balance'
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and row[0]:
        config = json.loads(row[0])
        return config.get("balance", 100000)
    return 100000


def calculate_profit_taking_stats(target_date: date) -> Dict:
    """計算盈利減倉統計 (V9.4)"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN action LIKE '%PROFIT_1%' THEN 1 ELSE 0 END) as level_1,
               SUM(CASE WHEN action LIKE '%PROFIT_2%' THEN 1 ELSE 0 END) as level_2
        FROM trades
        WHERE DATE(timestamp) = %s
        AND action LIKE '%PROFIT%'
    """, (target_date,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return {
        "total_partial_exits": row[0] or 0,
        "level_1_exits": row[1] or 0,
        "level_2_exits": row[2] or 0
    }


def calculate_v94_score(annual_return: float, max_drawdown: float, win_rate: float) -> float:
    """計算 V9.4 綜合評分"""
    # 回報分數 (年化 > 60% 為滿分)
    return_score = min(annual_return / 60 * 40, 40)
    
    # 回撤分數 (回撤 < 65% 為滿分，V9.4標準)
    drawdown_score = max(0, (65 - abs(max_drawdown)) / 65 * 30)
    
    # 勝率分數 (> 70% 為滿分)
    winrate_score = min(win_rate / 70 * 30, 30)
    
    return round(return_score + drawdown_score + winrate_score, 2)


def save_daily_record(target_date: date, daily_pnl: float, win_rate: float,
                     max_drawdown: float, badges: List[Dict], 
                     profit_taking_stats: Dict, v94_score: float) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    trade_stats = get_trade_stats(target_date)
    try:
        cur.execute("""
            INSERT INTO achievements 
                (trade_date, total_pnl, win_rate, max_drawdown, 
                 total_trades, winning_trades, badges_earned,
                 partial_exits_l1, partial_exits_l2, v94_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (trade_date) DO UPDATE SET
                total_pnl = EXCLUDED.total_pnl,
                win_rate = EXCLUDED.win_rate,
                max_drawdown = EXCLUDED.max_drawdown,
                total_trades = EXCLUDED.total_trades,
                winning_trades = EXCLUDED.winning_trades,
                badges_earned = EXCLUDED.badges_earned,
                partial_exits_l1 = EXCLUDED.partial_exits_l1,
                partial_exits_l2 = EXCLUDED.partial_exits_l2,
                v94_score = EXCLUDED.v94_score
        """, (target_date, daily_pnl, win_rate, max_drawdown,
             trade_stats["total_trades"], trade_stats["winning_trades"],
             json.dumps(badges),
             profit_taking_stats["level_1_exits"],
             profit_taking_stats["level_2_exits"],
             v94_score))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving daily record: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def send_webhook_notification(message: str) -> bool:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return False
    try:
        import requests
        payload = {"content": message}
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code in (200, 204)
    except Exception as e:
        print(f"Webhook error: {e}")
        return False


def run_daily_close(target_date: Optional[date] = None) -> Dict:
    if target_date is None:
        target_date = date.today()

    daily_pnl = calculate_daily_pnl(target_date)
    win_rate = calculate_win_rate()
    max_drawdown = calculate_max_drawdown()
    account_balance = get_account_balance()
    trade_stats = get_trade_stats(target_date)
    profit_taking_stats = calculate_profit_taking_stats(target_date)
    
    # 計算年化回報 (簡化版)
    total_pnl = calculate_daily_pnl(target_date)
    annual_return = (total_pnl / account_balance * 100) * 12 if account_balance > 0 else 0
    
    # V9.4 綜合評分
    v94_score = calculate_v94_score(annual_return, max_drawdown, win_rate)

    from badges import check_achievements
    badges = check_achievements(target_date)

    save_daily_record(target_date, daily_pnl, win_rate, max_drawdown, 
                     badges, profit_taking_stats, v94_score)

    pnl_percent = (daily_pnl / account_balance * 100) if account_balance > 0 else 0
    message = (f"📊 每日收盤報告 - {target_date}\n"
               f"盈虧: {daily_pnl:+.2f} ({pnl_percent:+.2f}%)\n"
               f"勝率: {win_rate}%\n"
               f"最大回撤: {max_drawdown}%\n"
               f"交易次數: {trade_stats['total_trades']}\n")
    
    # V9.4 新增指標
    if profit_taking_stats['total_partial_exits'] > 0:
        message += f"盈利減倉: {profit_taking_stats['level_1_exits']}(+10%) + {profit_taking_stats['level_2_exits']}(+20%)\n"
    
    message += f"V9.4 評分: {v94_score}/100\n"
    
    if badges:
        badge_text = " ".join(b["icon"] for b in badges)
        message += f"成就解鎖: {badge_text}"

    send_webhook_notification(message)

    return {
        "date": target_date.isoformat(),
        "daily_pnl": daily_pnl,
        "win_rate": win_rate,
        "max_drawdown": max_drawdown,
        "total_trades": trade_stats['total_trades'],
        "profit_taking": profit_taking_stats,
        "v94_score": v94_score,
        "badges": badges
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Daily Close Tasks V9.4")
    parser.add_argument("--date", type=str, help="Target date (YYYY-MM-DD)")
    args = parser.parse_args()

    target_date = None
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()

    result = run_daily_close(target_date)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
