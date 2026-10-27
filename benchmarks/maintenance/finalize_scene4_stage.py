"""Close the Scene4 engineering baseline stage using saved data only; never run ROS."""
import datetime
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path('D:/STGPlanner')
REPO = ROOT / 'catkin_ws/src/STGPlanner'
WORK = ROOT / 'codex/work'
OUT = ROOT / 'codex/outputs'
NOW = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
BASE = 'ac6927e8f41d95a406aec778e5536f6b2f529f8b'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8', newline='\n')

def dump(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert subprocess.check_output(['git', '-C', str(REPO), 'branch', '--show-current'], text=True).strip() == 'fix/fael-gbp2-progress'
assert subprocess.check_output(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True).strip() == BASE
assert not subprocess.check_output(['git', '-C', str(REPO), 'status', '--porcelain']).strip()

# Preserve the old published manifest before updating report hashes. Raw evidence is immutable.
manifest_path = REPO / 'evidence/scene4-progress-fix/evidence_manifest.json'
old_manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
for name, expected in old_manifest['files'].items():
    assert sha(REPO / name) == expected, name
snapshot = REPO / 'project-context/history/scene4-stage-before-closure'
write(snapshot / 'README.md', '# 阶段收尾前的交接快照\n\n来源提交：`' + BASE + '`。用于保留旧报告和交接文字；当前状态见两级上方的STATUS.md。原始数据在evidence中未改动。\n')
for name in ['evidence/scene4-progress-fix/evidence_manifest.json', 'README.md',
             'project-context/STATUS.md', 'project-context/RUNBOOK.md', 'project-context/SIMULATION_LOCK.json']:
    target = snapshot / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO / name, target)

# Move only unreferenced one-off workspace files. Deployed scripts and their filename
# dependencies retain their exact original locations, including relative-path tools.
files = {p.name: p for p in WORK.iterdir() if p.is_file()}
deployed = [ROOT / 'benchmarks', ROOT / 'scripts', REPO / 'benchmarks']
keep = {n for n in files if any((d / n).is_file() for d in deployed)}
external = '\n'.join(p.read_text(encoding='utf-8', errors='replace')
                     for d in deployed for p in d.iterdir()
                     if p.is_file() and p.suffix.lower() in ('.py', '.sh', '.ps1', '.cpp'))
texts = {n: p.read_text(encoding='utf-8', errors='replace') for n, p in files.items()
         if p.suffix.lower() in ('.py', '.sh', '.ps1', '.cpp', '.md')}
keep |= {n for n in files if n in external}
while True:
    previous = set(keep)
    references = '\n'.join(texts.get(n, '') for n in keep)
    keep |= {n for n in files if n in references}
    if previous == keep:
        break

archive = WORK / 'archive/2026-10-27-scene4'
moves = []
for name in sorted(set(files) - keep):
    source = files[name]
    if name == 'summarize_four_algorithms.py':
        target = WORK / 'reporting' / name
        category = 'reporting'
    else:
        category = ('notes-logs' if source.suffix.lower() in ('.log', '.txt', '.md', '.css')
                    else 'backup-history' if any(s in name for s in ('github', 'backup', 'upload', 'remote', 'clone', 'stage_'))
                    else 'report-history' if any(s in name for s in ('report', 'plot', 'package', 'finalize', 'render'))
                    else 'experiment-history')
        target = archive / category / name
    assert source.resolve().is_relative_to(WORK.resolve())
    assert target.resolve().is_relative_to(WORK.resolve()) and not target.exists()
    digest = sha(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))
    assert sha(target) == digest
    moves.append({'old_path': str(source), 'new_path': str(target), 'sha256': digest, 'category': category})
dump(WORK / 'archive/2026-10-27-scene4/move_manifest.json', {'generated_at': NOW, 'moves': moves,
     'policy': 'Only unreferenced one-off files moved; all operational script paths retained; no raw result moved.'})

# The current report generator is read-only with respect to project status.
generator = WORK / 'reporting/summarize_four_algorithms.py'
source = generator.read_text(encoding='utf-8')
source = source[:source.index("status=root/'codex/STATUS.md'")] + 'print(table)\n'
source = source.replace('**当前结果：', '**Scene4基线测试已阶段性完成。当前结果：')
write(generator, source)
subprocess.run(['python', str(generator)], check=True, stdout=subprocess.DEVNULL)
summary = (OUT / 'Scene4四算法与论文对比汇总.md').read_text(encoding='utf-8')
table = summary[summary.index('| 算法（本地版本）'):summary.index('\n## 口径与结论')].strip()
cautions = summary[summary.index('## 口径与结论'):summary.index('## 原始结果选择')].strip()
notice = ('> **阶段状态（2026-10-27）：Scene4四算法基线测试已阶段性完成。STGPlanner、TARE、修复FAEL达到本地公共95%；'
          'GBP2修复09在2400.007秒限时结束，覆盖56.338896%，未完成。GBP2保持用户暂停，不启动后续测试。'
          '本阶段是单次工程验证与对照归档，不是论文五次统计复现。**\n\n')
