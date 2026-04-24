"""
Google OAuth Re-Authorization
重新授權 Google Sheets + Vision API
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = 'token.pickle'

# 需要的權限
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/cloud-vision'
]

def reauthorize():
    """重新授權"""
    print("="*60)
    print("🔐 Google OAuth 重新授權")
    print("="*60)
    print()
    print("即將開啟瀏覽器，請完成以下步驟：")
    print("1. 選擇你的 Google 帳號")
    print("2. 點擊「允許」授權存取 Sheets 和 Vision API")
    print("3. 完成後會自動回到這裡")
    print()
    
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"❌ 錯誤：找不到 {CLIENT_SECRET_FILE}")
        return None
    
    try:
        # 建立 OAuth 流程
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE, 
            SCOPES,
            redirect_uri='http://localhost:8080'
        )
        
        # 執行授權（會開啟瀏覽器）
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',  # 強制顯示授權畫面
            access_type='offline'
        )
        
        # 儲存 token
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
        
        print()
        print("="*60)
        print("✅ 授權成功！")
        print(f"✅ Token 已儲存到 {TOKEN_FILE}")
        print(f"✅ 授權範圍: {creds.scopes}")
        print("="*60)
        
        return creds
        
    except Exception as e:
        print(f"\n❌ 授權失敗: {e}")
        print("\n請確認：")
        print("1. 瀏覽器已開啟並完成授權")
        print("2. 沒有點擊「取消」或「拒絕」")
        print("3. 使用的是正確的 Google 帳號")
        return None

def test_connection():
    """測試 API 連接"""
    from googleapiclient.discovery import build
    
    print("\n🧪 測試 API 連接...")
    
    if not os.path.exists(TOKEN_FILE):
        print("❌ 找不到 token.pickle")
        return
    
    with open(TOKEN_FILE, 'rb') as token:
        creds = pickle.load(token)
    
    print(f"   Token 有效: {creds.valid}")
    print(f"   授權範圍: {creds.scopes}")
    
    # 測試 Sheets
    try:
        sheets = build('sheets', 'v4', credentials=creds)
        spreadsheet_id = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'
        result = sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        print(f"✅ Google Sheets API: 連接成功")
        print(f"   試算表: {result['properties']['title']}")
    except Exception as e:
        print(f"❌ Google Sheets API: {e}")
    
    # 測試 Vision
    try:
        vision = build('vision', 'v1', credentials=creds)
        print(f"✅ Google Vision API: 連接成功")
    except Exception as e:
        print(f"❌ Google Vision API: {e}")

if __name__ == "__main__":
    creds = reauthorize()
    if creds:
        test_connection()
