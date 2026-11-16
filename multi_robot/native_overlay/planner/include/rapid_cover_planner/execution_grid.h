#pragma once
#include <vector>
#include <cmath>
#include <algorithm>
namespace rapid_cover_planner {
struct ExecutionGrid {
 double resolution=0,x0=0,y0=0;int width=0,height=0;std::vector<int> data;
 // 0: observed free footprint; 1: known obstacle/empty; 2: unknown/outside.
 int footprint(double x,double y,double yaw,double margin=.15)const{
  if(resolution<=0||width<=0||height<=0||data.size()!=size_t(width*height))return 2;
  double c=std::cos(yaw),s=std::sin(yaw),ac=std::abs(c),as=std::abs(s),hx=.35+margin,hy=.30+margin,r=resolution/2;
  double ex=hx*ac+hy*as,ey=hx*as+hy*ac;
  int ax=std::floor((x-ex-x0)/resolution),bx=std::floor((x+ex-x0)/resolution),ay=std::floor((y-ey-y0)/resolution),by=std::floor((y+ey-y0)/resolution);
  bool unknown=ax<0||ay<0||bx>=width||by>=height;
  for(int yy=std::max(0,ay);yy<=std::min(height-1,by);++yy)for(int xx=std::max(0,ax);xx<=std::min(width-1,bx);++xx){
   double dx=x0+(xx+.5)*resolution-x,dy=y0+(yy+.5)*resolution-y;
   if(std::abs(dx)>ex+r||std::abs(dy)>ey+r||std::abs(dx*c+dy*s)>hx+r*(ac+as)||std::abs(-dx*s+dy*c)>hy+r*(ac+as))continue;
   int state=data[yy*width+xx];if(state>=50)return 1;if(state<0)unknown=true;
  }
  return unknown?2:0;
 }
};
}
