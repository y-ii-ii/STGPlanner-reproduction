# 工作脚本导航

Scene4工程基线已阶段性完成，GBP2暂停；不要批量执行这里的脚本。

| 位置 | 用途 |
|---|---|
| reporting/ | 当前只读四算法论文对比生成器 |
| maintenance/ | 本轮阶段收尾、文档同步及验证工具 |
| archive/2026-10-27-scene4/experiment-history/ | 无活动依赖的一次性历史准备/实验辅助文件 |
| archive/2026-10-27-scene4/report-history/ | 历史报告/图表/打包草稿 |
| archive/2026-10-27-scene4/backup-history/ | 历史私有备份和上传过程工具 |
| archive/2026-10-27-scene4/notes-logs/ | 旧记录、日志、文本和样式 |
| 根目录保留的脚本 | 已部署同名工具、被现有脚本引用的文件或有原工作目录假设的程序；保持路径兼容 |
| private-backup-restore-*/ | 已核验的独立远端恢复克隆，路径保留以匹配已有验收记录；不是主工作仓库 |

文件作用见../outputs/代码目录说明.html；benchmarks逐文件索引见../../benchmarks/FILE_INDEX.md。
移动清单archive/2026-10-27-scene4/move_manifest.json含旧路径、新路径及移动时SHA；未删除文件。历史脚本如需重放，先按清单恢复原路径或在独立副本调整引用，不能重用旧运行目录。目录整理后当前汇总脚本只读取原始结果，不再修改STATUS。
