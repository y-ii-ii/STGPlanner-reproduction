# 本目录协作范围（2026-11-17最新授权）

- 最新授权覆盖旧scope停止条款：离线近墙目标／转向／跟踪修复后最多4次新双机Scene4，每次总wall／sim≤2400s，失败和中止计数；权威D:/STGPlanner/codex/TOPOLOGY_WALL_LIMITS_20261117.json。旧scope不重置，全部旧基线／结果／原生空间只读保留，新wall_native与wall Python空间；继续允许公开GitHub推送。

- 2026-11-16最新授权覆盖以下旧“仅离线”：补齐交通预约／让行，离线通过后最多4次新Scene4双机试验，每次总wall／sim≤2400秒，失败／中止计数；权威D:/STGPlanner/codex/TOPOLOGY_TRAFFIC_LIMITS_20261116.json。旧scope仍closed，新目录，不替换基线；本分支继续允许公开GitHub推送。

- 旧增量授权：补齐原STG五状态任务约束、执行器停止ACK和超时；仍仅离线。新原生bundle为team_topology_native_task_20261116_ws，不能混用旧Action ABI。

- 本阶段允许实施共同world、完美通信下的拓扑融合、连通任务和图距离分区，只做离线检查／隔离编译；禁止启动仿真、ROS节点或原生地图重放。
- 用户明确允许推送到当前公开的 y-ii-ii/STGPlanner-reproduction。此前“私有仓库”记录不代表当前实际可见性；不得更改仓库可见性。
- 本目录是独立候选，不替换成功单机04／Old dual02，不修改旧原生库、历史数据及试验限额。
- 距离贪心、MinPos、MDVRP仅为参考，不要求全部实现。当前选择图距离分区＋任务承诺，效果尚待在线验证。
- 每个完成的逻辑修改需注释、记录修改／原因／方法参考与验证后提交并推送feat/multi-robot-topology；不自动合并main。
- 运行中的脚本必须冻结；不得边执行边修改。WSL源码与Git提交源码必须核对一致；实验仍须新的有限授权。
