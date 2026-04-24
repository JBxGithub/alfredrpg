#!/bin/bash
# 六循環系統 - 自學習排程設置腳本 (Linux/Mac)
# 使用 cron 設置定時任務

PROJECT_PATH="/path/to/six-loop-system"
PYTHON_PATH="python3"

echo "=========================================="
echo "  六循環系統 V9.4 - Cron 排程設置"
echo "=========================================="
echo ""

# 檢查 cron 是否安裝
if ! command -v crontab &> /dev/null; then
    echo "❌ 未安裝 cron，請先安裝:"
    echo "   Ubuntu/Debian: sudo apt-get install cron"
    echo "   CentOS/RHEL: sudo yum install cronie"
    exit 1
fi

# 創建臨時 crontab 文件
TEMP_CRON=$(mktemp)

# 導出現有 crontab
crontab -l > "$TEMP_CRON" 2>/dev/null || echo "# 新建 crontab" > "$TEMP_CRON"

# 移除舊的六循環任務
sed -i '/# SixLoop-/d' "$TEMP_CRON"

# 添加新的六循環任務
cat >> "$TEMP_CRON" << EOF

# SixLoop-自動學習系統排程 (創建於 $(date '+%Y-%m-%d'))

# 每日監控 - 每天 08:00
0 8 * * * cd $PROJECT_PATH && $PYTHON_PATH run_adaptive_learning.py --mode daily >> logs/cron_daily.log 2>&1 # SixLoop-Daily-Monitor

# 每週回顧 - 每週一 09:00
0 9 * * 1 cd $PROJECT_PATH && $PYTHON_PATH run_adaptive_learning.py --mode weekly >> logs/cron_weekly.log 2>&1 # SixLoop-Weekly-Review

# 每月調整 - 每月1日 10:00
0 10 1 * * cd $PROJECT_PATH && $PYTHON_PATH run_adaptive_learning.py --mode monthly >> logs/cron_monthly.log 2>&1 # SixLoop-Monthly-Adjustment

# 持續監控 - 系統啟動時運行 (需要 @reboot 支持)
@reboot cd $PROJECT_PATH && $PYTHON_PATH run_adaptive_learning.py --mode continuous >> logs/cron_continuous.log 2>&1 # SixLoop-Continuous-Monitor
EOF

# 安裝新的 crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✅ Cron 任務已創建！"
echo ""
echo "任務列表:"
echo "  1. 每日監控      - 每天 08:00"
echo "  2. 每週回顧      - 每週一 09:00"
echo "  3. 每月調整      - 每月1日 10:00"
echo "  4. 持續監控      - 系統啟動時"
echo ""
echo "查看所有任務:"
echo "  crontab -l | grep SixLoop-"
echo ""
echo "手動測試運行:"
echo "  cd $PROJECT_PATH && $PYTHON_PATH run_adaptive_learning.py --mode daily"
echo ""
echo "日誌位置:"
echo "  $PROJECT_PATH/logs/cron_*.log"
echo ""
