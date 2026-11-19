#include "rapid_cover_planner/task_approach_route.h"
#include "rapid_cover_planner/topology_transit.h"
#include <cassert>
#include <iostream>
using namespace rapid_cover_planner;
int main(){
  ExecutionGrid grid;
  grid.width=grid.height=100;
  grid.resolution=.1;
  grid.x0=grid.y0=-5.;
  grid.data.assign(10000,0);
  NativeTaskScope scope;
  scope.active=true;
  TaskPatch patch;
  patch.x0=patch.y0=-.2;
  patch.resolution=.4;
  patch.approach={{0,3,5}};
  scope.patches={patch};
  auto deferred=[](double x,double){return x>1.9;};
  auto path=taskApproachRoute(grid,scope,0.,0.,0.,deferred);
  assert(path.method=="TASK_APPROACH_FALLBACK"&&path.poses.back().x<1.9&&path.arc>=.65);
  for(int j=0;j<100;++j)for(int i=58;i<62;++i)grid.data[j*100+i]=-1;
  assert(taskApproachRoute(grid,scope,0.,0.,0.,deferred).poses.empty());
  scope.active=false;
  grid.data.assign(10000,0);
  assert(taskApproachRoute(grid,scope,0.,0.,0.,deferred).poses.empty());
  // A coarse frontier can lie behind a wall from the current pose. A swept
  // sideways approach must actually reveal a previously hidden boundary.
  scope.active=true;
  scope.patches[0].approach={{2,2,2}};
  for(int y=47;y<=52;++y)grid.data[y*100+62]=100;
  assert(!seesBoundary(grid,{0,0},{2.2,0}));
  auto visible=taskApproachRoute(grid,scope,0.,0.,0.,deferred,{{2.2,0}});
  assert(!visible.poses.empty()&&visible.poses.back().y>.7);
  assert(taskApproachRoute(grid,scope,0.,0.,0.,deferred,{{0.2,1.2}}).poses.empty());
  grid.data.assign(10000,0);
  auto transit=directedTransit(grid,{{0,0},{.4,0},{.8,0},{1.2,0},{3.2,0}},.9,0,0);
  assert(transit.poses.size()>=2&&transit.poses.back().x>2.6);
  auto old_side=projectTransit({{0,0},{2,0},{2,2},{0,2},{0,0}}, {0,0},1.6);
  assert(old_side.arc==0&&old_side.after==1);
  auto staircase=transitLookahead(grid,{{0,0},{.8,0},{.8,.4},{1.6,.4},{1.6,.8},{2.4,.8}},0,0,0);
  assert(staircase.method=="DIRECTED_LOOKAHEAD"&&staircase.poses.back().x==2.4);
  for(int y=0;y<100;++y)grid.data[y*100+56]=100;
  assert(transitLookahead(grid,{{0,0},{.8,0},{1.6,.3},{2.4,.8}},0,0,0).poses.empty());
  std::cout<<"3 same-task approach checks passed (alternate, unknown, scope)\n";
  std::cout<<"5 branch progress checks passed (blocked ray, new view, no repeat gain, transit and crossing)\n";
  std::cout<<"2 assigned lookahead checks passed (staircase and swept obstacle)\n";
}
