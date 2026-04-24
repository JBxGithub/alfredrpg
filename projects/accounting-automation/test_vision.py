"""
測試 Google Vision OCR
"""
import os
import sys
import asyncio

# 設定環境變數
os.environ['OCR_PROVIDER'] = 'google'

sys.path.insert(0, 'src')

from vision_parser import ReceiptVisionParser

async def test_vision():
    """測試 Google Vision OCR"""
    print("📝 測試 Google Vision OCR...")
    
    parser = ReceiptVisionParser()
    print(f"✅ OCR 模組載入成功")
    print(f"   供應商: {parser.provider}")
    
    # 建立測試圖片（如果不存在）
    test_image = "data/test_receipt.jpg"
    
    if os.path.exists(test_image):
        result = await parser.parse_receipt(test_image)
        print("\n✅ 解析結果:")
        print(f"   日期: {result['date']}")
        print(f"   商家: {result['merchant']}")
        print(f"   金額: {result['amount']}")
        print(f"   類別: {result['category']}")
        print(f"   信賴度: {result['confidence']}")
    else:
        print(f"⚠️  測試圖片不存在: {test_image}")
        print("請放入一張發票圖片進行測試")

if __name__ == "__main__":
    asyncio.run(test_vision())
