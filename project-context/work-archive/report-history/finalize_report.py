from pathlib import Path
import json
import re
import shutil

task = Path(__file__).resolve().parents[1]
base = Path('D:/STGPlanner')
out = task / 'outputs'
out.mkdir(exist_ok=True)
headless = json.loads((base/'logs/runtime_headless.json').read_text(encoding='utf-8'))
gui = json.loads((base/'logs/runtime_gui.json').read_text(encoding='utf-8'))
gui_health = json.loads((base/'logs/gui_node_health.json').read_text(encoding='utf-8'))
assert headless['passed'] and gui['passed'], 'A required runtime test did not pass.'
assert all(gui_health.values()), 'A GUI node did not respond.'
long_result=json.loads((base/'logs/planner_completion/long_verification_summary.json').read_text())
assert long_result['passed'] and long_result['isolated_regression']['passed']
assert long_result['checks']['zero_post_finish_commands'] and long_result['checks']['stop_action_succeeded']
for data in (headless, gui):
    data['sim_duration'] = data['sim_time_end'] - data['sim_time_start']
    data['real_time_factor'] = data['sim_duration'] / data['wall_seconds']
report = (task/'work/report-base.md').read_text(encoding='utf-8')
report = report.replace('{{RESULT}}',
    '已在 `D:\\STGPlanner` 完成部署。28 个 Catkin 包全部编译成功，Scene4 的仿真、激光点云、里程计、局部控制和探索规划能够联动运行；无界面和图形模式的真实 ROS 运行检查均通过。Windows 窗口列表确认 Gazebo、RViz 和实时指标窗口均已创建，图形节点存活检查通过。\n\n'
    '后续已定位并修复 `RobotModel`、`topo_map`、`grid_map` 的诊断错误，三个显示项保持启用并通过实际 RViz 状态复验。已重新启动修复后的图形模式并更新截图，见第 6 节。结束演示环境可双击 `D:\\STGPlanner\\Stop-STGPlanner.cmd`。原始两次部署验收数据及上一轮自然结束记录作为历史证据保留。')
report=report.replace('原始两次部署验收数据及上一轮自然结束记录作为历史证据保留。',
    '进一步确认旧 `planner timeout` 混合了正常结束期间的阻塞等待与规划中止；已修复等待响应和日志分类，并完成 {:.1f} 分钟的完整运行观察。默认结束门槛为项目探索指标达到名义地图面积的 95%，不代表 100% 可达空间覆盖。详见第 6 节最新长时间验证。'.format(long_result['wall_seconds']/60))
