[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$TaskName = "MyAgentBackend",
    [ValidateSet("Logon", "Startup")]
    [string]$Trigger = "Logon",
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$startScript = (Resolve-Path (Join-Path $scriptDir "start-backend.ps1")).Path
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

if ($PythonExe) {
    if (-not (Test-Path -LiteralPath $PythonExe)) {
        throw "Python executable not found: $PythonExe"
    }

    $PythonExe = (Resolve-Path -LiteralPath $PythonExe).Path
}

$arguments = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-WindowStyle", "Hidden",
    "-File", "`"$startScript`""
)

if ($PythonExe) {
    $arguments += @("-PythonExe", "`"$PythonExe`"")
}

if ($PSCmdlet.ShouldProcess($TaskName, "Register scheduled task")) {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ($arguments -join " ")
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew `
        -StartWhenAvailable

    if ($Trigger -eq "Startup") {
        $taskTrigger = New-ScheduledTaskTrigger -AtStartup
        $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        Write-Warning "Startup mode runs before login. API calls work, but desktop-interaction tools may need a logged-in user session."
    } else {
        $taskTrigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
        $principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
    }

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $taskTrigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Starts the My Agent backend automatically on Windows." `
        -Force | Out-Null

    Write-Host "Scheduled task '$TaskName' installed with trigger '$Trigger'."
    Write-Host "Task action: powershell.exe $($arguments -join ' ')"
}
