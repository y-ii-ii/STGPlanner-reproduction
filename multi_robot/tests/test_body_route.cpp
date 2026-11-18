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
 g.data.assign(10000,0);
 for(int y=0;y<100;++y)for(int x=62;x<100;++x)g.data[y*100+x]=-1;
 auto partial=bodyRoute(g,{{0,0},{4,0}},0,0,0);assert(partial.status=="BODY_PREFIX");check(partial);
 g.data.assign(10000,0);
 auto heading=bodyRoute(g,{{0,0},{3*std::cos(.19),3*std::sin(.19)}},0,0,.19);check(heading);
 assert(std::abs(heading.poses[1].yaw-.19)<1e-9);
 ExecutionGrid near;near.width=near.height=100;near.resolution=.1;near.x0=near.y0=-5;near.data.assign(10000,0);
 for(int y=54;y<100;++y)for(int x=0;x<100;++x)near.data[y*100+x]=100;
 assert(near.footprint(0,0,.07,.05)==0&&near.footprint(0,0,.07,.15)!=0);
 auto parallel=bodyRoute(near,{{0,0},{3,0}},0,0,.07);
 assert(parallel.status=="BODY_RECENTER"&&parallel.arc>.67&&parallel.arc<=3.);
 auto recover=parallel.poses.back();assert(near.footprint(recover.x,recover.y,recover.yaw,.15)==0);
 auto no_guide=bodyRoute(near,{},0,0,.07);assert(no_guide.status=="BODY_RECENTER");
 near.data.assign(10000,0);for(int y=0;y<100;++y)for(int x=56;x<100;++x)near.data[y*100+x]=100;
 auto rotation=bodyRoute(near,{},0,0,M_PI/4);
 assert(rotation.status=="BODY_RECENTER"&&rotation.arc<1e-6);
 assert(std::abs(rotation.poses.back().yaw-M_PI/4)>.15);
 // Extra reserve is preferred in open observed space; output still declares
 // the existing 0.15m follower contract, rather than permitting less clearance.
 g.data.assign(10000,0);auto roomy=bodyRoute(g,{{0,0},{3,.9}},0,0,0);
 assert(!roomy.poses.empty()&&roomy.method=="CLEARANCE_SE2"&&roomy.margin==.15);
 for(auto p:roomy.poses)assert(g.footprint(p.x,p.y,p.yaw,.22)==0);
 // A 1m observed corridor admits the original body reserve but not 0.22m.
 // Preference must not delete that safe route or waive unknown cells.
 ExecutionGrid tight;tight.width=tight.height=200;tight.resolution=.05;tight.x0=tight.y0=-5;tight.data.assign(40000,0);
 for(int y=0;y<200;++y)for(int x=0;x<200;++x)if(std::abs(tight.y0+(y+.5)*.05)>=.5)tight.data[y*200+x]=100;
 assert(tight.footprint(0,0,0,.15)==0&&tight.footprint(0,0,0,.22)!=0);
 auto fallback=bodyRoute(tight,{{0,0},{3,0}},0,0,0);assert(!fallback.poses.empty()&&fallback.margin==.15);
 for(auto p:fallback.poses)assert(tight.footprint(p.x,p.y,p.yaw,.15)==0);
 std::cout<<"16 body-route cases passed (clearance preference, tight fallback, parallel-wall escape, empty-guide and rotation recovery)\n";
}
