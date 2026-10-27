#include <planner_common/map_manager_voxblox_impl.h>
#include <voxblox_msgs/FilePath.h>
#include <fstream>
#include <iostream>
int main(int argc,char**argv){
  ros::init(argc,argv,"gbp_gain_probe");
  if(argc!=4)return 2;
  ros::NodeHandle nh("/gbp_gain_probe_inputs"),priv("~");
  MapManagerVoxblox<MapManagerVoxbloxServer,MapManagerVoxbloxVoxel> map(nh,priv);
  ros::AsyncSpinner spinner(1);spinner.start();
  voxblox_msgs::FilePath load;load.request.file_path=argv[1];
  if(!ros::service::call(priv.resolveName("load_map"),load))return 3;
  SensorParamsBase sensor;if(!sensor.loadParams("/gbp_gain_probe/SensorParams/VLP16"))return 4;
  map.setRaycastingParams(true,1.0);
  std::ifstream positions(argv[2]);std::ofstream output(argv[3]);
  StateVec zero=StateVec::Zero();std::vector<Eigen::Vector3d> shape_endpoints;
  sensor.getFrustumEndpoints(zero,shape_endpoints);
  double max_length=0;for(const auto& p:shape_endpoints)max_length=std::max(max_length,p.norm());
  output<<"{\"native_map_replay\":true,\"resolution\":"<<map.getResolution()<<",\"scan_width\":"<<sensor.width<<",\"scan_height\":"<<sensor.height<<",\"endpoint_count\":"<<shape_endpoints.size()<<",\"configured_max_range\":"<<sensor.max_range<<",\"maximum_generated_ray_length\":"<<max_length<<",\"cases\":[";
  double x,y;bool first=true;
  while(positions>>x>>y){
    for(double z:{.456,.7}){
      StateVec state;state<<x,y,z,0;
      Eigen::Vector3d origin=state.head(3);std::vector<Eigen::Vector3d>endpoints;
      sensor.getFrustumEndpoints(state,endpoints);
      std::tuple<int,int,int>counts;std::vector<std::pair<Eigen::Vector3d,MapManager::VoxelStatus>>voxels;
      map.getScanStatus(origin,endpoints,counts,voxels,sensor);
      int unknown=0,known=0;double unknown_z_sum=0;
      for(const auto& item:voxels){auto p=item.first;
        if(p.x() < -50 || p.x() > 80 || p.y() < -20 || p.y()>100 || p.z() < -2 || p.z()>3)continue;
        if(item.second==MapManager::VoxelStatus::kUnknown){unknown++;unknown_z_sum+=p.z();}else known++;
      }
      // Read-only ablation: remove only the beyond-range ray tail.
      auto clipped=endpoints;
      for(auto& p:clipped)p=origin+(p-origin).normalized()*sensor.max_range;
      std::tuple<int,int,int>clipped_counts;std::vector<std::pair<Eigen::Vector3d,MapManager::VoxelStatus>>clipped_voxels;
      map.getScanStatus(origin,clipped,clipped_counts,clipped_voxels,sensor);
      int clipped_unknown=0;
      for(const auto& item:clipped_voxels){auto p=item.first;
        if(p.x()>=-50 && p.x()<=80 && p.y()>=-20 && p.y()<=100 && p.z()>=-2 && p.z()<=3 && item.second==MapManager::VoxelStatus::kUnknown)clipped_unknown++;
      }
      if(!first)output<<",";first=false;
      output<<"{\"x\":"<<x<<",\"y\":"<<y<<",\"z\":"<<z<<",\"unknown\":"<<unknown<<",\"known\":"<<known<<",\"frontier\":"<<(sensor.isFrontier(unknown*map.getResolution())?"true":"false")<<",\"range_clipped_unknown\":"<<clipped_unknown<<",\"unknown_mean_z\":"<<(unknown?unknown_z_sum/unknown:0)<<"}";
    }
  }
  output<<"]}\n";return 0;
}
