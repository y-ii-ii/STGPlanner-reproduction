#include "topo_planner/topo_planner.h"
#include "rapid_cover_planner/execution_grid.h"
#include "rapid_cover_planner/team_grid_search.h"
#include <std_msgs/Float64MultiArray.h>
#include <tf/transform_datatypes.h>

namespace heri_graph_cover_planner {
bool HeriGraphCoverPlanner::isExecutionDeferred(double x,double y)const{
 if(!execution_repair_enabled_)return false;double now=ros::Time::now().toSec();std::lock_guard<std::mutex>guard(execution_feedback_mutex_);
 for(auto const&b:execution_deferred_)if(b.until>now&&std::hypot(b.x-x,b.y-y)<b.radius)return true;return false;
}
void HeriGraphCoverPlanner::deferExecutionFrontier(double x,double y,double radius,double duration){
 if(!execution_repair_enabled_||!std::isfinite(x)||!std::isfinite(y))return;
 double now=ros::Time::now().toSec();std::lock_guard<std::mutex>guard(execution_feedback_mutex_);
 execution_deferred_.erase(std::remove_if(execution_deferred_.begin(),execution_deferred_.end(),[&](const ExecutionDeferred&b){return b.until<=now;}),execution_deferred_.end());
 bool existing=false;for(auto const&b:execution_deferred_)if(std::hypot(b.x-x,b.y-y)<radius*.5){existing=true;break;}
 if(!existing)execution_deferred_.push_back({x,y,radius,now+duration});
 execution_guiding_until_=std::max(execution_guiding_until_,now+8.);++execution_feedback_count_;
}
bool HeriGraphCoverPlanner::applyExecutionRecovery(const Point3D&current){
 if(!execution_repair_enabled_)return false;
 {std::lock_guard<std::mutex>guard(execution_feedback_mutex_);if(ros::Time::now().toSec()>=execution_guiding_until_)return false;}
 // Temporary original UFO-guidance recovery. Native pending branches remain
 // intact; a deferred target is not marked observed, completed or deleted.
 during_relocate_=false;is_frontier_guiding_=true;native_guide_evidence_valid_=false;no_frontier_left_=false;
 auto&gm=*global_topo_map_;auto const&g=gm.grid_map_;int nx=g.grid_x_num_,ny=g.grid_y_num_;std::vector<bool>free(nx*ny,false);int root=-1;double nearest=.65;
 for(int x=0;x<nx;++x)for(int y=0;y<ny;++y){int u=x*ny+y;free[u]=g.grids_[x][y].status==Free;if(free[u]){auto p=g.getGridCenter(u);double d=std::hypot(p.x()-current.x(),p.y()-current.y());if(d<nearest){nearest=d;root=u;}}}
 rapid_cover_planner::TeamGridSearch search(nx,ny,g.grid_size_,free,root);auto ownership=gm.team_policy_.capture();
 int selected=-1,best_priority=3;double best=INFINITY;Point3D evidence;
 auto consider=[&](const ufo::map::Code&code){
  auto f=gm.ufomap_->map_.toCoord(code.toKey());if(isExecutionDeferred(f.x(),f.y()))return;
  int priority=ownership.priority(f.x(),f.y());
  auto candidate=[&](Point2D p,double max_gap){
   if(!g.isInMapRange2D(p)||isExecutionDeferred(p.x(),p.y())||std::hypot(p.x()-current.x(),p.y()-current.y())<.8)return;
   auto i=g.getIndexInMap2D(p);int u=i.x()*ny+i.y();double gap=std::hypot(p.x()-f.x(),p.y()-f.y());
   if(!std::isfinite(search.cost[u])||gap>max_gap)return;double score=search.cost[u]+gap;
   if(priority<best_priority||(priority==best_priority&&score<best)){selected=u;best=score;best_priority=priority;evidence=Point3D(f.x(),f.y(),f.z());}
  };
  candidate(Point2D((f.x()+current.x())*.5,(f.y()+current.y())*.5),INFINITY);
  auto i=g.getIndexInMap2D(Point2D(f.x(),f.y()));
  for(int dx=-3;dx<=3;++dx)for(int dy=-3;dy<=3;++dy){int x=i.x()+dx,y=i.y()+dy;if(x>=0&&y>=0&&x<nx&&y<ny)candidate(g.getGridCenter(x,y),1.6);}
 };
 for(auto const&code:gm.ufomap_->local_frontier_cells_)consider(code);
 if(selected<0)for(auto const&code:gm.ufomap_->global_frontier_cells_)consider(code);
 tour_points_.clear();tour_points_gains_.clear();max_gain_=0.;
 if(selected>=0){auto p=g.getGridCenter(selected);Point3D view(p.x(),p.y(),current.z());tour_points_.insert(view);tour_points_gains_[view]=1.;max_gain_=1.;native_guide_evidence_=evidence;native_guide_evidence_valid_=true;}
 return true;
}
}

