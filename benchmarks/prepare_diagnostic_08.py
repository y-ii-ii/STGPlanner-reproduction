"""Install logging-only native diagnostics and a separately named diagnostic driver."""
import datetime
import hashlib
import json
import socket
import subprocess
from pathlib import Path

root=Path('/mnt/d/STGPlanner')
out=root/'codex/outputs/diagnostic_gbp2_gain_08_setup'
lock_path=root/'codex/SIMULATION_LOCK.json'
lock=json.loads(lock_path.read_text())
assert lock['state']=='idle' and not lock['runtime_active'], lock
for port in (11311,11345,11312):
    with socket.socket() as connection:
        assert connection.connect_ex(('127.0.0.1',port))!=0, f'Occupied port: {port}'
processes=subprocess.check_output(['ps','-eo','pid,comm,args'],text=True)
assert not any(line.split()[1:2] in ([name] for name in ('rosmaster','roslaunch','gzserver','gbplanner_node')) for line in processes.splitlines()), processes
out.mkdir(exist_ok=True)
assert not any(out.iterdir()), 'Diagnostic setup is not empty; do not overwrite'
native=Path('/opt/stgplanner/benchmarks/gbp2_ws/src/gbplanner/src/rrg.cpp')
before=native.read_text()
expected=json.loads((root/'benchmarks/results/repair_formal_gbp2_07/native_source_manifest.json').read_text())
row=next(row for row in expected['sources'] if row['method']=='gbp2' and row['relative']=='gbplanner/src/rrg.cpp')
assert hashlib.sha256(native.read_bytes()).hexdigest()==row['repaired_sha256']
needle='    best_vertex_ = local_graph_->getVertex(path[0]);'
assert before.count(needle)==1
extra='''    // BEGIN_DIAGNOSTIC_SELECTED_08: logging only, does not change selection.
    std::vector<Vertex*> diagnostic_path;
    local_graph_->getShortestPath(best_path_id, local_graph_rep_, true, diagnostic_path);
    int diagnostic_frontiers = 0, diagnostic_unknown_sum = 0;
    for (auto* vertex : diagnostic_path) {
      if (vertex->vol_gain.is_frontier && !vertex->is_hanging) ++diagnostic_frontiers;
      diagnostic_unknown_sum += vertex->vol_gain.num_unknown_voxels;
    }
    auto* diagnostic_leaf = local_graph_->getVertex(best_path_id);
    auto* diagnostic_root = local_graph_->getVertex(0);
    ROS_INFO("GBP_DIAGNOSTIC_SELECTED root_x=%.6f root_y=%.6f root_z=%.6f root_unknown=%d leaf_x=%.6f leaf_y=%.6f leaf_z=%.6f leaf_unknown=%d leaf_frontier=%d path_frontiers=%d path_unknown=%d any_frontier=%d gain=%.6f",
      diagnostic_root->state[0], diagnostic_root->state[1], diagnostic_root->state[2], diagnostic_root->vol_gain.num_unknown_voxels,
      diagnostic_leaf->state[0], diagnostic_leaf->state[1], diagnostic_leaf->state[2], diagnostic_leaf->vol_gain.num_unknown_voxels,
      diagnostic_leaf->vol_gain.is_frontier, diagnostic_frontiers, diagnostic_unknown_sum, frontier_exists, best_gain);
    // END_DIAGNOSTIC_SELECTED_08
'''
after=before.replace(needle,extra+needle)
(out/'rrg.cpp.before').write_text(before)
(out/'rrg.cpp.diagnostic').write_text(after)
native.write_text(after)
driver=(root/'benchmarks/benchmark_trial.py').read_text()
driver=driver.replace('from planner_msgs.srv import planner_srv, planner_srvRequest',
    'from planner_msgs.srv import planner_srv, planner_srvRequest\nfrom voxblox_msgs.srv import FilePath')
driver=driver.replace("d.update(adapter_revision=1,protocol_revision=3,", "d.update(diagnostic=True,diagnostic_note='Logging-only native selection diagnostics and in-run native map saves; not a formal statistical repeat.',adapter_revision=1,protocol_revision=3,")
driver=driver.replace("threading.Thread(target=driver,daemon=True).start();lastwrite=0;next_health=start_wall+10", "threading.Thread(target=driver,daemon=True).start();lastwrite=0;next_health=start_wall+10;next_snapshot=600")
needle2='        if sim-start_sim>=a.limit:finish('
assert driver.count(needle2)==1
snapshot='''        if sim-start_sim>=next_snapshot and next_snapshot<=1300:
            try:
                path=out/('native_snapshot_'+str(next_snapshot)+'.vxblx')
                response=rospy.ServiceProxy('/gbplanner_node/save_map',FilePath)(str(path))
                event('diagnostic_native_snapshot',requested_at_s=sim-start_sim,path=str(path),bytes=path.stat().st_size if path.exists() else 0,response=str(response))
            except Exception as error:event('diagnostic_native_snapshot_error',error=str(error))
            next_snapshot=1000 if next_snapshot==600 else 1300 if next_snapshot==1000 else 999999
'''
driver=driver.replace(needle2,snapshot+needle2)
(root/'codex/work/benchmark_diagnostic08.py').write_text(driver)
(out/'benchmark_diagnostic08.py').write_text(driver)
audit=(root/'codex/work/audit_live_07.py').read_text().replace('repair_formal_gbp2_07','diagnostic_gbp2_gain_08').replace('audit_07','audit_08')
(root/'codex/work/audit_live_08.py').write_text(audit)
refresh=(root/'codex/work/refresh_live_07.py').read_text().replace('repair_formal_gbp2_07','diagnostic_gbp2_gain_08').replace('runtime_07','runtime_08')
(root/'codex/work/refresh_live_08.py').write_text(refresh)
manifest={'trial':'diagnostic_gbp2_gain_08','diagnostic_only':True,'protocol_revision':3,'common_threshold_changed':False,
    'algorithm_decisions_changed':False,'changes':['logging-only native selected-path diagnostics','native map saves during diagnostic run'],
    'native_before_sha256':hashlib.sha256(before.encode()).hexdigest(),'native_diagnostic_sha256':hashlib.sha256(after.encode()).hexdigest(),
    'before_processes':processes,'limit_sim_s':1400,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(out/'setup_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
lock.update(state='running',runtime_active=False,phase='building_logging_only_diagnostics',trial='diagnostic_gbp2_gain_08',
    note='Algorithm chat owns WSL; no simulation active. Compiling selected-path logging only, then a new1400s diagnostic with native snapshots; formal07 remains preserved.')
lock_path.write_text(json.dumps(lock,indent=2)+'\n')
print(json.dumps(manifest))
