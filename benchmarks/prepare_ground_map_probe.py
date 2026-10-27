from pathlib import Path
import json,rospy
from voxblox_msgs.srv import FilePath
root=Path('/mnt/d/STGPlanner/benchmarks');rospy.init_node('prepare_ground_map_probe',anonymous=True)
rospy.wait_for_service('/gbplanner_node/save_map',timeout=10)
rospy.ServiceProxy('/gbplanner_node/save_map',FilePath)(str(root/'gbp_ground_snapshot.vxblx'))
context=json.loads((root/'results/repair_formal_gbp2_03/status.json').read_text())
(root/'gbp_ground_context.json').write_text(json.dumps(context,indent=2))
points=[(x,y) for x in [17.5,18.0,18.5,19.0,19.5,20.0] for y in [52+i*.5 for i in range(33)]]
(root/'gbp_ground_positions.txt').write_text(''.join(str(x)+' '+str(y)+'\n' for x,y in points))
text=Path('/opt/stgplanner/benchmarks/gbp2_ws/src/gbplanner/src/rrg.cpp').read_text();start=text.index('double Rrg::projectSample(');end=text.index('\n}\n',start)+3
function=text[start:end].replace('double Rrg::projectSample','double projectSample')
prefix='''#include <planner_common/map_manager_voxblox_impl.h>
#include <voxblox_msgs/FilePath.h>
#include <fstream>
#include <iostream>
using NativeMap=MapManagerVoxblox<MapManagerVoxbloxServer,MapManagerVoxbloxVoxel>;
NativeMap* map_manager_;
struct Params{bool interpolate_projection_distance=false;}planning_params_;
const char* name(MapManager::VoxelStatus s){if(s==MapManager::VoxelStatus::kFree)return "free";if(s==MapManager::VoxelStatus::kOccupied)return "occupied";return "unknown";}
'''
main=r'''
int main(int argc,char**argv){ros::init(argc,argv,"gbp_ground_probe");ros::NodeHandle nh("/ground_probe_inputs"),priv("~");NativeMap map(nh,priv);map_manager_=&map;ros::AsyncSpinner spinner(1);spinner.start();
voxblox_msgs::FilePath load;load.request.file_path=argv[1];if(!ros::service::call(priv.resolveName("load_map"),load))return 2;
RobotParams robot;if(!robot.loadParams("/gbp_ground_probe/RobotParams"))return 3;robot.setBoundMode(BoundModeType::kExtendedBound);Eigen::Vector3d size;robot.getPlanningSize(size);map.setRobotRadius(size.norm()/2);
std::ifstream points(argv[2]);std::ofstream output(argv[3]);output<<"{\"native_function_on_real_map\":true,\"box_size\":["<<size.x()<<","<<size.y()<<","<<size.z()<<"],\"cases\":[";double x,y;bool first=true;
while(points>>x>>y){Eigen::Vector3d p(x,y,.7);MapManager::VoxelStatus ground;double distance=projectSample(p,ground);p.z()-=(distance-.7);auto box=map.getBoxStatus(p+robot.center_offset,size,true);auto air=map.getVoxelStatus(Eigen::Vector3d(x,y,.456));
if(!first)output<<",";first=false;
output<<"{\"x\":"<<x<<",\"y\":"<<y<<",\"air_at_physical_lidar\":\""<<name(air)<<"\",\"ground\":\""<<name(ground)<<"\",\"projected_x\":"<<p.x()<<",\"projected_y\":"<<p.y()<<",\"projected_z\":"<<p.z()<<",\"box\":\""<<name(box)<<"\"}";}
output<<"]}\n";return 0;}
'''
Path('/opt/stgplanner/benchmarks/ground_map_probe.cpp').write_text(prefix+function+main)
print('Saved native map and generated replay from actual projectSample for',len(points),'corridor points')
