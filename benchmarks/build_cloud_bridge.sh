#!/bin/bash
set -e
source /opt/stgplanner/catkin_ws/devel/setup.bash
g++ -O3 -std=c++17 /mnt/d/STGPlanner/benchmarks/benchmark_cloud_bridge.cpp -o /opt/stgplanner/benchmarks/bin/benchmark_cloud_bridge $(pkg-config --cflags --libs tf2_sensor_msgs tf2_ros)
