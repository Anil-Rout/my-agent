[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$TaskName = "MyAgentBackend"
)

$ErrorActionPreference = "Stop"

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Host "Scheduled task '$TaskName' was not found."
    exit 0
}

if ($PSCmdlet.ShouldProcess($TaskName, "Unregister scheduled task")) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Scheduled task '$TaskName' removed."
}
