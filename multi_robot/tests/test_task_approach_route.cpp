#include "rapid_cover_planner/task_approach_route.h"
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
  std::cout<<"3 same-task approach checks passed (alternate, unknown, scope)\n";
}
