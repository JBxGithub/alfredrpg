"""
成就系統測試
測試每日收盤任務和徽章系統
"""

from datetime import datetime, timezone
import json
import os

class AchievementSystem:
    """成就系統"""
    
    def __init__(self):
        self.achievements_file = 'data/achievements.json'
        self.daily_tasks_file = 'data/daily_tasks.json'
        os.makedirs('data', exist_ok=True)
        self.achievements = self._load_achievements()
        self.daily_tasks = self._load_daily_tasks()
    
    def _load_achievements(self):
        """加載成就"""
        if os.path.exists(self.achievements_file):
            with open(self.achievements_file, 'r') as f:
                return json.load(f)
        return {
            'badges': [],
            'stats': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'streak_days': 0,
                'max_streak': 0
            }
        }
    
    def _load_daily_tasks(self):
        """加載每日任務"""
        if os.path.exists(self.daily_tasks_file):
            with open(self.daily_tasks_file, 'r') as f:
                return json.load(f)
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'tasks': [
                {'id': 'check_market', 'name': '檢查市場開盤', 'completed': False},
                {'id': 'monitor_data', 'name': '監控數據流', 'completed': False},
                {'id': 'review_signals', 'name': '審查交易信號', 'completed': False},
                {'id': 'check_risk', 'name': '檢查風險限制', 'completed': False},
                {'id': 'daily_report', 'name': '生成日報', 'completed': False},
            ]
        }
    
    def _save_achievements(self):
        """保存成就"""
        with open(self.achievements_file, 'w') as f:
            json.dump(self.achievements, f, indent=2)
    
    def _save_daily_tasks(self):
        """保存每日任務"""
        with open(self.daily_tasks_file, 'w') as f:
            json.dump(self.daily_tasks, f, indent=2)
    
    def complete_task(self, task_id):
        """完成任務"""
        for task in self.daily_tasks['tasks']:
            if task['id'] == task_id:
                task['completed'] = True
                print(f"   ✅ 完成任務: {task['name']}")
                self._check_daily_completion()
                return True
        return False
    
    def _check_daily_completion(self):
        """檢查每日任務是否全部完成"""
        all_completed = all(task['completed'] for task in self.daily_tasks['tasks'])
        
        if all_completed:
            print("   🎉 今日所有任務完成！")
            self._award_badge('daily_master', '每日大師')
            self.achievements['stats']['streak_days'] += 1
            
            if self.achievements['stats']['streak_days'] > self.achievements['stats']['max_streak']:
                self.achievements['stats']['max_streak'] = self.achievements['stats']['streak_days']
                print(f"   🔥 新紀錄！連續 {self.achievements['stats']['max_streak']} 天完成任務！")
        
        self._save_achievements()
        self._save_daily_tasks()
    
    def _award_badge(self, badge_id, badge_name):
        """頒發徽章"""
        # Check if already has badge
        existing = [b for b in self.achievements['badges'] if b['id'] == badge_id]
        
        if not existing:
            badge = {
                'id': badge_id,
                'name': badge_name,
                'awarded_at': datetime.now().isoformat()
            }
            self.achievements['badges'].append(badge)
            print(f"   🏆 獲得徽章: {badge_name}")
    
    def record_trade(self, pnl):
        """記錄交易"""
        self.achievements['stats']['total_trades'] += 1
        self.achievements['stats']['total_pnl'] += pnl
        
        if pnl > 0:
            self.achievements['stats']['winning_trades'] += 1
            print(f"   ✅ 盈利交易: +${pnl:.2f}")
        else:
            self.achievements['stats']['losing_trades'] += 1
            print(f"   ❌ 虧損交易: ${pnl:.2f}")
        
        # Check for badges
        if self.achievements['stats']['total_trades'] >= 10:
            self._award_badge('trader_10', '交易新手')
        
        if self.achievements['stats']['total_trades'] >= 100:
            self._award_badge('trader_100', '交易老手')
        
        win_rate = self.achievements['stats']['winning_trades'] / self.achievements['stats']['total_trades']
        if self.achievements['stats']['total_trades'] >= 20 and win_rate >= 0.6:
            self._award_badge('sharp_shooter', '神射手')
        
        self._save_achievements()
    
    def get_status(self):
        """獲取狀態"""
        print("\n" + "=" * 60)
        print("成就系統狀態")
        print("=" * 60)
        
        print("\n📊 統計:")
        stats = self.achievements['stats']
        print(f"   總交易數: {stats['total_trades']}")
        print(f"   盈利交易: {stats['winning_trades']}")
        print(f"   虧損交易: {stats['losing_trades']}")
        
        if stats['total_trades'] > 0:
            win_rate = stats['winning_trades'] / stats['total_trades'] * 100
            print(f"   勝率: {win_rate:.1f}%")
        
        print(f"   總盈虧: ${stats['total_pnl']:.2f}")
        print(f"   連續完成: {stats['streak_days']} 天")
        print(f"   最高連續: {stats['max_streak']} 天")
        
        print("\n🏆 徽章:")
        if self.achievements['badges']:
            for badge in self.achievements['badges']:
                print(f"   • {badge['name']}")
        else:
            print("   (暫無徽章)")
        
        print("\n📋 今日任務:")
        for task in self.daily_tasks['tasks']:
            status = "✅" if task['completed'] else "⬜"
            print(f"   {status} {task['name']}")
        
        print("=" * 60)

def test_achievement_system():
    """測試成就系統"""
    print("=" * 60)
    print("成就系統測試")
    print("=" * 60)
    
    system = AchievementSystem()
    
    # Test 1: Complete daily tasks
    print("\n🧪 測試: 完成每日任務")
    system.complete_task('check_market')
    system.complete_task('monitor_data')
    system.complete_task('review_signals')
    system.complete_task('check_risk')
    system.complete_task('daily_report')
    
    # Test 2: Record trades
    print("\n🧪 測試: 記錄交易")
    system.record_trade(125.50)   # Win
    system.record_trade(-50.00)   # Loss
    system.record_trade(200.00)   # Win
    
    # Show status
    system.get_status()
    
    print("\n✅ 成就系統測試完成!")
    
    return True

if __name__ == '__main__':
    test_achievement_system()