block = ('<!-- scene4-stage-summary:start -->\n' + notice + '## 最新四算法与论文数据对照\n\n' + table + '\n\n' + cautions
         + '\n\n完整数值、原始结果选择与SHA见[四算法论文对比汇总](Scene4四算法与论文对比汇总.html)。'
         '目录与脚本用途见[代码目录说明](代码目录说明.html)。下方保留原报告及历史测试过程。\n'
         '<!-- scene4-stage-summary:end -->\n\n')
report_names = ['Scene4基线算法对比报告', 'Scene4探索停滞修复报告',
                'FAEL成功与GBP2未完成阶段总结', 'STGPlanner部署报告']
for stem in report_names:
    path = OUT / (stem + '.md')
    original = path.read_text(encoding='utf-8')
    target = snapshot / 'docs' / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO / 'docs' / path.name, target)
    first, rest = original.split('\n', 1)
    write(path, first + '\n\n' + block + rest.lstrip())

descriptions = {
 'benchmark_trial.py': '统一测试主程序：公共覆盖、里程、健康与停车验收，保存原始运行结果。',
 'benchmark_coverage.cpp': '独立公共已知平面面积观察器；不向原生规划器提供真值探索目标。',
 'benchmark_cloud_bridge.cpp': '点云适配桥，将公共传感器流接到各算法原生接口。',
 'run_benchmark.sh': '单次算法运行入口，要求使用全新结果目录名。',
 'run_formal_trial.py': '正式运行监督器，保存运行版本并按结果目录归属清理进程。',
 'run_outcome.py': '结果分类：公共阈值、限时、原生结束、用户中止分别记录。',
 'cleanup_trial_runtime.py': '按进程命令/环境中的指定结果目录识别归属，清理并核查端口。',
 'Run-Scene4Suite.ps1': '历史四算法串行测试队列入口；当前禁止自动执行。',
 'Run-ProgressSuite.ps1': '历史修复后串行队列入口；当前禁止自动执行。',
 'Run-PilotQueue.ps1': '短测队列入口，pilot数据不当作论文正式重复。',
 'sources.lock.json': '各基线及依赖的精确上游地址和提交。',
 'protocol_manifest.json': '初期测试协议与环境指纹，历史记录。',
 'protocol2_manifest.json': '协议修订2的冻结记录，历史记录。',
 'progress_trials.json': '预先选择的修复后正式结果与诊断结果目录，禁止混作重复统计。',
 'environment.json': '部署环境/工作空间记录。',
 'benchmark_protocol.md': '公共测试协议、指标定义与比较边界。',
 'clone_locked_sources.py': '按sources.lock.json拉取锁定源码；不修改历史运行。',
 'prepare_benchmark.py': '生成/部署算法适配配置的历史准备程序。',
 'collect_benchmark_builds.py': '收集原生构建改动、适配补丁与指纹。',
 'build_all_baselines.sh': '编译全部基线的入口，恢复后才可按需执行。',
 'build_baseline.sh': '单个基线原生工作空间构建入口。',
 'build_gbp2.sh': 'GBP2依赖及原生工作空间构建。',
 'build_cloud_bridge.sh': '构建公共点云适配程序。',
 'build_coverage.sh': '构建独立公共面积观察器。',
 'build_progress_repairs.sh': '应用/构建FAEL与GBP2已保留修复，实际目标在WSL /opt。',
 'apply_progress_repairs.py': '将修复后的原生源码应用到WSL编译副本。',
 'rollback_progress_repairs.py': '按修复快照回滚原生源码；切Git分支不会自动完成此操作。',
 'capture_progress_manifest.py': '记录修复源码、配置和编译库SHA。',
 'apply_trial_repairs.py': '历史时间预算、返航/结束契约与参数适配修改。',
 'rollback_trial_repairs.py': '回滚上述历史契约/配置适配。',
 'path_frontier_repair.py': 'GBP2局部选路资格修复：仅可行且含有效前沿路径参与竞争。',
 'test_path_frontier_selection.py': '提取实际评分代码块的受控用例与幂等性检查。',
 'fael_frontier_regression.cpp': 'FAEL前沿生命周期与候选连通性受控原生回归。',
 'run_fael_frontier_regression.sh': '构建并执行FAEL受控回归；当前不执行。',
 'ray_cache_regression.py': 'GBP2射线缓存独立回归。',
 'gain_frame_regression.py': '感知坐标与收益计算几何受控回归。',
 'gbp_core_regression.py': 'GBP2核心逻辑受控回归。',
 'cluster_frontier_regression.py': 'GBP2聚类前沿类型/资格回归。',
 'path_contract_regression.py': '原生路径输出与公共执行链契约回归。',
 'trial_contract_regression.py': '时间/返航/终止契约回归。',
 'validate_outcomes_07.py': '对真实存档及中止元数据核查运行分类。',
 'validate_frontier_calibration.py': '参数校准及前沿相关配置一致性核查。',
 'verify_runtime_freeze_09.py': '09原生源码、加载库、控制二进制与参数的11项冻结核查。',
 'validate_benchmark.py': '核查原始四算法数据与协议验收；通过不等于全部算法探索完成。',
 'analyze_progress.py': '读取选定运行，区分协议健康和探索目标，汇总修复前后数据。',
 'plot_benchmark.py': '生成修复前四算法覆盖/轨迹图。',
 'plot_progress.py': '生成修复前后覆盖曲线与地图。',
 'plot_progress_diagnostic.py': '生成停滞诊断图。',
 'make_benchmark_report.py': '旧四算法报告生成器，保留历史用途。',
 'make_progress_report.py': '修复长测报告历史生成器，含相对工作目录假设；不要覆盖阶段收尾报告。',
 'summarize_four_algorithms.py': '只读四组已存result.json，生成当前论文对比表及源文件SHA。',
 'finalize_scene4_stage.py': '本次阶段收尾、文档同步和可追溯工作区归档的一次性脚本。',
 'stage_progress.py': '将选定证据、补丁、报告归档到Git；重复归档保留不同原始字节。',
 'update_progress_docs.py': '历史报告入口同步工具，存在原工作目录假设。',
 'prepare_backup09.py': '上一轮09结果私有备份准备程序；冻结历史用途。',
 'private_backup09_api.py': '使用现有Git凭据在内存中核查仓库私有性、远端提交与保护引用。',
 'verify_remote_clone09.py': '独立远端克隆/快进后核验记录文件SHA和09原生地图解压SHA。',
 'verify_archive09.py': '上一轮09备份的历史内容/凭据模式核查；冻结原清单假设。',
 'verify_index09.py': '上一轮09备份索引字节与记录SHA核查；冻结原清单假设。',
 'finalize_backup09_metadata.py': '上一轮备份验收/暂停交接元数据生成；历史用途。',
 'normalize_reports09.py': '上一轮报告文字口径清理；历史用途。',
 'audit_live_07.py': '07运行的只读指令速度/动作记录器，固定07路径。',
 'refresh_live_07.py': '07运行进程与加载库指纹快照，固定07路径。',
 'audit_live_08.py': '08诊断运行的只读指令速度/动作记录器。',
 'refresh_live_08.py': '08诊断运行版本快照。',
 'audit_passive_09_attached.py': '09后附加的只读速度/动作记录器；仅覆盖附加后的采样。',
 'prepare_passive_attachment_09.py': '生成09后附加审计脚本的历史准备程序。',
 'prepare_formal_09.py': '09固定名称运行的历史准备程序；不得直接重用旧运行名。',
 'run_formal_09.sh': '09固定名称运行的历史入口；不得直接重用旧运行名。',
 'prepare_diagnostic_08.py': '08日志诊断与固定名称运行准备。',
 'run_diagnostic_08.sh': '08固定名称日志诊断入口，历史用途。',
 'benchmark_diagnostic08.py': '08只加诊断日志的测试器副本，不是新算法正式重复。',
 'supervise_diagnostic_08.py': '08诊断监督器和归属清理。',
 'summarize_diagnostic_08.py': '解析08本地选路日志，统计无有效前沿却获选的路径。',
 'save_poststop_map_07.py': '07收尾地图尝试；服务已关闭错误留存，不代表保存成功。',
 'prepare_stagnation_probe_09.py': '为09最终原生地图生成48组离线收益查询。',
 'gbp_stagnation_probe_09.cpp': '09冻结原生地图查询程序；研究残余三维收益与平面增量分离。',
 'run_stagnation_probe_09.sh': '09离线原生地图查询入口，临时11312服务；不是新长测。',
 'summarize_stagnation_probe_09.py': '汇总48次只读查询，不将查询分布当作唯一因果结论。',
 'gbp_gain_probe.cpp': 'GBP2原生收益和感知射线诊断程序。',
 'prepare_gbp_gain_probe.py': '准备原生收益查询位置与上下文。',
 'run_gbp_gain_probe.sh': '编译/执行原生收益诊断。',
 'ground_map_probe.cpp': '地面感知高度与地图上下文查询程序。',
 'prepare_ground_map_probe.py': '准备地面高度诊断位置与原生函数。',
 'run_ground_map_probe.sh': '编译/执行地面地图诊断。',
 'adaptive_bound_probe.cpp': '自适应边界历史诊断程序；不表示正式试验已采用新边界。',
 'run_adaptive_bound_probe.sh': '编译/执行自适应边界历史诊断。',
 'ufo_probe.cpp': 'FAEL UFOMap前沿/占据状态诊断。',
 'offline_rrg_probe.py': '离线RRG图/原生地图诊断。',
 'run_offline_rrg_probe.sh': '离线RRG诊断入口。',
 'probe_gbp_map.py': 'GBP2地图状态只读诊断。',
 'probe_gbp_tf.py': 'GBP2 TF/感知坐标链只读诊断。',
 'probe_obstacles.py': '障碍与运动环境只读诊断。',
 'probe_stall.py': '停滞时原生前沿/候选/路径只读诊断。',
 'record_gbp_frontiers.py': '06原生前沿记录器，固定运行目录；历史用途。',
 'record_linkage.py': '记录原生库及控制链加载路径/指纹。',
 'stop_gbp_cache_diagnostic.py': '历史射线缓存诊断结束及归属清理，不是日常停止入口。',
 'instrument_gbp2.py': '历史GBP2原生耗时采样插桩。',
 'gbp_debug.py': '历史GBP2原生日志插桩。',
}

