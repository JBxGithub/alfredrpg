"""
數據提取器 - 從 OCR/Markdown 提取記帳資訊
"""

import re
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class ReceiptData:
    """統一收據數據結構"""
    date: str
    merchant: str
    amount: float
    category: str
    note: str
    receipt_no: str
    source_type: str  # 'image' or 'pdf'
    raw_text: str = ''
    
    def to_dict(self) -> Dict:
        return {
            'date': self.date,
            'merchant': self.merchant,
            'amount': self.amount,
            'category': self.category,
            'note': self.note,
            'receipt_no': self.receipt_no,
            'source_type': self.source_type,
            'raw_text': self.raw_text
        }


def extract_amount(text: str) -> Optional[float]:
    """從文字提取金額 - 改進版支援大額數字"""
    if not text:
        return None
    
    # 清理文字：統一貨幣符號和格式
    cleaned_text = text.replace('HKD$', '').replace('HKD', '').replace('USD', '').replace('CNY', '').replace('RMB', '')
    
    # 匹配模式：優先匹配大額數字
    patterns = [
        # 租金/大額專用：200,000 格式
        r'(?:租金|月租|Rent|Total)[^\d]*([\d]{1,3}(?:,\d{3})+(?:\.\d{2})?)',
        # 標準格式：$200,000.00
        r'\$?\s*([\d]{1,3}(?:,\d{3})+(?:\.\d{2})?)',
        # 總計格式
        r'(?:total|amount|sum|總計|合計|金額)[:\s]*[$\s]*([\d,]+\.?\d*)',
        # 簡單數字
        r'\$?\s*([\d,]+\.\d{2})',
    ]
    
    found_amounts = []
    
    for pattern in patterns:
        matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
        for match in matches:
            try:
                # 移除逗號並轉換
                amount_str = match.replace(',', '').replace('$', '').strip()
                amount = float(amount_str)
                # 過濾明顯錯誤的金額
                if 0 < amount < 10000000:  # 提高上限至 1000萬
                    found_amounts.append(amount)
            except ValueError:
                continue
    
    # 返回最大的合理金額 (通常是租金/總計)
    if found_amounts:
        # 過濾極小值 (可能是數量而非金額)
        reasonable_amounts = [a for a in found_amounts if a > 100]
        if reasonable_amounts:
            return max(reasonable_amounts)
        return max(found_amounts)
    
    return None


