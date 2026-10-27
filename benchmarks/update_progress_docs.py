from pathlib import Path
import json
task=Path(__file__).resolve().parents[1];out=task/'outputs';repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner')
v=json.loads((out/'Scene4修复长测结果.json').read_text(encoding='utf-8'))
notice='> **2026-10-27 后续更新：** 本页保留修复前的历史结果。FAEL、GBP2 的新增源码修复及长测结果见 [探索停滞修复报告](Scene4探索停滞修复报告.html)，原始旧结果未覆盖。'
for name in ['STGPlanner部署报告.md','Scene4基线算法对比报告.md']:
    path=out/name;text=path.read_text(encoding='utf-8')
    if notice not in text:
        first,rest=text.split('\n',1);text=first+'\n\n'+notice+'\n'+rest
    heading='## 后续更新：FAEL 与 GBP2 探索停滞修复（2026-10-27）'
    if heading in text:text=text.split(heading)[0].rstrip()+'\n'
    text+='\n'+heading+'\n\n本次保留原1600秒基线，另开修复分支并重新进行真实长测。\n\n'
    for method in ['fael','gbp2']:
        b=v['results'][method]['before'];a=v['results'][method]['after']
        text+=f"- {method.upper()}：原指标 {b['coverage_fraction']*100:.3f}%；修复后 {a['coverage_fraction']*100:.3f}%，仿真 {a['sim_time_s']:.3f}s，里程 {a['distance_m']:.3f}m，{'达到统一95%门槛' if a['finish_reason']=='coverage_threshold' else '限时未完成'}。\n"
    text+='\n根因、精确补丁、回归检查、1600秒同期比较、地图和回滚命令见 [新增修复报告](Scene4探索停滞修复报告.html)。每方法1次正式运行，新增本地源码改动不等于论文原始配置的统计复现。私有仓库分支 `fix/fael-gbp2-progress`，最终标签和远程发布验收尚未完成。\n'
    path.write_text(text,encoding='utf-8',newline='\n')
path=repo/'README.md';text=path.read_text(encoding='utf-8');heading='## Scene4 探索停滞修复（2026-10-27）'
if heading in text:text=text.split(heading)[0].rstrip()+'\n'
text+='\n'+heading+'\n\n`fix/fael-gbp2-progress` 修复 FAEL 前沿生命周期、候选连通性及 GBP2 射线缓存；原1600秒数据保留。\n\n| 方法 | 修复前指标 | 修复后指标 | 仿真时间(s) | 里程(m) | 结果 |\n|---|---:|---:|---:|---:|---|\n'
for method in ['fael','gbp2']:
    b=v['results'][method]['before'];a=v['results'][method]['after']
    text+=f"| {method.upper()} | {b['coverage_fraction']*100:.3f}% | {a['coverage_fraction']*100:.3f}% | {a['sim_time_s']:.3f} | {a['distance_m']:.3f} | {'统一95%门槛' if a['finish_reason']=='coverage_threshold' else '限时未完成'} |\n"
text+='\n- [修复与长测报告、重建和回滚命令](docs/Scene4探索停滞修复报告.md) / [单文件HTML](docs/Scene4探索停滞修复报告.html)\n- [修复前后源码、补丁与指纹](benchmarks/progress_repairs/manifest.json)\n- [独立回归与真实长测验收](evidence/scene4-progress-fix/validation.json)\n\n每方法只有1次正式运行，新增2400秒上限与原1600秒预算在报告中分开比较；不声称复现论文5次统计。最终标签和远程发布验收尚未完成，原main和两个历史基线标签保留。Git切换不会自动恢复Linux原生编译副本，回滚步骤须按报告执行。\n'
path.write_text(text,encoding='utf-8',newline='\n')
attributes=repo/'.gitattributes';text=attributes.read_text(encoding='utf-8')
for line in ['/evidence/scene4-progress-fix/** -text','/evidence/scene4-progress-fix/** whitespace=-blank-at-eol,-blank-at-eof','/benchmarks/progress_repairs/** -text','/benchmarks/progress_repairs/** whitespace=-blank-at-eol,-blank-at-eof']:
    if line not in text:text+='\n'+line
attributes.write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
print('Updated both report entry points, README and evidence attributes.')
archive_readme=repo/'benchmarks/progress_repairs/README.md'
archive_text=archive_readme.read_text(encoding='utf-8')
archive_text=archive_text.replace('Full reports\nand final acceptance are pending the new GBP2 long run; this is a source backup.',
    'Full reports and the recorded final long-run acceptance are available in docs/Scene4探索停滞修复报告.md and evidence/scene4-progress-fix/validation.json. The source checkpoint is preserved in Git history.')
archive_text=archive_text.replace('Final claims must follow the full real run.',
    'Final results use the explicitly selected runs in progress_trials.json. Each method has one final formal run; intermediate versions are separate diagnostics.')
archive_text=archive_text.replace('Latest run06 was selected before its outcome and is undergoing real2400s\nverification. Final claims must follow its recorded result. Prior failures remain.',
    'Run06 was user-interrupted. The fresh selected run is listed in progress_trials.json; its result is recorded in\n../../evidence/scene4-progress-fix/validation.json and the report in docs.\nPrior failures remain separate. A successful I/O audit does not imply exploration completion.')
archive_readme.write_text(archive_text,encoding='utf-8',newline='\n')
