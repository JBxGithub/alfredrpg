# AMS v2.1 升級提案：智能 Context 管理

> **提案日期**: 2026-04-11  
> **提案人**: 靚仔 + 呀鬼  
> **目標版本**: 2.1.0  
> **核心功能**: 自動 Summarize → Compact → 重新讀取

---

## 🎯 問題陳述

### 現狀問題
```
Context 接近上限 (85-95%)
    ↓
系統自動 Compact
    ↓
詳細對話變成簡短 Summary
    ↓
我失憶：「你想我做咩？」
    ↓
用戶煩躁：「又要重複講？」
```

### 理想流程
```
Context 達 85% (可配置)
    ↓
[Step 1] 📝 自動 Summarize
         → 生成詳細記錄
         → 寫入 memory/2026-04-11-session.md
         → 更新 project-states/*.md
         → 保存關鍵數據到 JSON
    ↓
[Step 2] 🗜️ 自動 Compact
         → 壓縮 Context (146k → 2.1k)
         → 釋放 99% 空間
    ↓
[Step 3] 📖 自動重新讀取
         → 載入剛保存的 memory 文件
         → 回復完整狀態
    ↓
✅ 無縫繼續：「繼續處理 FutuTradingBot 部署」
```

---

## 📐 新架構設計

### 新增組件：Context Lifecycle Manager

```
┌─────────────────────────────────────────────────────────────────┐
│              Context Lifecycle Manager (NEW v2.1)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  觸發條件 (Configurable Thresholds)                      │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐                   │   │
│  │  │  70%    │ │  85%    │ │  95%    │                   │   │
│  │  │ 警告    │ │ 存檔    │ │ 強制    │                   │   │
│  │  │ (現有)  │ │ (新增)  │ │ (現有)  │                   │   │
│  │  └────┬────┘ └────┬────┘ └────┬────┘                   │   │
│  │       └─────────────┴─────────────┘                      │   │
│  │                     │                                    │   │
│  │                     ▼                                    │   │
│  │       ┌─────────────────────────┐                       │   │
│  │       │   Smart Compact Flow    │                       │   │
│  │       │   (智能壓縮流程)         │                       │   │
│  │       └───────────┬─────────────┘                       │   │
│  │                   │                                      │   │
│  │    ┌──────────────┼──────────────┐                      │   │
│  │    ▼              ▼              ▼                      │   │
│  │ ┌──────┐     ┌──────┐     ┌──────┐                     │   │
│  │ │Save  │     │Compact│    │Reload│                     │   │
│  │ │保存  │ ──▶ │壓縮  │ ──▶ │重載  │                     │   │
│  │ └──────┘     └──────┘     └──────┘                     │   │
│  │    │              │              │                      │   │
│  │    ▼              ▼              ▼                      │   │
│  │ memory/*.md   Context 2.1k   重新載入                  │   │
│  │ project-states/  釋放空間    關鍵文件                  │   │
│  │ data/*.json                                 │           │   │
│  │                                             ▼           │   │
│  │                                    ┌──────────────┐     │   │
│  │                                    │ 無縫繼續對話  │     │   │
│  │                                    └──────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 技術實現

### 1. 新增核心模組

```python
# core/context_lifecycle_manager.py