size = (base/'wsl/ext4.vhdx').stat().st_size / 1024**3
report = report.replace('{{DISK}}', '交付时专用 WSL 虚拟磁盘文件约 **{:.2f} GiB**；文件按需增长，不会预先占用其显示的最大虚拟容量。'.format(size))
issues = '''| 问题 / 证据 | 解决措施与验证 |
|---|---|
| Windows 与上游 Ubuntu 20.04 / ROS Noetic 平台不一致；现有 WSL 是 Ubuntu 22.04 | 新建 D 盘独立 Ubuntu 20.04 发行版，安装 ROS Noetic / Gazebo 11，不混用 Windows Python 3.14 或现有 Conda。 |
| Git 报连接 `127.0.0.1:33210` 失败 | 确认为失效的全局代理；使用当前命令的 `http.proxy=` / `https.proxy=` 覆盖下载，未修改用户全局 Git 代理。 |
| 官方 `packages.ros.org` HTTPS 证书域名校验失败 | 改用清华 ROS 镜像并导入 ROS 官方签名密钥；未关闭 TLS 校验或 apt 验签。 |
| README 仿真命令缺少包名，且默认场景/参数文件并不存在 | 改为 `roslaunch exploration_manager sim_env.launch`；默认场景固定为实际提供的 `Scene4`，规划参数改为 `topo_planner_Scene4.yaml`；使用 Bash 的 `setup.bash`。 |
| 首次编译报 `tf2_sensor_msgs/tf2_sensor_msgs.h: No such file or directory` | 安装 `ros-noetic-tf2-sensor-msgs`，补齐 CMake 和 package.xml 依赖，修正 `tf_ros` 拼写；将导出的不存在库 `simulation` 改为实际的 `slam_output`。重编译 28 包全部成功。 |
| `robot_description` 无法执行 `jackal_description/scripts/env_run` | Windows Git CRLF 换行破坏 Linux 脚本头；统一相关脚本为 LF、恢复执行位、添加 `.gitattributes`。ROS 模型展开和三个 launch 检查通过。 |
| Gazebo 报 `model name jackal already exist` | Scene4 世界文件内保存了旧 Jackal，含作者机器 `/home/nhc/...` 网格绝对路径。移除该保存机器人，改由 URDF 生成；修复脚本校验其余环境模型名称集合完全保持一致。新机器人生成成功。 |
| 物理仿真初始化停滞，Gazebo 等待远程模型库；随后发现凉亭网格缺失 | 补齐官方 `grey_wall` 和 `gazebo` 模型及贴图；修正 `GAZEBO_MODEL_PATH` 的 roslaunch 变量语法，使用本地模型库，消除缺失场景资源对仿真和碰撞的影响。 |
| 初版部署启动器在 ROS Master 尚未就绪时过早返回，且场景可能处于暂停状态 | 改为有截止时间的服务/话题重试，显式解除物理暂停，顺序等待点云和里程计后才启动探索；为超时命令增加强制终止期限。正式启动验证通过。 |
| 统计输出目录不存在，Python 绘图脚本缺少正式安装规则 | 自动创建 `files/exploration_data`；添加 `catkin_install_python`，安装 Matplotlib/Tk。统计文件在实际测试中产生。 |
| 自动化运行时不希望强制开启可视化窗口 | 增加 `rviz`、`plot` 可选参数，默认保留图形显示；无界面测试显式关闭。 |
| 图形模式下 Gazebo 宣告了 WSL 的非回环地址，传感器桥接/客户端联动不正常 | 将 `GAZEBO_IP` 固定为 `127.0.0.1`，显式设置本机 Gazebo Master 地址；改用 `AnyMsg` 订阅检查话题就绪，避免 rostopic 动态类型解析的短超时。图形模式 60 秒联动检查通过。 |
| WSL 重启复用 PID，旧 PID 文件误报已有实例 | 将启动互斥改为 `flock`，专用停止入口使用 `wsl --terminate STGPlanner-Ubuntu20`，只终止本项目发行版；已验证停止后重新启动。 |
| 补充截图时发现 RViz 采用作者的大屏窗口尺寸和跟随视角 | 将窗口调整为 1600×900，保留 Displays 面板，使用固定 world 地图视角，方便在本机完整查看建图区域；原配置另存备份。 |
| 实时指标窗口没有处理 Tk 事件，重绘/交互不及时 | 绘制后增加 `plt.pause(0.001)` 处理 GUI 事件，重启绘图节点后已看到持续更新的累计指标曲线。 |
| RobotModel：虚拟里程计传感器链接缺少到 world 的 TF | 原关节为零行程 revolute，但没有相应 joint_states。改为 fixed，并使用 preserveFixedJoint 保留 Gazebo 插件需要的链接；URDF/SDF 结构、全部机器人链接的 TF 和运动回归均验证通过。 |
| topo_map / grid_map：Points should not be empty for specified marker type | 空类别原来发送空点集 ADD。修复实际发布函数，空类别改发 DELETE 清除旧图元，非空图元不变；实际消息审计及 RViz 连续状态检查通过。 |
| 正常结束前出现 planner timeout，且其他规划失败也被同名记录 | 默认 95% 指标门槛先触发统计节点结束并关闭规划器；客户端阻塞等待结果，未及时处理结束信号。改为处理回调的有界轮询，及时取消结束期间的请求；区分 SUCCEEDED、ABORTED 等状态和真正的 60 秒墙钟超时；记录明确的结束原因、指标与门槛。隔离回归和长时间真实运行均通过。 |
| 首轮长测结束后局部跟随器偶尔仍输出转向命令 | 停车回调的循环条件在刚进入时恒为假；Bool 停车话题没有订阅者。改为有 7 秒墙钟上限、至少持续 2 秒的停车确认；将 latched Bool 接入实际 pathFollower，覆盖线速度和角速度，下一条有效路径才释放停止。增加速度命令与位置稳定检查后，重新执行完整长测。 |
'''
extra = base/'logs/extra_repairs.md'
if extra.exists():
    issues += extra.read_text(encoding='utf-8')
