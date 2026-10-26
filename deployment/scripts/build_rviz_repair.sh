#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/noetic/setup.bash
exec > >(tee /mnt/d/STGPlanner/logs/rviz_repair/build.log) 2>&1
python3 /mnt/d/STGPlanner/scripts/repair_rviz_sources.py
source /opt/stgplanner/catkin_ws/devel/setup.bash
python3 /mnt/d/STGPlanner/scripts/validate_sensor_model.py
cd /opt/stgplanner/catkin_ws
PYTHONUNBUFFERED=1 catkin build planner --no-deps -j4 -p1 --no-status --summarize
