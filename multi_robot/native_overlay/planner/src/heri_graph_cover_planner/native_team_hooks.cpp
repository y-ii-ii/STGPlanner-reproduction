#include "topo_planner/topo_planner.h"
#include "rapid_cover_planner/team_grid_search.h"
#include <std_msgs/String.h>
#include <map>
#include <set>
#include <sstream>
#include <iomanip>

namespace heri_graph_cover_planner {
void HeriGraphCoverPlanner::preferNativeBranch(){
 auto&gm=*global_topo_map_;auto&policy=gm.team_policy_;
 if(!policy.active()||during_relocate_||initilize_num_<=1)return;
 auto snapshot=policy.capture();
 auto valid=[&](int label){return label>=0&&boost::vertex_by_label(label,gm.heriTopo_)<boost::num_vertices(gm.heriTopo_);};
 int current_priority=3,best_priority=3,selected=current_explore_branch_;
 double best_distance=INFINITY;utils::NodeSet old_pending;
 for(int label:gm.local_frontier_labels_){
  if(!valid(label)||gm.heriTopo_[label].confirmed)continue;
  int branch=gm.heriTopo_[label].parent_branch_label;if(!valid(branch))continue;
  auto p=gm.index2Point(gm.nodeLabel2Index(label));int priority=snapshot.priority(p.x(),p.y());
  double distance=gm.squaredIdDistance(gm.robot_current_id_,gm.nodeLabel2Index(label));
  if(branch==current_explore_branch_){current_priority=std::min(current_priority,priority);old_pending.insert(label);}
  if(priority<best_priority||(priority==best_priority&&distance<best_distance)){best_priority=priority;best_distance=distance;selected=branch;}
 }
 if(best_priority==0&&current_priority>0&&selected!=current_explore_branch_){
  rapid_cover_planner::preservePendingOnSwitch(history_missed_branches_,current_explore_branch_,selected,old_pending);
  ROS_INFO("Native team branch preference %d -> %d; pending histories preserved",current_explore_branch_,selected);
  current_explore_branch_=selected;is_frontier_guiding_=false;is_frontier_robot_same_=false;last_target_node_=-1;tour_topo_path_.clear();
 }
 std::stable_sort(gm.local_frontier_labels_.begin(),gm.local_frontier_labels_.end(),[&](int a,int b){
  if(!valid(a)||!valid(b))return valid(a)>valid(b);
  auto p=gm.index2Point(gm.nodeLabel2Index(a)),q=gm.index2Point(gm.nodeLabel2Index(b));
  return snapshot.priority(p.x(),p.y())<snapshot.priority(q.x(),q.y());
 });
}
}