class ContextLifecycleManager:
    """
    智能 Context 生命周期管理器
    實現 Summarize → Compact → Reload 自動化
    """
    
    def __init__(self):
        self.thresholds = {
            'warning': 70,      # 現有：發出警告
            'archive': 85,      # 新增：觸發存檔流程
            'critical': 95      # 現有：強制處理
        }
    
    def check_and_handle(self, current_usage: int) -> LifecycleAction:
        """
        檢查 Context 使用率並執行相應操作
        """
        if current_usage >= 95:
            return self._emergency_compact()
        elif current_usage >= 85:
            return self._smart_compact_flow()
        elif current_usage >= 70:
            return self._warn_user()
    
    def _smart_compact_flow(self) -> LifecycleAction:
        """
        智能壓縮流程：Summarize → Compact → Reload
        """
        # Step 1: 生成詳細摘要並保存
        summary = self._generate_detailed_summary()
        self._save_to_memory_files(summary)
        
        # Step 2: 通知 OpenClaw 執行 Compact
        self._trigger_compact()
        
        # Step 3: 重新載入關鍵文件
        self._reload_critical_files()
        
        return LifecycleAction.COMPLETED
    
    def _generate_detailed_summary(self) -> SessionSummary:
        """
        生成詳細對話摘要
        """
        return {
            'timestamp': datetime.now(),
            'session_key': self.session_key,
            'goal': self.extract_goal(),
            'progress': self.extract_progress(),
            'decisions': self.extract_decisions(),
            'next_actions': self.extract_next_actions(),
            'key_data': self.extract_key_data()
        }
    
    def _save_to_memory_files(self, summary: SessionSummary):
        """
        保存到多個記憶文件
        """
        # 1. 每日 Session 記錄
        write_memory_file(f"memory/{date}-session.md", summary)
        
        # 2. 專案狀態更新
        update_project_state(summary['project'], summary['progress'])
        
        # 3. 關鍵數據 JSON
        write_json(f"data/session_{timestamp}.json", summary['key_data'])
    
    def _reload_critical_files(self):
        """
        Compact 後重新載入關鍵文件
        """
        files_to_reload = [
            f"memory/{date}-session.md",
            "MEMORY.md",
            f"project-states/{active_project}-STATUS.md"
        ]
        return files_to_reload
```

### 2. 修改 Context Monitor

```python
# core/context_monitor.py (升級版)

class ContextMonitor:
    def __init__(self):
        self.thresholds = {
            70: self._on_warning,
            85: self._on_archive,    # 新增
            95: self._on_critical
        }
    
    def _on_archive(self, usage: int):
        """
        85% 觸發：智能存檔流程
        """
        # 調用 ContextLifecycleManager
        lifecycle = ContextLifecycleManager()
        return lifecycle.check_and_handle(usage)
```

### 3. 新增 OpenClaw 整合 Hook

```python
# integration/openclaw_lifecycle_hook.py

class OpenClawLifecycleHook:
    """
    與 OpenClaw 系統整合，實現自動 Compact 和 Reload
    """
    
    def on_context_threshold_reached(self, threshold: int):
        if threshold == 85:
            # 執行 Summarize + Save
            self._archive_current_session()
            
            # 通知 OpenClaw 執行 Compact
            self._request_compact()
            
            # Compact 完成後自動 Reload
            self._auto_reload()
    
    def _request_compact(self):
        """
        觸發 OpenClaw Compact 功能
        """
        # 透過系統指令或 API 觸發
        pass
    
    def _auto_reload(self):
        """
        Compact 後自動重新載入關鍵文件
        """
        files = self.lifecycle_manager.get_files_to_reload()
        for file in files:
            self.read_file(file)
```

---

## 📋 配置文件更新

```yaml
# ~/.ams/config.yaml (v2.1)

version: "2.1.0"

context:
  enabled: true
  thresholds:
    warning: 70      # 發出警告
    archive: 85      # 觸發智能存檔 (NEW)
    critical: 95     # 強制處理
  
  lifecycle:         # 新增配置區塊
    auto_archive: true
    auto_compact: true
    auto_reload: true
    
    archive_targets:  # 存檔目標
      - memory/{date}-session.md
      - project-states/{project}-STATUS.md
      - data/session_{timestamp}.json
    
    reload_files:     # 重載文件
      - memory/{date}-session.md
      - MEMORY.md
      - project-states/{project}-STATUS.md

summarizer:
  enabled: true
  detail_level: "high"    # high | medium | low
  extract_decisions: true
  extract_actions: true
  preserve_code: true     # 保留代碼塊
