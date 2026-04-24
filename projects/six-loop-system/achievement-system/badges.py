import psycopg2
import json
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "trading_db",
    "user": "postgres",
    "password": "PostgresqL"
}

ACHIEVEMENT_DEFINITIONS = {
    # ===== 基礎成就 =====
    "first_win": {
        "name": "首勝",
        "description": "第一筆盈利交易",
        "icon": "🥉",
        "exp_reward": 50,
        "condition": "first_profitable_trade"
    },
    "streak_5": {
        "name": "連勝",
        "description": "連續5筆盈利",
        "icon": "🥈",
        "exp_reward": 100,
        "condition": "consecutive_wins_5"
    },
    "streak_10": {
        "name": "大師",
        "description": "連續10筆盈利",
        "icon": "🥇",
        "exp_reward": 200,
        "condition": "consecutive_wins_10"
    },
    
    # ===== V9.4 新增：盈利減倉成就 =====
    "profit_taker_1": {
        "name": "落袋為安",
        "description": "首次執行盈利減倉 (+10%減50%)",
        "icon": "💰",
        "exp_reward": 75,
        "condition": "first_profit_taking_level_1"
    },
    "profit_taker_2": {
        "name": "鎖定利潤",
        "description": "執行二次盈利減倉 (+20%再減30%)",
        "icon": "🔒",
        "exp_reward": 100,
        "condition": "first_profit_taking_level_2"
    },
    "profit_master": {
        "name": "獲利大師",
        "description": "單筆交易完整執行兩次盈利減倉",
        "icon": "🏆",
        "exp_reward": 200,
        "condition": "complete_profit_taking_both_levels"
    },
    
    # ===== 風險控制成就 =====
    "steady": {
        "name": "穩健",
        "description": "最大回撤 < 2%",
        "icon": "🛡️",
        "exp_reward": 150,
        "condition": "max_drawdown_under_2"
    },
    "risk_manager": {
        "name": "風險管理師",
        "description": "連續30天最大回撤 < 5% (V9.4標準)",
        "icon": "🎖️",
        "exp_reward": 300,
        "condition": "max_drawdown_under_5_for_30_days"
    },
    "drawdown_hero": {
        "name": "回撤英雄",
        "description": "單月最大回撤控制在 -10% 以內",
        "icon": "⚡",
        "exp_reward": 250,
        "condition": "monthly_max_drawdown_under_10"
    },
    
    # ===== 盈利成就 =====
    "warrior": {
        "name": "勇士",
        "description": "單日盈利 > 5%",
        "icon": "⚔️",
        "exp_reward": 150,
        "condition": "daily_pnl_over_5_percent"
    },
    "sharp_shooter": {
        "name": "神射手",
        "description": "單週盈利 > 10%",
        "icon": "🎯",
        "exp_reward": 300,
        "condition": "weekly_pnl_over_10"
    },
    "diamond_hands": {
        "name": "鑽石手",
        "description": "持有倉位 > 5天",
        "icon": "💎",
        "exp_reward": 100,
        "condition": "hold_position_over_5_days"
    },
    "comeback_kid": {
        "name": "逆轉王",
        "description": "虧損後反彈 > 3%",
        "icon": "🔥",
        "exp_reward": 100,
        "condition": "comeback_after_loss"
    },
    "perfect_month": {
        "name": "完美一個月",
        "description": "單月盈利 > 20%",
        "icon": "🌟",
        "exp_reward": 500,
        "condition": "monthly_pnl_over_20"
    },
    
    # ===== 高級成就 =====
    "legend": {
        "name": "傳說",
        "description": "總盈利 > 100%",
        "icon": "👑",
        "exp_reward": 1000,
        "condition": "total_pnl_over_100"
    },
    "v9_4_master": {
        "name": "V9.4 大師",
        "description": "使用 V9.4 策略達成 2000% 回報",
        "icon": "🚀",
        "exp_reward": 2000,
        "condition": "v9_4_strategy_2000_percent_return"
    },
    "drawdown_optimizer": {
        "name": "回撤優化師",
        "description": "年化回報 > 60% 且最大回撤 < 65% (V9.4標準)",
        "icon": "📊",
        "exp_reward": 1500,
        "condition": "annual_return_over_60_drawdown_under_65"
    }
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def get_trades_for_date(target_date: date) -> List[Dict]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, symbol, action, quantity, price, pnl, status, timestamp
        FROM trades
        WHERE DATE(timestamp) = %s
        ORDER BY timestamp
    """, (target_date,))
    trades = []
    for row in cur.fetchall():
        trades.append({
            "id": row[0],
            "symbol": row[1],
            "action": row[2],
            "quantity": row[3],
            "price": float(row[4]) if row[4] else None,
            "pnl": float(row[5]) if row[5] else None,
            "status": row[6],
            "timestamp": row[7]
        })
    cur.close()
    conn.close()
    return trades


def get_consecutive_wins() -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT pnl FROM trades
        WHERE status = 'filled'
        ORDER BY timestamp DESC
    """)
    consecutive = 0
    for row in cur.fetchall():
        if row[0] and row[0] > 0:
            consecutive += 1
        else:
            break
    cur.close()
    conn.close()
    return consecutive


