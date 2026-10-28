"""Deploy a tested native configuration and record exact idle/native provenance."""
import argparse
import hashlib
import json
from pathlib import Path
from assert_idle import assert_idle
parser=argparse.ArgumentParser()
parser.add_argument('--reference',required=True)
parser.add_argument('--description',required=True)
args=parser.parse_args()
allowed=['repair_formal_gbp2_09','gbp2_sensor_height_20261028_12','gbp2_frontier015_height_20261028_13',
         'gbp2_frontier03_20261028_11','gbp2_frontier03_repeat_20261028_12']
assert args.reference in allowed
root=Path('/mnt/d/STGPlanner');out=root/'codex/outputs/gbp2_optimization_20261028'
idle=assert_idle(root,allow_capped=True)
audit=json.loads((out/'preflight_audit/audit.json').read_text())
records=[]
for item in audit['native_files']:
    actual=hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()
    assert actual==item['sha256'],item['path']
    records.append({'path':item['path'],'sha256':actual})
reference=root/'benchmarks/results'/args.reference
assert (reference/'result.json').exists()
config=reference/'config/gbp2.yaml'
if not config.exists():config=reference/'preflight/config/gbp2.yaml'
assert config.is_file()
target=root/'benchmarks/config/gbp2.yaml'
snapshot=out/'final_configuration';snapshot.mkdir(exist_ok=False)
(snapshot/'gbp2.yaml.before').write_bytes(target.read_bytes())
(snapshot/'gbp2.yaml.after').write_bytes(config.read_bytes())
target.write_bytes(config.read_bytes())
value={'reference_trial':args.reference,'description':args.description,
       'configuration_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
       'native_matches09':True,'runtime_idle_verified':True,'idle_check':idle,'native_files':records}
(out/'deployment_state.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value,indent=2))
