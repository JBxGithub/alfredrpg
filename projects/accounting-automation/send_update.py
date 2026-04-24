"""
發送系統更新通知
"""
import asyncio
from telegram import Bot

async def send_update():
    """發送更新通知"""
    bot = Bot(token='8577625613:AAFxqb8WFWLJ4Gcl-9UOiqbPvI_0Uqc9rMs')
    user_id = 1487898254
    
    message = """
🔄 *系統更新通知*

✅ OCR 供應商已切換：
• 之前：百度 OCR
• 現在：Google Vision API

*優點：*
✓ 非中國供應商
✓ 準確度更高 (90%+)
✓ 每月 1000 次免費額度
✓ 與 Google Sheets 同生態系

*注意：*
⚠️ 需要啟用 Google Vision API
（在 Google Cloud Console）

請發送一張發票測試新 OCR！📸
    """
    
    await bot.send_message(
        chat_id=user_id,
        text=message,
        parse_mode='Markdown'
    )
    print("✅ 更新通知已發送")

if __name__ == "__main__":
    asyncio.run(send_update())
