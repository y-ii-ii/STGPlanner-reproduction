# TARE优化后续工具（2026-10-28）

本目录只服务当前用户授权的TARE后续验证；GBP2继续暂停，旧Scene4基线阶段完成记录保留。

| 文件 | 作用 |
|---|---|
| experiment_plan.json | 最初方案，惯性候选未启动，保留决策历史 |
| experiment_plan.sensor_model_v2.json | 当前实际采用的感知模型对齐实验方案，含固定条件与复测规则 |
| audit_runtime.py | 启动前实际/proc与仿真端口只读检查；其runtime_before输出仅用于本轮初次审计，勿覆盖 |
| run_trial.sh / run_tare_trial.py | 新名称运行监督、配置/源码冻结、结果分类、按归属清理；拒绝覆盖旧结果目录 |
| observe_tare.py | 只订阅原生路线、目标、速度、里程计，记录诊断JSONL，不发布目标 |
| snapshot_live.sh / snapshot_live.py | 记录实际参数、运行二进制SHA及原生惯性触发计数；重复采样用新文件名 |
| summarize_diagnostics.py | 离线速度/换向/分段覆盖诊断汇总，不是探索目标反馈 |
| prepare_sensor_model.py | 默认只保存补丁proposal；--apply仅在无仿真时改两份原生源码并保存旧二进制 |
| sensor_model_regression.cpp / .sh | 对实际原生LiDARModel输入VLP16的16束物理角度；保留原版失败与候选通过记录 |
| build_sensor_model.sh | 在专用WSL中构建TARE候选；禁止活动运行期间使用 |
| restore_sensor_model.py | 闲置时恢复精确原始源码；恢复后必须重建，不能在运行中执行 |
| update_handoff.py / record_setup.py / record_candidate.py | 本轮各阶段一次性交接检查点，保留授权、真实结果与源码部署状态 |
| record_confirmation.py | 记录候选01完整结果与独立02确认的交接 |
| restore_and_build.sh | 候选不采用时恢复精确原始源码并重建，刷新源码mtime避免缓存保留候选对象 |
| freeze_deployment.py | 只读确认最终闲置原生部署与哪个已测试版本匹配 |
| plot_tare.py / make_report.py | 从全部预定完整观测生成曲线、报告、逐次差值及描述性统计，不择优删样本 |
| verify_tare.py | 核对所有原始结果、健康/停车、冻结版本、实验隔离及原生射线用例 |
| stage_delivery.py / verify_delivery.py | 原始新数据逐文件保留/压缩归档，验证压缩前后SHA和历史证据未变 |
| backup_tare.py | 私有仓库、受保护引用和独立远端恢复核验，现有凭据仅在内存中使用 |

交付和预检在codex/outputs/tare_optimization_20261028；正式原始运行数据在benchmarks/results的各自新目录。不要重跑固定名称或覆盖此前输出。候选感知用例通过不等于探索成功或性能提高，完整结果与最终采用/恢复决定以报告和STATUS为准。

从私有仓库恢复工作工具时，benchmarks/tare_optimization是归档副本，先按项目固定布局复制到D:/STGPlanner/codex/work/tare_optimization，再使用对应Windows/WSL入口。脚本保留机器路径和历史运行名；旧运行入口不是新测试授权，重做实验必须分配全新名称。native_repairs中的APPLIED.json仅表示曾应用，不代表当前程序仍为候选。
