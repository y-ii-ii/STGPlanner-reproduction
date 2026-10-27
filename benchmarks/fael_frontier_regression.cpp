#include <ros/ros.h>
#include <perception/ufomap.h>
#include <fstream>
#include <cmath>
int main(int argc,char** argv) {
  ros::init(argc,argv,"fael_frontier_regression");
  ros::NodeHandle nh("/fael_frontier_regression_inputs"),priv("~");
  priv.setParam("UFOMap/resolution",.4);
  priv.setParam("UFOMap/min_x",-1000.);priv.setParam("UFOMap/min_y",-1000.);
  priv.setParam("UFOMap/max_x",1000.);priv.setParam("UFOMap/max_y",1000.);
  perception::Ufomap map(nh,priv);
  map.pub_timer_.stop();map.frontier_timer_.stop();map.write_ufomap_timer_.stop();
  map.current_robot_pose_.translation()=ufo::math::Vector3(0,0,0);
  map.robot_bottom_=.05;map.robot_height_=.8;map.frontier_depth_=0;
  auto cell=map.map_.toCode(2.2,.2,.2,0);
  // This bundled UFOMap queries the parent aggregate for a depth-0 code.
  // Populate complete sibling groups so the fixture has an unambiguous free
  // aggregate, without changing the shared map implementation or its metric.
  perception::CodeUnorderSet seeded;
  auto block=[&](const ufo::map::Code& code,double evidence,bool once){
    auto p=map.map_.toCoord(code.toKey());
    double x=std::floor(p.x()/.8)*.8,y=std::floor(p.y()/.8)*.8,z=std::floor(p.z()/.8)*.8;
    for(int a=0;a<2;a++)for(int b=0;b<2;b++)for(int c=0;c<2;c++){
      auto leaf=map.map_.toCode(x+.2+a*.4,y+.2+b*.4,z+.2+c*.4,0);
      if(!once || seeded.insert(leaf).second)map.map_.updateOccupancy(leaf,evidence);
    }
  };
  block(cell,.4,true);
  map.history_frontier_cells_.insert(cell);
  map.changed_cell_codes_.clear();map.changed_cell_codes_.insert(cell);
  map.findPlaneLocalFrontier();
  bool reactivation=map.local_frontier_cells_.count(cell)>0;
  auto neighbours=map.get_XY_NeighborCell(cell,0);
  for(const auto& n:neighbours)block(n,.4,true);
  map.local_frontier_cells_.clear();map.global_frontier_cells_.clear();
  map.map_.resetChangeDetection();
  auto outside=map.map_.toCode(2.6,.2,.2,0);
  block(outside,.6,false); // Opposite evidence restores unknown log odds.
  map.frontierSearch();
  bool neighbour_change=map.global_frontier_cells_.count(cell)>0;
  std::ofstream out("/mnt/d/STGPlanner/benchmarks/fael_frontier_regression.json");
  out<<"{\"passed\":"<<(reactivation&&neighbour_change?"true":"false")
     <<",\"native_ufomap_test\":true,\"checks\":{\"seen_frontier_can_reactivate\":"<<(reactivation?"true":"false")
     <<",\"unchanged_free_cell_rechecked_after_neighbour_change\":"<<(neighbour_change?"true":"false")<<"}}\n";
  ROS_INFO("Frontier regression: reactivation=%d neighbour_change=%d",reactivation,neighbour_change);
  return reactivation&&neighbour_change?0:1;
}
