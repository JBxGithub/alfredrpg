# 六循環系統 - 自學習排程指南

> **版本**: V9.4  
> **更新日期**: 2026-04-23  
> **適用系統**: Windows / Linux / Mac

---

## 📅 排程總覽

| 任務 | 頻率 | 時間 | 功能 | 自動化程度 |
|------|------|------|------|-----------|
| **每日監控** | 每天 | 08:00 | 異常檢測、自動保護 | ✅ 全自動 |
| **每週回顧** | 每週一 | 09:00 | 趨勢分析、生成建議 | ✅ 全自動 |
| **每月調整** | 每月1日 | 10:00 | 長期分析、參數優化 | ⚠️ 可選自動 |
| **持續監控** | 持續 | - | 實時監控、即時警報 | ✅ 全自動 |

---

## 🚀 快速設置

### Windows (PowerShell)

```powershell
# 1. 以管理員身份運行 PowerShell
# 2. 執行設置腳本
.\setup_scheduled_tasks.ps1

# 3. 驗證任務創建
Get-ScheduledTask | Where-Object { $_.TaskName -like "SixLoop-*" }

# 4. 立即測試運行
Start-ScheduledTask -TaskName "SixLoop-Daily-Monitor"
```

### Linux / Mac (Bash)

```bash
# 1. 編輯腳本設置正確路徑
nano setup_cron_jobs.sh
# 修改: PROJECT_PATH="/your/actual/path"

# 2. 執行設置腳本
chmod +x setup_cron_jobs.sh
./setup_cron_jobs.sh

# 3. 驗證任務創建
crontab -l | grep SixLoop-

# 4. 手動測試
cd /your/path && python3 run_adaptive_learning.py --mode daily
```

---

## ⚙️ 詳細配置

### Windows 任務計劃程序

#### 創建任務 (手動)

1. **打開任務計劃程序**
   ```
   Win + R → taskschd.msc
   ```

2. **創建基本任務**
   - 名稱: `SixLoop-Daily-Monitor`
   - 描述: `六循環系統 - 每日監控`

3. **設置觸發器**
   - 每天
   - 開始時間: `08:00:00`
   - 每: `1` 天

4. **設置操作**
   - 程序: `python`
   - 參數: `C:\path\to\run_adaptive_learning.py --mode daily`
   - 起始于: `C:\path\to\six-loop-system`

5. **設置條件**
   - ✅ 喚醒計算機運行此任務
   - ✅ 只有在以下網絡連接可用時才啟動

6. **設置設置**
   - ✅ 允許按需運行任務
   - ✅ 如果任務運行時間超過以下時間，停止任務: `1 小時`
   - ✅ 如果請求後任務仍在運行，強行將其停止

#### 管理任務

```powershell
# 查看所有 SixLoop 任務
Get-ScheduledTask | Where-Object { $_.TaskName -like "SixLoop-*" }

# 啟動任務
Start-ScheduledTask -TaskName "SixLoop-Daily-Monitor"

# 停止任務
Stop-ScheduledTask -TaskName "SixLoop-Daily-Monitor"

# 禁用任務
Disable-ScheduledTask -TaskName "SixLoop-Daily-Monitor"

# 啟用任務
Enable-ScheduledTask -TaskName "SixLoop-Daily-Monitor"

# 刪除任務
Unregister-ScheduledTask -TaskName "SixLoop-Daily-Monitor" -Confirm:$false

# 查看任務歷史
Get-ScheduledTaskInfo -TaskName "SixLoop-Daily-Monitor"
```

### Linux / Mac (Cron)

#### 編輯 Crontab

```bash
# 編輯當前用戶的 crontab
crontab -e

# 查看當前 crontab
crontab -l

# 刪除當前 crontab
crontab -r
```

#### Crontab 語法

```
# .---------------- 分鐘 (0-59)
# |  .------------- 小時 (0-23)
# |  |  .---------- 日期 (1-31)
# |  |  |  .------- 月份 (1-12)
# |  |  |  |  .---- 星期 (0-7, 0和7都是星期日)
# |  |  |  |  |
# *  *  *  *  *  命令

# 示例
0 8 * * *   python run_adaptive_learning.py --mode daily      # 每天 08:00
0 9 * * 1   python run_adaptive_learning.py --mode weekly     # 每週一 09:00
0 10 1 * *  python run_adaptive_learning.py --mode monthly    # 每月1日 10:00
@reboot     python run_adaptive_learning.py --mode continuous # 系統啟動
```

#### 環境變量

