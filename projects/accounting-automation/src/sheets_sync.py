"""
Google Sheets Sync Module
處理發票資料到 Google Sheets 的同步
使用 GOG OAuth 或 Service Account
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Google Sheets API
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 嘗試多種認證方式
try:
    from google.oauth2.credentials import Credentials as UserCredentials
    USER_AUTH_AVAILABLE = True
except ImportError:
    USER_AUTH_AVAILABLE = False

try:
    from google.oauth2.service_account import Credentials as ServiceCredentials
    SERVICE_AUTH_AVAILABLE = True
except ImportError:
    SERVICE_AUTH_AVAILABLE = False

logger = logging.getLogger(__name__)


class GoogleSheetsSync:
    """Google Sheets 同步器"""
    
    def __init__(self):
        self.spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
        self.service = None
        
    def _get_service(self):
        """建立 Google Sheets API 服務"""
        if self.service:
            return self.service
            
        # 嘗試使用 OAuth token.pickle
        try:
            import pickle
            token_path = 'token.pickle'
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
                    
                if creds and creds.valid:
                    self.service = build('sheets', 'v4', credentials=creds)
                    logger.info("Google Sheets API 連接成功 (OAuth)")
                    return self.service
                    
        except Exception as e:
            logger.warning(f"OAuth 連接失敗: {e}")
            
        # 嘗試 Service Account
        try:
            if SERVICE_AUTH_AVAILABLE and os.path.exists(self.credentials_path):
                creds = ServiceCredentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=creds)
                logger.info("Google Sheets API 連接成功 (Service Account)")
                return self.service
                
        except Exception as e:
            logger.warning(f"Service Account 連接失敗: {e}")
            
        logger.error("無法建立 Google Sheets API 連接")
        return None
            
    def _ensure_sheet_structure(self, service) -> bool:
        """確保試算表有正確的結構"""
        try:
            # 檢查是否已有資料表
            spreadsheet = service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            sheet_names = [sheet['properties']['title'] for sheet in sheets]
            
            # 如果沒有「發票記錄」工作表，建立一個
            if '發票記錄' not in sheet_names:
                self._create_receipt_sheet(service)
                
            return True
            
        except Exception as e:
            logger.error(f"檢查試算表結構失敗: {e}")
            return False
            
    def _create_receipt_sheet(self, service):
        """建立發票記錄工作表"""
        try:
            # 新增工作表
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': '發票記錄',
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': 10
                            }
                        }
                    }
                }]
            }
            
            service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # 寫入標題列
            headers = [
                ['日期', '商家', '金額', '稅額', '類別', '商品項目', '發票號碼', '付款方式', '幣別', '建立時間']
            ]
            
            service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range='發票記錄!A1:J1',
                valueInputOption='USER_ENTERED',
                body={'values': headers}
            ).execute()
            
            logger.info("發票記錄工作表建立成功")
            
        except Exception as e:
            logger.error(f"建立工作表失敗: {e}")
            
    async def save_receipt(self, receipt_data: Dict[str, Any]) -> bool:
        """
        儲存發票資料到 Google Sheets
        
        Args:
            receipt_data: 發票資料字典
            
        Returns:
            bool: 是否成功
        """
        service = self._get_service()
        if not service:
            logger.error("Google Sheets 服務未建立")
            return False
            
        # 確保工作表結構
        if not self._ensure_sheet_structure(service):
            return False
            
        try:
            # 準備資料列
            row_data = [
                receipt_data.get('date', ''),
                receipt_data.get('merchant', ''),
                receipt_data.get('amount', 0),
                receipt_data.get('tax', 0),
                receipt_data.get('category', '其他'),
                ', '.join(receipt_data.get('items', [])),
                receipt_data.get('receipt_no', ''),
                receipt_data.get('payment_method', ''),
                receipt_data.get('currency', 'HKD'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
            
            # 附加到工作表
            body = {
                'values': [row_data]
            }
            
            result = service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='發票記錄!A:J',
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"發票已儲存到 Google Sheets: {receipt_data.get('receipt_no')}")
            return True
            
        except HttpError as e:
            logger.error(f"Google Sheets API 錯誤: {e}")
            return False
        except Exception as e:
            logger.error(f"儲存發票失敗: {e}")
            return False
            
    async def get_statistics(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        取得統計資料
        
        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            
        Returns:
            統計資料字典
        """
        service = self._get_service()
        if not service:
            return {}
            
        try:
            # 讀取所有資料
            result = service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='發票記錄!A:J'
            ).execute()
            
            values = result.get('values', [])
            if len(values) <= 1:  # 只有標題列
                return {'count': 0, 'total': 0, 'categories': {}}
                
            # 跳過標題列
            data_rows = values[1:]
            
            # 計算統計
            total_amount = sum(float(row[2]) if len(row) > 2 and row[2] else 0 for row in data_rows)
            count = len(data_rows)
            
            # 類別統計
            categories = {}
            for row in data_rows:
                if len(row) > 4:
                    category = row[4]
                    amount = float(row[2]) if len(row) > 2 and row[2] else 0
                    categories[category] = categories.get(category, 0) + amount
                    
            return {
                'count': count,
                'total': total_amount,
                'avg': total_amount / count if count > 0 else 0,
                'categories': categories
            }
            
        except Exception as e:
            logger.error(f"取得統計資料失敗: {e}")
            return {}


# 測試函數
async def test_sheets_sync():
    """測試 Google Sheets 同步"""
    sync = GoogleSheetsSync()
    
    # 測試資料
    test_receipt = {
        'date': '2024-03-21',
        'merchant': '7-Eleven',
        'amount': 45.50,
        'tax': 0.00,
        'category': '餐飲',
        'items': ['飲料', '零食'],
        'receipt_no': 'INV-20240321-001',
        'payment_method': '現金',
        'currency': 'HKD'
    }
    
    # 測試儲存
    success = await sync.save_receipt(test_receipt)
    if success:
        print("✅ 測試資料已儲存到 Google Sheets")
    else:
        print("❌ 儲存失敗")
        
    # 測試統計
    stats = await sync.get_statistics()
    print(f"\n📊 統計資料:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_sheets_sync())
