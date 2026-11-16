#include "rapid_cover_planner/topology_route_gate.h"
#include "rapid_cover_planner/topology_observation.h"
#include <cassert>
#include <iostream>
#include <limits>
using namespace rapid_cover_planner;
int main() {
  ExecutionGrid grid;
  grid.resolution=.1;grid.width=100;grid.height=60;grid.x0=-2;grid.y0=-3;
  grid.data.assign(grid.width*grid.height,0);
  std::vector<TopologyPoint> route{{0,0},{1,0},{2,0},{3,0},{4,0},{5,0}};
  auto full=topologyPrefix(grid,route,0,0,0,1,1);
  assert(full.status=="PREFIX"&&!full.points.empty()&&full.points.back().first<=4.);
  auto clear=topologyPrefix(grid,{{0,0},{1,0}},0,0,0,1,1);
  assert(clear.status=="CLEAR");
  assert(topologyPrefix(grid,route,0,0,0,4,1).status=="STALE");
  assert(topologyPrefix(grid,route,0,0,0,0,1).status=="STALE");
  assert(topologyPrefix(grid,{{2,0},{3,0}},0,0,0,1,1).points.empty());
  for(int y=0;y<grid.height;++y)for(int x=40;x<grid.width;++x)grid.data[y*grid.width+x]=-1;
  auto unknown=topologyPrefix(grid,route,0,0,0,1,1);
  assert(unknown.status=="PREFIX"&&unknown.points.back().first<1.6);
  for(int y=0;y<grid.height;++y)for(int x=21;x<grid.width;++x)grid.data[y*grid.width+x]=100;
  assert(topologyPrefix(grid,route,0,0,0,1,1).points.empty());
  grid.data.assign(grid.width*grid.height,0);
  grid.data[30*grid.width+25]=100;
  assert(topologyPrefix(grid,route,0,0,0,1,1).points.empty());
  assert(topologyPrefix(grid,route,0,0,std::numeric_limits<double>::quiet_NaN(),1,1).points.empty());
  assert(topologyPrefix(grid,{{0,0},{INFINITY,0}},0,0,0,1,1).points.empty());
  assert(topologyObservedCell(false,false,true)==-1);
  assert(topologyObservedCell(false,false,false)==-1);
  assert(topologyObservedCell(true,false,true)==0);
  assert(topologyObservedCell(true,false,false)==100);
  std::cout<<"10 native body-prefix + 4 observation-provenance cases passed; no ROS master or simulator\n";
}
