"""
WhatsApp Auto Receipt Bot - 全自動版本
接收發票相片 → OCR 解析 → 自動寫入 Google Sheets
無需人工確認，即時處理
"""

import os
import sys
import json
import logging
import asyncio
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Google Sheets API
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 設定檔
SPREADSHEET_ID = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'
PROJECT_DIR = Path(r'C:\Users\BurtClaw\openclaw_workspace\projects\accounting-automation')

class AutoReceiptBot:
    """全自動發票記帳 Bot"""
    
    def __init__(self):
        self.sheets_service = None
        self._init_sheets_service()
        
    def _init_sheets_service(self):
        """初始化 Google Sheets 服務"""
        try:
            os.chdir(PROJECT_DIR)
            
            # 載入 OAuth token
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
            
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            logger.info("✅ Google Sheets 服務已連接")
            
        except Exception as e:
            logger.error(f"❌ Google Sheets 連接失敗: {e}")
            self.sheets_service = None
    
    async def process_image(self, image_path: str, chat_id: str) -> Dict[str, Any]:
        """
        處理發票圖片 - 全自動流程
        
        1. OCR 解析
        2. 智能分類
        3. 寫入 Google Sheets
        4. 回報結果
        """
        result = {
            'success': False,
            'message': '',
            'data': {}
        }
        
        try:
            # Step 1: OCR 解析
            logger.info(f"🔍 開始 OCR 解析: {image_path}")
            receipt_data = await self._parse_receipt(image_path)
            
            if not receipt_data:
                result['message'] = "❌ 無法解析發票內容"
                return result
            
            # Step 2: 智能分類
            category = self._classify_receipt(receipt_data)
            receipt_data['category'] = category
            
            # Step 3: 寫入 Google Sheets
            logger.info("📝 寫入 Google Sheets...")
            success = await self._write_to_sheets(receipt_data)
            
            if success:
                result['success'] = True
                result['data'] = receipt_data
                result['message'] = self._format_success_message(receipt_data)
            else:
                result['message'] = "❌ 寫入 Google Sheets 失敗"
                
        except Exception as e:
            logger.error(f"處理發票時出錯: {e}")
            result['message'] = f"❌ 處理失敗: {str(e)}"
            
        return result
    
    async def _parse_receipt(self, image_path: str) -> Optional[Dict[str, Any]]:
        """使用 Vision AI 解析發票"""
        try:
            # 導入並使用 vision_parser
            sys.path.insert(0, str(PROJECT_DIR / 'src'))
            from vision_parser import ReceiptVisionParser
            
            parser = ReceiptVisionParser()
            result = await parser.parse_receipt(image_path)
            
            # 轉換為簡化格式
            return {
                'date': result.get('date', datetime.now().strftime('%Y/%m/%d')),
                'merchant': result.get('merchant', '未知商家'),
                'amount': result.get('amount', 0.0),
                'note': result.get('note', '商務餐飲'),
                'receipt_no': result.get('receipt_no', ''),
                'category': result.get('category', '其他'),
                'raw_text': result.get('raw_ocr_text', '')[:200]  # 前200字用於調試
            }
            
        except Exception as e:
            logger.error(f"OCR 解析失敗: {e}")
            # 回退到基本解析
            return {
                'date': datetime.now().strftime('%Y/%m/%d'),
                'merchant': '解析失敗-請手動輸入',
                'amount': 0.0,
                'note': '需要手動確認',
                'receipt_no': '',
                'category': '其他'
            }
    
    def _classify_receipt(self, receipt_data: Dict) -> str:
        """智能分類發票"""
        merchant = receipt_data.get('merchant', '').lower()
        note = receipt_data.get('note', '').lower()
        
        # 根據商家名稱和備註分類
        if any(kw in merchant + note for kw in ['餐廳', '麵館', 'cafe', 'restaurant', '餐飲', '食品']):
            return '餐飲'
        elif any(kw in merchant + note for kw in ['taxi', '的士', 'uber', '交通', '港鐵', '巴士']):
            return '交通'
        elif any(kw in merchant + note for kw in ['office', '文具', '電腦', '軟件', '辦公']):
            return '辦公'
        elif any(kw in merchant + note for kw in ['商務', '業務', '客戶']):
            return '商務費用'
        else:
            return '其他'
    
    async def _write_to_sheets(self, data: Dict) -> bool:
        """寫入 Google Sheets"""
        if not self.sheets_service:
            logger.error("Google Sheets 服務未初始化")
            return False
        
        try:
            # 準備資料列
            row_data = [
                data.get('date', ''),
                data.get('category', '其他'),
                data.get('merchant', ''),
                data.get('amount', 0),
                data.get('note', ''),
                data.get('receipt_no', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            # 檢查並建立標題列
            self._ensure_headers()
            
            # 附加資料
            body = {'values': [row_data]}
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range='工作表1!A:G',
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"✅ 已寫入 Sheets: {data.get('merchant')} - ${data.get('amount')}")
            return True
            
        except Exception as e:
            logger.error(f"寫入 Sheets 失敗: {e}")
            return False
    
    def _ensure_headers(self):
        """確保有標題列"""
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range='工作表1!A1:G1'
            ).execute()
            
            values = result.get('values', [])
            expected_headers = ['日期', '類別', '商家', '金額', '備註', '發票號碼', '記錄時間']
            
            if not values or values[0] != expected_headers:
                headers = [expected_headers]
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=SPREADSHEET_ID,
                    range='工作表1!A1:G1',
                    valueInputOption='USER_ENTERED',
                    body={'values': headers}
                ).execute()
                
        except Exception as e:
            logger.warning(f"檢查標題列時出錯: {e}")
    
    def _format_success_message(self, data: Dict) -> str:
        """格式化成功訊息"""
        return f"""✅ 發票已自動記錄！

🧾 {data.get('merchant', '未知商家')}
💰 ${data.get('amount', 0):.2f}
📅 {data.get('date', '')}
📊 {data.get('category', '其他')}
📝 {data.get('note', '')}

已寫入 Google Sheets 📊"""


# 建立 Bot 實例
auto_bot = AutoReceiptBot()

# 供 OpenClaw 調用的接口
async def process_receipt_image(image_path: str, chat_id: str) -> str:
    """
    OpenClaw 調用的主入口
    
    Args:
        image_path: 圖片檔案路徑
        chat_id: WhatsApp 群組 ID
        
    Returns:
        回覆訊息
    """
    result = await auto_bot.process_image(image_path, chat_id)
    return result['message']


if __name__ == "__main__":
    # 測試模式
    print("🤖 全自動發票記帳 Bot 已啟動！")
    print("等待 WhatsApp 圖片訊息...")
