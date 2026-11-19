[CmdletBinding()]
param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

function Resolve-PythonPath {
    param(
        [string]$Preferred,
        [string]$RepoRoot,
        [string]$BackendDir
    )

    if ($Preferred) {
        if (Test-Path -LiteralPath $Preferred) {
            return (Resolve-Path -LiteralPath $Preferred).Path
        }

        throw "Python executable not found: $Preferred"
    }

    $candidates = @(
        (Join-Path $RepoRoot ".venv\Scripts\python.exe"),
        (Join-Path $RepoRoot "venv\Scripts\python.exe"),
        (Join-Path $BackendDir ".venv\Scripts\python.exe"),
        (Join-Path $BackendDir "venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return $pythonCommand.Source
    }

    throw "Python executable not found. Pass -PythonExe with your python.exe path."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..\..")).Path
$backendDir = Join-Path $repoRoot "backend"
$logsDir = Join-Path $backendDir "logs"
$logFile = Join-Path $logsDir "autostart.log"

New-Item -ItemType Directory -Path $logsDir -Force | Out-Null

$resolvedPython = Resolve-PythonPath -Preferred $PythonExe -RepoRoot $repoRoot -BackendDir $backendDir
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $logFile -Value "$timestamp | Starting backend with $resolvedPython"

Push-Location $backendDir
try {
    & $resolvedPython run.py *>> $logFile
}
finally {
    Pop-Location
}
