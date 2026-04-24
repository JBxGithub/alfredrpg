"""
六循環系統 - 自學習系統 V9.4
每週回顧並優化策略參數
"""

import psycopg2
import json
import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import statistics

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "trading_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "PostgresqL")
}

# V9.4 基準參數
V94_BASELINE = {
    "max_position_pct": 90,
    "profit_level_1": 10,
    "reduce_1": 50,
    "profit_level_2": 20,
    "reduce_2": 30,
    "long_stop": 3,
    "short_stop": 2,
    "expected_annual_return": 60,
    "expected_max_drawdown": 65,
    "expected_win_rate": 70
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


class SelfLearningV9_4:
    """V9.4 自學習系統"""
    
    def __init__(self):
        self.baseline = V94_BASELINE
        
    def get_weekly_performance(self, weeks: int = 4) -> Dict:
        """獲取過去 N 週表現"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 獲取每週數據
        cur.execute("""
            SELECT 
                DATE_TRUNC('week', trade_date) as week,
                SUM(total_pnl) as weekly_pnl,
                AVG(win_rate) as avg_win_rate,
                MAX(max_drawdown) as max_dd,
                SUM(total_trades) as trades,
                SUM(partial_exits_l1) as l1_exits,
                SUM(partial_exits_l2) as l2_exits,
                AVG(v94_score) as avg_v94_score
            FROM achievements
            WHERE trade_date >= NOW() - INTERVAL '%s weeks'
            GROUP BY DATE_TRUNC('week', trade_date)
            ORDER BY week DESC
        """, (weeks,))
        
        weeks_data = []
        for row in cur.fetchall():
            weeks_data.append({
                "week": row[0].strftime("%Y-%m-%d"),
                "pnl": float(row[1]) if row[1] else 0,
                "win_rate": float(row[2]) if row[2] else 0,
                "max_drawdown": float(row[3]) if row[3] else 0,
                "trades": int(row[4]) if row[4] else 0,
                "l1_exits": int(row[5]) if row[5] else 0,
                "l2_exits": int(row[6]) if row[6] else 0,
                "v94_score": float(row[7]) if row[7] else 0
            })
        
        cur.close()
        conn.close()
        
        return weeks_data
    
    def analyze_profit_taking_efficiency(self, weeks_data: List[Dict]) -> Dict:
        """分析盈利減倉效率"""
        if not weeks_data:
            return {"efficiency": 0, "recommendation": "無數據"}
        
        total_l1 = sum(w["l1_exits"] for w in weeks_data)
        total_l2 = sum(w["l2_exits"] for w in weeks_data)
        total_trades = sum(w["trades"] for w in weeks_data)
        
        if total_trades == 0:
            return {"efficiency": 0, "recommendation": "無交易數據"}
        
        l1_rate = total_l1 / total_trades * 100
        l2_rate = total_l2 / total_trades * 100
        
        # 評估效率
        efficiency = "良好"
        recommendation = "保持現有參數"
        
        if l1_rate < 10:
            efficiency = "偏低"
            recommendation = "考慮降低 +10% 門檻至 +8%"
        elif l1_rate > 50:
            efficiency = "過高"
            recommendation = "考慮提高 +10% 門檻至 +12%"
        
        if l2_rate < 5:
            efficiency = "L2 偏低"
            recommendation += "，考慮降低 +20% 門檻至 +15%"
        
        return {
            "l1_rate": round(l1_rate, 2),
            "l2_rate": round(l2_rate, 2),
            "efficiency": efficiency,
            "recommendation": recommendation
        }
    
    def analyze_drawdown_control(self, weeks_data: List[Dict]) -> Dict:
        """分析回撤控制效果"""
        if not weeks_data:
            return {"status": "無數據"}
        
        max_dd_values = [w["max_drawdown"] for w in weeks_data if w["max_drawdown"]]
        avg_dd = statistics.mean(max_dd_values) if max_dd_values else 0
        worst_dd = min(max_dd_values) if max_dd_values else 0
        
        status = "良好"
        recommendation = "保持 90% 倉位上限"
        
        if worst_dd < -70:
            status = "⚠️ 需優化"
            recommendation = "考慮降低倉位至 85% 或收緊止損"
        elif worst_dd > -60 and avg_dd > -50:
            status = "✅ 優秀"
            recommendation = "可考慮提高倉位至 95% 以增加回報"
        
        return {
            "avg_drawdown": round(avg_dd, 2),
            "worst_drawdown": round(worst_dd, 2),
            "status": status,
            "recommendation": recommendation
        }
    
    def generate_weekly_report(self) -> Dict:
        """生成每週學習報告"""
        weeks_data = self.get_weekly_performance(4)
        
        if not weeks_data:
            return {"error": "無足夠數據生成報告"}
        
        # 計算關鍵指標
        avg_pnl = statistics.mean([w["pnl"] for w in weeks_data])
        avg_win_rate = statistics.mean([w["win_rate"] for w in weeks_data])
        avg_v94_score = statistics.mean([w["v94_score"] for w in weeks_data])
        
        # 分析各項效率
        profit_taking_analysis = self.analyze_profit_taking_efficiency(weeks_data)
        drawdown_analysis = self.analyze_drawdown_control(weeks_data)
        
        report = {
            "report_date": datetime.now().isoformat(),
            "analysis_period": "過去4週",
            "performance_summary": {
                "avg_weekly_pnl": round(avg_pnl, 2),
                "avg_win_rate": round(avg_win_rate, 2),
                "avg_v94_score": round(avg_v94_score, 2)
            },
            "profit_taking_analysis": profit_taking_analysis,
            "drawdown_analysis": drawdown_analysis,
            "recommendations": [
                profit_taking_analysis["recommendation"],
                drawdown_analysis["recommendation"]
            ],
            "current_params": self.baseline
        }
        
        return report
    
    def save_learning_log(self, report: Dict) -> bool:
        """保存學習記錄"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO learning_logs 
                    (log_date, report_type, content, recommendations, v94_score)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                date.today(),
                "weekly_review_v9_4",
                json.dumps(report, ensure_ascii=False),
                json.dumps(report["recommendations"], ensure_ascii=False),
                report["performance_summary"]["avg_v94_score"]
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"保存學習記錄失敗: {e}")
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()
    
    def run_weekly_review(self) -> Dict:
        """執行每週回顧"""
        print("=" * 70)
        print("六循環系統 - V9.4 每週自學習回顧")
        print("=" * 70)
        
        report = self.generate_weekly_report()
        
        if "error" in report:
            print(f"❌ {report['error']}")
            return report
        
        # 顯示報告
        print(f"\n📊 表現摘要 (過去4週)")
        print(f"  平均每週盈虧: ${report['performance_summary']['avg_weekly_pnl']:+.2f}")
        print(f"  平均勝率: {report['performance_summary']['avg_win_rate']:.1f}%")
        print(f"  V9.4 綜合評分: {report['performance_summary']['avg_v94_score']:.1f}/100")
        
        print(f"\n💰 盈利減倉分析")
        print(f"  L1 觸發率: {report['profit_taking_analysis']['l1_rate']:.1f}%")
        print(f"  L2 觸發率: {report['profit_taking_analysis']['l2_rate']:.1f}%")
        print(f"  效率評估: {report['profit_taking_analysis']['efficiency']}")
        
        print(f"\n🛡️ 回撤控制分析")
        print(f"  平均回撤: {report['drawdown_analysis']['avg_drawdown']:.1f}%")
        print(f"  最差回撤: {report['drawdown_analysis']['worst_drawdown']:.1f}%")
        print(f"  狀態: {report['drawdown_analysis']['status']}")
        
        print(f"\n💡 優化建議")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"  {i}. {rec}")
        
        # 保存記錄
        if self.save_learning_log(report):
            print(f"\n✅ 學習記錄已保存")
        
        print("=" * 70)
        
        return report


def main():
    """主函數"""
    learner = SelfLearningV9_4()
    report = learner.run_weekly_review()
    
    # 輸出 JSON 格式報告
    print("\n" + json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
