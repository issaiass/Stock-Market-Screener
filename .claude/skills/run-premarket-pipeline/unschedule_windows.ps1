<#
Remove the premarket pipeline scheduled task on Windows.
Usage (PowerShell):
  .\unschedule_windows.ps1                       # removes task "PremarketPipeline"
  .\unschedule_windows.ps1 -TaskName MyTask      # removes a differently named task
Only the scheduled task is deleted. Reports, logs and .env are left alone.
#>
param([string]$TaskName = "PremarketPipeline")

$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Output "No scheduled task named '$TaskName' found. Nothing to remove."
    exit 0
}
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Output "Failed to remove '$TaskName'. Try an elevated PowerShell."
    exit 1
}
Write-Output "Removed scheduled task '$TaskName'."
