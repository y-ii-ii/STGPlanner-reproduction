#pragma once
#include "rapid_cover_planner/topology_route_gate.h"
#include <queue>
#include <limits>
#include <array>
#include <functional>
namespace rapid_cover_planner {
struct BodyPose {double x,y,yaw;};
struct BodyRoute {std::vector<BodyPose> poses;std::string status="BODY_NO_PATH";int expanded=0;double goal_offset=0;};
// Local SE(2) repair of ONE assigned/native guide. Every translation, reverse
// and in-place turn is checked as a swept body, rather than point A* followed
// by an unplanned corner cut. Goal is an observation approach region, not a
// requirement to put the chassis on a frontier adjacent to a wall.
inline BodyRoute bodyRoute(const ExecutionGrid& grid,const std::vector<TopologyPoint>& reference,
                          double x,double y,double yaw){
 BodyRoute out;if(reference.empty()||grid.resolution<=0||!std::isfinite(grid.resolution)||!std::isfinite(x)||!std::isfinite(y)||!std::isfinite(yaw))return out;
 for(auto p:reference)if(!std::isfinite(p.first)||!std::isfinite(p.second))return out;
 const double margin=.15,step=std::max(.15,std::min(.25,grid.resolution));
 if(grid.footprint(x,y,yaw,margin)!=0){out.status="BODY_START_BLOCKED";return out;}
 TopologyPoint guide=reference.back();double length=0;TopologyPoint previous{x,y};
 for(auto p:reference){double d=std::hypot(p.first-previous.first,p.second-previous.second);
  if(length+d>=3.){double t=(3.-length)/std::max(d,1e-8);guide={previous.first+t*(p.first-previous.first),previous.second+t*(p.second-previous.second)};break;}
  length+=d;previous=p;
 }
 if(std::hypot(guide.first-x,guide.second-y)<.65){out.status="BODY_NO_PROGRESS";return out;}
 const std::array<int,16> dx{{3,3,2,1,0,-1,-2,-3,-3,-3,-2,-1,0,1,2,3}};
 const std::array<int,16> dy{{0,1,2,3,3,3,2,1,0,-1,-2,-3,-3,-3,-2,-1}};
 std::array<double,16> angle;int initial=0;double nearest=100;
 for(int h=0;h<16;++h){angle[h]=std::atan2(dy[h],dx[h]);double d=std::abs(std::atan2(std::sin(angle[h]-yaw),std::cos(angle[h]-yaw)));if(d<nearest){nearest=d;initial=h;}}
 auto sweep=[&](BodyPose a,BodyPose b){double turn=std::atan2(std::sin(b.yaw-a.yaw),std::cos(b.yaw-a.yaw));
  int n=std::max(1,int(std::ceil(std::max(std::hypot(b.x-a.x,b.y-a.y)/.05,std::abs(turn)/.06))));
  for(int k=1;k<=n;++k)if(grid.footprint(a.x+(b.x-a.x)*k/n,a.y+(b.y-a.y)*k/n,a.yaw+turn*k/n,margin)!=0)return false;
  return true;
 };
 if(!sweep({x,y,yaw},{x,y,angle[initial]})){out.status="BODY_INITIAL_TURN";return out;}
 const int radius=int(std::ceil(5./step)),side=2*radius+1,total=side*side*16;
 auto index=[&](int ix,int iy,int h){return ((iy+radius)*side+ix+radius)*16+h;};
 auto pose=[&](int id){int h=id%16,cell=id/16;return BodyPose{x+(cell%side-radius)*step,y+(cell/side-radius)*step,angle[h]};};
 std::vector<double> cost(total,std::numeric_limits<double>::infinity());std::vector<int> parent(total,-1);
 using Q=std::pair<double,int>;std::priority_queue<Q,std::vector<Q>,std::greater<Q>> queue;
 int start=index(0,0,initial),found=-1;cost[start]=0;queue.push({0,start});
 auto heuristic=[&](BodyPose p){return std::max(0.,std::hypot(p.x-guide.first,p.y-guide.second)-.8);};
 while(!queue.empty()&&out.expanded<4000){int id=queue.top().second;double f=queue.top().first;queue.pop();auto a=pose(id);
  if(f>cost[id]+heuristic(a)+1e-6)continue;++out.expanded;
  if(std::hypot(a.x-guide.first,a.y-guide.second)<=.8&&std::hypot(a.x-x,a.y-y)>=.6){found=id;break;}
  int h=id%16,cell=id/16,ix=cell%side-radius,iy=cell/side-radius;
  for(int action=0;action<4;++action){int nh=h,nx=ix,ny=iy;double edge;
   if(action<2){nh=(h+(action==0?1:15))%16;edge=.12;}
   else {int sign=action==2?1:-1;nx+=sign*dx[h];ny+=sign*dy[h];edge=std::hypot(dx[h],dy[h])*step*(sign>0?1.:1.5);}
   if(std::abs(nx)>radius||std::abs(ny)>radius)continue;int next=index(nx,ny,nh);
   if(cost[id]+edge>=cost[next])continue;auto b=pose(next);if(!sweep(a,b))continue;
   cost[next]=cost[id]+edge;parent[next]=id;queue.push({cost[next]+heuristic(b),next});
  }
 }
 if(found<0)return out;out.goal_offset=std::hypot(pose(found).x-guide.first,pose(found).y-guide.second);
 for(int id=found;id>=0;id=parent[id])out.poses.push_back(pose(id));std::reverse(out.poses.begin(),out.poses.end());
 out.poses.insert(out.poses.begin(),{x,y,yaw});
 // Retain the established <=4m execution-prefix contract even for a detour.
 double arc=0;size_t keep=1;
 for(;keep<out.poses.size();++keep){auto a=out.poses[keep-1],b=out.poses[keep];double d=std::hypot(b.x-a.x,b.y-a.y);if(arc+d>4.)break;arc+=d;}
 out.poses.resize(keep);out.status="BODY_APPROACH";return out;
}
}
