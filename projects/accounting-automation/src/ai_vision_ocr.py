"""
AI Vision OCR - 使用 OpenClaw 內建的 Image 工具
無需外部 API，直接使用 AI Vision
"""

import os
import re
import json
from datetime import datetime
from typing import Dict, Any, Optional


class AIVisionOCR:
    """使用 AI Vision 解析發票"""
    
    def __init__(self):
        pass
    
    def parse_receipt(self, image_path: str) -> Dict[str, Any]:
        """
        解析發票圖片
        
        這個方法會被 OpenClaw 主會話調用，
        使用內建的 image 工具分析圖片
        """
        # 這裡返回一個標記，表示需要外部調用 AI Vision
        # 實際的 OCR 會在 OpenClaw 會話中執行
        return {
            '_needs_ai_vision': True,
            'image_path': image_path
        }


# 供 OpenClaw 使用的解析函數
def extract_receipt_info_from_text(ocr_text: str) -> Dict[str, Any]:
    """
    從 OCR 文字中提取發票資訊
    
    這個函數處理 AI Vision 返回的文字
    """
    text = ocr_text
    lines = text.split('\n')
    
    result = {
        'date': None,
        'merchant': None,
        'amount': 0.0,
        'category': '其他',
        'receipt_no': None,
        'payment_method': '未知',
        'items': [],
        'confidence': 0.90
    }
    
    # 提取日期
    date_patterns = [
        r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',
        r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                groups = match.groups()
                if len(groups[0]) == 4:
                    result['date'] = f"{groups[0]}/{int(groups[1]):02d}/{int(groups[2]):02d}"
                else:
                    result['date'] = f"{groups[2]}/{int(groups[1]):02d}/{int(groups[0]):02d}"
                break
            except:
                pass
    
    if not result['date']:
        result['date'] = datetime.now().strftime('%Y/%m/%d')
    
    # 提取金額
    amounts = []
    amount_patterns = [
        r'[總合]計[:\s]*\$?\s*(\d+[.,]?\d*)',
        r'Total[:\s]*\$?\s*(\d+[.,]?\d*)',
        r'總額[:\s]*\$?\s*(\d+[.,]?\d*)',
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
    
    # 提取商家
    for line in lines[:5]:
        line = line.strip()
        if len(line) > 2 and not line.isdigit():
            if any(keyword in line for keyword in ['Ltd', 'Limited', '公司', '餐廳', 'Cafe', 'Restaurant', 'Store', 'Shop', '商場']):
                result['merchant'] = line
                break
    
    if not result['merchant'] and lines:
        result['merchant'] = lines[0].strip()[:30]
    
    # 自動分類
    result['category'] = auto_categorize(text, result['merchant'])
    
    # 提取發票號碼
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
    
    return result


def auto_categorize(text: str, merchant: str) -> str:
    """自動分類支出"""
    text_lower = (text + ' ' + (merchant or '')).lower()
    
    categories = {
        '餐飲': ['餐廳', '美食', '飲料', '咖啡', 'cafe', 'restaurant', 'food', '麥當勞', '麵館', '茶餐廳', '小吃', '快餐'],
        '交通': ['加油', '停車', '的士', 'taxi', 'uber', '地鐵', '港鐵', 'mtr', '巴士', '車費', '汽油', '交通'],
        '辦公': ['文具', '印刷', '影印', '辦公', 'stationery', 'print', '紙張', '筆', '電腦', '軟件'],
        '商務': ['商務', '業務', '客戶', '會議', '商業'],
        '購物': ['超市', '便利店', '7-eleven', '百佳', '惠康', 'supermarket', 'store', 'shop'],
        '娛樂': ['電影', '戲院', 'cinema', 'ktv', '唱k', '娛樂'],
    }
    
    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            return category
    
    return '其他'
