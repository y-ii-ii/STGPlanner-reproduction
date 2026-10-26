#!/usr/bin/env bash
set -e
source /opt/stgplanner/catkin_ws/devel/setup.bash
set -u
base=/mnt/d/STGPlanner/logs/rviz_repair
python3 /mnt/d/STGPlanner/scripts/marker_audit.py --seconds 60 --output "$base/markers_after.json" >"$base/markers_after.log" 2>&1 &
marker_pid=$!
python3 /mnt/d/STGPlanner/scripts/runtime_test.py --seconds 60 --output "$base/runtime_after.json" >"$base/runtime_after.log" 2>&1 &
runtime_pid=$!
python3 /mnt/d/STGPlanner/scripts/tf_audit.py >"$base/tf_after.log" 2>&1 &
tf_pid=$!
status=0
wait "$marker_pid" || status=1
wait "$runtime_pid" || status=1
wait "$tf_pid" || status=1
echo "RViz repair checks completed with exit code $status."
exit "$status"