def category(name):
    if any(s in name for s in ('backup', 'archive', 'index', 'remote', 'stage_', 'normalize', 'update_')):
        return '备份与历史归档'
    if any(s in name for s in ('report', 'plot', 'analyze', 'summarize')):
        return '数据分析与报告'
    if any(s in name for s in ('regression', 'validate', 'freeze')):
        return '验证与回归'
    if any(s in name for s in ('probe', 'audit', 'diagnostic', 'record', 'debug', 'instrument', 'refresh')):
        return '诊断与采样'
    if any(s in name for s in ('repair', 'frontier')):
        return '源码修复与回滚'
    if any(s in name for s in ('build', 'clone', 'prepare')):
        return '构建与准备'
    return '测试入口与协议'

def purpose(path):
    if path.name in descriptions:
        return descriptions[path.name]
    if path.suffix == '.json':
        return '机器可读配置/指纹记录；字段含义以文件内容和协议为准。'
    return '保留的历史辅助文件；按文件名对应原部署/测试阶段，使用前阅读源码与STATUS，勿批量执行。'

entries = sorted((p for p in (REPO / 'benchmarks').iterdir() if p.is_file()), key=lambda p: (category(p.name), p.name))
index = '# benchmarks文件用途索引\n\n当前状态：Scene4阶段性完成，GBP2暂停。文件按用途导航，部署路径保持稳定。固定07/08/09名称的脚本仅供历史复核，不可直接复用旧目录。\n\n'
index += '| 文件 | 分类 | 作用/使用边界 |\n|---|---|---|\n'
for path in entries:
    index += f'| [{path.name}]({path.name}) | {category(path.name)} | {purpose(path)} |\n'
