@echo off
powershell -NoProfile -Command ^
"$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'; ^
$folder = \"$env:C:\Users\BurtClaw\openclaw_workspace\OpenClaw_Screenshots\"; ^
if (-not (Test-Path $folder)) { New-Item -Path $folder -ItemType Directory -Force }; ^
$outputPath = \"$folder\desktop_full_$timestamp.png\"; ^
Add-Type -AssemblyName System.Windows.Forms; ^
Add-Type -AssemblyName System.Drawing; ^
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; ^
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height; ^
$graphics = [System.Drawing.Graphics]::FromImage($bitmap); ^
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size); ^
$bitmap.Save($outputPath); ^
$graphics.Dispose(); $bitmap.Dispose(); ^
Write-Host 'Screenshot saved to OpenClaw_Screenshots folder: ' $outputPath"
