#!/usr/bin/env bash
set -e
source /opt/stgplanner/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost
export ROS_HOME=/mnt/d/STGPlanner/ros
export LIBGL_ALWAYS_SOFTWARE=1
export QT_X11_NO_MITSHM=1
export DISABLE_ROS1_EOL_WARNINGS=1
python3 /mnt/d/STGPlanner/scripts/prepare_screenshot_view.py
rosnode kill /planner_rviz || true
sleep 2
exec rosrun rviz rviz -d /mnt/d/STGPlanner/catkin_ws/src/STGPlanner/stgp_planner/planner/resource/topo_planner.rviz __name:=planner_rviz
