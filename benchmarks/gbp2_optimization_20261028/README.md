# GBP2 Scene4 后续优化工具

> **用户最新限制：本阶段最多3次新增正式试验（10/11/12），次数已用完；12为最后一次。** 原1.5%及全部复测计划取消，原方案文件只作历史保存。`codex/GBP2_EXPERIMENT_LIMITS.json`优先于旧方案，`guard_new_experiment.py`已拦截新运行、调参准备和ROS地图重放入口。后续仅完成当前收尾、恢复已测试配置、离线报告/交接及私有备份；没有自动扩展次数或继续修改算法的安排。

本目录属于2026-10-28用户明确恢复的GBP2优化。TARE已完成、部署恢复原版；FAEL成功数据不重跑。只允许持有`codex/SIMULATION_LOCK.json`的会话操作仿真和原生代码。运行名必须全新，不能覆盖旧数据。

## 当前可复用入口

| 文件 | 作用 |
|---|---|
| `experiment_plan.json` | 运行10前固定的单阈值方案、后续条件与统计边界。 |
| `assert_idle.py` | 同时核对协作锁、实际`/proc`进程和11311/11312/11345端口。 |
| `guard_new_experiment.py`、`experiment_limits.json` | 拦截用户次数上限以外的所有新实验；不能通过旧条件方案自动增加次数。 |
| `prepare_frontier.py` | 仅空闲时部署预设阈值，保存配置before/after，核实原生代码及两库仍为09。 |
| `run_trial.sh` | 加载WSL ROS与Python消息包路径，调用监督器。 |
| `run_gbp2_trial.py` | 全新目录、固定95%/2400秒协议，冻结源码和配置，结束后验证并清理所属进程。 |
| `observe_and_save.py` | 被动记录速度指令、动作和运行指纹；公共停止后保存原生地图。 |
| `analyze_running.py` | 只读当前进度、与09相同时刻对比及原生全局切换；日志交错行单列。 |
| `analyze_completed.py` | 验收完整结果、配置/原生库身份、传感器、速度、停车、原生地图SHA、清理；公共成功单独判定。 |
| `compare_plane_maps.py` | 完成后与历史成功运行的平面图做离线重叠分析，不把这些图输入规划器。 |
| `analyze_revisits.py` | 将原生最佳路径叶点/实际动作终点与至少60秒前的真实轨迹比对，关联随后100秒面积增长；排除最终返航和保持阶段，仅作离线关联，不能把合法回溯当异常或把叶点当执行目标。 |
| `plot_results.py` | 在WSL用Matplotlib生成已完成运行的覆盖/里程曲线和地图，不把运行中数据当最终结果。 |
| `trial_catalog.json`、`update_checkpoint.py` | 固定各分支运行名与参数；根据实际锁/结果更新最新交接，不能靠猜测标记运行或成功。 |
| `native_volume_probe.cpp`、`run_volume_probe.sh` | 仅空闲时启动11312离线探针，从保存的原生地图采样自由点，对比非均匀/均匀射线和三维残余收益；不读公共平面图，不证明路径可达。独立编译探针，不改原生库。 |
| `audit_workspace_geometry.py` | 从历史已保存平面图核对XY范围，排查简单边界遗漏；仅离线诊断。 |
| `ground_sensor_geometry.py` | 从捕获的运行时URDF推导雷达相对车体和轮胎接地点的不同高度，与平地快照核对；不读探索目标。 |
| `verify_height_reference.py` | 比较中位平地根状态的名义感知高度换算与独立里程计快照，功能核对不等于完整探索或逐节点模型精确。 |
| `audit_sensor_model.py` | 提取运行时VLP16物理模型；物理插件最大130m与有效收益/原生积分/公共评分12m要分别解释，均不在本轮改变。 |
| `conditional_followup_plan.json`、`.v2.json`、`prepare_height.py` | 保留后续方案及修订；v2在12运行前固定：11完整未达95%且空闲后，回到09的1%阈值，仅相对09改变0.5192m距地高度。12若未达95%，再单测1.5%阈值；提出采用时独立重复。 |
| `freeze_deployment.py` | 仅空闲时选择已测试配置，记录最终实际原生源码/库和配置SHA；不会重跑测试。 |
| `make_report.py`、`update_report_links.py`、`render_reports.py`、`check_layout.cjs` | 阶段关闭后汇总全部运行，保留四算法预选表、补充全部新结果，生成独立HTML并验证排版。 |
| `review_paper_pdf.py` | 只读下载引用的原论文，渲染完整相关表格/曲线页；Fig5(d)仅作定性证据，不从图估填精确成功率。 |
| `stage_delivery.py`、`verify_delivery.py` | 阶段关闭后归档全部原始数据、原生快照与工作工具，校验压缩前后字节SHA和此前原始证据未改动。一次归档只执行一次。 |
| `backup_private.py`、`finalize_backup.py` | 验证私有性/保护引用、独立远端恢复，再记录内容提交和后续元数据提交；不保存认证凭据。 |

## 一次性记录与审计

`audit_native.py`、`record_resume.py`、`prepare_frontier10.py`、`record_trial10.py`、`checkpoint_native_end10.py`已经执行，保留作证据，**不能无条件重跑**。`audit_sensor_frames.py`、`audit_tf_frames.py`是运行10停车期间的一次只读快照；Gazebo原始world与归一化world的高度不同不能直接当TF错误。`analyze_frozen_replay.py`复查旧09的48次冻结地图查询，不重建历史时刻收益。

## 运行边界

四算法旧基线阶段不被本目录的后续试验替换。前沿资格阈值1%/3%/10%与公共95%阈值是不同概念。原生返航、达到95%、完整限时、用户中止分别记录。验证健康通过不代表探索成功；参数试验不自动构成论文五次统计复现。改变三维收益目标时必须另标“方法变体”。
