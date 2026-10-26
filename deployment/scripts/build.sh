#!/usr/bin/env bash
set -eo pipefail
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
export LANG=en_US.UTF-8
export DEBIAN_FRONTEND=noninteractive
mkdir -p /mnt/d/STGPlanner/logs
exec > >(tee -a /mnt/d/STGPlanner/logs/build.log) 2>&1
apt-get install -y --no-install-recommends ros-noetic-velodyne-simulator ros-noetic-tf2-sensor-msgs python3-matplotlib python3-tk mesa-utils libgl1-mesa-dri
bash /mnt/d/STGPlanner/scripts/install_assets.sh
mkdir -p /opt/stgplanner/catkin_ws
ln -sfn /mnt/d/STGPlanner/catkin_ws/src /opt/stgplanner/catkin_ws/src
mkdir -p /mnt/d/STGPlanner/catkin_ws/src/STGPlanner/files/exploration_data
chmod +x /mnt/d/STGPlanner/catkin_ws/src/STGPlanner/stgp_planner/visualization_tools/scripts/realTimePlot.py
source /opt/ros/noetic/setup.bash
cd /opt/stgplanner/catkin_ws
catkin init
catkin config --extend /opt/ros/noetic --cmake-args -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=17
catkin build -j4 -p2 --no-status --summarize
source devel/setup.bash
rospack find exploration_manager
rosversion -d
