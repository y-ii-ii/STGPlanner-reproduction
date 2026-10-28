#!/bin/bash
set -eo pipefail
source /opt/stgplanner/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311 ROS_HOSTNAME=localhost
exec python3 /mnt/d/STGPlanner/codex/work/tare_optimization/snapshot_live.py "$@"
