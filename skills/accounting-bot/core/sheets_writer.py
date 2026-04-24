"""
Google Sheets 寫入模組
"""

import os
import sys
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# 專案路徑設定
PROJECT_DIR = Path(r'C:\Users\BurtClaw\openclaw_workspace\projects\accounting-automation')

# Sheets 設定
SPREADSHEET_ID = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'


def get_sheets_service():
    """建立 Google Sheets API 服務"""
    try:
        # 切換到專案目錄
        original_dir = os.getcwd()
        os.chdir(PROJECT_DIR)
        
        # 添加專案路徑
        sys.path.insert(0, str(PROJECT_DIR))
        sys.path.insert(0, str(PROJECT_DIR / 'src'))
        
        from googleapiclient.discovery import build
        
        # 載入憑證
        token_path = PROJECT_DIR / 'token.pickle'
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
        
        service = build('sheets', 'v4', credentials=creds)
        
        # 恢復原目錄
        os.chdir(original_dir)
        
        return service
        
    except Exception as e:
        print(f"❌ 建立 Sheets 服務失敗: {e}")
        return None


def ensure_headers(service, sheet_name: str = 'Sheet1') -> bool:
    """確保標題列存在"""
    try:
        expected_headers = ['日期', 'P&L類型', 'P&L分類', '商家', '金額', '備註', '發票號碼', '記錄時間']
        
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A1:H1"
        ).execute()
        
        values = result.get('values', [])
        
        if not values or values[0] != expected_headers:
            headers = [expected_headers]
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{sheet_name}!A1:H1",
                valueInputOption='USER_ENTERED',
                body={'values': headers}
            ).execute()
            print("✅ 已建立 P&L 標題列")
        
        return True
        
    except Exception as e:
        print(f"⚠️ 標題列檢查: {e}")
        return False


def get_sheet_name(service) -> str:
    """取得第一個工作表名稱"""
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = spreadsheet.get('sheets', [])
        if sheets:
            return sheets[0]['properties']['title']
        return 'Sheet1'
    except:
        return 'Sheet1'


def write_to_sheets(
    date: str,
    pnl_type: str,
    pnl_category: str,
    merchant: str,
    amount: float,
    note: str = '',
    receipt_no: str = ''
) -> Dict:
    """
    寫入資料到 Google Sheets
    
    Args:
        date: 日期 (會自動加 ' 防止 Excel 轉換)
        pnl_type: 'REVENUE', 'COST', 或 'EXPENSES'
        pnl_category: P&L 分類編號與名稱
        merchant: 商家名稱
        amount: 金額
        note: 備註
        receipt_no: 發票/帳單號碼
    
    Returns:
        包含 success, message, url 的字典
    """
    try:
        service = get_sheets_service()
        if not service:
            return {
                'success': False,
                'message': '無法建立 Sheets 服務',
                'url': ''
            }
        
        # 取得工作表名稱
        sheet_name = get_sheet_name(service)
        
        # 確保標題列
        ensure_headers(service, sheet_name)
        
        # 格式化日期 (加 ' 防止 Excel 自動轉換)
        if not str(date).startswith("'"):
            date = "'" + str(date)
        
        # 準備資料列 - 所有可能自動轉換的欄位都加前導符號
        record_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        row_data = [
            date,                           # A: 日期 (已有 ')
            pnl_type,                       # B: P&L類型
            pnl_category,                   # C: P&L分類
            merchant[:30],                  # D: 商家
            amount,                         # E: 金額
            note,                           # F: 備註
            str(receipt_no),                # G: 發票號碼 (強制字串)
            "'" + record_time               # H: 記錄時間 (加 ' 防止 Excel 轉換)
        ]
        
        # 附加資料
        body = {'values': [row_data]}
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f'{sheet_name}!A:H',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        updated_range = result.get('updates', {}).get('updatedRange', 'N/A')
        
        return {
            'success': True,
            'message': f'已寫入: {merchant} - ${amount} ({pnl_category})',
            'url': f'https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit',
            'range': updated_range
        }
        
    except Exception as e:
        import traceback
        error_msg = f'寫入 Sheets 失敗: {str(e)}'
        print(f"❌ {error_msg}")
        traceback.print_exc()
        
        return {
            'success': False,
            'message': error_msg,
            'url': f'https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit'
        }
