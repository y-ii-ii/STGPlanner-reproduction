#!/bin/bash
set -eo pipefail
root=/mnt/d/STGPlanner
python3 "$root/codex/work/prepare_diagnostic_08.py"
source /opt/ros/noetic/setup.bash
cd /opt/stgplanner/benchmarks/gbp2_ws
catkin build gbplanner -j2 -p1 --no-status --summarize >"$root/codex/outputs/diagnostic_gbp2_gain_08_setup/build.log" 2>&1
source /opt/stgplanner/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311 ROS_HOSTNAME=localhost GAZEBO_IP=127.0.0.1 GAZEBO_MASTER_URI=http://127.0.0.1:11345
export ROS_HOME=/mnt/d/STGPlanner/ros GAZEBO_MODEL_PATH=/mnt/d/STGPlanner/models GAZEBO_MODEL_DATABASE_URI=file:///mnt/d/STGPlanner/models/
export PYTHONUNBUFFERED=1 QT_X11_NO_MITSHM=1 DISABLE_ROS1_EOL_WARNINGS=1 LIBGL_ALWAYS_SOFTWARE=1 MPLBACKEND=Agg
export PYTHONPATH=/opt/stgplanner/benchmarks/gbp2_ws/devel/lib/python3/dist-packages:$PYTHONPATH
exec python3 "$root/codex/work/supervise_diagnostic_08.py"
