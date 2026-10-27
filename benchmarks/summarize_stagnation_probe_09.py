import json
from pathlib import Path
folder=Path('D:/STGPlanner/codex/outputs/gbp_stagnation_probe_09')
data=json.loads((folder/'result.json').read_text())
groups={}
for label in ('projected','flat_sensor'):
    cases=[row for row in data['cases'] if '_'+label+'_' in row['name']]
    weighted=sum(row['final_map_unknown_weighted'] for row in cases)
    unique=sum(row['final_map_unknown_unique'] for row in cases)
    groups[label]={
        'queries':len(cases),'frontier_queries':sum(row['frontier_001'] for row in cases),
        'unknown_weighted_sum':weighted,'unknown_unique_sum_across_queries':unique,
        'weighted_unknown_above_2m_fraction':sum(row['unknown_z_bins'][4] for row in cases)/weighted if weighted else None,
        'weighted_unknown_over_known_plane_fraction':sum(row['unknown_weighted_over_known_plane'] for row in cases)/weighted if weighted else None,
        'weighted_unknown_over_known_free_plane_fraction':sum(row['unknown_weighted_over_known_free_plane'] for row in cases)/weighted if weighted else None,
        'unique_unknown_over_known_plane_fraction':sum(row['unknown_unique_over_known_plane'] for row in cases)/unique if unique else None,
    }
value={'groups':groups,'queries':len(data['cases']),
    'limitations':['Queries re-evaluate historical selected states on the final map; do not reconstruct historical gains.',
        'Fractions aggregate native weighted ray samples or native voxels across queries, not a global area metric.',
        'Public known-plane projection is an offline diagnostic only; never used for planner control.',
        'Distributions alone do not establish a unique causal explanation or justify changing bounds/thresholds.']}
(folder/'summary.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value,indent=2))
