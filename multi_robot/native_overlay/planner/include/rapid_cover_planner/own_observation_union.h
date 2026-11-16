#pragma once
#include "rapid_cover_planner/execution_grid.h"
namespace rapid_cover_planner {
// Terrain returns have a sensor blind annulus around the chassis. A missing
// terrain return is not missing evidence in the independently observed UFO
// projection. Combine OWN sources only: 0 free, 1 occupied, 2 unobserved.
// Whole fine cells need free evidence; neither unknown nor the robot pose is
// used to manufacture free space. Existing obstacles always win.
template<class Observe>
size_t combineOwnObservations(ExecutionGrid& grid,Observe observed){
  size_t filled=0;
  if(grid.resolution<=0||grid.data.size()!=size_t(grid.width*grid.height))return 0;
  const double epsilon=grid.resolution*1e-6;
  for(int y=0;y<grid.height;++y)for(int x=0;x<grid.width;++x){
    auto& value=grid.data[y*grid.width+x];if(value>=50)continue;
    bool free=true,occupied=false;
    for(double dx:{epsilon,grid.resolution-epsilon})for(double dy:{epsilon,grid.resolution-epsilon}){
      int state=observed(grid.x0+x*grid.resolution+dx,grid.y0+y*grid.resolution+dy);
      free=free&&state==0;occupied=occupied||state==1;
    }
    if(occupied)value=100;
    else if(value<0&&free){value=0;++filled;}
  }
  return filled;
}
}
