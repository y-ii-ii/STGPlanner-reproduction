#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export TZ=Asia/Shanghai
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
mkdir -p /mnt/d/STGPlanner/logs
exec > >(tee -a /mnt/d/STGPlanner/logs/bootstrap.log) 2>&1
date -Iseconds
cp /etc/apt/sources.list /etc/apt/sources.list.original
cat >/etc/apt/sources.list <<'EOF'
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal main restricted universe multiverse
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-updates main restricted universe multiverse
deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ focal-security main restricted universe multiverse
EOF
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl gnupg locales sudo git build-essential cmake python3-dev python3-pip lsb-release tzdata
locale-gen en_US.UTF-8
update-locale LANG=en_US.UTF-8
ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
curl -fL --retry 3 https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo 'deb [signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] https://mirrors.tuna.tsinghua.edu.cn/ros/ubuntu/ focal main' >/etc/apt/sources.list.d/ros1.list
apt-get update
apt-get install -y --no-install-recommends ros-noetic-desktop-full python3-catkin-tools python3-rosdep python3-wstool libgoogle-glog-dev libyaml-cpp-dev libtbb-dev libprotobuf-dev protobuf-compiler liblz4-dev ros-noetic-robot-localization ros-noetic-twist-mux ros-noetic-teleop-twist-joy ros-noetic-joy ros-noetic-diff-drive-controller ros-noetic-joint-state-controller ros-noetic-gazebo-ros-control ros-noetic-hector-gazebo-plugins ros-noetic-interactive-marker-twist-server ros-noetic-lms1xx ros-noetic-pointgrey-camera-description ros-noetic-octomap-ros ros-noetic-octomap-msgs ros-noetic-move-base-msgs
date -Iseconds
