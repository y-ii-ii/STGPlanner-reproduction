from pathlib import Path
import hashlib,json,shutil

task=Path(__file__).resolve().parents[1]
base=Path('D:/STGPlanner/logs/planner_completion')
out=task/'outputs'
d=json.loads((base/'long_runtime.json').read_text())
isolated=json.loads((base/'isolated_regression.json').read_text())
assert d['passed'] and isolated['passed']
assert d['checks'].get('zero_post_finish_commands') and d['checks'].get('post_finish_position_stable')
# Re-serialize the complete callback records from the authoritative final JSON.
# Windows-mounted append handles can interleave, so retain that original too.
event_file=base/'long_runtime.events.jsonl'
shutil.copy2(event_file,base/'long_runtime.events.raw.jsonl')
event_file.write_text(''.join(json.dumps(e)+'\n' for e in sorted(d['events'],key=lambda r:r['wall_seconds'])))
statuses=[json.loads(s) for s in (base/'status_after.history.jsonl').read_text().splitlines() if s.strip()]
assert len(statuses)>=10
assert all(len(s['displays'])==3 and all(v['enabled'] and v['status'] and all(p['name']=='Status: Ok' for p in v['status']) for v in s['displays'].values()) for s in statuses[-10:])
meta=json.loads((base/'qt_capture_metadata.json').read_text())
assert meta['unix_time']>d['started_unix']+d['finish_seconds']
shots=out/'screenshots'
picture=shots/'04_rviz_diagnostics_fixed.png'
shutil.copy2(base/'rviz_native_capture.png',picture)
from datetime import datetime,timezone
meta.update(file=picture.name,capturedAt=datetime.fromtimestamp(meta['unix_time'],timezone.utc).isoformat(),sha256=hashlib.sha256(picture.read_bytes()).hexdigest(),format='PNG; live Qt controls and OGRE framebuffer from the completed long-test run')
manifest=json.loads((shots/'capture_manifest.json').read_text())
manifest=[m for m in manifest if m['file']!=picture.name]+[meta]
(shots/'capture_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
for f in shots.iterdir():
    if f.is_file():shutil.copy2(f,Path('D:/STGPlanner/screenshots')/f.name)
shutil.copy2(base/'long_run_metrics.png',out/'long_run_metrics.png')
summary={k:v for k,v in d.items() if k not in ('metrics','events','node_samples','resources')}
summary['last_metric']=d['metrics'][-1]
summary['nominal_ratio']=d['metrics'][-1]['metric']/d['map_area']
summary['completion_response_seconds']=d['explorer_finish_seconds']-d['finish_seconds']
source_init=next(e['project_unix'] for e in d['events'] if e['kind']=='explorer_initialized')
source_finish=next(e['project_unix'] for e in d['events'] if e['kind']=='explorer_finish')
summary['source_completion_response_seconds']=source_finish-source_init-d['metrics'][-1]['project_elapsed']
summary['isolated_regression']=isolated
summary['rviz_last_ten_samples_ok']=True
summary['rviz_capture_unix']=meta['unix_time']
(base/'long_verification_summary.json').write_text(json.dumps(summary,indent=2))
shutil.copy2(base/'long_verification_summary.json',out/'长时间运行验证结果.json')
print(json.dumps(summary,indent=2))