index += '\n子目录：config为运行配置；patches为初期集成补丁；trial_repairs为契约/配置修复快照；progress_repairs为FAEL/GBP2原生修复前后源码与补丁；reporting为本次只读汇总工具；maintenance为本次归档/验证工具。\n'
write(REPO / 'benchmarks/FILE_INDEX.md', index)
write(ROOT / 'benchmarks/FILE_INDEX.md', index)

guide = '''# 代码目录与文件用途

当前Scene4四算法工程基线已阶段性完成；GBP2后续测试暂停。目录整理未改算法、原生编译副本、运行参数、公共协议或任何原始结果。

## 从哪里开始

1. 先读project-context/STATUS.md和RUNBOOK.md；本机对应D:/STGPlanner/codex/STATUS.md和RUNBOOK.md。
2. 最新结论看[四算法论文对比表](Scene4四算法与论文对比汇总.html)，详细故障证据看[修复长测报告](Scene4探索停滞修复报告.html)。
3. 找程序看[benchmarks逐文件索引](../benchmarks/FILE_INDEX.md)和下表；不要把历史prepare/run脚本批量执行。

## 各目录的职责

| 目录 | 作用 | 修改/使用原则 |
|---|---|---|
| stgp_planner/exploration_manager | STGPlanner探索流程及ROS协调 | 算法源码；本轮未修改 |
| stgp_planner/planner | STGPlanner核心规划 | 算法源码；本轮未修改 |
| stgp_planner/control_planner_interface | 规划/车辆控制接口 | 与公共执行契约配合 |
| stgp_planner/robot_move | 运动、局部规划与跟踪等车辆模块 | 四算法共用执行链配置见movement.launch |
| stgp_planner/sensor_conversion、visualization_tools | 传感器转换与可视化 | 接口/显示工具 |
| 3rdparty | 项目第三方源码/依赖 | 保留上游与许可 |
| files | 上游场景/工程资源 | 非测试结果目录 |
| deployment/scripts、deployment/windows | 主项目部署、构建、启停及历史验收工具 | 本机安装副本分别在D:/STGPlanner/scripts及项目根启动脚本 |
| benchmarks/config | 四算法launch/yaml、公共运动和观察器配置 | 不因整理修改配置 |
| benchmarks/*.py、*.sh、*.ps1、*.cpp | 已部署接口稳定的测试、修复、诊断和报告脚本 | 原路径保留；具体用途见FILE_INDEX.md |
| benchmarks/progress_repairs | FAEL/GBP2修复前后原生源码、patch、构建指纹 | .before/.after/.patch是可追溯证据，不是三份待编译工程 |
| benchmarks/trial_repairs、patches | 早期契约修复/参数快照及集成补丁 | 与progress_repairs分开，避免误用版本 |
| benchmarks/reporting | 当前只读四算法汇总生成器 | 读取已有result.json，不启动仿真 |
| benchmarks/maintenance | 本轮文档收尾及归档/验证脚本 | 一次性维护工具，不是测试入口 |
| evidence/scene4-final | 最初STGPlanner部署验证 | 原始历史证据 |
| evidence/scene4-baselines | 修复前四算法正式基线 | 旧FAEL/GBP2失败不覆盖 |
| evidence/scene4-progress-fix | 修复后运行、诊断、地图、SHA与协议验收 | 06中止、08诊断、07/09限时分开 |
| docs | 交付报告、图、最新四算法表与本说明 | 当前入口；历史内容有明确标识 |
| project-context | 最新状态、恢复清单、仿真锁及本轮备份验证 | 接手先读这里 |
| project-context/history | 收尾前交接/报告/清单快照 | 历史，不作为运行指令 |
| project-context/work-archive | 本机一次性工作文件的分类保留副本及移动清单 | 备查，默认不运行 |

## Windows、Git、WSL三层的关系

- D:/STGPlanner是部署总目录；实际Git根是D:/STGPlanner/catkin_ws/src/STGPlanner。
- D:/STGPlanner/benchmarks保存已部署工具、锁定上游sources、logs和results；仓库benchmarks保存可恢复的工具/配置，原始证据选取归档到evidence。
- 真正编译的FAEL、GBP2源码在STGPlanner-Ubuntu20的/opt/stgplanner/benchmarks/*_ws/src，库在对应devel中。D盘sources是上游克隆；修改它或只切Git分支不会自动更新已运行库。
- codex/work保存维护工作稿，codex/outputs保存最终交付。仍被部署脚本引用、依赖相对目录的工作文件保留原路径；无这些依赖的一次性文件移入archive/2026-10-27-scene4，逐项记录旧路径、新路径及SHA。
- archive内的脚本可能带旧机器绝对路径、固定试验名或原工作目录假设，仅作历史复核。确需重放时按移动清单恢复到原路径或在独立副本调整路径，且须先明确授权恢复测试；不能直接重用原试验目录。

## 常用文件如何区分

| 文件/组 | 作用 |
|---|---|
| run_benchmark.sh → benchmark_trial.py | 单次测试入口及公共指标/健康/停车验收 |
| run_formal_trial.py、cleanup_trial_runtime.py、run_outcome.py | 监督运行、按归属清理进程、准确分类结束原因 |
| benchmark_coverage.cpp、benchmark_cloud_bridge.cpp | 公共面积观察器、点云接口适配 |
| config/movement.launch | 四方法共享FALCO执行链，运行maxSpeed=2.0m/s |
| config/stgp/tare/fael/gbp2.launch及各yaml | 每种原生算法接口和参数；以运行冻结配置为准 |
| sources.lock.json、progress_trials.json | 上游版本锁定、预选结果目录 |
| apply_progress_repairs.py、path_frontier_repair.py、rollback_progress_repairs.py | 已保留源码修复与回滚 |
| *_regression.*、validate_*.py | 受控逻辑/协议核查，不能代替95%探索验证 |
| prepare_formal_09.py、run_formal_09.sh、*diagnostic*08* | 固定历史运行的准备和执行入口，禁止原名重跑 |
| *probe*、audit_*、record_* | 原生地图、前沿、感知、速度/动作等诊断；有些固定运行目录 |
| analyze_progress.py、plot_progress.py、make_progress_report.py | 历史修复对照分析与图/报告生成，重跑会影响交付，先审阅源码 |
| reporting/summarize_four_algorithms.py | 当前四算法论文表唯一生成入口，只读取四组已有结果 |
| *backup09*、verify_*09.py | 上一轮私有备份过程工具，历史假设冻结；本轮验收另有独立记录 |
| maintenance/verify_scene4_stage.py | 本轮原始证据、表格、归档字节与交接一致性检查，不运行ROS |

本次没有删除历史脚本、基线、失败/中止数据；没有移动Catkin源码、原生库或已部署入口。完整整理移动清单见project-context/work-archive/move_manifest.json。
'''
write(OUT / '代码目录说明.md', guide.replace('(../benchmarks/FILE_INDEX.md)', '(../../benchmarks/FILE_INDEX.md)'))
work_readme = '''# 工作脚本导航

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
'''
write(WORK / 'README.md', work_readme)
write(ROOT / 'README.md', '# STGPlanner本机项目入口\n\nScene4四算法基线测试已阶段性完成，GBP2暂停。\n\n- [当前状态](codex/STATUS.md) / [恢复与交接](codex/RUNBOOK.md)\n- [最新四算法论文对比](codex/outputs/Scene4四算法与论文对比汇总.html)\n- [代码目录与文件用途](codex/outputs/代码目录说明.html)\n- 实际Git仓库：catkin_ws/src/STGPlanner；本目录不执行git init。\n')

