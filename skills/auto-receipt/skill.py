"""
Auto Receipt Skill for OpenClaw
當收到 WhatsApp 群組圖片時，自動執行 OCR 並寫入 Google Sheets
"""

import os
import sys
import asyncio
from pathlib import Path

# 加入專案路徑
sys.path.insert(0, str(Path(r'C:\Users\BurtClaw\openclaw_workspace\projects\accounting-automation')))

async def handle_incoming_image(image_path: str, chat_id: str, sender: str) -> str:
    """
    處理收到的圖片訊息
    
    這個函數會被 OpenClaw 自動調用
    """
    try:
        # 導入自動 bot
        from whatsapp_auto_bot_v2 import auto_bot
        
        # 執行全自動流程
        result = await auto_bot.process_image(image_path, chat_id)
        
        return result['message']
        
    except Exception as e:
        return f"❌ 自動處理失敗: {str(e)}"


# 檢查是否為發票圖片的簡單啟發式規則
def is_likely_receipt(image_path: str) -> bool:
    """
    簡單判斷是否為發票圖片
    實際使用時可以加入更多判斷邏輯
    """
    # 目前所有圖片都當作發票處理
    # 未來可以加入圖片內容分析
    return True


# OpenClaw 技能入口
async def skill_main(context: dict) -> str:
    """
    OpenClaw 技能主入口
    
    context 包含:
    - image_path: 圖片路徑
    - chat_id: 群組 ID
    - sender: 發送者
    """
    image_path = context.get('image_path')
    chat_id = context.get('chat_id')
    sender = context.get('sender')
    
    if not image_path:
        return "❌ 未提供圖片路徑"
    
    # 檢查是否為發票
    if is_likely_receipt(image_path):
        return await handle_incoming_image(image_path, chat_id, sender)
    else:
        return "🖼️ 收到圖片（非發票，已忽略）"


# 測試
if __name__ == "__main__":
    # 模擬測試
    test_context = {
        'image_path': 'test_receipt.jpg',
        'chat_id': '120363426808630578@g.us',
        'sender': '+85263931048'
    }
    
    result = asyncio.run(skill_main(test_context))
    print(result)
