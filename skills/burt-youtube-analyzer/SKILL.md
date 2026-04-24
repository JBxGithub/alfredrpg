---
name: burt-youtube-analyzer
version: 2.0.0
description: Private YouTube video analyzer for Burt. Extract metadata, analyze content, and facilitate discussions. Not for public sharing.
author: Alfred (for Burt only)
private: true
---

# Burt's YouTube Analyzer v2.0

私人 YouTube 影片分析工具，專為靚仔設計。

## 核心協議 (2026-03-27 確立)

**溝通模式：**
```
Burt 分享影片 + 簡述內容 → Alfred 分析 → 雙方討論 → 提煉洞察/行動
```

**目標：** 每次都有真實 output — 新理解、新決定、或改進。

## Features

- 提取影片 metadata（標題、作者、描述、觀看數等）
- 分析影片內容趨勢
- 支援 YouTube Shorts
- 生成討論要點
- **v2.0 新增：** 內容策展分析（合作模式學習）

## Usage

```python
from skills.burt_youtube_analyzer import analyze_video

result = analyze_video("https://youtube.com/shorts/...")
# Returns: title, author, duration, description, view_count, discussion_prompts, etc.
```

## Workflow

1. **收到影片** → 自動提取 metadata
2. **Burt 簡述內容** → Alfred 結合分析
3. **雙方討論** → 探索應用/啟發
4. **記錄洞察** → 更新 MEMORY.md / 啟發資料庫

## CLI

```bash
python skills/burt-youtube-analyzer/analyzer.py <url>
```

## Notes

- Private skill for Burt & Alfred only
- Requires yt-dlp and ffmpeg
- Created: 2026-03-27
- Updated: 2026-03-27 (v2.0 - 加入溝通協議)
