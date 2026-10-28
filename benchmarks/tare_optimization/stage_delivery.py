"""Archive completed TARE follow-up and update current handoff; preserve all raw runs."""
import datetime
import gzip
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

root = Path('D:/STGPlanner')
repo = root / 'catkin_ws/src/STGPlanner'
out = root / 'codex/outputs'
work = out / 'tare_optimization_20261028'
sources = root / 'codex/work/tare_optimization'
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
summary = json.loads((work / 'summary.json').read_text(encoding='utf-8'))
validation = json.loads((work / 'validation.json').read_text(encoding='utf-8'))
assert validation['all_checks_passed']
deployment = json.loads((work / 'deployment_state.json').read_text(encoding='utf-8'))
assert not json.loads((root / 'codex/SIMULATION_LOCK.json').read_text(encoding='utf-8'))['runtime_active']
assert subprocess.check_output(['git','-C',str(repo),'branch','--show-current'],text=True).strip()=='fix/fael-gbp2-progress'
assert not subprocess.check_output(['git','-C',str(repo),'status','--porcelain']).strip()
history = repo / 'project-context/history/scene4-before-tare-20261028'
assert not history.exists()
history.mkdir(parents=True)
for name in ['README.md', 'project-context/STATUS.md', 'project-context/RUNBOOK.md', 'project-context/SIMULATION_LOCK.json',
             'evidence/scene4-progress-fix/evidence_manifest.json', 'benchmarks/FILE_INDEX.md']:
    destination = history / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo/name, destination)

evidence = repo / 'evidence/tare-optimization-20261028'
assert not evidence.exists()
evidence.mkdir()
archived = []

