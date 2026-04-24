"""
OpenClaw Integration Hook - OpenClaw 整合模組

在每次對話後自動檢查 Context，超過 70% 時發出警告。
此模組設計為與 OpenClaw 系統整合，不修改 OpenClaw 核心。

使用方法：
1. 在 AGENTS.md 啟動序列中導入並初始化
2. 在每次對話後調用 check_context_hook()

注意：所有功能默認關閉，需要手動啟用。
"""

import os
import sys
from typing import List, Dict, Optional, Any
from pathlib import Path

# 確保可以找到 AMS
ams_path = Path.home() / "openclaw_workspace"
if str(ams_path) not in sys.path:
    sys.path.insert(0, str(ams_path))

try:
    from alfred_memory_system import AMS, ContextStatus
    AMS_AVAILABLE = True
except ImportError:
    AMS_AVAILABLE = False
    print("[AMS Hook] Warning: Alfred Memory System not available")


class OpenClawHook:
    """
    OpenClaw 整合鉤子
    
    在每次對話後自動檢查 Context 使用情況，
    並在超過閾值時發出警告。
    """
    
    # 警告閾值（可配置）
    WARNING_THRESHOLD = 70  # 70% 發出警告
    
    def __init__(self, enabled: bool = False):
        """
        初始化 OpenClaw Hook
        
        Args:
            enabled: 是否啟用，默認 False（需要手動開啟）
        """
        self.enabled = enabled and AMS_AVAILABLE
        self.ams = None
        self._warning_issued = False  # 避免重複警告
        
        if self.enabled:
            try:
                self.ams = AMS()
                print(f"[AMS Hook] Initialized (enabled={enabled})")
            except Exception as e:
                print(f"[AMS Hook] Failed to initialize AMS: {e}")
                self.enabled = False
    
    def check_context(self, messages: List[Dict[str, Any]], 
                      session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        檢查 Context 使用情況
        
        Args:
            messages: 當前對話消息列表
            session_id: 可選 Session ID
        
        Returns:
            Context 狀態字典，如果未啟用則返回 None
        """
        if not self.enabled or not self.ams:
            return None
        
        try:
            # 檢查 Context
            status = self.ams.context_monitor.check_context(messages)
            
            # 如果超過閾值，發出警告
            if status.usage_percent >= self.WARNING_THRESHOLD:
                if not self._warning_issued:
                    self._print_warning(status)
                    self._warning_issued = True
            else:
                self._warning_issued = False
            
            # 記錄到數據庫（如果有 session_id）
            if session_id:
                self.ams.context_monitor.log_usage(session_id, status)
            
            return status.to_dict()
        
        except Exception as e:
            print(f"[AMS Hook] Error checking context: {e}")
            return None
    
    def _print_warning(self, status):
        """打印警告信息"""
        print("\n" + "="*60)
        print("🚨 AMS CONTEXT WARNING")
        print("="*60)
        print(f"Context Usage: {status.usage_percent:.1f}% ({status.tokens:,} / {status.limit:,} tokens)")
        print(f"Status: {status.status.upper()}")
        
        if status.action_required == 'notify_user':
            print("\n⚠️  Context 即將用盡，建議：")
            print("   1. 開始新對話")
            print("   2. 使用 /compact 壓縮上下文")
            print("   3. 總結當前進度並繼續")
        elif status.action_required == 'compress_context':
            print("\n📦 建議立即壓縮上下文")
        elif status.action_required == 'emergency_compress':
            print("\n🆘 Context 即將耗盡！請立即採取行動！")
        
        print("="*60 + "\n")
    
    def get_status(self) -> Dict[str, Any]:
        """獲取 Hook 狀態"""
        return {
            'enabled': self.enabled,
            'ams_available': AMS_AVAILABLE,
            'warning_threshold': self.WARNING_THRESHOLD,
            'warning_issued': self._warning_issued
        }


# ==================== 便捷函數 ====================

# 全局 Hook 實例（延遲初始化）
_hook_instance = None

def get_hook(enabled: bool = False) -> OpenClawHook:
    """獲取全局 Hook 實例"""
    global _hook_instance
    if _hook_instance is None:
        _hook_instance = OpenClawHook(enabled=enabled)
    return _hook_instance


def check_context_hook(messages: List[Dict[str, Any]], 
                       session_id: Optional[str] = None,
                       enabled: bool = False) -> Optional[Dict[str, Any]]:
    """
    便捷的 Context 檢查函數
    
    使用方式（在 AGENTS.md 啟動序列中）：
        from alfred_memory_system.integration.openclaw_hook import check_context_hook
        
        # 每次對話後檢查
        status = check_context_hook(messages, session_id, enabled=True)
    
    Args:
        messages: 當前對話消息列表
        session_id: 可選 Session ID
        enabled: 是否啟用 Hook
    
    Returns:
        Context 狀態字典，如果未啟用則返回 None
    """
    hook = get_hook(enabled=enabled)
    return hook.check_context(messages, session_id)


def init_ams_hook(enabled: bool = False) -> OpenClawHook:
    """
    初始化 AMS Hook
    
    使用方式（在 AGENTS.md 啟動序列中）：
        from alfred_memory_system.integration.openclaw_hook import init_ams_hook
        
        # 初始化（在啟動時調用一次）
        ams_hook = init_ams_hook(enabled=True)
    
    Args:
        enabled: 是否啟用
    
    Returns:
        OpenClawHook 實例
    """
    return get_hook(enabled=enabled)


# ==================== AGENTS.md 整合示例 ====================
"""
# 在 AGENTS.md 啟動序列中添加以下內容：

## AMS Integration (可選)

```python
# 在啟動時初始化 AMS Hook（只執行一次）
try:
    from alfred_memory_system.integration.openclaw_hook import init_ams_hook
    ams_hook = init_ams_hook(enabled=False)  # 默認關閉，需要時設為 True
except ImportError:
    ams_hook = None
```

## 每次對話後檢查 Context

```python
# 在每次對話後調用（例如在回覆生成後）
if ams_hook and ams_hook.enabled:
    try:
        status = ams_hook.check_context(messages, session_id)
        if status and status['usage_percent'] > 70:
            # Context 警告已在 Hook 中打印
            pass
    except Exception as e:
        print(f"[AMS] Context check failed: {e}")
```
"""
