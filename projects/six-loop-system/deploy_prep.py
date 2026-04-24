"""
部署準備腳本
檢查生產環境就緒狀態
"""

import os
import sys
import json
from datetime import datetime

class DeploymentPreparation:
    """部署準備器"""
    
    def __init__(self):
        self.checks = []
        self.ready = True
    
    def check_prerequisites(self):
        """檢查先決條件"""
        print("\n📋 檢查先決條件...")
        
        # Check Python version
        version = sys.version_info
        print(f"   Python 版本: {version.major}.{version.minor}.{version.micro}")
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("   ❌ Python 版本過低 (需要 >= 3.8)")
            self.ready = False
        else:
            print("   ✅ Python 版本符合要求")
        
        # Check required packages
        required_packages = [
            ('futu-api', 'futu'),
            ('psycopg2', 'psycopg2'),
            ('requests', 'requests'),
            ('pandas', 'pandas'),
            ('numpy', 'numpy')
        ]
        
        print("\n   檢查必要包:")
        for package_name, import_name in required_packages:
            try:
                __import__(import_name)
                print(f"   ✅ {package_name}")
            except ImportError:
                print(f"   ❌ {package_name} (未安裝)")
                self.ready = False
    
    def check_file_structure(self):
        """檢查文件結構"""
        print("\n📁 檢查文件結構...")
        
        required_files = [
            'SYSTEM_ARCHITECTURE.md',
            'OPERATIONS_MANUAL.md',
            'SIX_LOOP_IMPROVEMENT_PLAN.md',
            'config/symbols.yaml',
            'futu-adapter/futu_opend_feed_v2.py',
            'task_manager.py',
            'cron/six_loop_monitor.py',
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} (缺失)")
                self.ready = False
    
    def check_directories(self):
        """檢查目錄結構"""
        print("\n📂 檢查目錄結構...")
        
        required_dirs = [
            'config/',
            'flows/',
            'futu-adapter/',
            'cron/',
            'logs/',
            'tasks/',
            'data/',
        ]
        
        for dir_path in required_dirs:
            if os.path.exists(dir_path):
                print(f"   ✅ {dir_path}")
            else:
                print(f"   ⬜ {dir_path} (創建中...)")
                os.makedirs(dir_path, exist_ok=True)
    
    def check_database(self):
        """檢查數據庫就緒"""
        print("\n🗄️  檢查數據庫...")
        
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host='localhost', port=5432, database='trading_db',
                user='postgres', password='PostgresqL'
            )
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = [
                'raw_market_data',
                'system_config',
            ]
            
            for table in required_tables:
                if table in tables:
                    print(f"   ✅ {table}")
                else:
                    print(f"   ❌ {table} (缺失)")
                    self.ready = False
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"   ❌ 數據庫連接失敗: {e}")
            self.ready = False
    
    def check_external_services(self):
        """檢查外部服務"""
        print("\n🌐 檢查外部服務...")
        
        # Check Futu OpenD
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex(('127.0.0.1', 11111))
            sock.close()
            
            if result == 0:
                print("   ✅ Futu OpenD (端口 11111)")
            else:
                print("   ⚠️  Futu OpenD (端口 11111) 未運行")
                print("      提示: 啟動富途牛牛 → OpenD")
        except Exception as e:
            print(f"   ❌ Futu OpenD 檢查失敗: {e}")
        
        # Check Node-RED
        try:
            import requests
            response = requests.get('http://localhost:1880/flows', timeout=5)
            if response.status_code == 200:
                print("   ✅ Node-RED (端口 1880)")
            else:
                print("   ⚠️  Node-RED (端口 1880) 異常")
        except Exception as e:
            print(f"   ⚠️  Node-RED (端口 1880) 未運行")
    
    def check_security(self):
        """檢查安全配置"""
        print("\n🔒 檢查安全配置...")
        
        # Check .gitignore
        if os.path.exists('.gitignore'):
            print("   ✅ .gitignore 存在")
            
            with open('.gitignore', 'r') as f:
                content = f.read()
            
            if '.env' in content:
                print("   ✅ 環境變量已忽略")
            else:
                print("   ⚠️  .gitignore 缺少 .env")
        else:
            print("   ❌ .gitignore 不存在")
            self.ready = False
    
    def generate_deployment_report(self):
        """生成部署報告"""
        print("\n" + "=" * 60)
        print("部署準備報告")
        print("=" * 60)
        print(f"檢查時間: {datetime.now()}")
        
        if self.ready:
            print("\n✅ 系統已就緒，可以部署！")
            print("\n下一步:")
            print("  1. 確保 Futu OpenD 已啟動")
            print("  2. 啟動 Futu 數據饋送器")
            print("  3. 運行監控腳本")
            print("  4. 開始實盤交易")
        else:
            print("\n⚠️  系統未完全就緒，請解決上述問題後再部署。")
        
        print("=" * 60)
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'ready': self.ready,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        }
        
        with open(f"logs/deployment_prep_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        return self.ready

def main():
    """運行部署準備"""
    print("=" * 60)
    print("六循環系統 - 部署準備")
    print("=" * 60)
    
    prep = DeploymentPreparation()
    
    prep.check_prerequisites()
    prep.check_file_structure()
    prep.check_directories()
    prep.check_database()
    prep.check_external_services()
    prep.check_security()
    
    ready = prep.generate_deployment_report()
    
    return 0 if ready else 1

if __name__ == '__main__':
    exit(main())