namespace topo_planner {
void TopoPlanner::initializeExecutionRepair(){
 nh_private_.param("execution_repair/enabled",execution_repair_enabled_,true);planner_->execution_repair_enabled_=execution_repair_enabled_;
 execution_grid_pub_=nh_private_.advertise<nav_msgs::OccupancyGrid>("native_execution_grid",1,true);
 execution_feedback_sub_=nh_private_.subscribe<std_msgs::Float64MultiArray>("execution_feedback",5,&TopoPlanner::executionFeedback,this);
}
void TopoPlanner::executionFeedback(const std_msgs::Float64MultiArray::ConstPtr&m){
 if(!execution_repair_enabled_||m->data.size()!=6)return;
 for(double v:m->data)if(!std::isfinite(v))return;
 if(std::abs(ros::Time::now().toSec()-m->data[4])>5.)return;
 double duration=m->data[5]==2?15.:45.;
 planner_->deferExecutionFrontier(m->data[0],m->data[1],1.2,duration);
 planner_->deferExecutionFrontier(m->data[2],m->data[3],1.5,duration);
}
rapid_cover_planner::ExecutionGrid TopoPlanner::executionGrid(){
 rapid_cover_planner::ExecutionGrid out;auto&m=*elements_->map_2d_manager_;
 std::lock_guard<std::mutex>guard(m.map_2d_update_mutex_);auto const&g=m.map_;
 if(g.grids_.empty()||g.grids_[0].empty())return out;
 out.resolution=g.grid_size_;out.x0=g.min_x_;out.y0=g.min_y_;out.width=g.grid_x_num_;out.height=g.grid_y_num_;
 if(out.width<=0||out.height<=0||g.grids_.size()!=size_t(out.width)||g.grids_[0].size()!=size_t(out.height))return out;
 out.data.resize(out.width*out.height,-1);
 for(int x=0;x<out.width;++x)for(int y=0;y<out.height;++y){auto state=g.grids_[x][y].status;out.data[y*out.width+x]=state==perception::Free?0:(state==perception::Unknown?-1:100);}
 return out;
}
void TopoPlanner::publishExecutionGrid(){
 if(!execution_repair_enabled_||ros::Time::now().toSec()-last_execution_grid_<.4)return;
 last_execution_grid_=ros::Time::now().toSec();auto g=executionGrid();if(g.data.empty())return;
 nav_msgs::OccupancyGrid m;m.header.frame_id="world";m.header.stamp=elements_->map_2d_manager_->last_observation_stamp_;
 m.info.resolution=g.resolution;m.info.width=g.width;m.info.height=g.height;m.info.origin.position.x=g.x0;m.info.origin.position.y=g.y0;m.info.origin.orientation.w=1;
 m.data.assign(g.data.begin(),g.data.end());execution_grid_pub_.publish(m);
}
void TopoPlanner::repairExecutionPath(control_planner_interface::ExplorerPlannerResult&result){
 execution_status_="UNCHANGED";raw_execution_x_=0;raw_execution_y_=0;
 if(!execution_repair_enabled_)return;
 std::vector<std::pair<int,int>>indices;for(int s=0;s<int(result.paths.size());++s)for(int p=0;p<int(result.paths[s].path.size());++p)indices.push_back({s,p});
 if(indices.empty())return;
 auto last=indices.back();auto end=result.paths[last.first].path[last.second];raw_execution_x_=end.position.x;raw_execution_y_=end.position.y;
 auto grid=executionGrid();int state=grid.footprint(end.position.x,end.position.y,tf::getYaw(end.orientation));
 bool deferred=planner_->isExecutionDeferred(end.position.x,end.position.y);
 if(!deferred&&state!=1){execution_status_=state==0?"CLEAR":"DEFER_UNKNOWN";return;}
 auto reject=[&](){
  result.paths.clear();execution_status_="REJECTED";++execution_rejections_;
  planner_->deferExecutionFrontier(raw_execution_x_,raw_execution_y_,1.2,45.);
  if(planner_->native_guide_evidence_valid_)planner_->deferExecutionFrontier(planner_->native_guide_evidence_.x(),planner_->native_guide_evidence_.y(),1.5,45.);
  else {auto&gm=*elements_->global_topo_map_;for(int label:gm.local_frontier_labels_)if(label>=0&&boost::vertex_by_label(label,gm.heriTopo_)<boost::num_vertices(gm.heriTopo_)&&gm.heriTopo_[label].parent_branch_label==planner_->current_explore_branch_&&!gm.heriTopo_[label].confirmed){auto p=gm.index2Point(gm.nodeLabel2Index(label));planner_->deferExecutionFrontier(p.x(),p.y(),1.5,45.);break;}}
 };
 if(deferred){reject();return;}
 for(auto it=indices.rbegin();it!=indices.rend();++it){
  auto pose=result.paths[it->first].path[it->second];double from_end=std::hypot(pose.position.x-end.position.x,pose.position.y-end.position.y);
  if(from_end>5.)break;
  double progress=std::hypot(pose.position.x-elements_->current_position_.x(),pose.position.y-elements_->current_position_.y());
  if(progress<.6||grid.footprint(pose.position.x,pose.position.y,tf::getYaw(pose.orientation))!=0)continue;
  // Keep a prefix of the ORIGINAL native route; no direct fallback segment.
  result.paths.resize(it->first+1);result.paths.back().path.resize(it->second+1);execution_status_="APPROACH";++execution_projections_;return;
 }
 reject();
}
}