issues += '''
仍可见的非阻塞诊断：

- 完整构建有 7 个包带警告，包括旧 Gazebo API 弃用、PCL 可选 I/O 功能、UFOMap 的重载/返回值相关警告；没有编译失败。本次未改写上游规划算法来消除这些警告。
- `gazebo_ros_control` 会打印四个车轮缺少 PID 增益。当前机器人采用 `VelocityJointInterface`；[官方控制插件源码](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/noetic-devel/gazebo_ros_control/src/default_robot_hw_sim.cpp) 在缺少 PID 参数时回退到直接关节速度控制。实测运动链路通过，因此保留原控制方式，没有随意填写 PID 改变动力学。
- WSL 会提示宿主 localhost 代理未映射到 NAT 网络；本项目下载过程已使用可访问的源，ROS/Gazebo 使用本机通信，测试通过。此提示不等于项目依赖安装失败。
'''
report = report.replace('{{ISSUES}}', issues)
def row(label, key, fmt=None):
    def value(d):
        v=d[key]
        return format(v, fmt) if fmt else str(v)
    return '| {} | {} | {} |'.format(label, value(headless), value(gui))
table = ['| 指标 | 无界面模式 | 图形模式 |', '|---|---:|---:|']
table += [row('实际采集时长（秒）', 'wall_seconds', '.1f'),
          row('仿真时间推进（秒）', 'sim_duration', '.2f'),
          row('采集窗口的实时因子', 'real_time_factor', '.2f'),
          row('收到的点云帧', 'pointcloud_messages'),
          row('每帧最大点数', 'pointcloud_max_points'),
          row('收到的里程计消息', 'odometry_messages'),
          row('采集期间里程计累计位移（米）', 'odometry_distance_m', '.2f'),
          row('非零速度命令数', 'nonzero_commands'),
          row('局部路径消息数', 'path_messages'),
          row('成功且非空的探索规划数', 'successful_nonempty_plans'),
          row('项目上报最大探索指标', 'explored_volume_max', '.2f')]
table += ['| 关键节点存活 | 全部通过 | 全部通过 |', '| 全部自动检查 | PASS | PASS |']
test_text = '''- 完整构建：`All 28 packages succeeded`，0 失败、0 跳过；修复后的完整构建耗时约 15 分 26 秒。
- 环境和启动检查：Ubuntu、ROS、Gazebo、PCL、OpenCV、TBB 版本已记录；OpenGL 可用；三个启动文件解析成功。
- 两次运行测试均直接订阅项目话题，不使用合成数据或模拟测试结果。以下位移只统计采集窗口；项目自己上报的累计距离可能包含测试脚本启动前的运动，因此两者不必完全相同。

'''+ '\n'.join(table)
test_text += '\n\n探索指标沿用上游消息字段 `exploredVolume`。程序对外标注面积/体积的用法不完全一致，本报告不将该数值当作独立校准的面积测量结果。\n\n'
test_text += '![180 秒无界面运行实测轨迹](runtime_trajectory.png)\n\n原始轨迹 CSV、完整指标 JSON 和节点/话题快照随部署材料交付。'
shots = out/'screenshots'
for filename in ('01_gazebo_scene4.jpg','02_rviz_mapping.jpg','03_exploration_metrics.jpg','04_rviz_diagnostics_fixed.png'):
    assert (shots/filename).is_file(), 'Missing requested runtime screenshot: '+filename