stage = {
 'updated_at': NOW, 'stage': 'Scene4四算法工程基线测试', 'status': 'stage_complete',
 'scope': '四方法部署、公共协议单次正式观测、必要修复验证、论文对照、证据归档和交接；不是论文五次统计复现',
 'gbp2_followup': 'paused_by_user', 'new_simulation_started': False,
 'stgp': {'trial': 'formal_stgp_01', 'reached_95': True},
 'tare': {'trial': 'formal_tare_01', 'reached_95': True, 'time_difference_from_paper_mean_percent': 25.40},
 'fael': {'trial': 'repair_formal_fael_01', 'reached_95': True},
 'gbp2': {'trial': 'repair_formal_gbp2_09', 'reached_95': False, 'coverage_percent': 56.338896,
          'sim_time_s': 2400.007, 'finish_reason': 'sim_time_limit'},
 'open_issues': ['GBP2后期平面覆盖停滞未解决；三维残余收益与平面增量分离仅为诊断线索，未证明唯一根因',
                 'TARE单次时间比论文均值高25.40%，尚不能据此判定代码故障',
                 '同条件五次均值/Std及其他场景不在本次阶段完成范围'],
 'directory_cleanup': {'moved_files': len(moves), 'original_bytes_preserved': True,
                       'deployed_paths_preserved': True, 'raw_results_unchanged': True},
 'backup_branch': 'fix/fael-gbp2-progress', 'previous_backup_commit': BASE,
 'backup_verification': '本轮远端提交及恢复核验见SCENE4_STAGE_BACKUP_VERIFIED.json；未生成前不得视为本轮推送已验收'
}
dump(ROOT / 'codex/SCENE4_STAGE_COMPLETION.json', stage)
status_path = ROOT / 'codex/STATUS.md'
status = status_path.read_text(encoding='utf-8')
status = re.sub(r'更新时间：[^。]+。', '更新时间：' + NOW + '。', status, count=1)
status = status.replace('## 当前状态：用户暂停GBP2后续测试，整理已完成结果并备份私有仓库',
                        '## 当前状态：Scene4四算法基线测试阶段性完成；GBP2后续测试暂停')
