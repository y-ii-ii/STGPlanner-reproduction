"""Freeze original native code, then change only the native frontier parameter."""
import hashlib
import json
import socket
from pathlib import Path
root=Path('/mnt/d/STGPlanner');out=root/'codex/outputs/gbp2_optimization_20261028'
lock=json.loads((root/'codex/SIMULATION_LOCK.json').read_text());assert not lock['runtime_active'] and lock['gbp2_followup']=='resumed_by_user'
for port in [11311,11312,11345]:
    with socket.socket() as s:assert s.connect_ex(('127.0.0.1',port)) != 0
path=root/'benchmarks/config/gbp2.yaml';before=path.read_text();old='frontier_percentage_threshold: 0.01';new='frontier_percentage_threshold: 0.1'
assert before.count(old)==1
after=before.replace(old,new)
dest=out/'frontier10_configuration';dest.mkdir(exist_ok=False)
(dest/'gbp2.yaml.before').write_text(before);(dest/'gbp2.yaml.after').write_text(after)
audit=json.loads((out/'preflight_audit/audit.json').read_text())
for item in audit['native_files']:assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256']
path.write_text(after)
(dest/'change.json').write_text(json.dumps({'single_parameter_change':True,'old':0.01,'new':0.1,'native_sources_binaries_unchanged':True},indent=2)+'\n')
print('Native frontier qualification changed 1% -> upstream default10%; common coverage criterion unchanged.')
