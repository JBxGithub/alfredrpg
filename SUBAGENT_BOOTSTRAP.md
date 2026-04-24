# 子代理啟動強制清單

> 每次啟動必須執行，否則任務無效

---

## ⚠️ 強制步驟（執行前必做）

### 步驟 1: 讀取規範檔案
```
必須讀取：
1. C:\Users\BurtClaw\openclaw_workspace\FILE_MANAGEMENT_PROTOCOL.md
2. C:\Users\BurtClaw\openclaw_workspace\SKILL_PROTOCOL.md
```

### 步驟 2: 檢查現有檔案
```powershell
# 必須執行，記錄結果
Get-ChildItem -Path "[目標位置]" -Recurse | Select-Object Name, FullName
```

### 步驟 3: 報告計劃
```
我計劃：
- 創建檔案: [完整路徑]
- 修改檔案: [完整路徑]
- 預期結果: [說明]
```

---

## 🚫 禁止事項

- 禁止喺根目錄創建檔案
- 禁止重複命名（如 clawtrade-pro vs ClawTradePro）
- 禁止跨目錄重複（skills/ vs private skills/）
- 禁止無文檔創建技能

---

## ✅ 正確流程

### 創建技能：
1. 確認位置: `private skills/[skill-name]/`
2. 檢查現有: `Get-ChildItem "private skills/"`
3. 創建檔案: `SKILL.md`, `scripts/`, `README.md`
4. 更新文檔: 確保 SKILL.md 完整
5. 報告結果: 列出所有創建嘅路徑

### 創建專案：
1. 確認位置: `projects/[project-name]/`
2. 檢查現有: `Get-ChildItem "projects/"`
3. 創建結構: `src/`, `docs/`, `tests/`, `README.md`
4. 更新文檔: 確保 README.md 完整
5. 報告結果: 列出所有創建嘅路徑

---

## 📋 完成後必須報告

```
任務完成報告：
================
✅ 創建檔案:
   - [完整路徑1]
   - [完整路徑2]

✅ 修改檔案:
   - [完整路徑1]

✅ 已讀取規範:
   - FILE_MANAGEMENT_PROTOCOL.md
   - SKILL_PROTOCOL.md

⚠️ 注意事項:
   - [如有]
```

---

**未執行以上步驟，任務視為無效！**
