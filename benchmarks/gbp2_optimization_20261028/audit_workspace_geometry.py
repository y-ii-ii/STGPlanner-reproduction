"""Check saved plane geometry against the declared native XY bounds, offline only."""
import csv
import json
from pathlib import Path
root=Path('D:/STGPlanner');results=root/'benchmarks/results'
records={}
for name in ['formal_stgp_01','formal_tare_01','repair_formal_fael_01','repair_formal_gbp2_09']:
    with (results/name/'known_plane_cells.csv').open(encoding='utf-8') as handle:
        cells=[(float(r['x']),float(r['y'])) for r in csv.DictReader(handle)]
    outside=[(x,y) for x,y in cells if not (-50<=x<=80 and -20<=y<=100)]
    records[name]={'known_cells':len(cells),'xy_extent':{'xmin':min(x for x,y in cells),'xmax':max(x for x,y in cells),
        'ymin':min(y for x,y in cells),'ymax':max(y for x,y in cells)},'outside_native_xy_bounds_cells':len(outside),
        'outside_native_xy_bounds_fraction':len(outside)/len(cells)}
value={'declared_native_xy_bounds':[-50,80,-20,100],'records':records,
       'scope':'Read-only check using saved plane cells; not a reachable mask, not a planning input, and not a new scoring rule.'}
target=root/'codex/outputs/gbp2_optimization_20261028/workspace_geometry_audit.json'
target.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,indent=2))
