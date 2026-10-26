#!/usr/bin/env bash
set -e
source /opt/stgplanner/catkin_ws/devel/setup.bash
exec python3 /mnt/d/STGPlanner/scripts/marker_audit.py --seconds "$1" --output "$2"
