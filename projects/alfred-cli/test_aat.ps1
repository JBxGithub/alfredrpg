# AAT 功能驗證腳本

$env:PYTHONPATH = "C:\Users\BurtClaw\openclaw_workspace\projects\skill-analyzer\src;" +
                  "C:\Users\BurtClaw\openclaw_workspace\projects\smart-router\src;" +
                  "C:\Users\BurtClaw\openclaw_workspace\projects\performance-dashboard\src;" +
                  "C:\Users\BurtClaw\openclaw_workspace\projects\snippets-pro\src;" +
                  "C:\Users\BurtClaw\openclaw_workspace\projects\workflow-designer\src;" +
                  "C:\Users\BurtClaw\openclaw_workspace\projects\skill-dev-assistant\src"

Write-Host "🧪 開始驗證 AAT 功能..." -ForegroundColor Cyan
Write-Host ""

$cliPath = "C:\Users\BurtClaw\openclaw_workspace\projects\alfred-cli\alfred.py"

# 測試 1: analyze skills
Write-Host "測試 1: alfred analyze skills" -ForegroundColor Yellow
python $cliPath analyze skills
Write-Host ""

# 測試 2: dashboard show
Write-Host "測試 2: alfred dashboard show" -ForegroundColor Yellow
python $cliPath dashboard show
Write-Host ""

# 測試 3: snippet search
Write-Host "測試 3: alfred snippet search error" -ForegroundColor Yellow
python $cliPath snippet search error
Write-Host ""

# 測試 4: workflow list
Write-Host "測試 4: alfred workflow list" -ForegroundColor Yellow
python $cliPath workflow list
Write-Host ""

# 測試 5: route
Write-Host "測試 5: alfred route 'check trading'" -ForegroundColor Yellow
python $cliPath route "check trading"
Write-Host ""

Write-Host "✅ 驗證完成！" -ForegroundColor Green
