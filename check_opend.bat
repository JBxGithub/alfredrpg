@echo off
echo [檢查] Futu OpenD 狀態...
netstat -an | findstr "11111"
if %errorlevel% == 0 (
    echo [結果] OpenD 正在運行 (端口 11111)
) else (
    echo [結果] OpenD 未運行 (端口 11111 未偵測到)
)
pause