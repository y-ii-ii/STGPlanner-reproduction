#include <planner_common/map_manager_voxblox_impl.h>
#include <voxblox_msgs/FilePath.h>
#include <fstream>
#include <iostream>
#include <set>
#include <tuple>

int main(int argc, char** argv) {
  ros::init(argc,argv,"gbp_sampling_probe_07");
  if(argc!=4) return 2;
  ros::NodeHandle nh("/gbp_sampling_probe_inputs"), priv("~");
  MapManagerVoxblox<MapManagerVoxbloxServer,MapManagerVoxbloxVoxel> map(nh,priv);
  ros::AsyncSpinner spinner(1); spinner.start();
  voxblox_msgs::FilePath load; load.request.file_path=argv[1];
  if(!ros::service::call(priv.resolveName("load_map"),load)) return 3;
  const std::string ns="/gbp_sampling_probe_07/SensorParams/VLP16";
  map.setRaycastingParams(true,1.0);
  std::ifstream input(argv[2]); std::vector<std::pair<double,double>> positions;
  double x,y; while(input>>x>>y) positions.emplace_back(x,y);
  std::ofstream output(argv[3]); output<<"{\"frozen_map\":\""<<argv[1]<<"\",\"no_motion\":true,\"cases\":[";
  bool first=true;
  for(double vertical_degrees : {5.0,2.0}) {
    std::vector<double> resolution{5.0*M_PI/180.,vertical_degrees*M_PI/180.};
    ros::param::set(ns+"/resolution",resolution);
    ros::param::set(ns+"/frontier_percentage_threshold",.01);
    SensorParamsBase sensor; if(!sensor.loadParams(ns)) return 4;
    for(const auto& point : positions) for(double yaw_degrees : {0.,45.,90.}) {
      StateVec state; state<<point.first,point.second,.456,yaw_degrees*M_PI/180.;
      Eigen::Vector3d origin=state.head(3); std::vector<Eigen::Vector3d> endpoints;
      sensor.getFrustumEndpoints(state,endpoints);
      std::tuple<int,int,int> counts;
      std::vector<std::pair<Eigen::Vector3d,MapManager::VoxelStatus>> voxels;
      map.getScanStatus(origin,endpoints,counts,voxels,sensor);
      int unknown=0,known=0,bins[5]={0,0,0,0,0}; double zsum=0.;
      std::set<std::tuple<int,int,int>> unique;
      for(const auto& item:voxels) {
        const auto& p=item.first;
        if(p.x() < -50 || p.x() > 80 || p.y() < -20 || p.y()>100 || p.z() < -2 || p.z()>3) continue;
        if(item.second==MapManager::VoxelStatus::kUnknown) {
          ++unknown; zsum+=p.z();
          ++bins[p.z()<0?0:p.z()<.5?1:p.z()<1.?2:p.z()<2.?3:4];
          unique.emplace(std::floor(p.x()/.2),std::floor(p.y()/.2),std::floor(p.z()/.2));
        } else ++known;
      }
      if(!first) output<<","; first=false;
      output<<"{\"x\":"<<point.first<<",\"y\":"<<point.second<<",\"yaw_degrees\":"<<yaw_degrees
        <<",\"vertical_resolution_degrees\":"<<vertical_degrees<<",\"width\":"<<sensor.width<<",\"height\":"<<sensor.height
        <<",\"unknown\":"<<unknown<<",\"unique_unknown\":"<<unique.size()<<",\"known\":"<<known
        <<",\"frontier_001\":"<<(sensor.isFrontier(unknown*map.getResolution())?"true":"false")
        <<",\"unknown_mean_z\":"<<(unknown?zsum/unknown:0)<<",\"unknown_z_bins\":[";
      for(int i=0;i<5;i++){if(i)output<<","; output<<bins[i];} output<<"]}";
    }
  }
  output<<"]}\n";
}
