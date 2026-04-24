"""
檔案類型分類器 - 自動判斷輸入類型
"""

import os
from pathlib import Path
from typing import Literal

FileType = Literal['image', 'pdf', 'unknown']

# 支援的圖片格式
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}

# 支援的文件格式
PDF_EXTENSIONS = {'.pdf'}


def classify_file(file_path: str) -> FileType:
    """
    自動判斷檔案類型
    
    Args:
        file_path: 檔案路徑
    
    Returns:
        'image', 'pdf', 或 'unknown'
    
    Examples:
        >>> classify_file('/path/to/receipt.jpg')
        'image'
        >>> classify_file('/path/to/bill.pdf')
        'pdf'
    """
    if not file_path or not os.path.exists(file_path):
        return 'unknown'
    
    path = Path(file_path)
    extension = path.suffix.lower()
    
    if extension in IMAGE_EXTENSIONS:
        return 'image'
    elif extension in PDF_EXTENSIONS:
        return 'pdf'
    else:
        return 'unknown'


def is_supported_file(file_path: str) -> bool:
    """
    檢查是否為支援的檔案類型
    
    Args:
        file_path: 檔案路徑
    
    Returns:
        True 如果支援，False 如果不支援
    """
    return classify_file(file_path) != 'unknown'


def get_file_info(file_path: str) -> dict:
    """
    取得檔案詳細資訊
    
    Args:
        file_path: 檔案路徑
    
    Returns:
        包含檔案資訊的字典
    """
    if not file_path or not os.path.exists(file_path):
        return {'error': 'File not found'}
    
    path = Path(file_path)
    stat = path.stat()
    
    return {
        'path': str(path.absolute()),
        'name': path.name,
        'extension': path.suffix.lower(),
        'type': classify_file(file_path),
        'size_bytes': stat.st_size,
        'size_mb': round(stat.st_size / (1024 * 1024), 2),
        'supported': is_supported_file(file_path)
    }
