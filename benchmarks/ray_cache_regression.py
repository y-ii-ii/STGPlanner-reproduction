"""Exercise the allocation and boundary expressions extracted from native code."""
from pathlib import Path
import json,re,resource,subprocess
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
root=Path('/mnt/d/STGPlanner/benchmarks');out=Path('/opt/stgplanner/benchmarks/ray_regression');out.mkdir(exist_ok=True)
before=(root/'progress_repairs/gbp2__planner_common__src__voxblox__voxblox_alt_impl.cpp.before').read_text()
after=Path('/opt/stgplanner/benchmarks/gbp2_ws/src/planner_common/src/voxblox/voxblox_alt_impl.cpp').read_text()
scan=json.loads((root/'gbp_gain_probe.json').read_text())
width,height=scan['scan_width'],scan['scan_height']
def allocation(s):return re.search(r'Eigen::MatrixXd starting_points\(\s*(height, width|width, height)\);',s).group(1)
results={}
for label,text in [('original',before),('fixed',after)]:
    dims=allocation(text)
    source='''#include <Eigen/Dense>
#include <iostream>
int main(){int width=WIDTH,height=HEIGHT;Eigen::MatrixXd starting_points(DIMS);starting_points.setZero();
for(int y=0;y<height;y++)for(int x=0;x<width;x++)starting_points(x,y)=1000*y+x;
int wrong=0;for(int y=0;y<height;y++)for(int x=0;x<width;x++)if(starting_points(x,y)!=1000*y+x)wrong++;
std::cout<<wrong<<std::endl;return wrong?9:0;}'''.replace('DIMS',dims).replace('WIDTH',str(width)).replace('HEIGHT',str(height))
    path=out/(label+'.cpp');path.write_text(source);binary=out/label
    subprocess.run(['g++','-std=c++17','-O1','-DNDEBUG','-I/usr/include/eigen3',str(path),'-o',str(binary)],check=True)
    r=subprocess.run([str(binary)],capture_output=True,text=True)
    results[label]={'allocation':dims,'exit':r.returncode,'aliased_cells':int(r.stdout.strip())}
# The allocation fix must also bound x+1 at the final horizontal ray.
for label,text in [('original',before),('fixed',after)]:
    condition=re.search(r'if \((x_increment_dist <= voxel_size && x(?: \+ 1)? < width)\)',text).group(1)
    source='''#include <Eigen/Dense>
int main(){int width=WIDTH,height=HEIGHT;float x_increment_dist=.01,voxel_size=.2;
Eigen::MatrixXd starting_points(width,height);starting_points.setZero();
int x=width-1,y=height-1;if(CONDITION)starting_points(x+1,y)=1;return 0;}'''.replace('CONDITION',condition).replace('WIDTH',str(width)).replace('HEIGHT',str(height))
    path=out/(label+'_edge.cpp');path.write_text(source);binary=out/(label+'_edge')
    subprocess.run(['g++','-std=c++17','-O1','-I/usr/include/eigen3',str(path),'-o',str(binary)],check=True)
    r=subprocess.run([str(binary)],capture_output=True,text=True)
    results[label+'_edge']={'condition':condition,'exit':r.returncode,'assertion':r.stderr[:250]}
checks={'original_cache_failure_reproduced':results['original']['aliased_cells']>0,'fixed_rays_independent':results['fixed']['aliased_cells']==0,'original_last_column_failure_reproduced':results['original_edge']['exit']!=0,'fixed_last_column_in_bounds':results['fixed_edge']['exit']==0}
checks['native_endpoint_dimensions_match']=scan['endpoint_count']==width*height
value={'passed':all(checks.values()),'shape':[width,height],'checks':checks,'cases':results}
(root/'ray_cache_regression.json').write_text(json.dumps(value,indent=2));print(json.dumps(value,indent=2))
if not value['passed']:raise SystemExit(1)