status = status.replace('此新增汇总当前为本地文件，上一轮私有备份ac6927e保留不变。',
                        '本次已纳入阶段收尾报告及私有分支备份范围；本轮推送验收见独立记录，上一轮ac6927e记录作为历史保留。')
status += ('\n## Scene4基线测试阶段性完成（最新授权收尾）\n\n' + notice +
           '完成范围：四算法Scene4部署及单次工程测试、必要修复验证、论文单表对照、原始数据/代码保留、报告和交接。'
           'STGPlanner及修复FAEL的时间/路径接近论文均值；TARE成功但时间高25.40%、路径高9.23%，不能笼统称三者所有指标都相近。'
           'GBP2限时失败是本阶段有效结果，不再以其未修复阻止基线阶段关闭。尚未完成论文同条件五次统计及其他场景。\n\n' +
           table + '\n\n' + cautions + '\n\n' +
           f'目录整理：{len(moves)}个无部署依赖的一次性文件归类迁移并逐项SHA核对；已部署入口、算法源码、配置、原始结果均未移动或修改。'
           '汇总工具位于codex/work/reporting；旧工作稿在codex/work/archive/2026-10-27-scene4；完整用途见codex/outputs/代码目录说明.md及benchmarks/FILE_INDEX.md。\n\n'
           '本轮验证：只读核对四组原始结果与对比表、原始证据SHA、迁移前后字节和交接/暂停状态；不运行ROS或重编译。'
           '未解决事项：GBP2后期覆盖停滞，收益/平面增长一致性待以后明确授权研究；STGPlanner/TARE/修复FAEL暂无已证实阻止本次探索的未修复故障，不代表代码无缺陷。'
           '后续：默认维持暂停和阶段完成；仅在用户明确授权新范围后另开新名试验。\n\n'
           '本轮备份：沿用fix/fael-gbp2-progress，保留main和两个历史基线引用。内容提交SHA及远端恢复验收见SCENE4_STAGE_BACKUP_VERIFIED.json；'
           '本轮不新建“全部问题修复”标签。先前ac6927e/522项验收仅为上一轮记录。\n')
