from pathlib import Path
import json,subprocess
root=Path('/mnt/d/STGPlanner/benchmarks')
source=Path('/opt/stgplanner/benchmarks/gbp2_ws/src/gbplanner/src/rrg.cpp').read_text()
helper=source.split('// BEGIN_GAIN_SENSOR_FRAME\n')[1].split('// END_GAIN_SENSOR_FRAME')[0]
program='''#include <Eigen/Dense>
#include <Eigen/Geometry>
#include <cmath>
using StateVec=Eigen::Matrix<double,4,1>;
'''+helper+'''
int main(){StateVec projected;projected<<10,20,.7,M_PI/2;
auto sensing=gainSensingState(projected,true,.456,.7);
if(std::abs(sensing[2]-.456)>1e-12)return 1;
if(std::abs(projected[2]-.7)>1e-12)return 2;
auto aerial=gainSensingState(projected,false,.456,.7);
if((aerial-projected).norm()>1e-12)return 3;
auto origin=gainSensorOrigin(sensing,Eigen::Vector3d(.2,0,.3));
if((origin-Eigen::Vector3d(10,20.2,.756)).norm()>1e-12)return 4;
return 0;}
'''
path=Path('/opt/stgplanner/benchmarks/gain_frame_regression.cpp');path.write_text(program)
binary=path.with_suffix('')
subprocess.run(['g++','-O1','-std=c++17','-I/usr/include/eigen3',str(path),'-o',str(binary)],check=True)
result=subprocess.run([str(binary)])
checks={'physical_ground_height_and_unchanged_input_and_aerial_and_rotated_extrinsic':result.returncode==0,'both_native_ray_gain_paths_use_sensor_state':source.count('getFrustumEndpoints(sensor_state,')==2,'both_native_ray_gain_paths_use_sensor_origin':source.count('Eigen::Vector3d origin = gainSensorOrigin(sensor_state,')==2}
value={'passed':all(checks.values()),'checks':checks,'exit':result.returncode,'ground_projection_m':.7,'physical_sensor_reference_m':.456}
(root/'gain_frame_regression.json').write_text(json.dumps(value,indent=2));print(json.dumps(value,indent=2))
if not value['passed']:raise SystemExit(1)
