#!/bin/bash
set -e
source /opt/ros/noetic/setup.bash
g++ -std=c++14 -fPIC -shared /mnt/d/STGPlanner/scripts/rviz_native_capture.cpp -o /opt/stgplanner/librviz_native_capture.so $(pkg-config --cflags --libs rviz Qt5Widgets)
