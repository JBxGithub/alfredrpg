"""
WhatsApp 群組全自動記帳 Bot
收到相片立即處理，無需確認
"""

import os
import sys
import json
import logging
import asyncio
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# 設定環境變數
os.environ['GOOGLE_SHEETS_SPREADSHEET_ID'] = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'
os.environ['GOOGLE_CREDENTIALS_PATH'] = './credentials.json'

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/whatsapp_auto_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 資料儲存路徑
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# 群組 JID
GROUP_JID = "120363426808630578@g.us"


class WhatsAppAutoBot:
    """全自動 WhatsApp 記帳 Bot"""
    
    def __init__(self):
        self.processed_messages = set()  # 避免重複處理
        
    async def process_image(self, image_path: str, message_id: str = None) -> Dict[str, Any]:
        """
        處理發票圖片 - 全自動流程
        
        1. OCR 解析
        2. 提取資訊
        3. 寫入 Google Sheets
        4. 回報結果
        """
        try:
            # 1. OCR 解析
            logger.info(f"開始處理圖片: {image_path}")
            receipt_data = await self._parse_with_google_vision(image_path)
            
            # 2. 寫入 Google Sheets
            logger.info(f"寫入 Google Sheets: {receipt_data['receipt_no']}")
            success = await self._save_to_sheets(receipt_data)
            
            if success:
                # 3. 回報成功
                result_message = self._format_success_message(receipt_data)
                await self._send_to_group(result_message)
                logger.info(f"✅ 成功處理: {receipt_data['receipt_no']}")
                return {'status': 'success', 'data': receipt_data}
            else:
                error_msg = f"❌ 寫入 Google Sheets 失敗: {receipt_data['receipt_no']}"
                await self._send_to_group(error_msg)
                return {'status': 'error', 'message': 'save_failed'}
                
        except Exception as e:
            logger.error(f"處理圖片時出錯: {e}")
            error_msg = f"❌ 處理失敗: {str(e)}"
            await self._send_to_group(error_msg)
            return {'status': 'error', 'message': str(e)}
            
    async def _parse_with_google_vision(self, image_path: str) -> Dict[str, Any]:
        """使用 Google Vision API 解析發票"""
        from googleapiclient.discovery import build
        import pickle
        
        # 載入 OAuth 憑證
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
        service = build('vision', 'v1', credentials=creds)
        
        # 讀取圖片
        with open(image_path, 'rb') as f:
            image_data = f.read()
            
        # 呼叫 Vision API
        request = {
            'image': {'content': base64.b64encode(image_data).decode()},
            'features': [{'type': 'TEXT_DETECTION'}]
        }
        
        response = service.images().annotate(body={'requests': [request]}).execute()
        
        # 提取文字
        text_annotations = response['responses'][0].get('textAnnotations', [])
        if text_annotations:
            full_text = text_annotations[0]['description']
        else:
            full_text = ""
            
        logger.info(f"OCR 識別文字: {full_text[:200]}...")
        
        # 解析發票資訊
        return self._extract_receipt_info(full_text, image_path)
        
    def _extract_receipt_info(self, text: str, image_path: str) -> Dict[str, Any]:
        """從 OCR 文字中提取發票資訊"""
        import re
        from datetime import datetime
        
        lines = text.split('\n')
        
        # 初始化結果
        result = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'merchant': '未知商家',
            'amount': 0.0,
            'tax': 0.0,
            'category': '其他',
            'items': [],
            'receipt_no': f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'payment_method': '未知',
            'currency': 'HKD',
            'raw_text': text[:500],
            'image_path': image_path
        }
        
        # 提取日期
        date_patterns = [
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    result['date'] = f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
                    break
                except:
                    pass
                    
        # 提取金額
        amount_patterns = [
            r'[總合]計[:\s]*\$?\s*(\d+[.,]?\d*)',
            r'Total[:\s]*\$?\s*(\d+[.,]?\d*)',
            r'\$\s*(\d+[.,]?\d{1,2})',
        ]
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    if amount > 0:
                        amounts.append(amount)
                except:
                    pass
        if amounts:
            result['amount'] = max(amounts)
            
        # 提取商家（第一行非數字字串）
        for line in lines[:5]:
            if line.strip() and len(line) > 2:
                if not any(char.isdigit() for char in line[:5]):
                    result['merchant'] = line.strip()
                    break
                    
        # 自動分類
        result['category'] = self._auto_categorize(text)
        
        return result
        
    def _auto_categorize(self, text: str) -> str:
        """自動分類支出"""
        text_lower = text.lower()
        
        categories = {
            '餐飲': ['餐廳', '美食', '飲料', '咖啡', 'cafe', 'restaurant', 'food', '麥當勞', '肯德基'],
            '交通': ['加油', '停車', '的士', 'taxi', 'uber', '地鐵', '港鐵', 'mtr', '巴士'],
            '辦公': ['文具', '印刷', '影印', '辦公', 'stationery', 'print'],
            '購物': ['超市', '便利店', '7-eleven', '百佳', '惠康', 'supermarket'],
            '娛樂': ['電影', '戲院', 'cinema', 'ktv'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
                
        return '其他'
        
    async def _save_to_sheets(self, data: Dict) -> bool:
        """儲存到 Google Sheets"""
        try:
            sys.path.insert(0, 'src')
            from sheets_sync import GoogleSheetsSync
            
            sheets = GoogleSheetsSync()
            return await sheets.save_receipt(data)
            
        except Exception as e:
            logger.error(f"儲存到 Sheets 時出錯: {e}")
            return False
            
    def _format_success_message(self, data: Dict) -> str:
        """格式化成功訊息"""
        return f"""✅ 發票已記錄！

📅 日期：{data['date']}
🏪 商家：{data['merchant']}
💰 金額：${data['amount']:.2f}
📊 類別：{data['category']}
🧾 編號：{data['receipt_no']}

已自動寫入 Google Sheets 📊"""
        
    async def _send_to_group(self, message: str):
        """發送訊息到群組"""
        # 這裡使用 OpenClaw 的 message tool
        # 實際使用時會調用
        logger.info(f"發送到群組: {message[:100]}...")


# 建立 Bot 實例
auto_bot = WhatsAppAutoBot()

print("🤖 WhatsApp 全自動記帳 Bot 已準備就緒！")
print(f"群組: {GROUP_JID}")
print("收到相片將自動處理並寫入 Google Sheets")
