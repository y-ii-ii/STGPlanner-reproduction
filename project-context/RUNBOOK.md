# 新会话恢复与协作清单

> 2026-10-28用户已明确恢复GBP2面积提升与机制验证；本会话独占运行/代码。TARE后续完成并保持原版。旧历史命令不是其他会话的自动执行授权。

## 新会话怎么开始

在STGPlanner项目中创建一个**全新会话**，不要复制完整旧聊天。首条可直接粘贴：

> 请先读取D:/STGPlanner/AGENTS.md、D:/STGPlanner/codex/STATUS.md和RUNBOOK.md，只汇报当前状态与本会话负责范围，暂不启动仿真。

用户明确恢复后，实验会话可用：

> 恢复GBP2验证。先读取项目交接文件，保留06用户中止数据，为新一轮分配新运行名，完整验证95%目标后再更新报告和私有分支。

建议按任务开短会话：①算法与长测；②报告与论文对照；③后续新功能。多开本身不会把会话变成共享完整记忆。共享依据是文件、Git、原始结果和简短阶段交接。不要同时让几个会话操作同一仿真、同一代码文件或切同一个工作目录的分支。

## 启动前核对

```powershell
Get-Content D:/STGPlanner/codex/STATUS.md
Get-Content D:/STGPlanner/codex/SIMULATION_LOCK.json
git -C D:/STGPlanner/catkin_ws/src/STGPlanner status --short
git -C D:/STGPlanner/catkin_ws/src/STGPlanner log -4 --oneline
wsl.exe --list --running
```

2026-10-27用户已在“STGPlanner 报告与论文对照”明确恢复测试；本轮由算法与长测会话01a17c85-9d73-7573-885c-a95dbbc4abbf独占仿真及共享代码/状态写入，报告会话只读。具体运行状态以STATUS.md和SIMULATION_LOCK.json为准，其他会话不能因本清单启动第二套仿真。每次取得控制权前检查实际进程，确认没有其他会话持有仿真；再把锁记录state设为running、owner_thread和trial设为本会话。结束后更新为idle/paused，并写结果路径。锁文件是协作约定，不是操作系统强制互斥。

## 用户明确恢复后的长测示例

无需因迁移重新安装。先确认最新代码、原生编译指纹和配置，必要时再编译。每次采用新目录，禁止覆盖任何已有运行（尤其06/07/08/09）；示例10也须先检查名称是否已占用。

```powershell
git -C D:/STGPlanner/catkin_ws/src/STGPlanner branch --show-current
# 修改源码后才按需重建；正在长测时不得执行：
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/benchmarks/build_progress_repairs.sh gbp2
# 必须先确认本专用发行版没有别的会话正在使用，才能终止并重启：
wsl.exe --terminate STGPlanner-Ubuntu20
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/benchmarks/run_benchmark.sh gbp2 --name repair_formal_gbp2_10 --limit 2400
```

运行前固定选择并保存manifest/config。运行后看result.json、metrics.jsonl、events.jsonl、known_plane_cells.csv、原生日志和停车验收，不能只看是否生成路径。06不能从1082秒原地续算正式试验。

## 报告工具位置

D:/STGPlanner/codex/work保留最新未发布工具草稿，D:/STGPlanner/benchmarks有已部署工具。旧对话脚本的相对路径已随codex/work和codex/outputs迁入；使用前读STATUS中的待办，不要无条件批量运行。

完成新正式运行且整理选择文件后：Linux执行analyze_progress.py、plot_progress.py；Windows执行make_progress_report.py --output D:/STGPlanner/codex/outputs，更新旧报告入口，pandoc生成独立HTML；stage_progress.py归档。正式发布前核查模板不再写06为最终完成，所有验证通过。

## 每次交接写什么

只补必要信息：目标/暂停或运行状态、当前分支与提交、修改文件、测试命令与结果、正在运行的PID/试验名、未解决问题、下一步。状态以最新文件和实际进程为准；历史文件不是当前运行指令。

## 官方依据

AGENTS.md用于持久项目指导，官方说明：https://learn.chatgpt.com/docs/agent-configuration/agents-md 。本项目用短AGENTS加独立状态文件，避免将全部实验历史塞入自动加载上下文。迁入项目不能扩大单会话上下文或保证不发生其他中断。

## 阶段完成后的交接入口

先读SCENE4_STAGE_COMPLETION.json、STATUS.md最新阶段结论，再看四算法论文对比汇总和代码目录说明。STGPlanner/TARE/修复FAEL达95%，GBP2修复09限时56.338896%。TARE时间比论文均值高25.40%；不将所有成功方法称为所有指标接近。

当前只读表格生成器：codex/work/reporting/summarize_four_algorithms.py（仓库副本benchmarks/reporting/）；逐文件说明benchmarks/FILE_INDEX.md；一次性工作文件已归档，旧路径映射和SHA见codex/work/archive/2026-10-27-scene4/move_manifest.json。已部署运行入口仍在原位置。不要重跑旧prepare_formal_09/run_formal_09、旧报告/备份生成器。

