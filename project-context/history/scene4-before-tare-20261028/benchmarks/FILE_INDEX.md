# benchmarks文件用途索引

当前状态：Scene4阶段性完成，GBP2暂停。文件按用途导航，部署路径保持稳定。固定07/08/09名称的脚本仅供历史复核，不可直接复用旧目录。

| 文件 | 分类 | 作用/使用边界 |
|---|---|---|
| [finalize_backup09_metadata.py](finalize_backup09_metadata.py) | 备份与历史归档 | 上一轮备份验收/暂停交接元数据生成；历史用途。 |
| [normalize_reports09.py](normalize_reports09.py) | 备份与历史归档 | 上一轮报告文字口径清理；历史用途。 |
| [prepare_backup09.py](prepare_backup09.py) | 备份与历史归档 | 上一轮09结果私有备份准备程序；冻结历史用途。 |
| [private_backup09_api.py](private_backup09_api.py) | 备份与历史归档 | 使用现有Git凭据在内存中核查仓库私有性、远端提交与保护引用。 |
| [stage_progress.py](stage_progress.py) | 备份与历史归档 | 将选定证据、补丁、报告归档到Git；重复归档保留不同原始字节。 |
| [update_progress_docs.py](update_progress_docs.py) | 备份与历史归档 | 历史报告入口同步工具，存在原工作目录假设。 |
| [verify_archive09.py](verify_archive09.py) | 备份与历史归档 | 上一轮09备份的历史内容/凭据模式核查；冻结原清单假设。 |
| [verify_index09.py](verify_index09.py) | 备份与历史归档 | 上一轮09备份索引字节与记录SHA核查；冻结原清单假设。 |
| [verify_remote_clone09.py](verify_remote_clone09.py) | 备份与历史归档 | 独立远端克隆/快进后核验记录文件SHA和09原生地图解压SHA。 |
| [analyze_progress.py](analyze_progress.py) | 数据分析与报告 | 读取选定运行，区分协议健康和探索目标，汇总修复前后数据。 |
| [make_benchmark_report.py](make_benchmark_report.py) | 数据分析与报告 | 旧四算法报告生成器，保留历史用途。 |
| [make_progress_report.py](make_progress_report.py) | 数据分析与报告 | 修复长测报告历史生成器，含相对工作目录假设；不要覆盖阶段收尾报告。 |
| [plot_benchmark.py](plot_benchmark.py) | 数据分析与报告 | 生成修复前四算法覆盖/轨迹图。 |
| [plot_progress.py](plot_progress.py) | 数据分析与报告 | 生成修复前后覆盖曲线与地图。 |
| [summarize_diagnostic_08.py](summarize_diagnostic_08.py) | 数据分析与报告 | 解析08本地选路日志，统计无有效前沿却获选的路径。 |
| [summarize_stagnation_probe_09.py](summarize_stagnation_probe_09.py) | 数据分析与报告 | 汇总48次只读查询，不将查询分布当作唯一因果结论。 |
| [build_all_baselines.sh](build_all_baselines.sh) | 构建与准备 | 编译全部基线的入口，恢复后才可按需执行。 |
| [build_baseline.sh](build_baseline.sh) | 构建与准备 | 单个基线原生工作空间构建入口。 |
| [build_cloud_bridge.sh](build_cloud_bridge.sh) | 构建与准备 | 构建公共点云适配程序。 |
| [build_coverage.sh](build_coverage.sh) | 构建与准备 | 构建独立公共面积观察器。 |
| [build_gbp2.sh](build_gbp2.sh) | 构建与准备 | GBP2依赖及原生工作空间构建。 |
| [clone_locked_sources.py](clone_locked_sources.py) | 构建与准备 | 按sources.lock.json拉取锁定源码；不修改历史运行。 |
| [collect_benchmark_builds.py](collect_benchmark_builds.py) | 构建与准备 | 收集原生构建改动、适配补丁与指纹。 |
| [prepare_benchmark.py](prepare_benchmark.py) | 构建与准备 | 生成/部署算法适配配置的历史准备程序。 |
| [prepare_formal_09.py](prepare_formal_09.py) | 构建与准备 | 09固定名称运行的历史准备程序；不得直接重用旧运行名。 |
| [prepare_passive_attachment_09.py](prepare_passive_attachment_09.py) | 构建与准备 | 生成09后附加审计脚本的历史准备程序。 |
| [Run-ProgressSuite.ps1](Run-ProgressSuite.ps1) | 测试入口与协议 | 历史修复后串行队列入口；当前禁止自动执行。 |
| [Run-Scene4Suite.ps1](Run-Scene4Suite.ps1) | 测试入口与协议 | 历史四算法串行测试队列入口；当前禁止自动执行。 |
| [benchmark_cloud_bridge.cpp](benchmark_cloud_bridge.cpp) | 测试入口与协议 | 点云适配桥，将公共传感器流接到各算法原生接口。 |
| [benchmark_coverage.cpp](benchmark_coverage.cpp) | 测试入口与协议 | 独立公共已知平面面积观察器；不向原生规划器提供真值探索目标。 |
| [benchmark_protocol.md](benchmark_protocol.md) | 测试入口与协议 | 公共测试协议、指标定义与比较边界。 |
| [benchmark_trial.py](benchmark_trial.py) | 测试入口与协议 | 统一测试主程序：公共覆盖、里程、健康与停车验收，保存原始运行结果。 |
| [capture_progress_manifest.py](capture_progress_manifest.py) | 测试入口与协议 | 记录修复源码、配置和编译库SHA。 |
| [cleanup_trial_runtime.py](cleanup_trial_runtime.py) | 测试入口与协议 | 按进程命令/环境中的指定结果目录识别归属，清理并核查端口。 |
| [environment.json](environment.json) | 测试入口与协议 | 部署环境/工作空间记录。 |
| [progress_trials.json](progress_trials.json) | 测试入口与协议 | 预先选择的修复后正式结果与诊断结果目录，禁止混作重复统计。 |
| [protocol_manifest.json](protocol_manifest.json) | 测试入口与协议 | 初期测试协议与环境指纹，历史记录。 |
| [run_benchmark.sh](run_benchmark.sh) | 测试入口与协议 | 单次算法运行入口，要求使用全新结果目录名。 |
| [run_formal_09.sh](run_formal_09.sh) | 测试入口与协议 | 09固定名称运行的历史入口；不得直接重用旧运行名。 |
| [run_formal_trial.py](run_formal_trial.py) | 测试入口与协议 | 正式运行监督器，保存运行版本并按结果目录归属清理进程。 |
| [run_outcome.py](run_outcome.py) | 测试入口与协议 | 结果分类：公共阈值、限时、原生结束、用户中止分别记录。 |
| [save_poststop_map_07.py](save_poststop_map_07.py) | 测试入口与协议 | 07收尾地图尝试；服务已关闭错误留存，不代表保存成功。 |
| [sources.lock.json](sources.lock.json) | 测试入口与协议 | 各基线及依赖的精确上游地址和提交。 |
| [apply_progress_repairs.py](apply_progress_repairs.py) | 源码修复与回滚 | 将修复后的原生源码应用到WSL编译副本。 |
| [apply_trial_repairs.py](apply_trial_repairs.py) | 源码修复与回滚 | 历史时间预算、返航/结束契约与参数适配修改。 |
| [build_progress_repairs.sh](build_progress_repairs.sh) | 源码修复与回滚 | 应用/构建FAEL与GBP2已保留修复，实际目标在WSL /opt。 |
| [path_frontier_repair.py](path_frontier_repair.py) | 源码修复与回滚 | GBP2局部选路资格修复：仅可行且含有效前沿路径参与竞争。 |
| [rollback_progress_repairs.py](rollback_progress_repairs.py) | 源码修复与回滚 | 按修复快照回滚原生源码；切Git分支不会自动完成此操作。 |
| [rollback_trial_repairs.py](rollback_trial_repairs.py) | 源码修复与回滚 | 回滚上述历史契约/配置适配。 |
| [test_path_frontier_selection.py](test_path_frontier_selection.py) | 源码修复与回滚 | 提取实际评分代码块的受控用例与幂等性检查。 |
| [adaptive_bound_probe.cpp](adaptive_bound_probe.cpp) | 诊断与采样 | 自适应边界历史诊断程序；不表示正式试验已采用新边界。 |
| [audit_live_07.py](audit_live_07.py) | 诊断与采样 | 07运行的只读指令速度/动作记录器，固定07路径。 |
| [audit_passive_09_attached.py](audit_passive_09_attached.py) | 诊断与采样 | 09后附加的只读速度/动作记录器；仅覆盖附加后的采样。 |
| [benchmark_diagnostic08.py](benchmark_diagnostic08.py) | 诊断与采样 | 08只加诊断日志的测试器副本，不是新算法正式重复。 |
| [gbp_debug.py](gbp_debug.py) | 诊断与采样 | 历史GBP2原生日志插桩。 |
| [gbp_gain_probe.cpp](gbp_gain_probe.cpp) | 诊断与采样 | GBP2原生收益和感知射线诊断程序。 |
| [gbp_stagnation_probe_09.cpp](gbp_stagnation_probe_09.cpp) | 诊断与采样 | 09冻结原生地图查询程序；研究残余三维收益与平面增量分离。 |
| [ground_map_probe.cpp](ground_map_probe.cpp) | 诊断与采样 | 地面感知高度与地图上下文查询程序。 |
| [instrument_gbp2.py](instrument_gbp2.py) | 诊断与采样 | 历史GBP2原生耗时采样插桩。 |
| [offline_rrg_probe.py](offline_rrg_probe.py) | 诊断与采样 | 离线RRG图/原生地图诊断。 |
| [prepare_diagnostic_08.py](prepare_diagnostic_08.py) | 诊断与采样 | 08日志诊断与固定名称运行准备。 |
| [prepare_gbp_gain_probe.py](prepare_gbp_gain_probe.py) | 诊断与采样 | 准备原生收益查询位置与上下文。 |
| [prepare_ground_map_probe.py](prepare_ground_map_probe.py) | 诊断与采样 | 准备地面高度诊断位置与原生函数。 |
| [prepare_stagnation_probe_09.py](prepare_stagnation_probe_09.py) | 诊断与采样 | 为09最终原生地图生成48组离线收益查询。 |
| [probe_obstacles.py](probe_obstacles.py) | 诊断与采样 | 障碍与运动环境只读诊断。 |
| [probe_stall.py](probe_stall.py) | 诊断与采样 | 停滞时原生前沿/候选/路径只读诊断。 |
| [record_gbp_frontiers.py](record_gbp_frontiers.py) | 诊断与采样 | 06原生前沿记录器，固定运行目录；历史用途。 |
| [record_linkage.py](record_linkage.py) | 诊断与采样 | 记录原生库及控制链加载路径/指纹。 |
| [refresh_live_07.py](refresh_live_07.py) | 诊断与采样 | 07运行进程与加载库指纹快照，固定07路径。 |
| [run_adaptive_bound_probe.sh](run_adaptive_bound_probe.sh) | 诊断与采样 | 编译/执行自适应边界历史诊断。 |
| [run_diagnostic_08.sh](run_diagnostic_08.sh) | 诊断与采样 | 08固定名称日志诊断入口，历史用途。 |
| [run_gbp_gain_probe.sh](run_gbp_gain_probe.sh) | 诊断与采样 | 编译/执行原生收益诊断。 |
| [run_ground_map_probe.sh](run_ground_map_probe.sh) | 诊断与采样 | 编译/执行地面地图诊断。 |
| [run_offline_rrg_probe.sh](run_offline_rrg_probe.sh) | 诊断与采样 | 离线RRG诊断入口。 |
| [run_stagnation_probe_09.sh](run_stagnation_probe_09.sh) | 诊断与采样 | 09离线原生地图查询入口，临时11312服务；不是新长测。 |
| [stop_gbp_cache_diagnostic.py](stop_gbp_cache_diagnostic.py) | 诊断与采样 | 历史射线缓存诊断结束及归属清理，不是日常停止入口。 |
| [supervise_diagnostic_08.py](supervise_diagnostic_08.py) | 诊断与采样 | 08诊断监督器和归属清理。 |
| [cluster_frontier_regression.py](cluster_frontier_regression.py) | 验证与回归 | GBP2聚类前沿类型/资格回归。 |
| [fael_frontier_regression.cpp](fael_frontier_regression.cpp) | 验证与回归 | FAEL前沿生命周期与候选连通性受控原生回归。 |
| [gain_frame_regression.py](gain_frame_regression.py) | 验证与回归 | 感知坐标与收益计算几何受控回归。 |
| [gbp_core_regression.py](gbp_core_regression.py) | 验证与回归 | GBP2核心逻辑受控回归。 |
| [path_contract_regression.py](path_contract_regression.py) | 验证与回归 | 原生路径输出与公共执行链契约回归。 |
| [ray_cache_regression.py](ray_cache_regression.py) | 验证与回归 | GBP2射线缓存独立回归。 |
| [run_fael_frontier_regression.sh](run_fael_frontier_regression.sh) | 验证与回归 | 构建并执行FAEL受控回归；当前不执行。 |
| [trial_contract_regression.py](trial_contract_regression.py) | 验证与回归 | 时间/返航/终止契约回归。 |
| [validate_benchmark.py](validate_benchmark.py) | 验证与回归 | 核查原始四算法数据与协议验收；通过不等于全部算法探索完成。 |
| [validate_frontier_calibration.py](validate_frontier_calibration.py) | 验证与回归 | 参数校准及前沿相关配置一致性核查。 |
| [validate_outcomes_07.py](validate_outcomes_07.py) | 验证与回归 | 对真实存档及中止元数据核查运行分类。 |
| [verify_runtime_freeze_09.py](verify_runtime_freeze_09.py) | 验证与回归 | 09原生源码、加载库、控制二进制与参数的11项冻结核查。 |

子目录：config为运行配置；patches为初期集成补丁；trial_repairs为契约/配置修复快照；progress_repairs为FAEL/GBP2原生修复前后源码与补丁；reporting为本次只读汇总工具；maintenance为本次归档/验证工具。

## 当前分目录工具

| 文件 | 用途 |
|---|---|
| reporting/summarize_four_algorithms.py | 只读生成四算法论文对比与原始结果SHA |
| maintenance/finalize_scene4_stage.py | 本轮一次性阶段收尾与目录归档，非幂等历史脚本，勿重复运行 |
| maintenance/verify_scene4_stage.py | 当前报告/证据/归档/交接只读一致性核验 |
| maintenance/backup_scene4_stage.py | 私有性、保护引用及远端克隆恢复核验，凭据仅在内存中使用 |
| maintenance/check_report_layout.cjs | 以本机无头Edge检查本地HTML表格与图片，不访问外部站点 |
