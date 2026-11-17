#include "rapid_cover_planner/body_route.h"
#include <cassert>
#include <iostream>
using namespace rapid_cover_planner;
int main(){
 ExecutionGrid g;g.width=g.height=100;g.resolution=.15;g.x0=g.y0=-7.5;g.data.assign(10000,0);
 auto check=[&](const BodyRoute& r){assert(!r.poses.empty());double arc=0;for(size_t i=0;i<r.poses.size();++i){auto p=r.poses[i];assert(g.footprint(p.x,p.y,p.yaw)==0);if(i)arc+=std::hypot(p.x-r.poses[i-1].x,p.y-r.poses[i-1].y);}assert(arc<=4.00001);};
 auto forward=bodyRoute(g,{{0,0},{3,0}},0,0,0);check(forward);assert(forward.expanded>0);
 auto reverse=bodyRoute(g,{{0,0},{-3,0}},0,0,0);check(reverse);assert(reverse.poses.back().x<0);
 // Requested chassis endpoint is inside a wall: a known-free observation
 // approach must be chosen, never an occupied goal or an unknown-space waiver.
 for(int y=0;y<100;++y)for(int x=66;x<100;++x)g.data[y*100+x]=100;
 auto wall=bodyRoute(g,{{0,0},{2.5,0}},0,0,0);check(wall);assert(wall.goal_offset>.3);
 g.data.assign(10000,-1);assert(bodyRoute(g,{{0,0},{3,0}},0,0,0).poses.empty());
 g.data.assign(10000,100);assert(bodyRoute(g,{{0,0},{3,0}},0,0,0).status=="BODY_START_BLOCKED");
 g.data.assign(10000,0);assert(bodyRoute(g,{{0,0},{NAN,0}},0,0,0).poses.empty());
 assert(bodyRoute(g,{{0,0},{.2,0}},0,0,0).status=="BODY_NO_PROGRESS");
 // A turn in a narrow corridor is not replaceable by a point-wise A* corner.
 for(int y=0;y<100;++y)for(int x=0;x<100;++x)if(std::abs(g.y0+(y+.5)*.15)>.6)g.data[y*100+x]=100;
 auto corridor=bodyRoute(g,{{0,0},{0,3}},0,0,0);assert(corridor.poses.empty());
 g.data.assign(10000,0);
 for(int y=0;y<100;++y)for(int x=53;x<100;++x)g.data[y*100+x]=100;
 assert(g.footprint(0,0,0,.05)==0&&g.footprint(0,0,0,.15)!=0);
 auto recenter=bodyRoute(g,{{0,0},{3,0}},0,0,0);
 assert(recenter.status=="BODY_RECENTER"&&recenter.margin==.05&&!recenter.poses.empty());
 auto end=recenter.poses.back();assert(g.footprint(end.x,end.y,end.yaw,.15)==0);
 for(auto p:recenter.poses)assert(g.footprint(p.x,p.y,p.yaw,.05)==0);
 std::cout<<"9 body-route cases passed (including bounded, observed-free recenter escape)\n";
}
