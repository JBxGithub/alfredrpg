"""
Accounting Bot - 統一入口
OpenClaw 調用的主要接口 - 支援圖片與 PDF
"""

import sys
from pathlib import Path

# 添加 skill 路徑
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

from core.classifier import classify_file
from core.extractor import extract_from_ocr_text, extract_from_markdown, ReceiptData, extract_receipt_no
from core.sheets_writer import write_to_sheets
from config.pnl_categories import get_pnl_category, get_pnl_type, simplify_merchant, format_date_for_sheets

# PDF 處理依賴
try:
    from pdf2image import convert_from_path
    import pytesseract
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

__version__ = '1.1.0'
__author__ = 'Alfred (呀鬼)'

# Tesseract 路徑 (Windows)
TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


async def process_image_receipt(image_path: str, ocr_text: str = None, chat_id: str = None, sender: str = None) -> str:
    """
    處理圖片發票 - 使用本地 pytesseract OCR
    
    Args:
        image_path: 圖片路徑
        ocr_text: 可選，如提供則直接使用；否則用 pytesseract
        chat_id: WhatsApp 群組 ID
        sender: 發送者
    
    Returns:
        處理結果訊息
    """
    from datetime import datetime
    from PIL import Image
    from core.tracker import is_file_processed, mark_file_processed
    
    print(f"🤖 [{datetime.now().strftime('%H:%M:%S')}] 處理圖片發票")
    
    # 檢查是否已處理
    if is_file_processed(image_path):
        print("   ⏭️  檔案已處理，跳過")
        return "⏭️  此檔案已記錄過"
    
    # 設定 tesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    
    try:
        # 使用本地 OCR (pytesseract)
        if ocr_text:
            # 如提供外部 OCR 文字，直接使用
            text = ocr_text
            print("   🔍 使用提供的 OCR 文字")
        else:
            # 否則使用本地 pytesseract
            print("   🔍 使用 pytesseract OCR...")
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='chi_tra+eng')
            print(f"   ✅ OCR 完成，提取 {len(text)} 字元")
        
        if not text or len(text) < 20:
            return "❌ OCR 識別失敗，內容過少"
        
        # 提取數據
        receipt_data = extract_from_ocr_text(text)
        
        # P&L 分類
        pnl_category = get_pnl_category(receipt_data.category)
        pnl_type = get_pnl_type(receipt_data.category)
        
        # 寫入 Sheets
        result = write_to_sheets(
            date=format_date_for_sheets(receipt_data.date),
            pnl_type=pnl_type,
            pnl_category=pnl_category,
            merchant=simplify_merchant(receipt_data.merchant),
            amount=receipt_data.amount,
            note=receipt_data.note,
            receipt_no=receipt_data.receipt_no
        )
        
        if result['success']:
            # 標記為已處理
            mark_file_processed(image_path, receipt_data.receipt_no, receipt_data.amount)
            
            return f"""✅ 發票已記錄！

🧾 {receipt_data.merchant}
💰 ${receipt_data.amount:.2f}
📅 {receipt_data.date}
📊 {pnl_type} - {pnl_category}

📎 {result['url']}"""
        else:
            return f"❌ 失敗: {result['message']}"
            
    except Exception as e:
        return f"❌ 圖片處理失敗: {str(e)}"


