@echo off
title STGPlanner - Scene4
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/run.sh Scene4 true
if errorlevel 1 pause
