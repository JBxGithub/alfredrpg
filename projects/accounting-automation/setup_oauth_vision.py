"""
Google OAuth Setup with Vision API
更新 OAuth 權限，加入 Google Sheets + Vision API
"""

import os
import json
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# OAuth 設定 - 加入 Vision API 權限
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = 'token.pickle'
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/cloud-vision'  # Vision API
]

def setup_oauth_with_vision():
    """設定 Google OAuth (包含 Vision API)"""
    creds = None
    
    print("🔐 開始 OAuth 授權流程...")
    print("請在瀏覽器中完成 Google 授權")
    print("(需要登入並允許存取 Sheets 和 Vision API)")
    print()
    
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"❌ 找不到 {CLIENT_SECRET_FILE}")
        return None
        
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRET_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # 儲存 token
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(creds, token)
        
    print(f"✅ OAuth 授權完成！Token 已儲存到 {TOKEN_FILE}")
    return creds

def test_apis():
    """測試 Sheets 和 Vision API"""
    from googleapiclient.discovery import build
    
    # 載入憑證
    if not os.path.exists(TOKEN_FILE):
        print("❌ 找不到 token.pickle，請先執行 setup")
        return
        
    with open(TOKEN_FILE, 'rb') as token:
        creds = pickle.load(token)
    
    print("\n🧪 測試 API 連接...")
    print(f"   Scopes: {creds.scopes}")
    
    # 測試 Sheets
    try:
        sheets_service = build('sheets', 'v4', credentials=creds)
        spreadsheet_id = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'
        
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        print(f"✅ Google Sheets API: 連接成功")
        print(f"   試算表: {spreadsheet.get('properties', {}).get('title')}")
        
    except Exception as e:
        print(f"❌ Google Sheets API: 失敗 - {e}")
    
    # 測試 Vision
    try:
        vision_service = build('vision', 'v1', credentials=creds)
        print(f"✅ Google Vision API: 連接成功")
        
    except Exception as e:
        print(f"❌ Google Vision API: 失敗 - {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_apis()
    else:
        setup_oauth_with_vision()
        print("\n" + "="*50)
        test_apis()
