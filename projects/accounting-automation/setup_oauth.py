"""
Google OAuth Setup Helper
使用現有的 client_secret 設定 OAuth
"""

import os
import json
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# OAuth 設定
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = 'token.pickle'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def setup_oauth():
    """設定 Google OAuth"""
    creds = None
    
    # 檢查是否已有 token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
            
    # 如果沒有有效的憑證，進行 OAuth 流程
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                print(f"❌ 找不到 {CLIENT_SECRET_FILE}")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # 儲存 token 供未來使用
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
            
    return creds

def test_sheets_access():
    """測試 Sheets 存取"""
    from googleapiclient.discovery import build
    
    creds = setup_oauth()
    if not creds:
        print("❌ OAuth 設定失敗")
        return
        
    try:
        service = build('sheets', 'v4', credentials=creds)
        
        # 測試讀取試算表
        spreadsheet_id = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'
        
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        print(f"✅ 成功連接到試算表！")
        print(f"📋 名稱: {spreadsheet.get('properties', {}).get('title')}")
        print(f"📑 工作表: {[s['properties']['title'] for s in spreadsheet.get('sheets', [])]}")
        
        # 測試寫入
        test_data = [
            ['日期', '商家', '金額', '類別', '測試標記'],
            ['2024-03-21', '測試商家', '100', '測試', '自動匯入']
        ]
        
        body = {'values': test_data}
        
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='A1:E1',
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        print(f"✅ 測試資料已寫入！")
        print(f"🔗 試算表連結: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    print("🔄 設定 Google OAuth...")
    test_sheets_access()
