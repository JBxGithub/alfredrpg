"""
六循環系統 - 自適應學習系統 (Adaptive Learning System)
持續監控、學習、自動修正交易參數

核心功能:
1. 每日監控實盤表現
2. 每週自動回顧並生成優化建議
3. 每月評估並自動調整參數 (可選)
4. 異常檢測與自動保護機制
5. 長期趨勢分析與策略漂移檢測
"""

import psycopg2
import json
import os
import yaml
import schedule
import time
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import logging

# 設置日誌
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


class AlertLevel(Enum):
    """警報級別"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceAlert:
    """績效警報"""
    level: AlertLevel
    metric: str
    current_value: float
    threshold: float
    message: str
    suggested_action: str


@dataclass
class ParameterAdjustment:
    """參數調整"""
    param_name: str
    old_value: float
    new_value: float
    reason: str
    confidence: float
    timestamp: datetime


class AdaptiveLearningSystem:
    """
    自適應學習系統
    
    設計理念:
    - 持續監控: 每日檢查表現
    - 定期回顧: 每週分析趨勢
    - 自動優化: 每月調整參數 (可選)
    - 異常保護: 自動暫停或減倉
    """
    
    def __init__(self, auto_adjust: bool = False):
        self.auto_adjust = auto_adjust  # 是否自動調整參數
        self.config_path = "config/v9_4_config.yaml"
        self.current_params = self._load_current_params()
        self.adjustment_history = []
        self.alert_history = []
        
    def _load_current_params(self) -> Dict:
        """加載當前參數"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.error(f"加載配置失敗: {e}")
            return {}
    
    def _save_params(self, params: Dict) -> bool:
        """保存參數"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(params, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            logger.error(f"保存配置失敗: {e}")
            return False
    
    def get_db_connection(self):
        return psycopg2.connect(**DB_CONFIG)
    
    # ========== 每日監控 ==========
    
    def daily_monitoring(self) -> Dict:
        """每日監控 - 檢查異常"""
        logger.info("執行每日監控...")
        
        alerts = []
        
        # 1. 檢查昨日表現
        yesterday = date.today() - timedelta(days=1)
        daily_stats = self._get_daily_stats(yesterday)
        
        if daily_stats:
            # 檢查日虧損
            if daily_stats['pnl'] < -2000:  # 單日虧損 > $2000
                alerts.append(PerformanceAlert(
                    level=AlertLevel.WARNING,
                    metric="daily_pnl",
                    current_value=daily_stats['pnl'],
                    threshold=-2000,
                    message=f"昨日虧損過大: ${daily_stats['pnl']:.2f}",
                    suggested_action="檢查市場狀況，考慮暫停交易"
                ))
            
            # 檢查連續虧損
            recent_pnls = self._get_recent_pnls(days=3)
            if all(p < 0 for p in recent_pnls):
                alerts.append(PerformanceAlert(
                    level=AlertLevel.ERROR,
                    metric="consecutive_losses",
                    current_value=len(recent_pnls),
                    threshold=3,
                    message="連續3日虧損",
                    suggested_action="啟動保護模式，減倉50%或暫停"
                ))
            
            # 檢查回撤
            if daily_stats['max_drawdown'] < -10:  # 單日回撤 > 10%
                alerts.append(PerformanceAlert(
                    level=AlertLevel.WARNING,
                    metric="daily_drawdown",
                    current_value=daily_stats['max_drawdown'],
                    threshold=-10,
                    message=f"昨日回撤過大: {daily_stats['max_drawdown']:.1f}%",
                    suggested_action="檢查止損執行是否正常"
                ))
        
        # 2. 檢查系統健康
        system_health = self._check_system_health()
        if not system_health['database']:
            alerts.append(PerformanceAlert(
                level=AlertLevel.CRITICAL,
                metric="database_connection",
                current_value=0,
                threshold=1,
                message="數據庫連接失敗",
                suggested_action="立即檢查數據庫狀態"
            ))
        
        # 處理警報
        for alert in alerts:
            self._handle_alert(alert)
        
        self.alert_history.extend(alerts)
        
        return {
            "date": yesterday.isoformat(),
            "alerts": [self._alert_to_dict(a) for a in alerts],
            "daily_stats": daily_stats,
            "system_health": system_health
        }
    
    def _get_daily_stats(self, target_date: date) -> Optional[Dict]:
        """獲取每日統計"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT total_pnl, win_rate, max_drawdown, total_trades,
                       partial_exits_l1, partial_exits_l2, v94_score
                FROM achievements
                WHERE trade_date = %s
            """, (target_date,))
            
            row = cur.fetchone()
            if row:
                return {
                    'pnl': float(row[0]) if row[0] else 0,
                    'win_rate': float(row[1]) if row[1] else 0,
                    'max_drawdown': float(row[2]) if row[2] else 0,
                    'total_trades': int(row[3]) if row[3] else 0,
                    'l1_exits': int(row[4]) if row[4] else 0,
                    'l2_exits': int(row[5]) if row[5] else 0,
                    'v94_score': float(row[6]) if row[6] else 0
                }
        except Exception as e:
            logger.error(f"獲取每日統計失敗: {e}")
        finally:
            cur.close()
            conn.close()
        
        return None
    
    def _get_recent_pnls(self, days: int = 3) -> List[float]:
        """獲取最近N日盈虧"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        pnls = []
        try:
            cur.execute("""
                SELECT total_pnl
                FROM achievements
                WHERE trade_date >= NOW() - INTERVAL '%s days'
                ORDER BY trade_date DESC
            """, (days,))
            
            for row in cur.fetchall():
                pnls.append(float(row[0]) if row[0] else 0)
        except Exception as e:
            logger.error(f"獲取近期盈虧失敗: {e}")
        finally:
            cur.close()
            conn.close()
        
        return pnls
    
    def _check_system_health(self) -> Dict:
        """檢查系統健康狀態"""
        health = {
            'database': False,
            'futu_opend': False,
            'node_red': False
        }
        
        # 檢查數據庫
        try:
            conn = self.get_db_connection()
            conn.close()
            health['database'] = True
        except:
            pass
        
        # 檢查 Futu OpenD (簡化版)
        # 實際應檢查端口 11111
        
        # 檢查 Node-RED (簡化版)
        # 實際應檢查 http://localhost:1880
        
        return health
    
    def _handle_alert(self, alert: PerformanceAlert):
        """處理警報"""
        if alert.level == AlertLevel.CRITICAL:
            logger.critical(f"🚨 {alert.message} - 建議: {alert.suggested_action}")
            # 發送緊急通知
            self._send_notification(f"🚨 緊急警報: {alert.message}", urgent=True)
        elif alert.level == AlertLevel.ERROR:
            logger.error(f"❌ {alert.message} - 建議: {alert.suggested_action}")
            self._send_notification(f"❌ 錯誤警報: {alert.message}")
        elif alert.level == AlertLevel.WARNING:
            logger.warning(f"⚠️ {alert.message} - 建議: {alert.suggested_action}")
        else:
            logger.info(f"ℹ️ {alert.message}")
    
    def _alert_to_dict(self, alert: PerformanceAlert) -> Dict:
        return {
            'level': alert.level.value,
            'metric': alert.metric,
            'current_value': alert.current_value,
            'threshold': alert.threshold,
            'message': alert.message,
            'suggested_action': alert.suggested_action
        }
    
    # ========== 每週回顧 ==========
    
    def weekly_review(self) -> Dict:
        """每週回顧 - 分析趨勢並生成建議"""
        logger.info("執行每週回顧...")
        
        # 獲取過去4週數據
        weekly_data = self._get_weekly_data(weeks=4)
        
        if not weekly_data:
            return {"error": "無足夠數據"}
        
        # 計算關鍵指標
        avg_pnl = statistics.mean([w['pnl'] for w in weekly_data])
        avg_win_rate = statistics.mean([w['win_rate'] for w in weekly_data])
        avg_drawdown = statistics.mean([w['max_drawdown'] for w in weekly_data])
        worst_drawdown = min([w['max_drawdown'] for w in weekly_data])
        
        # 趨勢分析
        pnls = [w['pnl'] for w in weekly_data]
        trend = "上升" if pnls[0] > pnls[-1] else "下降" if pnls[0] < pnls[-1] else "平穩"
        
        # 生成建議
        suggestions = []
        
        # 1. 回撤分析
        if worst_drawdown < -70:
            suggestions.append({
                'param': 'max_position_pct',
                'current': self.current_params.get('position_management', {}).get('max_position_pct', 90),
                'suggested': 85,
                'reason': f'最差回撤 {worst_drawdown:.1f}% 過高',
                'priority': 'high'
            })
        
        # 2. 盈利減倉分析
        total_l1 = sum(w['l1_exits'] for w in weekly_data)
        total_l2 = sum(w['l2_exits'] for w in weekly_data)
        total_trades = sum(w['total_trades'] for w in weekly_data)
        
        if total_trades > 0:
            l1_rate = total_l1 / total_trades * 100
            if l1_rate < 10:
                suggestions.append({
                    'param': 'profit_level_1',
                    'current': 10,
                    'suggested': 8,
                    'reason': f'L1 觸發率 {l1_rate:.1f}% 過低',
                    'priority': 'medium'
                })
        
        # 3. 勝率分析
        if avg_win_rate < 60:
            suggestions.append({
                'param': 'long_threshold',
                'current': 60,
                'suggested': 62,
                'reason': f'勝率 {avg_win_rate:.1f}% 偏低，提高入場門檻',
                'priority': 'medium'
            })
        
        report = {
            'review_date': datetime.now().isoformat(),
            'period': '過去4週',
            'summary': {
                'avg_weekly_pnl': round(avg_pnl, 2),
                'avg_win_rate': round(avg_win_rate, 2),
                'avg_drawdown': round(avg_drawdown, 2),
                'worst_drawdown': round(worst_drawdown, 2),
                'trend': trend
            },
            'suggestions': suggestions,
            'weekly_data': weekly_data
        }
        
        # 保存回顧記錄
        self._save_weekly_review(report)
        
        logger.info(f"每週回顧完成，生成 {len(suggestions)} 條建議")
        
        return report
    
    def _get_weekly_data(self, weeks: int = 4) -> List[Dict]:
        """獲取週數據"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        data = []
        try:
            cur.execute("""
                SELECT 
                    DATE_TRUNC('week', trade_date) as week,
                    SUM(total_pnl) as pnl,
                    AVG(win_rate) as win_rate,
                    MAX(max_drawdown) as max_dd,
                    SUM(total_trades) as trades,
                    SUM(partial_exits_l1) as l1,
                    SUM(partial_exits_l2) as l2
                FROM achievements
                WHERE trade_date >= NOW() - INTERVAL '%s weeks'
                GROUP BY DATE_TRUNC('week', trade_date)
                ORDER BY week DESC
            """, (weeks,))
            
            for row in cur.fetchall():
                data.append({
                    'week': row[0].strftime('%Y-%m-%d'),
                    'pnl': float(row[1]) if row[1] else 0,
                    'win_rate': float(row[2]) if row[2] else 0,
                    'max_drawdown': float(row[3]) if row[3] else 0,
                    'total_trades': int(row[4]) if row[4] else 0,
                    'l1_exits': int(row[5]) if row[5] else 0,
                    'l2_exits': int(row[6]) if row[6] else 0
                })
        except Exception as e:
            logger.error(f"獲取週數據失敗: {e}")
        finally:
            cur.close()
            conn.close()
        
        return data
    
    def _save_weekly_review(self, report: Dict):
        """保存每週回顧"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO learning_logs 
                    (log_date, report_type, content, recommendations)
                VALUES (%s, %s, %s, %s)
            """, (
                date.today(),
                'weekly_review_auto',
                json.dumps(report, ensure_ascii=False),
                json.dumps(report['suggestions'], ensure_ascii=False)
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"保存每週回顧失敗: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
    # ========== 每月調整 ==========
    
    def monthly_adjustment(self) -> Dict:
        """每月調整 - 自動調整參數 (如啟用)"""
        logger.info("執行每月調整...")
        
        # 獲取過去1個月數據
        monthly_data = self._get_monthly_data(months=3)
        
        if len(monthly_data) < 2:
            return {"error": "無足夠數據進行月度調整"}
        
        # 評估是否需要調整
        adjustments = []
        
        # 檢查回撤趨勢
        drawdowns = [m['max_drawdown'] for m in monthly_data]
        avg_drawdown = statistics.mean(drawdowns)
        
        if avg_drawdown < -65:  # 平均回撤超過 -65%
            adjustments.append(ParameterAdjustment(
                param_name='max_position_pct',
                old_value=self.current_params.get('position_management', {}).get('max_position_pct', 90),
                new_value=85,
                reason=f'過去3個月平均回撤 {avg_drawdown:.1f}% 過高',
                confidence=0.8,
                timestamp=datetime.now()
            ))
        
        # 檢查勝率趨勢
        win_rates = [m['win_rate'] for m in monthly_data]
        avg_win_rate = statistics.mean(win_rates)
        
        if avg_win_rate < 65:
            adjustments.append(ParameterAdjustment(
                param_name='long_threshold',
                old_value=60,
                new_value=62,
                reason=f'過去3個月平均勝率 {avg_win_rate:.1f}% 偏低',
                confidence=0.7,
                timestamp=datetime.now()
            ))
        
        # 執行調整 (如啟用自動調整)
        executed = []
        if self.auto_adjust and adjustments:
            for adj in adjustments:
                if adj.confidence >= 0.75:  # 只執行高信心調整
                    if self._apply_adjustment(adj):
                        executed.append(adj)
                        self.adjustment_history.append(adj)
        
        return {
            'adjustment_date': datetime.now().isoformat(),
            'proposed_adjustments': [asdict(a) for a in adjustments],
            'executed_adjustments': [asdict(a) for a in executed],
            'auto_adjust_enabled': self.auto_adjust,
            'monthly_data': monthly_data
        }
    
    def _get_monthly_data(self, months: int = 3) -> List[Dict]:
        """獲取月數據"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        data = []
        try:
            cur.execute("""
                SELECT 
                    DATE_TRUNC('month', trade_date) as month,
                    SUM(total_pnl) as pnl,
                    AVG(win_rate) as win_rate,
                    MAX(max_drawdown) as max_dd
                FROM achievements
                WHERE trade_date >= NOW() - INTERVAL '%s months'
                GROUP BY DATE_TRUNC('month', trade_date)
                ORDER BY month DESC
            """, (months,))
            
            for row in cur.fetchall():
                data.append({
                    'month': row[0].strftime('%Y-%m'),
                    'pnl': float(row[1]) if row[1] else 0,
                    'win_rate': float(row[2]) if row[2] else 0,
                    'max_drawdown': float(row[3]) if row[3] else 0
                })
        except Exception as e:
            logger.error(f"獲取月數據失敗: {e}")
        finally:
            cur.close()
            conn.close()
        
        return data
    
    def _apply_adjustment(self, adjustment: ParameterAdjustment) -> bool:
        """應用參數調整"""
        try:
            # 更新配置
            if adjustment.param_name == 'max_position_pct':
                self.current_params['position_management']['max_position_pct'] = adjustment.new_value
            elif adjustment.param_name == 'long_threshold':
                self.current_params['thresholds']['long'] = adjustment.new_value
            
            # 保存
            if self._save_params(self.current_params):
                logger.info(f"已調整參數: {adjustment.param_name} {adjustment.old_value} → {adjustment.new_value}")
                return True
        except Exception as e:
            logger.error(f"應用調整失敗: {e}")
        
        return False
    
    # ========== 通知 ==========
    
    def _send_notification(self, message: str, urgent: bool = False):
        """發送通知"""
        # 這裡可以整合 WhatsApp、Discord、Email 等
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url:
            try:
                import requests
                payload = {
                    "content": message,
                    "username": "六循環監控機器人"
                }
                requests.post(webhook_url, json=payload, timeout=10)
            except Exception as e:
                logger.error(f"發送通知失敗: {e}")
    
    # ========== 排程運行 ==========
    
    def setup_schedule(self):
        """設置定時任務"""
        # 每日 08:00 執行監控
        schedule.every().day.at("08:00").do(self.daily_monitoring)
        
        # 每週一 09:00 執行回顧
        schedule.every().monday.at("09:00").do(self.weekly_review)
        
        # 每月1日 10:00 執行調整
        schedule.every().day.at("10:00").do(self._check_monthly_adjustment)
        
        logger.info("定時任務已設置")
    
    def _check_monthly_adjustment(self):
        """檢查是否為每月1日"""
        if date.today().day == 1:
            self.monthly_adjustment()
    
    def run_continuously(self):
        """持續運行"""
        logger.info("自適應學習系統啟動...")
        self.setup_schedule()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次
    
    def run_once(self, task: str = "daily"):
        """單次運行"""
        if task == "daily":
            return self.daily_monitoring()
        elif task == "weekly":
            return self.weekly_review()
        elif task == "monthly":
            return self.monthly_adjustment()
        else:
            return {"error": f"未知任務: {task}"}


def main():
    """主函數"""
    import argparse
    parser = argparse.ArgumentParser(description="Adaptive Learning System")
    parser.add_argument("--mode", choices=["daily", "weekly", "monthly", "continuous"], 
                       default="daily", help="運行模式")
    parser.add_argument("--auto-adjust", action="store_true", 
                       help="啟用自動參數調整")
    args = parser.parse_args()
    
    system = AdaptiveLearningSystem(auto_adjust=args.auto_adjust)
    
    if args.mode == "continuous":
        system.run_continuously()
    else:
        result = system.run_once(args.mode)
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
