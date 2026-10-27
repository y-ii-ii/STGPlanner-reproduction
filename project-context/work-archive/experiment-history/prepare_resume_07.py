"""Verify the deployed runtime and freeze a new trial before launch; run in WSL."""
import datetime
import hashlib
import json
import shutil
import socket
import subprocess
from pathlib import Path

ROOT = Path('/mnt/d/STGPlanner')
BENCH = ROOT / 'benchmarks'
TRIAL = 'repair_formal_gbp2_07'
OWNER = '01a17c85-9d73-7573-885c-a95dbbc4abbf'
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

lock_path = ROOT / 'codex/SIMULATION_LOCK.json'
old_lock = json.loads(lock_path.read_text())
assert old_lock['state'] in ('paused_by_user', 'idle', 'paused'), old_lock
assert not (BENCH / 'results' / TRIAL).exists(), 'Trial already exists'
processes = subprocess.check_output(['ps', '-eo', 'pid,comm,args'], text=True)
bad = [line for line in processes.splitlines() if any(
    name in line.split()[1:2] for name in ('rosmaster', 'roslaunch', 'gzserver', 'gbplanner_node', 'topo_planner_no'))]
assert not bad, bad
for port in (11311, 11345):
    with socket.socket() as sock:
        assert sock.connect_ex(('127.0.0.1', port)) != 0, 'Port occupied: ' + str(port)

previous = BENCH / 'results/repair_formal_gbp2_06'
manifest = json.loads((previous / 'native_source_manifest.json').read_text())
checks = []
for row in manifest['sources']:
    path = Path('/opt/stgplanner/benchmarks') / (row['method'] + '_ws/src') / row['relative']
    actual = sha(path)
    assert actual == row['repaired_sha256'], str(path)
    checks.append({'path': str(path), 'sha256': actual, 'matches_trial_06': True})
for row in manifest['binaries'].values():
    path = Path(row['path'])
    actual = sha(path)
    assert actual == row['sha256'], str(path)
    checks.append({'path': str(path), 'sha256': actual, 'matches_trial_06': True})
adapter = json.loads((previous / 'adapter_config_manifest.json').read_text())
for relative, row in adapter['files'].items():
    path = ROOT / relative
    actual = sha(path)
    assert actual == row['repaired_sha256'], str(path)
    checks.append({'path': str(path), 'sha256': actual, 'matches_trial_06': True})

preflight = ROOT / 'codex/outputs' / ('preflight_' + TRIAL)
preflight.mkdir(exist_ok=False)
local = ROOT / 'catkin_ws/src/STGPlanner/stgp_planner/robot_move/cmu_planner/local_planner'
shared = ROOT / 'catkin_ws/src/STGPlanner/stgp_planner/robot_move/path_execution'
control_paths = [local / 'launch/local_planner.launch', local / 'src/localPlanner.cpp',
                 local / 'src/pathFollower.cpp', shared / 'src/path_execution.cpp',
                 BENCH / 'config/movement.launch', BENCH / 'config/terrain_static.launch',
                 BENCH / 'benchmark_trial.py', BENCH / 'config/gbp2.yaml']
control_paths += [Path('/opt/stgplanner/catkin_ws/devel/lib/local_planner') / name
                  for name in ('localPlanner', 'pathFollower')]
control_paths += [Path('/opt/stgplanner/catkin_ws/devel/lib/path_execution/path_execution_node')]
controls = [{'path': str(p), 'sha256': sha(p)} for p in control_paths]
selection = json.loads((BENCH / 'progress_trials.json').read_text())
selection['final_runs']['gbp2'] = TRIAL
selection['intermediate_runs'].append('repair_formal_gbp2_06')
selection['intermediate_labels'].append('Cluster frontier type repair (user interrupted at 1082.027s, 54.153530%)')
selection['selection_note'] = ('Trial 07 selected before its outcome, same source/binary/configuration as user-interrupted 06. '
    'Fresh initial conditions, 2400 simulation-second cap, unchanged common 95% threshold/protocol 3. '
    '06 remains user-interrupted evidence, not completion. Trials are engineering validation, not five paper repeats.')
