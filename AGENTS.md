# STGPlanner 项目协作规则

- 2026-10-28最新用户限制：本轮GBP2新增正式试验硬上限3次（10/11/12），12结束后不再启动新仿真、原生地图重放、1.5%阈值试验或复测，也不继续修改算法。权威限制为D:/STGPlanner/codex/GBP2_EXPERIMENT_LIMITS.json，离线备份见project-context同名文件；后续仅验收、恢复已测试配置、离线报告/交接和私有备份。新实验须有用户新的明确授权与有限次数。

- 在当前运行机先读D:/STGPlanner/codex/STATUS.md、RUNBOOK.md和SIMULATION_LOCK.json；project-context内副本是最近提交的交接快照，长测中不能用其旧“空闲/暂停”推断实时状态。离线恢复副本再读project-context/STATUS.md、RUNBOOK.md。不要默认读取整段旧聊天或历史归档。
- 项目暂停或恢复以用户最新明确授权及状态文件为准。Scene4四算法基线阶段已完成；用户于2026-10-28明确恢复GBP2面积提升与机制验证，由当前会话独占。运行前核对最新STATUS、仿真锁和实际进程，不因新会话自动启动测试。TARE保持已验证原版，FAEL成功结果保留，不自动重跑。
- 本项目目录D:/STGPlanner不是Git根。实际Git仓库在D:/STGPlanner/catkin_ws/src/STGPlanner；不要在D盘项目根执行git init。
- 私有仓库y-ii-ii/STGPlanner-reproduction；当前修复分支fix/fael-gbp2-progress。保留main及两个历史基线标签。
- 部署工具D:/STGPlanner/benchmarks；WSL发行版STGPlanner-Ubuntu20。真正编译的FAEL/GBP2源码在WSL /opt/stgplanner/benchmarks/*_ws/src，修改D盘上游克隆不会自动改变二进制。
- 多会话不假定互相知道聊天内容。每个实质阶段结束更新STATUS.md的结果、改动文件、验证与下一步；不以巨型聊天复制代替交接。
- 同时只允许一个会话控制这套WSL/ROS/Gazebo。运行前读SIMULATION_LOCK.json并核对实际进程；更新归属。其他会话不得终止发行版、占用11311/11345、重编译正在用的原生库。
- 同一Git工作目录只允许一个会话写代码/切分支/提交；并行代码任务使用独立Git工作树。报告会话读取已落盘数据，最终报告写入由一个会话完成。
- 原始基线与失败/用户中止数据不可覆盖。新测试必须新目录名；95%公共阈值、原生结束、限时、用户暂停分别报告，不把健康验收或单次试验当作论文统计复现。
- 项目内中间脚本用codex/work，交付用codex/outputs。历史原始会话工作区及其outputs仍保留，路径见STATUS.md。
