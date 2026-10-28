#!/bin/bash
set -eo pipefail
source /opt/stgplanner/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311 ROS_HOSTNAME=localhost
export PYTHONPATH=/opt/stgplanner/catkin_ws/devel/lib/python3/dist-packages:/opt/stgplanner/benchmarks/gbp2_ws/devel/lib/python3/dist-packages:$PYTHONPATH
export PYTHONUNBUFFERED=1
exec python3 /mnt/d/STGPlanner/codex/work/gbp2_optimization_20261028/run_gbp2_trial.py "$@"