def save(source, target, compress=False):
    assert not target.exists(), target
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = source.read_bytes()
    target.write_bytes(gzip.compress(raw, mtime=0) if compress else raw)
    archived.append({'source':str(source), 'archive':target.relative_to(repo).as_posix(),
                     'source_sha256':hashlib.sha256(raw).hexdigest(), 'archive_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                     'gzip':compress})

for record in summary['records'][1:]:
    folder = root / 'benchmarks/results' / record['trial']
    for path in folder.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            relative = path.relative_to(folder)
            compress = path.stat().st_size>65536 or path.suffix.lower() in ['.log','.jsonl','.csv']
            target = evidence / record['trial'] / (relative.as_posix()+('.gz' if compress else ''))
            save(path,target,compress)
for path in work.rglob('*'):
    if path.is_file() and '__pycache__' not in path.parts:
        relative = path.relative_to(work)
        compress = path.stat().st_size>65536 and path.suffix.lower() not in ['.png','.gz']
        save(path,evidence/'analysis'/(relative.as_posix()+('.gz' if compress else '')),compress)
(evidence/'manifest.json').write_text(json.dumps({'generated_at':now,'files':archived,'raw_runs_preserved_in_place':True,
    'old_baseline_result_sha256':summary['records'][0]['result_sha256']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
tools = repo / 'benchmarks/tare_optimization'
shutil.copytree(sources,tools,ignore=shutil.ignore_patterns('__pycache__'))
shutil.copytree(work/'sensor_model_proposal', tools/'native_repairs', ignore=shutil.ignore_patterns('tare_planner_node.*'))
(tools/'native_repairs/README.md').write_text('# TARE感知模型实验快照\n\n本目录保存实际试验的before/after/patch。APPLIED.json表示历史上曾应用，不表示当前部署。当前部署以project-context/TARE_DEPLOYMENT_STATE.json为准；本轮性能未证实改善，候选不作为默认性能优化采用。精确原/候选二进制另保存在evidence/tare-optimization-20261028/analysis的压缩证据中。\n',encoding='utf-8',newline='\n')
license_path=root/'benchmarks/sources/tare_planner/LICENSE'
if license_path.exists():shutil.copy2(license_path,tools/'native_repairs/UPSTREAM_LICENSE')
assets = repo/'docs/tare_optimization_20261028'
assets.mkdir()
shutil.copy2(work/'tare_optimization_curves.png',assets/'tare_optimization_curves.png')
for suffix in ['.md','.html']:shutil.copy2(out/('TARE优化测试报告'+suffix),repo/'docs'/('TARE优化测试报告'+suffix))

headline='## 当前状态：TARE后续优化验证已完成；GBP2继续暂停'
status=root/'codex/STATUS.md'
text=status.read_text(encoding='utf-8')
text=re.sub(r'更新时间：[^。]+。','更新时间：'+now+'。',text,count=1)
text=re.sub(r'## 当前状态：[^\n]+',headline,text,count=1)
text+='\n## TARE优化后续最终结论（2026-10-28）\n\n'+summary['decision_text']+'\n\n'
for record in summary['records']:
    d=record['result']
    text+=f"- {record['trial']}：{d['sim_time_s']:.3f}s、{d['distance_m']:.3f}m、{d['coverage_fraction']*100:.4f}%，{d['finish_reason']}。\n"
text+='\n旧原配置1277.279s偏差不是稳定结果，新原配置未改算法已996.477s；不能把这一改善归到候选修复名下。感知端点用例旧14/16、对齐16/16，功能差异确认；候选性能必须结合全部重复观测，不能宣称唯一根因或论文五次统计复现。\n\n'
text+='当前实际原生部署：'+summary['deployment']+'；精确源码/二进制SHA见codex/outputs/tare_optimization_20261028/deployment_state.json。全部新运行已清理所属进程，11311/11345核查空闲；没有活动长测，不安排自动续跑。GBP2继续暂停，FAEL结果未重跑。\n\n'
text+='新增报告codex/outputs/TARE优化测试报告.md/.html；工具codex/work/tare_optimization；Git工具归档benchmarks/tare_optimization，原始数据/诊断evidence/tare-optimization-20261028。旧基线/失败/中止数据及本轮三组新原始数据均未覆盖。既有四算法基线阶段完成仍成立，本轮后续已完成。私有备份核验记录见TARE_OPTIMIZATION_BACKUP_VERIFIED.json；生成前不冒称本轮远端已验收。\n'
status.write_text(text,encoding='utf-8',newline='\n')
runbook=root/'codex/RUNBOOK.md'
text=runbook.read_text(encoding='utf-8')
text=text.replace('2026-10-28用户另授权TARE优化测试，当前仅本会话控制；','2026-10-28用户另授权的TARE优化验证已完成，无活动测试；')
text+='\n## TARE后续优化已结束\n\n先读STATUS最新TARE结论和TARE优化测试报告。实际原生部署见deployment_state.json，不以D盘上游克隆推断。工具及各自作用见benchmarks/tare_optimization/README.md；原始候选和新原配置对照分开保留。原生感知模型修正与性能收益分开评价，不能将新原配置的改善归到修改名下。当前无活动长测；GBP2继续暂停。后续新实验必须明确范围、先检查锁/进程，并采用新结果名。\n'
runbook.write_text(text,encoding='utf-8',newline='\n')
lock_path=root/'codex/SIMULATION_LOCK.json'
lock=json.loads(lock_path.read_text(encoding='utf-8'))
lock.update(state='idle',runtime_active=False,native_build_active=False,phase='tare_optimization_complete_gbp2_paused',updated_at=now,
            tare_followup='complete',stage_status='Scene4_prior_baseline_complete_TARE_followup_complete',gbp2_followup='paused_by_user',native_tare_deployment=deployment['deployment'],
            note='TARE follow-up tests and cleanup complete; no simulation scheduled. GBP2 remains paused.')
lock_path.write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8',newline='\n')
for name in ['STATUS.md','RUNBOOK.md','SIMULATION_LOCK.json']:shutil.copy2(root/'codex'/name,repo/'project-context'/name)
for name,newname in [('summary.json','TARE_OPTIMIZATION_SUMMARY.json'),('validation.json','TARE_OPTIMIZATION_VERIFIED.json'),('deployment_state.json','TARE_DEPLOYMENT_STATE.json')]:shutil.copy2(work/name,repo/'project-context'/newname)
readme=repo/'README.md';text=readme.read_text(encoding='utf-8');first,rest=text.split('\n',1)
text=first+'\n\n> **2026-10-28 TARE后续已完成：** 新原配置996.477s/1490.842m已接近论文时间；旧单次偏差不代表稳定性能。'+summary['decision_text']+'详见[全部TARE优化测试](docs/TARE优化测试报告.md)及[当前部署](project-context/TARE_DEPLOYMENT_STATE.json)。GBP2继续暂停。\n\n'+rest.lstrip();readme.write_text(text,encoding='utf-8',newline='\n')
index=repo/'benchmarks/FILE_INDEX.md';index.write_text(index.read_text(encoding='utf-8')+'\n## TARE后续优化（2026-10-28）\n\n新增[tare_optimization/README.md](tare_optimization/README.md)，列明运行监督、只读诊断、感知模型补丁、实际原生回归、重建/恢复、报告/归档与验证工具的作用。当前真实部署以project-context/TARE_DEPLOYMENT_STATE.json为准。\n',encoding='utf-8',newline='\n')
attrs=repo/'.gitattributes';attrs.write_text(attrs.read_text(encoding='utf-8')+'\n/evidence/tare-optimization-20261028/** -text\n/evidence/tare-optimization-20261028/** whitespace=-blank-at-eol,-blank-at-eof\n/benchmarks/tare_optimization/native_repairs/** -text\n/benchmarks/tare_optimization/native_repairs/** whitespace=-blank-at-eol,-blank-at-eof\n',encoding='utf-8',newline='\n')
# Refresh only current documentation hashes in the previous phase's index;
# the exact prior index lives at the recorded pre-TARE checkpoint and history path.
path=repo/'evidence/scene4-progress-fix/evidence_manifest.json'
manifest=json.loads(path.read_text(encoding='utf-8'))
manifest['before_tare_snapshot_commit']='7a1b99e5042906097b7e60beaa98e2db6390e6f7'
manifest['before_tare_manifest']='project-context/history/scene4-before-tare-20261028/evidence/scene4-progress-fix/evidence_manifest.json'
for name in manifest['files']:manifest['files'][name]=hashlib.sha256((repo/name).read_bytes()).hexdigest()
path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'archived_files':len(archived),'stage':'TARE follow-up complete','deployment':deployment['deployment']},ensure_ascii=False))
