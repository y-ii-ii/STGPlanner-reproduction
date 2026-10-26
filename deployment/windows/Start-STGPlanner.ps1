param([switch]$Headless)
$ErrorActionPreference = 'Stop'
$gui = if ($Headless) { 'false' } else { 'true' }
Write-Host 'Starting STGPlanner (Scene4). Press Ctrl+C to stop.'
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/run.sh Scene4 $gui
exit $LASTEXITCODE
