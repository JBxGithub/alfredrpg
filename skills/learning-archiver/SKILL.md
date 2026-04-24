# Learning Archiver

> 自動學習歸檔系統 - 將錯誤和經驗自動記錄到 Self-Improving 系統

**版本**: 1.0.0  
**類型**: Auto-Trigger Skill  
**執行方式**: OpenCode ACP (agentId: opencode)  
**觸發時機**: 每次對話結束後自動執行

---

## 功能

1. **錯誤自動檢測** - 識別用戶糾正、工具失敗、異常終止
2. **經驗自動提取** - 識別成功模式、高效做法、創新解決方案
3. **自動歸檔** - 寫入 ERRORS.md 或 LEARNINGS.md
4. **每週彙整** - 為 Self-Improving Weekly Review 準備數據

---

## 觸發條件

```python
def should_archive(session):
    # 條件 1: 用戶明確糾正
    if user_said(["錯了", "不對", "應該是", "不是這樣", "stop", "delete"]):
        return True, "ERROR"
    
    # 條件 2: 工具調用失敗
    if tool_call_failed():
        return True, "ERROR"
    
    # 條件 3: 複雜任務完成 (>5 tool calls)
    if tool_calls_count > 5 and success:
        return True, "LEARNING"
    
    # 條件 4: 用戶明確表示記住
    if user_said(["記住", "記得", "以後要", "下次"]):
        return True, "LEARNING"
    
    return False, None
```

---

## 檔案位置

- **錯誤記錄**: `~/.openclaw/skills/self-improving/.learnings/ERRORS.md`
- **經驗記錄**: `~/.openclaw/skills/self-improving/.learnings/LEARNINGS.md`
- **日誌**: `~/.openclaw/skills/learning-archiver/logs/`

---

## 輸出格式

### ERRORS.md 條目
```markdown
## YYYY-MM-DD - 錯誤簡述

**錯誤描述**: [具體描述]
**影響**: [影響範圍]
**糾正措施**: [如何修正]
**預防方案**: [如何避免]
**參考**: [相關檔案]
```

### LEARNINGS.md 條目
```markdown
## YYYY-MM-DD - 經驗簡述

**情境**: [什麼情況]
**做法**: [具體做法]
**效果**: [結果如何]
**可重用性**: [高/中/低]
```

---

## 自動化流程

```
對話結束
    │
    ▼
檢測觸發條件
    │
    ├── 錯誤? ──▶ 寫入 ERRORS.md
    │
    └── 經驗? ──▶ 寫入 LEARNINGS.md
                    │
                    ▼
              更新每週彙整數據
```

---

## Cron Job 整合

此 Skill 由以下機制觸發：
- **Hook**: `session-memory` (每次對話後)
- **Cron**: 無需獨立 cron，被動觸發

---

## 注意事項

- 只記錄**可學習**的內容，避免冗餘
- 保護用戶隱私，不記錄敏感數據
- 定期清理舊記錄（保留 90 天）