async def process_pdf_bill(file_path: str, chat_id: str = None, sender: str = None) -> str:
    """
    處理 PDF 帳單 - 完整流程: PDF → 圖片 → OCR → 記帳
    
    Args:
        file_path: PDF 路徑
        chat_id: WhatsApp 群組 ID
        sender: 發送者
    
    Returns:
        處理結果訊息
    """
    from datetime import datetime
    import re
    from core.tracker import is_file_processed, mark_file_processed
    
    print(f"🤖 [{datetime.now().strftime('%H:%M:%S')}] 處理 PDF 帳單")
    
    # 檢查是否已處理 (防止重覆)
    if is_file_processed(file_path):
        print("   ⏭️  檔案已處理，跳過")
        return "⏭️  此檔案已記錄過"
    
    if not PDF_SUPPORT:
        return "❌ PDF 支援未就緒，請安裝 pdf2image 與 pytesseract"
    
    # 設定 tesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    
    try:
        # Step 1: PDF → 圖片
        print("   📄 PDF → 圖片轉換...")
        images = convert_from_path(file_path, first_page=1, last_page=1, dpi=200)
        
        if not images:
            return "❌ PDF 轉換失敗，無法提取頁面"
        
        # Step 2: OCR 識別
        print("   🔍 OCR 識別...")
        text = pytesseract.image_to_string(images[0], lang='chi_tra+eng')
        
        if not text or len(text) < 50:
            return "❌ OCR 識別失敗，內容過少"
        
        # Step 3: 從檔名提取發票號碼 (更可靠)
        # 福澤2026年5月1日至5月31日租單發票00031---xxx.pdf → 00031
        filename_receipt_no = ''
        filename_match = re.search(r'發票(\d+)', Path(file_path).name)
        if filename_match:
            filename_receipt_no = filename_match.group(1)
        
        # 從 OCR 提取發票號碼 (備用)
        ocr_receipt_no = extract_receipt_no(text)
        
        # 優先使用檔名提取的號碼
        receipt_no = filename_receipt_no if filename_receipt_no else ocr_receipt_no
        
        # Step 4: 提取數據
        print("   📊 提取帳單資訊...")
        receipt_data = extract_from_ocr_text(text)
        
        # 強制分類邏輯：檢查是否為租單
        is_rent = '租' in text or 'rent' in text.lower() or '租單' in Path(file_path).name
        
        if is_rent:
            category = '租金'
            merchant = '福澤發展建設有限公司 (租單)'
        elif '電' in text or '中電' in text or 'CLP' in text.upper():
            category = '水電'
            merchant = '中電 (CLP)'
        elif '水' in text or '水務' in text:
            category = '水電'
            merchant = '水務署'
        elif '煤氣' in text:
            category = '水電'
            merchant = '煤氣公司'
        else:
            category = receipt_data.category
            merchant = receipt_data.merchant
        
        # P&L 分類
        pnl_category = get_pnl_category(category)
        pnl_type = get_pnl_type(category)
        
        # Step 5: 寫入 Sheets
        print("   📝 寫入 Google Sheets...")
        result = write_to_sheets(
            date=format_date_for_sheets(receipt_data.date),
            pnl_type=pnl_type,
            pnl_category=pnl_category,
            merchant=simplify_merchant(merchant),
            amount=receipt_data.amount if receipt_data.amount > 0 else 0,
            note=f"PDF帳單: {receipt_data.note}",
            receipt_no=receipt_no
        )
        
        if result['success']:
            # 標記為已處理
            mark_file_processed(file_path, receipt_no, receipt_data.amount)
            
            return f"""✅ 帳單已記錄！

🧾 {merchant}
💰 ${receipt_data.amount:.2f}
📅 {receipt_data.date}
📊 {pnl_type} - {pnl_category}
📝 發票號碼: {receipt_no}

📎 {result['url']}"""
        else:
            return f"❌ 失敗: {result['message']}"
            
    except Exception as e:
        return f"❌ PDF 處理失敗: {str(e)}"


async def process_auto(file_path: str, ocr_text: str = None, chat_id: str = None, sender: str = None) -> str:
    """
    自動判斷並處理 (統一入口) - 全部使用本地 pytesseract
    
    Args:
        file_path: 檔案路徑
        ocr_text: 可選，如提供則直接使用
        chat_id: WhatsApp 群組 ID
        sender: 發送者
    
    Returns:
        處理結果訊息
    """
    file_type = classify_file(file_path)
    
    if file_type == 'image':
        # 圖片：使用本地 pytesseract (不再依賴外部 OCR)
        return await process_image_receipt(file_path, ocr_text, chat_id, sender)
    elif file_type == 'pdf':
        # PDF：使用本地 pdf2image + pytesseract
        return await process_pdf_bill(file_path, chat_id, sender)
    else:
        return "❌ 不支援的檔案類型。請上傳圖片 (JPG/PNG) 或 PDF 帳單。"


# 供 OpenClaw 直接調用的函數
process_receipt = process_image_receipt
process_bill = process_pdf_bill
process_accounting_entry = process_auto

__all__ = [
    'process_auto',
    'process_receipt',
    'process_bill',
    'process_accounting_entry',
    'process_image_receipt',
    'process_pdf_bill',
]
