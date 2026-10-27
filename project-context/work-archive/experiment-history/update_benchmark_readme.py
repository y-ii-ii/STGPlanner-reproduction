from pathlib import Path
import json
repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner');p=repo/'README.md';s=p.read_text(encoding='utf-8')
marker='\n## Scene4 多算法本机对比（2026-10-27）'
if marker in s:s=s[:s.index(marker)]
s+=marker+'''

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

本机环境为 `D:\\STGPlanner\\benchmarks`；Linux工作空间在D盘专用WSL虚拟磁盘中。重建入口是 `build_all_baselines.sh`；单项测试入口是 `run_benchmark.sh`，需要给出新的结果目录名。完整数据读取、计时口径和回滚方法见报告。
'''
p.write_text(s,encoding='utf-8',newline='\n');print(p)
