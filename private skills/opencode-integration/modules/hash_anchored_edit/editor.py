"""
Hash-Anchored Edit - 哈希錨定編輯系統
提供可靠的文件編輯機制，防止衝突和數據損壞
"""

import zlib
import base64
import hashlib
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class EditResult(Enum):
    """編輯結果狀態"""
    SUCCESS = "success"
    HASH_MISMATCH = "hash_mismatch"
    LINE_NOT_FOUND = "line_not_found"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    VALIDATION_ERROR = "validation_error"


@dataclass
class LineAnchor:
    """行錨點 - 標識特定行的哈希"""
    line_number: int
    hash: str
    content: str
    
    def verify(self, current_content: str) -> bool:
        """驗證行內容是否匹配"""
        current_hash = compute_line_hash(current_content)
        return current_hash == self.hash


@dataclass
class EditOperation:
    """編輯操作"""
    operation_type: str  # 'replace', 'insert', 'delete', 'append'
    target_anchor: Optional[LineAnchor] = None
    start_line: int = 0
    end_line: int = 0
    new_content: str = ""
    expected_hashes: List[str] = None
    
    def __post_init__(self):
        if self.expected_hashes is None:
            self.expected_hashes = []


@dataclass
class EditResultData:
    """編輯結果數據"""
    success: bool
    result: EditResult
    message: str
    affected_lines: List[int]
    new_hashes: Dict[int, str]
    old_content: Optional[str] = None


def compute_line_hash(line_content: str, hash_length: int = 3) -> str:
    """
    計算行內容的短哈希
    
    Args:
        line_content: 行內容
        hash_length: 哈希長度（默認 3 字符）
    
    Returns:
        短哈希字符串
    """
    # 標準化：移除尾部換行符
    normalized = line_content.rstrip('\n\r')
    
    # 使用 CRC32 計算哈希（快速）
    hash_value = zlib.crc32(normalized.encode('utf-8')) & 0xffffffff
    
    # 轉換為 Base32 編碼
    base32_hash = base64.b32encode(hash_value.to_bytes(4, 'big')).decode('ascii')
    
    return base32_hash[:hash_length].lower()


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    計算文件整體哈希（SHA-256）
    
    Args:
        file_path: 文件路徑
    
    Returns:
        SHA-256 哈希值
    """
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_content_hash(content: str) -> str:
    """
    從內容計算文件哈希
    
    Args:
        content: 文件內容
    
    Returns:
        SHA-256 哈希值
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


class FileVersion:
    """文件版本快照"""
    
    def __init__(self, file_path: Union[str, Path], content: str = None):
        self.file_path = Path(file_path)
        if content is None:
            content = self._read_file()
        self.content = content
        self.file_hash = compute_content_hash(content)
        self.line_hashes = self._compute_line_hashes()
        self.lines = content.split('\n')
    
    def _read_file(self) -> str:
        """讀取文件內容"""
        if not self.file_path.exists():
            return ""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _compute_line_hashes(self) -> Dict[int, str]:
        """計算所有行的哈希"""
        lines = self.content.split('\n')
        return {i+1: compute_line_hash(line) for i, line in enumerate(lines)}
    
    def verify_line(self, line_number: int, expected_hash: str) -> bool:
        """驗證特定行是否未改變"""
        current_hash = self.line_hashes.get(line_number)
        return current_hash == expected_hash
    
    def verify_range(self, start: int, end: int, hashes: List[str]) -> bool:
        """驗證行範圍是否未改變"""
        for i, hash_val in enumerate(hashes):
            line_num = start + i
            if self.line_hashes.get(line_num) != hash_val:
                return False
        return True
    
    def get_line_content(self, line_number: int) -> Optional[str]:
        """獲取特定行內容"""
        if 1 <= line_number <= len(self.lines):
            return self.lines[line_number - 1]
        return None
    
    def create_anchor(self, line_number: int) -> Optional[LineAnchor]:
        """為特定行創建錨點"""
        content = self.get_line_content(line_number)
        if content is None:
            return None
        hash_val = self.line_hashes.get(line_number, "")
        return LineAnchor(line_number, hash_val, content)


