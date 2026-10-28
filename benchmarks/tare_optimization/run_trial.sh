#!/bin/bash
set -eo pipefail
source /opt/stgplanner/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311 ROS_HOSTNAME=localhost
export PYTHONUNBUFFERED=1
exec python3 /mnt/d/STGPlanner/codex/work/tare_optimization/run_tare_trial.py "$@"