def get_max_drawdown(lookback_days: int = 30) -> float:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DATE(timestamp) as trade_date, SUM(pnl) as daily_pnl
        FROM trades
        WHERE status = 'filled'
        AND timestamp > NOW() - INTERVAL '%s days'
        GROUP BY DATE(timestamp)
        ORDER BY trade_date
    """, (lookback_days,))
    cumulative = 0
    peak = 0
    max_dd = 0
    for row in cur.fetchall():
        cumulative += float(row[1]) if row[1] else 0
        if cumulative > peak:
            peak = cumulative
        dd = (peak - cumulative) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
    cur.close()
    conn.close()
    return max_dd * 100


def get_daily_pnl(target_date: date) -> float:
    trades = get_trades_for_date(target_date)
    return sum(t.get("pnl", 0) for t in trades if t.get("pnl"))


def get_account_balance() -> float:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT config_value FROM system_config WHERE config_name = 'account_balance'")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return float(json.loads(row[0]).get("balance", 100000))
    return 100000


def check_achievements(target_date: date) -> List[Dict]:
    unlocked_badges = []
    trades = get_trades_for_date(target_date)
    daily_pnl = get_daily_pnl(target_date)
    account_balance = get_account_balance()
    max_drawdown = get_max_drawdown()
    consecutive_wins = get_consecutive_wins()

    if not ACHIEVEMENT_DEFINITIONS:
        return []

    winning_trades = [t for t in trades if t.get("pnl", 0) > 0]

    if winning_trades and len(winning_trades) == 1:
        unlocked_badges.append({
            "id": "first_win",
            **ACHIEVEMENT_DEFINITIONS["first_win"]
        })

    if consecutive_wins >= 5:
        unlocked_badges.append({
            "id": "streak_5",
            **ACHIEVEMENT_DEFINITIONS["streak_5"]
        })

    if consecutive_wins >= 10:
        unlocked_badges.append({
            "id": "streak_10",
            **ACHIEVEMENT_DEFINITIONS["streak_10"]
        })

    if max_drawdown < 2:
        unlocked_badges.append({
            "id": "steady",
            **ACHIEVEMENT_DEFINITIONS["steady"]
        })

    daily_pnl_percent = (daily_pnl / account_balance) * 100 if account_balance > 0 else 0
    if daily_pnl_percent > 5:
        unlocked_badges.append({
            "id": "warrior",
            **ACHIEVEMENT_DEFINITIONS["warrior"]
        })

    return unlocked_badges


def save_achievements(target_date: date, daily_pnl: float, win_rate: float,
                     max_drawdown: float, total_trades: int, winning_trades: int,
                     badges: List[Dict]) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO achievements (trade_date, total_pnl, win_rate, max_drawdown,
                                    total_trades, winning_trades, badges_earned)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (trade_date) DO UPDATE SET
                total_pnl = EXCLUDED.total_pnl,
                win_rate = EXCLUDED.win_rate,
                max_drawdown = EXCLUDED.max_drawdown,
                total_trades = EXCLUDED.total_trades,
                winning_trades = EXCLUDED.winning_trades,
                badges_earned = EXCLUDED.badges_earned
        """, (target_date, daily_pnl, win_rate, max_drawdown, total_trades,
             winning_trades, json.dumps(badges)))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving achievements: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    today = date.today()
    badges = check_achievements(today)
    print(f"Date: {today}")
    print(f"Unlocked badges: {len(badges)}")
    for badge in badges:
        print(f"  {badge['icon']} {badge['name']}: {badge['description']}")