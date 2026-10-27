"""Check classification against preserved real runs and reject corrupt pause metadata."""
import copy
import json
import tempfile
from pathlib import Path
from run_outcome import classify_outcome

root = Path('/mnt/d/STGPlanner/benchmarks')
expected = {
    'repair_formal_fael_01': 'common_threshold_reached',
    'repair_formal_gbp2_01': 'intentional_diagnostic_stop',
    'repair_formal_gbp2_03': 'complete_time_limit_observation',
    'repair_formal_gbp2_05': 'complete_time_limit_observation',
    'repair_formal_gbp2_06': 'user_interrupted',
}
checks = {}
for trial, classification in expected.items():
    folder = root / 'results' / trial
    result = json.loads((folder / 'result.json').read_text())
    actual = classify_outcome(folder, result)
    checks[trial] = actual == classification
    assert checks[trial], (trial, actual, classification)
folder = root / 'results/repair_formal_gbp2_06'
result = json.loads((folder / 'result.json').read_text())
pause = json.loads((folder / 'user_pause.json').read_text())
with tempfile.TemporaryDirectory() as temporary:
    temporary = Path(temporary)
    altered = copy.deepcopy(pause)
    altered['sim_time_s'] += 1
    (temporary / 'user_pause.json').write_text(json.dumps(altered))
    try: classify_outcome(temporary, result)
    except AssertionError: checks['pause_metadata_mismatch_rejected'] = True
    else: raise AssertionError('Mismatched pause metadata accepted')
checks['user_pause_rejected_as_final_observation'] = classify_outcome(folder, result) not in (
    'common_threshold_reached','complete_time_limit_observation')
record = {'checks': checks, 'passed': all(checks.values()),
    'note': 'Real preserved fixture outcomes; original result and interruption files not modified.'}
(root / 'outcome_classification_validation.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
