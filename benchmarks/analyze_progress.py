"""Validate completed real runs; keep exploration success separate from I/O health."""
from pathlib import Path
import csv,datetime,hashlib,json,math,re
root=Path('/mnt/d/STGPlanner/benchmarks');repo=Path('/mnt/d/STGPlanner/catkin_ws/src/STGPlanner')
selection=json.loads((root/'progress_trials.json').read_text())
out=root/'progress_report';out.mkdir(exist_ok=True)
checks={};results={};goals={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def summarize(folder):
    d=json.loads((folder/'result.json').read_text())
    rows=[json.loads(l) for l in (folder/'metrics.jsonl').read_text().splitlines() if l.strip()]
    stationary=longest=0.
    for a,b in zip(rows,rows[1:]):
        stationary=stationary+b['sim_s']-a['sim_s'] if math.hypot(b['x']-a['x'],b['y']-a['y'])<.03 else 0.
        longest=max(longest,stationary)
    checkpoint=next((x for x in rows if x['sim_s']>=1600),None)
    end={k:d[k] for k in ['finish_reason','sim_time_s','wall_time_s','distance_m','area_m2','coverage_fraction','nonempty_plans','empty_plans','runtime_native_s_summary','average_speed_m_s','rejected_disconnected_paths']}
    end.update(longest_near_stationary_sim_s=longest,checkpoint_1600=checkpoint,completed_before_1600=d['finish_reason']=='coverage_threshold' and d['sim_time_s']<1600,native_finished=d.get('native_finished',False),native_finish_sim_s=d.get('native_finish_sim_s'),native_homing_motion_state=d.get('native_homing_motion_state'),adapter_revision=d.get('adapter_revision',0),trial=d['trial'])
    if rows:
        before=next((x for x in rows if x['sim_s']>=d['sim_time_s']-100),rows[0])
        end['final_100s_area_gain_m2']=d['area_m2']-before['area_m2']
    return d,rows,end
for method in ['fael','gbp2']:
    folder=root/'results'/selection['final_runs'][method]
    d,rows,summary=summarize(folder);old,_,oldsummary=summarize(root/'results'/('formal_'+method+'_01'))
    log=(folder/'native_planner.log').read_text(errors='replace')
    results[method]={'before':oldsummary,'after':summary}
    flags={
      'no_fatal_error':'fatal_error' not in d,
      'protocol_revision':d['protocol_revision']==3,
      'adapter_revision_recorded':d.get('adapter_revision',0)==selection['adapter_revision'][method],
      'same_threshold':d['area_threshold_m2']==old['area_threshold_m2']==7400.5,
      'static_terrain':'* /terrainAnalysis/clearDyObs: False' in (folder/'movement.log').read_text(),
      'no_active_ros_errors':not d['errors'],
      'native_alive':bool(d['native_health']) and all(x['alive'] for x in d['native_health']),
      'valid_stop_reason':d['finish_reason'] in ['coverage_threshold','sim_time_limit'],
      'real_motion':d['validation']['planner_produced_motion'],
      'stop_ack':d['validation']['stop_ack'],
      'parked_command_zero':d['validation']['parked_command_zero'],
      'parking_drift':d['validation']['parking_drift_under_0_1m'],
      'sensor_live':d['validation']['sensor_stream_live'] and d['cloud_messages']>1000,
      'monotonic_time':all(b['sim_s']>=a['sim_s'] for a,b in zip(rows,rows[1:])),
      'monotonic_area':all(b['area_m2']>=a['area_m2'] for a,b in zip(rows,rows[1:])),
      'monotonic_distance':all(b['distance_m']>=a['distance_m'] for a,b in zip(rows,rows[1:])),
      'nominal_ratio':abs(d['coverage_fraction']-d['area_m2']/7790)<1e-9,
      'time_bound':d['sim_time_s']<=2401,
      'finish_matches_metric':(d['finish_reason']=='coverage_threshold')==(d['area_m2']>7400.5),
      'map_saved':(folder/'coverage.ufo').stat().st_size>100,
      'runtime_recorded':d['runtime_native_s_summary']['count']>0,
    }
    cells=list(csv.DictReader((folder/'known_plane_cells.csv').open()))
    flags['saved_cells_match']=d['area_m2']-.001<=len(cells)*.16<=d['area_m2']+100
    for k,v in flags.items():checks[method+'.'+k]=v
    if d.get('native_finish_sim_s') is not None:
        parked=[r for r in rows if r['sim_s']>d['native_finish_sim_s']+2]
        checks[method+'.native_end_does_not_restart_planning']=not parked or all(r['nonempty_plans']==parked[0]['nonempty_plans'] and r['empty_plans']==parked[0]['empty_plans'] for r in parked)
        summary['observed_hold_after_native_end_s']=max(0,d['sim_time_s']-d['native_finish_sim_s'])
    goals[method+'.common_threshold_reached']=d['finish_reason']=='coverage_threshold'
    goals[method+'.coverage_improved']=d['coverage_fraction']>old['coverage_fraction']
    if method=='fael':
        counts=[tuple(map(int,x)) for x in re.findall(r'FAEL_PROGRESS frontiers=(\d+) candidates=(\d+) tours=(\d+) roadmap=(\d+)',log)]
        summary['native_frontier_diagnostics']={'records':len(counts),'max_frontiers':max((x[0] for x in counts),default=0),'zero_tour_records':sum(x[2]==0 for x in counts)}
        summary['guard_warnings']={name:log.count('PROGRESS_DIAGNOSTIC '+name) for name in ['no connected tour candidate','disconnected optimized tour']}
    else:
        counts=list(map(int,re.findall(r'Have (\d+) frontiers from global graph',log)))
        summary['native_frontier_diagnostics']={'records':len(counts),'max_global_frontiers':max(counts,default=0),'nonzero_records':sum(x>0 for x in counts)}
for filename in ['ray_cache_regression.json','fael_frontier_regression.json','gain_frame_regression.json','gbp_core_regression.json','trial_contract_regression.json','frontier_calibration_validation.json','cluster_frontier_regression.json']:
    regression=json.loads((root/filename).read_text())
    for k,v in regression['checks'].items():checks[filename+'.'+k]=v
manifest=json.loads((root/'protocol_manifest.json').read_text())
trial_repairs=json.loads((root/'trial_repairs/manifest.json').read_text())
for relative,expected in manifest['files'].items():
    if relative in trial_repairs['files']:
        record=trial_repairs['files'][relative]
        checks['archived_original_protocol.'+relative]=record['original_sha256']==expected and sha(root/'trial_repairs'/(record['archive_stem']+'.before'))==expected
        expected=record['repaired_sha256']
    checks['recorded_protocol.'+relative]=sha(repo/relative)==expected
    actual=root/relative[len('benchmarks/'):] if relative.startswith('benchmarks/') else repo/relative
    checks['active_protocol.'+relative]=sha(actual)==expected
repairs=json.loads((root/'progress_repairs/manifest.json').read_text())
for item in repairs['sources']:
    actual=Path('/opt/stgplanner/benchmarks')/(item['method']+'_ws/src')/item['relative']
    checks['native_source.'+item['method']+'.'+item['relative']]=sha(actual)==item['repaired_sha256']
for name,item in repairs['binaries'].items():checks['native_binary.'+name]=sha(Path(item['path']))==item['sha256']
attempts=[]
for trial in selection['intermediate_runs']:
    attempt=root/'results'/trial;data=json.loads((attempt/'result.json').read_text());interruption=json.loads((attempt/'interruption.json').read_text()) if (attempt/'interruption.json').exists() else None
    if interruption:
        checks[trial+'.intentional_stop_documented']=interruption['intentional_native_stop'] and data['finish_reason'] in ['process_exit:native_planner','native_node_unresponsive']
    else:
        checks[trial+'.complete_failed_observation_preserved']=data['finish_reason']=='sim_time_limit' and data['sim_time_s']>=2400
    checks[trial+'.stop_confirmed']=all(data['validation'][x] for x in ['stop_ack','parked_command_zero','parking_drift_under_0_1m'])
    attempts.append({'result':{k:data[k] for k in ['trial','sim_time_s','distance_m','area_m2','coverage_fraction','finish_reason']},'intentional_stop':interruption})
probe=json.loads((root/'gbp_gain_probe.json').read_text());pairs=list(zip(probe['cases'][::2],probe['cases'][1::2]))
calibrated=json.loads((root/'gbp_gain_probe_calibrated.json').read_text())
checks['native_calibrated_probe.endpoint_dimensions_match']=calibrated['scan_width']*calibrated['scan_height']==calibrated['endpoint_count']
checks['native_calibrated_probe.physical_ray_range']=abs(calibrated['maximum_generated_ray_length']-calibrated['configured_max_range'])<1e-5
diagnostics={'intermediate_attempts':attempts,'gain_height_replay':{'visited_positions':len(pairs),'actual_height_unknown_mean':sum(a['unknown'] for a,b in pairs)/len(pairs),'projected_height_unknown_mean':sum(b['unknown'] for a,b in pairs)/len(pairs),'actual_height_frontiers':sum(a['frontier'] for a,b in pairs),'projected_height_frontiers':sum(b['frontier'] for a,b in pairs),'original_maximum_ray_length':probe['maximum_generated_ray_length'],'corrected_maximum_ray_length':calibrated['maximum_generated_ray_length'],'native_scan_shape':[calibrated['scan_width'],calibrated['scan_height']]}}
diagnostics['native_service_sampling_comparison']=json.loads((root/'offline_rrg_probe.json').read_text())
value={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'trial_selection':selection,'adapter_and_configuration_changes':trial_repairs,'protocol_checks_passed':all(checks.values()),'exploration_goals_passed':all(goals.values()),'checks':checks,'exploration_goals':goals,'results':results,'intermediate_diagnostics':diagnostics,'note':'Final repair configuration selected before its outcome. Previous attempts include intentional diagnostic stops and a complete 2400s failure; none are pooled as repetitions. Common observer/controller/coverage-time stop unchanged, adapter and native configuration changes explicitly archived. 1600s checkpoint is first sample at or after1600s; earlier completed run uses terminal result. A censored run is not a completion time.'}
(out/'progress_validation.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k not in ['checks','results']},indent=2))
if not value['protocol_checks_passed']:raise SystemExit(1)
