"""
測試 Google Sheets 連接
"""
import os
import sys

# 設定環境變數
os.environ['GOOGLE_SHEETS_SPREADSHEET_ID'] = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'
os.environ['GOOGLE_CREDENTIALS_PATH'] = './credentials.json'

# 加入 src 到路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import asyncio
from sheets_sync import GoogleSheetsSync

async def test_connection():
    """測試 Google Sheets 連接"""
    print("🔄 測試 Google Sheets 連接...")
    print(f"📊 Spreadsheet ID: {os.environ['GOOGLE_SHEETS_SPREADSHEET_ID']}")
    
    sync = GoogleSheetsSync()
    service = sync._get_service()
    
    if service:
        print("✅ Google Sheets API 連接成功！")
        
        # 測試讀取試算表資訊
        try:
            spreadsheet = service.spreadsheets().get(
                spreadsheetId=sync.spreadsheet_id
            ).execute()
            
            print(f"📋 試算表名稱: {spreadsheet.get('properties', {}).get('title', 'Unknown')}")
            print(f"📑 工作表數量: {len(spreadsheet.get('sheets', []))}")
            
            for sheet in spreadsheet.get('sheets', []):
                print(f"   - {sheet['properties']['title']}")
                
        except Exception as e:
            print(f"❌ 讀取試算表失敗: {e}")
            return
            
        # 測試寫入資料
        print("\n📝 測試寫入資料...")
        test_receipt = {
            'date': '2024-03-21',
            'merchant': '測試商家',
            'amount': 100.00,
            'tax': 0.00,
            'category': '測試',
            'items': ['測試項目'],
            'receipt_no': 'TEST-001',
            'payment_method': '現金',
            'currency': 'HKD'
        }
        
        success = await sync.save_receipt(test_receipt)
        if success:
            print("✅ 測試資料寫入成功！")
            print(f"🔗 試算表連結: https://docs.google.com/spreadsheets/d/{sync.spreadsheet_id}/edit")
        else:
            print("❌ 寫入失敗")
    else:
        print("❌ Google Sheets API 連接失敗")
        print("\n可能原因：")
        print("1. credentials.json 不存在")
        print("2. GOG OAuth 未設定")
        print("3. 試算表權限未開放")

if __name__ == "__main__":
    asyncio.run(test_connection())
