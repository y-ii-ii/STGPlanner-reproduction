// Read-only diagnostics against a saved native TSDF. No common coverage input.
#include <planner_common/map_manager_voxblox_impl.h>
#include <voxblox_msgs/FilePath.h>
#include <fstream>
#include <map>
#include <set>
#include <tuple>
#include <cmath>

int main(int argc, char** argv) {
  ros::init(argc, argv, "gbp2_volume_probe");
  if (argc != 3) return 2;
  ros::NodeHandle nh("/gbp2_volume_probe_inputs"), priv("~");
  MapManagerVoxblox<MapManagerVoxbloxServer,MapManagerVoxbloxVoxel> map(nh,priv);
  ros::AsyncSpinner spinner(1); spinner.start();
  voxblox_msgs::FilePath load; load.request.file_path=argv[1];
  if (!ros::service::call(priv.resolveName("load_map"),load)) return 3;
  SensorParamsBase sensor;
  if (!sensor.loadParams("/gbp2_volume_probe/SensorParams/VLP16")) return 4;
  std::ofstream output(argv[2]);
  output << "{\"native_map_only\":true,\"robot_motion\":false,"
            "\"route_feasibility_proven\":false,\"grid_spacing_m\":4,\"cases\":[";
  bool first=true;
  std::map<std::pair<int,int>,bool> known_columns;
  for (double x=-48;x<=80;x+=4) for (double y=-20;y<=100;y+=4) {
    // Only native-map free query origins, not assumed reachable viewpoints.
    if (map.getVoxelStatus(Eigen::Vector3d(x,y,.7)) != MapManager::VoxelStatus::kFree)
      continue;
    bool box_free = map.getBoxStatus(Eigen::Vector3d(x,y,.7),
         Eigen::Vector3d(1.,.8,.6),true) == MapManager::VoxelStatus::kFree;
    // Replicate the native root's downward projection from a flat sensor pose.
    // This is a hypothetical flat pose, not a measured sensor height elsewhere.
    double ground_distance=-1.;
    for (const auto& delta : std::vector<Eigen::Vector3d>{Eigen::Vector3d(0,0,0),
          Eigen::Vector3d(.5,0,.5),Eigen::Vector3d(-.5,0,.5),
          Eigen::Vector3d(0,.5,.5),Eigen::Vector3d(0,-.5,.5)}) {
      Eigen::Vector3d start=Eigen::Vector3d(x,y,.456)+delta;
      Eigen::Vector3d end=start-Eigen::Vector3d(0,0,5),hit;
      double tsdf_distance;
      if (map.getRayStatus(start,end,true,hit,tsdf_distance) == MapManager::VoxelStatus::kOccupied) {
        ground_distance=std::abs(start.z()-hit.z())-delta.z(); break;
      }
    }
    for (bool nonuniform : {true,false}) {
      map.setRaycastingParams(nonuniform,1.0);
      StateVec state; state << x,y,.456,0.;
      Eigen::Vector3d origin=state.head(3);
      std::vector<Eigen::Vector3d> endpoints;
      sensor.getFrustumEndpoints(state,endpoints);
      std::tuple<int,int,int> counts;
      std::vector<std::pair<Eigen::Vector3d,MapManager::VoxelStatus>> voxels;
      map.getScanStatus(origin,endpoints,counts,voxels,sensor);
      int unknown=0,above2=0,known_xy=0;
      std::set<std::tuple<int,int,int>> unique;
      std::set<std::pair<int,int>> xy_unknown,xy_novel;
      for (const auto& item : voxels) {
        const auto& p=item.first;
        if (p.x() < -50 || p.x()>80 || p.y() < -20 || p.y()>100 || p.z() < -2 || p.z()>3)
          continue;
        if (item.second != MapManager::VoxelStatus::kUnknown) continue;
        ++unknown; if (p.z()>2) ++above2;
        unique.emplace(int(std::floor(p.x()/.2)),int(std::floor(p.y()/.2)),int(std::floor(p.z()/.2)));
        const auto xy=std::make_pair(int(std::floor(p.x()/.4)),int(std::floor(p.y()/.4)));
        xy_unknown.insert(xy);
        auto found=known_columns.find(xy);
        if (found == known_columns.end()) {
          bool known=false;
          for (double z=.1;z<=1.91;z+=.2) {
            auto status=map.getVoxelStatus(Eigen::Vector3d((xy.first+.5)*.4,(xy.second+.5)*.4,z));
            if (status != MapManager::VoxelStatus::kUnknown) { known=true; break; }
          }
          found=known_columns.emplace(xy,known).first;
        }
        if (found->second) ++known_xy; else xy_novel.insert(xy);
      }
      if (!first) output << ','; first=false;
      output << "{\"x\":"<<x<<",\"y\":"<<y<<",\"sensor_z\":0.456,\"box_free\":"<<(box_free?"true":"false")
             <<",\"native_ground_distance_from_flat_pose\":"<<ground_distance
             <<",\"root_sensor_z_using_fixed_robot_height\":"<<(ground_distance>=0?.912-ground_distance:-999)
             <<",\"nonuniform\":"<<(nonuniform?"true":"false")
             <<",\"unknown_weighted\":"<<unknown<<",\"unknown_unique\":"<<unique.size()
             <<",\"unknown_above2m\":"<<above2<<",\"unknown_over_native_known_column\":"<<known_xy
             <<",\"unknown_xy_cells\":"<<xy_unknown.size()<<",\"native_novel_xy_cells\":"<<xy_novel.size()
             <<",\"native_ratio\":"<<unknown*map.getResolution()/5184.
             <<",\"frontier001\":"<<(unknown*map.getResolution()/5184.>=.01?"true":"false")
             <<",\"frontier003\":"<<(unknown*map.getResolution()/5184.>=.03?"true":"false")
             <<",\"frontier010\":"<<(unknown*map.getResolution()/5184.>=.1?"true":"false")<<'}';
    }
  }
  output << "]}\n";
  return 0;
}
