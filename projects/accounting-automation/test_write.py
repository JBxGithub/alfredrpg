"""
測試寫入 Google Sheets
"""
import os
import sys
import asyncio

# 設定環境變數
os.environ['GOOGLE_SHEETS_SPREADSHEET_ID'] = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'
os.environ['GOOGLE_CREDENTIALS_PATH'] = './credentials.json'

sys.path.insert(0, 'src')

from sheets_sync import GoogleSheetsSync

async def test_write():
    """測試寫入資料"""
    print("📝 測試寫入發票資料到 Google Sheets...")
    
    sheets = GoogleSheetsSync()
    
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
    
    success = await sheets.save_receipt(test_receipt)
    
    if success:
        print("✅ 測試資料已成功寫入 Google Sheets！")
        print(f"🔗 查看試算表: https://docs.google.com/spreadsheets/d/{sheets.spreadsheet_id}/edit")
    else:
        print("❌ 寫入失敗")

if __name__ == "__main__":
    asyncio.run(test_write())
