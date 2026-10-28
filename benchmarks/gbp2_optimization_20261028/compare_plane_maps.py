"""Post-hoc overlap with successful runs; never used by the native planner."""
import argparse
import csv
import json
import math
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--trial',default='repair_formal_gbp2_09');args=parser.parse_args()
root=Path('D:/STGPlanner');results=root/'benchmarks/results'
def read_cells(trial):
    with (results/trial/'known_plane_cells.csv').open(encoding='utf-8') as handle:
        return {(math.floor(float(row['x'])/.4+1e-7),math.floor(float(row['y'])/.4+1e-7)) for row in csv.DictReader(handle)}
references={name:read_cells(name) for name in ['formal_stgp_01','formal_tare_01','repair_formal_fael_01']}
union=set.union(*references.values());candidate=read_cells(args.trial)
records={}
for name,cells in {**references,args.trial:candidate}.items():
    records[name]={'known_cells':len(cells),'known_area_m2':len(cells)*.16,
                  'overlap_with_reference_union_fraction':len(cells&union)/len(union),
                  'own_cells_outside_reference_union_fraction':len(cells-union)/len(cells)}
value={'reference_union_cells':len(union),'records':records,
       'scope':'Offline overlap diagnostic with the union of other successful runs. This union is not ground truth or a reachable-area mask, is never fed into native control, and does not replace the public95 metric.'}
out=root/'codex/outputs/gbp2_optimization_20261028'/(args.trial+'_map_overlap.json')
out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
