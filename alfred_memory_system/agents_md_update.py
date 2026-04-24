"""
AGENTS.md 更新腳本

此腳本生成 AGENTS.md 中 AMS 整合的建議代碼片段。
運行後會輸出需要添加到 AGENTS.md 的內容。
"""

AMS_INTEGRATION_SNIPPET = '''
# 🧠 Alfred Memory System (AMS) Integration

## 啟動序列添加（在 AGENTS.md 中）

在啟動序列的適當位置添加以下內容：

```python
# ============================================================
# Alfred Memory System (AMS) Integration - 可選，默認關閉
# ============================================================

# 初始化 AMS Hook（在啟動時調用一次）
ams_hook = None
try:
    from alfred_memory_system.integration.openclaw_hook import init_ams_hook
    
    # 設置為 True 啟用 Context 監控
    ams_hook = init_ams_hook(enabled=False)
    
    if ams_hook and ams_hook.enabled:
        print("[AMS] Context monitoring enabled")
except ImportError:
    print("[AMS] Not available")
    ams_hook = None
except Exception as e:
    print(f"[AMS] Initialization error: {e}")
    ams_hook = None

# 初始化 AMS 核心（用於記憶同步）
ams_core = None
try:
    from alfred_memory_system import AMS
    ams_core = AMS()
    # 不調用 initialize() 避免重複創建數據庫
except ImportError:
    ams_core = None
except Exception as e:
    print(f"[AMS Core] Initialization error: {e}")
    ams_core = None
```

## 每次對話後檢查 Context

在每次對話處理後添加：

```python
def after_message_processing(messages, session_id=None):
    """每次消息處理後的後續操作"""
    
    # AMS Context 檢查
    if ams_hook and ams_hook.enabled:
        try:
            status = ams_hook.check_context(messages, session_id)
            
            if status and status['usage_percent'] > 70:
                # Context 警告已在 Hook 中打印
                # 可以在這裡添加額外處理
                pass
        except Exception as e:
            # 靜默處理錯誤，避免影響主流程
            pass
```

## 記憶同步（可選）

在適當的時機（例如每天一次）同步記憶：

```python
def sync_memories():
    """同步記憶文件"""
    if ams_core:
        try:
            from alfred_memory_system.integration import sync_all, sync_projects
            
            # 同步記憶文件
            result = sync_all(dry_run=False, db_manager=ams_core.db)
            print(f"[AMS] Memory sync: {result['files_scanned']} files scanned")
            
            # 同步專案
            result = sync_projects(dry_run=False, db_manager=ams_core.db)
            print(f"[AMS] Project sync: {result['projects_found']} projects found")
            
        except Exception as e:
            print(f"[AMS] Sync error: {e}")
```

## 使用 AMS CLI

可以在系統中調用 AMS CLI：

```bash
# 查看狀態
python -m alfred_memory_system.cli status

# 添加學習記錄
python -m alfred_memory_system.cli learning add "重要發現" --type improvement

# 添加專案
python -m alfred_memory_system.cli project add "新專案" --description "描述"

# 同步
python -m alfred_memory_system.cli sync --memory --projects
```

## 注意事項

1. **默認關閉**: 所有 AMS 功能默認關閉，需要手動啟用
2. **非侵入式**: 不修改 OpenClaw 核心，只作為輔助工具
3. **錯誤處理**: 所有 AMS 調用都應該有 try-except 保護
4. **性能**: Context 檢查很快（<10ms），不會影響響應速度

'''

if __name__ == "__main__":
    print("="*70)
    print("AGENTS.md AMS Integration Guide")
    print("="*70)
    print(AMS_INTEGRATION_SNIPPET)
    print("="*70)
    print("\n請將上述內容添加到 AGENTS.md 的適當位置。")
    print("建議添加到 'First Run' 或 'Every Session' 部分。")
