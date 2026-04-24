#!/usr/bin/env python3
"""
CreditClaw Setup Script for Alfred
自動註冊 CreditClaw Bot 並設定消費限制
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime

# 配置
CREDITCLAW_BASE_URL = "https://creditclaw.com/api/v1"
CONFIG_FILE = Path(__file__).parent / ".env"

def load_config():
    """載入配置"""
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    return config

def register_bot():
    """註冊 CreditClaw Bot"""
    config = load_config()
    
    bot_name = config.get('CREDITCLAW_BOT_NAME', 'Alfred-Bot')
    owner_email = config.get('CREDITCLAW_OWNER_EMAIL', '')
    
    if not owner_email:
        print("❌ 錯誤：請先在 .env 檔案中設定 CREDITCLAW_OWNER_EMAIL")
        return None
    
    print(f"🤖 正在註冊 CreditClaw Bot: {bot_name}")
    
    payload = {
        "bot_name": bot_name,
        "owner_email": owner_email,
        "description": "Alfred - AI Agent for Burt's automation and profit generation"
    }
    
    try:
        response = requests.post(
            f"{CREDITCLAW_BASE_URL}/bots/register",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            print("✅ 註冊成功！")
            print(f"   Bot ID: {data.get('bot_id')}")
            print(f"   Claim Token: {data.get('claim_token')}")
            print(f"   驗證網址: {data.get('owner_verification_url')}")
            print(f"\n🔑 API Key: {data.get('api_key')}")
            print("\n⚠️  請立即保存此 API Key，之後無法再次查看！")
            
            # 更新 .env 檔案
            update_env_file('CREDITCLAW_API_KEY', data.get('api_key'))
            
            return data
        else:
            print(f"❌ 註冊失敗: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ 註冊錯誤: {e}")
        return None

def update_env_file(key, value):
    """更新 .env 檔案"""
    lines = []
    found = False
    
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            lines = f.readlines()
    
    # 更新或添加金鑰
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            found = True
            break
    
    if not found:
        lines.append(f"{key}={value}\n")
    
    with open(CONFIG_FILE, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ 已更新 .env: {key}")

def check_status():
    """檢查 Bot 狀態"""
    config = load_config()
    api_key = config.get('CREDITCLAW_API_KEY')
    
    if not api_key:
        print("❌ 尚未註冊，請先執行 register()")
        return
    
    try:
        response = requests.get(
            f"{CREDITCLAW_BASE_URL}/bot/status",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Bot 狀態:")
            print(json.dumps(data, indent=2))
        else:
            print(f"⚠️  狀態查詢失敗: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 查詢錯誤: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python setup_creditclaw.py register  # 註冊新 Bot")
        print("  python setup_creditclaw.py status    # 檢查狀態")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "register":
        register_bot()
    elif command == "status":
        check_status()
    else:
        print(f"未知命令: {command}")
