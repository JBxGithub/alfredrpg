param (
    [string]$action,
    [string]$paramsJson = '{}'
)

Set-Location "$skillDir"

$env:PYTHONPATH = "$skillDir"

try {
    $cmd = "python -m desktop_control --action `"$action`" --params `"$paramsJson`""
    $result = Invoke-Expression $cmd 2>&1
    Write-Output $result
}
catch {
    Write-Output "Error: $($_.Exception.Message)"
}
finally {
    Set-Location "C:\Users\BurtClaw\openclaw_workspace"
}
