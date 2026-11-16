#pragma once
#include <ros/ros.h>
#include <nav_msgs/OccupancyGrid.h>
#include <mutex>
#include <cmath>
#include <limits>
#include <algorithm>

namespace rapid_cover_planner {
// Preferences are applied to ORIGINAL native frontier/branch choices.
// They never erase the native pending-frontier set or replace its planner.
class NativeTeamPolicy {
 ros::Subscriber sub_;nav_msgs::OccupancyGrid map_;mutable std::mutex mutex_;
 ros::WallTime received_;bool enabled_=false;int id_=1,count_=1;
public:
 struct Snapshot{
  nav_msgs::OccupancyGrid map;bool active=false,fresh=false;int id=1;
  unsigned epoch()const{return map.info.map_load_time.sec;}
  int owner(double x,double y)const{
   if(!active)return id;if(!fresh||map.data.empty())return 0;
   int xx=std::floor((x-map.info.origin.position.x)/map.info.resolution),yy=std::floor((y-map.info.origin.position.y)/map.info.resolution);
   return xx>=0&&yy>=0&&xx<int(map.info.width)&&yy<int(map.info.height)?map.data[yy*map.info.width+xx]:0;
  }
  int priority(double x,double y)const{int o=owner(x,y);return !active||o==id?0:o==0?1:2;}
 };
 Snapshot capture()const{std::lock_guard<std::mutex>g(mutex_);Snapshot s;s.map=map_;s.active=active();s.id=id_;s.fresh=!map_.data.empty()&&(ros::WallTime::now()-received_).toSec()<=3.;return s;}
 void init(ros::NodeHandle&nh,ros::NodeHandle&priv){
  priv.param("team/enabled",enabled_,false);priv.param("team/robot_id",id_,1);priv.param("team/robot_count",count_,1);
  bool topology=false;priv.param("team/topology_enabled",topology,false);
  if(topology)enabled_=false; // Do not mix the historical 4m ownership channel into G_task.
  if(active())sub_=nh.subscribe("/team/native_ownership",1,&NativeTeamPolicy::receive,this);
 }
 bool active()const{return enabled_&&count_>1;}
 int robotId()const{return id_;}
 void receive(const nav_msgs::OccupancyGrid::ConstPtr&m){
  if(m->header.frame_id!="world"||!std::isfinite(m->info.resolution)||m->info.resolution<=0||m->data.size()!=m->info.width*m->info.height||std::abs(m->info.origin.orientation.w-1)>1e-6)return;
  std::lock_guard<std::mutex> g(mutex_);
  if(!map_.data.empty()&&m->info.map_load_time<map_.info.map_load_time)return;
  if(!map_.data.empty()&&m->info.map_load_time==map_.info.map_load_time&&m->data!=map_.data)return;
  map_=*m;received_=ros::WallTime::now();
 }
 int owner(double x,double y)const{
  if(!active())return id_;
  std::lock_guard<std::mutex> g(mutex_);
  if(map_.data.empty()||(ros::WallTime::now()-received_).toSec()>3.)return 0;
  int xx=std::floor((x-map_.info.origin.position.x)/map_.info.resolution),yy=std::floor((y-map_.info.origin.position.y)/map_.info.resolution);
  return xx>=0&&yy>=0&&xx<int(map_.info.width)&&yy<int(map_.info.height)?map_.data[yy*map_.info.width+xx]:0;
 }
 int priority(double x,double y)const{int o=owner(x,y);return !active()||o==id_?0:o==0?1:2;}
 unsigned epoch()const{std::lock_guard<std::mutex>g(mutex_);return map_.info.map_load_time.sec;}
};

// Preserve all other pending branches when switching the active native branch.
// The selected branch becomes active, so remove only its pending duplicate.
template<class History,class Labels>
void preservePendingOnSwitch(History&history,int old_branch,int selected,const Labels&old_pending){
 if(old_branch==selected)return;
 for(auto it=history.begin();it!=history.end();){it->erase(selected);if(it->empty())it=history.erase(it);else ++it;}
 if(old_pending.empty())return;
 for(auto&frame:history){auto found=frame.find(old_branch);if(found!=frame.end()){found->second.frontiers.insert(old_pending.begin(),old_pending.end());return;}}
 typename History::value_type pending;pending[old_branch].frontiers.insert(old_pending.begin(),old_pending.end());history.push_back(pending);
}
}
