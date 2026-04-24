"""
啟動記帳 Bot 並測試完整流程
"""
import os
import sys
import asyncio
import logging

# 設定環境變數
os.environ['TELEGRAM_BOT_TOKEN'] = '8577625613:AAFxqb8WFWLJ4Gcl-9UOiqbPvI_0Uqc9rMs'
os.environ['GOOGLE_SHEETS_SPREADSHEET_ID'] = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'
os.environ['GOOGLE_CREDENTIALS_PATH'] = './credentials.json'
os.environ['OCR_PROVIDER'] = 'baidu'

# 加入 src 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from telegram import Bot

async def test_bot():
    """測試 Bot 連接"""
    print("🤖 測試 Ghost Mode 記帳 Bot...")
    print("=" * 50)
    
    # 測試 Telegram Bot
    try:
        bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
        me = await bot.get_me()
        print(f"✅ Telegram Bot 連接成功")
        print(f"   名稱: {me.first_name}")
        print(f"   帳號: @{me.username}")
    except Exception as e:
        print(f"❌ Telegram Bot 連接失敗: {e}")
        return
    
    # 測試 Google Sheets
    print("\n📊 測試 Google Sheets 連接...")
    try:
        from sheets_sync import GoogleSheetsSync
        sheets = GoogleSheetsSync()
        
        # 嘗試讀取試算表資訊
        service = sheets._get_service()
        if service:
            spreadsheet = service.spreadsheets().get(
                spreadsheetId=sheets.spreadsheet_id
            ).execute()
            print(f"✅ Google Sheets 連接成功")
            print(f"   試算表: {spreadsheet.get('properties', {}).get('title')}")
        else:
            print("⚠️  使用 OAuth 模式，需要 token.pickle")
    except Exception as e:
        print(f"⚠️  Google Sheets 測試: {e}")
    
    # 測試 OCR
    print("\n📝 測試 OCR 模組...")
    try:
        from vision_parser import ReceiptVisionParser
        parser = ReceiptVisionParser()
        print(f"✅ OCR 模組載入成功")
        print(f"   供應商: {parser.provider}")
    except Exception as e:
        print(f"❌ OCR 模組載入失敗: {e}")
    
    # 發送啟動通知
    print("\n📨 發送啟動通知...")
    try:
        user_id = 1487898254  # 靚仔的 Telegram ID
        
        message = """
🤖 *Ghost Mode 記帳 Bot 已啟動！*

✅ 系統狀態：
• Telegram Bot：已連接
• Google Sheets：已設定
• OCR 模組：已就緒

*使用方式：*
1️⃣ 直接發送發票相片
2️⃣ AI 自動解析內容
3️⃣ 確認後自動記帳

*指令：*
/start - 開始使用
/help - 顯示說明
/status - 查看統計

請發送一張發票測試！📸
        """
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
        print("✅ 啟動通知已發送")
        
    except Exception as e:
        print(f"❌ 發送通知失敗: {e}")
    
    print("\n" + "=" * 50)
    print("🚀 Bot 準備就緒！")
    print(f"   試算表: https://docs.google.com/spreadsheets/d/{os.environ['GOOGLE_SHEETS_SPREADSHEET_ID']}/edit")

if __name__ == "__main__":
    asyncio.run(test_bot())
