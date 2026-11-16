# 多机器人拓扑协同独立实现

本目录从成功 Old dual02 的 planner 源码导入独立副本，不修改原单机／双机、历史数据和原生库。
BASELINE_IMPORT.json 固定导入前各文件 SHA256，后续改动由 Git diff 单独追踪。

本轮范围：共同 world、完美通信、拓扑增量融合、连通任务和图距离分区；只做离线检查。
不包含仿真授权，不宣称已完成回环、受限通信或取得新的 T95。

参考：C²-Explorer 的连通任务思想；GVP-MREP 的图距离分区及增量拓扑交换。
MinPos、MDVRP、距离贪心为候选参考，不要求全部实现。

实现入口：[team_topology](team_topology/README.md)。原生接口与验收边界见 [NATIVE_CONTRACT.md](docs/NATIVE_CONTRACT.md)。
本轮用户已明确允许推送至当前公开仓库，仅上传本轮源码、来源清单和离线证据，不上传历史原始数据或本机凭据。

当前增量：原STG五状态任务视图、独立速度门控／停稳证明及新Action租约；使用build_native_task_offline.sh和test_native_task_offline.sh。首阶段文稿是历史快照，当前接口见docs/NATIVE_CONTRACT.md。

本轮结果：[五状态任务约束与停止ACK离线报告](docs/NATIVE_TASK_EXECUTION_20261116.md)，以及[最终离线证据](evidence/native_task_offline_20261116/validation.json)。46项Python、51项C++检查及五包隔离编译通过；未启动仿真，尚无新95%／T95。

2026-11-16交通验证已关闭于4/4：[完整结果](docs/TRAFFIC_SCENE4_RESULTS_20261116.md)。新候选未达到95%，无T95，第四次触墙中止；不得替换单机04／Old dual02，也不得自动第五次。最终代码b505e98，54项Python／22项本轮C++离线检查通过不代表在线安全通过。
