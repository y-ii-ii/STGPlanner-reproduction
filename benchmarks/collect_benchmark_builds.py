from pathlib import Path
import difflib,hashlib,json,subprocess
root=Path('/mnt/d/STGPlanner/benchmarks');patchdir=root/'patches';patchdir.mkdir(exist_ok=True)
pairs=[
 ('fael-cmake.patch',root/'sources/FAEL/fael_planner/planner/CMakeLists.txt',Path('/opt/stgplanner/benchmarks/fael_ws/src/planner/CMakeLists.txt'),'fael_planner/planner/CMakeLists.txt'),
 ('tare-path-diagnostic.patch',root/'sources/tare_planner/src/tare_planner/src/sensor_coverage_planner/sensor_coverage_planner_ground.cpp',Path('/opt/stgplanner/benchmarks/tare_ws/src/tare_planner/src/sensor_coverage_planner/sensor_coverage_planner_ground.cpp'),'src/tare_planner/src/sensor_coverage_planner/sensor_coverage_planner_ground.cpp'),
 ('gbp2-runtime-measurement.patch',root/'sources/gbplanner_ros/gbplanner/src/gbplanner.cpp',Path('/opt/stgplanner/benchmarks/gbp2_ws/src/gbplanner/src/gbplanner.cpp'),'gbplanner/src/gbplanner.cpp'),
 ('gbp2-native-diagnostics.patch',root/'sources/gbplanner_ros/gbplanner/src/rrg.cpp',Path('/opt/stgplanner/benchmarks/gbp2_ws/src/gbplanner/src/rrg.cpp'),'gbplanner/src/rrg.cpp')]
for name,original,modified,path in pairs:
    patch=''.join(difflib.unified_diff(original.read_text().splitlines(True),modified.read_text().splitlines(True),fromfile='a/'+path,tofile='b/'+path))
    (patchdir/name).write_text(patch)
facts={}
for label,command in [('uname',['uname','-a']),('cpu',['lscpu']),('ros',['rosversion','-d']),('gazebo',['gazebo','--version']),('compiler',['g++','--version'])]:
    r=subprocess.run(command,capture_output=True,text=True);facts[label]=r.stdout.strip()
for name in ['planner','control_planner_interface','traversability_analysis']:
    original=root/'sources/FAEL/fael_planner'/('robot_move/traversability_analysis' if name=='traversability_analysis' else name)
    native=Path('/mnt/d/STGPlanner/catkin_ws/src/STGPlanner/stgp_planner')/('robot_move/traversability_analysis' if name=='traversability_analysis' else name)
    if name=='traversability_analysis':
        # Verify shared perception module behaviour, ignoring upstream comments.
        import re
        rows={}
        for p in original.rglob('*.cpp'):
            q=native/p.relative_to(original)
            if q.exists():
                def canonical(x):return re.sub(r'\s+','',re.sub(r'//[^\n]*|/\*.*?\*/','',x,flags=re.S))
                rows[str(p.relative_to(original))]=canonical(p.read_text())==canonical(q.read_text())
        facts['shared_traversability_source_equivalence_without_comments']=rows
facts['source_lock_sha256']=hashlib.sha256((root/'sources.lock.json').read_bytes()).hexdigest()
(root/'environment.json').write_text(json.dumps(facts,indent=2))
print(json.dumps(facts,indent=2))
