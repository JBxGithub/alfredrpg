# 技能使用日誌

> 記錄每次技能使用，建立「肌肉記憶」

## 2026-04-09

### 今日使用技能
| 時間 | 技能 | 任務 | 效果 | 備註 |
|------|------|------|------|------|
| 16:20 | openclaw skills list | 檢查可用技能 | ✅ 成功 | 96個技能可用 |
| 16:30 | web_fetch | 獲取OpenClaw changelog | ✅ 成功 | 用於版本對比 |
| 19:35 | read / write | 更新 SKILL_PROTOCOL.md | ✅ 成功 | 完整分類96個技能 |
| 19:40 | edit | 更新 skill-usage-log.md | ✅ 成功 | 記錄技能使用 |

### 學到嘅教訓
1. `openclaw gateway restart` 經常失效，要用 PowerShell 直接 kill process
2. `web_fetch` 比 `web_search` 可靠（後者需要 Brave API key）
3. 群組 mention 問題係 `wasMentioned: false`，唔係配置問題
4. 建立 SKILL_PROTOCOL.md v2.0，分類10大類技能，有決策樹輔助選擇
5. 技能使用要記錄，累積「肌肉記憶」

### 待測試技能
- [ ] opencode-controller（未實際用過）
- [ ] parallel（高精度研究）
- [ ] agenthub（agent-to-agent 通訊）

---

## 使用模板

### 新增記錄
```markdown
| 時間 | 技能 | 任務 | 效果 | 備註 |
|------|------|------|------|------|
| HH:MM | 技能名 | 做咩 | ✅/❌ | 特別注意事項 |
```

### 記錄教訓
```markdown
### 學到嘅教訓
1. 教訓內容
2. 改善建議
```
