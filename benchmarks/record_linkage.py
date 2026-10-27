from pathlib import Path
import subprocess
root=Path('/mnt/d/STGPlanner/benchmarks');lines=[]
for method,pkg,node in [('fael','planner','topo_planner_node'),('tare','tare_planner','tare_planner_node'),('gbp2','gbplanner','gbplanner_node'),('stgp','planner','topo_planner_node'),('stgp','path_execution','path_execution_node')]:
    ws='/opt/stgplanner/catkin_ws' if method=='stgp' else '/opt/stgplanner/benchmarks/'+method+'_ws'
    binary=ws+'/devel/lib/'+pkg+'/'+node
    r=subprocess.run(['bash','-c','source '+ws+'/devel/setup.bash; sha256sum '+binary+'; ldd '+binary],capture_output=True,text=True,check=True)
    assert 'not found' not in r.stdout
    lines+=['METHOD '+method+' NODE '+node,r.stdout]
(root/'runtime_linkage.txt').write_text('\n'.join(lines))
print('Recorded five native executable/library resolutions')
