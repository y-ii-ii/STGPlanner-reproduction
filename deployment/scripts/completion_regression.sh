#!/bin/bash
set -eo pipefail
source /opt/stgplanner/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311 ROS_HOSTNAME=localhost
g++ -std=c++17 /mnt/d/STGPlanner/scripts/completion_regression.cpp -o /opt/stgplanner/completion_regression $(pkg-config --cflags --libs control_planner_interface)
/opt/stgplanner/completion_regression
