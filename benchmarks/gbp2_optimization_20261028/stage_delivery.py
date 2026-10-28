"""Archive a closed GBP2 native-parameter phase without touching previous raw runs."""
import datetime
import gzip
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
root=Path('D:/STGPlanner');repo=root/'catkin_ws/src/STGPlanner'
out=root/'codex/outputs';work=out/'gbp2_optimization_20261028'
sources=root/'codex/work/gbp2_optimization_20261028'
summary=json.loads((work/'summary.json').read_text(encoding='utf-8'))
decision=summary['decision'];assert decision['phase_complete']
deployment=json.loads((work/'deployment_state.json').read_text(encoding='utf-8'))
lock_path=root/'codex/SIMULATION_LOCK.json';lock=json.loads(lock_path.read_text(encoding='utf-8'))
assert not lock['runtime_active'] and deployment['runtime_idle_verified']
git=['git','-c','core.quotepath=false','-C',str(repo)]
assert subprocess.check_output(git+['branch','--show-current'],text=True).strip()=='fix/fael-gbp2-progress'
dirty=subprocess.check_output(git+['status','--porcelain'],text=True).splitlines()
assert all(line[3:]=='AGENTS.md' for line in dirty),dirty
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
history=repo/'project-context/history/scene4-before-gbp2-optimization-20261028'
assert not history.exists();history.mkdir(parents=True)
for name in ['README.md','project-context/STATUS.md','project-context/RUNBOOK.md','project-context/SIMULATION_LOCK.json',
             'evidence/scene4-progress-fix/evidence_manifest.json','benchmarks/FILE_INDEX.md',
             'benchmarks/config/gbp2.yaml',
             'docs/代码目录说明.md','docs/代码目录说明.html',
             'docs/Scene4四算法与论文对比汇总.md','docs/Scene4四算法与论文对比汇总.html','docs/Scene4四算法与论文对比汇总.json']:
    if not (repo/name).exists():continue
    target=history/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/name,target)

evidence=repo/'evidence/gbp2-optimization-20261028';assert not evidence.exists();evidence.mkdir()
archived=[]
def save(source,target):
    assert not target.exists(),target
    raw=source.read_bytes()
    compress=(len(raw)>65536 or source.suffix.lower() in ['.log','.jsonl','.csv']) and source.suffix.lower() not in ['.png','.gz']
    target=target.with_name(target.name+'.gz') if compress else target
    assert not target.exists(),target
    target.parent.mkdir(parents=True,exist_ok=True)
    payload=gzip.compress(raw,mtime=0) if compress else raw
    target.write_bytes(payload)
    archived.append({'source':str(source),'archive':target.relative_to(repo).as_posix(),
        'source_sha256':hashlib.sha256(raw).hexdigest(),'archive_sha256':hashlib.sha256(payload).hexdigest(),'gzip':compress})
for record in summary['records']:
    folder=root/'benchmarks/results'/record['trial']
    for path in folder.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:save(path,evidence/record['trial']/path.relative_to(folder))
for path in work.rglob('*'):
    if path.is_file() and '__pycache__' not in path.parts:save(path,evidence/'analysis'/path.relative_to(work))
