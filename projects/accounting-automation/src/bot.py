"""
Telegram Receipt Bot - Phase 1 MVP
接收發票相片，使用 Vision AI 解析，儲存到 Google Sheets
"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# 設定環境變數（如果沒有設定）
if not os.getenv('TELEGRAM_BOT_TOKEN'):
    os.environ['TELEGRAM_BOT_TOKEN'] = '8577625613:AAFxqb8WFWLJ4Gcl-9UOiqbPvI_0Uqc9rMs'
if not os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID'):
    os.environ['GOOGLE_SHEETS_SPREADSHEET_ID'] = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'
if not os.getenv('GOOGLE_CREDENTIALS_PATH'):
    os.environ['GOOGLE_CREDENTIALS_PATH'] = '../credentials.json'

from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

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

# 資料儲存路徑
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

class ReceiptBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.pending_receipts: Dict[str, Dict] = {}  # 暫存等待確認的收據
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """啟動指令"""
        welcome_message = """
🤖 *Ghost Mode 記帳機器人*

歡迎使用！我可以幫你：
📸 拍照記帳 - 直接發送發票相片
📊 自動分類 - AI 辨識支出類別
💾 儲存報表 - 同步到 Google Sheets

*使用方式：*
1. 直接發送發票相片
2. 確認 AI 解析結果
3. 自動記帳完成！

*指令：*
/help - 顯示說明
/status - 查看今日記帳統計
/export - 匯出本月報表
        """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """幫助指令"""
        help_text = """
*📖 使用說明*

1️⃣ *拍照記帳*
   - 直接發送發票/收據相片
   - 支援多張同時發送
   - AI 會自動辨識金額、日期、商家

2️⃣ *確認與修正*
   - 解析後會顯示詳細資訊
   - 可回覆進行修正
   - 確認後自動儲存

3️⃣ *查看報表*
   - /status - 今日統計
   - /export - 匯出 Excel/CSV
   - Dashboard 連結

*💡 提示：*
- 確保相片清晰、光線充足
- 發票四角都在畫面內
- 支援中文/英文/數字辨識
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
        
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看統計"""
        user_id = str(update.effective_user.id)
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 讀取今日記錄
        stats = self._get_today_stats(user_id, today)
        
        status_text = f"""
*📊 今日記帳統計 ({today})*

📝 總筆數：{stats['count']} 筆
💰 總支出：${stats['total']:.2f}
📈 平均單筆：${stats['avg']:.2f}

