from pathlib import Path
import json,shutil
task=Path(__file__).resolve().parents[1];out=task/'outputs';bench=Path('D:/STGPlanner/benchmarks')
summary=json.loads((out/'Scene4对比结果.json').read_text(encoding='utf-8'))
p=out/'STGPlanner部署报告.md';s=p.read_text(encoding='utf-8');marker='\n## 8. Scene4 三种论文基线的本机部署与对比'
if marker in s:s=s[:s.index(marker)]
s=s.replace('### 复现范围与论文表 I 对照','### 首次单方法验收：复现范围与论文表 I 对照（历史记录）')
s=s.replace('本次未运行其他三个论文场景、GBP2/TARE/FAEL 基线，也未按论文要求在相同配置下重复 5 次计算均值和标准差；','首次单方法验收尚未运行其他三个论文场景及GBP2/TARE/FAEL基线；后续Scene4基线部署和实际对比见第8节。至本次更新仍未按论文要求在相同配置下重复5次计算均值和标准差；')
append=marker+'\n\n追加日期：'+summary['generated']+'。已实际部署 GBP2、TARE、FAEL，并在同一 Scene4 上完成各1次正式长测；同时补测 STGPlanner。本次完整方法、修复、指令和原始数据说明见 [Scene4基线算法对比报告](Scene4基线算法对比报告.html)。原第6节的历史 STGPlanner 单方法验证保留；下表使用新统一观察器和修复后的公共控制器，属于另一批试验。\n\n'
append+='| 方法 | 结束状态 | 仿真时间(s) | 距离(m) | 已知平面指标名义比值 |\n|---|---|---:|---:|---:|\n'
for name in ['gbp2','tare','fael','stgp']:
    d=summary['results'][name];label={'gbp2':'GBP2','tare':'TARE','fael':'FAEL','stgp':'STGPlanner'}[name]
    append+=f"| {label} | {'达到统一95%门槛' if d['finish_reason']=='coverage_threshold' else '1600s限时未完成'} | {d['sim_time_s']:.2f} | {d['distance_m']:.2f} | {100*d['coverage_fraction']:.3f}% |\n"
append+='\n论文每方法5次均值±标准差，本批次仅每方法1次，且基线版本、适配接口和硬件不同，不能宣称严格复现论文统计结论。限时记录不能当作完整探索结果。\n\n![Scene4统一指标和真实里程曲线](scene4_curves.png)\n\n![各方法实际记录的已知平面和轨迹](scene4_maps.png)\n\n源码、配置、补丁和结果备份到私有仓库的 `benchmark/scene4-baselines` 分支；原 `main` / `repro-baseline-2026-10-26` 保留。完整交付为 `Scene4基线对比材料.zip` 和 `Scene4对比结果.json`。\n'
p.write_text(s+append,encoding='utf-8',newline='\n');shutil.copy2(p,Path('D:/STGPlanner/部署报告.md'))
print(p)
