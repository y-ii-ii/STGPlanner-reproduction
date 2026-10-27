# STGPlanner 最新交接状态

更新时间：2026-10-27T20:39:43.520895+08:00。本文件覆盖旧聊天及history中的过时运行描述。

## 当前状态：Scene4四算法基线测试阶段性完成；GBP2后续测试暂停

Scene4四算法工程基线测试已按用户最新要求阶段性关闭。STGPlanner、TARE及修复FAEL达到公共95%；GBP2修复09完整限时未达95%，保持暂停。当前无活动长测或自动续跑安排；本轮只更新报告、交接与私有备份、整理工作文件，未启动ROS、仿真或重新编译。后续只有用户明确授权新范围才恢复测试。

| 运行 | 仿真秒 | 面积比例 | 里程(m) | 分类 |
|---|---:|---:|---:|---|
| repair_formal_fael_01 | 1017.008 | 95.3366% | 1351.931 | 已达到公共95%，本轮未重跑 |
| repair_formal_gbp2_06 | 1082.027 | 54.153530% | 1179.247 | 用户中止，未完成95% |
| repair_formal_gbp2_07 | 2400.018 | 54.964827% | 2389.938 | 完整限时失败 |
| diagnostic_gbp2_gain_08 | 1400.018 | 41.415148% | 1535.363 | pilot/diagnostic限时，非正式重复 |
| repair_formal_gbp2_09 | 2400.007 | 56.338896% | 2413.450 | 完整限时失败 |

09面积4388.80m²，墙钟2412.783秒，1600.551秒时已是56.338896%，最后100秒新增0m²。原生未自然结束；finish_reason=sim_time_limit。375条原生本地选路日志均包含有效前沿，但后期反复在右侧中部运动，最长近静止仅3.017秒。**资格修复已生效，探索问题尚未解决。**
09停车确认、零指令、漂移与传感器检查通过；44,141,149字节的poststop_native_map.vxblx已保存，SHA256 cb24b46f3bd8e3158572335df7a0283439423e4c0755db13a3eb2cfa082a1224。08三份原生地图也保留。08/09监督器结束时按结果目录归属清理进程并复核11311/11345，记录无残留。09离线11312探针退出码0，脚本带所属roscore清理trap；最后一次额外WSL ps复核被用户拒绝，因此未执行，不冒称额外复核已通过。07曾有所属ROS/Gazebo残留，已在08之前核实归属后重启专用发行版清除；07无原生地图收尾快照，poststop_map_capture.json记有服务已关闭错误。

## 本轮结论、修改和验证

- 四种方法无条件共用movement.launch→path_execution/localPlanner/pathFollower。运行实参maxSpeed=2.0；autonomySpeed=3.0经代码截断后不代表3m/s。09的11项运行版本核对通过：仅rrg源码相对07改变，已加载GB库匹配冻结09，3个公共控制二进制、原生时间模型2/1m/s、采样2000及前沿阈值0.01未变。原0.2是原生时间模型，与实际低层速度上限分开；05完整失败也表明校准不能单独解决41%停滞。
- 08只加日志，实际228条本地选择中72条路径无有效前沿，58条在其他路径有前沿时仍获选。09修复为仅让可行且含有效非悬空前沿的路径竞争最佳局部路径；不可行路径不保留frontier_exists标志。沿用已有全局回退，不加新visited规则、真值目标或公共覆盖反馈。实际评分块5个受控用例及转换幂等性共6项检查通过，18包编译成功。
- 09结果211项协议/数据检查全部通过，exploration_goals_passed=false。06分类为user_interrupted，7项真实存档/元数据检查通过；不将06作为完整观测，也不将健康通过或单次跨平台当作95%或论文五次统计复现。
- 09附加速度/动作记录器最初因Python消息包路径缺失而未启动；主测试器覆盖、里程和健康数据持续存在。补充动作首条在相对688.131秒，之前无补充速度/动作采样；原错误日志及passive_audit_attachment.json保留。passive_speed_audit的audit_start_absolute_sim=0是初始无效时钟，不能用作全程采样起点。附加后采样最大线速度指令2.0m/s；物理里程计小量超调与指令上限分开。
- 最终原生地图48次只读重放：按投影感知高度24组中2组仍是前沿，按平地实测感知高度0.456m查询24组中13组是前沿；未知样本XY投影均100%落在公共已知平面，加权未知样本分别84.49%/87.70%位于2m以上。这是查询级三维残余收益分布，不是新面积指标，也不是历史收益重建或唯一因果证明；公共平面图只用于离线诊断，未输入规划器。
- 旧03冻结地图138组5°/2°垂直采样对照未支持“改成2°即可消除残余收益”，未据此改正式设置。论文v4 IV-A统一修改版[25] FALCO和2m/s；Table I中GBP2四场景均用>号报告时间、标准差为横杠，Scene4为>1600s/>1560m，正文提到后期远点往返。不能假称论文所有GBP2试验完整完成，也不能仅凭表断言崩溃。作者各基线适配细节未核实。

## 目录、版本及本地交付