namespace topo_planner {
void TopoPlanner::publishNativeCatalog(){
 auto&gm=*elements_->global_topo_map_;if(!gm.team_policy_.active())return;
 double now=ros::Time::now().toSec();if(now-last_native_catalog_<1.)return;last_native_catalog_=now;
 const auto&g=gm.grid_map_;int nx=g.grid_x_num_,ny=g.grid_y_num_;std::vector<bool>free(nx*ny,false);
 int root=-1;double nearest=1.01;
 for(int x=0;x<nx;++x)for(int y=0;y<ny;++y){
  int u=x*ny+y;free[u]=gm.grid_map_image_.at<unsigned char>(gm.index2CvPoint(perception::Index2D(x,y)))==255;
  if(free[u]){auto p=g.getGridCenter(u);double d=std::hypot(p.x()-elements_->current_position_.x(),p.y()-elements_->current_position_.y());if(d<nearest){nearest=d;root=u;}}
 }
 rapid_cover_planner::TeamGridSearch search(nx,ny,g.grid_size_,free,root);
 std::set<int>labels(gm.local_frontier_labels_.begin(),gm.local_frontier_labels_.end());
 for(auto const&frame:planner_->history_missed_branches_)for(auto const&entry:frame)labels.insert(entry.second.frontiers.begin(),entry.second.frontiers.end());
 struct Bid{double x=0,y=0,cost=INFINITY;int gain=0;};std::map<int,Bid>bids;
 for(int label:labels){
  if(label<0||boost::vertex_by_label(label,gm.heriTopo_)>=boost::num_vertices(gm.heriTopo_)||gm.heriTopo_[label].confirmed)continue;
  auto point=gm.index2Point(gm.nodeLabel2Index(label));if(planner_->isExecutionDeferred(point.x(),point.y()))continue;auto index=g.getIndexInMap2D(point);double best=INFINITY;
  // Unconfirmed native skeleton endpoints need a known-free approach. The
  // final <=2m gap is an explicitly optimistic BID cost, not an issued path.
  for(int dx=-5;dx<=5;++dx)for(int dy=-5;dy<=5;++dy){int x=index.x()+dx,y=index.y()+dy;if(x<0||y<0||x>=nx||y>=ny)continue;int u=x*ny+y;if(!std::isfinite(search.cost[u]))continue;auto q=g.getGridCenter(u);double gap=(q-point).norm();if(gap<=2.)best=std::min(best,search.cost[u]+gap);}
  if(!std::isfinite(best))continue;
  int x=std::floor((point.x()+56.)/4.),y=std::floor((point.y()+24.)/4.);if(x<0||y<0||x>=36||y>=32)continue;
  auto&b=bids[y*36+x];++b.gain;if(best<b.cost){b.x=point.x();b.y=point.y();b.cost=best;}
 }
 std::ostringstream s;s<<std::setprecision(12)<<"{\"schema\":1,\"source\":\"ORIGINAL_NATIVE_BRANCHES\",\"robot\":"<<gm.team_policy_.robotId()<<",\"stamp\":"<<now<<",\"root_connected\":"<<(root>=0?"true":"false")<<",\"native_pending_labels\":"<<labels.size()<<",\"bids\":[";bool first=true;
 for(auto const&kv:bids){if(!first)s<<",";first=false;auto&b=kv.second;s<<"["<<kv.first<<","<<b.x<<","<<b.y<<","<<b.cost<<","<<b.gain<<"]";}s<<"]}";std_msgs::String m;m.data=s.str();native_catalog_pub_.publish(m);
}

void TopoPlanner::publishNativeStatus(int iteration,const control_planner_interface::ExplorerPlannerResult&result){
 auto&gm=*elements_->global_topo_map_;auto&policy=gm.team_policy_;
 auto snapshot=policy.capture();
 unsigned long deferred_calls;{std::lock_guard<std::mutex>guard(planner_->execution_feedback_mutex_);deferred_calls=planner_->execution_feedback_count_;}
 bool has_path=false;geometry_msgs::Point endpoint;
 for(auto const&segment:result.paths)if(!segment.path.empty()){endpoint=segment.path.back().position;has_path=true;}
 bool evidence=false;perception::Point2D p;
 if(planner_->is_frontier_guiding_&&planner_->native_guide_evidence_valid_){p=perception::Point2D(planner_->native_guide_evidence_.x(),planner_->native_guide_evidence_.y());evidence=true;}
 else if(!planner_->during_relocate_){
  for(int label:gm.local_frontier_labels_){if(label<0||boost::vertex_by_label(label,gm.heriTopo_)>=boost::num_vertices(gm.heriTopo_))continue;
   if(gm.heriTopo_[label].parent_branch_label==planner_->current_explore_branch_&&!gm.heriTopo_[label].confirmed){p=gm.index2Point(gm.nodeLabel2Index(label));evidence=true;break;}}
 }
 int owner=evidence?snapshot.owner(p.x(),p.y()):0;
 const char*mode=planner_->during_relocate_?"ORIGINAL_RELOCATE":planner_->is_frontier_guiding_?"ORIGINAL_UFO_GUIDING":"ORIGINAL_HIERARCHY";
 const char*intent=!has_path?"EMPTY":!policy.active()?"SINGLE_NATIVE":evidence&&owner==policy.robotId()?"OWNED_NATIVE_WORK":"NATIVE_FALLBACK";
 int key=evidence?(int(std::floor((p.y()+24.)/4.))*36+int(std::floor((p.x()+56.)/4.))):-1;
 std::ostringstream s;s<<std::setprecision(12)<<"{\"schema\":1,\"iteration\":"<<iteration<<",\"mode\":\""<<mode<<"\",\"intent\":\""<<intent<<"\",\"epoch\":"<<snapshot.epoch()<<",\"task\":"<<key<<",\"evidence_x\":"<<(evidence?p.x():0)<<",\"evidence_y\":"<<(evidence?p.y():0)<<",\"owner\":"<<owner<<",\"branch\":"<<planner_->current_explore_branch_<<",\"pending_history_frames\":"<<planner_->history_missed_branches_.size()<<",\"segments\":"<<result.paths.size()<<",\"execution_repair\":{\"status\":\""<<execution_status_<<"\",\"raw_goal\":["<<raw_execution_x_<<","<<raw_execution_y_<<"],\"projected\":"<<execution_projections_<<",\"rejected\":"<<execution_rejections_<<",\"deferred_calls\":"<<deferred_calls<<"},\"map_sync\":"<<elements_->frontier_map_->nativeMapSyncJson()<<",\"has_path\":"<<(has_path?"true":"false")<<",\"x\":"<<(has_path?endpoint.x:0)<<",\"y\":"<<(has_path?endpoint.y:0)<<"}";
 std_msgs::String m;m.data=s.str();native_status_pub_.publish(m);
}
}
