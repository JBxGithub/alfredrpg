"""
發送最終確認訊息
"""
import asyncio
from telegram import Bot

async def send_final_confirmation():
    """發送最終確認"""
    bot = Bot(token='8577625613:AAFxqb8WFWLJ4Gcl-9UOiqbPvI_0Uqc9rMs')
    user_id = 1487898254
    
    message = """🎉 Ghost Mode 記帳 Bot - 系統就緒！

✅ 所有服務已啟動：
• Telegram Bot 已連接
• Google Sheets 已連接
• OCR: Google Vision API
• 免費額度: 1000次/月

使用方法：
1. 發送發票相片到 Bot
2. AI 自動解析
3. 確認解析結果
4. 自動記帳到 Google Sheets

指令：
/start - 開始使用
/help - 顯示說明
/status - 查看統計

隨時可以發送發票測試！"""
    
    await bot.send_message(
        chat_id=user_id,
        text=message,
        # parse_mode='Markdown'
    )
    print("✅ 最終確認訊息已發送")

if __name__ == "__main__":
    asyncio.run(send_final_confirmation())
