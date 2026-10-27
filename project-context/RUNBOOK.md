# 新会话恢复与协作清单

> Scene4四算法基线测试已阶段性完成；GBP2后续测试保持用户暂停。当前只维护报告/归档；下列启动命令仅为未来明确恢复后的参考，不自动执行。

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
