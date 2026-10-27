#include <planner_common/map_manager_voxblox_impl.h>
#include <voxblox_msgs/FilePath.h>
#include <fstream>
#include <iostream>
using NativeMap=MapManagerVoxblox<MapManagerVoxbloxServer,MapManagerVoxbloxVoxel>;
NativeMap* map_manager_;
struct Params{bool interpolate_projection_distance=false;}planning_params_;
const char* name(MapManager::VoxelStatus s){if(s==MapManager::VoxelStatus::kFree)return "free";if(s==MapManager::VoxelStatus::kOccupied)return "occupied";return "unknown";}
double projectSample(Eigen::Vector3d& sample,
                          MapManager::VoxelStatus& voxel_status) {
  double max_proj_len = 5.0;

  float voxel_size = map_manager_->getResolution();

  int unknown_count = 0;
  double central_ray_len = 0.0;
  std::vector<Eigen::Vector3d> extra_samples(5, Eigen::Vector3d::Zero());
  extra_samples[0] = Eigen::Vector3d(0.0, 0.0, 0.0);
  extra_samples[1] = Eigen::Vector3d(0.5, 0.0, 0.5);
  extra_samples[2] = Eigen::Vector3d(-0.5, 0.0, 0.5);
  extra_samples[3] = Eigen::Vector3d(0.0, 0.5, 0.5);
  extra_samples[4] = Eigen::Vector3d(0.0, -0.5, 0.5);
  for (int i = 0; i < extra_samples.size(); ++i) {
    Eigen::Vector3d delta = extra_samples[i];
    Eigen::Vector3d start = sample + delta;
    Eigen::Vector3d end = start - Eigen::Vector3d(0.0, 0.0, max_proj_len);

    if (planning_params_.interpolate_projection_distance) {
      double ground_dist = 0.0;
      Eigen::Vector3d point = start;
      while (ground_dist < max_proj_len) {
        double tsdf_dist = map_manager_->getPointDistance(point);
        if (tsdf_dist < 0.0) {
          // Hit Unknown
          if (i == 0) {
            central_ray_len = (point - start).norm();
          }
          ++unknown_count;
          break;
        } else {
          if (tsdf_dist <= voxel_size) {
            // Hit occupied
            voxel_status = MapManager::VoxelStatus::kOccupied;
            sample(0) = start(0);
            sample(1) = start(1);
            return (start.z() - point.z()) + tsdf_dist - delta.z();
          } else {
            // Still in free
            ground_dist += tsdf_dist;
            point -= Eigen::Vector3d(0.0, 0.0, tsdf_dist - 0.02);
          }
        }
      }
    } else {
      Eigen::Vector3d end_voxel;
      double tsdf_dist;
      MapManager::VoxelStatus vs =
          map_manager_->getRayStatus(start, end, true, end_voxel, tsdf_dist);

      if (vs == MapManager::VoxelStatus::kOccupied) {
        double ray_len = std::abs(start(2) - end_voxel(2));
        if (i == 0) {
          central_ray_len = ray_len;
        }
        voxel_status = MapManager::VoxelStatus::kOccupied;
        sample(0) = start(0);
        sample(1) = start(1);
        return ray_len - delta.z();
      } else if (vs == MapManager::VoxelStatus::kUnknown) {
        double ray_len = std::abs(start(2) - end_voxel(2));
        if (i == 0) {
          central_ray_len = ray_len;
        }
        ++unknown_count;
      }
    }
  }

  if (unknown_count >= extra_samples.size()) {
    voxel_status = MapManager::VoxelStatus::kUnknown;
    return central_ray_len;
  }

  voxel_status = MapManager::VoxelStatus::kFree;
  return -1.0;
}

int main(int argc,char**argv){ros::init(argc,argv,"gbp_ground_probe");ros::NodeHandle nh("/ground_probe_inputs"),priv("~");NativeMap map(nh,priv);map_manager_=&map;ros::AsyncSpinner spinner(1);spinner.start();
voxblox_msgs::FilePath load;load.request.file_path=argv[1];if(!ros::service::call(priv.resolveName("load_map"),load))return 2;
RobotParams robot;if(!robot.loadParams("/gbp_ground_probe/RobotParams"))return 3;robot.setBoundMode(BoundModeType::kExtendedBound);Eigen::Vector3d size;robot.getPlanningSize(size);map.setRobotRadius(size.norm()/2);
std::ifstream points(argv[2]);std::ofstream output(argv[3]);output<<"{\"native_function_on_real_map\":true,\"box_size\":["<<size.x()<<","<<size.y()<<","<<size.z()<<"],\"cases\":[";double x,y;bool first=true;
while(points>>x>>y){Eigen::Vector3d p(x,y,.7);MapManager::VoxelStatus ground;double distance=projectSample(p,ground);p.z()-=(distance-.7);auto box=map.getBoxStatus(p+robot.center_offset,size,true);auto air=map.getVoxelStatus(Eigen::Vector3d(x,y,.456));
if(!first)output<<",";first=false;
output<<"{\"x\":"<<x<<",\"y\":"<<y<<",\"air_at_physical_lidar\":\""<<name(air)<<"\",\"ground\":\""<<name(ground)<<"\",\"projected_x\":"<<p.x()<<",\"projected_y\":"<<p.y()<<",\"projected_z\":"<<p.z()<<",\"box\":\""<<name(box)<<"\"}";}
output<<"]}\n";return 0;}