(evidence/'manifest.json').write_text(json.dumps({'generated_at':now,'files':archived,
    'raw_runs_preserved_in_place':True,'previous_checkpoint':'8c55a9aee073a292df78aeb2d8f82d8aa4e13593',
    'completed_trials':decision['completed_trials']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
tools=repo/'benchmarks/gbp2_optimization_20261028';assert not tools.exists()
shutil.copytree(sources,tools,ignore=shutil.ignore_patterns('__pycache__'))
assets=repo/'docs/gbp2_optimization_20261028';assets.mkdir()
for name in ['gbp2_frontier_curves.png','gbp2_frontier_maps.png']:shutil.copy2(work/name,assets/name)
(assets/'paper_review').mkdir()
shutil.copy2(work/'paper_review/paper_fig5d_scene4.png',assets/'paper_review/paper_fig5d_scene4.png')
for suffix in ['.md','.html']:shutil.copy2(out/('GBP2优化测试报告'+suffix),repo/'docs'/('GBP2优化测试报告'+suffix))
for name in ['Scene4四算法与论文对比汇总.md','Scene4四算法与论文对比汇总.html','Scene4四算法与论文对比汇总.json','代码目录说明.md','代码目录说明.html']:
    shutil.copy2(out/name,repo/'docs'/name)
shutil.copy2(root/'benchmarks/config/gbp2.yaml',repo/'benchmarks/config/gbp2.yaml')

# Canonical current summary first; the previous status is retained in history.
status=root/'codex/STATUS.md';previous_text=status.read_text(encoding='utf-8')
status_history=root/'codex/history/scene4-before-gbp2-phase-close-20261028.md'
status_history.parent.mkdir(exist_ok=True);assert not status_history.exists();status_history.write_text(previous_text,encoding='utf-8',newline='\n')
text='# STGPlanner 最新交接状态\n\n更新时间：'+now+'。本文件是当前恢复入口，旧阶段叙述已另存history。\n\n'
text+='## 当前状态：GBP2本轮原生参数优化阶段结束，无活动仿真\n\n'+decision['conclusion']+'\n\n'+decision['deployment_text']+'\n\n'
text+='Scene4四算法原基线阶段已完成；TARE后续已完成且恢复验证原版，FAEL成功数据保留、均未重跑。本阶段按用户最新3次上限结束，当前全部所属运行已清理，95%目标仍未达到；不再继续调参、重放或补测。新实验入口已硬拦截，限制见codex/GBP2_EXPERIMENT_LIMITS.json。\n\n'
text+='## 本阶段全部结果\n\n| 运行 | 前沿阈值 | 距地高度(m) | 观察(s) | 原生结束(s) | 覆盖 | 路程(m) | 公共95% |\n|---|---:|---:|---:|---:|---:|---:|---|\n'
for row in summary['records']:
    d=row['result'];end=d.get('native_finish_sim_s');end_text=f'{end:.3f}' if end is not None else '未结束'
    text+=f"| {row['trial']} | {row['threshold']:g} | {row['height']:g} | {d['sim_time_s']:.3f} | {end_text} | {d['coverage_fraction']*100:.6f}% | {d['distance_m']:.3f} | {'达到' if d['area_m2']>7400.5 else '未达到'} |\n"
text+='\n历史修复09：2400.007s、56.338896%、4388.80m²、2413.450m、未原生结束、sim_time_limit；06为用户中止，07/09完整失败，08为诊断，均不覆盖或混成重复。修复FAEL01：1017.008s、95.3365854%、1351.931m。\n\n'
text+='## 验证与剩余问题\n\n'+decision['interpretation']+'\n\n'+decision['next_step']+'\n\n'
text+='每轮保持公共95%/7790m²分母、12m、2m/s、采样2000、2400秒、独立新图。原生源码与两库均为工程修复09；原生提前返航、公共95%、完整限时、用户中止分别记录。报告不宣称论文五次统计复现。运行时URDF导出雷达距地0.5192m；TF点云/传感器原点差约0.3mm，不能混用原始Gazebo world与归一化world宣称TF错误。详细证据及所有失败见报告。\n\n'
text+='## 路径、版本与恢复\n\n- 实际Git根：D:/STGPlanner/catkin_ws/src/STGPlanner；私有库y-ii-ii/STGPlanner-reproduction，分支fix/fael-gbp2-progress。本阶段起点8c55a9a，最终HEAD以Git/远端验收为准；main及历史基线分支、两个标签保持不变。\n'
text+='- WSL：STGPlanner-Ubuntu20，真正原生源码/库在/opt/stgplanner/benchmarks/*_ws；修改D盘上游克隆不会更新二进制。当前部署SHA见codex/outputs/gbp2_optimization_20261028/deployment_state.json。\n'
text+='- 原始结果：D:/STGPlanner/benchmarks/results；当前工具：codex/work/gbp2_optimization_20261028/README.md；交付：codex/outputs/GBP2优化测试报告.md/.html及gbp2_optimization_20261028；Git副本为benchmarks/gbp2_optimization_20261028、evidence/gbp2-optimization-20261028。\n'
text+='- 旧状态：codex/history/scene4-before-gbp2-phase-close-20261028.md；Git中本阶段前状态在project-context/history/scene4-before-gbp2-optimization-20261028。更早原始聊天工作区路径保存在旧状态，不必读取整段历史聊天。\n'
text+='- 后续先读本文件、RUNBOOK、SIMULATION_LOCK并核对实际/proc和端口；只有一个会话控制WSL/ROS/Gazebo及共享Git写入。新测试用新目录，不重跑旧prepare、恢复、归档脚本。\n'
text+='- 本阶段私有备份以GBP2_OPTIMIZATION_BACKUP_VERIFIED.json为准；文件生成前不冒称远端已验收。此前TARE内容7944515、最终8c55a9a已验收；四算法阶段内容6fd0d05、最终7a1b99e已验收。\n'
status.write_text(text,encoding='utf-8',newline='\n')
runbook=root/'codex/RUNBOOK.md'
with runbook.open('a',encoding='utf-8',newline='\n') as handle:
    handle.write('\n## GBP2本轮原生参数优化阶段结束（最新）\n\n'+decision['conclusion']+'\n\n'+decision['deployment_text']+'\n\n当前无活动仿真；TARE/FAEL未重跑。当前工具统一在codex/work/gbp2_optimization_20261028，逐文件作用见README.md；实验方案v1/v2、原生快照、所有失败/候选、验证和部署指纹保留。先读最新STATUS，旧长测状态只作历史。后续先核对锁、实际进程和端口，使用新结果目录，不把原生结束或健康通过算作95%成功。私有备份验收见GBP2_OPTIMIZATION_BACKUP_VERIFIED.json。\n')
lock.update(state='idle',runtime_active=False,phase='gbp2_optimization_phase_complete',gbp2_followup='optimization_phase_complete',
            max_new_formal_trials=3,used_new_formal_trials=3,new_experiments_blocked=True,
            updated_at=now,native_gbp2_configuration=deployment['reference_trial'],note='User three-trial cap reached. No further simulation, probe, repeat or optimization authorized.')
lock_path.write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8',newline='\n')
for name in ['STATUS.md','RUNBOOK.md','SIMULATION_LOCK.json']:shutil.copy2(root/'codex'/name,repo/'project-context'/name)
shutil.copy2(root/'codex/GBP2_EXPERIMENT_LIMITS.json',repo/'project-context/GBP2_EXPERIMENT_LIMITS.json')
shutil.copy2(work/'summary.json',repo/'project-context/GBP2_OPTIMIZATION_SUMMARY.json')
shutil.copy2(work/'deployment_state.json',repo/'project-context/GBP2_DEPLOYMENT_STATE.json')
readme=repo/'README.md';first,rest=readme.read_text(encoding='utf-8').split('\n',1)
readme.write_text(first+'\n\n> **2026-10-28 GBP2后续阶段结束：** '+decision['conclusion']+' 详见[全部GBP2优化测试](docs/GBP2优化测试报告.md)和[当前原生部署](project-context/GBP2_DEPLOYMENT_STATE.json)。TARE保持验证原版，FAEL成功数据未重跑。\n\n'+rest.lstrip(),encoding='utf-8',newline='\n')
index=repo/'benchmarks/FILE_INDEX.md'
with index.open('a',encoding='utf-8',newline='\n') as handle:
    handle.write('\n## GBP2后续原生参数优化（2026-10-28）\n\n新增[gbp2_optimization_20261028/README.md](gbp2_optimization_20261028/README.md)，说明单参数部署、监督器、被动记录、冻结地图诊断、URDF几何校准、报告和私有备份工具。运行脚本不会证明探索成功；当前实际部署见project-context/GBP2_DEPLOYMENT_STATE.json。\n')
shutil.copy2(index,root/'benchmarks/FILE_INDEX.md')
attrs=repo/'.gitattributes'
with attrs.open('a',encoding='utf-8',newline='\n') as handle:
    handle.write('\n/evidence/gbp2-optimization-20261028/** -text\n/evidence/gbp2-optimization-20261028/** whitespace=-blank-at-eol,-blank-at-eof\n')
manifest_path=repo/'evidence/scene4-progress-fix/evidence_manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['before_gbp2_optimization_checkpoint']='8c55a9aee073a292df78aeb2d8f82d8aa4e13593'
manifest['before_gbp2_optimization_manifest']='project-context/history/scene4-before-gbp2-optimization-20261028/evidence/scene4-progress-fix/evidence_manifest.json'
for name in manifest['files']:manifest['files'][name]=hashlib.sha256((repo/name).read_bytes()).hexdigest()
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'archived_files':len(archived),'completed_trials':decision['completed_trials'],'deployment':deployment['reference_trial']},ensure_ascii=False))
