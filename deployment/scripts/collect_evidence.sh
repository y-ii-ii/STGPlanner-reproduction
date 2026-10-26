#!/usr/bin/env bash
set -eo pipefail
base=/mnt/d/STGPlanner
mkdir -p "$base/logs/gui_run" "$base/logs/gui_statistics" "$base/logs/gazebo_final"
dpkg-query -W -f='${binary:Package}\t${Version}\n' > "$base/logs/installed-packages.tsv"
cp "$base/logs/simulation.log" "$base/logs/movement.log" "$base/logs/exploration.log" "$base/logs/gui_run/"
cp "$base/catkin_ws/src/STGPlanner/files/exploration_data/"*.txt "$base/logs/gui_statistics/"
cp /root/.gazebo/server-11345/default.log "$base/logs/gazebo_final/server.log"
cp /root/.gazebo/client-11345/default.log "$base/logs/gazebo_final/client.log"
cp /root/.gazebo/ogre.log "$base/logs/gazebo_final/ogre.log"
bash -n "$base/scripts/run.sh" "$base/scripts/test.sh" "$base/scripts/build.sh" "$base/scripts/bootstrap.sh" "$base/scripts/install_assets.sh" "$base/scripts/verify_environment.sh"
echo 'Evidence collected; shell scripts parse successfully.'
