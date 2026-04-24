#!/usr/bin/env python3
"""
CreditClaw Configuration Script for Alfred
設定消費限制、批准模式和創建收款頁面
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime

# 載入配置
CONFIG_FILE = Path(__file__).parent / ".env"

def load_config():
    """載入 .env 配置"""
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    return config

def setup_spending_limits():
    """設定消費限制和批准模式"""
    config = load_config()
    api_key = config.get('CREDITCLAW_API_KEY')
    
    if not api_key:
        print("❌ 錯誤：找不到 CREDITCLAW_API_KEY")
        return False
    
    print("🔧 設定消費限制...")
    
    # 這裡需要調用 CreditClaw API 來更新限制
    # 注意：實際上消費限制需要在 CreditClaw 網站上由主人手動設定
    
    print("⚠️  重要：請手動在 CreditClaw 網站上設定以下限制：")
    print("   https://creditclaw.com/overview")
    print("")
    print("   建議設定：")
    print("   • 單筆交易限制：$500 USD")
    print("   • 每日限制：$500 USD")
    print("   • 每月限制：$2000 USD")
    print("   • 自動批准上限：$50 USD")
    print("")
    print("   這樣設定後：")
    print("   ✅ $50 以下：我自動批准並執行")
    print("   ⚠️  $51-$500：我會問你批准")
    print("   ❌ 超過 $500：自動拒絕")
    
    return True

def create_checkout_page():
    """創建收款頁面"""
    config = load_config()
    api_key = config.get('CREDITCLAW_API_KEY')
    
    if not api_key:
        print("❌ 錯誤：找不到 CREDITCLAW_API_KEY")
        return None
    
    print("🛒 創建收款頁面...")
    
    # API 端點
    url = "https://creditclaw.com/api/v1/bot/checkout-pages/create"
    
    # 收款頁面配置
    payload = {
        "title": "Alfred AI 自動化服務",
        "description": "AI 代理自動化解決方案 - 記帳、研究、數據分析",
        "amount_usd": 50.00,
        "amount_locked": False,  # 允許客戶自訂金額
        "allowed_methods": ["x402", "usdc_direct", "stripe_onramp", "base_pay"],
        "page_type": "product",
        "shop_visible": True,
        "collect_buyer_name": True
    }
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        
        if response.status_code == 201:
            data = response.json()
            print("✅ 收款頁面創建成功！")
            print(f"   頁面 ID: {data.get('checkout_page_id')}")
            print(f"   收款網址: https://creditclaw.com{data.get('checkout_url')}")
            return data
        else:
            print(f"⚠️  創建失敗: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return None

def main():
    """主程式"""
    print("=" * 50)
    print("🤖 Alfred's CreditClaw 設定")
    print("=" * 50)
    print("")
    
    # 1. 顯示設定建議
    setup_spending_limits()
    print("")
    
    # 2. 創建收款頁面
    result = create_checkout_page()
    
    if result:
        print("")
        print("=" * 50)
        print("✅ 設定完成！")
        print("=" * 50)
        print("")
        print("下一步：")
        print("1. 前往 https://creditclaw.com/overview 設定消費限制")
        print("2. 分享收款頁面給潛在客戶")
        print("3. 我開始自動賺錢模式！")
    else:
        print("")
        print("⚠️  收款頁面創建失敗，請檢查 API Key 是否正確")

if __name__ == "__main__":
    main()
