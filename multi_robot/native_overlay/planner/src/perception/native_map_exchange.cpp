#include "perception/ufomap.h"
#include "rapid_cover_planner/remote_observation.h"
#include <sstream>
#include <iomanip>
#include <stdexcept>

namespace perception {
void Ufomap::initializeNativeMapExchange(){
 bool enabled=false,shared=false;int count=1,id=1;
 nh_private_.param("team/enabled",enabled,false);nh_private_.param("team/shared_sensor_mapping",shared,false);
 nh_private_.param("team/robot_count",count,1);nh_private_.param("team/robot_id",id,1);
 bool topology=false;nh_private_.param("team/topology_enabled",topology,false);
 // Topology collaboration never opens the historical remote cloud subscriber.
 if(topology){if(shared)throw std::runtime_error("topology mode forbids remote cloud mapping");return;}
 // Inactive single behavior, including its original own input callback, is
 // unchanged. The extra source only exists for the explicit two-robot mode.
 if(!enabled||!shared||count!=2)return;
 native_map_shared_=true;remote_peer_prefix_="robot_"+std::to_string(id==1?2:1)+"/";
 nh_private_.param("team/remote_map_period_s",remote_map_period_,.2);
 remote_cloud_sub_.reset(new message_filters::Subscriber<sensor_msgs::PointCloud2>(nh_,"remote_point_cloud",5));
 remote_odom_sub_.reset(new message_filters::Subscriber<nav_msgs::Odometry>(nh_,"remote_sensor_odometry",30));
 remote_sync_.reset(new message_filters::Synchronizer<SyncPolicyRemoteCloudOdom>(SyncPolicyRemoteCloudOdom(30),*remote_cloud_sub_,*remote_odom_sub_));
 remote_sync_->registerCallback(boost::bind(&Ufomap::remotePointCloudOdomCallback,this,_1,_2));
}

void Ufomap::remotePointCloudOdomCallback(const sensor_msgs::PointCloud2::ConstPtr&scan,const nav_msgs::OdometryConstPtr&odom){
 std::lock_guard<std::mutex> source_guard(remote_source_mutex_);
 if(!native_map_shared_||!rapid_cover_planner::validRemoteObservation(*scan,*odom,remote_peer_prefix_,frame_id_)){++remote_rejected_;return;}
 double stamp=scan->header.stamp.toSec();
 if(stamp<=last_remote_stamp_){++remote_rejected_;return;}
 if(stamp-last_remote_stamp_<remote_map_period_-1e-6){++remote_throttled_;return;}
 // This pose is the REMOTE ray origin. Never overwrite the own sensor/base
 // state used by native local frontier/FOV tests, clearing or motion planning.
 ufo::math::Pose6 source_pose;const auto&p=odom->pose.pose.position;const auto&q=odom->pose.pose.orientation;
 source_pose.translation()=ufo::math::Vector3(p.x,p.y,p.z);
 double norm=std::sqrt(q.w*q.w+q.x*q.x+q.y*q.y+q.z*q.z);
 source_pose.rotation().w()=q.w/norm;source_pose.rotation().x()=q.x/norm;source_pose.rotation().y()=q.y/norm;source_pose.rotation().z()=q.z/norm;
 ufo::math::Pose6 source_base;
 if(clear_robot_enabled_){
  try{auto t=tf_buffer_.lookupTransform(odom->child_frame_id,remote_peer_prefix_+"base_link",odom->header.stamp);source_base=source_pose*ufomap_ros::rosToUfo(t.transform);}
  catch(tf2::TransformException&){++remote_rejected_;return;}
 }
 pcl::PointCloud<pcl::PointXYZ>::Ptr input(new pcl::PointCloud<pcl::PointXYZ>);pcl::fromROSMsg(*scan,*input);
 pcl::VoxelGrid<pcl::PointXYZ> filter;filter.setLeafSize(scan_voxel_size_,scan_voxel_size_,scan_voxel_size_);filter.setInputCloud(input);pcl::PointCloud<pcl::PointXYZ>filtered;filter.filter(filtered);
 ufo::map::PointCloud points;for(auto const&v:filtered)if(std::isfinite(v.x)&&std::isfinite(v.y)&&std::isfinite(v.z))points.push_back(ufo::map::Point3(v.x,v.y,v.z));points.transform(source_pose);
 std::lock_guard<std::mutex> map_guard(map_mutex_);
 ufo::map::KeySet keys;ufo::map::PointCloud world;
 for(auto const&v:points)if(keys.insert(map_.toKey(v,0)).second)world.push_back(map_.toCoord(map_.toKey(v,0),0));
 if(insert_discrete_)map_.insertPointCloudDiscrete(source_pose.translation(),world,max_range_,insert_depth_,simple_ray_casting_,early_stopping_,false);
 else map_.insertPointCloud(source_pose.translation(),world,max_range_,insert_depth_,simple_ray_casting_,early_stopping_,false);
 if(clear_robot_enabled_){
  ufo::geometry::AABB body(ufo::map::Point3(source_base.x()-sensor_height_,source_base.y()-sensor_height_,source_base.z()-robot_bottom_),ufo::map::Point3(source_base.x()+sensor_height_,source_base.y()+sensor_height_,source_base.z()+robot_height_));
  map_.setValueVolume(body,map_.getClampingThresMin(),clearing_depth_);
 }
 last_remote_stamp_=stamp;++remote_frames_;last_remote_origin_[0]=p.x;last_remote_origin_[1]=p.y;last_remote_origin_[2]=p.z;last_remote_frame_=odom->child_frame_id;
}

std::string Ufomap::nativeMapSyncJson()const{
 std::lock_guard<std::mutex>guard(remote_source_mutex_);std::ostringstream s;
 s<<std::setprecision(12)<<"{\"enabled\":"<<(native_map_shared_?"true":"false")<<",\"remote_frames\":"<<remote_frames_<<",\"rejected\":"<<remote_rejected_<<",\"throttled\":"<<remote_throttled_<<",\"stamp\":"<<last_remote_stamp_<<",\"source_frame\":\""<<last_remote_frame_<<"\",\"origin\":["<<last_remote_origin_[0]<<","<<last_remote_origin_[1]<<","<<last_remote_origin_[2]<<"]}";return s.str();
}
}
