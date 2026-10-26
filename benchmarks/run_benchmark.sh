#!/bin/bash
set -eo pipefail
source /opt/stgplanner/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311 ROS_HOSTNAME=localhost GAZEBO_IP=127.0.0.1 GAZEBO_MASTER_URI=http://127.0.0.1:11345
export ROS_HOME=/mnt/d/STGPlanner/ros GAZEBO_MODEL_PATH=/mnt/d/STGPlanner/models GAZEBO_MODEL_DATABASE_URI=file:///mnt/d/STGPlanner/models/
export PYTHONUNBUFFERED=1 QT_X11_NO_MITSHM=1 DISABLE_ROS1_EOL_WARNINGS=1 LIBGL_ALWAYS_SOFTWARE=1 MPLBACKEND=Agg
export PYTHONPATH=/opt/stgplanner/benchmarks/gbp2_ws/devel/lib/python3/dist-packages:$PYTHONPATH
exec python3 /mnt/d/STGPlanner/benchmarks/benchmark_trial.py "$@"
