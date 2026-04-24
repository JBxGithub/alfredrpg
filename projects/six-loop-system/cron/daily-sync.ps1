# Six-Loop System Daily Sync
# 每日同步任務狀態和系統監控

Write-Host "=" -ForegroundColor Cyan
Write-Host "Six-Loop System Daily Sync" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan
Write-Host "Time: $(Get-Date)" -ForegroundColor Gray

# Change to project directory
Set-Location "C:\Users\BurtClaw\openclaw_workspace\projects\six-loop-system"

# 1. Run system monitor
Write-Host "`n[1/4] Running system monitor..." -ForegroundColor Yellow
python cron\six_loop_monitor.py

# 2. Update task progress
Write-Host "`n[2/4] Updating task progress..." -ForegroundColor Yellow
python task_manager.py report

# 3. Check Futu data feed
Write-Host "`n[3/4] Checking Futu data feed..." -ForegroundColor Yellow
python -c "
import psycopg2
from datetime import datetime, timezone

conn = psycopg2.connect(
    host='localhost', port=5432, database='trading_db',
    user='postgres', password='PostgresqL'
)
cursor = conn.cursor()

# Check today's Futu data
cursor.execute('''
    SELECT COUNT(*), MAX(timestamp) 
    FROM raw_market_data 
    WHERE source = 'futu_opend' 
    AND timestamp > CURRENT_DATE
''')

count, latest = cursor.fetchone()
print(f'Futu data today: {count} records')
if latest:
    now = datetime.now(timezone.utc)
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=timezone.utc)
    diff = (now - latest).total_seconds() / 60
    print(f'Latest: {latest} ({diff:.1f} minutes ago)')

cursor.close()
conn.close()
"

# 4. Generate daily report
Write-Host "`n[4/4] Generating daily report..." -ForegroundColor Yellow
$report = @"

Six-Loop System Daily Report
============================
Date: $(Get-Date)

System Status:
- Futu OpenD: $(Test-NetConnection -ComputerName 127.0.0.1 -Port 11111 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded)
- Node-RED: $(Test-NetConnection -ComputerName 127.0.0.1 -Port 1880 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded)
- PostgreSQL: $(Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -WarningAction SilentlyContinue | Select-Object -ExpandProperty TcpTestSucceeded)

Next Steps:
- Continue Phase 2: Task Management
- Complete remaining tasks

============================
"@

Write-Host $report -ForegroundColor Green

# Save report
$report | Out-File -FilePath "logs\daily_report_$(Get-Date -Format 'yyyyMMdd').txt" -Encoding UTF8

Write-Host "`nDaily sync completed!" -ForegroundColor Cyan
