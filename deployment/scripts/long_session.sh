#!/bin/bash
set -eo pipefail
source /opt/stgplanner/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311 ROS_HOSTNAME=localhost
export ROS_HOME=/mnt/d/STGPlanner/ros
export LIBGL_ALWAYS_SOFTWARE=1 QT_X11_NO_MITSHM=1 DISABLE_ROS1_EOL_WARNINGS=1
base=/mnt/d/STGPlanner/logs/planner_completion
bash /mnt/d/STGPlanner/scripts/run.sh Scene4 true &
demo_pid=$!
python3 /mnt/d/STGPlanner/scripts/wait_exploration_ready.py
python3 /mnt/d/STGPlanner/scripts/rviz_status_probe.py "$base/status_after.json" >"$base/rviz_probe.log" 2>&1 &
set +e
python3 /mnt/d/STGPlanner/scripts/long_runtime_test.py --minimum-seconds 1200 --maximum-seconds 2400 --post-finish-seconds 120 --output "$base/long_runtime.json" >"$base/long_runtime.log" 2>&1
result=$?
mkdir -p "$base/long_run_statistics"
cp /mnt/d/STGPlanner/catkin_ws/src/STGPlanner/files/exploration_data/* "$base/long_run_statistics/"
cp /mnt/d/STGPlanner/logs/exploration.log "$base/long_exploration.log"
cp /mnt/d/STGPlanner/logs/movement.log "$base/long_movement.log"
cp /mnt/d/STGPlanner/logs/simulation.log "$base/long_simulation.log"
echo "$result" >"$base/long_runtime.exit"
echo "Long lifecycle test finished with status $result; graphical windows remain open."
wait "$demo_pid"
