"""
測試最簡單的 Bot 連接
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

BOT_TOKEN = '8577625613:AAFxqb8WFWLJ4Gcl-9UOiqbPvI_0Uqc9rMs'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Bot is working!')

async def main():
    print("🤖 啟動最簡單 Bot 測試...")
    
    # 建立 Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 添加處理器
    application.add_handler(CommandHandler("start", start))
    
    print("✅ Application 建立完成")
    print("🚀 開始 polling...")
    
    # 啟動
    await application.initialize()
    await application.start()
    
    # 使用簡單的 polling
    await application.updater.start_polling(drop_pending_updates=True)
    
    print("✅ Bot 正在運行，按 Ctrl+C 停止")
    
    # 保持運行
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot 已停止")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