class HashAnchoredEditor:
    """
    哈希錨定編輯器
    
    提供基於哈希驗證的可靠文件編輯功能
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        初始化編輯器
        
        Args:
            strict_mode: 是否啟用嚴格模式（哈希不匹配時拒絕編輯）
        """
        self.strict_mode = strict_mode
        self.versions: Dict[str, FileVersion] = {}
    
    def read_file(self, file_path: Union[str, Path]) -> FileVersion:
        """
        讀取文件並創建版本快照
        
        Args:
            file_path: 文件路徑
        
        Returns:
            FileVersion: 文件版本快照
        """
        file_path = Path(file_path)
        version = FileVersion(file_path)
        self.versions[str(file_path)] = version
        return version
    
    def edit_line(self, file_path: Union[str, Path], line_number: int, 
                  expected_hash: str, new_content: str) -> EditResultData:
        """
        編輯單行（基於哈希驗證）
        
        Args:
            file_path: 文件路徑
            line_number: 行號（1-based）
            expected_hash: 期望的行哈希
            new_content: 新內容
        
        Returns:
            EditResultData: 編輯結果
        """
        file_path = Path(file_path)
        
        # 檢查文件是否存在
        if not file_path.exists():
            return EditResultData(
                success=False,
                result=EditResult.FILE_NOT_FOUND,
                message=f"文件不存在: {file_path}",
                affected_lines=[],
                new_hashes={}
            )
        
        # 讀取當前版本
        current_version = self.read_file(file_path)
        
        # 驗證行號
        if line_number < 1 or line_number > len(current_version.lines):
            return EditResultData(
                success=False,
                result=EditResult.LINE_NOT_FOUND,
                message=f"行號 {line_number} 超出範圍 (1-{len(current_version.lines)})",
                affected_lines=[],
                new_hashes={}
            )
        
        # 驗證哈希
        current_hash = current_version.line_hashes.get(line_number)
        if current_hash != expected_hash:
            if self.strict_mode:
                return EditResultData(
                    success=False,
                    result=EditResult.HASH_MISMATCH,
                    message=f"哈希不匹配: 期望 {expected_hash}, 實際 {current_hash}",
                    affected_lines=[line_number],
                    new_hashes={},
                    old_content=current_version.get_line_content(line_number)
                )
        
        # 執行編輯
        old_content = current_version.content
        lines = current_version.lines.copy()
        lines[line_number - 1] = new_content
        new_file_content = '\n'.join(lines)
        
        # 寫入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)
        except PermissionError:
            return EditResultData(
                success=False,
                result=EditResult.PERMISSION_DENIED,
                message=f"無權限寫入文件: {file_path}",
                affected_lines=[],
                new_hashes={}
            )
        
        # 計算新哈希
        new_version = FileVersion(file_path, new_file_content)
        new_hashes = {line_number: new_version.line_hashes[line_number]}
        
        # 更新版本緩存
        self.versions[str(file_path)] = new_version
        
        return EditResultData(
            success=True,
            result=EditResult.SUCCESS,
            message=f"成功編輯第 {line_number} 行",
            affected_lines=[line_number],
            new_hashes=new_hashes,
            old_content=old_content
        )
    
    def insert_line(self, file_path: Union[str, Path], after_line: int,
                    new_content: str) -> EditResultData:
        """
        在指定行之後插入新行
        
        Args:
            file_path: 文件路徑
            after_line: 插入位置的行號（0 表示文件開頭）
            new_content: 新行內容
        
        Returns:
            EditResultData: 編輯結果
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return EditResultData(
                success=False,
                result=EditResult.FILE_NOT_FOUND,
                message=f"文件不存在: {file_path}",
                affected_lines=[],
                new_hashes={}
            )
        
        current_version = self.read_file(file_path)
        lines = current_version.lines.copy()
        
        # 在指定位置後插入
        lines.insert(after_line, new_content)
        new_file_content = '\n'.join(lines)
        
        # 寫入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)
        except PermissionError:
            return EditResultData(
                success=False,
                result=EditResult.PERMISSION_DENIED,
                message=f"無權限寫入文件: {file_path}",
                affected_lines=[],
                new_hashes={}
            )
        
        # 計算新哈希
        new_version = FileVersion(file_path, new_file_content)
        new_line_number = after_line + 1
        new_hashes = {new_line_number: new_version.line_hashes[new_line_number]}
        
        self.versions[str(file_path)] = new_version
        
        return EditResultData(
            success=True,
            result=EditResult.SUCCESS,
            message=f"成功在第 {after_line} 行後插入新行",
            affected_lines=list(range(after_line + 1, len(lines) + 1)),
            new_hashes=new_hashes
        )
    
    def delete_line(self, file_path: Union[str, Path], line_number: int,
                    expected_hash: str) -> EditResultData:
        """
        刪除指定行（基於哈希驗證）
        
        Args:
            file_path: 文件路徑
            line_number: 行號
            expected_hash: 期望的行哈希
        
        Returns:
            EditResultData: 編輯結果
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return EditResultData(
                success=False,
                result=EditResult.FILE_NOT_FOUND,
                message=f"文件不存在: {file_path}",
                affected_lines=[],
                new_hashes={}
            )
        
        current_version = self.read_file(file_path)
        
        # 驗證行號
        if line_number < 1 or line_number > len(current_version.lines):
            return EditResultData(
                success=False,
                result=EditResult.LINE_NOT_FOUND,
                message=f"行號 {line_number} 超出範圍",
                affected_lines=[],
                new_hashes={}
            )
        
        # 驗證哈希
        current_hash = current_version.line_hashes.get(line_number)
        if current_hash != expected_hash and self.strict_mode:
            return EditResultData(
                success=False,
                result=EditResult.HASH_MISMATCH,
                message=f"哈希不匹配: 期望 {expected_hash}, 實際 {current_hash}",
                affected_lines=[line_number],
                new_hashes={}
            )
        
        # 執行刪除
        old_content = current_version.content
        lines = current_version.lines.copy()
        deleted_content = lines.pop(line_number - 1)
        new_file_content = '\n'.join(lines)
        
        # 寫入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)
        except PermissionError:
            return EditResultData(
                success=False,
                result=EditResult.PERMISSION_DENIED,
                message=f"無權限寫入文件: {file_path}",
                affected_lines=[],
                new_hashes={}
            )
        
        # 更新版本
        new_version = FileVersion(file_path, new_file_content)
        self.versions[str(file_path)] = new_version
        
        return EditResultData(
            success=True,
            result=EditResult.SUCCESS,
            message=f"成功刪除第 {line_number} 行",
            affected_lines=list(range(line_number, len(lines) + 2)),
            new_hashes={},
            old_content=deleted_content
        )
    
    def replace_range(self, file_path: Union[str, Path], start_line: int,
                      end_line: int, expected_hashes: List[str],
                      new_content: str) -> EditResultData:
        """
        替換行範圍（基於哈希驗證）
        
        Args:
            file_path: 文件路徑
            start_line: 起始行號
            end_line: 結束行號
            expected_hashes: 期望的各行哈希列表
            new_content: 新內容（可包含多行）
        
        Returns:
            EditResultData: 編輯結果
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return EditResultData(
                success=False,
                result=EditResult.FILE_NOT_FOUND,
                message=f"文件不存在: {file_path}",
                affected_lines=[],
                new_hashes={}
            )
        
        current_version = self.read_file(file_path)
        
        # 驗證範圍
        if start_line < 1 or end_line > len(current_version.lines) or start_line > end_line:
            return EditResultData(
                success=False,
                result=EditResult.LINE_NOT_FOUND,
                message=f"行範圍無效: {start_line}-{end_line}",
                affected_lines=[],
                new_hashes={}
            )
        
        # 驗證哈希
        range_length = end_line - start_line + 1
        if len(expected_hashes) != range_length:
            return EditResultData(
                success=False,
                result=EditResult.VALIDATION_ERROR,
                message=f"哈希數量不匹配: 期望 {range_length}, 實際 {len(expected_hashes)}",
                affected_lines=list(range(start_line, end_line + 1)),
                new_hashes={}
            )
        
        if not current_version.verify_range(start_line, end_line, expected_hashes):
            if self.strict_mode:
                return EditResultData(
                    success=False,
                    result=EditResult.HASH_MISMATCH,
                    message="行範圍哈希不匹配",
                    affected_lines=list(range(start_line, end_line + 1)),
                    new_hashes={}
                )
        
        # 執行替換
        old_content = current_version.content
        lines = current_version.lines.copy()
        new_lines = new_content.split('\n')
        
        # 替換範圍
        lines[start_line - 1:end_line] = new_lines
        new_file_content = '\n'.join(lines)
        
        # 寫入文件
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_file_content)
        except PermissionError:
            return EditResultData(
                success=False,
                result=EditResult.PERMISSION_DENIED,
                message=f"無權限寫入文件: {file_path}",
                affected_lines=[],
                new_hashes={}
            )
        
        # 計算新哈希
        new_version = FileVersion(file_path, new_file_content)
        new_hashes = {
            i: new_version.line_hashes[i]
            for i in range(start_line, start_line + len(new_lines))
        }
        
        self.versions[str(file_path)] = new_version
        
        return EditResultData(
            success=True,
            result=EditResult.SUCCESS,
            message=f"成功替換第 {start_line}-{end_line} 行",
            affected_lines=list(range(start_line, max(end_line, start_line + len(new_lines) - 1) + 1)),
            new_hashes=new_hashes,
            old_content=old_content
        )
    
    def get_file_with_hashes(self, file_path: Union[str, Path]) -> str:
        """
        獲取帶哈希標註的文件內容
        
        Args:
            file_path: 文件路徑
        
        Returns:
            帶哈希標註的內容字符串
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return ""
        
        version = self.read_file(file_path)
        lines_with_hashes = []
        
        for i, line in enumerate(version.lines, 1):
            hash_val = version.line_hashes.get(i, "")
            lines_with_hashes.append(f"{i}:{hash_val}|{line}")
        
        return '\n'.join(lines_with_hashes)


# 便捷函數
def edit_file_line(file_path: Union[str, Path], line_number: int,
                   expected_hash: str, new_content: str,
                   strict: bool = True) -> EditResultData:
    """便捷函數：編輯單行"""
    editor = HashAnchoredEditor(strict_mode=strict)
    return editor.edit_line(file_path, line_number, expected_hash, new_content)


def get_line_hash(content: str) -> str:
    """便捷函數：計算行哈希"""
    return compute_line_hash(content)
