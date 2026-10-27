# STGPlanner Scene4 复现基线

基于 [Haochen-Niu/STGPlanner](https://github.com/Haochen-Niu/STGPlanner) 的公开代码，保留其 Git 历史、作者信息及各文件原有许可声明。上游基线：`59b41451f7b80ba09a9bcbaf44b58141cd6f9de8`。原始项目说明和论文引用见 [UPSTREAM_README](docs/UPSTREAM_README.md)。

本仓库用于保存本机已验证版本，后续在分支上逐步修改，并通过固定标签回到当前基线。

## 已验证范围

- Windows 11 + D 盘独立 WSL2 Ubuntu 20.04，ROS Noetic / Gazebo 11。
- 28 个 Catkin 包构建成功；实际运行公开代码提供的 Scene4。
- 修复编译依赖、CRLF、场景模型、TF、空 Marker、结束期间误报超时与停车链路。
- 最终完整观察 1200.1 秒，16 项生命周期检查全部通过；3646 次成功且非空规划，项目累计距离约 1214.97 米。
- 默认以项目指标超过名义地图面积的 95% 停止；不代表真实可达区域 100% 覆盖。
- 只完成 Scene4 功能复现；其他论文场景、基线方法和同配置五轮统计尚未复现。

## 入口

- [完整部署报告](docs/STGPlanner部署报告.md) / [单文件 HTML 报告](docs/STGPlanner部署报告.html)
- [版本控制与回滚](docs/版本控制与回滚.md)
- [最终验证结果](evidence/scene4-final/verification_summary.json)
- [论文 Scene4 对照](evidence/paper-comparison.json)
- [部署脚本](deployment/scripts/) / [Windows 启停入口](deployment/windows/)

## 当前机器启动

```powershell
& 'D:\STGPlanner\Start-STGPlanner.cmd'
# 停止专用发行版中的项目
& 'D:\STGPlanner\Stop-STGPlanner.cmd'
```

从仓库恢复运行脚本（尤其在切换旧版本后）：

```powershell
Set-Location D:\STGPlanner\catkin_ws\src\STGPlanner
& .\deployment\install-local-tools.ps1
wsl.exe -d STGPlanner-Ubuntu20 -u root -- bash /mnt/d/STGPlanner/scripts/build.sh
```

新电脑应先克隆到上述固定路径，再按照部署报告导入 Ubuntu、安装依赖、复制部署工具和构建。报告中历史上游克隆命令仅说明原部署过程，恢复此复现版本应克隆本仓库，而非重新拉取未经修复的上游。

## 版本约定

固定基线标签：`repro-baseline-2026-10-26`。`main` 保存可运行版本；新修改先开独立分支，完成有意义的检查后提交和推送。回滚方法见对应文档。

仓库包含完整上游源码、修复、部署脚本、报告、截图与选定测试证据。WSL 虚拟磁盘、APT/模型下载缓存、编译产物和密钥不进入 Git；模型由脚本从固定上游提交重新下载。

## Scene4 多算法本机对比（2026-10-27）

本分支在同一个公开 Scene4 上部署 GBP2（gbplanner2）、TARE、FAEL，并补测 STGPlanner。各方法完成原生编译、短测及一次统一协议修订3的正式测试；原 `main` 和 `repro-baseline-2026-10-26` 保留。

| 方法 | 仿真时间(s) | 里程(m) | 结果 |
|---|---:|---:|---|
| STGPlanner | 760.10 | 1187.54 | 达到项目95%门槛 |
| TARE | 1277.28 | 1791.35 | 达到项目95%门槛 |
| GBP2 | 1600.04 | 1945.54 | 限时未完成，指标41.179% |
| FAEL | 1600.04 | 571.34 | 后期空候选停滞，限时指标41.278% |

这是每种方法1次正式试验，不能替代论文5次均值±标准差。FAEL未复现论文完成性能；115项数据和接口检查通过不代表四方法均探索成功。修复过程中的失败数据也保留，不将不同协议试验混作重复统计。

- [完整对比报告、部署命令与故障处理](docs/Scene4基线算法对比报告.md)
- [统一测试协议与比较边界](benchmarks/benchmark_protocol.md)
- [上游精确提交与依赖锁定](benchmarks/sources.lock.json)
- [正式数据、失败对照与115项验收](evidence/scene4-baselines/validation.json)
- [实际覆盖曲线](docs/scene4_curves.png) / [已知平面与实际轨迹](docs/scene4_maps.png)

本机环境为 `D:\STGPlanner\benchmarks`；Linux工作空间在D盘专用WSL虚拟磁盘中。重建入口是 `build_all_baselines.sh`；单项测试入口是 `run_benchmark.sh`，需要给出新的结果目录名。完整数据读取、计时口径和回滚方法见报告。
