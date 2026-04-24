"""
Hash-Anchored Edit - 哈希錨定編輯系統

提供可靠的文件編輯機制，防止衝突和數據損壞
"""

from .editor import (
    HashAnchoredEditor,
    LineAnchor,
    EditOperation,
    EditResult,
    EditResultData,
    compute_line_hash,
    compute_file_hash,
    compute_content_hash,
    edit_file_line,
    get_line_hash,
)

__all__ = [
    'HashAnchoredEditor',
    'LineAnchor',
    'EditOperation',
    'EditResult',
    'EditResultData',
    'compute_line_hash',
    'compute_file_hash',
    'compute_content_hash',
    'edit_file_line',
    'get_line_hash',
]
