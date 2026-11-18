# 2026-11-18 parallel 新轮次

- 权威 `TOPOLOGY_PARALLEL_LIMITS_20261118.json`。离线修复起步让行、任务波动停车与本地路径受阻。最多4次新Scene4双机试验，每次含启动收尾wall/sim≤2400秒。保存既有原始数据，使用隔离原生和Python工作区。核对锁和实际进程后启动冻结脚本。修改带注释，验证后推送当前已授权的GitHub分支。

# 2026-11-18 motion 4/4已验收关闭

- `TOPOLOGY_MOTION_LIMITS_20261118.json` 已关闭。第1次保留原生崩溃，前沿快照修复 `7d6c4ee` 的三次复测无原生退出。最高并集36.416%，无T95，原成功基线及全部历史保留。报告见 `multi_robot/docs/MOTION_SCENE4_RESULTS_20261118.md`。后续新试验额度以用户新的明确授权为准。

# 2026-11-18本轮授权记录

- 最新用户明确授权覆盖下方旧停止入口：离线修复PASS覆盖局部制动、全队观测摘要去重和协调租约，重点实际推进，再最多4次新Scene4双机，每次含启动收尾wall/sim≤2400s。权威TOPOLOGY_MOTION_LIMITS_20261118.json；旧scope全部保持closed，旧基线、结果与原生空间只读。新motion_native/motion Python独立空间；失败中止计数，不自动补跑。代码注释、每个完成逻辑修订推送公开GitHub并说明原因，保留main和基线。

# 2026-11-18停止入口：liveness已4/4结束关闭

- 权威D:/STGPlanner/codex/TOPOLOGY_LIVENESS_LIMITS_20261117.json已closed。第4次b4ab2a8总wall2311.067s、并集29.488%、705.705m，无95/T95；四次最终双车STOP ACK通过、无非地面接触/新SIGSEGV记录。单机04与Old dual02及全部历史保留，新候选不晋升。
- 本轮不得第五次/补跑/原生地图重放或继续修改算法；后续必须用户新的明确有限授权。“请继续/额度恢复”不自动重置次数。仅验收、报告、保全与恢复已测试配置。
- 剩余问题已落证：PASS交通许可可覆盖当前局部零意图；作者观测完成摘要未充分进入全队跨ID去重；不同任务切换、整车可执行性与大图分配耗时仍未闭环。报告见multi_robot/docs/LIVENESS_SCENE4_RESULTS_20261117.md及D:/STGPlanner/codex/outputs/Scene4跨任务重派图积压与原生内存修复验证报告_20261117.html；证据codex/work/topology_liveness_20261117。新算法/编译空间保持冻结；锁和实际进程仍须核对。

# 已用完的增量授权：2026-11-17 liveness

- 最新用户明确授权：先离线修复跨任务重派、图积压与原生SIGSEGV，再最多4次新Scene4双机；每次含启动收尾wall/sim≤2400s，失败、中止、崩溃计数。权威D:/STGPlanner/codex/TOPOLOGY_LIVENESS_LIMITS_20261117.json。新独立liveness_native/liveness Python空间；旧scope保持closed、全部基线和历史只读。继续允许公开GitHub推送，每个逻辑修改注释、解释原因并验证后推送。

# 本目录协作范围（2026-11-17最新授权）

- 当前新授权：先离线修复STOP/ACK派发环与近墙恢复，再最多4次新Scene4双机，每次含启动收尾wall/sim≤2400s，失败/中止计数；新权威D:/STGPlanner/codex/TOPOLOGY_DISPATCH_LIMITS_20261117.json。旧wall等scope不重置，旧结果/原生空间只读；新dispatch_native与dispatch Python空间。代码注释、验证后继续推送当前公开仓库，全部基线保留。

- 最新授权覆盖旧scope停止条款：离线近墙目标／转向／跟踪修复后最多4次新双机Scene4，每次总wall／sim≤2400s，失败和中止计数；权威D:/STGPlanner/codex/TOPOLOGY_WALL_LIMITS_20261117.json。旧scope不重置，全部旧基线／结果／原生空间只读保留，新wall_native与wall Python空间；继续允许公开GitHub推送。

- 2026-11-16最新授权覆盖以下旧“仅离线”：补齐交通预约／让行，离线通过后最多4次新Scene4双机试验，每次总wall／sim≤2400秒，失败／中止计数；权威D:/STGPlanner/codex/TOPOLOGY_TRAFFIC_LIMITS_20261116.json。旧scope仍closed，新目录，不替换基线；本分支继续允许公开GitHub推送。

- 旧增量授权：补齐原STG五状态任务约束、执行器停止ACK和超时；仍仅离线。新原生bundle为team_topology_native_task_20261116_ws，不能混用旧Action ABI。

- 本阶段允许实施共同world、完美通信下的拓扑融合、连通任务和图距离分区，只做离线检查／隔离编译；禁止启动仿真、ROS节点或原生地图重放。
- 用户明确允许推送到当前公开的 y-ii-ii/STGPlanner-reproduction。此前“私有仓库”记录不代表当前实际可见性；不得更改仓库可见性。
- 本目录是独立候选，不替换成功单机04／Old dual02，不修改旧原生库、历史数据及试验限额。
- 距离贪心、MinPos、MDVRP仅为参考，不要求全部实现。当前选择图距离分区＋任务承诺，效果尚待在线验证。
- 每个完成的逻辑修改需注释、记录修改／原因／方法参考与验证后提交并推送feat/multi-robot-topology；不自动合并main。
- 运行中的脚本必须冻结；不得边执行边修改。WSL源码与Git提交源码必须核对一致；实验仍须新的有限授权。

2026-11-17 dispatch scope 4/4 complete/closed. TOPOLOGY_DISPATCH_LIMITS_20261117.json is authoritative. No fifth simulation, automatic rerun, native replay or further algorithm change in this finite scope. Only evidence, reports, preservation and restore of tested configurations; new online work requires new explicit finite user authorization. Final algorithm 687e867; no new union95/T95; original successful single04 and Old dual02 remain selected. Trial03 SIGSEGV/final stop ACK failure is preserved.
