"""Compare the nominal flat-root sensing conversion with independent live odometry."""
import json
import re
import statistics
from pathlib import Path
root=Path('D:/STGPlanner');out=root/'codex/outputs/gbp2_optimization_20261028'
records={}
for name in ['gbp2_default_frontier_20261028_10','gbp2_sensor_height_20261028_12']:
    folder=root/'benchmarks/results'/name
    snapshot=json.loads((folder/'sensor_frame_snapshot.json').read_text(encoding='utf-8'))
    audit=json.loads((folder/'live_runtime_audit.json').read_text(encoding='utf-8'))
    planning=audit['native_parameters']['PlanningParams']
    sensor=audit['native_parameters']['SensorParams']['VLP16'];assert sensor['center_offset']==[0.,0.,0.]
    measured=snapshot['odometry']['/sensor_to_world/odometry']['position'][2]
    log=(folder/'native_planner.log').read_text(encoding='utf-8',errors='replace')
    roots=[float(value) for value in re.findall(r'root_z=(-?\d+\.\d+)',log)]
    assert roots
    projected=statistics.median(roots)
    predicted=projected+planning['robot_height']-planning['max_ground_height']
    records[name]={'root_samples':len(roots),'projected_root_z_range_m':[min(roots),max(roots)],
       'projected_root_z_median_m':projected,'live_robot_height_m':planning['robot_height'],
       'projection_height_m':planning['max_ground_height'],'converted_root_sensor_z_m':predicted,
       'live_sensor_z_at_flat_snapshot_m':measured,'absolute_reference_difference_m':abs(measured-predicted)}
before=records['gbp2_default_frontier_20261028_10']['absolute_reference_difference_m']
after=records['gbp2_sensor_height_20261028_12']['absolute_reference_difference_m']
value={'records':records,'flat_reference_difference_reduced':after<before,
       'scope':'Nominal conversion at median projected flat roots versus independent sensor-odometry snapshots on the same flat floor. Snapshots are not temporally paired with every selected root. Does not establish all sample/cluster gain origins or sensor angles are exact, and does not establish exploration performance improvement. Residual ground-projection/voxel quantization remains.'}
(out/'height_reference_validation.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,indent=2))
