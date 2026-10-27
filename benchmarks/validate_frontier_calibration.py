from pathlib import Path
import json,yaml
root=Path('/mnt/d/STGPlanner/benchmarks')
gain=json.loads((root/'gbp_corridor_gain.json').read_text());geometry=json.loads((root/'gbp_ground_probe.json').read_text())
free={(r['x'],r['y']) for r in geometry['cases'] if r['box']=='free'}
rows=[r for r in gain['cases'] if r['z']==.456 and (r['x'],r['y']) in free]
old=sum(r['frontier'] for r in rows);new=sum(r['frontier_001'] for r in rows)
gateway=next(r for r in rows if r['x']==18.5 and r['y']==66)
config=yaml.safe_load((root/'config/gbp2.yaml').read_text())
checks={'native_probe_and_real_collision_map_used':gain['native_map_replay'] and geometry['native_function_on_real_map'],
 'original_fraction_misses_all_free_corridor_views':len(rows)==125 and old==0,
 'calibrated_fraction_retains_outlet_views':new==16,
 'specific_free_gateway_view_reactivated':not gateway['frontier'] and gateway['frontier_001'] and gateway['unknown']==275,
 'deployed_native_fraction_matches_calibration':config['SensorParams']['VLP16']['frontier_percentage_threshold']==.01}
value={'passed':all(checks.values()),'checks':checks,'free_views':len(rows),'original_frontier_views':old,'calibrated_frontier_views':new,'native_unknown_cutoff_005':gain['minimum_unknown_005'],'native_unknown_cutoff_001':gain['minimum_unknown_001'],'specific_gateway':gateway,'note':'Native fraction0.05->0.01 is a declared sensor-frontier configuration calibration. Common observer ratio/95% evaluation threshold is unchanged. Frozen map evidence is not a full exploration result.'}
(root/'frontier_calibration_validation.json').write_text(json.dumps(value,indent=2));print(json.dumps(value,indent=2))
if not value['passed']:raise SystemExit(1)
