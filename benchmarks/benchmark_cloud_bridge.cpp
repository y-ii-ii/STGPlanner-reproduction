#include <ros/ros.h>
#include <sensor_msgs/PointCloud2.h>
#include <tf2_ros/transform_listener.h>
#include <tf2_sensor_msgs/tf2_sensor_msgs.h>
class Bridge {
  ros::NodeHandle nh_;
  tf2_ros::Buffer buffer_;
  tf2_ros::TransformListener listener_;
  ros::Publisher scan_,terrain_;
  ros::Subscriber scan_sub_,terrain_sub_;
public:
  Bridge():listener_(buffer_) {
    scan_=nh_.advertise<sensor_msgs::PointCloud2>("/benchmark/registered_cloud",1);
    terrain_=nh_.advertise<sensor_msgs::PointCloud2>("/benchmark/terrain_map",1);
    scan_sub_=nh_.subscribe<sensor_msgs::PointCloud2>("/registered_point_cloud",1,[this](const sensor_msgs::PointCloud2::ConstPtr& m){convert(m,scan_);});
    terrain_sub_=nh_.subscribe<sensor_msgs::PointCloud2>("/terrain_map",1,[this](const sensor_msgs::PointCloud2::ConstPtr& m){convert(m,terrain_);});
  }
  void convert(const sensor_msgs::PointCloud2::ConstPtr& m,ros::Publisher& pub) {
    try {
      auto transform=buffer_.lookupTransform("world",m->header.frame_id,m->header.stamp,ros::Duration(.2));
      sensor_msgs::PointCloud2 output;tf2::doTransform(*m,output,transform);pub.publish(output);
    } catch(const tf2::TransformException& error) {ROS_WARN_THROTTLE(5,"Benchmark cloud transform: %s",error.what());}
  }
};
int main(int argc,char** argv){ros::init(argc,argv,"benchmark_cloud_bridge");Bridge bridge;ros::spin();}
