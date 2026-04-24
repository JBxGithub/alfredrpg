@echo off
chcp 65001 >nul
echo ==========================================
echo OpenClaw Gateway Auto-Start Setup
echo ==========================================
echo.

:: Check admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Please run as Administrator
    echo Right-click - Run as administrator
    pause
    exit /b 1
)

echo [1/4] Creating log directory...
if not exist "%USERPROFILE%\.openclaw\logs" mkdir "%USERPROFILE%\.openclaw\logs"
echo Done
echo.

echo [2/4] Creating Task Scheduler job...

:: Delete old job if exists
schtasks /delete /tn "OpenClawGatewayAutoStart" /f >nul 2>&1

:: Create new job with XML for better control
set "TEMP_XML=%TEMP%\openclaw-task.xml"

(
echo ^<?xml version="1.0" encoding="UTF-16"?^>
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^>
echo   ^<RegistrationInfo^>
echo     ^<Description^>Auto-start OpenClaw Gateway on boot, detect Windows Update reboots and send WhatsApp notification^</Description^>
echo   ^</RegistrationInfo^>
echo   ^<Triggers^>
echo     ^<BootTrigger^>
echo       ^<Enabled^>true^</Enabled^>
echo       ^<Delay^>PT30S^</Delay^>
echo     ^</BootTrigger^>
echo     ^<LogonTrigger^>
echo       ^<Enabled^>true^</Enabled^>
echo       ^<Delay^>PT30S^</Delay^>
echo     ^</LogonTrigger^>
echo   ^</Triggers^>
echo   ^<Principals^>
echo     ^<Principal id="Author"^>
echo       ^<LogonType^>InteractiveToken^</LogonType^>
echo       ^<RunLevel^>HighestAvailable^</RunLevel^>
echo     ^</Principal^>
echo   ^</Principals^>
echo   ^<Settings^>
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^>
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^>
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^>
echo     ^<AllowHardTerminate^>true^</AllowHardTerminate^>
echo     ^<StartWhenAvailable^>true^</StartWhenAvailable^>
echo     ^<RunOnlyIfNetworkAvailable^>false^</RunOnlyIfNetworkAvailable^>
echo     ^<IdleSettings^>
echo       ^<StopOnIdleEnd^>false^</StopOnIdleEnd^>
echo       ^<RestartOnIdle^>false^</RestartOnIdle^>
echo     ^</IdleSettings^>
echo     ^<AllowStartOnDemand^>true^</AllowStartOnDemand^>
echo     ^<Enabled^>true^</Enabled^>
echo     ^<Hidden^>false^</Hidden^>
echo     ^<RunOnlyIfIdle^>false^</RunOnlyIfIdle^>
echo     ^<WakeToRun^>false^</WakeToRun^>
echo     ^<ExecutionTimeLimit^>PT1H^</ExecutionTimeLimit^>
echo     ^<Priority^>7^</Priority^>
echo     ^<RestartOnFailure^>
echo       ^<Interval^>PT5M^</Interval^>
echo       ^<Count^>3^</Count^>
echo     ^</RestartOnFailure^>
echo   ^</Settings^>
echo   ^<Actions Context="Author"^>
echo     ^<Exec^>
echo       ^<Command^>powershell.exe^</Command^>
echo       ^<Arguments^>-ExecutionPolicy Bypass -WindowStyle Normal -File "C:\Users\BurtClaw\openclaw_workspace\scripts\gateway-auto-start.ps1"^</Arguments^>
echo       ^<WorkingDirectory^>C:\Users\BurtClaw\openclaw_workspace^</WorkingDirectory^>
echo     ^</Exec^>
echo   ^</Actions^>
echo ^</Task^>
) > "%TEMP_XML%"

schtasks /create /tn "OpenClawGatewayAutoStart" /xml "%TEMP_XML%" /f
set TASK_RESULT=%errorLevel%

del "%TEMP_XML%" 2>nul

if %TASK_RESULT% equ 0 (
    echo Job created successfully
echo.
    
    echo [3/4] Verifying setup...
    schtasks /query /tn "OpenClawGatewayAutoStart" /fo list 2>nul | findstr "TaskName"
    if %errorLevel% equ 0 (
        echo.
        echo ==========================================
        echo Setup Complete!
        echo ==========================================
        echo.
        echo Job Name: OpenClawGatewayAutoStart
        echo Triggers: System boot + User logon
        echo Delay: 30 seconds
        echo Window: Visible (Foreground)
        echo.
        echo Test command:
        echo   schtasks /run /tn "OpenClawGatewayAutoStart"
        echo.
        echo View logs:
        echo   %USERPROFILE%\.openclaw\logs\gateway-auto-start.log
        echo.
    ) else (
        echo [WARNING] Verification failed, please check Task Scheduler manually
    )
) else (
    echo [ERROR] Job creation failed, error code: %TASK_RESULT%
    echo Trying alternative method...
    
    schtasks /create ^
        /tn "OpenClawGatewayAutoStart" ^
        /tr "powershell.exe -ExecutionPolicy Bypass -WindowStyle Normal -File 'C:\Users\BurtClaw\openclaw_workspace\scripts\gateway-auto-start.ps1'" ^
        /sc onstart ^
        /delay 30 ^
        /f
    
    if %errorLevel% equ 0 (
        echo Alternative method succeeded
    ) else (
        echo [ERROR] Alternative method also failed
    )
)

echo.
pause
