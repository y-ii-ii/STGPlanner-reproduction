#!/usr/bin/env bash
set -eo pipefail
WORLD=${1:-Scene4}
GUI=${2:-true}
if [[ "$WORLD" != Scene4 || ! "$GUI" =~ ^(true|false)$ ]]; then
  echo 'Usage: run.sh Scene4 true|false' >&2
  exit 2
fi
source /opt/stgplanner/catkin_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost
export GAZEBO_IP=127.0.0.1
export GAZEBO_MASTER_URI=http://127.0.0.1:11345
export ROS_HOME=/mnt/d/STGPlanner/ros
export ROS_LOG_DIR=/mnt/d/STGPlanner/logs/ros
export GAZEBO_MODEL_PATH="/mnt/d/STGPlanner/models:${GAZEBO_MODEL_PATH:-}"
export GAZEBO_MODEL_DATABASE_URI=file:///mnt/d/STGPlanner/models/
export PYTHONUNBUFFERED=1
export QT_X11_NO_MITSHM=1
export DISABLE_ROS1_EOL_WARNINGS=1
export LIBGL_ALWAYS_SOFTWARE=${LIBGL_ALWAYS_SOFTWARE:-1}
export MPLBACKEND=TkAgg
mkdir -p "$ROS_HOME" "$ROS_LOG_DIR"
PIDFILE=/tmp/stgplanner-launch.pid
exec 9>/tmp/stgplanner-launch.lock
if ! flock -n 9; then
  echo 'STGPlanner is already running. Stop it before starting another instance.' >&2
  exit 1
fi
if timeout -k 2 3 rostopic list >/dev/null 2>&1; then
  echo 'ROS master port 11311 is already occupied. Stop the existing ROS session first.' >&2
  exit 1
fi
echo $$ >"$PIDFILE"
pids=()
cleanup() {
  trap - EXIT INT TERM
  echo 'Stopping STGPlanner nodes...'
  if ((${#pids[@]})); then
    timeout -k 2 5 rosnode kill -a >/dev/null 2>&1 || true
  fi
  for ((i=${#pids[@]}-1; i>=0; i--)); do
    kill -INT -- "-${pids[i]}" 2>/dev/null || true
  done
  for ((attempt=0; attempt<8; attempt++)); do
    alive=false
    for pid in "${pids[@]}"; do
      if kill -0 "$pid" 2>/dev/null; then alive=true; fi
    done
    if [[ "$alive" == false ]]; then break; fi
    sleep 1
  done
  for pid in "${pids[@]}"; do
    kill -TERM -- "-$pid" 2>/dev/null || true
  done
  sleep 2
  for pid in "${pids[@]}"; do
    kill -KILL -- "-$pid" 2>/dev/null || true
  done
  for pid in "${pids[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
  rm -f "$PIDFILE"
}
trap cleanup EXIT
trap 'exit 0' INT TERM
start_launch() {
  local label=$1
  shift
  setsid roslaunch "$@" >"/mnt/d/STGPlanner/logs/${label}.log" 2>&1 &
  pids+=("$!")
}
wait_topic() {
  local topic=$1
  echo "Waiting for $topic ..."
  local deadline=$((SECONDS+180))
  while ((SECONDS < deadline)); do
    if timeout -k 2 25 python3 /mnt/d/STGPlanner/scripts/wait_topic.py "$topic" >/dev/null 2>&1; then return 0; fi
    for pid in "${pids[@]}"; do
      if ! kill -0 "$pid" 2>/dev/null; then
        echo 'ROS launch process exited. See D:\STGPlanner\logs.' >&2
        exit 1
      fi
    done
    sleep 1
  done
  echo "Timed out waiting for $topic. See D:\\STGPlanner\\logs." >&2
  exit 1
}
start_launch simulation exploration_manager sim_env.launch world:="$WORLD" gazebo_gui:="$GUI"
deadline=$((SECONDS+180))
until timeout -k 2 5 rosservice call /gazebo/unpause_physics >/dev/null 2>&1; do
  if ((SECONDS >= deadline)); then echo 'Gazebo physics service did not become ready.' >&2; exit 1; fi
  sleep 1
done
wait_topic /jackal/velodyne/velodyne_points
start_launch movement exploration_manager robot_move.launch
wait_topic /base_link/odometry
start_launch exploration exploration_manager explorer.launch world:="$WORLD" rviz:="$GUI" plot:="$GUI"
echo 'STGPlanner started. Logs: D:\STGPlanner\logs. Press Ctrl+C to stop.'
while :; do
  for pid in "${pids[@]}"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "Launch process $pid exited; stopping the session." >&2
      exit 1
    fi
  done
  sleep 2
done
