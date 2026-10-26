param([int]$WaitForPid = 0)
$ErrorActionPreference = 'Stop'
$prior = if ($WaitForPid -gt 0) { Get-Process -Id $WaitForPid -ErrorAction SilentlyContinue } else { $null }
if ($prior -and $prior.ProcessName -eq 'wsl') { $prior.WaitForExit() }
function Invoke-Scene4Trial([string]$method, [string]$name, [int]$limit, [bool]$pilot) {
    wsl --terminate STGPlanner-Ubuntu20 | Out-Null
    $trialArguments = @('-d','STGPlanner-Ubuntu20','-u','root','--','bash','/mnt/d/STGPlanner/benchmarks/run_benchmark.sh',$method,'--name',$name,'--limit',"$limit")
    if ($pilot) { $trialArguments += '--pilot' }
    $p = Start-Process -FilePath wsl.exe -ArgumentList $trialArguments -WindowStyle Hidden -RedirectStandardOutput "D:\STGPlanner\benchmarks\logs\$name.log" -RedirectStandardError "D:\STGPlanner\benchmarks\logs\$name.err" -PassThru
    "$(Get-Date -Format o) start $name pid=$($p.Id)" | Add-Content D:\STGPlanner\benchmarks\logs\suite.log
    $p.WaitForExit()
    $result = Get-Content -Raw "D:\STGPlanner\benchmarks\results\$name\result.json" | ConvertFrom-Json
    "$(Get-Date -Format o) complete $name reason=$($result.finish_reason) area=$($result.area_m2) distance=$($result.distance_m)" | Add-Content D:\STGPlanner\benchmarks\logs\suite.log
    if ($result.fatal_error) { throw "$name fatal error: $($result.fatal_error)" }
    if ($pilot -and (-not $result.validation.planner_produced_motion -or -not $result.validation.stop_ack -or -not $result.validation.parked_command_zero)) { throw "$name interface pilot failed" }
    if (-not $pilot -and $result.finish_reason -notin @('coverage_threshold','sim_time_limit')) { throw "$name runtime failure requires investigation" }
}
foreach ($method in @('gbp2','stgp','fael','tare')) { Invoke-Scene4Trial $method "pilot_${method}_protocol1" 45 $true }
foreach ($method in @('fael','tare','gbp2','stgp')) { Invoke-Scene4Trial $method "formal_${method}_01" 1600 $false }
wsl --terminate STGPlanner-Ubuntu20 | Out-Null
"$(Get-Date -Format o) suite_complete" | Add-Content D:\STGPlanner\benchmarks\logs\suite.log