```

---

## 🔄 新運作流程

### 完整流程圖

```
用戶對話進行中
    │
    ▼
┌─────────────────────┐
│  Context Monitor    │
│  檢查使用率          │
└──────────┬──────────┘
           │
           ▼
    達到 85%?
           │
    ┌──────┴──────┐
    │             │
   否            是
    │             │
    ▼             ▼
繼續對話    ┌─────────────────┐
            │ Smart Compact   │
            │ 流程啟動        │
            └────────┬────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌────────┐  ┌────────┐  ┌────────┐
   │Summarize│  │Compact │  │Reload  │
   │生成摘要 │  │壓縮    │  │重載    │
   └────┬───┘  └────┬───┘  └────┬───┘
        │           │           │
        ▼           ▼           ▼
   memory/*.md  Context 2k  關鍵文件
   project-states/ 釋放空間  重新載入
        │                       │
        └───────────┬───────────┘
                    ▼
            ┌──────────────┐
            │ 無縫繼續對話  │
            │ 「繼續處理...」│
            └──────────────┘
```

---

## 📊 與現有系統整合

### 整合點

| 現有組件 | 整合方式 | 效果 |
|---------|---------|------|
| Context Monitor | 加入 85% 觸發器 | 自動啟動流程 |
| Summarizer | 調用詳細摘要生成 | 高質量存檔 |
| Memory Manager | 保存到多個目標 | 冗餘保護 |
| Skill Hook | 對話後檢查 | 實時監控 |

### 文件輸出

```
~/openclaw_workspace/
├── memory/
│   ├── 2026-04-11.md              # 現有：每日記錄
│   ├── 2026-04-11-session.md      # 新增：Session 詳細記錄
│   └── 2026-04-11-compact-1.md    # 新增：第1次 Compact 記錄
│
├── project-states/
│   ├── FutuTradingBot-STATUS.md   # 現有
│   └── FutuTradingBot-STATUS-2026-04-11.md  # 新增：每日備份
│
└── alfred_memory_system/
    └── data/
        ├── session_2026-04-11-184500.json   # 新增：結構化數據
        └── compact_history.json             # 新增：Compact 歷史
```

---

## 🎯 用戶體驗對比

### Before (v2.0)
```
[對話進行中，Context 達 90%]

系統: [自動 Compact]

我: 「你想我做咩？」

靚仔: 「又要重複講？剛才講咗...」

[浪費時間，煩躁]
```

### After (v2.1)
```
[對話進行中，Context 達 85%]

系統: [自動執行 Smart Compact]
      📝 已保存 Session 記錄
      🗜️ 已壓縮 Context
      📖 已重新載入關鍵文件

我: 「繼續處理 FutuTradingBot 部署，
      剛才講到準備測試 cron jobs...」

靚仔: [無縫繼續]

[流暢，高效]
```

---

## 🚀 實施計劃

### Phase 1: 核心功能 (1-2 天)
- [ ] 創建 `ContextLifecycleManager` 類
- [ ] 升級 `ContextMonitor` 加入 85% 觸發
- [ ] 實現詳細 Summarizer

### Phase 2: 整合測試 (1 天)
- [ ] 與 OpenClaw Compact 整合
- [ ] 測試自動 Reload 流程
- [ ] 驗證文件輸出

### Phase 3: 優化調整 (1 天)
- [ ] 調整摘要質量
- [ ] 優化重載文件選擇
- [ ] 用戶體驗測試

---

## 📝 下一步行動

靚仔，請指示：

1. **立即開始實施** — 我開始編寫 v2.1 代碼
2. **調整設計** — 修改某些細節
3. **先測試現有功能** — 驗證 AMS v2.0 運作正常
4. **其他優先事項** — 暫緩此升級

---

*提案由 呀鬼 (Alfred) 編寫*  
*日期: 2026-04-11*  
*版本: v2.1.0 Proposal*
