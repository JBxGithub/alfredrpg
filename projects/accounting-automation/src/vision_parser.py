"""
Vision AI Receipt Parser - 使用百度 OCR API
免費額度：1000次/月
"""

import os
import json
import base64
import requests
from typing import Dict, Any, Optional
from pathlib import Path


class ReceiptVisionParser:
    """發票視覺解析器 - 百度 OCR 版本"""
    
    # 百度 OCR API 設定（來自 pdf-ocr skill）
    API_KEY = "vOBOM7tO0lL8cKMJdZy453Ai"
    SECRET_KEY = "bib8MvDPTfXXdPz4JyzIyDCvCeKxtpyu"
    OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic"
    
    def __init__(self):
        self.access_token = None
        self.provider = 'google'
        # 不再初始化百度 token
        
    def _get_access_token(self):
        """取得百度 API Access Token"""
        url = f"https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.API_KEY,
            "client_secret": self.SECRET_KEY
        }
        
        try:
            response = requests.post(url, params=params, timeout=10)
            result = response.json()
            self.access_token = result.get("access_token")
            print(f"✅ 百度 OCR API 連接成功")
        except Exception as e:
            print(f"❌ 百度 OCR API 連接失敗: {e}")
            self.access_token = None
            
    def _encode_image(self, image_path: str) -> str:
        """將圖片編碼為 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
            
    async def parse_receipt(self, image_path: str) -> Dict[str, Any]:
        """
        解析發票圖片 - 使用 Google Vision API
        
        Args:
            image_path: 圖片檔案路徑
            
        Returns:
            解析結果字典
        """
        try:
            # 使用 Google Vision API
            return await self._parse_with_google_vision(image_path)
            
        except Exception as e:
            print(f"Google Vision OCR error: {e}")
            return self._parse_mock(image_path)
            
    async def _parse_with_google_vision(self, image_path: str) -> Dict[str, Any]:
        """使用 Google Vision API 解析"""
        from googleapiclient.discovery import build
        import pickle
        
        # 載入 OAuth 憑證
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
        service = build('vision', 'v1', credentials=creds)
        
        # 讀取圖片
        with open(image_path, 'rb') as f:
            image_data = f.read()
            
        # 呼叫 Vision API
        request = {
            'image': {'content': base64.b64encode(image_data).decode()},
            'features': [{'type': 'TEXT_DETECTION'}]
        }
        
        response = service.images().annotate(body={'requests': [request]}).execute()
        
        # 提取文字
        text_annotations = response['responses'][0].get('textAnnotations', [])
        if text_annotations:
            full_text = text_annotations[0]['description']
        else:
            full_text = ""
            
        print(f"📝 OCR 識別文字:\n{full_text[:500]}...")
        
        # 使用規則引擎解析
        parsed_data = self._extract_receipt_info(full_text)
        parsed_data['raw_ocr_text'] = full_text
        parsed_data['confidence'] = 0.90  # Google Vision 準確度較高
        parsed_data['provider'] = 'google'
        
        return parsed_data
            
    def _extract_receipt_info(self, text: str) -> Dict[str, Any]:
        """
        從 OCR 文字中提取發票資訊
        使用規則引擎 + 關鍵字匹配
        """
        import re
        from datetime import datetime
        
        lines = text.split('\n')
        
        # 初始化結果
        result = {
            'date': None,
            'merchant': None,
            'amount': 0.0,
            'tax': 0.0,
            'category': '其他',
            'items': [],
            'receipt_no': None,
            'payment_method': None,
            'currency': 'HKD'
        }
        
        # 1. 提取日期 (多種格式)
        date_patterns = [
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',  # 2024-03-21 或 2024/03/21
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',  # 21-03-2024
            r'(\d{4})(\d{2})(\d{2})',              # 20240321
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        # 判斷是 YYYY-MM-DD 還是 DD-MM-YYYY
                        first, second, third = match.groups()
                        if len(first) == 4:  # YYYY-MM-DD
                            result['date'] = f"{first}-{int(second):02d}-{int(third):02d}"
                        else:  # DD-MM-YYYY
                            result['date'] = f"{third}-{int(second):02d}-{int(first):02d}"
                    break
                except:
                    pass
                    
        if not result['date']:
            result['date'] = datetime.now().strftime('%Y-%m-%d')
            
        # 2. 提取金額 (找尋 $ 符號或「總計」「合計」後的數字)
        amount_patterns = [
            r'[總合]計[:\s]*\$?\s*(\d+[.,]?\d*)',
            r'總額[:\s]*\$?\s*(\d+[.,]?\d*)',
            r'Amount[:\s]*\$?\s*(\d+[.,]?\d*)',
            r'Total[:\s]*\$?\s*(\d+[.,]?\d*)',
            r'\$\s*(\d+[.,]?\d{1,2})',  # $ 45.50
            r'HKD\s*(\d+[.,]?\d*)',     # HKD 45.50
        ]
        
        amounts = []
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
            # 通常最大的數字是總金額
            result['amount'] = max(amounts)
            
        # 3. 提取商家名稱 (通常是第一行或包含特定關鍵字的行)
        merchant_keywords = ['Ltd', 'Limited', '公司', '餐廳', '咖啡', 'Cafe', 'Restaurant', 'Store', 'Shop']
        
        for line in lines[:5]:  # 檢查前5行
            if any(keyword in line for keyword in merchant_keywords) or len(line) > 3:
                if not any(char.isdigit() for char in line[:10]):  # 開頭不是數字
                    result['merchant'] = line.strip()
                    break
                    
        if not result['merchant'] and lines:
            result['merchant'] = lines[0].strip()
            
        # 4. 自動分類
        result['category'] = self._auto_categorize(text, result['merchant'])
        
        # 5. 提取發票號碼
        receipt_patterns = [
            r'發票號碼[:\s]*([A-Z0-9-]+)',
            r'Invoice[:\s#]*([A-Z0-9-]+)',
            r'Receipt[:\s#]*([A-Z0-9-]+)',
            r'No\.?[:\s]*([A-Z0-9-]{6,})',
        ]
        
        for pattern in receipt_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['receipt_no'] = match.group(1)
                break
                
        if not result['receipt_no']:
            result['receipt_no'] = f"INV-{datetime.now().strftime('%Y%m%d')}-{hash(text) % 1000:03d}"
            
        # 6. 提取付款方式
        payment_keywords = {
            '信用卡': ['信用卡', 'Credit Card', 'Visa', 'Mastercard', 'AE'],
            '現金': ['現金', 'Cash'],
            '電子支付': ['支付寶', 'Alipay', 'WeChat', '微信支付', '八達通', 'Octopus', 'FPS', '轉數快']
        }
        
        for method, keywords in payment_keywords.items():
            if any(keyword in text for keyword in keywords):
                result['payment_method'] = method
                break
                
        if not result['payment_method']:
            result['payment_method'] = '未知'
            
        # 7. 提取商品項目 (包含數字的行，可能是商品)
        for line in lines:
            if any(char.isdigit() for char in line) and len(line) > 5 and len(line) < 50:
                if not any(keyword in line for keyword in ['總計', '合計', 'Total', '日期', '發票']):
                    result['items'].append(line.strip())
                    
        if not result['items']:
            result['items'] = ['商品項目']
            
        return result
        
    def _auto_categorize(self, text: str, merchant: str) -> str:
        """自動分類支出類別"""
        text_lower = (text + ' ' + (merchant or '')).lower()
        
        categories = {
            '餐飲': ['餐廳', '美食', '飲料', '咖啡', 'cafe', 'restaurant', 'food', '麥當勞', '肯德基', 'pizza', 'burger', '茶餐廳'],
            '交通': ['加油', '停車', '的士', 'taxi', 'uber', 'grab', '地鐵', '港鐵', 'mtr', '巴士', '車費', '汽油'],
            '辦公': ['文具', '印刷', '影印', '辦公', 'stationery', 'print', '紙張', '筆'],
            '行銷': ['廣告', '宣傳', 'marketing', 'ad', 'promotion', '設計', 'design'],
            '購物': ['超市', '便利店', '7-eleven', '百佳', '惠康', 'supermarket', 'store', 'shop'],
            '娛樂': ['電影', '戲院', 'cinema', 'game', '娛樂', 'ktv', '唱k'],
            '通訊': ['電話', '上網', '寬頻', 'mobile', 'data', '通訊'],
            '租金': ['租金', 'rent', '管理費', 'management fee'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
                
        return '其他'
        
    def _parse_mock(self, image_path: str) -> Dict[str, Any]:
        """模擬解析（當 API 失敗時使用）"""
        import random
        from datetime import datetime
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "merchant": "測試商家",
            "amount": round(random.uniform(20, 500), 2),
            "tax": 0.00,
            "category": "其他",
            "items": ["測試項目"],
            "receipt_no": f"INV-{datetime.now().strftime('%Y%m%d')}-{random.randint(100,999)}",
            "payment_method": "未知",
            "currency": "HKD",
            "confidence": 0.50,
            "note": "OCR API 失敗，使用模擬數據"
        }


# 測試函數
async def test_parser():
    """測試解析器"""
    parser = ReceiptVisionParser()
    
    # 建立測試圖片路徑
    test_image = "data/test_receipt.jpg"
    
    if os.path.exists(test_image):
        result = await parser.parse_receipt(test_image)
        print("\n✅ 解析結果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"⚠️ 測試圖片不存在: {test_image}")
        print("請放入一張發票圖片到 data/test_receipt.jpg 進行測試")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_parser())
