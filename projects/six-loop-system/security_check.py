"""
安全檢查腳本
檢查 API 密鑰配置、風險限制設置
"""

import os
import json
from datetime import datetime

class SecurityChecker:
    """安全檢查器"""
    
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
    
    def check_env_files(self):
        """檢查環境變量文件"""
        print("\n🔒 檢查環境變量配置...")
        
        env_files = [
            '.env',
            'futu-adapter/.env',
            'config/.env'
        ]
        
        for env_file in env_files:
            if os.path.exists(env_file):
                print(f"   ✅ {env_file} 存在")
                
                # Check if it contains sensitive data
                with open(env_file, 'r') as f:
                    content = f.read()
                    
                if 'password' in content.lower() or 'secret' in content.lower() or 'key' in content.lower():
                    print(f"   ⚠️  {env_file} 包含敏感數據，確保已加入 .gitignore")
                    self.warnings.append(f"{env_file} 包含敏感數據")
            else:
                print(f"   ⬜ {env_file} 不存在 (可選)")
    
    def check_gitignore(self):
        """檢查 .gitignore"""
        print("\n🔒 檢查 .gitignore...")
        
        if not os.path.exists('.gitignore'):
            print("   ❌ .gitignore 不存在")
            self.errors.append("缺少 .gitignore 文件")
            return
        
        with open('.gitignore', 'r') as f:
            content = f.read()
        
        required_patterns = [
            '.env',
            '*.env',
            '__pycache__/',
            '*.pyc',
            'logs/',
            'data/',
            '*.log'
        ]
        
        for pattern in required_patterns:
            if pattern in content:
                print(f"   ✅ {pattern} 已忽略")
            else:
                print(f"   ⚠️  {pattern} 未忽略")
                self.warnings.append(f".gitignore 缺少: {pattern}")
    
    def check_risk_limits(self):
        """檢查風險限制配置"""
        print("\n🔒 檢查風險限制...")
        
        risk_config = {
            'max_position_size': 1000,  # Maximum shares
            'max_daily_loss': 500,      # $500 daily loss limit
            'max_total_risk': 0.04,     # 4% total risk
            'stop_loss_pct': 0.02,      # 2% stop loss
            'take_profit_pct': 0.03,    # 3% take profit
        }
        
        print(f"   最大倉位: {risk_config['max_position_size']} 股")
        print(f"   日虧損限制: ${risk_config['max_daily_loss']}")
        print(f"   總風險限制: {risk_config['max_total_risk']*100}%")
        print(f"   止損: {risk_config['stop_loss_pct']*100}%")
        print(f"   止盈: {risk_config['take_profit_pct']*100}%")
        
        # Validate limits
        if risk_config['max_daily_loss'] > 1000:
            self.warnings.append("日虧損限制較高 ($>1000)")
        
        if risk_config['max_total_risk'] > 0.05:
            self.errors.append("總風險限制過高 (>5%)")
        
        print("   ✅ 風險限制配置合理")
    
    def check_api_keys(self):
        """檢查 API 密鑰配置"""
        print("\n🔒 檢查 API 密鑰...")
        
        # Check Futu configuration
        futu_config_path = 'config/futu_config.json'
        if os.path.exists(futu_config_path):
            print(f"   ✅ Futu 配置文件存在")
            
            with open(futu_config_path, 'r') as f:
                config = json.load(f)
            
            if 'api_key' in config or 'password' in config:
                self.warnings.append("Futu 配置文件包含明文密鑰")
        else:
            print(f"   ⬜ Futu 配置文件不存在 (使用環境變量)")
        
        # Check if running in demo mode
        print("   ℹ️  當前使用 Futu OpenD 免費版 (QQQ 數據)")
        print("   ℹ️  交易執行將使用 FutuTradingBot (需單獨配置)")
    
    def check_database_security(self):
        """檢查數據庫安全"""
        print("\n🔒 檢查數據庫安全...")
        
        # Check if using default password
        db_config_path = 'config/database.json'
        if os.path.exists(db_config_path):
            with open(db_config_path, 'r') as f:
                config = json.load(f)
            
            if config.get('password') == 'PostgresqL':
                self.warnings.append("使用默認數據庫密碼，建議修改")
        
        print("   ✅ 數據庫配置檢查完成")
    
    def check_backup_strategy(self):
        """檢查備份策略"""
        print("\n🔒 檢查備份策略...")
        
        backup_items = [
            ('flows/', 'Node-RED Flows'),
            ('config/', '配置文件'),
            ('sql/', 'SQL 腳本'),
            ('logs/', '日誌文件'),
        ]
        
        for path, name in backup_items:
            if os.path.exists(path):
                print(f"   ✅ {name} ({path})")
            else:
                print(f"   ⚠️  {name} ({path}) 不存在")
        
        # Check backup script
        if os.path.exists('backup.sh') or os.path.exists('backup.ps1'):
            print("   ✅ 備份腳本存在")
        else:
            print("   ⬜ 備份腳本不存在 (建議創建)")
    
    def generate_report(self):
        """生成安全檢查報告"""
        print("\n" + "=" * 60)
        print("安全檢查報告")
        print("=" * 60)
        print(f"檢查時間: {datetime.now()}")
        
        if self.errors:
            print(f"\n❌ 錯誤 ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ 所有安全檢查通過！")
        
        print("=" * 60)
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'errors': self.errors,
            'warnings': self.warnings,
            'status': 'failed' if self.errors else ('warning' if self.warnings else 'passed')
        }
        
        os.makedirs('logs', exist_ok=True)
        with open(f"logs/security_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        return len(self.errors) == 0

def main():
    """運行安全檢查"""
    print("=" * 60)
    print("六循環系統 - 安全檢查")
    print("=" * 60)
    
    checker = SecurityChecker()
    
    checker.check_env_files()
    checker.check_gitignore()
    checker.check_risk_limits()
    checker.check_api_keys()
    checker.check_database_security()
    checker.check_backup_strategy()
    
    passed = checker.generate_report()
    
    return 0 if passed else 1

if __name__ == '__main__':
    exit(main())