manifest = json.loads((shots/'capture_manifest.json').read_text(encoding='utf-8'))
test_text += '''

### 补充的真实图形运行截图

图 1～3 保留上一轮演示的真实 Windows 窗口截图，作为部署过程与修复前状态的历史记录；图 4 是本次长时间测试结束后的最新 RViz 画面。图 4 从运行中的 RViz 同一次回调读取 Qt 面板和 OGRE 视口帧缓冲，避免 WSLg 普通截图接口返回黑屏或错误窗口。所有截图均来自实际运行，没有生成或重绘地图及状态文字；时间与捕获方法见 `screenshots/capture_manifest.json`。图 3 和图 4 不属于同一轮次，不能用于直接比较完成进度；图 5 提供与图 4 同轮的完整指标记录。

**图 1：Gazebo 的 Scene4 场景。** 可见仓库提供的墙体、走廊和三座凉亭，以及物理仿真状态栏。

![Gazebo Scene4 运行窗口](screenshots/01_gazebo_scene4.jpg)

**图 2：修复前的 RViz 建图与轨迹（历史对照）。** 左侧三个红色诊断是本次修复的对象；此图不代表当前状态。修复后的三个 Ok 状态和地图见图 4。

![RViz 建图与路径运行窗口](screenshots/02_rviz_mapping.jpg)

**图 3：上一轮演示的实时探索指标（历史记录）。** 展示项目上报的探索量、累计行走距离及每轮规划耗时。绘图节点中途重启导致曲线起始段直接连接至当时的累计值；定量复验使用下方 JSON 记录。

![实时探索指标窗口](screenshots/03_exploration_metrics.jpg)

RViz 的 ROS 1 生命周期说明弹窗已关闭。显示调整不改变规划算法或运动控制参数。交付时保留仿真和图形窗口，探索已按 95% 指标门槛停止，可使用本报告提供的停止入口结束整个环境。
'''
current = json.loads((base/'logs/screenshot_demo/runtime_current.json').read_text(encoding='utf-8'))
assert current['passed']
test_text += '\n补充截图期间另外执行了 {:.1f} 秒实际运行检查：{} 帧点云、{:.2f} 米位移、{} 次成功且非空规划，9 项检查均通过。原始数据为 `logs/screenshot_demo/runtime_current.json`。\n'.format(current['wall_seconds'], current['pointcloud_messages'], current['odometry_distance_m'], current['successful_nonempty_plans'])
test_text += '\n历史演示轮次后续日志显示 `the exploration process has finished`，程序报告总耗时 `940.312803 s`；最后一条统计记录为累计行走 `1224.75 m`、项目探索指标 `7436.64`。这些属于程序自身的统计和结束判据，不能据此声称所有场景或所有可达区域均已被无遗漏覆盖。该轮结束日志与统计保存在 `logs/screenshot_demo/`，不与本次修复后的新一轮数据混用。\n'
repair=json.loads((base/'logs/rviz_repair/verification_summary.json').read_text())
assert repair['passed']
test_text += '\n### RViz 三项诊断修复与复验\n\n'
test_text += '''修复前从 RViz 自身的状态属性读取到：RobotModel 为虚拟传感器链接缺少 TF；topo_map 的 skeleton/6、myTopo/7 等类别，以及 grid_map 的 unknown/3 等类别报空点集 Marker 错误。实际订阅审计也记录到对应空 ADD。基线见 `logs/rviz_repair/markers_status_before.json` 和 `markers_before.json`。RViz 的判定依据可参见 [官方 Marker 校验源码](https://github.com/ros-visualization/rviz/blob/noetic-devel/src/rviz/default_plugin/marker_utils.cpp)。

修复涉及三个实际源码文件：`VLP_16.urdf.xacro`、`global_topo_manager.cpp`、`grid_map_2d.cpp`。没有关闭这三个显示项，也没有改变其订阅话题或用固定“正常”文本代替真实状态。

'''
test_text += '- 机器人模型：{} 个链接均可变换到 world，虚拟传感器连接为 fixed，Gazebo 保留了传感器链接及插件引用。\n'.format(repair['robot_link_count'])
test_text += '- RViz：三个显示项均启用，连续 {} 次状态采样为 Ok，覆盖 {:.1f} 秒。状态直接从实际加载同一配置的 RViz 显示组件读取。\n'.format(repair['stable_samples'],repair['stable_seconds'])
for name,values in repair['markers'].items():
    test_text += '- {}：收到 {} 条实际消息，空 ADD 为 {}，DELETE 为 {}，非空 ADD 为 {}，非法浮点/奇数线段点集均为 0。\n'.format(name,values['messages'],values['empty_add'],values['delete'],values['nonempty_add'])
