"""After diagnostic08 has stopped, apply a scoped repair and freeze formal09."""
import datetime
import hashlib
import json
import re
import shutil
import socket
import subprocess
from pathlib import Path
from path_frontier_repair import repair_local_frontier_selection

root=Path('/mnt/d/STGPlanner'); bench=root/'benchmarks'; trial='repair_formal_gbp2_09'
preflight=root/'codex/outputs'/('preflight_'+trial)
lock_path=root/'codex/SIMULATION_LOCK.json'; lock=json.loads(lock_path.read_text())
assert lock['owner_thread']=='01a17c85-9d73-7573-885c-a95dbbc4abbf'
assert lock['state']=='idle' and not lock['runtime_active'], lock
diagnostic=bench/'results/diagnostic_gbp2_gain_08'
assert (diagnostic/'result.json').exists(), 'Diagnostic must finish first'
for port in (11311,11345,11312):
    with socket.socket() as connection:assert connection.connect_ex(('127.0.0.1',port))!=0, f'Occupied port{port}'
assert not (bench/'results'/trial).exists()
preflight.mkdir(exist_ok=False)
setup=root/'codex/outputs/diagnostic_gbp2_gain_08_setup'
manifest08=json.loads((setup/'setup_manifest.json').read_text())
native=Path('/opt/stgplanner/benchmarks/gbp2_ws/src/gbplanner/src/rrg.cpp')
assert hashlib.sha256(native.read_bytes()).hexdigest()==manifest08['native_diagnostic_sha256']
shutil.copytree(bench/'progress_repairs',preflight/'baseline07_progress_repairs')
shutil.copy2(bench/'progress_report/progress_validation.json',preflight/'trial07_validation.json')
for name in ('apply_progress_repairs.py','path_frontier_repair.py'):
    shutil.copy2(root/'codex/work'/name,bench/name)
baseline=(setup/'rrg.cpp.before').read_text()
expected=repair_local_frontier_selection(baseline)
(preflight/'rrg.cpp.baseline07').write_text(baseline)
(preflight/'rrg.cpp.expected09').write_text(expected)
native.write_text(baseline)  # Remove the explicitly archived logging-only08 version.
lock.update(state='running',runtime_active=False,phase='building_formal09',trial=trial,
    updated_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
    note='Diagnostic08 stopped and ports verified free. Applying scoped local-frontier eligibility repair; public controller/threshold unchanged.')
lock_path.write_text(json.dumps(lock,indent=2)+'\n')
with (preflight/'build.log').open('x') as log:
    subprocess.run(['bash',str(bench/'build_progress_repairs.sh'),'gbp2'],stdout=log,stderr=subprocess.STDOUT,check=True)
assert native.read_text()==expected, 'Deployed source differs from reproducible repair'
with (preflight/'regression.log').open('x') as log:
    subprocess.run(['python3',str(root/'codex/work/test_path_frontier_selection.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
shutil.copy2(root/'codex/outputs/path_frontier_selection_regression/result.json',bench/'path_frontier_selection_regression.json')
subprocess.run(['python3',str(bench/'capture_progress_manifest.py')],stdout=(preflight/'manifest_capture.log').open('x'),check=True)
source_manifest=json.loads((bench/'progress_repairs/manifest.json').read_text())
shutil.copy2(bench/'progress_repairs/manifest.json',preflight/'native_source_manifest.json')
shutil.copy2(bench/'trial_repairs/manifest.json',preflight/'adapter_config_manifest.json')
shutil.copy2(bench/'benchmark_trial.py',preflight/'benchmark_trial.py')
shutil.copytree(bench/'config',preflight/'config')
shutil.copytree(bench/'progress_repairs',preflight/'progress_repairs')
prior=json.loads((root/'codex/outputs/preflight_repair_formal_gbp2_07/audit.json').read_text())
for entry in prior['common_controller_files']:
    assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest()==entry['sha256'], entry['path']
selection=json.loads((bench/'progress_trials.json').read_text())
assert selection['final_runs']['gbp2']=='repair_formal_gbp2_07'
selection['intermediate_runs'].append('repair_formal_gbp2_07')
selection['intermediate_labels'].append('Cluster type repair (2400s /54.96% failure)')
selection['plot_intermediate_runs'].append('repair_formal_gbp2_07')
selection['diagnostic_runs']=['diagnostic_gbp2_gain_08']
selection['final_runs']['gbp2']=trial
selection['selected_at']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
selection['selection_note']='Trial09 selected before outcome after diagnostic08 and six controlled path-eligibility checks. Only admissible paths containing a valid frontier may win local selection; inadmissible paths do not suppress native global fallback. Native configuration and public protocol3 /95% threshold/controller unchanged.07 is a preserved complete2400s failure,06 user-interrupted,08 diagnostic; none pooled as repetitions.'
for path in (bench/'progress_trials.json',root/'codex/work/progress_trials.json',preflight/'progress_trials.json'):
    path.write_text(json.dumps(selection,indent=2)+'\n')
audit={'trial':trial,'selected_at':selection['selected_at'],'common_controller_files':prior['common_controller_files'],
    'common_protocol_revision':3,'common_threshold_m2':7400.5,'algorithm_changes':['only admissible paths containing valid nonhanging frontiers compete for best local path','inadmissible frontier paths do not set frontier_exists','native selected-path diagnostics'],
    'parameter_changes':None,'public_protocol_changes':None,'diagnostic_evidence':'diagnostic_gbp2_gain_08','regression_checks':6,
    'native_source_manifest':source_manifest,'preserved_prior':'baseline07_progress_repairs/ and trial07_validation.json'}
(preflight/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
for original,name in (('audit_live_07.py','audit_live.py'),('refresh_live_07.py','refresh_live.py'),('save_poststop_map_07.py','save_poststop_map.py')):
    text=(root/'codex/work'/original).read_text().replace('repair_formal_gbp2_07',trial)
    (preflight/name).write_text(text)
lock.update(phase='preflight_complete',preflight=str(preflight),result_path=str(bench/'results'/trial),runtime_active=False)
lock_path.write_text(json.dumps(lock,indent=2)+'\n')
status_path=root/'codex/STATUS.md'; status=status_path.read_text()
status=re.sub(r'## 当前状态：[^\n]+','## 当前状态：GBP2 09修复已编译，准备正式完整验证',status,count=1)
status+='\n## 09启动前检查\n\n08诊断已结束并清理所属ROS/Gazebo，11311/11345/11312无占用。已根据实际无前沿选路记录及6项独立受控检查，修复局部路径前沿资格与不可通行路径的回退标志；未改公共控制器、95%门槛或GBP2原生参数。09已在结果产生前固定选择、源码/库与配置。07完整失败和06用户中止均保留。原07源码/补丁及验收另存preflight_repair_formal_gbp2_09，当前progress_repairs已更新为09版本，不能再用当前库冒称07运行库。\n'
status_path.write_text(status)
print(json.dumps({'trial':trial,'preflight':str(preflight),'ready':True}))
