#!/usr/bin/env bash
set -eo pipefail
source /opt/stgplanner/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost
seconds=${1:-180}
output=${2:-/mnt/d/STGPlanner/logs/runtime_retest.json}
python3 /mnt/d/STGPlanner/scripts/runtime_test.py --seconds "$seconds" --output "$output" | tee "${output%.json}.log"