test_text += '- 修复后运动规划回归：{:.1f} 秒，行走 {:.2f} 米，成功且非空规划 {} 次，运行检查通过。\n'.format(repair['runtime_seconds'],repair['distance_m'],repair['successful_nonempty_plans'])
test_text += '\n**图 4：本次长时间测试达到 95% 指标门槛后的 RViz。** 三个显示项保持勾选，分别显示绿色 `Status: Ok`，右侧为真实地图和规划可视化。为完整显示 Scene4，视角中心设为 `(15,40,0)`、距离 190；白色路径由 RViz 接收的数据绘制，完整记录的里程计轨迹见图 5。\n\n![RViz 三个显示项均为 Ok](screenshots/04_rviz_diagnostics_fixed.png)\n\n前次 RViz 修复复验汇总：`logs/rviz_repair/verification_summary.json`；原始状态历史、TF 审计、模型转换结果、构建日志和消息审计均随材料交付。该次增量编译仅重建 planner，未改动的 27 个包沿用已通过的构建产物；本轮长测的新增修复见下文。\n'
test_text += '''
历史 RViz 修复后的演示在程序报告的 `1051.394369 s` 后退出；进一步核查表明，统计节点先达到 95% 门槛并关闭规划器，客户端约 81.4 秒墙钟（约 70 秒仿真时间）后才打印 timeout 并处理结束信号。原报告对“上游终止行为”的表述不足以说明此等待问题，现已补充根因、修复和完整复验；日志保留于 `logs/rviz_repair/fixed_run/` 和 `logs/planner_completion/baseline/`。

复现本次修复与检查（先停止运行实例，编译完成后重新启动）：

```powershell
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/build_rviz_repair.sh
& 'D:\\STGPlanner\\Start-STGPlanner.cmd'
# 在另一 PowerShell 窗口、机器人开始运动后执行 60 秒审计
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/verify_rviz_repair.sh
```

状态截图辅助程序需要先执行 `build_rviz_capture.sh` 编译原生捕获库，再运行 `rviz_status_probe.sh /mnt/d/STGPlanner/logs/rviz_repair/status_after.json`。它加载项目的实际 RViz 配置和话题；此附加窗口用于取证，常规启动使用原 RViz。
'''
iso=long_result['isolated_regression']
last=long_result['last_metric']
test_text += '''
### planner timeout 根因与长时间完整运行验证（最新）

**截图中的残余区域与结束判据。** 图 3 是早先轮次中的指标窗口；图 4 已更新为本次完整运行结束后的地图。图中未覆盖部分可能包含未探索空间、障碍物内部、边界外或无法通过的区域，单凭颜色无法确认其可达性。源码的实际默认判据是 `known_space_volume > 0.95 * map_area`，Scene4 的 `map_area=7790`，即指标超过 `7400.5` 即停止；因此程序报告结束时仍可能有残余区域。本次保留该门槛，没有把结束阈值调高或把未知区域当成已覆盖。

**根因证据。** 旧轮次统计节点在仿真时间 `16072.288` 记录 `max volume threshold is reach...` 并广播结束、关闭规划器；客户端仍处于 `sendGoalAndWait(60s, 10s)`，直到 `16142.255` 才打印 `planner timeout`。旧接口还把 ABORTED 等任何非成功结果都打印成 timeout，故该日志本身无法证明计算卡死，也不能一概当作正常完成。

**实际修复。** `ControlPlannerInterface::callForPlanner` 改为处理 ROS 回调的等待循环，收到探索结束时取消当前请求并返回；采用 60 秒墙钟期限，区分成功、ABORTED 等终态与真正超时。Explorer 将完成标志保持为真，结束时不再打印重试警告；统计节点记录 `EXPLORATION_STOP reason=coverage_threshold` 及实际指标，并保留可读取的 `finish_reason` 参数。

**长测进一步发现并修复停车问题。** 首轮 20 分钟记录虽然通过初版 13 项检查，但末期仍出现角速度命令（最大线/角速度命令绝对值之和约 1.0472），因此未作为最终停车验收。源码中 `stopMoveCallback` 以“启动后已超过 2 秒”作为进入循环的条件，刚开始便跳过；它发布的 Bool 话题也未接入 pathFollower。现已修正循环、保持停车发布为 latched，并接入跟随器同时清零线/角速度；新有效路径才释放该停止状态，原有独立 `/stop` 功能保留。最终数据来自加强检查后重新执行的第二轮完整长测，首轮证据保留在 `logs/planner_completion/first_long_before_stop_fix/`。

'''
test_text += '隔离接口回归使用独立 `/completion_regression` 命名空间和无运动 PCI：成功路径返回通过；ABORTED 在 {:.3f} 秒返回且保留状态；回调触发的正常结束在 {:.3f} 秒内取消；注入不返回结果的服务端后，在 {:.3f} 秒出现明确的真实超时。该项属于受控故障注入，不与下方真实场景数据混用。\n\n'.format(iso['aborted_seconds'],iso['completion_seconds'],iso['timeout_seconds'])
test_text += '| 最新真实场景检查 | 实测结果 |\n|---|---:|\n'
for label,value in [
    ('完整观察时长','{:.1f} 秒（{:.1f} 分钟）'.format(long_result['wall_seconds'],long_result['wall_seconds']/60)),
    ('初始化完成至指标门槛','{:.2f} 秒（{:.1f} 分钟）'.format(last['project_elapsed'],last['project_elapsed']/60)),
    ('结束原因',long_result['finish_reason']),
    ('最终项目探索指标','{:.2f} / 7790（名义比值 {:.3f}%）'.format(last['metric'],100*long_result['nominal_ratio'])),
    ('实际订阅点云帧',str(long_result['pointcloud_messages'])),
    ('实际订阅里程计消息',str(long_result['odometry_messages'])),
    ('采集期间里程计距离','{:.2f} 米'.format(long_result['distance_m'])),
    ('成功且非空规划次数',str(long_result['successful_nonempty_plans'])),
    ('Action 结果状态计数',str(long_result['planner_states'])),
    ('结束信号与 Explorer 结束事件的接收时差','<0.001 秒' if long_result['completion_response_seconds']<.001 else '{:.3f} 秒'.format(long_result['completion_response_seconds'])),
    ('结束后仿真时钟继续推进','{:.2f} 秒'.format(long_result['post_finish_sim_seconds'])),
    ('结束 10 秒后最大里程计速度','{:.6f} m/s'.format(long_result['post_finish_max_speed'])),
    ('结束 10 秒后最大速度命令绝对值之和','{:.6f}'.format(long_result['max_post_finish_command'])),
    ('结束 10 秒后累计位置变化','{:.6f} 米'.format(long_result['post_finish_distance_m'])),
    ('停车 action 结果','SUCCEEDED' if long_result.get('stop_action_status')==3 else str(long_result.get('stop_action_status'))),
    ('真实超时 / 旧误导 timeout 日志','均未出现'),
    ('RViz 三项诊断','均启用，末尾连续 10 次为 Ok'),
    ('生命周期检查','{} 项全部 PASS'.format(len(long_result['checks']))),
]:test_text+='| {} | {} |\n'.format(label,value)
test_text += '\nAction 状态 3 表示 SUCCEEDED，4 表示 ABORTED；短暂 ABORTED 按重试分支处理，实际次数见上表。测试允许达到门槛后规划/统计节点主动退出，要求仿真、里程计和静止状态继续正常；不会把预期退出误判为节点崩溃。完整观察时长包括达到门槛后的静止观察，实际探索时长单独列出。\n\n'
test_text += '**图 5：与图 4 同一轮的完整指标及轨迹。** 图由实际 ROS 订阅记录和项目统计文件绘制；虚线标出默认停止门槛。名义比值不等同于独立测量的真实可达区域覆盖率。\n\n![长时间完整运行的实际指标与轨迹](long_run_metrics.png)\n\n'
test_text += '''复验原始证据：`logs/planner_completion/long_runtime.json`、逐条指标/事件 JSONL、节点与内存采样、`long_run_statistics/`、退出日志和 `isolated_regression.json`。首轮监测时 Windows 挂载盘出现并发追加事件行交错，最终记录器已加锁；归档同时从完整内存记录保存的最终 JSON 按时间重序列化 JSONL，原追加文件另存 `long_runtime.events.raw.jsonl`。此修正只涉及监测记录的文件写入。便于阅读的摘要为 `长时间运行验证结果.json`。本轮重建了 `control_planner_interface`、`exploration_manager`、`visualization_tools`、`path_execution`、`local_planner` 五个包，其余构建产物沿用已验证版本。

复现该轮测试时，先停止现有实例，在 PowerShell 依次运行：

```powershell
& 'D:\\STGPlanner\\Stop-STGPlanner.cmd'
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/build_planner_completion.sh
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/long_session.sh
```

长测最少观察 1200 秒，达到门槛后至少再观察 120 秒，最大期限 2400 秒；结果写入 `D:\\STGPlanner\\logs\\planner_completion\\long_runtime.json`。最终结果生成后仿真窗口继续保留，使用停止入口结束。首次重建环境需先执行 `build_rviz_capture.sh`，以便取证窗口导出图 4。
'''
test_text += (base/'logs/paper_comparison_section.md').read_text(encoding='utf-8')
report = report.replace('{{TESTS}}', test_text)
report = report.replace('{{DELIVERABLES}}', '''- 本报告：本次实际部署步骤、故障修复、命令和验证结果。
- `STGPlanner部署材料.zip`：部署/测试脚本、本地源码补丁、环境版本、安装依赖清单、模型提交与校验值、构建日志和两次运行测试数据。
- `runtime_trajectory.png`：真实里程计轨迹图，来自无界面测试采集数据。
- `long_run_metrics.png`、`长时间运行验证结果.json`：最新完整探索轮次的指标图和复验摘要。
- `screenshots/`：更新后的运行画面、三个显示项正常状态的截图及捕获元数据。
- `STGPlanner部署报告.html`：嵌入图片的单文件浏览版报告，便于直接打开。
- D 盘实际运行环境与源码保留在 `D:\\STGPlanner`。压缩包不包含数 GB 的 WSL 虚拟磁盘或 Ubuntu 安装镜像；完整环境直接保留在本机。''')
assert not re.search(r'\{\{\w+\}\}', report), 'Unfilled report placeholder'
dest = out/'STGPlanner部署报告.md'
dest.write_text(report, encoding='utf-8')
shutil.copy2(dest, base/'部署报告.md')
print(dest)
