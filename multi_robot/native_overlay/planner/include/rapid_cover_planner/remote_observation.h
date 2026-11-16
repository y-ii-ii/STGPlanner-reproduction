#pragma once
#include <sensor_msgs/PointCloud2.h>
#include <nav_msgs/Odometry.h>
#include <cmath>
#include <string>
namespace rapid_cover_planner {
inline bool validRemoteObservation(const sensor_msgs::PointCloud2&cloud,const nav_msgs::Odometry&odom,const std::string&peer,const std::string&world){
 const auto&p=odom.pose.pose.position;const auto&q=odom.pose.pose.orientation;
 double norm=q.w*q.w+q.x*q.x+q.y*q.y+q.z*q.z;
 return !peer.empty()&&cloud.header.frame_id.compare(0,peer.size(),peer)==0&&odom.child_frame_id.compare(0,peer.size(),peer)==0&&odom.header.frame_id==world&&cloud.header.stamp==odom.header.stamp&&std::isfinite(p.x)&&std::isfinite(p.y)&&std::isfinite(p.z)&&std::isfinite(norm)&&norm>.99&&norm<1.01;
}
}
