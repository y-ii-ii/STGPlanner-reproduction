#include <planner_common/map_manager_voxblox_impl.h>
#include <voxblox_msgs/FilePath.h>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <tuple>
#include <cmath>

int main(int argc,char**argv){
  ros::init(argc,argv,"gbp_stagnation_probe_09");if(argc!=5)return 2;
  ros::NodeHandle nh("/gbp_stagnation_probe_inputs"),priv("~");
  MapManagerVoxblox<MapManagerVoxbloxServer,MapManagerVoxbloxVoxel> map(nh,priv);
  ros::AsyncSpinner spinner(1);spinner.start();
  voxblox_msgs::FilePath load;load.request.file_path=argv[1];
  if(!ros::service::call(priv.resolveName("load_map"),load))return 3;
  SensorParamsBase sensor;if(!sensor.loadParams("/gbp_stagnation_probe_09/SensorParams/VLP16"))return 4;
  map.setRaycastingParams(true,1.0);
  std::map<std::pair<int,int>,bool> known_plane;
  std::ifstream cells(argv[3]);std::string line;std::getline(cells,line);
  while(std::getline(cells,line)){
    for(auto&character:line)if(character==',')character=' ';
    std::istringstream row(line);double x,y;int occupied;
    if(row>>x>>y>>occupied)known_plane[{int(std::floor(x/.4)),int(std::floor(y/.4))}]=occupied;
  }
  std::ifstream positions(argv[2]);std::ofstream output(argv[4]);
  output<<"{\"same_native_scan_api\":true,\"post_exploration_map\":true,\"restores_historical_gain\":false,\"public_plane_cells\":"<<known_plane.size()<<",\"cases\":[";
  std::string name;double x,y,z,yaw,stored;bool first=true;
  while(positions>>name>>x>>y>>z>>yaw>>stored){
    StateVec state;state<<x,y,z,yaw;Eigen::Vector3d origin=state.head(3);
    std::vector<Eigen::Vector3d>endpoints;sensor.getFrustumEndpoints(state,endpoints);
    std::tuple<int,int,int>counts;std::vector<std::pair<Eigen::Vector3d,MapManager::VoxelStatus>>voxels;
    map.getScanStatus(origin,endpoints,counts,voxels,sensor);
    int unknown=0,z_bins[5]={0,0,0,0,0};double z_sum=0.;
    int weighted_over_known_plane=0,weighted_over_known_free_plane=0;
    std::set<std::tuple<int,int,int>> unique,unique_known_plane,unique_known_free_plane;
    for(const auto&item:voxels){const auto&p=item.first;
      if(p.x() < -50 || p.x()>80 || p.y() < -20 || p.y()>100 || p.z() < -2 || p.z()>3)continue;
      if(item.second!=MapManager::VoxelStatus::kUnknown)continue;
      ++unknown;z_sum+=p.z();++z_bins[p.z()<0?0:p.z()<.5?1:p.z()<1?2:p.z()<2?3:4];
      const auto key=std::make_tuple(int(std::floor(p.x()/.2)),int(std::floor(p.y()/.2)),int(std::floor(p.z()/.2)));
      unique.insert(key);auto cell=known_plane.find({int(std::floor(p.x()/.4)),int(std::floor(p.y()/.4))});
      if(cell!=known_plane.end()){
        ++weighted_over_known_plane;unique_known_plane.insert(key);
        if(!cell->second){++weighted_over_known_free_plane;unique_known_free_plane.insert(key);}
      }
    }
    if(!first)output<<",";first=false;
    output<<"{\"name\":\""<<name<<"\",\"x\":"<<x<<",\"y\":"<<y<<",\"sensing_z\":"<<z<<",\"yaw\":"<<yaw
      <<",\"stored_historical_unknown\":"<<stored<<",\"final_map_unknown_weighted\":"<<unknown<<",\"final_map_unknown_unique\":"<<unique.size()
      <<",\"frontier_001\":"<<(sensor.isFrontier(unknown*map.getResolution())?"true":"false")<<",\"unknown_mean_z\":"<<(unknown?z_sum/unknown:0)
      <<",\"unknown_weighted_over_known_plane\":"<<weighted_over_known_plane<<",\"unknown_unique_over_known_plane\":"<<unique_known_plane.size()
      <<",\"unknown_weighted_over_known_free_plane\":"<<weighted_over_known_free_plane<<",\"unknown_unique_over_known_free_plane\":"<<unique_known_free_plane.size()
      <<",\"unknown_z_bins\":[";
    for(int i=0;i<5;i++){if(i)output<<",";output<<z_bins[i];}output<<"]}";
  }
  output<<"]}\n";
}
