"""Deploy one preregistered frontier threshold only when the runtime is idle."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from assert_idle import assert_idle
from guard_new_experiment import check_new_experiment

parser = argparse.ArgumentParser()
parser.add_argument('--value', type=float, required=True)
parser.add_argument('--expected', type=float, required=True)
parser.add_argument('--tag', required=True)
args = parser.parse_args()
assert args.value in [.01, .015, .03, .1]
assert re.fullmatch('[a-z0-9_]+', args.tag)
root = Path('/mnt/d/STGPlanner')
check_new_experiment(root)
out = root/'codex/outputs/gbp2_optimization_20261028'
idle = assert_idle(root)
path = root/'benchmarks/config/gbp2.yaml'
before = path.read_text()
pattern = r'(?m)^(\s*frontier_percentage_threshold:\s*)([0-9.]+)(\s*)$'
matches = list(re.finditer(pattern, before))
assert len(matches) == 1 and float(matches[0][2]) == args.expected
after = re.sub(pattern, lambda m: m[1]+str(args.value)+m[3], before)
audit = json.loads((out/'preflight_audit/audit.json').read_text())
for item in audit['native_files']:
    assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest() == item['sha256'], item['path']
dest = out/(args.tag+'_configuration')
dest.mkdir(exist_ok=False)
(dest/'gbp2.yaml.before').write_text(before)
(dest/'gbp2.yaml.after').write_text(after)
(dest/'change.json').write_text(json.dumps({'before': args.expected, 'after': args.value,
    'native_sources_binaries_unchanged': True, 'actual_idle_check': idle,
    'single_parameter_change': 'SensorParams/VLP16/frontier_percentage_threshold'}, indent=2)+'\n')
path.write_text(after)
print(json.dumps({'deployed': args.value, 'snapshot': str(dest)}))
