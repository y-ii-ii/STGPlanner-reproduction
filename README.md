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
