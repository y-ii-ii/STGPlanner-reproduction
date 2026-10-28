"""Record an independently restored content checkpoint; final metadata HEAD is separate."""
import datetime
import hashlib
import json
import shutil
from pathlib import Path
root=Path('D:/STGPlanner');repo=root/'catkin_ws/src/STGPlanner'
out=root/'codex/outputs/gbp2_optimization_20261028'
receipt=json.loads((out/'GBP2_OPTIMIZATION_BACKUP_VERIFIED.json').read_text(encoding='utf-8'))
assert receipt['private'] and receipt['verification']['all_checks_passed']
commit=receipt['remote_commit'];v=receipt['verification']
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
for target in [repo/'project-context/GBP2_OPTIMIZATION_BACKUP_VERIFIED.json',root/'codex/GBP2_OPTIMIZATION_BACKUP_VERIFIED.json']:
    shutil.copy2(out/'GBP2_OPTIMIZATION_BACKUP_VERIFIED.json',target)
message=(f"内容提交`{commit}`已推送到私有分支fix/fael-gbp2-progress，远端独立克隆恢复通过{v['new_archive_files']}项本阶段归档的压缩前后SHA、此前{v['previous_manifest_files']}项索引及{v['prior_tare_archive_files']}项TARE归档、{v['experiment_checks']}项实验检查。旧原始证据不变，main、历史基线分支和两个标签保留。验收记录指向内容提交；随后交接元数据提交的最终HEAD以Git和GBP2_OPTIMIZATION_FINAL_HEAD_VERIFIED.json为准。当前无活动仿真，TARE/FAEL未重跑。")
for name in ['STATUS.md','RUNBOOK.md']:
    path=root/'codex'/name
    with path.open('a',encoding='utf-8',newline='\n') as handle:handle.write('\n## GBP2本轮私有备份已验收\n\n'+message+'\n')
    shutil.copy2(path,repo/'project-context'/name)
path=root/'codex/SIMULATION_LOCK.json';lock=json.loads(path.read_text(encoding='utf-8'))
assert not lock['runtime_active']
lock.update(updated_at=now,gbp2_backup_verified=True,backup_content_commit=commit)
path.write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8',newline='\n')
shutil.copy2(path,repo/'project-context/SIMULATION_LOCK.json')
(repo/'docs/GBP2私有备份说明.md').write_text('# GBP2后续私有备份验收\n\n'+message+'\n\n[完整实验报告](GBP2优化测试报告.md)；[验收记录](../project-context/GBP2_OPTIMIZATION_BACKUP_VERIFIED.json)。\n',encoding='utf-8',newline='\n')
path=repo/'evidence/scene4-progress-fix/evidence_manifest.json';index=json.loads(path.read_text(encoding='utf-8'))
for name in index['files']:index['files'][name]=hashlib.sha256((repo/name).read_bytes()).hexdigest()
path.write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Verified GBP2 content backup recorded: '+commit)
