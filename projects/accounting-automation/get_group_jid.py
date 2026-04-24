"""
獲取 WhatsApp 群組 JID 的工具
"""
import json
import os

# 檢查 WhatsApp 憑證檔案
whatsapp_creds_path = os.path.expanduser("~/.openclaw/credentials/whatsapp/default/creds.json")

if os.path.exists(whatsapp_creds_path):
    with open(whatsapp_creds_path, 'r') as f:
        creds = json.load(f)
    
    print("WhatsApp 憑證資訊：")
    print(f"  用戶 ID: {creds.get('me', {}).get('id', 'N/A')}")
    print(f"  用戶名: {creds.get('me', {}).get('name', 'N/A')}")
    
    # 檢查是否有群組資訊
    print("\n已知的群組：")
    # 這裡需要實際的群組資料
    
else:
    print(f"找不到憑證檔案: {whatsapp_creds_path}")

# 提示用戶如何找到群組 JID
print("\n" + "="*50)
print("如何找到群組 JID：")
print("1. 在 WhatsApp 群組中發送一條訊息")
print("2. 查看 OpenClaw 的日誌")
print("3. 尋找類似 '123456789@g.us' 的格式")
print("="*50)
