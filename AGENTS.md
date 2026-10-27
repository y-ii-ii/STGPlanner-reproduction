# STGPlanner 项目协作规则

- 先读最新状态与恢复清单：project-context/STATUS.md、project-context/RUNBOOK.md。不要默认读取整段旧聊天或历史归档。
- 当前项目由用户主动暂停。除非用户后续明确恢复，不启动仿真、修改算法或继续长测；可回答问题及维护交接文件。
- 本项目目录D:/STGPlanner不是Git根。实际Git仓库在D:/STGPlanner/catkin_ws/src/STGPlanner；不要在D盘项目根执行git init。
- 私有仓库y-ii-ii/STGPlanner-reproduction；当前修复分支fix/fael-gbp2-progress。保留main及两个历史基线标签。
- 部署工具D:/STGPlanner/benchmarks；WSL发行版STGPlanner-Ubuntu20。真正编译的FAEL/GBP2源码在WSL /opt/stgplanner/benchmarks/*_ws/src，修改D盘上游克隆不会自动改变二进制。
- 多会话不假定互相知道聊天内容。每个实质阶段结束更新STATUS.md的结果、改动文件、验证与下一步；不以巨型聊天复制代替交接。
- 同时只允许一个会话控制这套WSL/ROS/Gazebo。运行前读SIMULATION_LOCK.json并核对实际进程；更新归属。其他会话不得终止发行版、占用11311/11345、重编译正在用的原生库。
- 同一Git工作目录只允许一个会话写代码/切分支/提交；并行代码任务使用独立Git工作树。报告会话读取已落盘数据，最终报告写入由一个会话完成。
- 原始基线与失败/用户中止数据不可覆盖。新测试必须新目录名；95%公共阈值、原生结束、限时、用户暂停分别报告，不把健康验收或单次试验当作论文统计复现。
- 项目内中间脚本用codex/work，交付用codex/outputs。历史原始会话工作区及其outputs仍保留，路径见STATUS.md。
