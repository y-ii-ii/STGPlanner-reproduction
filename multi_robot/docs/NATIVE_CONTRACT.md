# 原生任务约束、执行授权与停稳确认合同

本候选使用共同world和完美通信，仅经过离线检查与隔离编译；没有启动ROS节点、Gazebo或原生地图重放。首阶段报告保留为历史，当前行为以下述合同为准。

## 原STG五状态接入

|状态|接入方式|
|---|---|
|1 拓扑前沿|按任务unknown／portal及本车自由空间入口接近带建立候选视图，调用原Initialize|
|2 分支更新|原updateCurrentExploreBranch只见本任务候选，沿用成功源码现有规则；不将距离规则冒称原论文窄分支规则|
|3 回溯|原历史栈建立可恢复视图；未分配标签及路径／距离元数据保留，调用结束或正常异常退出后恢复|
|4 边界补充|本地／全局UFO前沿及原生恢复入口都使用相同任务范围|
|5 规划执行|调用原planning／A*，目标或分支要有任务证据；无有效局部候选才使用本任务的融合图路线接近|

任务范围是每个连通任务的RLE成员及入口摘要，随TaskDelta传输；它不把远端点云／完整格图插入本车UFOMap。范围限制探索目标，不封锁公共通道。不归本车、空候选、停滞、超时都不能删除或确认任务；completed仍来自执行者本车观测证据。入口接近带只从portal沿本车已知自由格4邻接扩展，最多min(8格, ceil(1m/res))，不会穿墙扩张；UFO边界选择仍限原unknown／portal范围。

全局拓扑格图初始化的Empty不算观测，Free／Occupied才是该图的真实证据；Map2DManager的实测地形空洞语义不能套用到它。

任务可由A发现、B执行。B按任务unknown成员集合检查自身观测，发OBSERVATION_COMPLETED，绑定session／robot／task／version／dispatch_id和scope_digest，且地图时间新鲜、去重后成员全部观测。中央只记录完成覆盖，不改写A的来源任务或格图；仍等最终停止ACK才把责任状态转completed。相同任务后来扩张出未覆盖成员，旧执行代次停止后用新版本重新分配。候选耗尽、抵达入口和执行超时不算完成。

## 三层反馈与执行代次

- 原生规划器ACCEPTED只记planner_accepted，不将责任标成已执行。
- 执行器验证任务、版本、dispatch_id并发布本代次路径，发EXECUTOR_ACCEPTED；此时责任可转active。
- 最终速度门控发STOPPED及stop_id／request_ids／停稳证据，才能解除停止屏障。

心跳序号、任务版本、执行代次和停止请求号分开。旧代次Goal、旧nonce和迟到证明不能解锁。Action新增execution_lease，停止结果新增stop_proof；必须整套使用新planner、path_execution、control_planner_interface、exploration_manager、team_topology，不能混用旧Action二进制。

## 停止与超时规则

最终门控是每车cmd_vel唯一发布者，pathFollower改发本车topology/raw_cmd_vel。启动、交接、显式停止与失败恢复先通过唯一停止屏障。证明必须同时满足：

- 停止请求之后的新鲜、递增里程计至少3帧；
- twist与位姿差分速度不超过0.05m/s、0.09rad/s，持续至少0.5秒；
- 门控已成功提交零速输出至少0.5秒，最近零速发布仍新鲜。

冻结／旧数据、仅构造零速却未发布、错误请求号均不能确认。默认单调时间保护：协调器1.5秒、执行器许可0.3秒、传感器／跟随器约0.3秒失效即归零；仿真时钟暂停不冻结计时。新代次先发新路径，再释放跟随器及授予许可；首份许可清除缓存旧速度。

同代次8秒无0.1米位移触发停滞，整体代次60秒上限，频繁换路径不能重置。执行器单次Goal上限30秒，规划请求5秒，协调器停止屏障6秒，停止服务7秒，客户端等待7.5秒。阈值尚未在Gazebo负载中调优，可能产生保守停车。

停滞只对当前车暂缓任务8秒，规划阻塞暂缓2秒；归属释放等停稳证明，不伪造completed。停滞接回原生deferExecutionFrontier；融合图fallback不能绕过它。迟到STOP可安全停车，迟到ROUTE不得授予运动。停止超时进入故障，迟到ACK不能自动解锁；新请求须重新取证。

执行器退出时，在门控、协调器和里程计仍活着的前提下，门控独立归零并可提供证明；死掉的Action服务不伪装成功。门控自身退出后的停止仍依赖底层控制器命令看门狗，尚未在线验收。

## 话题、通信与配置

本车topology_snapshot只给本车agent；团队交换topology_delta。schema 2 topology_command发给原生规划器、执行器和门控；execution_permit是本车内部许可，execution_feedback包含执行接收、停止请求和最终证明。

中央统计拓扑接收、反馈接收及命令发布的应用字节，包括RLE与ACK，按一次交付模型计，不包括订阅复制、网络头、重传和物理无线流量；不要再与发送端计数重复相加。

collaboration.launch包含两车agent、协调器和两个最终门控。prepare_stack仅离线转换成功栈副本：禁用远端点云及未授权初始化运动、应用新ABI、改接raw_cmd_vel、把ROS_HOME迁到新目录。它不启动任何进程。不能直接套旧run.py或保留旧速度发布者；实际ROS图单发布者、TF与传感器时序需要后续验收。未来经授权启动也须先source新工作空间devel/setup.bash，保证roslaunch本身解析新包；节点内部env不能替代外层环境选择。

## 离线入口和边界

- build_native_task_offline.sh：新team_topology_native_task_20261116_ws，保留首阶段和成功库。
- test_native_task_offline.sh NEW_DIRECTORY：标准库检查、ASan/UBSan车体／Scope／租约检查及真实ROS消息序列化，无ros::init或master。
- team_topology.prepare_stack：只生成新配置并静态验证，不执行roslaunch。

任务导出仅扫描存在真实自由／未知入口的格；地图不变时复用结果。规模优化经过任务及载荷等价检查，不通过删前沿减耗时。

当前已新增短路径交通预约、停稳取证后的让行及本车地图验证的有限后退，见TRAFFIC_PROTOCOL_20261116.md；采用新协议，不直接运行旧run.py交通监督器，在线验收以本轮报告为准。

本轮构建仅用build_traffic_offline.sh的新planner／最终Python工作空间。旧build_native_task_offline.sh指向已保全的前阶段空间，本阶段不能用它覆盖重编译。执行图合并本车地形与真实UFO观测以补盲区；障碍优先、未知不放行，尚不代表坑洞／起伏地面支撑证明。

本轮已观察到五状态在线访问及路径执行，但4/4试验无95%和T95，第四次车轮触墙，持续探索／整体安全验收失败。最终双车停车ACK通过不抹去接触。详见TRAFFIC_SCENE4_RESULTS_20261116.md；旧成功基线保留，不再自动运行本候选。当前不是SLAM回环，也没有实现全部候选分配算法；新的运行须另有明确有限授权。
