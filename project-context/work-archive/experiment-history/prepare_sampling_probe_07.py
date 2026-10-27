import json
from pathlib import Path
root=Path('D:/STGPlanner')
out=root/'codex/outputs/gbp_sampling_probe_07'
out.mkdir(exist_ok=False)
rows=[json.loads(line) for line in (root/'benchmarks/results/repair_formal_gbp2_03/metrics.jsonl').read_text().splitlines()]
positions=[(r['x'],r['y']) for r in rows if r['sim_s']>1800][::30]
positions.extend([(18.5,55.5),(18.5,60.),(18.5,66.)])
(out/'positions.txt').write_text(''.join(f'{x} {y}\n' for x,y in positions))
(out/'note.json').write_text(json.dumps({'source_map':'gbp_ground_snapshot.vxblx','source_poses':'repair_formal_gbp2_03 final600s / 30s stride plus corridor points','changes_live_algorithm':False,'comparison':'Native 5deg versus 2deg vertical gain rays on same frozen old map; diagnostics only, no claim of full-run improvement.'},indent=2))
print({'positions':len(positions),'out':str(out)})