*類別分佈：*
{self._format_categories(stats['categories'])}
        """
        await update.message.reply_text(status_text, parse_mode='Markdown')
        
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理相片訊息"""
        user_id = str(update.effective_user.id)
        message_id = str(update.message.message_id)
        
        await update.message.reply_text("📸 收到相片，正在分析中...")
        
        try:
            # 下載相片
            photo = update.message.photo[-1]  # 取最高解析度
            file = await context.bot.get_file(photo.file_id)
            
            # 儲存到本地
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{user_id}_{timestamp}.jpg"
            filepath = DATA_DIR / filename
            await file.download_to_drive(str(filepath))
            
            logger.info(f"Photo saved: {filepath}")
            
            # 使用 Vision AI 解析 (Phase 1: 模擬解析，實際整合時替換)
            receipt_data = await self._parse_receipt_with_ai(str(filepath))
            
            # 儲存到暫存等待確認
            self.pending_receipts[message_id] = {
                'user_id': user_id,
                'filepath': str(filepath),
                'data': receipt_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # 顯示解析結果等待確認
            await self._send_receipt_confirmation(update, receipt_data, message_id, str(filepath))
            
        except Exception as e:
            logger.error(f"Error processing photo: {e}")
            await update.message.reply_text(f"❌ 處理失敗：{str(e)}\n請重試或聯繫管理員")
            
    async def _parse_receipt_with_ai(self, image_path: str) -> Dict[str, Any]:
        """
        使用百度 OCR + 規則引擎解析發票
        免費額度：1000次/月
        """
        from vision_parser import ReceiptVisionParser
        
        parser = ReceiptVisionParser()
        result = await parser.parse_receipt(image_path)
        
        return result
        
    async def _send_receipt_confirmation(self, update: Update, data: Dict, message_id: str):
        """發送收據確認訊息"""
        confirmation_text = f"""
*🧾 發票解析結果*

📅 日期：{data['date']}
🏪 商家：{data['merchant']}
💰 金額：${data['amount']:.2f}
📊 類別：{data['category']}
🧾 發票號：{data['receipt_no']}
💳 付款方式：{data['payment_method']}

*商品明細：*
{chr(10).join(f"• {item}" for item in data['items'])}

*信賴度：*{data['confidence']*100:.0f}%

請回覆：
✅ *確認* - 儲存到報表
📝 *修正* - 修改資訊
❌ *取消* - 捨棄此筆
        """
        
        sent_message = await update.message.reply_text(
            confirmation_text, 
            parse_mode='Markdown',
            reply_to_message_id=update.message.message_id
        )
        
        # 更新暫存記錄的確認訊息 ID
        if message_id in self.pending_receipts:
            self.pending_receipts[message_id]['confirmation_message_id'] = sent_message.message_id
            
    async def handle_text_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理文字回覆（確認/修正/取消）"""
        if not update.message.reply_to_message:
            return
            
        text = update.message.text.strip()
        reply_to_id = str(update.message.reply_to_message.message_id)
        
        # 查找對應的暫存收據
        original_message_id = None
        for msg_id, receipt in self.pending_receipts.items():
            if receipt.get('confirmation_message_id') == int(reply_to_id):
                original_message_id = msg_id
                break
                
        if not original_message_id:
            return
            
        receipt = self.pending_receipts[original_message_id]
        
        if '確認' in text or '✅' in text:
            # 儲存到 Google Sheets
            success = await self._save_to_sheets(receipt['data'])
            if success:
                await update.message.reply_text("✅ 已儲存到報表！")
                del self.pending_receipts[original_message_id]
            else:
                await update.message.reply_text("❌ 儲存失敗，請重試")
                
        elif '取消' in text or '❌' in text:
            del self.pending_receipts[original_message_id]
            await update.message.reply_text("❌ 已取消")
            
        elif '修正' in text or '📝' in text:
            await update.message.reply_text(
                "📝 請直接回覆修正資訊，格式：\n"
                "`欄位: 新值`\n"
                "例如：`金額: 50.00` 或 `商家: Starbucks`"
            )
            
    async def _save_to_sheets(self, data: Dict) -> bool:
        """
        儲存到 Google Sheets
        """
        try:
            # 先儲存到本地 JSON (備份)
            records_file = DATA_DIR / "receipts.json"
            
            records = []
            if records_file.exists():
                with open(records_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
                    
            records.append({
                **data,
                'saved_at': datetime.now().isoformat(),
                'synced_to_sheets': False
            })
            
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
                
            # 同步到 Google Sheets
            from sheets_sync import GoogleSheetsSync
            sheets = GoogleSheetsSync()
            sheets_success = await sheets.save_receipt(data)
            
            if sheets_success:
                logger.info(f"Receipt saved to Google Sheets: {data['receipt_no']}")
                # 更新本地記錄的同步狀態
                records[-1]['synced_to_sheets'] = True
                with open(records_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
            else:
                logger.warning(f"Failed to sync to Google Sheets, saved locally only")
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving receipt: {e}")
            return False
            
    def _get_today_stats(self, user_id: str, date: str) -> Dict:
        """取得今日統計"""
        records_file = DATA_DIR / "receipts.json"
        
        if not records_file.exists():
            return {'count': 0, 'total': 0, 'avg': 0, 'categories': {}}
            
        with open(records_file, 'r', encoding='utf-8') as f:
            records = json.load(f)
            
        today_records = [r for r in records if r['date'] == date]
        
        if not today_records:
            return {'count': 0, 'total': 0, 'avg': 0, 'categories': {}}
            
        categories = {}
        for r in today_records:
            cat = r.get('category', '其他')
            categories[cat] = categories.get(cat, 0) + r['amount']
            
        return {
            'count': len(today_records),
            'total': sum(r['amount'] for r in today_records),
            'avg': sum(r['amount'] for r in today_records) / len(today_records),
            'categories': categories
        }
        
    def _format_categories(self, categories: Dict) -> str:
        """格式化類別統計"""
        if not categories:
            return "無數據"
        return '\n'.join([f"• {cat}: ${amt:.2f}" for cat, amt in categories.items()])


def main():
    """主程式"""
    bot = ReceiptBot()
    
    try:
        # 建立 Application
        application = Application.builder().token(bot.token).build()
        
        # 註冊指令處理器
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("help", bot.help_command))
        application.add_handler(CommandHandler("status", bot.status_command))
        
        # 註冊相片處理器
        application.add_handler(MessageHandler(filters.PHOTO, bot.handle_photo))
        
        # 註冊文字回覆處理器
        application.add_handler(MessageHandler(filters.TEXT & filters.REPLY, bot.handle_text_reply))
        
        # 啟動 Bot
        logger.info("Bot started!")
        print("🤖 Bot 已啟動！正在監聽訊息...")
        print("按 Ctrl+C 停止")
        
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # 清除之前的更新
            poll_interval=1.0,  # 每秒檢查一次
            timeout=30  # 30秒超時
        )
        
    except Exception as e:
        logger.error(f"Bot 錯誤: {e}")
        print(f"❌ Bot 錯誤: {e}")
        print("\n可能原因：")
        print("1. 另一個 Bot 實例正在運行")
        print("2. 網路連接問題")
        print("3. Telegram API 限制")
        raise


if __name__ == "__main__":
    main()
