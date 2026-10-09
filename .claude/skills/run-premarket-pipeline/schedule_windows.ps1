<#
Schedule the premarket pipeline on Windows (Task Scheduler), weekdays.
Usage (PowerShell):
  .\schedule_windows.ps1                      # install at 08:15 ET
  .\schedule_windows.ps1 -TimeET 08:00        # different Eastern time
  .\schedule_windows.ps1 -PipelineArgs '--prompt "Focus on semiconductors" --tickers NVDA,AMD --lang english'
                                              # flags passed to run_pipeline.py on every run
  .\schedule_windows.ps1 -Remove              # delete the task
The Eastern time is converted to this PC's local time zone when the task is created.
Re-run after a daylight-saving change if your PC is not on US Eastern time.
The PC must be on (the task can wake it) and `claude` must be on your PATH.
#>
param(
    [string]$TimeET = "08:15",
    [string]$PipelineArgs = "",
    [string]$TaskName = "PremarketPipeline",
    [switch]$Remove
)

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Output "Removed task $TaskName"
    exit 0
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = (Get-Command python).Source }
$script = Join-Path $PSScriptRoot "run_pipeline.py"

# Convert the Eastern time to local time
$et = [TimeZoneInfo]::FindSystemTimeZoneById("Eastern Standard Time")
$etNow = [TimeZoneInfo]::ConvertTime([DateTime]::Now, $et)
$etTarget = [DateTime]::ParseExact($TimeET, "HH:mm", $null)
$etDateTime = [DateTime]::SpecifyKind((Get-Date -Year $etNow.Year -Month $etNow.Month -Day $etNow.Day -Hour $etTarget.Hour -Minute $etTarget.Minute -Second 0), [DateTimeKind]::Unspecified)
$local = [TimeZoneInfo]::ConvertTime($etDateTime, $et, [TimeZoneInfo]::Local)

$action = New-ScheduledTaskAction -Execute $python -Argument "`"$script`" $PipelineArgs" -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At $local
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Output ("Task '{0}' set for weekdays at {1} ET (= {2:HH:mm} local)." -f $TaskName, $TimeET, $local)
if ($PipelineArgs) { Write-Output "Pipeline flags: $PipelineArgs" }
Write-Output "Test now:  Start-ScheduledTask -TaskName $TaskName"
Write-Output "Logs:      $root\logs\pipeline_<date>.log"
