"""
Auto Receipt Processor - Cron Job 整合版
整合 accounting-bot skill 與現有記帳系統

觸發條件：
1. WhatsApp 群組收到圖片/PDF
2. Cron 定時檢查未處理檔案
3. 手動批次處理

使用方法：
    python auto_receipt_processor.py --mode whatsapp --file <path>
    python auto_receipt_processor.py --mode batch --dir <directory>
    python auto_receipt_processor.py --mode cron
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# 添加 accounting-bot skill 路徑
SKILL_DIR = Path(r'C:\Users\BurtClaw\openclaw_workspace\private skills\accounting-bot')
sys.path.insert(0, str(SKILL_DIR))

# 添加現有專案路徑
PROJECT_DIR = Path(r'C:\Users\BurtClaw\openclaw_workspace\projects\accounting-automation')
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / 'src'))

from __init__ import process_auto, process_image_receipt, process_pdf_bill

# 設定檔
SPREADSHEET_ID = '1BQXOvBoovN27N5nwUC_qtNqc7hgcw05WUB89yVpo1yk'
WHATSAPP_GROUP = '120363426808630578@g.us'


async def process_whatsapp_file(file_path: str, sender: str = 'Burtoddjobs') -> str:
    """
    處理 WhatsApp 收到的檔案
    
    Args:
        file_path: 檔案路徑
        sender: 發送者名稱
    
    Returns:
        處理結果訊息
    """
    print(f"🤖 [{datetime.now().strftime('%H:%M:%S')}] 處理 WhatsApp 檔案")
    print(f"   📁 {file_path}")
    
    # 使用統一入口處理
    result = await process_auto(
        file_path=file_path,
        ocr_text=None,  # PDF 會自動處理，圖片需要外部 OCR
        chat_id=WHATSAPP_GROUP,
        sender=sender
    )
    
    if result == "_NEEDS_OCR_":
        # 圖片需要 AI Vision OCR
        print("   🔍 需要 OCR，請使用 OpenClaw image tool")
        return "_NEEDS_OCR_"
    
    return result


async def process_with_ocr(file_path: str, ocr_text: str, sender: str = 'Burtoddjobs') -> str:
    """
    處理圖片 (已提供 OCR 文字)
    
    Args:
        file_path: 圖片路徑
        ocr_text: AI Vision OCR 結果
        sender: 發送者名稱
    
    Returns:
        處理結果訊息
    """
    return await process_image_receipt(
        image_path=file_path,
        ocr_text=ocr_text,
        chat_id=WHATSAPP_GROUP,
        sender=sender
    )


async def batch_process(directory: str, file_type: str = None):
    """
    批次處理目錄中的檔案
    
    Args:
        directory: 目錄路徑
        file_type: 指定檔案類型 (image/pdf/all)
    """
    from core.classifier import classify_file
    
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"❌ 目錄不存在: {directory}")
        return
    
    # 收集檔案
    files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.pdf']:
        files.extend(dir_path.glob(ext))
    
    print(f"🤖 批次處理: 發現 {len(files)} 個檔案")
    
    success_count = 0
    fail_count = 0
    
    for file_path in files:
        file_type_detected = classify_file(str(file_path))
        
        if file_type and file_type != 'all' and file_type_detected != file_type:
            continue
        
        print(f"\n📄 {file_path.name}")
        
        try:
            result = await process_auto(
                file_path=str(file_path),
                chat_id=WHATSAPP_GROUP
            )
            
            if "✅" in result:
                success_count += 1
                print("   ✅ 成功")
            elif result == "_NEEDS_OCR_":
                print("   ⏭️  跳過 (需要 OCR)")
            else:
                fail_count += 1
                print(f"   ❌ 失敗: {result[:50]}")
                
        except Exception as e:
            fail_count += 1
            print(f"   ❌ 錯誤: {e}")
    
    print(f"\n{'='*50}")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失敗: {fail_count}")
    print(f"⏭️  跳過: {len(files) - success_count - fail_count}")


async def cron_check():
    """Cron job: 檢查未處理檔案"""
    inbox_dir = Path(r'C:\Users\BurtClaw\.openclaw\media\inbound')
    
    if not inbox_dir.exists():
        print("❌ 收件目錄不存在")
        return
    
    # 檢查最近 1 小時的檔案
    from datetime import timedelta
    cutoff_time = datetime.now() - timedelta(hours=1)
    
    recent_files = [
        f for f in inbox_dir.iterdir()
        if f.is_file() and f.stat().st_mtime > cutoff_time.timestamp()
    ]
    
    if recent_files:
        print(f"🤖 Cron: 發現 {len(recent_files)} 個新檔案")
        for file_path in recent_files:
            result = await process_whatsapp_file(str(file_path))
            print(f"   {file_path.name}: {'✅' if '✅' in result else '❌'}")
    else:
        print("🤖 Cron: 無新檔案")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description='Auto Receipt Processor')
    parser.add_argument('--mode', choices=['whatsapp', 'batch', 'cron'], 
                       default='whatsapp', help='運作模式')
    parser.add_argument('--file', help='單一檔案路徑')
    parser.add_argument('--dir', help='批次處理目錄')
    parser.add_argument('--type', choices=['image', 'pdf', 'all'], 
                       default='all', help='檔案類型篩選')
    parser.add_argument('--ocr-text', help='OCR 文字 (圖片模式)')
    
    args = parser.parse_args()
    
    if args.mode == 'whatsapp':
        if not args.file:
            print("❌ 請指定 --file")
            return
        
        if args.ocr_text:
            # 圖片模式 (已提供 OCR)
            result = asyncio.run(process_with_ocr(args.file, args.ocr_text))
        else:
            # 自動判斷 (PDF 或需要 OCR 的圖片)
            result = asyncio.run(process_whatsapp_file(args.file))
        
        print(result)
    
    elif args.mode == 'batch':
        directory = args.dir or r'C:\Users\BurtClaw\.openclaw\media\inbound'
        asyncio.run(batch_process(directory, args.type))
    
    elif args.mode == 'cron':
        asyncio.run(cron_check())


if __name__ == "__main__":
    main()
