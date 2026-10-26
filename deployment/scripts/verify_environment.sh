#!/usr/bin/env bash
set -eo pipefail
source /opt/stgplanner/catkin_ws/devel/setup.bash
exec > >(tee /mnt/d/STGPlanner/logs/environment.txt) 2>&1
date -Iseconds
cat /etc/os-release
uname -a
python3 --version
gcc --version | head -n1
cmake --version | head -n1
rosversion -d
rosversion roslaunch
dpkg-query -W gazebo11 libgazebo11-dev
dpkg-query -W libpcl-dev libopencv-dev libtbb-dev
df -h /
echo '=== Packages ==='
catkin list --workspace /opt/stgplanner/catkin_ws --unformatted
dpkg-query -W 'ros-noetic-desktop-full' 'ros-noetic-velodyne*' python3-matplotlib
echo '=== OpenGL ==='
LIBGL_ALWAYS_SOFTWARE=1 glxinfo -B
echo '=== Launch validation ==='
roslaunch --nodes exploration_manager sim_env.launch world:=Scene4 gazebo_gui:=false
roslaunch --nodes exploration_manager robot_move.launch
roslaunch --nodes exploration_manager explorer.launch world:=Scene4 rviz:=false plot:=false
roslaunch --dump-params exploration_manager sim_env.launch world:=Scene4 >/mnt/d/STGPlanner/logs/simulation_params.yaml
echo 'Environment and launch validation passed.'
