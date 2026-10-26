$ErrorActionPreference = 'Stop'
$StgRepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$StgExpectedRoot = 'D:\STGPlanner\catkin_ws\src\STGPlanner'
if ($StgRepositoryRoot.TrimEnd('\') -ne $StgExpectedRoot) {
    throw "Clone this repository into $StgExpectedRoot before installing the fixed-path deployment tools."
}
$StgScriptDirectory = 'D:\STGPlanner\scripts'
New-Item -ItemType Directory -Force -Path $StgScriptDirectory | Out-Null
Copy-Item -Path (Join-Path $PSScriptRoot 'scripts\*') -Destination $StgScriptDirectory -Force
Copy-Item -Path (Join-Path $PSScriptRoot 'windows\*') -Destination 'D:\STGPlanner' -Force
Write-Host 'Deployment tools synchronized from the current checked-out Git revision.'