write(status_path, status)
runbook = ROOT / 'codex/RUNBOOK.md'
text = runbook.read_text(encoding='utf-8')
text = text.replace('> 当前用户已暂停GBP2后续测试。本次仅整理FAEL成功/GBP2未达95%的结果并备份；以下启动命令只是用户未来明确恢复后的参考，不自动执行。',
                    '> Scene4四算法基线测试已阶段性完成；GBP2后续测试保持用户暂停。当前只维护报告/归档；下列启动命令仅为未来明确恢复后的参考，不自动执行。')
text += '\n## 阶段完成后的交接入口\n\n先读SCENE4_STAGE_COMPLETION.json、STATUS.md最新阶段结论，再看四算法论文对比汇总和代码目录说明。STGPlanner/TARE/修复FAEL达95%，GBP2修复09限时56.338896%。TARE时间比论文均值高25.40%；不将所有成功方法称为所有指标接近。\n\n当前只读表格生成器：codex/work/reporting/summarize_four_algorithms.py（仓库副本benchmarks/reporting/）；逐文件说明benchmarks/FILE_INDEX.md；一次性工作文件已归档，旧路径映射和SHA见codex/work/archive/2026-10-27-scene4/move_manifest.json。已部署运行入口仍在原位置。不要重跑旧prepare_formal_09/run_formal_09、旧报告/备份生成器。\n\n本阶段完成不等于全部代码问题修复或论文多次统计复现。GBP2剩余问题已登记但无自动续跑；未来恢复须明确授权、检查仿真锁与实际进程并使用全新结果目录。私有备份核验见SCENE4_STAGE_BACKUP_VERIFIED.json。\n'
write(runbook, text)
lock_path = ROOT / 'codex/SIMULATION_LOCK.json'
lock = json.loads(lock_path.read_text(encoding='utf-8'))
lock.update(updated_at=NOW, phase='scene4_baseline_stage_complete_gbp2_paused', stage_status='stage_complete',
            note='Scene4 baseline stage complete; GBP2 follow-up paused by user. Documentation/archive maintenance only; no simulation started or scheduled.')
dump(lock_path, lock)
for path in [ROOT / 'AGENTS.md', REPO / 'AGENTS.md']:
    text = path.read_text(encoding='utf-8')
    text = text.replace('用户已暂停GBP2后续测试，当前仅整理结果与备份；', 'Scene4四算法基线测试已阶段性完成，用户已暂停GBP2后续测试；')
    write(path, text)

readme = (REPO / 'README.md').read_text(encoding='utf-8')
readme = readme.replace('- 只完成 Scene4 功能复现；其他论文场景、基线方法和同配置五轮统计尚未复现。',
                         '- Scene4四算法工程基线已阶段性完成；其他论文场景和同配置五轮统计尚未复现。')
