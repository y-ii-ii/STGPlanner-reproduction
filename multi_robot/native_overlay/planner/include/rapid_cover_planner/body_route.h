#pragma once
#include "rapid_cover_planner/topology_route_gate.h"
#include <queue>
#include <limits>
#include <array>
#include <functional>
namespace rapid_cover_planner {
struct BodyPose {double x,y,yaw;};
struct BodyRoute {std::vector<BodyPose> poses;std::string status="BODY_NO_PATH",method="SE2";int expanded=0;double goal_offset=0,margin=.15,arc=0;};
// Local SE(2) repair of ONE assigned/native guide. Every translation, reverse
// and in-place turn is checked as a swept body, rather than point A* followed
// by an unplanned corner cut. Goal is an observation approach region, not a
// requirement to put the chassis on a frontier adjacent to a wall.
inline BodyRoute bodyRouteWithReserve(const ExecutionGrid& grid,const std::vector<TopologyPoint>& reference,
                          double x,double y,double yaw,double normal_sweep_margin){
 BodyRoute out;if(grid.resolution<=0||!std::isfinite(grid.resolution)||!std::isfinite(x)||!std::isfinite(y)||!std::isfinite(yaw))return out;
 for(auto p:reference)if(!std::isfinite(p.first)||!std::isfinite(p.second))return out;
 const bool recenter=grid.footprint(x,y,yaw,.15)!=0;
 if(reference.empty()&&!recenter)return out;
 const double margin=recenter?.05:.15,step=std::max(.15,std::min(.25,grid.resolution));out.margin=margin;
 const double sweep_margin=recenter?margin:normal_sweep_margin;
 // A newly observed obstacle can invalidate the normal reserve while the
 // physical body remains clear. Only a <=3m low-speed escape to full clearance
 // is allowed; no obstacle/unknown cell or physical-body collision is waived.
 if(grid.footprint(x,y,yaw,sweep_margin)!=0){out.status="BODY_START_BLOCKED";return out;}
 if(recenter){
  // Prefer a directly certified back-off/turn. A long parallel-wall escape
  // should not exhaust a Dijkstra budget on many irrelevant heading states.
  // The extra 3cm at the goal covers the executor's 8mm / 0.02rad tolerance;
  // normal motion still requires the full 0.15m body reserve.
  double best=INFINITY;BodyRoute candidate;
  for(int direction:{-1,1}){
   std::vector<BodyPose> path{{x,y,yaw}};
   for(int k=1;k<=60;++k){double d=k*.05;BodyPose p{x+direction*d*std::cos(yaw),y+direction*d*std::sin(yaw),yaw};
    if(grid.footprint(p.x,p.y,p.yaw,.05)!=0)break;path.push_back(p);
    if(grid.footprint(p.x,p.y,p.yaw,.18)==0){double score=d*(direction<0?1.5:1.);
     if(score<best){best=score;candidate.poses=path;candidate.arc=d;candidate.method="RECENTER_STRAIGHT";}break;}
   }
   path={{x,y,yaw}};
   for(int k=1;k<=32;++k){double angle=std::min(k*.05,M_PI/2);BodyPose p{x,y,yaw+direction*angle};
    if(grid.footprint(p.x,p.y,p.yaw,.05)!=0)break;path.push_back(p);
    if(grid.footprint(p.x,p.y,p.yaw,.18)==0){double score=angle*.4;
     if(score<best){best=score;candidate.poses=path;candidate.arc=0;candidate.method="RECENTER_ROTATE";}break;}
   }
  }
  if(!candidate.poses.empty()){candidate.status="BODY_RECENTER";candidate.margin=.05;return candidate;}
 }
 // A task target may have been deferred while stopping. Clearance recovery is
 // still needed under that valid task lease, even with no exploration guide.
 TopologyPoint guide=reference.empty()?TopologyPoint{x,y}:reference.back();double length=0;TopologyPoint previous{x,y};
 for(auto p:reference){double d=std::hypot(p.first-previous.first,p.second-previous.second);
  if(length+d>=3.){double t=(3.-length)/std::max(d,1e-8);guide={previous.first+t*(p.first-previous.first),previous.second+t*(p.second-previous.second)};break;}
  length+=d;previous=p;
 }
 if(!recenter&&std::hypot(guide.first-x,guide.second-y)<.65){out.status="BODY_NO_PROGRESS";return out;}
 const std::array<int,16> dx{{3,3,2,1,0,-1,-2,-3,-3,-3,-2,-1,0,1,2,3}};
 const std::array<int,16> dy{{0,1,2,3,3,3,2,1,0,-1,-2,-3,-3,-3,-2,-1}};
 // Rotate the lattice with the measured chassis heading. A world-aligned
 // lattice forced an unnecessary initial snap turn, even when a straight
 // back-off was safe. Positions AND headings use the same rotated basis.
 std::array<double,16> angle;const int initial=0;const double cy=std::cos(yaw),sy=std::sin(yaw);
 for(int h=0;h<16;++h)angle[h]=yaw+std::atan2(dy[h],dx[h]);
 auto sweep=[&](BodyPose a,BodyPose b){double turn=std::atan2(std::sin(b.yaw-a.yaw),std::cos(b.yaw-a.yaw));
  int n=std::max(1,int(std::ceil(std::max(std::hypot(b.x-a.x,b.y-a.y)/.05,std::abs(turn)/.06))));
  for(int k=1;k<=n;++k)if(grid.footprint(a.x+(b.x-a.x)*k/n,a.y+(b.y-a.y)*k/n,a.yaw+turn*k/n,sweep_margin)!=0)return false;
  return true;
 };
 const int radius=int(std::ceil(5./step)),side=2*radius+1,total=side*side*16;
 auto index=[&](int ix,int iy,int h){return ((iy+radius)*side+ix+radius)*16+h;};
 auto pose=[&](int id){int h=id%16,cell=id/16;double px=(cell%side-radius)*step,py=(cell/side-radius)*step;return BodyPose{x+cy*px-sy*py,y+sy*px+cy*py,angle[h]};};
 std::vector<double> cost(total,std::numeric_limits<double>::infinity()),travel(total,std::numeric_limits<double>::infinity());std::vector<int> parent(total,-1);
 using Q=std::pair<double,int>;std::priority_queue<Q,std::vector<Q>,std::greater<Q>> queue;
 int start=index(0,0,initial),found=-1,best_prefix=-1;double best_remaining=std::hypot(x-guide.first,y-guide.second)-.5;cost[start]=travel[start]=0;queue.push({0,start});
 auto heuristic=[&](BodyPose p){return recenter?0.:std::max(0.,std::hypot(p.x-guide.first,p.y-guide.second)-.8);};
 while(!queue.empty()&&out.expanded<1600){int id=queue.top().second;double f=queue.top().first;queue.pop();auto a=pose(id);
  if(f>cost[id]+heuristic(a)+1e-6)continue;++out.expanded;
  double remaining=std::hypot(a.x-guide.first,a.y-guide.second);
  if(!recenter&&cost[id]<=4.&&std::hypot(a.x-x,a.y-y)>=.6&&remaining<best_remaining){best_remaining=remaining;best_prefix=id;}
  if(recenter?((std::hypot(a.x-x,a.y-y)>=.15||std::abs(std::atan2(std::sin(a.yaw-yaw),std::cos(a.yaw-yaw)))>=.15)&&grid.footprint(a.x,a.y,a.yaw,.18)==0):
      (std::hypot(a.x-guide.first,a.y-guide.second)<=.8&&std::hypot(a.x-x,a.y-y)>=.6)){found=id;break;}
  int h=id%16,cell=id/16,ix=cell%side-radius,iy=cell/side-radius;
  for(int action=0;action<4;++action){int nh=h,nx=ix,ny=iy;double edge;
   if(action<2){nh=(h+(action==0?1:15))%16;edge=.12;}
   else {int sign=action==2?1:-1;nx+=sign*dx[h];ny+=sign*dy[h];edge=std::hypot(dx[h],dy[h])*step*(sign>0?1.:1.5);}
   if(std::abs(nx)>radius||std::abs(ny)>radius)continue;int next=index(nx,ny,nh);
   // Previous weighted budget=1 allowed at most 0.67m of reverse. A nearly
   // parallel wall can require a longer observed-free back-off before turning.
   // Bound the actual translational arc separately, not by reverse penalties.
   double next_arc=travel[id]+(action<2?0.:std::hypot(dx[h],dy[h])*step);
   if(cost[id]+edge>=cost[next]||(recenter&&(cost[id]+edge>6.||next_arc>3.)))continue;auto b=pose(next);if(!sweep(a,b))continue;
   cost[next]=cost[id]+edge;travel[next]=next_arc;parent[next]=id;queue.push({cost[next]+heuristic(b),next});
  }
 }
 bool partial=found<0&&best_prefix>=0;if(partial)found=best_prefix;
 if(found<0)return out;out.goal_offset=std::hypot(pose(found).x-guide.first,pose(found).y-guide.second);
 for(int id=found;id>=0;id=parent[id])out.poses.push_back(pose(id));std::reverse(out.poses.begin(),out.poses.end());
 out.poses.insert(out.poses.begin(),{x,y,yaw});
 if(recenter){
  double arc=0.;for(size_t i=1;i<out.poses.size();++i)arc+=std::hypot(out.poses[i].x-out.poses[i-1].x,out.poses[i].y-out.poses[i-1].y);
  // A truncated recovery may still lack normal clearance. Reject it; unlike an
  // exploration prefix, recovery must end with the full reserve restored.
  if(arc>3.){out.poses.clear();out.status="BODY_RECENTER_LIMIT";return out;}
 }
 // Retain the established <=4m execution-prefix contract even for a detour.
 double arc=0;size_t keep=1;
 for(;keep<out.poses.size();++keep){auto a=out.poses[keep-1],b=out.poses[keep];double d=std::hypot(b.x-a.x,b.y-a.y);if(arc+d>4.)break;arc+=d;}
 out.poses.resize(keep);out.arc=arc;out.status=recenter?"BODY_RECENTER":(partial?"BODY_PREFIX":"BODY_APPROACH");return out;
}
inline BodyRoute bodyRoute(const ExecutionGrid& grid,const std::vector<TopologyPoint>& reference,
                          double x,double y,double yaw){
 // Prefer an additional 7cm PLANNING reserve when the measured start permits
 // it. Recorded stops lost clearance after inertial turning near a wall. This
 // does not relax the 15cm execution contract or the 5cm bounded recovery.
 // A tight corridor/unknown/finite search budget may reject this preference;
 // keep the original validated search as a fallback, not a new hard dead end.
 int preferred_expanded=0;
 if(grid.resolution>0&&std::isfinite(grid.resolution)&&std::isfinite(x)&&std::isfinite(y)&&std::isfinite(yaw)
       &&!reference.empty()&&grid.footprint(x,y,yaw,.22)==0){
   auto roomy=bodyRouteWithReserve(grid,reference,x,y,yaw,.22);
   if(!roomy.poses.empty()){roomy.method="CLEARANCE_"+roomy.method;return roomy;}
   preferred_expanded=roomy.expanded;
 }
 auto original=bodyRouteWithReserve(grid,reference,x,y,yaw,.15);
 original.expanded+=preferred_expanded;return original;
}
}
