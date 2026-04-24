# Hash-Anchored Edit 機制研究報告

## 研究目標

為 OpenClaw edit 工具設計一套基於哈希驗證的編輯機制，解決當前文件編輯中的衝突檢測和可靠性問題。

---

## 1. Hash-Anchored Edit 核心原理

### 1.1 問題背景

當前主流的 AI 編碼助手（如 Claude Code、Codex）在文件編輯時面臨以下問題：

1. **str_replace 模式**：需要模型完美重現舊文本（包括空格和縮進），容易因格式問題失敗
2. **apply_patch 模式**：使用 diff 格式，但非 OpenAI 模型難以理解，失敗率高達 50%+
3. **無衝突檢測**：當文件在讀取後被其他進程修改時，編輯可能導致數據損壞

### 1.2 Hash-Anchored Edit 概念

Hash-Anchored Edit（哈希錨定編輯）是一種創新的文件編輯機制，核心思想：

```
讀取階段：
1:a3|function hello() {
2:f1|  return "world";
3:0e|}

編輯階段：
- 引用哈希標籤而非文本內容
- "替換行 2:f1" 或 "在 3:0e 後插入"
- 如果哈希不匹配，拒絕編輯（樂觀併發控制）
```

### 1.3 核心優勢

| 優勢 | 說明 |
|------|------|
| **無需完美重現** | 模型不需要重現舊文本，只需引用短哈希 |
| **內建衝突檢測** | 哈希不匹配自動拒絕編輯，防止數據損壞 |
| **跨模型兼容** | 不依賴特定模型的輸出格式 |
| **減少 Token 消耗** | 避免重複輸出舊文本，減少 20-60% 的輸出 Token |

### 1.4 實證數據

