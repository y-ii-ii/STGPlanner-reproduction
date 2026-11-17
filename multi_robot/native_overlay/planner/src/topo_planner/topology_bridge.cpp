#include "topo_planner/topo_planner.h"
#include "rapid_cover_planner/topology_route_gate.h"
#include "rapid_cover_planner/topology_observation.h"
#include "rapid_cover_planner/own_observation_union.h"
#include "rapid_cover_planner/body_route.h"
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
  topology_command_sub_=nh_private_.subscribe<std_msgs::String>("topology_command",10,&TopoPlanner::topologyCommand,this);
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
    // GlobalTopoManager initializes its unobserved padding as Empty, unlike
    // Map2DManager's observed terrain holes. Only Free/Occupied are evidence here.
    s<<rapid_cover_planner::topologyObservedCell(observed==perception::Free,
        observed==perception::Occupied,value==255);
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
    if(value.get<int>("schema")!=2 || value.get<std::string>("frame")!="world" ||
       value.get<int>("robot")!=topology_robot_)return;
    double stamp=value.get<double>("stamp"),now=ros::Time::now().toSec();
    if(!std::isfinite(stamp)||now<stamp||(value.get<std::string>("mode")=="ROUTE"&&now-stamp>2.))return;
    auto seq=value.get<unsigned long>("command_seq");
    auto session=value.get<std::string>("allocation_session");
    auto mode=value.get<std::string>("mode");
    if(mode!="STOP"&&mode!="ROUTE")return;
    std::vector<rapid_cover_planner::TopologyPoint> path;
    std::string task;unsigned long version=0,dispatch=0;
    rapid_cover_planner::NativeTaskScope scope;
    if(mode=="ROUTE"){
      task=value.get<std::string>("task");version=value.get<unsigned long>("version");
      dispatch=value.get<unsigned long>("dispatch_id");scope.active=true;
      size_t scope_cells=0;
      for(const auto& patch:value.get_child("scopes")){
        rapid_cover_planner::TaskPatch out;auto origin=patch.second.get_child("origin");
        if(origin.size()!=2)return;auto it=origin.begin();
        out.x0=it++->second.get_value<double>();out.y0=it->second.get_value<double>();
        out.resolution=patch.second.get<double>("resolution");
        if(!std::isfinite(out.x0)||!std::isfinite(out.y0)||!std::isfinite(out.resolution)||out.resolution<=0
           ||std::abs(out.x0)>1e7||std::abs(out.y0)>1e7||out.resolution>1000)return;
        auto read_runs=[&](const std::string&name,std::vector<rapid_cover_planner::TaskRun>&runs){
          for(const auto& row:patch.second.get_child(name)){
            if(row.second.size()!=3||runs.size()>10000)throw std::runtime_error("invalid task RLE");
            auto a=row.second.begin();int y=a++->second.get_value<int>();
            int lo=a++->second.get_value<int>(),hi=a->second.get_value<int>();
            if(lo>hi||std::abs(double(lo))>1e7||std::abs(double(hi))>1e7||std::abs(double(y))>1e7)
              throw std::runtime_error("invalid task run range");
            scope_cells+=size_t(hi-lo)+1;
            if(scope_cells>100000)throw std::runtime_error("task geometry exceeds cell budget");
            runs.push_back({y,lo,hi});
          }
        };
        read_runs("unknown_runs",out.unknown);read_runs("portal_runs",out.portals);
        if(out.unknown.empty()||out.portals.empty())return;
        scope.patches.push_back(out);
      }
      if(scope.patches.empty()||scope.patches.size()>100)return;
      for(const auto& row:value.get_child("path")){
        if(row.second.size()!=2)return;
        auto it=row.second.begin();double x=it++->second.get_value<double>(),y=it->second.get_value<double>();
        if(!std::isfinite(x)||!std::isfinite(y))return;path.push_back({x,y});
      }
      if(path.size()>200000)return;
    }
    const std::string scope_digest=mode=="ROUTE"?value.get<std::string>("scope_digest"):"";
    if(mode=="ROUTE"&&scope_digest.size()!=64)return;
    std::lock_guard<std::mutex> guard(topology_mutex_);
    if((!topology_session_.empty()&&topology_session_!=session)||seq<=topology_command_seq_)return;
    topology_session_=session;topology_command_seq_=seq;topology_command_stamp_=stamp;
    topology_task_=task;topology_version_=version;topology_mode_=mode;topology_route_=path;
    topology_dispatch_=dispatch;topology_scope_=scope;
    topology_scope_digest_=scope_digest;
    if(mode=="STOP"&&value.get<std::string>("reason","")=="EXECUTION_STALL"){
      auto stop_id=value.get<std::string>("stop_id","");
      if(topology_evidence_valid_&&stop_id!=topology_recovery_stop_id_){
        // Fresh-odometry stagnation feeds the existing native recovery entry.
        // Defer the target, preserve pending work, and never report completion.
        planner_->deferExecutionFrontier(topology_evidence_x_,topology_evidence_y_,1.2,8.);
        topology_recovery_stop_id_=stop_id;
      }
    }
  }catch(const std::exception& e){
    ROS_WARN_THROTTLE(2.,"Invalid topology command: %s",e.what());
  }
}

