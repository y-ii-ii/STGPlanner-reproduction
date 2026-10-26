#!/bin/bash
set -e
source /opt/stgplanner/catkin_ws/devel/setup.bash
mkdir -p /opt/stgplanner/benchmarks/bin
g++ -O3 -DNDEBUG -std=c++17 /mnt/d/STGPlanner/benchmarks/benchmark_coverage.cpp -o /opt/stgplanner/benchmarks/bin/benchmark_coverage $(pkg-config --cflags --libs planner)
