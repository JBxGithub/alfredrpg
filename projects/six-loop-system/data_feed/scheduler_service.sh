#!/bin/bash
REM NQ100 自動更新服務 (Unix/Mac/Linux)
REM 使用方法: ./scheduler_service.sh 或 nohup bash scheduler_service.sh &

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "[NQ100] 啟動排程服務..."
echo "執行時間: 09:30, 14:00, 21:00"
echo

python data_feed/scheduler.py