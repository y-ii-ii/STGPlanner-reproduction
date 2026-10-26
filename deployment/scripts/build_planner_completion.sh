#!/bin/bash
set -eo pipefail
source /opt/stgplanner/catkin_ws/devel/setup.bash
mkdir -p /mnt/d/STGPlanner/logs/planner_completion
exec > >(tee /mnt/d/STGPlanner/logs/planner_completion/build.log) 2>&1
python3 /mnt/d/STGPlanner/scripts/repair_planner_completion.py
cd /opt/stgplanner/catkin_ws
catkin build control_planner_interface exploration_manager visualization_tools path_execution local_planner --no-deps -j4 -p1 --no-status --summarize