```bash
# 在 crontab 頂部設置環境變量
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
PYTHONPATH=/path/to/project
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_db
DB_USER=postgres
DB_PASSWORD=your_password

# 然後是任務
0 8 * * * cd /path && python run_adaptive_learning.py --mode daily
```

---

## 📊 排程流程圖

```
時間軸:
─────────────────────────────────────────────────────────▶

每天 08:00
    │
    ▼
┌─────────────┐
│ 每日監控     │ ──▶ 檢查昨日表現
│ (自動)      │ ──▶ 異常檢測
└─────────────┘ ──▶ 自動保護 (如需要)
    │
    │ 交易日 09:30-16:00
    ▼
┌─────────────┐
│ 交易執行     │ ──▶ 實時交易
│ (持續)      │ ──▶ 風險管理
└─────────────┘ ──▶ 盈利減倉
    │
    │ 每天 16:30
    ▼
┌─────────────┐
│ 每日收盤     │ ──▶ 計算績效
│ (自動)      │ ──▶ 更新成就
└─────────────┘ ──▶ 保存數據
    │
    │ 每週一 09:00
    ▼
┌─────────────┐
│ 每週回顧     │ ──▶ 分析4週趨勢
│ (自動)      │ ──▶ 生成優化建議
└─────────────┘ ──▶ 發送報告
    │
    │ 每月1日 10:00
    ▼
┌─────────────┐
│ 每月調整     │ ──▶ 長期趨勢分析
│ (可選自動)   │ ──▶ 策略漂移檢測
└─────────────┘ ──▶ 自動調整參數
```

---

## 🔔 通知設置

### Discord Webhook

```bash
# 設置環境變量
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Windows PowerShell
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."
```

### 郵件通知 (可選)

```python
# 在 adaptive_learning_config.yaml 中配置
notifications:
  channels:
    - type: "email"
      smtp_server: "smtp.gmail.com"
      smtp_port: 587
      username: "your_email@gmail.com"
      password: "your_app_password"
      to: "alert@yourdomain.com"
      level: ["critical"]
```

---

## 🛠️ 故障排除

### 常見問題

**Q: 任務沒有運行？**

Windows:
```powershell
# 檢查任務狀態
Get-ScheduledTask -TaskName "SixLoop-Daily-Monitor"

# 查看最後運行結果
(Get-ScheduledTask -TaskName "SixLoop-Daily-Monitor").LastTaskResult

# 查看事件日誌
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational'; ID=201} | 
  Where-Object { $_.Message -like "*SixLoop*" }
```

Linux/Mac:
```bash
# 檢查 cron 日誌
tail -f /var/log/syslog | grep CRON

# 檢查郵件 (cron 輸出)
cat /var/mail/$USER
```

**Q: Python 找不到？**

```bash
# 使用完整路徑
which python3
# /usr/bin/python3

# 在 crontab 中使用完整路徑
0 8 * * * /usr/bin/python3 /path/run_adaptive_learning.py --mode daily
```

**Q: 數據庫連接失敗？**

```bash
# 檢查環境變量是否正確設置
env | grep DB_

# 在腳本開頭添加
source /path/to/.env
```

---

## 📈 監控排程健康

### 創建健康檢查腳本

```python
# health_check_scheduler.py
import subprocess
import sys

def check_windows_tasks():
    result = subprocess.run(
        ['powershell', '-Command', 
         'Get-ScheduledTask | Where-Object { $_.TaskName -like "SixLoop-*" } | Select-Object TaskName, State, LastRunTime'],
        capture_output=True, text=True
    )
    print(result.stdout)
    
def check_cron_jobs():
    result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    sixloop_jobs = [line for line in result.stdout.split('\n') if 'SixLoop-' in line]
    for job in sixloop_jobs:
        print(job)

if __name__ == "__main__":
    if sys.platform == "win32":
        check_windows_tasks()
    else:
        check_cron_jobs()
```

---

## 🎯 最佳實踐

1. **先測試後部署**
   ```bash
   # 手動運行測試
   python run_adaptive_learning.py --mode daily
   ```

2. **設置日誌輪轉**
   ```bash
   # Linux: 使用 logrotate
   # Windows: 使用內置日誌管理
   ```

3. **監控磁盤空間**
   ```bash
   # 定期清理舊日誌
   find logs/ -name "*.log" -mtime +30 -delete
   ```

4. **備份配置**
   ```bash
   # 定期備份配置文件
   cp config/v9_4_config.yaml config/backups/v9_4_config_$(date +%Y%m%d).yaml
   ```

---

**排程設置完成後，系統將自動運行，無需人工干預！** 🚀
