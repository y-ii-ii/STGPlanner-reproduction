# STGPlanner 本机部署与运行测试报告

部署日期：2026 年 10 月 26 日（北京时间，UTC+8）  
项目：[Haochen-Niu/STGPlanner](https://github.com/Haochen-Niu/STGPlanner)  
源码基线：`59b41451f7b80ba09a9bcbaf44b58141cd6f9de8`（本地保留 Git 历史与修复差异）

## 1. 部署结果

{{RESULT}}

## 2. 本机环境与目录

| 项目 | 实际配置 |
|---|---|
| 宿主系统 | Windows 11，10.0.22621.2861，x64 |
| GPU | NVIDIA GeForce RTX 4060，8 GB，驱动 546.33 |
| Linux | 独立 WSL2 发行版 `STGPlanner-Ubuntu20`，Ubuntu 20.04 |
| WSL | 2.7.10.0；Linux 内核 6.18.33.2 |
| ROS / 仿真 | ROS Noetic / Gazebo 11 |
| 编译 | GCC 9、CMake 3.16.3、C++17、Release |
| Python | Ubuntu 自带 Python 3.8；NumPy、Matplotlib、Tk 均用 apt 安装 |
| 图形 | WSLg + Mesa 21.2.6 llvmpipe 软件渲染，OpenGL 检查通过 |
| 精确软件版本 | `logs/environment.txt` 和 `logs/installed-packages.tsv` |

```text
D:\STGPlanner\
├─ catkin_ws\src\STGPlanner\   Git 源码与本地修复
├─ wsl\ext4.vhdx              Ubuntu、ROS、依赖、编译产物
├─ downloads\                 已校验的 Ubuntu 基础系统安装包
├─ models\                    官方 grey_wall、gazebo 模型和本地模型库
├─ scripts\                   安装、修复、构建、启动和测试脚本
├─ logs\                      安装/构建/仿真日志、测试数据
├─ ros\                       ROS 用户数据
├─ Start-STGPlanner.cmd        双击启动 Scene4 图形演示
├─ Stop-STGPlanner.cmd         停止本次部署管理的运行实例
├─ Start-STGPlanner.ps1        PowerShell 启动入口，支持 -Headless
└─ Stop-STGPlanner.ps1         PowerShell 停止入口
```

Linux 工作空间为 `/opt/stgplanner/catkin_ws`，其 `src` 链接到 `/mnt/d/STGPlanner/catkin_ws/src`。源码可从 Windows 直接编辑；build、devel 等位于 D 盘 VHDX 内的 Linux 文件系统，以保留 Catkin 所需的 Linux 文件属性并提高构建效率。现有 `Ubuntu-22.04` 未迁移或替换，现有 Conda/Python 环境也未用于本项目。

{{DISK}}

## 3. 日常启动、停止与重新编译

### 图形模式

双击 `D:\STGPlanner\Start-STGPlanner.cmd`，或在 PowerShell 执行：

```powershell
& 'D:\STGPlanner\Start-STGPlanner.cmd'
```

脚本依次启动 Gazebo Scene4、等待激光点云、启动运动控制、等待里程计，最后启动探索策略、RViz 和实时指标绘图。启动过程的详细输出见 `D:\STGPlanner\logs`。

停止时可按启动窗口中的 Ctrl+C，或另开 PowerShell：

```powershell
& 'D:\STGPlanner\Stop-STGPlanner.cmd'
```

停止脚本会终止本项目专用的 `STGPlanner-Ubuntu20` 发行版，保证 Gazebo 和 ROS 后台进程一并退出；因此不要在这个专用发行版中放置其他需要长期运行的任务。

### 只关闭 Figure 1

只关闭当前会话的 Figure 1，保留其他仿真节点：

```powershell
wsl.exe -d STGPlanner-Ubuntu20 -u root -- python3 /mnt/d/STGPlanner/scripts/close_figure1.py
```

绘图节点设置本次 ROS Master 会话的 `suppress_window` 参数后空闲，避免 roslaunch 的自动重启重新弹窗；停止并重新启动整个项目后默认恢复绘图。

### 无界面模式

```powershell
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/run.sh Scene4 false
```

此模式关闭 Gazebo GUI、RViz 和绘图窗口；原项目的 GPU ray 雷达仍需要 WSLg/OpenGL 渲染支持。

### 修改源码后重新编译

```powershell
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/build.sh
```

等价的 Linux 构建核心命令：

```bash
source /opt/ros/noetic/setup.bash
cd /opt/stgplanner/catkin_ws
catkin init
catkin config --extend /opt/ros/noetic \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=17
catkin build -j4 -p2 --no-status --summarize
source devel/setup.bash
```

### 按 README 分三个终端启动

每个终端先进入指定发行版：

```powershell
wsl.exe -d STGPlanner-Ubuntu20 -u root
```

每个 Linux 终端先执行以下环境设置，再分别执行后面的启动命令：

```bash
source /opt/stgplanner/catkin_ws/devel/setup.bash
export LIBGL_ALWAYS_SOFTWARE=1
export QT_X11_NO_MITSHM=1
export GAZEBO_IP=127.0.0.1
export GAZEBO_MASTER_URI=http://127.0.0.1:11345
export GAZEBO_MODEL_PATH=/mnt/d/STGPlanner/models
export GAZEBO_MODEL_DATABASE_URI=file:///mnt/d/STGPlanner/models/
```

```bash
# 终端 1：仿真
roslaunch exploration_manager sim_env.launch world:=Scene4 gazebo_gui:=true

# 终端 2：运动控制，等待仿真启动后执行
roslaunch exploration_manager robot_move.launch

# 终端 3：探索策略
roslaunch exploration_manager explorer.launch world:=Scene4
```

## 4. 从基础系统重建的部署指令

以下用于理解、复现部署；本机已安装，无需再次导入同名发行版。复现时先将交付材料中的脚本放入 `D:\STGPlanner\scripts`。安装与克隆命令应在能访问 WSL 和 D 盘的 Windows 用户会话运行。

```powershell
New-Item -ItemType Directory -Force D:\STGPlanner\downloads, D:\STGPlanner\scripts, D:\STGPlanner\logs

# 原 Git 全局代理失效，此处只覆盖当前命令，不修改全局配置
git -c core.autocrlf=false -c http.proxy= -c https.proxy= clone `
  https://github.com/Haochen-Niu/STGPlanner.git `
  D:\STGPlanner\catkin_ws\src\STGPlanner
git -C D:\STGPlanner\catkin_ws\src\STGPlanner checkout 59b41451f7b80ba09a9bcbaf44b58141cd6f9de8

curl.exe -fL --retry 2 -o D:\STGPlanner\downloads\ubuntu-base-20.04.5-base-amd64.tar.gz `
  https://cdimage.ubuntu.com/ubuntu-base/releases/20.04/release/ubuntu-base-20.04.5-base-amd64.tar.gz
Get-FileHash D:\STGPlanner\downloads\ubuntu-base-20.04.5-base-amd64.tar.gz -Algorithm SHA256

wsl.exe --import STGPlanner-Ubuntu20 D:\STGPlanner\wsl `
  D:\STGPlanner\downloads\ubuntu-base-20.04.5-base-amd64.tar.gz --version 2

wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/bootstrap.sh
wsl.exe -d STGPlanner-Ubuntu20 -u root -- python3 /mnt/d/STGPlanner/scripts/patch_deployment.py
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/build.sh
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/verify_environment.sh
```

Ubuntu 安装包实际 SHA256：

```text
60e216b60947653dc8989be3821380268315b99b2959c29882781541bfe5a426
```

该值与 [Ubuntu 官方 SHA256SUMS](https://cdimage.ubuntu.com/ubuntu-base/releases/20.04/release/SHA256SUMS) 一致。系统采用独立 WSL 导入，参见 [Microsoft WSL 命令文档](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)。

`bootstrap.sh` 的主要工作为配置 Ubuntu focal 软件源、安装基础编译工具、导入 ROS 官方签名密钥、配置清华 ROS 镜像并安装 `ros-noetic-desktop-full` 和控制/建图依赖。`build.sh` 补充 Velodyne、TF2 sensor messages、Matplotlib/Tk，并进行完整构建。依赖清单与准确指令均保存在脚本中；apt 验签保持启用。

`install_assets.sh` 使用 Git 稀疏检出安装 [OSRF 官方 Gazebo 模型](https://github.com/osrf/gazebo_models)，固定提交 `8163eb4b5e7e21985c6591d1c0bfb56468c0093f`，仅取 `grey_wall` 和 `gazebo` 两个目录；由 `build.sh` 自动调用。资源校验值见 `logs/model_checksums.txt`。

## 5. 遇到的问题与解决措施

{{ISSUES}}

## 6. 运行测试与证据

{{TESTS}}

### 自行复测

先启动项目，再另开 PowerShell 运行：

```powershell
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash -lc `
  'source /opt/stgplanner/catkin_ws/devel/setup.bash; python3 /mnt/d/STGPlanner/scripts/runtime_test.py --seconds 180 --output /mnt/d/STGPlanner/logs/runtime_retest.json'
```

测试使用真实 ROS 订阅数据，核对激光点云、里程计、非零速度命令、局部路径、成功且非空的探索规划、探索量指标及仿真时钟。测试进程退出码为 0 表示这些检查全部通过；退出码为 1 表示至少一项未满足。测试本身不会发送运动指令，运动来自项目的探索和控制节点。

## 7. 交付材料与验证边界

{{DELIVERABLES}}

本次针对仓库提供的 `Scene4` 和当前机器进行部署测试。测试时长与指标见上表；不代表已经覆盖所有探索过程、所有随机种子或真实机器人场景。渲染使用 CPU 软件后端，不能将测试速度当作 RTX 4060 硬件渲染性能。Ubuntu 20.04 / ROS Noetic 是为匹配上游要求而固定的环境，后续升级系统或 ROS 时需要重新验证依赖与 Gazebo 插件兼容性。
