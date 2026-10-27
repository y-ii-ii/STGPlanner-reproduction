from pathlib import Path
import csv,json,math,hashlib
root=Path('/mnt/d/STGPlanner/benchmarks');checks={};details={}
for method in ['fael','tare','gbp2','stgp']:
    path=root/'results'/('formal_'+method+'_01')
    d=json.loads((path/'result.json').read_text())
    rows=[json.loads(line) for line in (path/'metrics.jsonl').read_text().splitlines() if line.strip()]
    checks[method+'.no_fatal_error']='fatal_error' not in d
    checks[method+'.protocol_revision_matches']=d.get('protocol_revision')==3
    checks[method+'.static_terrain_configuration']='* /terrainAnalysis/clearDyObs: False' in (path/'movement.log').read_text()
    checks[method+'.no_active_ros_errors']=not d['errors']
    checks[method+'.native_health']=bool(d.get('native_health')) and all(x['alive'] for x in d['native_health'])
    checks[method+'.valid_stop_reason']=d.get('finish_reason') in ['coverage_threshold','sim_time_limit']
    checks[method+'.vehicle_moved']=d['validation']['planner_produced_motion']
    checks[method+'.stop_confirmed']=d['validation']['stop_ack'] and d['validation']['parked_command_zero'] and d['validation']['parking_drift_under_0_1m']
    checks[method+'.sensor_stream_live']=d['validation']['sensor_stream_live'] and d['cloud_messages']>1000
    checks[method+'.monotonic_time']=all(b['sim_s']>=a['sim_s'] and b['wall_s']>=a['wall_s'] for a,b in zip(rows,rows[1:]))
    checks[method+'.monotonic_distance']=all(b['distance_m']>=a['distance_m'] for a,b in zip(rows,rows[1:]))
    checks[method+'.metric_is_nominal_ratio']=abs(d['coverage_fraction']-d['area_m2']/7790)<1e-9
    checks[method+'.time_limit_respected']=d['sim_time_s']<=1601
    checks[method+'.finish_matches_metric']=(d['finish_reason']=='coverage_threshold')==(d['area_m2']>7400.5)
    cells=list(csv.DictReader((path/'known_plane_cells.csv').open()))
    cell_area=len(cells)*.16
    checks[method+'.saved_cells_consistent']=d['area_m2']-.001<=cell_area<=d['area_m2']+100
    checks[method+'.saved_map_present']=(path/'coverage.ufo').is_file() and (path/'coverage.ufo').stat().st_size>100
    checks[method+'.physical_average_speed']=0<d['average_speed_m_s']<2.2
    checks[method+'.native_runtime_recorded']=d['runtime_native_s_summary']['count']>0
    longest=0.;interval=0.
    for previous,current in zip(rows,rows[1:]):
        if math.hypot(current['x']-previous['x'],current['y']-previous['y'])<.03:interval+=current['sim_s']-previous['sim_s']
        else:interval=0.
        longest=max(longest,interval)
    details[method]={'reason':d['finish_reason'],'sim_time_s':d['sim_time_s'],'wall_time_s':d['wall_time_s'],'distance_m':d['distance_m'],'area_m2':d['area_m2'],'saved_cell_area_m2':cell_area,'native_runtime_mean_s':d['runtime_native_s_summary']['mean'],'average_speed_m_s':d['average_speed_m_s'],'active_ros_error_count':len(d['errors']),'longest_near_stationary_sim_s':longest,'rejected_disconnected_paths':d.get('rejected_disconnected_paths',0)}
regression=json.loads((root/'path_contract_regression.json').read_text())
for key,value in regression['checks'].items():checks['captured_path_regression.'+key]=value
manifest=json.loads((root/'protocol_manifest.json').read_text());repo=Path('/mnt/d/STGPlanner/catkin_ws/src/STGPlanner')
for rel,expected in manifest['files'].items():
    path=repo/rel;checks['protocol_hash.'+rel]=hashlib.sha256(path.read_bytes()).hexdigest()==expected
result={'passed':all(checks.values()),'checks':checks,'results':details}
(root/'validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
if not result['passed']:raise SystemExit(1)
