# 子代理任務模板

## 任務前必須執行

**⚠️ 重要：執行任務前，必須完成以下步驟：**

1. **讀取規範檔案**（強制）
   ```
   read: C:\Users\BurtClaw\openclaw_workspace\SUBAGENT_BOOTSTRAP.md
   read: C:\Users\BurtClaw\openclaw_workspace\FILE_MANAGEMENT_PROTOCOL.md
   read: C:\Users\BurtClaw\openclaw_workspace\SKILL_PROTOCOL.md
   ```

2. **檢查現有檔案**（強制）
   ```powershell
   Get-ChildItem -Path "[目標位置]" -Recurse | Select-Object Name, FullName
   ```

3. **報告計劃**（強制）
   - 我將創建：[檔案列表]
   - 我將修改：[檔案列表]

---

## 實際任務

[任務描述]

---

## 完成後必須報告

- [ ] 列出所有創建/修改嘅檔案完整路徑
- [ ] 確認已讀取所有規範檔案
- [ ] 報告任何異常情況

---

**未執行「任務前必須執行」步驟，任務將被拒絕！**
