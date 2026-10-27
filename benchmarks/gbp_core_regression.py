"""Compile actual extracted native code against controlled geometric fixtures."""
from pathlib import Path
import json,re,subprocess
root=Path('/mnt/d/STGPlanner/benchmarks');native=Path('/opt/stgplanner/benchmarks/gbp2_ws/src');archive=root/'progress_repairs';scratch=Path('/opt/stgplanner/benchmarks/core_regression');scratch.mkdir(exist_ok=True)
before=(archive/'gbp2__gbplanner__src__rrg.cpp.before').read_text();after=(native/'gbplanner/src/rrg.cpp').read_text()
def run(name,code):
    source=scratch/(name+'.cpp');source.write_text(code);binary=source.with_suffix('')
    subprocess.run(['g++','-O1','-std=c++17','-I/usr/include/eigen3',str(source),'-o',str(binary)],check=True)
    return list(map(float,subprocess.check_output([str(binary)],text=True).split()))
stub='''#include <Eigen/Dense>
#include <iostream>
#include <cmath>
#include <vector>
struct MapManager {
enum class VoxelStatus{kUnknown,kFree,kOccupied};
bool fallback=true,all_unknown=false;
double getResolution(){return .2;}
double getPointDistance(const Eigen::Vector3d& p){return all_unknown||(fallback&&std::abs(p.x())<.25)?-1:p.z();}
VoxelStatus getRayStatus(const Eigen::Vector3d& start,const Eigen::Vector3d&,bool,Eigen::Vector3d& end,double& dist){
end=start;dist=0;if(all_unknown||(fallback&&std::abs(start.x())<.25))return VoxelStatus::kUnknown;end.z()=0;return VoxelStatus::kOccupied;}
};
MapManager map;MapManager* map_manager_=&map;
struct Params {bool interpolate_projection_distance=false;} planning_params_;
'''
projection={};times={};geometry={}
for label,text in [('original',before),('fixed',after)]:
    start=text.index('double Rrg::projectSample(');end=text.index('\n}\n',start)+3
    function=text[start:end].replace('double Rrg::projectSample','double projectSample')
    main='''int main(){MapManager::VoxelStatus status;Eigen::Vector3d p(0,0,.7);
double distance=projectSample(p,status);std::cout<<.7-distance+.7<<" ";
planning_params_.interpolate_projection_distance=true;p=Eigen::Vector3d(0,0,.7);distance=projectSample(p,status);std::cout<<.7-distance+.7<<" ";
planning_params_.interpolate_projection_distance=false;map.fallback=false;p=Eigen::Vector3d(0,0,.7);distance=projectSample(p,status);std::cout<<.7-distance+.7<<" ";
map.all_unknown=true;p=Eigen::Vector3d(0,0,.7);projectSample(p,status);std::cout<<(status==MapManager::VoxelStatus::kUnknown)<<std::endl;}
'''
    projection[label]=run('projection_'+label,stub+function+main)
    expression=re.search(r'double time_cost = (time_to_target.*?);',text,re.S).group(1)
    program='''#include <iostream>
struct Params{bool auto_homing_enable=true;}planning_params_;
double cost(double time_to_target,double time_to_home){return EXPRESSION;}
int main(){std::cout<<cost(120,80)<<" ";planning_params_.auto_homing_enable=false;std::cout<<cost(120,80)<<std::endl;}
'''.replace('EXPRESSION',expression)
    times[label]=run('time_'+label,program)
for label,path in [('original',archive/'gbp2__planner_common__src__params.cpp.before'),('fixed',native/'planner_common/src/params.cpp')]:
    text=path.read_text();start=text.index('else if (type == SensorType::kLidar) {');body=text[start:text.index('\n  }',start)]
    declarations='\n'.join(re.search(r'double '+axis+r' = .*?;',body).group(0) for axis in ['x','y','z'])
    program='''#include <cmath>
#include <iostream>
int main(){double max_range=12,dv=M_PI/12,dh=.3;DECLARATIONS
std::cout<<std::sqrt(x*x+y*y+z*z)<<std::endl;}
'''.replace('DECLARATIONS',declarations)
    geometry[label]=run('range_'+label,program)[0]
checks={
 'original_lateral_ray_downshift_reproduced':abs(projection['original'][0]-.2)<1e-8,
 'fixed_discrete_projection_height':abs(projection['fixed'][0]-.7)<1e-8,
 'fixed_interpolated_projection_height':abs(projection['fixed'][1]-.7)<1e-8,
 'central_projection_preserved':abs(projection['fixed'][2]-.7)<1e-8,
 'unknown_ground_not_fabricated':projection['fixed'][3]==1,
 'original_outbound_budget_omission_reproduced':times['original']==[80,80],
 'fixed_outbound_and_optional_return_budget':times['fixed']==[200,120],
 'original_lidar_range_overshoot_reproduced':geometry['original']>12.3,
 'fixed_lidar_range_is_physical':abs(geometry['fixed']-12)<1e-8,
 'both_lidar_generators_corrected':(native/'planner_common/src/params.cpp').read_text().count('double x = max_range * cos(dv) * cos(dh);')==2,
}
value={'passed':all(checks.values()),'checks':checks,'projected_heights_discrete_interpolated_central_unknown':projection,'time_costs_return_enabled_disabled':times,'ray_norm_at_15deg':geometry,'fixture_note':'Projection uses the actual extracted native function. Only map ray queries are controlled: central unknown, raised lateral ray hits a horizontal plane at z=0.'}
(root/'gbp_core_regression.json').write_text(json.dumps(value,indent=2));print(json.dumps(value,indent=2))
if not value['passed']:raise SystemExit(1)