- 项目根D:/STGPlanner；实际Git根D:/STGPlanner/catkin_ws/src/STGPlanner。私有远端y-ii-ii/STGPlanner-reproduction，分支fix/fael-gbp2-progress；本轮父提交59eba6c，新本地代码/证据检查点以git log为准。本次代码/证据内容提交bbab488a560319118da045aaeade532e879b45b6已推送并通过私有性、远端提交及克隆SHA核验；随后元数据提交记录本次验收。未创建“全部修复完成”标签，main及历史基线保持不变。
- 保留main/repro-baseline-2026-10-26=dfc712982891f29c266083d7efad72ad48e730a2；benchmark/scene4-baselines及scene4-baselines-2026-10-27=9dec3c45184259a0d68e3dfe066040966d807aed。
- 专用WSL STGPlanner-Ubuntu20；实际编译源码/opt/stgplanner/benchmarks/*_ws/src，主环境/opt/stgplanner/catkin_ws。当前原生库/源码及benchmarks/progress_repairs对应09，不能当作07版本。preflight_repair_formal_gbp2_09/baseline07_progress_repairs保留07源码/补丁，trial07_validation.json保留07验收。
- 新工具在codex/work，主要为path_frontier_repair.py、test_path_frontier_selection.py、run_outcome.py、prepare_formal_09.py、run_formal_trial.py及原生收益探针。部署工具D:/STGPlanner/benchmarks。修改D盘上游克隆不会自动改变/opt编译副本。
- 原始结果benchmarks/results/各独立运行目录；06的user_pause.json/interruption.json不改，旧基线和中间失败均保留。progress_trials.json在09结果前固定选择；08单列diagnostic_runs，不混作重复。
- 本地报告codex/outputs/Scene4探索停滞修复报告.md/.html，曲线scene4_progress_curves.png、地图scene4_progress_maps.png，验证Scene4修复长测结果.json；旧部署/基线报告入口已更新。图片已人工查看。07阶段报告、验证和图另存codex/outputs/trial07_review。
- 只读证据：codex/outputs/运动执行与速度审计_2026-10-27.md、preflight_repair_formal_gbp2_07、diagnostic_gbp2_gain_08_setup、path_frontier_selection_regression、gbp_sampling_probe_07、gbp_stagnation_probe_09。正式证据归档到Git的evidence/scene4-progress-fix，源码/报告由本会话统一写入。
- 原始大对话工作区C:/Users/Administrator/Documents/Codex/2026-10-26/add-windowscapability-online-name-openssh-server-9仍保留；其outputs已复制到codex/outputs，不依赖整段聊天接续。

## 后续安排与备份边界

用户已明确要求GBP2先不继续测试。本次只整理报告、证据、代码及私有Git备份，不启动新仿真、不修改算法、不安排续跑。FAEL成功定义为本地一次完整运行达到公共95%并通过停车/传感器验收；GBP2最新09为完整2400秒限时、56.338896%，探索未完成。两者均不冒充论文五次统计复现。
潜在的感知自由空间/原生收益一致性问题仅作未解决事项留存；待用户明确恢复后才接续，新实验须新名称及单一仿真控制权。06保持用户中止分类，07/09保持完整限时失败，08单列诊断。
备份目标为私有仓库fix/fael-gbp2-progress分支，保留main及两个历史基线标签。本次不创建scene4-progress-fix-2026-10-27“全部修复完成”标签。远程备份验收另存codex/outputs/私有仓库备份验证.json；未完成的验证不得冒称通过。

## 本次私有备份验收

- 内容检查点：bbab488a560319118da045aaeade532e879b45b6，fix/fael-gbp2-progress，远端私有性已确认。
- 从远端独立克隆恢复，522项记录文件SHA全部匹配，09原生地图解压SHA匹配，工作树干净，历史基线标签保留。
- 内容结论仍为FAEL本地成功、GBP2未达95%；GBP2后续测试保持用户暂停，不自动续跑。
- 验收记录见project-context/BACKUP_VERIFIED.json、docs/私有仓库备份说明.md；本地记录在codex/outputs/私有仓库备份验证.json和私有仓库克隆恢复核验.json。
- 本文所记录的是内容提交，随后仅增加验收/交接元数据；最终分支HEAD以git log及远端最终核对为准。

## 最终备份完成记录（本地补全）

最终远端与本地HEAD：ac6927e8f41d95a406aec778e5536f6b2f529f8b。内容提交bbab488、验收/暂停交接提交ac6927e均已推送；私有性、原main/基线引用、522项克隆文件SHA及原生地图解压SHA均通过。当前Git工作树干净。
本地bundle已创建并验证：D:\STGPlanner\codex\outputs\STGPlanner-FAEL-success-GBP2-incomplete-2026-10-27.bundle，SHA256 415b4ef962f84bffa38f2ad2831b551bdc6272f4d38fece0ac9afa45eac2ee63。机器记录见codex/outputs/私有备份完成记录.json。Git内交接记录的是内容提交及验收元数据，当前最终HEAD可由git log核对。GBP2后续测试保持用户暂停，不自动恢复。

## 四算法论文对照汇总（只读整理）

新增codex/outputs/Scene4四算法与论文对比汇总.md/.html/.json，依据已存四组正式结果与论文v4 Scene4表格，单表列时间、路径、原生规划耗时、平均速度和95%判定。STGPlanner/TARE/修复FAEL达标，GBP2修复09未达95%；含版本与统计口径限制，无新增测试。本次已纳入阶段收尾报告及私有分支备份范围；本轮推送验收见独立记录，上一轮ac6927e记录作为历史保留。

## Scene4基线测试阶段性完成（最新授权收尾）

> **阶段状态（2026-10-27）：Scene4四算法基线测试已阶段性完成。STGPlanner、TARE、修复FAEL达到本地公共95%；GBP2修复09在2400.007秒限时结束，覆盖56.338896%，未完成。GBP2保持用户暂停，不启动后续测试。本阶段是单次工程验证与对照归档，不是论文五次统计复现。**

完成范围：四算法Scene4部署及单次工程测试、必要修复验证、论文单表对照、原始数据/代码保留、报告和交接。STGPlanner及修复FAEL的时间/路径接近论文均值；TARE成功但时间高25.40%、路径高9.23%，不能笼统称三者所有指标都相近。GBP2限时失败是本阶段有效结果，不再以其未修复阻止基线阶段关闭。尚未完成论文同条件五次统计及其他场景。

| 算法（本地版本） | 探索时间(s)：论文 → 本地 | 路径长度(m)：论文 → 本地 | 平均规划耗时(s)：论文 → 本地 | 平均速度(m/s)：论文 → 本地 | 本地覆盖指标 | 本地判定 |
|---|---:|---:|---:|---:|---:|---|
| STGPlanner（本机基线01） | 779.8±17.2 → 760.100 | 1194.0±12.9 → 1187.544 | 0.015 → 0.0405 | 1.53 → 1.562 | 95.0614% | 达到公共95% |
| TARE（本机基线01） | 1018.6±82.3 → 1277.279 | 1640.0±135.3 → 1791.349 | 0.338 → 0.2514 | 1.61 → 1.402 | 95.4023% | 达到公共95% |
| FAEL（原生修复01） | 1033.9±149.8 → 1017.008 | 1420.3±128.4 → 1351.931 | 0.119 → 0.0380 | 1.37 → 1.329 | 95.3366% | 达到公共95% |
| GBP2（原生修复09） | >1600（Std —） → 2400.007（限时） | >1560（Std —） → 2413.450 | 0.465 → 1.0080 | 0.97 → 1.006 | 56.3389% | 限时未达95% |

## 口径与结论

- 本地成功定义为公共观察器的已知平面面积/7790m²达到95%（面积>7400.5m²），并通过停车和传感器验收；不是算法自然结束或严格可达区域100%覆盖。论文未提供可直接对应的本地覆盖比例，故不填造论文覆盖率。
- GBP2的2400.007秒、2413.450米是限时观测窗口及其部分探索轨迹，不是完成时间/完整覆盖路径。论文的>1600和>1560同样不是准确完成值；Std横杠表示未提供，不能单独断言成功或崩溃，因此不计算GBP2相对论文的完成性能差。
- FAEL使用修复后的01运行，GBP2使用最新修复/校准后的09运行；两者含本地实现改动，不能与未经改动的上游/作者配置画等号。原FAEL1600秒41.2775%、原GBP2 1600秒41.1789%及全部中间失败/中止数据均保留，未用后续结果覆盖。
- 规划耗时按各代码原生统计范围：STGPlanner/FAEL为IterationTime，TARE为/runtime分项和，GBP2为服务回调内部稳态时钟。统计边界、CPU和负载不同，不能据此宣称跨论文的计算效率排名。本地速度是里程/探索仿真时长，含转向、等待及停滞，不是2m/s速度上限。
- 完成运行的单次数值对照：STGPlanner时间比论文均值低2.53%、路径低0.54%；FAEL时间低1.63%、路径低4.81%；TARE时间高25.40%、路径高9.23%。这些是描述性差值，不证明改进/退化或统计显著性。

目录整理：48个无部署依赖的一次性文件归类迁移并逐项SHA核对；已部署入口、算法源码、配置、原始结果均未移动或修改。汇总工具位于codex/work/reporting；旧工作稿在codex/work/archive/2026-10-27-scene4；完整用途见codex/outputs/代码目录说明.md及benchmarks/FILE_INDEX.md。

本轮验证：只读核对四组原始结果与对比表、原始证据SHA、迁移前后字节和交接/暂停状态；不运行ROS或重编译。未解决事项：GBP2后期覆盖停滞，收益/平面增长一致性待以后明确授权研究；STGPlanner/TARE/修复FAEL暂无已证实阻止本次探索的未修复故障，不代表代码无缺陷。后续：默认维持暂停和阶段完成；仅在用户明确授权新范围后另开新名试验。

本轮备份：沿用fix/fael-gbp2-progress，保留main和两个历史基线引用。内容提交SHA及远端恢复验收见SCENE4_STAGE_BACKUP_VERIFIED.json；本轮不新建“全部问题修复”标签。先前ac6927e/522项验收仅为上一轮记录。
