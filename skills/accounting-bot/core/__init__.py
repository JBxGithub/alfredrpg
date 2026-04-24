# Accounting Bot Core Modules
from .classifier import classify_file, get_file_info, is_supported_file
from .extractor import extract_from_ocr_text, extract_from_markdown, ReceiptData
from .sheets_writer import write_to_sheets, get_sheets_service

__all__ = [
    'classify_file',
    'get_file_info',
    'is_supported_file',
    'extract_from_ocr_text',
    'extract_from_markdown',
    'ReceiptData',
    'write_to_sheets',
    'get_sheets_service',
]
_all__ = [
    'classify_file',
    'get_file_info',
    'extract_from_ocr_text',
    'extract_from_markdown',
    'ReceiptData',
    'write_to_sheets',
    'get_pnl_category',
    'get_pnl_type',
    'simplify_merchant',
    'format_date_for_sheets',
    'process_accounting_entry',
]


async def process_accounting_entry(
    file_path: str,
    ocr_text: str = None,
    chat_id: str = None,
    sender: str = None
) -> str:
    """
    全自動記帳入口 - 統一處理圖片或 PDF
    
    這是主要的入口函數，由 OpenClaw 在收到檔案時調用。
    
    Args:
        file_path: 檔案路徑
        ocr_text: OCR 結果文字 (圖片時由 OpenClaw image tool 提供)
        chat_id: WhatsApp 群組 ID
        sender: 發送者名稱
    
    Returns:
        處理結果訊息
    """
    from datetime import datetime
    
    print(f"🤖 [{datetime.now().strftime('%H:%M:%S')}] 自動記帳流程啟動")
    print(f"   📁 檔案: {file_path}")
    
    # Step 1: 判斷檔案類型
    file_type = classify_file(file_path)
    print(f"   📋 類型: {file_type}")
    
    if file_type == 'unknown':
        return "❌ 不支援的檔案類型。請上傳圖片 (JPG/PNG) 或 PDF 帳單。"
    
    # Step 2: 提取數據
    print("   🔍 提取數據...")
    
    if file_type == 'image':
        if not ocr_text:
            return "_NEEDS_OCR_"  # 需要 OpenClaw 調用 image tool
        receipt_data = extract_from_ocr_text(ocr_text)
    else:  # PDF
        # 調用 pdf-to-markdown skill
        print("   📄 轉換 PDF to Markdown...")
        try:
            import subprocess
            result = subprocess.run(
                ['bash', '-c', f'cd ~/openclaw_workspace/skills/pdf-to-markdown && scripts/script.sh md "{file_path}"'],
                capture_output=True,
                text=True,
                timeout=30
            )
            md_text = result.stdout
            receipt_data = extract_from_markdown(md_text)
        except Exception as e:
            return f"❌ PDF 處理失敗: {str(e)}"
    
    # Step 3: P&L 分類
    print(f"   📊 分類: {receipt_data.category}")
    pnl_category = get_pnl_category(receipt_data.category)
    pnl_type = get_pnl_type(receipt_data.category)
    
    # Step 4: 寫入 Sheets
    print("   📝 寫入 Google Sheets...")
    result = write_to_sheets(
        date=format_date_for_sheets(receipt_data.date),
        pnl_type=pnl_type,
        pnl_category=pnl_category,
        merchant=simplify_merchant(receipt_data.merchant),
        amount=receipt_data.amount,
        note=receipt_data.note,
        receipt_no=receipt_data.receipt_no
    )
    
    # Step 5: 回覆結果
    if result['success']:
        return f"""✅ 記帳完成！

🧾 {receipt_data.merchant}
💰 ${receipt_data.amount:.2f}
📅 {receipt_data.date}
📊 {pnl_type} - {pnl_category}
📝 {receipt_data.note or '(無備註)'}

已寫入 Google Sheets 📊
{result['url']}"""
    else:
        return f"❌ 記帳失敗: {result['message']}"
