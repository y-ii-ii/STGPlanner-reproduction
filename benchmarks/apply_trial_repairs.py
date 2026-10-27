"""Record the GBP2 adapter fix and explicitly calibrated sampling/time settings."""
from pathlib import Path
import difflib,hashlib,json
root=Path('/mnt/d/STGPlanner/benchmarks');archive=root/'trial_repairs';archive.mkdir(exist_ok=True)
records={}
def edit(relative,transform):
    path=root/relative;stem=relative.replace('/','__')
    before=archive/(stem+'.before');after=archive/(stem+'.after')
    if not before.exists():before.write_bytes(path.read_bytes())
    original=before.read_text();updated=transform(original);assert updated!=original
    allowed={original,updated}
    if after.exists():allowed.add(after.read_text())
    if path.read_text() not in allowed:raise RuntimeError('Unrecorded edits; will not overwrite '+str(path))
    if path.read_text()!=updated:path.write_text(updated)
    after.write_text(updated)
    (archive/(stem+'.patch')).write_text(''.join(difflib.unified_diff(original.splitlines(True),updated.splitlines(True),fromfile='a/benchmarks/'+relative,tofile='b/benchmarks/'+relative)))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    records['benchmarks/'+relative]={'original_sha256':sha(before),'repaired_sha256':sha(after),'archive_stem':stem}
def driver(s):
    needle='d.update(protocol_revision=3,';assert needle in s
    s=s.replace(needle,'d.update(adapter_revision=1,protocol_revision=3,',1)
    needle="                else:d['empty_plans']+=1;time.sleep(.2)\n"
    assert s.count(needle)==1
    return s.replace(needle,needle+'''                # IDL kHoming=2 ends native exploration. Execute its return
                # path once, then observe while parked until the SAME common
                # coverage/time stop. Do not force another exploration cycle.
                if response.status == 2 and not finished.is_set():
                    d['native_finished'] = True
                    d['native_finish_sim_s'] = rospy.get_time()-start_sim
                    d['native_homing_path_empty'] = not bool(response.path)
                    d['native_homing_motion_state'] = motion.get_state() if response.path else None
                    event('native_homing_ended',path_empty=not bool(response.path),motion_state=d['native_homing_motion_state'])
                    if response.path and motion.get_state() != 3:
                        finish('native_homing_motion_failure');return
                    pause_pub.publish(Bool(True))
                    while not finished.is_set():time.sleep(.05)
                    return
''')
def config(s):
    for old,new in [('num_vertices_max: 500','num_vertices_max: 2000'),('num_edges_max:    5000','num_edges_max:    20000'),('num_loops_cutoff: 2000','num_loops_cutoff: 8000'),('num_loops_max:    20000','num_loops_max:    80000')]:
        assert old in s;s=s.replace(old,new,1)
    needle='PlanningParams:\n';assert needle in s
    return s.replace(needle,needle+'''  # Shared controller max is 2m/s; use a conservative 1m/s return estimate.
  v_max:            2.0
  v_homing_max:     1.0
''',1)
edit('benchmark_trial.py',driver);edit('config/gbp2.yaml',config)
value={'common_protocol_revision':3,'adapter_revision':1,'measurement_controller_threshold_unchanged':True,'native_sampling_limits':{'vertices':[500,2000],'edges':[5000,20000],'loops_cutoff':[2000,8000],'loops_max':[20000,80000]},'native_time_model_m_s':{'v_max':[.2,2.0],'v_homing_max':[.2,1.0]},'files':records,'note':'Only the GBP2 native-end branch changes in the adapter. Common observer, controller, initialization and coverage/time stop remain unchanged. Algorithm parameters changed explicitly; final results are an engineering adaptation, not paper-identical settings.'}
(archive/'manifest.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
