#include "topo_planner/topo_planner.h"
#include "rapid_cover_planner/topology_route_gate.h"
#include "rapid_cover_planner/topology_observation.h"
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace topo_planner {
void TopoPlanner::initializeTopology() {
  nh_private_.param("team/topology_enabled", topology_enabled_, false);
  if (!topology_enabled_) return;
  bool shared=false;
  int count=1;
  nh_private_.param("team/shared_sensor_mapping",shared,false);
  nh_private_.param("team/robot_id",topology_robot_,1);
  nh_private_.param("team/robot_count",count,1);
  if(elements_->frontier_map_->frame_id_!="world")
    throw std::runtime_error("phase-1 topology requires a common world frame");
  if (shared || count<2 || topology_robot_<1 || topology_robot_>count)
    throw std::runtime_error("topology mode requires unique robot ID, count>=2, and no remote point-cloud mapping");
  topology_snapshot_pub_=nh_private_.advertise<std_msgs::String>("topology_snapshot",1,true);
  topology_feedback_pub_=nh_private_.advertise<std_msgs::String>("topology_feedback",5);
  topology_command_sub_=nh_private_.subscribe<std_msgs::String>("topology_command",1,&TopoPlanner::topologyCommand,this);
}

void TopoPlanner::publishTopologySnapshot() {
  if (!topology_enabled_) return;
  auto& gm=*elements_->global_topo_map_;
  const auto& g=gm.grid_map_;
  int nx=g.grid_x_num_,ny=g.grid_y_num_;
  if (nx<=0 || ny<=0 || gm.grid_map_image_.cols!=nx || gm.grid_map_image_.rows!=ny) return;
  double now=ros::Time::now().toSec();
  if (now-last_topology_snapshot_<.5) return;
  last_topology_snapshot_=now;
  // This topic is LOCAL to the robot's adapter. The adapter sends only topology,
  // task summaries and state to /team/topology_delta, never this full grid.
  std::ostringstream s;s<<std::setprecision(12);
  s<<"{\"frame\":\"world\",\"stamp\":"<<now<<",\"pose\":["
   <<elements_->current_position_.x()<<","<<elements_->current_position_.y()
   <<"],\"grid\":{\"width\":"<<nx<<",\"height\":"<<ny<<",\"resolution\":"
   <<g.grid_size_<<",\"origin\":["<<g.min_x_<<","<<g.min_y_<<"],\"data\":[";
  bool first=true;
  for(int y=0;y<ny;++y)for(int x=0;x<nx;++x){
    if(!first)s<<",";first=false;
    int value=gm.grid_map_image_.at<unsigned char>(gm.index2CvPoint(perception::Index2D(x,y)));
    auto observed=g.grids_[x][y].status;
    // Morphological skeleton preparation can paint UNKNOWN pixels white.
    // Such pixels are not observation evidence and must never become nav edges.
    s<<rapid_cover_planner::topologyObservedCell(observed==perception::Free,
        observed==perception::Occupied||observed==perception::Empty,value==255);
  }
  s<<"]},\"nodes\":[";
  first=true;
  auto& graph=gm.heriTopo_.graph();
  auto vs=boost::vertices(graph);
  for(auto it=vs.first;it!=vs.second;++it){
    const auto& node=graph[*it];if(node.removed)continue;
    auto index=gm.cvPoint2Index(node.cvPt);
    if(index.x()<0||index.y()<0||index.x()>=nx||index.y()>=ny)continue;
    auto p=gm.index2Point(index);
    if(!first)s<<",";first=false;
    s<<"{\"id\":"<<gm.index2NodeLabel(index)<<",\"p\":["<<p.x()<<","<<p.y()<<"]}";
  }
  s<<"],\"edges\":[";first=true;
  auto es=boost::edges(graph);
  for(auto it=es.first;it!=es.second;++it){
    auto a=boost::source(*it,graph),b=boost::target(*it,graph);
    if(graph[a].removed||graph[b].removed)continue;
    if(!first)s<<",";first=false;
    s<<"["<<gm.cvPoint2NodeLabel(graph[a].cvPt)<<","<<gm.cvPoint2NodeLabel(graph[b].cvPt)<<"]";
  }
  s<<"]}";std_msgs::String msg;msg.data=s.str();topology_snapshot_pub_.publish(msg);
}

void TopoPlanner::topologyCommand(const std_msgs::String::ConstPtr& msg) {
  if(!topology_enabled_)return;
  try{
    boost::property_tree::ptree value;std::istringstream in(msg->data);
    boost::property_tree::read_json(in,value);
    if(value.get<int>("schema")!=1 || value.get<std::string>("frame")!="world" ||
       value.get<int>("robot")!=topology_robot_)return;
    double stamp=value.get<double>("stamp"),now=ros::Time::now().toSec();
    if(!std::isfinite(stamp)||now<stamp||now-stamp>2.)return;
    auto seq=value.get<unsigned long>("command_seq");
    auto session=value.get<std::string>("allocation_session");
    auto mode=value.get<std::string>("mode");
    if(mode!="WAIT"&&mode!="ROUTE")return;
    std::vector<rapid_cover_planner::TopologyPoint> path;
    std::string task;unsigned long version=0;
    if(mode=="ROUTE"){
      task=value.get<std::string>("task");version=value.get<unsigned long>("version");
      for(const auto& row:value.get_child("path")){
        if(row.second.size()!=2)return;
        auto it=row.second.begin();double x=it++->second.get_value<double>(),y=it->second.get_value<double>();
        if(!std::isfinite(x)||!std::isfinite(y))return;path.push_back({x,y});
      }
      if(path.size()>200000)return;
    }
    std::lock_guard<std::mutex> guard(topology_mutex_);
    if((!topology_session_.empty()&&topology_session_!=session)||seq<=topology_command_seq_)return;
    topology_session_=session;topology_command_seq_=seq;topology_command_stamp_=stamp;
    topology_task_=task;topology_version_=version;topology_mode_=mode;topology_route_=path;
  }catch(const std::exception& e){
    ROS_WARN_THROTTLE(2.,"Invalid topology command: %s",e.what());
  }
}

void TopoPlanner::topologyPlanning(control_planner_interface::ExplorerPlannerResult& result) {
  std::lock_guard<std::mutex> guard(topology_mutex_);
  result.paths.clear();
  if(topology_mode_!="ROUTE")return;
  auto grid=executionGrid();
  auto prefix=rapid_cover_planner::topologyPrefix(grid,topology_route_,
    elements_->current_position_.x(),elements_->current_position_.y(),
    tf::getYaw(elements_->current_pose_.orientation),ros::Time::now().toSec(),topology_command_stamp_);
  if(!prefix.points.empty()){
    rapid_cover_planner::Path path;
    for(const auto& p:prefix.points)
      path.emplace_back(p.first,p.second,elements_->current_position_.z());
    control_planner_interface::Path segment;segment.path=wayPoseGeneration(path);
    result.paths.push_back(segment);
  }
  // ACK means native planning accepted a current locally checked prefix.
  // It is NOT a physical stop ACK or proof that the complete route was executed.
  boost::property_tree::ptree f;
  f.put("robot",topology_robot_);f.put("task",topology_task_);f.put("version",topology_version_);
  f.put("command_seq",topology_command_seq_);f.put("allocation_session",topology_session_);
  f.put("status",result.paths.empty()?"BLOCKED":"ACCEPTED");f.put("local_gate",prefix.status);
  std::ostringstream out;boost::property_tree::write_json(out,f,false);
  std_msgs::String msg;msg.data=out.str();topology_feedback_pub_.publish(msg);
}
}
