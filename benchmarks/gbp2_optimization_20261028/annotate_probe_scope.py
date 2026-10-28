"""Clarify a diagnostic fixture's limits without altering its original outputs."""
import json
from pathlib import Path
out=Path('D:/STGPlanner/codex/outputs/gbp2_optimization_20261028')
for name in ['repair_formal_gbp2_09','gbp2_default_frontier_20261028_10']:
    path=out/('volume_probe_'+name)/'SCOPE_CLARIFICATION.json'
    assert not path.exists()
    value={'original_probe_outputs_preserved':True,'native_map_unchanged':True,
           'grid_origin_filter':'Native voxel at(x,y,z0.7) must be free',
           'query_sensor_z_m':.456,
           'box_filter':'A1.0x0.8x0.6m box centered atz0.7. This is a simplified diagnostic filter, not the exact per-query projected native robot box.',
           'does_not_prove_native_vertex_or_route_feasibility':True,
           'threshold_counts_with_box_filter_are_diagnostic_only':True,
           'effect_on_formal_trial11_selection':'None. Intermediate0.03 was preregistered before trial10 and before this probe.',
           'unknown_over_native_known_columns':'XY0.4m columns are marked known if at least one native voxel atz0.1..1.9 is known. This is neither the public known-plane map nor a ground-truth reachable mask.'}
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Probe scope annotations saved; original outputs unchanged.')
