$ErrorActionPreference = 'Stop'
foreach ($repairMethod in @('fael','gbp2')) {
    $repairName = "repair_formal_${repairMethod}_01"
    if (Test-Path -LiteralPath "D:\STGPlanner\benchmarks\results\$repairName") { throw "Refusing to overwrite $repairName" }
    wsl --terminate STGPlanner-Ubuntu20 | Out-Null
    $repairArgs = @('-d','STGPlanner-Ubuntu20','-u','root','--','bash','/mnt/d/STGPlanner/benchmarks/run_benchmark.sh',$repairMethod,'--name',$repairName,'--limit','2400')
    $repairProcess = Start-Process -FilePath wsl.exe -ArgumentList $repairArgs -WindowStyle Hidden -RedirectStandardOutput "D:\STGPlanner\benchmarks\logs\$repairName.log" -RedirectStandardError "D:\STGPlanner\benchmarks\logs\$repairName.err" -PassThru
    "$(Get-Date -Format o) start $repairName pid=$($repairProcess.Id)" | Add-Content D:\STGPlanner\benchmarks\logs\progress_suite.log
    $repairProcess.WaitForExit()
    $repairResult = Get-Content -Raw -LiteralPath "D:\STGPlanner\benchmarks\results\$repairName\result.json" | ConvertFrom-Json
    "$(Get-Date -Format o) complete $repairName reason=$($repairResult.finish_reason) area=$($repairResult.area_m2) distance=$($repairResult.distance_m)" | Add-Content D:\STGPlanner\benchmarks\logs\progress_suite.log
    if ($repairResult.fatal_error -or $repairResult.finish_reason -notin @('coverage_threshold','sim_time_limit')) { throw "$repairName runtime failure" }
}
wsl --terminate STGPlanner-Ubuntu20 | Out-Null
"$(Get-Date -Format o) progress_suite_complete" | Add-Content D:\STGPlanner\benchmarks\logs\progress_suite.log
