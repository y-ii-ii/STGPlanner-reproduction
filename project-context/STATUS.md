# STGPlanner 最新交接状态

更新时间：2026-10-27T16:37:35.036294+08:00。本文件覆盖旧聊天及history中所有“仍在运行”的历史描述。

## 当前状态：用户主动暂停

用户最新要求：先暂停算法项目；迁入已创建的STGPlanner项目，配置短会话交接。
侧栏已按项目分组。项目ID bd16d030-19af-4456-a6f4-fecde2256511。
旧对话迁移接口两次返回成功，但list_threads仍显示projectId=null，故**不能确认旧对话已归入项目**；原对话保留原位置作为历史，不依赖它接续。
已用项目接口建立两个全新短会话，均只读初始化并等待用户，不执行算法任务：
- STGPlanner 算法与长测：01a17c85-9d73-7573-885c-a95dbbc4abbf。
- STGPlanner 报告与论文对照：01a17c85-a03f-7170-8f21-68dd9119e2d2。
新会话工作目录D:/STGPlanner，使用状态文件接续，未复制巨型历史。
GBP2第六轮已按用户要求停止原生启动器，公共测试器执行停车并保存结果；随后专用WSL发行版已停止。没有活动长测。

- 第六轮repair_formal_gbp2_06：1082.027仿真秒，54.153530%，4218.56m²，1179.247m。
- **已突破原41%平台并进入右侧；尚未完成95%。** 本轮被用户中止，不能声称完整2400秒试验或算法自然结束。
- 原始finish_reason是process_exit:native_planner，源于有记录的人工关闭原生启动器。interruption.json和user_pause.json说明用户暂停；停车确认、零指令、漂移和传感器检查均通过。
- 不能从1082秒精确续跑：进程内图和仿真状态已结束。恢复时使用新的运行名（建议repair_formal_gbp2_07）从相同初始条件重测；保留06为用户中止证据。

## 目录和版本

- 项目根：D:/STGPlanner；Git根：D:/STGPlanner/catkin_ws/src/STGPlanner。
- 私有远程：https://github.com/y-ii-ii/STGPlanner-reproduction，分支fix/fael-gbp2-progress。
- 最近已推送的算法代码检查点e2b5d2d（聚类前沿类型修复）；之前14925ee（返航契约）、11afc7d（几何修复）。迁移交接另有后续提交，读取git log核实。
- 保留main/repro-baseline-2026-10-26=dfc712982891f29c266083d7efad72ad48e730a2；benchmark/scene4-baselines和scene4-baselines-2026-10-27=9dec3c45184259a0d68e3dfe066040966d807aed。
- 最终修复标签scene4-progress-fix-2026-10-27尚未创建；最终报告、远程克隆验收和最终ZIP/bundle尚未完成，不得冒称已发布。
- WSL：STGPlanner-Ubuntu20（root，Ubuntu20/ROS Noetic）；WSL磁盘在D盘。原生编译副本/opt/stgplanner/benchmarks/fael_ws和gbp2_ws，主环境/opt/stgplanner/catkin_ws。
- 部署脚本、配置、回归和原始结果D:/STGPlanner/benchmarks；新会话工具和报告副本D:/STGPlanner/codex/work、outputs。
- 原始会话工作区：C:/Users/Administrator/Documents/Codex/2026-10-26/add-windowscapability-online-name-openssh-server-9；原outputs保留，迁移时也复制到项目codex/outputs，旧文件不删除。

## 已确认结果和修复

- FAEL原1600秒41.2775%，约415秒后停滞；修复前沿生命周期、XY邻格更新、近点分配一致性、路网更新和不可达2-opt后，repair_formal_fael_01在1017.008s达到95.3366%，1351.931m，停车验收通过。
- GBP2原1600秒41.1789%、1945.54m；01/02中间诊断主动停止，03完整2400.032s仍41.7582%；04修复返航契约后855.756s原生结束，仅41.3186%，后续主动诊断停止；05完整2400.014s仍41.4049%、2343.532m，2116.081s原生返航结束。
- GBP2原生修复：73x6射线缓存维度/末列越界；投影点到物理感知高度及外参；旁侧地面射线漏扣0.5m；LiDAR球坐标超程12.3954->12m；时间预算三元表达式优先级；返航IDL状态2正确传播和适配器仅执行一次返航；聚类收益复制后同步邻节点前沿类型（旧受控用例收益前沿2/类型1，修复2/2）。
- 显式配置校准：采样节点500->2000、边/循环上限4倍，时间模型2/1m/s，原生前沿比例0.05->0.01。公共95%完成阈值不变。这些是本地工程改动，不能称论文原始参数复现。
- 通道冻结地图诊断排除了地面缺失与AdaptiveObb挡住通道。500/2000节点原生服务分别0/3、3/3给出通道前进；125个自由观察点原生前沿比例0.05下0个、0.01下16个有效。它们均为离线诊断，05完整失败已证明其单独不足以完成全程。
- 06与05相比只加聚类类型同步修复；采样随机，单次全程差异不能独立证明该修复的因果贡献。06确已突破41%，但被用户暂停，必须重新完整验证。
- 回归：射线5、FAEL2、感知坐标3、几何/预算10、适配器契约10、前沿校准5、聚类3。对应JSON在benchmarks。最近编译18包通过。

## 公共协议与证据

Scene4独立观察器已知平面面积/7790m²，.4m栅格、12m截断；完成面积>7400.5m²。这不是100%可达区覆盖。机器人映射预热5秒后前进3米再计时。控制器/地形固定；返航、公共完成、时间上限分开记录。公共协议revision3，GBP适配器revision1。
源码/二进制指纹progress_repairs/manifest.json；原生修复9个文件、3个库。driver和gbp2.yaml的允许变更及原始SHA在trial_repairs/manifest.json。每轮native_source_manifest、adapter_config_manifest和配置随结果保存。06还有live_rosparams.yaml确认实际0.01/2000。
06附加只读passive_frontier_audit.jsonl，早期submitted_controller_path标签实际是局部localPlanner的/path候选，不是GBP全局下发路径；后续标签已更正并节流。不要用这些局部候选统计里程或当作原生全局路径。

## 恢复后优先事项

1. 先读RUNBOOK.md；按用户新目标决定是否恢复GBP2，不自动启动。
2. 06改为用户中止的中间证据；07为新正式运行，运行前固定progress_trials.json。当前分析/报告脚本仍选择06，**它们是待整理草稿，不能直接生成“最终完成”报告**。
3. 完整运行后核验原始result、源代码/二进制和实际参数，区别健康检查通过与探索达95%。FAEL结果不需因迁移重复跑。
4. 更新analyze_progress.py对用户中止分类的验收；当前最终分支仅接受coverage_threshold/sim_time_limit，因此06会失败，不能靠放宽最终完成标准糊弄。
5. 生成曲线/地图，人工查看图片；make_progress_report.py、update_progress_docs.py、pandoc更新3份报告。修订模板的最终运行名/中止描述。旧基线原始结果保留。
6. stage_progress.py归档代码/新证据/报告，凭据模式检查、diff --check，提交推送；再建最终标签，verify_progress_remote.py及verify_progress_clone.py核对旧refs、私有性、全部文件SHA；最后bundle和package_progress.py。这些交付尚未执行。

## 多会话约定

主协调/长测会话独占WSL和代码写入；报告会话可读结果/处理独立草稿；新功能会话需独立Git工作树，不能随意切换共享分支。
新会话只加载本文件及当次涉及源码，按需查RUNBOOK/history。每阶段更新本文件，避免长聊天不断追加。