本阶段完成不等于全部代码问题修复或论文多次统计复现。GBP2剩余问题已登记但无自动续跑；未来恢复须明确授权、检查仿真锁与实际进程并使用全新结果目录。私有备份核验见SCENE4_STAGE_BACKUP_VERIFIED.json。

## 本轮阶段收尾私有备份已验收

内容提交`6fd0d05332be4571b845c85f71bbb04ed011dbe7`已推送到私有分支fix/fael-gbp2-progress。远端独立恢复克隆的622项清单SHA、412项原始证据、原生地图解压SHA及归档移动文件均核验通过；main、历史基线分支和两个标签未变。验收记录SCENE4_STAGE_BACKUP_VERIFIED.json指向此内容提交；随后仅提交验收/交接元数据，最终分支HEAD以git log和远端核对为准。GBP2继续暂停，本次未启动仿真。

## TARE后续优化已结束

先读STATUS最新TARE结论和TARE优化测试报告。实际原生部署见deployment_state.json，不以D盘上游克隆推断。工具及各自作用见benchmarks/tare_optimization/README.md；原始候选和新原配置对照分开保留。原生感知模型修正与性能收益分开评价，不能将新原配置的改善归到修改名下。当前无活动长测；GBP2继续暂停。后续新实验必须明确范围、先检查锁/进程，并采用新结果名。

## TARE后续私有备份已验收

内容提交`79445155ee6bfaa7621ac99c880bc1a3984d4dd6`已推送到私有分支fix/fael-gbp2-progress。远端独立克隆恢复通过261项新增归档的压缩前后SHA、此前622项清单、67项实验隔离/运行检查，历史原始证据未改动；main、历史基线分支和两个标签均保留。验收记录TARE_OPTIMIZATION_BACKUP_VERIFIED.json指向该内容提交，随后交接/报告互链元数据提交的最终HEAD以git log和远端核对为准。TARE当前恢复已验证原版，无活动测试；GBP2保持暂停。旧四算法表只增加后续入口，保留原预选TARE基线行，全部新对照/候选在TARE报告中单列。

## 当前GBP2恢复优化（2026-10-28，覆盖上方旧暂停状态）

用户已明确恢复GBP2优化，TARE/FAEL不重跑。首先看STATUS最新GBP2章节和SIMULATION_LOCK.json；gbp2_default_frontier_20261028_10正在完整2400秒观察，原生约707.079秒返航且公共覆盖40.4724%，仍不等于探索成功。当前仿真及共享代码仅归原算法会话所有，其他会话不得启动/停止或重编译。

2026-10-28后续检查点：10已完整结束并清理，46项协议验收通过、95%失败；独立新图gbp2_frontier03_20261028_11正在运行，限时2400秒。新监督器已补充实际/proc检查和所有配置文件的冻结指纹；11起只在公共停止后保存原生全局图。不要启动第二轮或编译。

当前工具集中codex/work/gbp2_optimization_20261028；run_trial.sh启动固定协议，run_gbp2_trial.py冻结指纹并按所属结果目录清理，observe_and_save.py只读订阅及结束后保存原生地图。assert_idle.py核对实际/proc、端口与锁；prepare_frontier.py仅空闲后部署预设单阈值，保存before/after。下一预设值0.03，必须新运行名。analyze_running.py读取进度/原生选点日志；compare_plane_maps.py仅离线对比历史成功运行重叠，绝不可给规划器输入这些平面图。不要重跑旧prepare或历史恢复脚本。

## 最新硬限制：GBP2本轮最多3次，已停止

10/11/12三次已完整结束且未达95%，没有覆盖改善。用户限制覆盖旧v1/v2方案：1.5%、全部复测、新ROS/Gazebo/地图重放与算法修改均取消。权威限制codex/GBP2_EXPERIMENT_LIMITS.json；新入口guard_new_experiment.py拒绝继续。仅离线收尾、恢复已测试09配置、报告/交接及私有备份。不得以旧“恢复测试”章节自动续跑。

## GBP2本轮原生参数优化阶段结束（最新）

本轮新增正式试验限额3次（10/11/12）已用完，三次均未达公共95%，也未提高历史修复09的56.338896%覆盖。按用户限制停止GBP2优化，不再测试或修改算法。当前配置下GBP2存在明显覆盖停滞，不作为Scene4达95%的成功基线。

已恢复历史修复09的可追溯已测试配置（前沿0.01、名义高度0.456m），原生源码及两库仍与09一致；该配置仍明确标为未达95%。全部候选before/after、失败数据和校准依据保留，不将较差候选作为默认性能优化。

当前无活动仿真；TARE/FAEL未重跑。当前工具统一在codex/work/gbp2_optimization_20261028，逐文件作用见README.md；实验方案v1/v2、原生快照、所有失败/候选、验证和部署指纹保留。先读最新STATUS，旧长测状态只作历史。后续先核对锁、实际进程和端口，使用新结果目录，不把原生结束或健康通过算作95%成功。私有备份验收见GBP2_OPTIMIZATION_BACKUP_VERIFIED.json。
