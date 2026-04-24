# FutuTradingBot Strategy Config Panel

專業級交易策略參數調整面板，支持多種交易策略配置。

## 功能特性

### 策略支持
- **TQQQ策略**: Z-Score均值回歸 + RSI過濾
- **Trend策略**: EMA趨勢跟踪 + 指標共振
- **ZScore策略**: 純Z-Score均值回歸
- **Breakout策略**: 突破交易 + 成交量確認
- **Momentum策略**: 動量交易 + RSI過濾
- **FlexibleArbitrage策略**: 靈活套利 + 動態調整

### MTF多時間框架
- MTF分析開關
- MACD-V指標
- 背離檢測
- 時間框架權重調整（月/週/日）
- 最低評分閾值

### 風險控制
- 單筆最大風險限制
- 每日最大虧損限制
- 最大持倉數限制
- 部分獲利功能
- 動態止損功能

### 系統功能
- 參數滑動條/輸入框
- 實時參數驗證
- 配置保存/重置/套用
- JSON配置導出/導入

## 技術棧

- **前端**: React + TypeScript
- **後端**: Python FastAPI
- **樣式**: CSS3 (深色主題 + 金色強調)

## 安裝與運行

### 後端
```bash
cd backend
pip install -r requirements.txt
python main.py
```

後端服務將在 http://localhost:8000 運行

### 前端
```bash
cd frontend
npm install
npm start
```

前端應用將在 http://localhost:3000 運行

## API端點

- `GET /api/config` - 獲取當前配置
- `POST /api/config` - 更新配置
- `POST /api/config/reset` - 重置為默認配置
- `POST /api/config/save/{filename}` - 保存配置到文件
- `POST /api/config/load/{filename}` - 從文件加載配置
- `GET /api/config/list` - 列出保存的配置
- `POST /api/config/export` - 導出配置
- `POST /api/config/import` - 導入配置
- `POST /api/config/apply` - 應用配置到交易系統
- `GET /api/strategies` - 獲取策略列表
- `GET /api/validate` - 驗證配置

## 設計風格

- **主色調**: #1a1a2e (深藍黑)
- **強調色**: #ffd700 (金色)
- **輔助色**: #252538, #3d3d5c
- **字體**: 系統默認無襯線字體

## 開發團隊

FutuTradingBot Development Team
