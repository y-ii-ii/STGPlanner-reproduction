from pathlib import Path
import json, shutil, hashlib
from datetime import datetime, timezone

task=Path(__file__).resolve().parents[1]
base=Path('D:/STGPlanner')
folder=base/'logs/rviz_repair'
shots=task/'outputs/screenshots'
meta=json.loads((folder/'qt_capture_metadata.json').read_text())
assert all(v['enabled'] and v['status'] and all(s['name']=='Status: Ok' for s in v['status']) for v in meta['status'].values())
dest=shots/'04_rviz_diagnostics_fixed.png'
shutil.copy2(folder/'rviz_native_capture.png',dest)
data=dest.read_bytes()
assert data[:8]==b'\x89PNG\r\n\x1a\n' and len(data)>150000
meta['file']=dest.name
meta['capturedAt']=datetime.fromtimestamp(meta['unix_time'],timezone.utc).isoformat()
meta['sha256']=hashlib.sha256(data).hexdigest()
meta['format']='PNG; native Qt controls and OGRE rendered framebuffer'
manifest=json.loads((shots/'capture_manifest.json').read_text(encoding='utf-8'))
manifest=[m for m in manifest if m['file']!=dest.name]+[meta]
(shots/'capture_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
for p in shots.iterdir():
    if p.is_file():shutil.copy2(p,base/'screenshots'/p.name)
shutil.copy2(folder/'verification_summary.json',task/'outputs/RViz修复验证结果.json')
print(json.dumps({'file':str(dest),'capturedAt':meta['capturedAt'],'sha256':meta['sha256'],'bytes':len(data)},indent=2))