selection['selected_at'] = now
for dest in (BENCH / 'progress_trials.json', ROOT / 'codex/work/progress_trials.json', preflight / 'progress_trials.json'):
    dest.write_text(json.dumps(selection, indent=2) + '\n')
for name in ('native_source_manifest.json', 'adapter_config_manifest.json'):
    shutil.copy2(previous / name, preflight / name)
shutil.copy2(BENCH / 'benchmark_trial.py', preflight / 'benchmark_trial.py')
shutil.copytree(BENCH / 'config', preflight / 'config')
audit = {'captured_at': now, 'trial': TRIAL, 'owner_thread': OWNER,
         'processes_before_launch': processes, 'ports_free': [11311, 11345],
         'runtime_matches_trial_06': checks, 'common_controller_files': controls,
         'common_protocol_revision': 3, 'common_threshold_m2': 7400.5,
         'paper_url': 'https://arxiv.org/html/2412.13664v4',
         'paper_audit': 'IV-A uses modified [25] FALCO and vmax=2m/s. Shared movement.launch includes common localPlanner/pathFollower. Both clamp autonomySpeed/maxSpeed to [0,1]. Native GBP2 v_max=2 and v_homing_max=1 are time models, not actuator speed. Trial 05 already used them and failed at 41.4049%; calibration alone did not solve stagnation. Adapter executes native path via common vehicle action and honors homing status 2 once. Public author baseline adapters remain unverified; this is engineering validation.'}
(preflight / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
lock_path.write_text(json.dumps({'state': 'running', 'owner_thread': OWNER, 'trial': TRIAL,
    'updated_at': now, 'runtime_active': False, 'phase': 'preflight_complete',
    'note': 'User explicitly resumed in report chat; algorithm chat exclusively controls WSL/ROS/Gazebo and code/status. Runtime verified idle; fresh trial launch next.',
    'preflight': str(preflight)}, indent=2) + '\n')
status_path = ROOT / 'codex/STATUS.md'
status = status_path.read_text()
begin = status.index('## 当前状态：')
end = status.index('## 目录和版本')
status = status[:begin] + '''## 当前状态：用户已明确恢复，GBP2 07启动前核验完成

2026-10-27 用户在“STGPlanner 报告与论文对照”明确授权解除暂停、自主继续测试，由算法与长测会话 01a17c85-9d73-7573-885c-a95dbbc4abbf 独占 WSL/ROS/Gazebo、共享代码和 STATUS/SIMULATION_LOCK 写入。报告会话只读审计。
Git工作区干净，分支fix/fael-gbp2-progress，HEAD 59eba6c。
实际进程及11311/11345端口无占用；专用WSL仅为核验启动。07将从相同初始条件开始，2400仿真秒上限，公共协议3和95%阈值不变；已在结果产生前固定progress_trials.json。
原生9个源码、3个库和适配器/配置SHA均与06归档吻合，无需重编译。证据：codex/outputs/preflight_repair_formal_gbp2_07/audit.json。尚未有07结果。

- 第六轮repair_formal_gbp2_06：1082.027仿真秒，54.153530%，4218.56m²，1179.247m，用户中止，未完成95%；全部原始数据保留，不原地续算。
- FAEL repair_formal_fael_01已达95.3366%，本次不因迁移重复运行。
- 论文v4 IV-A统一修改版[25] FALCO、上限2m/s；部署四方法共用movement.launch→path_execution/localPlanner/pathFollower。autonomySpeed=3经joySpeed截断后乘maxSpeed=2，不能解释为3m/s。运行时参数和进程二进制待07启动后存证。
- GBP2原生v_max=2/v_homing_max=1属于时间预算模型，与低层控制上限分开；05完整2400秒仍41.4049%，不支持“仅速度校准解决41%”的说法。适配器将原生全局路径转为公共动作并仅执行一次返航；作者各基线适配代码尚未核实。
- 本轮保持06设置以验证完整表现，不能独立归因聚类修复，也不是论文五次统计复现。最终标签、报告、ZIP/bundle均未发布。

''' + status[end:]
status_path.write_text(status)
print(json.dumps({'trial': TRIAL, 'preflight': str(preflight), 'matched_runtime_files': len(checks),
                  'controller_files': len(controls), 'ports_free': True}))
