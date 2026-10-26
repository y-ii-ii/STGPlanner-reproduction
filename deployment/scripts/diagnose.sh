#!/usr/bin/env bash
source /opt/stgplanner/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost
echo SERVICES
rosservice list
echo PHYSICS
timeout 5 rosservice call /gazebo/get_physics_properties
echo PHYSICS_CODE=$?
echo UNPAUSE
timeout 5 rosservice call /gazebo/unpause_physics
echo UNPAUSE_CODE=$?
echo WORLD
timeout 5 rosservice call /gazebo/get_world_properties | tail -6
echo PROCESSES
ps -eo pid,ppid,pgid,comm,pcpu,stat,wchan:25 | grep -E 'gazebo|gzserver|roslaunch|python|rosservice|timeout|rostopic|spawn'
echo GAZEBO_LOG
find /root/.gazebo -type f -name '*.log' -exec tail -n 20 {} \; 2>/dev/null
echo NODE_LOG
find /mnt/d/STGPlanner/logs/ros -name 'urdf_spawner*.log' -mmin -5 -exec tail -n 15 {} \;