def extract_date(text: str) -> str:
    """從文字提取日期"""
    if not text:
        return datetime.now().strftime('%Y/%m/%d')
    
    # 各種日期格式
    patterns = [
        # 2026/03/22, 2026-03-22
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
        # 22/03/2026, 22-03-2026 (日/月/年)
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        # 2026年3月22日
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        # Mar 22, 2026 或 22 Mar 2026
        r'(?:\d{1,2}\s+[A-Za-z]{3,}\s+\d{4}|\d{4}\s+[A-Za-z]{3,}\s+\d{1,2})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                groups = match.groups()
                if len(groups) == 3:
                    year, month, day = groups
                    # 判斷是 YYYY/MM/DD 還是 DD/MM/YYYY
                    if len(year) == 4:
                        return f"{year}/{int(month):02d}/{int(day):02d}"
                    else:
                        # DD/MM/YYYY 格式
                        day, month, year = groups
                        return f"{year}/{int(month):02d}/{int(day):02d}"
            except:
                continue
    
    return datetime.now().strftime('%Y/%m/%d')


def extract_merchant(text: str) -> str:
    """從文字提取商家名稱"""
    if not text:
        return '未知商家'
    
    lines = text.strip().split('\n')
    
    # 常見商家標識
    merchant_indicators = [
        'merchant', 'store', 'shop', 'restaurant', 'vendor', 'supplier',
        '商家', '商店', '餐廳', '門市', '公司', '有限公司'
    ]
    
    # 優先找包含關鍵字的行
    for line in lines[:10]:  # 檢查前10行
        line = line.strip()
        if any(indicator in line.lower() for indicator in merchant_indicators):
            # 清理並返回
            return line.replace('Merchant:', '').replace('Store:', '').strip()[:50]
    
    # 如果沒有找到，返回第一個非空行
    for line in lines:
        line = line.strip()
        if line and len(line) > 2 and not line.startswith('http'):
            return line[:50]
    
    return '未知商家'


def extract_receipt_no(text: str) -> str:
    """從文字提取發票/帳單號碼"""
    if not text:
        return ''
    
    patterns = [
        r'(?:receipt|invoice|bill|ref|no|number|#)[:\s#]*([A-Z0-9\-]+)',
        r'(?:發票號碼|帳單號碼|編號|單號)[:\s#]*([A-Z0-9\-]+)',
        r'#\s*([A-Z0-9\-]{4,})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ''


def infer_category(text: str, merchant: str = '') -> str:
    """根據文字內容推斷消費類別"""
    if not text:
        return '其他'
    
    text_lower = (text + ' ' + merchant).lower()
    
    # 類別關鍵字映射
    category_keywords = {
        '餐飲': ['restaurant', 'dining', 'food', 'meal', 'lunch', 'dinner', 'cafe', 'coffee', 
                '餐廳', '餐飲', '美食', '午餐', '晚餐', '咖啡', '茶餐廳', '酒樓', '麵館'],
        '交通': ['transport', 'taxi', 'uber', 'bus', 'train', 'subway', 'metro', 'fuel', 'petrol',
                '交通', '的士', '巴士', '地鐵', '火車', '汽油', '柴油', '停車'],
        '辦公': ['office', 'stationery', 'printing', 'supplies', '文具', '印刷', '辦公'],
        '通訊': ['phone', 'mobile', 'internet', 'telecom', '通訊', '電話', '手機', '網絡'],
        '軟件': ['software', 'subscription', 'api', 'license', '軟件', '訂閱', '授權'],
        '設備': ['equipment', 'computer', 'hardware', 'device', '設備', '電腦', '硬件'],
        '廣告': ['advertising', 'marketing', 'ads', 'promotion', '廣告', '行銷', '推廣'],
        '租金': ['rent', 'lease', '租金', '租賃'],
        '保險': ['insurance', '保險'],
        '稅費': ['tax', 'fee', 'rates', '稅', '費用'],
        '賠償': ['claim', 'insurance claim', '賠償'],
        '差旅': ['travel', 'hotel', 'accommodation', 'flight', '差旅', '酒店', '機票'],
        '薪資': ['salary', 'wage', 'payroll', '薪資', '工資'],
        '淘寶': ['taobao', '淘宝', '淘寶', 'alibaba', '天貓'],
    }
    
    for category, keywords in category_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return category
    
    return '其他'


def extract_from_ocr_text(ocr_text: str) -> ReceiptData:
    """
    從 OCR 文字提取收據資訊 (圖片發票)
    
    Args:
        ocr_text: AI Vision OCR 結果
    
    Returns:
        ReceiptData 對象
    """
    amount = extract_amount(ocr_text) or 0.0
    date = extract_date(ocr_text)
    merchant = extract_merchant(ocr_text)
    receipt_no = extract_receipt_no(ocr_text)
    category = infer_category(ocr_text, merchant)
    
    return ReceiptData(
        date=date,
        merchant=merchant,
        amount=amount,
        category=category,
        note='',
        receipt_no=receipt_no,
        source_type='image',
        raw_text=ocr_text[:500]  # 保留前500字元作為參考
    )


def extract_from_markdown(md_text: str) -> ReceiptData:
    """
    從 Markdown 提取帳單資訊 (PDF 帳單)
    
    Args:
        md_text: PDF-to-Markdown 結果
    
    Returns:
        ReceiptData 對象
    """
    amount = extract_amount(md_text) or 0.0
    date = extract_date(md_text)
    merchant = extract_merchant(md_text)
    receipt_no = extract_receipt_no(md_text)
    category = infer_category(md_text, merchant)
    
    # PDF 通常是帳單，備註可以包含帳單期間
    note = 'PDF帳單'
    
    return ReceiptData(
        date=date,
        merchant=merchant,
        amount=amount,
        category=category,
        note=note,
        receipt_no=receipt_no,
        source_type='pdf',
        raw_text=md_text[:500]
    )
