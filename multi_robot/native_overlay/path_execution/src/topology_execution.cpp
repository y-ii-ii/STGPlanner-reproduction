#include "path_execution/path_execution.h"
#include <cmath>

namespace path_execution {
void PathExecution::initializeTopologyExecution(){
  nh_private_.param("team/topology_enabled",topology_mode_,false);
  if(!topology_mode_)return;
  nh_private_.param("team/robot_id",topology_robot_,1);
  std::string root="/robot_"+std::to_string(topology_robot_);
  topology_issuer_="executor/"+std::to_string(ros::WallTime::now().toNSec());
  topology_permit_pub_=nh_.advertise<std_msgs::String>(root+"/topology/execution_permit",5);
  topology_feedback_pub_=nh_.advertise<std_msgs::String>(root+"/topology/execution_feedback",10);
  topology_certified_pub_=nh_.advertise<std_msgs::String>(root+"/topology/certified_path",1);
  topology_command_sub_=nh_.subscribe<std_msgs::String>(root+"/topo_planner_node/topology_command",5,&PathExecution::topologyControl,this);
  topology_feedback_sub_=nh_.subscribe<std_msgs::String>(root+"/topology/execution_feedback",20,&PathExecution::topologyFeedback,this);
  topology_watchdog_=nh_.createWallTimer(ros::WallDuration(.05),&PathExecution::topologyWatchdog,this);
  std_msgs::Bool stop;stop.data=true;stop_move_pub_.publish(stop);
}
geometry_msgs::Pose PathExecution::poseSnapshot(){
  std::lock_guard<std::mutex> guard(pose_mutex_);return current_pose_;
}
void PathExecution::topologyControl(const std_msgs::String::ConstPtr&msg){
  try{
    auto p=interface::jsonTree(msg->data);
    if(p.get<int>("schema")!=2||p.get<int>("robot")!=topology_robot_||p.get<std::string>("frame")!="world")return;
    auto session=p.get<std::string>("allocation_session"),mode=p.get<std::string>("mode");
    auto seq=p.get<unsigned long>("command_seq");double stamp=p.get<double>("stamp"),now=ros::Time::now().toSec();
    if(!std::isfinite(stamp)||now<stamp||(mode=="ROUTE"&&now-stamp>2.)||(mode!="STOP"&&mode!="ROUTE"))return;
    interface::ExecutionLease lease;if(mode=="ROUTE")lease=interface::readExecutionLease(msg->data);
    std::lock_guard<std::mutex> guard(topology_mutex_);
    if((!topology_session_.empty()&&topology_session_!=session)||seq<=topology_command_seq_)return;
    topology_session_=session;topology_command_seq_=seq;topology_mode_text_=mode;topology_received_=interface::executionMonotonicNow();
    if(mode=="STOP"){
      topology_stop_proofs_.beginStop(p.get<std::string>("stop_id",""));
      topology_stop_pending_=true;topology_goal_active_=false;
      std_msgs::Bool stop;stop.data=true;stop_move_pub_.publish(stop);
    }else{
      if(lease.token()!=topology_current_.token()){
        topology_stop_pending_=false;
        topology_stop_proofs_.beginMotion();
      }
      topology_current_=lease;
    }
  }catch(const std::exception& e){ROS_WARN_THROTTLE(2.,"Executor command rejected: %s",e.what());}
}
void PathExecution::topologyFeedback(const std_msgs::String::ConstPtr&msg){
  try{
    auto p=interface::jsonTree(msg->data);
    std::lock_guard<std::mutex> guard(topology_mutex_);
    if(p.get<std::string>("source")!="velocity_gate"||p.get<std::string>("status")!="STOPPED"||
       p.get<int>("robot")!=topology_robot_||p.get<std::string>("allocation_session")!=topology_session_)return;
    for(const auto&id:p.get_child("request_ids")){
      auto request=id.second.get_value<std::string>();
      if(interface::stoppedProofMatches(msg->data,request,topology_robot_,topology_session_))
        topology_stop_proofs_.record(request,p.get<std::string>("stop_id"),msg->data,p.get<double>("stamp"));
    }
  }catch(const std::exception&){}
}
bool PathExecution::topologyAuthorize(const control_planner_interface::VehicleExecuteGoal&goal){
  try{
    auto lease=interface::readExecutionLease(goal.execution_lease);
    double body_margin=interface::jsonTree(goal.execution_lease).get<double>("body_margin_m",.15);
    if(body_margin!=.05&&body_margin!=.15)return false;
    double now=ros::Time::now().toSec();
    if(goal.header.frame_id!="world"||goal.paths.empty()||now<goal.header.stamp.toSec()||now-goal.header.stamp.toSec()>2.||goal.header.stamp.toSec()<lease.stamp)return false;
    bool points=false;
    for(const auto&s:goal.paths)for(const auto&p:s.path){
      if(!std::isfinite(p.position.x)||!std::isfinite(p.position.y)||!std::isfinite(p.position.z))return false;
      points=true;
    }
    if(!points)return false;
    std::lock_guard<std::mutex> guard(topology_mutex_);
    if(topology_stop_pending_||topology_mode_text_!="ROUTE"||
       !interface::executionLeaseMatches(lease,topology_current_,now)||
       interface::executionMonotonicNow()-topology_received_>1.5)return false;
    if(topology_goal_.token()==lease.token()&&goal.header.seq<=last_topology_goal_seq_)return false;
    if(topology_goal_.token()!=lease.token())topology_path_published_=false;
    topology_stop_proofs_.beginMotion();
    topology_goal_=lease;last_topology_goal_seq_=goal.header.seq;topology_body_margin_=body_margin;
    topology_goal_active_=true;topology_goal_began_=interface::executionMonotonicNow();
    return true;
  }catch(const std::exception&){return false;}
}
bool PathExecution::topologyKeepRunning(){
  std::lock_guard<std::mutex> guard(topology_mutex_);
  return topologyKeepRunningLocked(interface::executionMonotonicNow());
}
void PathExecution::topologyRejected(const control_planner_interface::VehicleExecuteGoal&goal){
  // Preserve the rejected request's identity. A stale planner result must not
  // defer/cancel unrelated current work; coordinator checks the exact generation.
  try{
    auto lease=interface::readExecutionLease(goal.execution_lease);
    std::lock_guard<std::mutex> guard(topology_mutex_);
    boost::property_tree::ptree p;p.put("source","executor");p.put("status","EXECUTOR_REJECTED");
    p.put("robot",topology_robot_);p.put("task",lease.task);p.put("version",lease.version);
    p.put("dispatch_id",lease.dispatch);p.put("allocation_session",lease.session);
    p.put("goal_command_seq",lease.sequence);p.put("current_command_seq",topology_current_.sequence);
    p.put("goal_token",lease.token());p.put("current_token",topology_current_.token());
    p.put("mode",topology_mode_text_);p.put("stop_pending",topology_stop_pending_);
    p.put("goal_stamp",goal.header.stamp.toSec());p.put("lease_stamp",lease.stamp);
    p.put("stamp",ros::Time::now().toSec());
    std::ostringstream out;boost::property_tree::write_json(out,p,false);
    std_msgs::String msg;msg.data=out.str();topology_feedback_pub_.publish(msg);
  }catch(const std::exception&){}
}
bool PathExecution::topologyKeepRunningLocked(double now)const{
  return topology_goal_active_&&!topology_stop_pending_&&topology_mode_text_=="ROUTE"
    &&topology_goal_.token()==topology_current_.token()
    &&now-topology_received_<=1.5&&now-topology_goal_began_<=30.;
}
void PathExecution::topologyWatchdog(const ros::WallTimerEvent&){
  // A fresh per-executor permit is required at the final velocity publisher.
  // If this process exits, permit expiry still forces zero independently.
  std::lock_guard<std::mutex> guard(topology_mutex_);
  bool allow=topologyKeepRunningLocked(interface::executionMonotonicNow());
  // A new dispatch cannot release the follower or grant a permit before its
  // first new waypoint/path is published. Same-task rolling updates keep continuity.
  if(allow&&!topology_path_published_)return;
  if(!allow){std_msgs::Bool stop;stop.data=true;stop_move_pub_.publish(stop);}
  boost::property_tree::ptree p;p.put("token",topology_goal_.token());p.put("allow",allow);
  p.put("issuer",topology_issuer_);p.put("permit_seq",++topology_permit_seq_);
  std::ostringstream out;boost::property_tree::write_json(out,p,false);
  std_msgs::String msg;msg.data=out.str();topology_permit_pub_.publish(msg);
}
void PathExecution::topologyPathPublished(){
  std::lock_guard<std::mutex> guard(topology_mutex_);
  if(!topology_goal_active_||topology_stop_pending_)return;
  if(!topology_path_published_){
    topology_path_published_=true;
    std_msgs::Bool resume;resume.data=false;stop_move_pub_.publish(resume);
    boost::property_tree::ptree p;p.put("source","executor");p.put("status","EXECUTOR_ACCEPTED");
    p.put("robot",topology_robot_);p.put("task",topology_goal_.task);p.put("version",topology_goal_.version);
    p.put("dispatch_id",topology_goal_.dispatch);p.put("command_seq",topology_goal_.sequence);
    p.put("allocation_session",topology_session_);
    std::ostringstream out;boost::property_tree::write_json(out,p,false);
    std_msgs::String msg;msg.data=out.str();topology_feedback_pub_.publish(msg);
  }
}
void PathExecution::topologyPublishPath(const Path& path){
  std::lock_guard<std::mutex> guard(topology_mutex_);
  if(!topologyKeepRunningLocked(interface::executionMonotonicNow()))return;
  boost::property_tree::ptree p,points;p.put("token",topology_goal_.token());
  p.put("stamp",ros::Time::now().toSec());p.put("goal_seq",last_topology_goal_seq_);
  p.put("body_margin_m",topology_body_margin_);
  for(const auto& pose:path){boost::property_tree::ptree row;
    for(double value:{pose.position.x,pose.position.y,tf::getYaw(pose.orientation)}){
      boost::property_tree::ptree n;n.put("",value);row.push_back({"",n});
    }points.push_back({"",row});
  }
  p.add_child("path",points);std::ostringstream out;boost::property_tree::write_json(out,p,false);
  std_msgs::String msg;msg.data=out.str();topology_certified_pub_.publish(msg);
}
void PathExecution::topologyFinish(){
  std::lock_guard<std::mutex> guard(topology_mutex_);
  topology_goal_active_=false;
  if(topology_goal_.token()==topology_current_.token()||topology_mode_text_!="ROUTE")topology_stop_pending_=true;
  std_msgs::Bool stop;stop.data=true;stop_move_pub_.publish(stop);
}
void PathExecution::topologyStop(const control_planner_interface::VehicleExecuteGoal&goal){
  std::string request,session;
  const double requested_stamp=ros::Time::now().toSec();
  try{request=interface::jsonTree(goal.execution_lease).get<std::string>("request_id");}catch(const std::exception&){}
  std::string cached;
  {
    std::lock_guard<std::mutex> guard(topology_mutex_);
    cached=topology_stop_proofs_.retryProof(request,topology_stop_pending_&&!topology_goal_active_);
    topology_goal_active_=false;topology_stop_pending_=true;
  }
  std_msgs::Bool stop;stop.data=true;stop_move_pub_.publish(stop);
  if(request.empty()){stop_move_server_.setAborted();return;}
  if(!cached.empty()){
    // Same request ID, same uninterrupted stopped epoch: an RPC retransmission
    // may receive its original proof. New IDs always take the fresh-proof path;
    // any ROUTE/new execution invalidates retry eligibility, while preserving
    // delivery to an older in-flight RPC that already earned its proof.
    control_planner_interface::VehicleExecuteResult result;result.finish=true;result.stop_proof=cached;
    stop_move_server_.setSucceeded(result);return;
  }
  {
    std::lock_guard<std::mutex> guard(topology_mutex_);
    topology_goal_active_=false;topology_stop_pending_=true;
    topology_stop_proofs_.erase(request);session=topology_session_;
  }
  boost::property_tree::ptree p;p.put("source","executor");p.put("status","STOP_REQUEST");
  p.put("robot",topology_robot_);p.put("allocation_session",session);p.put("request_id",request);
  std::ostringstream out;boost::property_tree::write_json(out,p,false);
  std_msgs::String msg;msg.data=out.str();topology_feedback_pub_.publish(msg);
  double began=interface::executionMonotonicNow();
  while(ros::ok()&&interface::executionMonotonicNow()-began<7.){
    std::string proof;
    {std::lock_guard<std::mutex> guard(topology_mutex_);
      proof=topology_stop_proofs_.waitingProof(request,requested_stamp);}
    if(!proof.empty()){
      control_planner_interface::VehicleExecuteResult result;result.finish=true;result.stop_proof=proof;
      stop_move_server_.setSucceeded(result);return;
    }
    if(stop_move_server_.isPreemptRequested()){stop_move_server_.setPreempted();return;}
    stop_move_pub_.publish(stop);ros::WallDuration(.02).sleep();
  }
  // Never convert missing odometry, a dead gate or a timeout into success.
  stop_move_server_.setAborted(control_planner_interface::VehicleExecuteResult(),"No fresh nonce-bound stop proof");
}
}