void TopoPlanner::topologyPlanning(control_planner_interface::ExplorerPlannerResult& result) {
  std::lock_guard<std::mutex> guard(topology_mutex_);
  result.paths.clear();
  auto& gm=*elements_->global_topo_map_;
  // Keep the final velocity shield's own fine map alive during STOP/WAIT too.
  auto grid=executionGrid();
  const int terrain_start=grid.footprint(elements_->current_position_.x(),elements_->current_position_.y(),tf::getYaw(elements_->current_pose_.orientation));
  const auto own_free_fill=rapid_cover_planner::combineOwnObservations(grid,[&](double x,double y){
    auto state=gm.grid_map_.getStatusInMap2D(perception::Point2D(x,y));
    return state==perception::Free?0:(state==perception::Occupied?1:2);
  });
  double map_stamp;{std::lock_guard<std::mutex> guard(elements_->map_2d_manager_->map_2d_update_mutex_);map_stamp=elements_->map_2d_manager_->last_observation_stamp_.toSec();}
  if(!grid.data.empty()){
    nav_msgs::OccupancyGrid m;m.header.frame_id="world";m.header.stamp.fromSec(map_stamp);
    m.info.resolution=grid.resolution;m.info.width=grid.width;m.info.height=grid.height;
    m.info.origin.position.x=grid.x0;m.info.origin.position.y=grid.y0;m.info.origin.orientation.w=1;
    m.data.assign(grid.data.begin(),grid.data.end());execution_grid_pub_.publish(m);
  }
  if(topology_mode_!="ROUTE")return;
  gm.task_scope_=topology_scope_;
  struct Reset {perception::GlobalTopoManager& gm;~Reset(){gm.task_scope_.active=false;}} reset{gm};
  double observation_stamp;{std::lock_guard<std::mutex> guard(elements_->map_2d_manager_->map_2d_update_mutex_);
    observation_stamp=elements_->map_2d_manager_->last_observation_stamp_.toSec();}
  auto counts=rapid_cover_planner::taskObservationCounts(gm.task_scope_.patches,[&](double x,double y){
    perception::Point2D p(x,y);if(!gm.grid_map_.isInMapRange2D(p))return false;
    auto status=gm.grid_map_.getStatusInMap2D(p);
    return status==perception::Free||status==perception::Occupied;
  });
  double observed_now=ros::Time::now().toSec();
  if(counts.second&&counts.first==counts.second&&observed_now>=observation_stamp&&observed_now-observation_stamp<=1.){
    // The assignee may finish a task authored by its peer. No peer grid/cloud
    // is fused: completion is certified against THIS robot's observed map.
    boost::property_tree::ptree f;f.put("source","planner");f.put("status","OBSERVATION_COMPLETED");
    f.put("robot",topology_robot_);f.put("task",topology_task_);f.put("version",topology_version_);
    f.put("dispatch_id",topology_dispatch_);f.put("allocation_session",topology_session_);
    f.put("scope_digest",topology_scope_digest_);f.put("required_cells",counts.second);f.put("observed_cells",counts.first);
    f.put("map_stamp",observation_stamp);
    std::ostringstream out;boost::property_tree::write_json(out,f,false);std_msgs::String msg;msg.data=out.str();
    topology_feedback_pub_.publish(msg);return; // Stop barrier still required before releasing execution.
  }
  for(auto& patch:gm.task_scope_.patches)rapid_cover_planner::fillTaskApproach(patch,[&](double x,double y){
    perception::Point2D p(x,y);if(!gm.grid_map_.isInMapRange2D(p))return false;
    auto index=gm.point2Index(p);
    return gm.grid_map_.getStatusInMap2D(p)==perception::Free&&gm.grid_map_image_.at<unsigned char>(gm.index2CvPoint(index))==255;
  });
  auto valid=[&](int label){
    return label>=0&&boost::vertex_by_label(label,gm.heriTopo_)<boost::num_vertices(gm.heriTopo_)
      &&!gm.heriTopo_[label].removed&&!gm.heriTopo_[label].confirmed;
  };
  auto allowed=[&](int label){
    auto p=gm.index2Point(gm.nodeLabel2Index(label));
    int branch=gm.heriTopo_[label].parent_branch_label;
    return gm.task_scope_.allows(p.x(),p.y())&&branch>=0
      &&boost::vertex_by_label(branch,gm.heriTopo_)<boost::num_vertices(gm.heriTopo_);
  };
  using History=std::vector<utils::MissedBranchMap>;
  rapid_cover_planner::ScopedPending<utils::NodeQueue,History> view(
    gm.local_frontier_labels_,planner_->history_missed_branches_,gm.task_suppressed_frontiers_,valid,allowed);
  // Native states 1/2/3 are entered with a reversible task-filtered view.
  // State 4 filters UFO frontier evidence; state 5 keeps the original planner.
  planner_->no_frontier_left_=false;
  std::string local_task=topology_session_+"/"+topology_task_+"/"+std::to_string(topology_version_);
  if(local_task!=topology_local_task_key_){
    topology_evidence_valid_=false;
    planner_->during_relocate_=false;planner_->is_frontier_guiding_=false;
    planner_->is_frontier_robot_same_=false;planner_->last_target_node_=-1;
    planner_->tour_topo_path_.clear();topology_local_task_key_=local_task;
  }
  if(planner_->current_explore_branch_<0||
      boost::vertex_by_label(planner_->current_explore_branch_,gm.heriTopo_)>=boost::num_vertices(gm.heriTopo_))
    planner_->current_explore_branch_=gm.home_node_label_;
  bool native_ready=planner_->current_explore_branch_>=0&&
    boost::vertex_by_label(planner_->current_explore_branch_,gm.heriTopo_)<boost::num_vertices(gm.heriTopo_);
  if(native_ready)planner_->Initialize(elements_->current_position_);
  else {planner_->tour_topo_path_.clear();planner_->tsp_path_.clear();planner_->native_task_trace_.clear();
    planner_->is_frontier_guiding_=false;planner_->native_guide_evidence_valid_=false;}
  // The native path generator may prune its tour queue. Capture task evidence
  // before planning, rather than accidentally judging the pruned queue.
  bool topology_evidence=false;
  if(!planner_->tour_topo_path_.empty()){
    auto target=gm.index2Point(gm.nodeLabel2Index(planner_->tour_topo_path_.back()));
    topology_evidence=gm.task_scope_.allows(target.x(),target.y());
    if(topology_evidence){topology_evidence_valid_=true;topology_evidence_x_=target.x();topology_evidence_y_=target.y();}
  }
  if(planner_->during_relocate_)for(auto label:gm.local_frontier_labels_)
    if(valid(label)&&allowed(label)&&gm.heriTopo_[label].parent_branch_label==planner_->current_explore_branch_)
      topology_evidence=true;
  bool native_ok=false;
  if(!planner_->tour_topo_path_.empty()||planner_->is_frontier_guiding_)
    planner_->planning(elements_->current_pose_,elements_->forward_directory_,native_ok);
  if(!native_ok||planner_->tsp_path_.empty()){
    planner_->native_task_trace_.push_back(4);
    planner_->getSuitableTourPoints(elements_->current_position_);
    planner_->is_frontier_guiding_=true;
    if(!planner_->tour_points_.empty())
      planner_->planning(elements_->current_pose_,elements_->forward_directory_,native_ok);
  }
  bool evidence_ok=false;
  if(native_ok&&!planner_->tsp_path_.empty()){
    if(planner_->is_frontier_guiding_&&planner_->native_guide_evidence_valid_)
      evidence_ok=gm.task_scope_.allowsBoundary(planner_->native_guide_evidence_.x(),planner_->native_guide_evidence_.y());
    else evidence_ok=topology_evidence;
  }
  std::vector<rapid_cover_planner::TopologyPoint> route;
  if(evidence_ok&&planner_->is_frontier_guiding_){topology_evidence_valid_=true;
    topology_evidence_x_=planner_->native_guide_evidence_.x();topology_evidence_y_=planner_->native_guide_evidence_.y();}
  std::string selection="FUSED_GRAPH_TRANSIT";
  if(evidence_ok){for(const auto& p:planner_->tsp_path_)route.push_back({p.x(),p.y()});selection="NATIVE_TASK_STATES";}
  else {
    route=topology_route_; // Only this task; do not bypass native stall feedback.
    if(!route.empty()&&planner_->isExecutionDeferred(route.back().first,route.back().second)){
      route.clear();selection="DEFERRED_TASK";
    }
  }
  const double yaw=tf::getYaw(elements_->current_pose_.orientation);
  double now=ros::Time::now().toSec();
  auto prefix=rapid_cover_planner::bodyRoute(grid,route,elements_->current_position_.x(),elements_->current_position_.y(),yaw);
  if(now<map_stamp||now-map_stamp>1.||now-topology_command_stamp_>2.){prefix.poses.clear();prefix.status="STALE_MAP";}
  if(!prefix.poses.empty()){
    control_planner_interface::Path segment;
    for(const auto& p:prefix.poses){geometry_msgs::Pose v;v.position.x=p.x;v.position.y=p.y;v.position.z=elements_->current_position_.z();v.orientation=tf::createQuaternionMsgFromYaw(p.yaw);segment.path.push_back(v);}
    result.paths.push_back(segment);
    boost::property_tree::ptree lease;
    lease.put("schema",2);lease.put("allocation_session",topology_session_);
    lease.put("robot",topology_robot_);lease.put("task",topology_task_);
    lease.put("version",topology_version_);lease.put("dispatch_id",topology_dispatch_);
    lease.put("command_seq",topology_command_seq_);lease.put("stamp",topology_command_stamp_);
    lease.put("body_margin_m",prefix.margin);
    std::ostringstream encoded;boost::property_tree::write_json(encoded,lease,false);
    result.execution_lease=encoded.str();
  }
  // ACK means native planning accepted a current locally checked prefix.
  // It is NOT a physical stop ACK or proof that the complete route was executed.
  boost::property_tree::ptree f;
  f.put("robot",topology_robot_);f.put("task",topology_task_);f.put("version",topology_version_);
  f.put("command_seq",topology_command_seq_);f.put("allocation_session",topology_session_);
  f.put("status",result.paths.empty()?"BLOCKED":"ACCEPTED");f.put("local_gate",prefix.status);
  f.put("source","planner");f.put("selection",selection);f.put("dispatch_id",topology_dispatch_);
  f.put("terrain_start_footprint",terrain_start);f.put("own_free_fill_cells",own_free_fill);
  f.put("combined_start_footprint",grid.footprint(elements_->current_position_.x(),elements_->current_position_.y(),yaw));
  f.put("body_search_expanded",prefix.expanded);f.put("approach_offset_m",prefix.goal_offset);
  f.put("body_margin_m",prefix.margin);
  f.put("planned_arc_m",prefix.arc);
  f.put("body_route_method",prefix.method);
  if(result.paths.empty()&&!route.empty())planner_->deferExecutionFrontier(route.back().first,route.back().second,1.0,15.);
  boost::property_tree::ptree trace;for(int state:planner_->native_task_trace_){boost::property_tree::ptree n;n.put("",state);trace.push_back({"",n});}
  f.add_child("native_states",trace);
  std::ostringstream out;boost::property_tree::write_json(out,f,false);
  std_msgs::String msg;msg.data=out.str();topology_feedback_pub_.publish(msg);
}
}
