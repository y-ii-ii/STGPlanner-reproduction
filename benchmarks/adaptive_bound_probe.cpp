#include <adaptive_obb/adaptive_obb.h>
#include <voxblox_msgs/FilePath.h>
#include <fstream>
int main(int argc,char**argv){
  ros::init(argc,argv,"gbp_bound_probe");ros::NodeHandle nh("/bound_probe_inputs"),priv("~");
  MapManagerVoxblox<MapManagerVoxbloxServer,MapManagerVoxbloxVoxel> map(nh,priv);ros::AsyncSpinner spinner(1);spinner.start();
  voxblox_msgs::FilePath load;load.request.file_path=argv[1];if(!ros::service::call(priv.resolveName("load_map"),load))return 2;
  // Match upstream Rrg ownership: the declared destructor has no definition.
  auto* obb=new AdaptiveObb(&map);if(!obb->loadParams("/gbp_bound_probe/AdaptiveObbParams"))return 3;
  std::ofstream out(argv[2]);out<<"{\"native_adaptive_obb\":true,\"initial_min\":[-10,-10,-0.75],\"initial_max\":[10,10,0.75],\"cases\":[";
  std::vector<Eigen::Vector3d> poses{{18.4979,55.4525,.7},{18.5,60,.7},{13,54,.7},{0,0,.7},{-20,20,.7},{4,45,.7}};
  bool first=true;for(const auto& pos:poses){Eigen::Vector3d low(-10,-10,-.75),high(10,10,.75),rotation,mean,sd;
    obb->constructBoundingBox(pos,low,high,rotation,mean,sd);
    Eigen::Matrix3d r=(Eigen::AngleAxisd(rotation[0],Eigen::Vector3d::UnitZ())*Eigen::AngleAxisd(rotation[1],Eigen::Vector3d::UnitY())*Eigen::AngleAxisd(rotation[2],Eigen::Vector3d::UnitX())).toRotationMatrix();
    Eigen::Vector3d q=r*(Eigen::Vector3d(18.5,64,.7)-pos);
    bool root_xy=low[0]<=0&&high[0]>=0&&low[1]<=0&&high[1]>=0;
    bool ahead=(q.array()>=low.array()).all()&&(q.array()<=high.array()).all();
    if(!first)out<<",";first=false;
    out<<"{\"position\":["<<pos.x()<<","<<pos.y()<<","<<pos.z()<<"],\"min\":["<<low.x()<<","<<low.y()<<","<<low.z()<<"],\"max\":["<<high.x()<<","<<high.y()<<","<<high.z()<<"],\"root_inside_xy\":"<<(root_xy?"true":"false")<<",\"corridor_target_inside\":"<<(ahead?"true":"false")<<"}";
  }out<<"]}\n";return 0;
}
