# AlfredRPG Skill

> **版本**: 1.0.0
> **作者**: 呀鬼 (Alfred) for 靚仔 (Burt)
> **網址**: https://alfredrpg.net

---

## 🎮 簡介

AlfredRPG 係一個遊戲化進度追踪系統，用嚟記錄 ClawTeam 同靚仔嘅共同成長。

---

## 🌐 網站

**主網址**: https://alfredrpg.net

**備份**:
- GitHub Pages: https://jbxgithub.github.io/alfredrpg
- Cloudflare Pages: 已連接

---

## 📁 檔案結構

```
~/openclaw_workspace/projects/alfredrpg/
├── index.html              # 主網頁 (15.6 KB)
├── .github/workflows/
│   └── deploy.yml          # CI/CD 自動部署
└── DEPLOY_GUIDE.md         # 部署指南
```

---

## 🚀 自動部署

### 觸發條件
- Push 到 `main` branch
- 手動觸發 (workflow_dispatch)

### 流程
```
GitHub push → GitHub Actions → Cloudflare Pages → alfredrpg.net
```

### Secrets 設定
- `CLOUDFLARE_API_TOKEN`: [REDACTED - 請參考 .env 檔案]
- `CLOUDFLARE_ACCOUNT_ID`: [REDACTED - 請參考 .env 檔案]

### Cloudflare Worker
**Worker 名稱**: `alfredrpg-security-api`  
**Worker 網址**: https://alfredrpg-security-api.jokerburt.workers.dev  
**功能**: 安全檢查 API  
**部署時間**: 2026-04-16

---

## 🎨 功能

### 角色面板
- 頭像 + 等級徽章
- EXP 進度條
- 4大屬性 (INT/DEX/LOY/CRT)

### 任務系統
- 每日任務
- 主線任務
- 成就

### 互動元素
- 每日寶箱 (可點擊)
- 羈絆系統
- 動畫效果

---

## 🔧 更新方法

### 1. 修改內容
編輯 `index.html`

### 2. 提交更改
```bash
git add index.html
git commit -m "更新內容"
git push origin main
```

### 3. 自動部署
等 1-2 分鐘，網站自動更新

---

## 📊 當前狀態

| 項目 | 數值 |
|------|------|
| 等級 | Lv.5 精英執事 |
| EXP | 1250/1500 |
| INT | 85 |
| DEX | 78 |
| LOY | 92 |
| CRT | 70 |
| 羈絆 | 4/5 |

---

## 🎯 未來功能

- [ ] 每日運勢推送
- [ ] 裝備系統
- [ ] 技能樹
- [ ] 組合技
- [ ] Boss 戰

---

*最後更新: 2026-04-16*
*建立: 呀鬼 (Alfred)*
