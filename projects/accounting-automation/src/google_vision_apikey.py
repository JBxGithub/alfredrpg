"""
Google Vision OCR - 使用 API Key 方式
無需 OAuth，直接使用 API Key
"""

import os
import re
import base64
import requests
from datetime import datetime
from typing import Dict, Any, Optional


class GoogleVisionOCR:
    """使用 Google Vision API (API Key 方式)"""
    
    def __init__(self):
        # 從環境變數或直接使用（實際使用時應該從 secrets 讀取）
        self.api_key = os.getenv('GOOGLE_VISION_API_KEY', '')
        self.base_url = "https://vision.googleapis.com/v1/images:annotate"
        
    def encode_image(self, image_path: str) -> str:
        """將圖片編碼為 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def parse_receipt(self, image_path: str) -> Dict[str, Any]:
        """解析發票圖片"""
        try:
            # 讀取圖片
            base64_image = self.encode_image(image_path)
            
            # 準備請求
            request_body = {
                "requests": [{
                    "image": {
                        "content": base64_image
                    },
                    "features": [{
                        "type": "TEXT_DETECTION",
                        "maxResults": 1
                    }]
                }]
            }
            
            # 呼叫 API
            url = f"{self.base_url}?key={self.api_key}"
            response = requests.post(
                url,
                json=request_body,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Vision API 錯誤: {response.status_code}")
                print(f"   {response.text[:200]}")
                return self._fallback_parse(image_path)
            
            result = response.json()
            
            # 提取文字
            text_annotations = result['responses'][0].get('textAnnotations', [])
            if text_annotations:
                full_text = text_annotations[0]['description']
            else:
                full_text = ""
            
            print(f"📝 OCR 識別文字 (前300字):")
            print(f"   {full_text[:300]}...")
            
            # 解析資訊
            parsed = self._extract_info(full_text)
            parsed['raw_text'] = full_text[:500]  # 保存原始文字供調試
            
            return parsed
            
        except Exception as e:
            print(f"❌ Vision OCR 失敗: {e}")
            return self._fallback_parse(image_path)
    
    def _extract_info(self, text: str) -> Dict[str, Any]:
        """從 OCR 文字中提取發票資訊"""
        lines = text.split('\n')
        
        result = {
            'date': None,
            'merchant': None,
            'amount': 0.0,
            'category': '其他',
            'receipt_no': None,
            'payment_method': '未知',
            'confidence': 0.90
        }
        
        # 提取日期
        import re
        date_patterns = [
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    groups = match.groups()
                    if len(groups[0]) == 4:  # YYYY-MM-DD
                        result['date'] = f"{groups[0]}/{int(groups[1]):02d}/{int(groups[2]):02d}"
                    else:
                        result['date'] = f"{groups[2]}/{int(groups[1]):02d}/{int(groups[0]):02d}"
                    break
                except:
                    pass
        
        if not result['date']:
            result['date'] = datetime.now().strftime('%Y/%m/%d')
        
        # 提取金額（找最大的數字）
        amounts = []
        amount_patterns = [
            r'[總合]計[:\s]*\$?\s*(\d+[.,]?\d*)',
            r'Total[:\s]*\$?\s*(\d+[.,]?\d*)',
            r'\$\s*(\d+[.,]?\d{1,2})',
            r'HKD\s*(\d+[.,]?\d*)',
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    if amount > 0:
                        amounts.append(amount)
                except:
                    pass
        
        if amounts:
            result['amount'] = max(amounts)
        
        # 提取商家（第一行或包含關鍵字的行）
        for line in lines[:5]:
            if len(line.strip()) > 2 and not line.strip().isdigit():
                if any(keyword in line for keyword in ['Ltd', 'Limited', '公司', '餐廳', 'Cafe', 'Restaurant']):
                    result['merchant'] = line.strip()
                    break
        
        if not result['merchant'] and lines:
            result['merchant'] = lines[0].strip()[:30]  # 限制長度
        
        # 自動分類
        result['category'] = self._auto_categorize(text, result['merchant'])
        
        # 提取發票號碼
        receipt_patterns = [
            r'發票號碼[:\s]*([A-Z0-9-]+)',
            r'Invoice[:\s#]*([A-Z0-9-]+)',
            r'No\.?[:\s]*([A-Z0-9-]{6,})',
        ]
        
        for pattern in receipt_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['receipt_no'] = match.group(1)
                break
        
        return result
    
    def _auto_categorize(self, text: str, merchant: str) -> str:
        """自動分類"""
        text_lower = (text + ' ' + (merchant or '')).lower()
        
        categories = {
            '餐飲': ['餐廳', '美食', '飲料', '咖啡', 'cafe', 'restaurant', 'food', '麥當勞', '麵館', '茶餐廳'],
            '交通': ['加油', '停車', '的士', 'taxi', 'uber', '地鐵', '港鐵', 'mtr', '巴士'],
            '辦公': ['文具', '印刷', '影印', '辦公', 'stationery', 'print'],
            '購物': ['超市', '便利店', '7-eleven', '百佳', '惠康', 'supermarket'],
            '娛樂': ['電影', '戲院', 'cinema', 'ktv', '唱k'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return '其他'
    
    def _fallback_parse(self, image_path: str) -> Dict[str, Any]:
        """回退解析"""
        return {
            'date': datetime.now().strftime('%Y/%m/%d'),
            'merchant': '解析失敗-請手動輸入',
            'amount': 0.0,
            'category': '其他',
            'receipt_no': '',
            'payment_method': '未知',
            'confidence': 0.0
        }


# 測試
if __name__ == "__main__":
    ocr = GoogleVisionOCR()
    
    # 測試圖片
    test_image = r"C:\Users\BurtClaw\.openclaw\media\inbound\4218bc91-3b44-45f3-ae12-b0c91f6081cd.jpg"
    
    if os.path.exists(test_image):
        result = ocr.parse_receipt(test_image)
        print("\n✅ 解析結果:")
        import json
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"⚠️ 測試圖片不存在")
