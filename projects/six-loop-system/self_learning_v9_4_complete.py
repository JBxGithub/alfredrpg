"""
六循環系統 - 自學習系統 V9.4 完整版
每週回顧、分析、優化、自動調整策略參數
"""

import psycopg2
import json
import os
import yaml
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import statistics
from dataclasses import dataclass, asdict

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

# 參數調整範圍
PARAM_RANGES = {
    "max_position_pct": (70, 95, 5),      # (min, max, step)
    "profit_level_1": (5, 15, 1),
    "profit_level_2": (15, 25, 1),
    "long_stop": (2, 5, 0.5),
    "short_stop": (1, 3, 0.5)
}


@dataclass
class PerformanceMetrics:
    """績效指標數據類"""
    avg_pnl: float
    avg_win_rate: float
    avg_drawdown: float
    worst_drawdown: float
    total_trades: int
    l1_exits: int
    l2_exits: int
    v94_score: float
    sharpe_ratio: float


@dataclass
class ParameterSuggestion:
    """參數建議數據類"""
    param_name: str
    current_value: float
    suggested_value: float
    reason: str
    confidence: float  # 0-1


class SelfLearningV9_4:
    """V9.4 完整自學習系統"""
    
    def __init__(self):
        self.baseline = V94_BASELINE
        self.param_ranges = PARAM_RANGES
        self.learning_history = []
        
    def get_db_connection(self):
        return psycopg2.connect(**DB_CONFIG)
    
    def get_weekly_performance(self, weeks: int = 4) -> List[Dict]:
        """獲取過去 N 週表現"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # 檢查新列是否存在
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='achievements' AND column_name='partial_exits_l1'
            )
        """)
        has_new_columns = cur.fetchone()[0]
        
        if has_new_columns:
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
        else:
            # 向後兼容
            cur.execute("""
                SELECT 
                    DATE_TRUNC('week', trade_date) as week,
                    SUM(total_pnl) as weekly_pnl,
                    AVG(win_rate) as avg_win_rate,
                    MAX(max_drawdown) as max_dd,
                    SUM(total_trades) as trades,
                    0 as l1_exits,
                    0 as l2_exits,
                    0 as avg_v94_score
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
    
    def get_historical_performance(self, months: int = 6) -> List[Dict]:
        """獲取歷史表現用於比較"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        # 檢查 v94_score 列是否存在
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='achievements' AND column_name='v94_score'
            )
        """)
        has_v94_score = cur.fetchone()[0]
        
        if has_v94_score:
            cur.execute("""
                SELECT 
                    DATE_TRUNC('month', trade_date) as month,
                    SUM(total_pnl) as monthly_pnl,
                    AVG(win_rate) as avg_win_rate,
                    MAX(max_drawdown) as max_dd,
                    AVG(v94_score) as avg_v94_score
                FROM achievements
                WHERE trade_date >= NOW() - INTERVAL '%s months'
                GROUP BY DATE_TRUNC('month', trade_date)
                ORDER BY month DESC
            """, (months,))
        else:
            # 向後兼容：不使用 v94_score
            cur.execute("""
                SELECT 
                    DATE_TRUNC('month', trade_date) as month,
                    SUM(total_pnl) as monthly_pnl,
                    AVG(win_rate) as avg_win_rate,
                    MAX(max_drawdown) as max_dd,
                    0 as avg_v94_score
                FROM achievements
                WHERE trade_date >= NOW() - INTERVAL '%s months'
                GROUP BY DATE_TRUNC('month', trade_date)
                ORDER BY month DESC
            """, (months,))
        
        history = []
        for row in cur.fetchall():
            history.append({
                "month": row[0].strftime("%Y-%m"),
                "pnl": float(row[1]) if row[1] else 0,
                "win_rate": float(row[2]) if row[2] else 0,
                "max_drawdown": float(row[3]) if row[3] else 0,
                "v94_score": float(row[4]) if row[4] else 0
            })
        
        cur.close()
        conn.close()
        
        return history
    
    def calculate_performance_metrics(self, weeks_data: List[Dict]) -> PerformanceMetrics:
        """計算績效指標"""
        if not weeks_data:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        pnls = [w["pnl"] for w in weeks_data]
        win_rates = [w["win_rate"] for w in weeks_data]
        drawdowns = [w["max_drawdown"] for w in weeks_data]
        v94_scores = [w["v94_score"] for w in weeks_data]
        
        # 計算夏普比率 (簡化版)
        avg_pnl = statistics.mean(pnls)
        std_pnl = statistics.stdev(pnls) if len(pnls) > 1 else 1
        sharpe = avg_pnl / std_pnl if std_pnl > 0 else 0
        
        return PerformanceMetrics(
            avg_pnl=avg_pnl,
            avg_win_rate=statistics.mean(win_rates),
            avg_drawdown=statistics.mean(drawdowns),
            worst_drawdown=min(drawdowns),
            total_trades=sum(w["trades"] for w in weeks_data),
            l1_exits=sum(w["l1_exits"] for w in weeks_data),
            l2_exits=sum(w["l2_exits"] for w in weeks_data),
            v94_score=statistics.mean(v94_scores),
            sharpe_ratio=sharpe
        )
    
    def analyze_profit_taking_efficiency(self, metrics: PerformanceMetrics) -> Dict:
        """分析盈利減倉效率"""
        if metrics.total_trades == 0:
            return {"efficiency": "無數據", "recommendation": "無交易數據"}
        
        l1_rate = metrics.l1_exits / metrics.total_trades * 100
        l2_rate = metrics.l2_exits / metrics.total_trades * 100
        
        # 評估效率並給出具體建議
        suggestions = []
        
        if l1_rate < 10:
            suggestions.append("降低 +10% 門檻至 +8%，增加 L1 觸發機會")
        elif l1_rate > 50:
            suggestions.append("提高 +10% 門檻至 +12%，避免過早減倉")
        else:
            suggestions.append("L1 門檻適中，保持 +10%")
        
        if l2_rate < 5:
            suggestions.append("降低 +20% 門檻至 +15% 或 +18%")
        elif l2_rate > 20:
            suggestions.append("提高 +20% 門檻至 +22% 或 +25%")
        else:
            suggestions.append("L2 門檻適中，保持 +20%")
        
        return {
            "l1_rate": round(l1_rate, 2),
            "l2_rate": round(l2_rate, 2),
            "efficiency": "良好" if 10 <= l1_rate <= 50 and 5 <= l2_rate <= 20 else "需調整",
            "suggestions": suggestions
        }
    
    def analyze_drawdown_control(self, metrics: PerformanceMetrics) -> Dict:
        """分析回撤控制效果"""
        suggestions = []
        
        if metrics.worst_drawdown < -70:
            status = "⚠️ 需緊急優化"
            suggestions.append("降低倉位上限至 85%")
            suggestions.append("收緊止損至 -2.5%")
        elif metrics.worst_drawdown < -65:
            status = "⚠️ 需優化"
            suggestions.append("考慮降低倉位至 87-88%")
        elif metrics.avg_drawdown > -50:
            status = "✅ 優秀"
            if metrics.v94_score > 80:
                suggestions.append("可考慮提高倉位至 92-95% 以增加回報")
        else:
            status = "✅ 良好"
            suggestions.append("保持現有參數")
        
        return {
            "avg_drawdown": round(metrics.avg_drawdown, 2),
            "worst_drawdown": round(metrics.worst_drawdown, 2),
            "status": status,
            "suggestions": suggestions
        }
    
    def generate_parameter_suggestions(self, metrics: PerformanceMetrics) -> List[ParameterSuggestion]:
        """生成參數調整建議"""
        suggestions = []
        
        # 1. 倉位上限建議
        if metrics.worst_drawdown < -65:
            suggestions.append(ParameterSuggestion(
                "max_position_pct",
                self.baseline["max_position_pct"],
                85,
                f"最差回撤 {metrics.worst_drawdown:.1f}% 過高，建議降低倉位",
                0.8
            ))
        elif metrics.v94_score > 85 and metrics.worst_drawdown > -60:
            suggestions.append(ParameterSuggestion(
                "max_position_pct",
                self.baseline["max_position_pct"],
                92,
                f"表現優秀 (V94評分 {metrics.v94_score:.1f})，可適度提高倉位",
                0.7
            ))
        
        # 2. 盈利減倉門檻建議
        l1_rate = metrics.l1_exits / max(metrics.total_trades, 1) * 100
        if l1_rate < 10:
            suggestions.append(ParameterSuggestion(
                "profit_level_1",
                self.baseline["profit_level_1"],
                8,
                f"L1 觸發率 {l1_rate:.1f}% 過低，建議降低門檻",
                0.75
            ))
        elif l1_rate > 50:
            suggestions.append(ParameterSuggestion(
                "profit_level_1",
                self.baseline["profit_level_1"],
                12,
                f"L1 觸發率 {l1_rate:.1f}% 過高，建議提高門檻",
                0.75
            ))
        
        # 3. 止損參數建議
        if metrics.worst_drawdown < -70:
            suggestions.append(ParameterSuggestion(
                "long_stop",
                self.baseline["long_stop"],
                2.5,
                f"回撤過大，建議收緊多單止損",
                0.8
            ))
        
        return suggestions
    
    def compare_with_baseline(self, metrics: PerformanceMetrics) -> Dict:
        """與基準比較"""
        return {
            "return_vs_expected": {
                "actual": "計算中",  # 需要年化處理
                "expected": self.baseline["expected_annual_return"],
                "status": "達標" if metrics.v94_score > 70 else "未達標"
            },
            "drawdown_vs_expected": {
                "actual": metrics.worst_drawdown,
                "expected": -self.baseline["expected_max_drawdown"],
                "status": "達標" if metrics.worst_drawdown > -70 else "超標"
            },
            "win_rate_vs_expected": {
                "actual": metrics.avg_win_rate,
                "expected": self.baseline["expected_win_rate"],
                "status": "達標" if metrics.avg_win_rate >= 65 else "未達標"
            }
        }
    
    def update_config_file(self, suggestions: List[ParameterSuggestion]) -> bool:
        """更新配置文件"""
        config_path = "config/v9_4_config.yaml"
        
        try:
            # 讀取現有配置
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 應用建議
            for suggestion in suggestions:
                if suggestion.confidence > 0.7:  # 只應用高信心建議
                    config["position_management"][suggestion.param_name] = suggestion.suggested_value
            
            # 保存
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            
            return True
        except Exception as e:
            print(f"更新配置文件失敗: {e}")
            return False
    
    def generate_comprehensive_report(self) -> Dict:
        """生成綜合報告"""
        # 獲取數據
        weeks_data = self.get_weekly_performance(4)
        history = self.get_historical_performance(6)
        
        if not weeks_data:
            return {"error": "無足夠數據生成報告"}
        
        # 計算指標
        metrics = self.calculate_performance_metrics(weeks_data)
        
        # 各項分析
        profit_analysis = self.analyze_profit_taking_efficiency(metrics)
        drawdown_analysis = self.analyze_drawdown_control(metrics)
        param_suggestions = self.generate_parameter_suggestions(metrics)
        baseline_comparison = self.compare_with_baseline(metrics)
        
        # 趨勢分析
        trend = "上升" if len(history) >= 2 and history[0]["v94_score"] > history[-1]["v94_score"] else "平穩"
        
        report = {
            "report_date": datetime.now().isoformat(),
            "analysis_period": "過去4週",
            "version": "V9.4",
            "performance_summary": {
                "avg_weekly_pnl": round(metrics.avg_pnl, 2),
                "avg_win_rate": round(metrics.avg_win_rate, 2),
                "avg_drawdown": round(metrics.avg_drawdown, 2),
                "worst_drawdown": round(metrics.worst_drawdown, 2),
                "v94_score": round(metrics.v94_score, 2),
                "sharpe_ratio": round(metrics.sharpe_ratio, 2),
                "total_trades": metrics.total_trades
            },
            "profit_taking_analysis": profit_analysis,
            "drawdown_analysis": drawdown_analysis,
            "parameter_suggestions": [asdict(s) for s in param_suggestions],
            "baseline_comparison": baseline_comparison,
            "trend_analysis": {
                "direction": trend,
                "historical_data": history[:3]  # 最近3個月
            },
            "actions": {
                "immediate": [s.reason for s in param_suggestions if s.confidence > 0.8],
                "consider": [s.reason for s in param_suggestions if 0.6 <= s.confidence <= 0.8]
            }
        }
        
        return report
    
    def save_learning_log(self, report: Dict) -> bool:
        """保存學習記錄"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO learning_logs 
                    (log_date, report_type, content, recommendations, v94_score, actions_taken)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                date.today(),
                "weekly_review_v9_4_complete",
                json.dumps(report, ensure_ascii=False, default=str),
                json.dumps(report["actions"], ensure_ascii=False),
                report["performance_summary"]["v94_score"],
                json.dumps(report["parameter_suggestions"], ensure_ascii=False, default=str)
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
    
    def run_weekly_review(self, auto_update: bool = False) -> Dict:
        """執行每週回顧"""
        print("=" * 80)
        print("六循環系統 - V9.4 完整自學習回顧")
        print("=" * 80)
        
        report = self.generate_comprehensive_report()
        
        if "error" in report:
            print(f"❌ {report['error']}")
            return report
        
        # 顯示報告
        print(f"\n📊 表現摘要 (過去4週)")
        print(f"  平均每週盈虧: ${report['performance_summary']['avg_weekly_pnl']:+.2f}")
        print(f"  平均勝率: {report['performance_summary']['avg_win_rate']:.1f}%")
        print(f"  平均回撤: {report['performance_summary']['avg_drawdown']:.1f}%")
        print(f"  最差回撤: {report['performance_summary']['worst_drawdown']:.1f}%")
        print(f"  V9.4 評分: {report['performance_summary']['v94_score']:.1f}/100")
        print(f"  夏普比率: {report['performance_summary']['sharpe_ratio']:.2f}")
        
        print(f"\n💰 盈利減倉分析")
        print(f"  L1 觸發率: {report['profit_taking_analysis']['l1_rate']:.1f}%")
        print(f"  L2 觸發率: {report['profit_taking_analysis']['l2_rate']:.1f}%")
        print(f"  效率: {report['profit_taking_analysis']['efficiency']}")
        for suggestion in report['profit_taking_analysis']['suggestions']:
            print(f"    • {suggestion}")
        
        print(f"\n🛡️ 回撤控制分析")
        print(f"  狀態: {report['drawdown_analysis']['status']}")
        for suggestion in report['drawdown_analysis']['suggestions']:
            print(f"    • {suggestion}")
        
        print(f"\n📈 與基準比較")
        for key, value in report['baseline_comparison'].items():
            print(f"  {key}: {value['status']}")
        
        print(f"\n🎯 參數調整建議")
        for suggestion in report['parameter_suggestions']:
            print(f"  • {suggestion['param_name']}: {suggestion['current_value']} → {suggestion['suggested_value']}")
            print(f"    原因: {suggestion['reason']} (信心度: {suggestion['confidence']:.0%})")
        
        print(f"\n📊 趨勢分析")
        print(f"  方向: {report['trend_analysis']['direction']}")
        
        # 自動更新
        if auto_update and report['parameter_suggestions']:
            high_confidence = [s for s in report['parameter_suggestions'] if s['confidence'] > 0.8]
            if high_confidence:
                print(f"\n🔄 自動更新高信心參數...")
                if self.update_config_file([ParameterSuggestion(**s) for s in high_confidence]):
                    print("✅ 配置文件已更新")
                else:
                    print("❌ 配置文件更新失敗")
        
        # 保存記錄
        if self.save_learning_log(report):
            print(f"\n✅ 學習記錄已保存")
        
        print("=" * 80)
        
        return report


def main():
    """主函數"""
    import argparse
    parser = argparse.ArgumentParser(description="V9.4 Self-Learning System")
    parser.add_argument("--auto-update", action="store_true", help="自動更新高信心參數")
    args = parser.parse_args()
    
    learner = SelfLearningV9_4()
    report = learner.run_weekly_review(auto_update=args.auto_update)
    
    # 輸出 JSON 格式報告
    print("\n" + json.dumps(report, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
