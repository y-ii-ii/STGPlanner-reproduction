"""Record verified content backup; a later metadata commit is identified by Git."""
import datetime
import hashlib
import json
import shutil
from pathlib import Path
root=Path('D:/STGPlanner');repo=root/'catkin_ws/src/STGPlanner';out=root/'codex/outputs/tare_optimization_20261028'
receipt=json.loads((out/'TARE_OPTIMIZATION_BACKUP_VERIFIED.json').read_text(encoding='utf-8'))
assert receipt['private'] and receipt['verification']['all_checks_passed']
commit=receipt['remote_commit'];now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
for target in [repo/'project-context/TARE_OPTIMIZATION_BACKUP_VERIFIED.json',root/'codex/TARE_OPTIMIZATION_BACKUP_VERIFIED.json']:
    shutil.copy2(out/'TARE_OPTIMIZATION_BACKUP_VERIFIED.json',target)
for name in ['STATUS.md','RUNBOOK.md']:
    path=root/'codex'/name;text=path.read_text(encoding='utf-8')
    text+='\n## TARE后续私有备份已验收\n\n内容提交`'+commit+'`已推送到私有分支fix/fael-gbp2-progress。远端独立克隆恢复通过261项新增归档的压缩前后SHA、此前622项清单、67项实验隔离/运行检查，历史原始证据未改动；main、历史基线分支和两个标签均保留。验收记录TARE_OPTIMIZATION_BACKUP_VERIFIED.json指向该内容提交，随后交接/报告互链元数据提交的最终HEAD以git log和远端核对为准。TARE当前恢复已验证原版，无活动测试；GBP2保持暂停。旧四算法表只增加后续入口，保留原预选TARE基线行，全部新对照/候选在TARE报告中单列。\n'
    path.write_text(text,encoding='utf-8',newline='\n');shutil.copy2(path,repo/'project-context'/name)
path=root/'codex/SIMULATION_LOCK.json';value=json.loads(path.read_text(encoding='utf-8'));value.update(updated_at=now,backup_content_commit=commit,tare_backup_verified=True)
path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n');shutil.copy2(path,repo/'project-context/SIMULATION_LOCK.json')
for name in ['README.md','finalize_backup.py']:shutil.copy2(root/'codex/work/tare_optimization'/name,repo/'benchmarks/tare_optimization'/name)
path=repo/'evidence/scene4-progress-fix/evidence_manifest.json';value=json.loads(path.read_text(encoding='utf-8'))
for name in value['files']:value['files'][name]=hashlib.sha256((repo/name).read_bytes()).hexdigest()
path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Verified content backup recorded: '+commit)