readme = readme.replace('## Scene4 多算法本机对比（2026-10-27）', '## Scene4 多算法本机对比（历史：修复前，2026-10-27）')
readme = readme.replace('最终标签和远程发布验收尚未完成，原main和两个历史基线标签保留。',
                         '上一轮私有备份ac6927e已验收；本次阶段收尾的备份核验另见project-context/SCENE4_STAGE_BACKUP_VERIFIED.json。原main和两个历史基线标签保留。')
first, rest = readme.split('\n', 1)
readme_block = block.replace('](Scene4', '](docs/Scene4').replace('](代码目录', '](docs/代码目录')
readme_block = readme_block.replace('下方保留原报告及历史测试过程。', '下方保留工程说明及修复前历史结果；当前入口见[文件用途索引](benchmarks/FILE_INDEX.md)与[阶段交接](project-context/STATUS.md)。')
write(REPO / 'README.md', first + '\n\n' + readme_block + rest.lstrip())

# Render all changed deliverables as standalone HTML and copy only current outputs.
stems = report_names + ['Scene4四算法与论文对比汇总', '代码目录说明']
for stem in stems:
    subprocess.run(['pandoc', str(OUT / (stem + '.md')), '--standalone', '--embed-resources',
                    '--metadata', 'title=' + stem, '--css', str(OUT / 'scene4_table_style.css'),
                    '-o', str(OUT / (stem + '.html'))], check=True, cwd=str(OUT))
    for suffix in ('.md', '.html'):
        shutil.copy2(OUT / (stem + suffix), REPO / 'docs' / (stem + suffix))
write(REPO / 'docs/代码目录说明.md', guide)
subprocess.run(['pandoc', str(REPO / 'docs/代码目录说明.md'), '--standalone', '--embed-resources',
                '--metadata', 'title=代码目录说明', '--css', str(OUT / 'scene4_table_style.css'),
                '-o', str(REPO / 'docs/代码目录说明.html')], check=True, cwd=str(REPO / 'docs'))
shutil.copy2(OUT / 'Scene4四算法与论文对比汇总.json', REPO / 'docs/Scene4四算法与论文对比汇总.json')
shutil.copy2(OUT / 'scene4_table_style.css', REPO / 'docs/scene4_table_style.css')
for src, dst in [('STATUS.md', 'STATUS.md'), ('RUNBOOK.md', 'RUNBOOK.md'),
                 ('SIMULATION_LOCK.json', 'SIMULATION_LOCK.json'), ('SCENE4_STAGE_COMPLETION.json', 'SCENE4_STAGE_COMPLETION.json')]:
    shutil.copy2(ROOT / 'codex' / src, REPO / 'project-context' / dst)
shutil.copytree(archive, REPO / 'project-context/work-archive', dirs_exist_ok=True)
shutil.copy2(WORK / 'README.md', REPO / 'project-context/WORKSPACE_README.md')
for folder in ['reporting', 'maintenance']:
    shutil.copytree(WORK / folder, REPO / 'benchmarks' / folder, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__'))

# Update the current manifest for changed report bytes, keeping the old manifest
# and all overwritten historical report texts in a separate traceable snapshot.
new_files = {name: sha(REPO / name) for name in old_manifest['files']}
for parent in [REPO / 'docs', REPO / 'project-context', REPO / 'benchmarks/reporting', REPO / 'benchmarks/maintenance']:
    for path in parent.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            new_files[path.relative_to(REPO).as_posix()] = sha(path)
for name in ['README.md', 'AGENTS.md', 'benchmarks/FILE_INDEX.md']:
    new_files[name] = sha(REPO / name)
dump(manifest_path, {'generated_at': NOW, 'previous_snapshot_commit': BASE,
     'previous_manifest': 'project-context/history/scene4-stage-before-closure/evidence/scene4-progress-fix/evidence_manifest.json',
     'raw_evidence_policy': 'Original scene4-final/baselines/progress-fix run evidence unchanged; report/context hashes refreshed only.',
     'files': dict(sorted(new_files.items()))})

dump(OUT / 'Scene4阶段收尾本地整理.json', {'updated_at': NOW, 'stage_status': 'stage_complete',
     'moved_file_count': len(moves), 'kept_root_work_files': len(keep),
     'manifest_files': len(new_files), 'GBP2_followup': 'paused_by_user', 'new_simulation_started': False})
print(json.dumps({'moved_files': len(moves), 'retained_work_files': len(keep), 'manifest_files': len(new_files),
                  'stage': 'stage_complete', 'GBP2': 'paused_by_user'}, ensure_ascii=False))
