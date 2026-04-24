"""
啟動 Bot 並顯示進度
"""
import os
import sys
import time

# 設定環境變數
os.environ['TELEGRAM_BOT_TOKEN'] = '8577625613:AAFxqb8WFWLJ4Gcl-9UOiqbPvI_0Uqc9rMs'
os.environ['GOOGLE_SHEETS_SPREADSHEET_ID'] = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'
os.environ['GOOGLE_CREDENTIALS_PATH'] = '../credentials.json'

sys.path.insert(0, 'src')

print("🤖 啟動 Ghost Mode 記帳 Bot...")
print("=" * 50)

# 等待 Telegram 伺服器重置
print("\n⏳ 等待 Telegram 伺服器重置 (30秒)...")
for i in range(30, 0, -1):
    print(f"   還剩 {i} 秒...", end='\r')
    time.sleep(1)
print("\n✅ 等待完成！")

# 啟動 Bot
print("\n🚀 正在啟動 Bot...")
from bot import main

try:
    main()
except Exception as e:
    print(f"\n❌ Bot 啟動失敗: {e}")
    print("\n請檢查：")
    print("1. 是否有其他 Bot 實例在運行")
    print("2. 網路連接是否正常")
    print("3. Telegram Token 是否正確")