根據 [The Harness Problem](https://blog.can.ac/2026/02/12/the-harness-problem/) 的研究：

- **Grok Code Fast 1**：從 6.7% 提升到 68.3%（10倍改進）
- **MiniMax**：成功率翻倍
- **Grok 4 Fast**：輸出 Token 減少 61%
- **Gemini**：+8% 成功率（超過大多數模型升級的改進）

---

## 2. 哈希計算策略

### 2.1 行級哈希（Line-Level Hash）

**設計**：
- 每行獨立計算哈希
- 使用短哈希（2-4 字符），如 Base32 編碼的 CRC32 前 3 字符
- 格式：`行號:哈希|內容`

**算法選擇**：

```python
import zlib
import base64

def compute_line_hash(line_content: str, hash_length: int = 3) -> str:
    """
    計算行內容的短哈希
    
    Args:
        line_content: 行內容（包含換行符或不包含）
        hash_length: 哈希長度（默認 3 字符）
    
    Returns:
        短哈希字符串
    """
    # 標準化：移除尾部換行符，保留其他空白
    normalized = line_content.rstrip('\n\r')
    
    # 使用 CRC32 計算哈希（快速，碰撞率低於 SHA1 對於短內容）
    hash_value = zlib.crc32(normalized.encode('utf-8')) & 0xffffffff
    
    # 轉換為 Base32 編碼，取前 N 字符
    # Base32 使用 A-Z2-7，適合區分大小寫不敏感的環境
    base32_hash = base64.b32encode(hash_value.to_bytes(4, 'big')).decode('ascii')
    
    return base32_hash[:hash_length].lower()
```

**碰撞概率**：
- 3 字符 Base32 = 32^3 = 32,768 種組合
- 對於 1000 行文件，碰撞概率約為 1.5%
- 對於 10,000 行文件，碰撞概率約為 15%
- **建議**：對於大文件使用 4 字符哈希（100萬種組合）

### 2.2 區塊級哈希（Block-Level Hash）

**設計**：
- 將連續的相關行組合成區塊
- 每個區塊有一個統一的哈希標識
- 適合函數級別的編輯

**應用場景**：
- 替換整個函數
- 刪除代碼區塊
- 插入新區塊

```python
class BlockAnchor:
    """區塊錨點"""
    
    def __init__(self, start_line: int, end_line: int, lines: List[str]):
        self.start_line = start_line
        self.end_line = end_line
        # 計算區塊整體哈希
        content = '\n'.join(lines)
        self.hash = compute_block_hash(content)
    
    def verify(self, current_lines: List[str]) -> bool:
        """驗證區塊是否未改變"""
        if self.end_line > len(current_lines):
            return False
        content = '\n'.join(current_lines[self.start_line-1:self.end_line])
        return compute_block_hash(content) == self.hash
```

### 2.3 文件級哈希（File-Level Hash）

**設計**：
- 整個文件的哈希作為版本標識
- 用於快速檢測文件是否被修改
- 作為樂觀併發控制的第一道防線

```python
import hashlib

def compute_file_hash(file_path: str) -> str:
    """計算文件整體哈希（SHA-256）"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def compute_file_hash_from_content(content: str) -> str:
    """從內容計算文件哈希"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
```

### 2.4 多級哈希策略比較

| 策略 | 粒度 | 適用場景 | 碰撞風險 | 驗證速度 |
|------|------|----------|----------|----------|
| 行級 | 單行 | 精確編輯 | 中 | 快 |
| 區塊級 | 多行 | 函數/邏輯塊 | 低 | 快 |
| 文件級 | 整文件 | 版本檢查 | 極低 | 極快 |

**推薦組合策略**：
1. 文件級哈希作為快速檢查
2. 行級哈希作為主要錨點
3. 區塊級哈希作為備選（當行級碰撞時）

---

## 3. 衝突檢測機制設計

### 3.1 樂觀併發控制（Optimistic Concurrency Control）

**原理**：
- 讀取時記錄文件狀態（哈希值）
- 編輯時驗證當前狀態是否與讀取時一致
- 不一致則拒絕編輯，返回衝突信息

```python
class FileVersion:
    """文件版本快照"""
    
    def __init__(self, file_path: str, content: str, line_hashes: Dict[int, str]):
        self.file_path = file_path
        self.content = content
        self.file_hash = compute_file_hash_from_content(content)
        self.line_hashes = line_hashes  # 行號 -> 哈希映射
        self.timestamp = time.time()
    
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
```

### 3.2 衝突類型與檢測

```python
from enum import Enum, auto

class ConflictType(Enum):
    """衝突類型"""
    FILE_MODIFIED = auto()      # 文件整體被修改
    LINE_MODIFIED = auto()      # 特定行被修改
    LINE_DELETED = auto()       # 行被刪除
    LINE_INSERTED = auto()      # 行被插入（導致行號偏移）
    HASH_MISMATCH = auto()      # 哈希不匹配
    RANGE_INVALID = auto()      # 範圍無效

class ConflictInfo:
    """衝突信息"""
    
    def __init__(self, 
                 conflict_type: ConflictType,
                 expected_line: int,
                 expected_hash: str,
                 actual_hash: Optional[str] = None,
                 actual_line: Optional[int] = None,
                 message: str = ""):
        self.conflict_type = conflict_type
        self.expected_line = expected_line
        self.expected_hash = expected_hash
        self.actual_hash = actual_hash
        self.actual_line = actual_line
        self.message = message
    
    def __str__(self) -> str:
        return (f"衝突: {self.conflict_type.name} "
                f"at line {self.expected_line} "
                f"(expected: {self.expected_hash}, "
                f"actual: {self.actual_hash})")
```

### 3.3 衝突解決策略

```python
class ConflictResolver:
    """衝突解決器"""
    
    def __init__(self, strategy: str = "strict"):
        self.strategy = strategy  # strict, fuzzy, auto
    
    def resolve(self, 
                original_version: FileVersion,
                current_content: str,
                edit_request: EditRequest) -> Union[EditResult, ConflictInfo]:
        """
        嘗試解決衝突
        
        Strategies:
        - strict: 任何不匹配都拒絕
        - fuzzy: 嘗試通過內容匹配找到對應行
        - auto: 如果內容相似度高，自動調整行號
        """
        if self.strategy == "strict":
            return self._strict_resolve(original_version, current_content, edit_request)
        elif self.strategy == "fuzzy":
            return self._fuzzy_resolve(original_version, current_content, edit_request)
        elif self.strategy == "auto":
            return self._auto_resolve(original_version, current_content, edit_request)
    
    def _fuzzy_resolve(self, original_version, current_content, edit_request):
        """模糊匹配策略：通過內容查找對應行"""
        current_lines = current_content.split('\n')
        
        # 嘗試通過哈希找到對應行（即使行號不同）
        target_hash = edit_request.anchor_hash
        for i, line in enumerate(current_lines):
            if compute_line_hash(line) == target_hash:
                # 找到匹配行，調整編輯請求的行號
                adjusted_request = edit_request.with_line_offset(
                    new_line=i+1,
                    original_line=edit_request.line_number
                )
                return EditResult.success(adjusted_request)
        
        return ConflictInfo(
            ConflictType.HASH_MISMATCH,
            edit_request.line_number,
            target_hash,
            message="無法找到匹配的內容"
        )
```

### 3.4 行號漂移處理

當文件被修改後，行號可能發生變化。處理策略：

```python
class LineMapping:
    """行號映射追蹤"""
    
    def __init__(self):
        self.mappings: Dict[int, int] = {}  # 原行號 -> 新行號
        self.inserted_lines: Set[int] = set()
        self.deleted_lines: Set[int] = set()
    
    @staticmethod
    def compute_diff(old_lines: List[str], new_lines: List[str]) -> 'LineMapping':
        """計算行號映射"""
        import difflib
        
        mapping = LineMapping()
        sm = difflib.SequenceMatcher(None, old_lines, new_lines)
        
        old_line_num = 0
        new_line_num = 0
        
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                # 未改變的行
                for i in range(i2 - i1):
                    mapping.mappings[i1 + i + 1] = j1 + i + 1
                old_line_num = i2
                new_line_num = j2
            elif tag == 'delete':
                # 刪除的行
                for i in range(i1, i2):
                    mapping.deleted_lines.add(i + 1)
                old_line_num = i2
            elif tag == 'insert':
                # 插入的行
                for i in range(j1, j2):
                    mapping.inserted_lines.add(i + 1)
                new_line_num = j2
            elif tag == 'replace':
                # 替換的行
                for i in range(i1, i2):
                    mapping.deleted_lines.add(i + 1)
                for i in range(j1, j2):
                    mapping.inserted_lines.add(i + 1)
                old_line_num = i2
                new_line_num = j2
        
        return mapping
    
    def map_line(self, old_line: int) -> Optional[int]:
        """將原行號映射到新行號"""
        if old_line in self.deleted_lines:
            return None  # 行已被刪除
        
        # 計算偏移量
        offset = 0
        for inserted in sorted(self.inserted_lines):
            if inserted < self.mappings.get(old_line, old_line):
                offset += 1
        
        return self.mappings.get(old_line, old_line + offset)
```

---

## 4. 與現有 edit 工具的整合方案

### 4.1 OpenClaw edit 工具現狀

OpenClaw 當前使用 `edit` 工具進行文件修改，主要參數：
- `path`: 文件路徑
- `edits`: 編輯操作列表（oldText/newText）

### 4.2 向後兼容的整合方案

**方案 A：擴展現有 edit 工具（推薦）**

```typescript
// 擴展 edit 工具的參數
interface EditToolParams {
  path: string;
  edits: EditOperation[];
  // 新增可選參數
  useHashAnchors?: boolean;  // 啟用哈希錨定
  fileVersion?: string;      // 文件版本哈希（用於 OCC）
}

interface EditOperation {
  // 現有方式（向後兼容）
  oldText?: string;
  newText: string;
  
  // 新增哈希錨定方式
  anchor?: {
    type: 'line' | 'range' | 'block';
    lineNumber?: number;
    startLine?: number;
    endLine?: number;
    hash: string;  // 錨點哈希
  };
}
```

**方案 B：獨立的 hashEdit 工具**

```typescript
interface HashEditToolParams {
  path: string;
  fileHash: string;  // 文件級哈希（必須）
  operations: HashEditOperation[];
}

interface HashEditOperation {
  type: 'replace_line' | 'replace_range' | 'insert_after' | 'insert_before' | 'delete';
  anchorHash: string;  // 錨點哈希
  lineNumber?: number; // 可選的預期行號
  newContent?: string; // 新內容（用於替換/插入）
}
```

### 4.3 read 工具的增強

為了支持哈希錨定，read 工具需要返回帶哈希標記的內容：

```typescript
interface ReadToolResult {
  content: string;           // 原始內容
  fileHash: string;          // 文件整體哈希
  lineHashes?: LineHash[];   // 行級哈希（可選）
}

interface LineHash {
  lineNumber: number;
  hash: string;
  content: string;
}
```

**輸出格式示例**：

```
1:a3b|import os
2:f1e|import sys
3:0e2|
4:c9d|def main():
5:2a1|    print("Hello")
```

### 4.4 整合架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                      OpenClaw Agent                         │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   read tool   │   │   edit tool   │   │  write tool   │
│  (增強版)      │   │  (擴展版)      │   │  (現有)        │
└───────┬───────┘   └───────┬───────┘   └───────────────┘
        │                   │
        ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Hash-Anchored Edit Engine                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Hash Calc   │  │ Conflict    │  │ Line Mapping        │  │
│  │ (哈希計算)   │  │ Detection   │  │ (行號映射)          │  │
│  └─────────────┘  │ (衝突檢測)   │  └─────────────────────┘  │
│                   └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      File System                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 偽代碼與代碼框架

### 5.1 核心類定義

```python
# hash_anchored_edit.py

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Callable
from enum import Enum, auto
import zlib
import base64
import hashlib
import time


class EditType(Enum):
    """編輯類型"""
    REPLACE_LINE = auto()
    REPLACE_RANGE = auto()
    INSERT_AFTER = auto()
    INSERT_BEFORE = auto()
    DELETE_LINE = auto()
    DELETE_RANGE = auto()


@dataclass
class LineAnchor:
    """行錨點"""
    line_number: int
    hash: str
    content: str
    
    def verify(self, current_content: str) -> bool:
        """驗證錨點是否有效"""
        return compute_line_hash(current_content) == self.hash


@dataclass
class EditOperation:
    """編輯操作"""
    edit_type: EditType
    anchor: LineAnchor
    new_content: Optional[str] = None
    end_anchor: Optional[LineAnchor] = None  # 用於範圍操作
    
    def to_dict(self) -> dict:
        return {
            'type': self.edit_type.name,
            'line': self.anchor.line_number,
            'hash': self.anchor.hash,
            'new_content': self.new_content,
            'end_line': self.end_anchor.line_number if self.end_anchor else None,
            'end_hash': self.end_anchor.hash if self.end_anchor else None
        }


@dataclass
class EditResult:
    """編輯結果"""
    success: bool
    message: str
    new_content: Optional[str] = None
    conflicts: List['ConflictInfo'] = field(default_factory=list)
    applied_operations: int = 0
    
    @staticmethod
    def ok(new_content: str, operations: int = 1) -> 'EditResult':
        return EditResult(
            success=True,
            message=f"成功應用 {operations} 個操作",
            new_content=new_content,
            applied_operations=operations
        )
    
    @staticmethod
    def fail(message: str, conflicts: List['ConflictInfo'] = None) -> 'EditResult':
        return EditResult(
            success=False,
            message=message,
            conflicts=conflicts or []
        )


@dataclass
class ConflictInfo:
    """衝突信息"""
    operation: EditOperation
    expected_line: int
    expected_hash: str
    actual_hash: Optional[str]
    actual_content: Optional[str]
    message: str
```

### 5.2 哈希計算模塊

```python
# hash_utils.py

import zlib
import base64
import hashlib
from typing import List


class HashConfig:
    """哈希配置"""
    LINE_HASH_LENGTH = 3      # 行級哈希長度
    BLOCK_HASH_LENGTH = 6     # 區塊級哈希長度
    FILE_HASH_ALGORITHM = 'sha256'


def compute_line_hash(line_content: str, length: int = None) -> str:
    """
    計算行內容的短哈希
    
    使用 CRC32 + Base32 編碼，產生短且可讀的哈希值
    """
    length = length or HashConfig.LINE_HASH_LENGTH
    
    # 標準化：保留前導空格，移除尾部換行
    normalized = line_content.rstrip('\n\r')
    
    # CRC32 計算（快速且對短內容足夠）
    crc = zlib.crc32(normalized.encode('utf-8')) & 0xffffffff
    
    # 轉換為 Base32（使用小寫字母和數字）
    base32 = base64.b32encode(crc.to_bytes(4, 'big')).decode('ascii')
    
    return base32[:length].lower()


def compute_block_hash(lines: List[str]) -> str:
    """計算區塊哈希"""
    content = '\n'.join(line.rstrip('\n\r') for line in lines)
    crc = zlib.crc32(content.encode('utf-8')) & 0xffffffff
    base32 = base64.b32encode(crc.to_bytes(4, 'big')).decode('ascii')
    return base32[:HashConfig.BLOCK_HASH_LENGTH].lower()


def compute_file_hash(content: str) -> str:
    """計算文件整體哈希（SHA-256）"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def compute_file_hash_binary(file_path: str) -> str:
    """從文件計算哈希"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()
```

### 5.3 文件版本管理

```python
# file_version.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from hash_utils import compute_line_hash, compute_file_hash


@dataclass
class FileVersion:
    """文件版本快照"""
    file_path: str
    content: str
    file_hash: str
    line_hashes: Dict[int, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    @classmethod
    def from_content(cls, file_path: str, content: str) -> 'FileVersion':
        """從內容創建版本快照"""
        lines = content.split('\n')
        line_hashes = {
            i+1: compute_line_hash(line)
            for i, line in enumerate(lines)
        }
        return cls(
            file_path=file_path,
            content=content,
            file_hash=compute_file_hash(content),
            line_hashes=line_hashes
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> 'FileVersion':
        """從文件創建版本快照"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return cls.from_content(file_path, content)
    
    def get_line_hash(self, line_number: int) -> Optional[str]:
        """獲取指定行的哈希"""
        return self.line_hashes.get(line_number)
    
    def get_line_content(self, line_number: int) -> Optional[str]:
        """獲取指定行的內容"""
        lines = self.content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return None
    
    def verify_line(self, line_number: int, expected_hash: str) -> bool:
        """驗證指定行是否未改變"""
        actual_hash = self.get_line_hash(line_number)
        return actual_hash == expected_hash
    
    def verify_file(self, expected_hash: str) -> bool:
        """驗證文件整體是否未改變"""
        return self.file_hash == expected_hash
    
    def to_annotated_content(self) -> str:
        """生成帶哈希標記的內容"""
        lines = self.content.split('\n')
        annotated = []
        for i, line in enumerate(lines, 1):
            hash_val = self.line_hashes.get(i, '???')
            annotated.append(f"{i}:{hash_val}|{line}")
        return '\n'.join(annotated)
```

### 5.4 編輯引擎核心

```python
# edit_engine.py

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from file_version import FileVersion
from hash_utils import compute_line_hash, compute_file_hash


class HashAnchoredEditEngine:
    """哈希錨定編輯引擎"""
    
    def __init__(self, conflict_resolver: Optional[Callable] = None):
        self.conflict_resolver = conflict_resolver
        self._version_cache: Dict[str, FileVersion] = {}
    
    def read_file(self, file_path: str) -> FileVersion:
        """讀取文件並創建版本快照"""
        version = FileVersion.from_file(file_path)
        self._version_cache[file_path] = version
        return version
    
    def read_content(self, file_path: str, content: str) -> FileVersion:
        """從內容創建版本快照"""
        version = FileVersion.from_content(file_path, content)
        self._version_cache[file_path] = version
        return version
    
    def apply_edits(self, 
                    file_path: str,
                    original_version: FileVersion,
                    operations: List[EditOperation],
                    current_content: Optional[str] = None) -> EditResult:
        """
        應用編輯操作
        
        Args:
            file_path: 文件路徑
            original_version: 原始版本快照
            operations: 編輯操作列表
            current_content: 當前內容（如果為 None，則從文件讀取）
        
        Returns:
            EditResult: 編輯結果
        """
        # 獲取當前內容
        if current_content is None:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_content = f.read()
            except FileNotFoundError:
                return EditResult.fail(f"文件不存在: {file_path}")
        
        # 創建當前版本快照
        current_version = FileVersion.from_content(file_path, current_content)
        
        # 首先驗證文件級哈希
        if current_version.file_hash != original_version.file_hash:
            # 文件已被修改，需要檢查具體衝突
            pass  # 繼續檢查行級衝突
        
        # 驗證所有錨點
        conflicts = []
        for op in operations:
            conflict = self._verify_anchor(op, current_version)
            if conflict:
                conflicts.append(conflict)
        
        if conflicts:
            # 嘗試衝突解決
            if self.conflict_resolver:
                resolved = self.conflict_resolver(conflicts, operations, current_version)
                if not resolved:
                    return EditResult.fail(
                        f"檢測到 {len(conflicts)} 個衝突",
                        conflicts
                    )
            else:
                return EditResult.fail(
                    f"檢測到 {len(conflicts)} 個衝突",
                    conflicts
                )
        
        # 應用編輯
        try:
            new_content = self._apply_operations(
                current_content,
                operations,
                current_version
            )
            return EditResult.ok(new_content, len(operations))
        except Exception as e:
            return EditResult.fail(f"應用編輯時出錯: {str(e)}")
    
    def _verify_anchor(self, 
                       operation: EditOperation, 
                       current_version: FileVersion) -> Optional[ConflictInfo]:
        """驗證單個錨點"""
        anchor = operation.anchor
        actual_hash = current_version.get_line_hash(anchor.line_number)
        
        if actual_hash is None:
            return ConflictInfo(
                operation=operation,
                expected_line=anchor.line_number,
                expected_hash=anchor.hash,
                actual_hash=None,
                actual_content=None,
                message=f"行 {anchor.line_number} 不存在"
            )
        
        if actual_hash != anchor.hash:
            actual_content = current_version.get_line_content(anchor.line_number)
            return ConflictInfo(
                operation=operation,
                expected_line=anchor.line_number,
                expected_hash=anchor.hash,
                actual_hash=actual_hash,
                actual_content=actual_content,
                message=f"行 {anchor.line_number} 哈希不匹配"
            )
        
        # 驗證結束錨點（如果是範圍操作）
        if operation.end_anchor:
            end_anchor = operation.end_anchor
            end_hash = current_version.get_line_hash(end_anchor.line_number)
            
            if end_hash != end_anchor.hash:
                return ConflictInfo(
                    operation=operation,
                    expected_line=end_anchor.line_number,
                    expected_hash=end_anchor.hash,
                    actual_hash=end_hash,
                    actual_content=current_version.get_line_content(end_anchor.line_number),
                    message=f"結束行 {end_anchor.line_number} 哈希不匹配"
                )
        
        return None
    
    def _apply_operations(self,
                          content: str,
                          operations: List[EditOperation],
                          version: FileVersion) -> str:
        """應用編輯操作到內容"""
        lines = content.split('\n')
        
        # 按行號降序排序操作（避免行號偏移問題）
        sorted_ops = sorted(
            operations,
            key=lambda op: op.anchor.line_number,
            reverse=True
        )
        
        for op in sorted_ops:
            line_idx = op.anchor.line_number - 1
            
            if op.edit_type == EditType.REPLACE_LINE:
                if 0 <= line_idx < len(lines):
                    lines[line_idx] = op.new_content
                else:
                    raise IndexError(f"行號超出範圍: {op.anchor.line_number}")
            
            elif op.edit_type == EditType.REPLACE_RANGE:
                end_idx = op.end_anchor.line_number - 1
                if 0 <= line_idx <= end_idx < len(lines):
                    new_lines = op.new_content.split('\n') if op.new_content else []
                    lines[line_idx:end_idx+1] = new_lines
                else:
                    raise IndexError(f"範圍超出邊界: {op.anchor.line_number}-{op.end_anchor.line_number}")
            
            elif op.edit_type == EditType.INSERT_AFTER:
                new_lines = op.new_content.split('\n') if op.new_content else ['']
                insert_idx = line_idx + 1
                lines[insert_idx:insert_idx] = new_lines
            
            elif op.edit_type == EditType.INSERT_BEFORE:
                new_lines = op.new_content.split('\n') if op.new_content else ['']
                lines[line_idx:line_idx] = new_lines
            
            elif op.edit_type == EditType.DELETE_LINE:
                if 0 <= line_idx < len(lines):
                    del lines[line_idx]
                else:
                    raise IndexError(f"行號超出範圍: {op.anchor.line_number}")
            
            elif op.edit_type == EditType.DELETE_RANGE:
                end_idx = op.end_anchor.line_number - 1
                if 0 <= line_idx <= end_idx < len(lines):
                    del lines[line_idx:end_idx+1]
                else:
                    raise IndexError(f"範圍超出邊界: {op.anchor.line_number}-{op.end_anchor.line_number}")
        
        return '\n'.join(lines)
```

### 5.5 OpenClaw 工具整合

```python
# openclaw_integration.py

from typing import Dict, List, Any, Optional
import json
from edit_engine import HashAnchoredEditEngine, EditOperation, EditType
from file_version import FileVersion
from hash_utils import compute_line_hash


class OpenClawHashEditTool:
    """OpenClaw 哈希編輯工具整合"""
    
    def __init__(self):
        self.engine = HashAnchoredEditEngine()
        self._file_versions: Dict[str, FileVersion] = {}
    
    def read(self, path: str, **kwargs) -> Dict[str, Any]:
        """
        增強的 read 工具
        
        Returns:
            包含文件內容和哈希信息的字典
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return {'error': f'File not found: {path}'}
        except Exception as e:
            return {'error': str(e)}
        
        # 創建版本快照
        version = self.engine.read_content(path, content)
        self._file_versions[path] = version
        
        # 構建結果
        result = {
            'content': content,
            'fileHash': version.file_hash,
            'path': path
        }
        
        # 如果請求哈希標記，添加行級哈希
        if kwargs.get('includeHashes', False):
            result['lineHashes'] = [
                {
                    'lineNumber': line_num,
                    'hash': hash_val,
                    'content': version.get_line_content(line_num)
                }
                for line_num, hash_val in version.line_hashes.items()
            ]
            result['annotatedContent'] = version.to_annotated_content()
        
        return result
    
    def edit(self, path: str, edits: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        增強的 edit 工具，支持哈希錨定
        
        Args:
            path: 文件路徑
            edits: 編輯操作列表
                - 傳統格式: {'oldText': str, 'newText': str}
                - 哈希格式: {'anchor': {'line': int, 'hash': str}, 'newText': str, 'type': str}
            useHashAnchors: 是否強制使用哈希錨定
            fileVersion: 預期的文件版本哈希
        
        Returns:
            編輯結果
        """
        # 檢查是否有版本信息
        file_version = kwargs.get('fileVersion')
        use_hash_anchors = kwargs.get('useHashAnchors', False)
        
        # 獲取原始版本
        original_version = self._file_versions.get(path)
        if not original_version:
            # 如果沒有緩存的版本，讀取當前文件
            original_version = self.engine.read_file(path)
        
        # 驗證文件版本（如果提供）
        if file_version and original_version.file_hash != file_version:
            return {
                'success': False,
                'error': 'File version mismatch',
                'expectedVersion': file_version,
                'actualVersion': original_version.file_hash,
                'message': 'File has been modified since last read. Please re-read the file.'
            }
        
        # 轉換編輯操作
        operations = []
        for edit in edits:
            if 'anchor' in edit:
                # 哈希錨定格式
                op = self._parse_hash_edit(edit, original_version)
                if op:
                    operations.append(op)
            elif 'oldText' in edit:
                # 傳統格式
                if use_hash_anchors:
                    return {
                        'success': False,
                        'error': 'Traditional edit format not allowed when useHashAnchors is true'
                    }
                op = self._convert_traditional_edit(edit, original_version)
                if op:
                    operations.append(op)
            else:
                return {
                    'success': False,
                    'error': f'Invalid edit format: {edit}'
                }
        
        # 應用編輯
        result = self.engine.apply_edits(
            path,
            original_version,
            operations
        )
        
        if result.success:
            # 寫入文件
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(result.new_content)
                
                # 更新緩存的版本
                new_version = self.engine.read_content(path, result.new_content)
                self._file_versions[path] = new_version
                
                return {
                    'success': True,
                    'message': result.message,
                    'operationsApplied': result.applied_operations,
                    'newFileHash': new_version.file_hash
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to write file: {str(e)}'
                }
        else:
            # 構建衝突報告
            conflict_report = []
            for conflict in result.conflicts:
                conflict_report.append({
                    'line': conflict.expected_line,
                    'expectedHash': conflict.expected_hash,
                    'actualHash': conflict.actual_hash,
                    'actualContent': conflict.actual_content,
                    'message': conflict.message
                })
            
            return {
                'success': False,
                'error': result.message,
                'conflicts': conflict_report,
                'suggestion': 'Re-read the file to get current hashes and try again.'
            }
    
    def _parse_hash_edit(self, edit: Dict, version: FileVersion) -> Optional[EditOperation]:
        """解析哈希錨定格式的編輯"""
        anchor_data = edit['anchor']
        anchor = LineAnchor(
            line_number=anchor_data['line'],
            hash=anchor_data['hash'],
            content=version.get_line_content(anchor_data['line']) or ''
        )
        
        edit_type_str = edit.get('type', 'replace_line').upper()
        edit_type = EditType[edit_type_str]
        
        end_anchor = None
        if 'endAnchor' in edit:
            end_data = edit['endAnchor']
            end_anchor = LineAnchor(
                line_number=end_data['line'],
                hash=end_data['hash'],
                content=version.get_line_content(end_data['line']) or ''
            )
        
        return EditOperation(
            edit_type=edit_type,
            anchor=anchor,
            new_content=edit.get('newText', ''),
            end_anchor=end_anchor
        )
    
    def _convert_traditional_edit(self, 
                                   edit: Dict, 
                                   version: FileVersion) -> Optional[EditOperation]:
        """將傳統格式轉換為哈希錨定格式"""
        old_text = edit['oldText']
        new_text = edit['newText']
        
        # 在文件中查找 old_text
        lines = version.content.split('\n')
        for i, line in enumerate(lines):
            if old_text in line:
                # 找到匹配行
                anchor = LineAnchor(
                    line_number=i+1,
                    hash=version.get_line_hash(i+1),
                    content=line
                )
                
                # 計算新內容
                new_line_content = line.replace(old_text, new_text, 1)
                
                return EditOperation(
                    edit_type=EditType.REPLACE_LINE,
                    anchor=anchor,
                    new_content=new_line_content
                )
        
        # 未找到匹配
        return None


# 工具函數導出
def create_hash_edit_tool() -> OpenClawHashEditTool:
    """創建哈希編輯工具實例"""
    return OpenClawHashEditTool()
```

---

## 6. 邊緣案例處理建議

### 6.1 哈希碰撞處理

**問題**：不同內容產生相同哈希值

**解決方案**：

```python
class CollisionHandler:
    """哈希碰撞處理器"""
    
    def __init__(self, hash_length: int = 3):
        self.hash_length = hash_length
        self._collision_map: Dict[str, List[int]] = {}  # hash -> [line_numbers]
    
    def detect_collisions(self, content: str) -> Dict[str, List[int]]:
        """檢測內容中的哈希碰撞"""
        lines = content.split('\n')
        hash_to_lines: Dict[str, List[int]] = {}
        
        for i, line in enumerate(lines, 1):
            hash_val = compute_line_hash(line, self.hash_length)
            if hash_val not in hash_to_lines:
                hash_to_lines[hash_val] = []
            hash_to_lines[hash_val].append(i)
        
        # 返回有碰撞的哈希
        return {h: lines for h, lines in hash_to_lines.items() if len(lines) > 1}
    
    def resolve_collision(self, 
                          hash_val: str, 
                          expected_line: int,
                          content: str) -> Optional[int]:
        """
        嘗試解決碰撞
        
        策略：
        1. 優先使用預期的行號
        2. 如果預期行號的內容哈希匹配，使用該行
        3. 否則返回所有候選行
        """
        lines = content.split('\n')
        
        # 檢查預期行號
        if 1 <= expected_line <= len(lines):
            if compute_line_hash(lines[expected_line - 1], self.hash_length) == hash_val:
                return expected_line
        
        # 查找所有匹配的行
        candidates = []
        for i, line in enumerate(lines, 1):
            if compute_line_hash(line, self.hash_length) == hash_val:
                candidates.append(i)
        
        if len(candidates) == 1:
            return candidates[0]
        
        # 多個候選，需要額外信息
        return None  # 返回 None 表示需要人工介入或更長的哈希
```

**建議**：
- 對於小文件（<1000 行），使用 3 字符哈希足夠
- 對於大文件（>5000 行），自動升級到 4 字符哈希
- 檢測到碰撞時，提供警告並建議使用更長的哈希

### 6.2 行尾空白處理

**問題**：不同操作系統的行尾符號（\n vs \r\n）和尾部空白

**解決方案**：

```python
class LineNormalizer:
    """行內容標準化"""
    
    @staticmethod
    def normalize(line: str) -> str:
        """
        標準化行內容
        
        規則：
        1. 保留前導空白（縮進）
        2. 移除尾部換行符
        3. 移除尾部空白
        """
        # 移除尾部換行符
        line = line.rstrip('\n\r')
        # 保留前導空白，移除尾部空白
        return line.rstrip()
    
    @staticmethod
    def for_hashing(line: str) -> str:
        """用於哈希計算的標準化"""
        # 保留前導空白，移除尾部換行和空白
        return line.rstrip('\n\r').rstrip()
    
    @staticmethod
    def for_display(line: str) -> str:
        """用於顯示的標準化"""
        # 顯示時保留所有內容，只標記行尾
        if line.endswith('\r\n'):
            return line[:-2] + '␍␊'  # 標記 CRLF
        elif line.endswith('\n'):
            return line[:-1] + '␊'   # 標記 LF
        return line + '␃'            # 標記無換行
```

### 6.3 大文件處理

**問題**：大文件（>10MB）的哈希計算和內容處理

**解決方案**：

```python
class LargeFileHandler:
    """大文件處理器"""
    
    CHUNK_SIZE = 1000  # 每次處理的行數
    
    def __init__(self, max_file_size: int = 50 * 1024 * 1024):  # 50MB
        self.max_file_size = max_file_size
    
    def is_large_file(self, file_path: str) -> bool:
        """檢查是否為大文件"""
        import os
        return os.path.getsize(file_path) > self.max_file_size
    
    def read_with_hashes_streaming(self, file_path: str):
        """流式讀取文件並計算哈希"""
        line_number = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            chunk = []
            for line in f:
                line_number += 1
                hash_val = compute_line_hash(line)
                chunk.append({
                    'lineNumber': line_number,
                    'hash': hash_val,
                    'content': line.rstrip('\n\r')
                })
                
                if len(chunk) >= self.CHUNK_SIZE:
                    yield chunk
                    chunk = []
            
            if chunk:
                yield chunk
    
    def edit_large_file(self, 
                        file_path: str,
                        operations: List[EditOperation]) -> EditResult:
        """
        使用臨時文件處理大文件編輯
        
        策略：
        1. 創建臨時文件
        2. 流式複製並應用修改
        3. 原子性替換原文件
        """
        import tempfile
        import os
        
        temp_path = None
        try:
            # 創建臨時文件
            fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path))
            os.close(fd)
            
            # 流式處理
            with open(file_path, 'r', encoding='utf-8') as src:
                with open(temp_path, 'w', encoding='utf-8') as dst:
                    line_number = 0
                    for line in src:
                        line_number += 1
                        # 檢查是否有針對該行的操作
                        modified_line = self._apply_line_operations(
                            line, line_number, operations
                        )
                        dst.write(modified_line)
            
            # 原子性替換
            os.replace(temp_path, file_path)
            
            return EditResult.ok("", len(operations))
            
        except Exception as e:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
            return EditResult.fail(f"大文件編輯失敗: {str(e)}")
    
    def _apply_line_operations(self, 
                               line: str, 
                               line_number: int,
                               operations: List[EditOperation]) -> str:
        """應用單行操作"""
        # 簡化實現：實際應該根據操作類型處理
        return line
```

### 6.4 二進制文件處理

**問題**：二進制文件不應使用行級哈希

**解決方案**：

```python
class FileTypeDetector:
    """文件類型檢測器"""
    
    BINARY_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
        '.pdf', '.zip', '.tar', '.gz', '.rar',
        '.exe', '.dll', '.so', '.dylib',
        '.bin', '.dat', '.db'
    }
    
    @classmethod
    def is_binary(cls, file_path: str) -> bool:
        """檢測是否為二進制文件"""
        import os
        ext = os.path.splitext(file_path)[1].lower()
        if ext in cls.BINARY_EXTENSIONS:
            return True
        
        # 檢查文件內容
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\x00' in chunk
        except:
            return True
    
    @classmethod
    def get_edit_strategy(cls, file_path: str) -> str:
        """獲取文件的編輯策略"""
        if cls.is_binary(file_path):
            return 'binary'  # 不支持哈希錨定
        
        import os
        size = os.path.getsize(file_path)
        if size > 10 * 1024 * 1024:  # 10MB
            return 'large_text'  # 使用流式處理
        
        return 'standard'  # 標準處理
```

### 6.5 並發編輯處理

**問題**：多個進程或代理同時編輯同一文件

**解決方案**：

```python
import fcntl
import os

class ConcurrentEditManager:
    """並發編輯管理器"""
    
    def __init__(self, lock_dir: str = '/tmp/openclaw_locks'):
        self.lock_dir = lock_dir
        os.makedirs(lock_dir, exist_ok=True)
    
    def _get_lock_path(self, file_path: str) -> str:
        """獲取鎖文件路徑"""
        # 使用文件路徑的哈希作為鎖文件名
        file_hash = hashlib.md5(file_path.encode()).hexdigest()
        return os.path.join(self.lock_dir, f"{file_hash}.lock")
    
    def acquire_lock(self, file_path: str, timeout: float = 30.0) -> bool:
        """獲取文件鎖"""
        lock_path = self._get_lock_path(file_path)
        
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return True
            except FileExistsError:
                # 檢查鎖是否過期
                try:
                    with open(lock_path, 'r') as f:
                        pid = int(f.read().strip())
                    # 檢查進程是否存在
                    os.kill(pid, 0)
                except (ValueError, OSError, ProcessLookupError):
                    # 鎖已過期，刪除並重試
                    try:
                        os.unlink(lock_path)
                    except:
                        pass
                
                time.sleep(0.1)
        
        return False
    
    def release_lock(self, file_path: str):
        """釋放文件鎖"""
        lock_path = self._get_lock_path(file_path)
        try:
            if os.path.exists(lock_path):
                with open(lock_path, 'r') as f:
                    pid = f.read().strip()
                if pid == str(os.getpid()):
                    os.unlink(lock_path)
        except:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 清理所有鎖
        pass
```

### 6.6 編碼問題處理

**問題**：不同編碼（UTF-8, GBK, Latin-1 等）的文件

**解決方案**：

```python
import chardet

class EncodingHandler:
    """編碼處理器"""
    
    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """檢測文件編碼"""
        with open(file_path, 'rb') as f:
            raw = f.read(4096)
            result = chardet.detect(raw)
            return result.get('encoding', 'utf-8')
    
    @staticmethod
    def read_with_encoding(file_path: str, 
                           preferred_encoding: str = 'utf-8') -> tuple:
        """
        讀取文件並返回編碼信息
        
        Returns:
            (content, encoding, confidence)
        """
        try:
            # 首先嘗試首選編碼
            with open(file_path, 'r', encoding=preferred_encoding) as f:
                return f.read(), preferred_encoding, 1.0
        except UnicodeDecodeError:
            pass
        
        # 檢測編碼
        encoding = EncodingHandler.detect_encoding(file_path)
        
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read(), encoding, 0.8
    
    @staticmethod
    def write_with_encoding(file_path: str, 
                            content: str, 
                            encoding: str = 'utf-8'):
        """寫入文件並保留 BOM（如果需要）"""
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
```

---

## 7. 實施建議

### 7.1 分階段實施

**第一階段：基礎支持（MVP）**
- 實現行級哈希計算
- 支持基本的 replace_line 和 insert_after 操作
- 提供簡單的衝突檢測

**第二階段：完整功能**
- 支持所有編輯操作類型
- 實現衝突解決策略
- 添加行號漂移處理

**第三階段：優化與擴展**
- 大文件流式處理
- 並發編輯支持
- 性能優化

### 7.2 配置選項

```json
{
  "hashAnchoredEdit": {
    "enabled": true,
    "hashLength": 3,
    "collisionDetection": true,
    "conflictResolution": "strict",
    "cacheVersions": true,
    "maxFileSize": 10485760,
    "largeFileStrategy": "streaming"
  }
}
```

### 7.3 測試策略

1. **單元測試**：哈希計算、錨點驗證、編輯操作
2. **集成測試**：完整編輯流程、衝突檢測
3. **基準測試**：與傳統 edit 工具的性能對比
4. **邊緣案例測試**：大文件、二進制文件、編碼問題

---

## 8. 結論

Hash-Anchored Edit 機制為 OpenClaw 的 edit 工具提供了一個強大的改進方向：

1. **可靠性提升**：通過哈希驗證防止意外數據損壞
2. **模型兼容性**：不依賴特定模型的輸出格式
3. **效率提升**：減少 Token 消耗，提高編輯成功率
4. **向後兼容**：可以無縫整合到現有工具中

根據已有的研究數據，這種機制可以將編輯成功率提升 8-60%，特別是對於非頂級模型效果更為顯著。

---

## 參考資料

1. [The Harness Problem](https://blog.can.ac/2026/02/12/the-harness-problem/) - Can Acar
2. [OpenAI Codex Issue #11601](https://github.com/openai/codex/issues/11601) - Hash based edit tool
3. [OpenAI Codex Issue #12987](https://github.com/openai/codex/issues/12987) - Hash-anchored edit mode
4. [Oh-My-OpenAgent Issue #2243](https://github.com/code-yeongyu/oh-my-openagent/issues/2243) - Harden hash line edits
5. [EDIT-Bench](https://arxiv.org/abs/2511.04486) - 編輯基準測試
6. [Diff-XYZ benchmark](https://arxiv.org/abs/2510.12487) - JetBrains 差異測試

---

*報告生成時間：2026-04-13*
*版本：v1.0*
