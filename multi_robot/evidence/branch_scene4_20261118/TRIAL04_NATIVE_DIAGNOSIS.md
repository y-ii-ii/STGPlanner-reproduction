# 第4次原生退出定位

2026-11-19最后一次Scene4双机试验在探索约306.074秒时退出，车1 topo_planner_node 的PID 559返回139。并集953.12 m²（12.235%），两车最终STOP动作回执有效，接触监视在线且无非地面接触。运行日志在本轮第4次原始目录内，字节未改动。

用第4次实际归档的 `01_libtopo_planner.so` 符号化原生堆栈。偏移 `0x1d7d90` 对应 `execution_repair.cpp:31` 的 `map_.toCoord(code.toKey())`，展开到UFOMap `octree.h:579` 的 `getNodeHalfSize`。上一调用为 `applyExecutionRecovery` 在该文件第44行遍历本地前沿，来自 `HeriGraphCoverPlanner::Initialize`，再来自原生任务规划回调。

原实现的恢复路径仍直接遍历 `local_frontier_cells_` 和 `global_frontier_cells_` 的引用。定时地图更新会在写锁下清空或替换这两个集合。常规 `getSuitableTourPoints` 已使用持同一把锁的值快照及深度检查，恢复入口尚未接入这一保护。日志与源码指出恢复入口共享容器并发访问的缺口。单次堆栈未记录线程交错和当时Code值，因此复核范围为调用点和潜在失效机制。

本轮已用满4次。原生退出只做了离线定位，接受第4次失败结果并保留二进制、符号化输出与原始数据。在本轮记录中，恢复入口仍是已知未关闭的问题。
