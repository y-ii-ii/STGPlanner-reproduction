#pragma once
#include "rapid_cover_planner/body_route.h"

namespace rapid_cover_planner {
struct RouteProjection { double arc=0., gap=INFINITY; size_t after=0; };

inline RouteProjection projectTransit(const std::vector<TopologyPoint>& path,
                                      TopologyPoint pose,double limit){
  RouteProjection best;
  double arc=0.;
  for(size_t i=1;i<path.size()&&arc<limit;++i){
    const auto [ax,ay]=path[i-1];
    const auto [bx,by]=path[i];
    const double dx=bx-ax,dy=by-ay,length=std::hypot(dx,dy);
    if(length<1e-7)continue;
    double t=std::clamp(((pose.first-ax)*dx+(pose.second-ay)*dy)/(length*length),
                        0.,std::min(1.,(limit-arc)/length));
    double gap=std::hypot(ax+t*dx-pose.first,ay+t*dy-pose.second);
    if(gap+1e-8<best.gap)best={arc+t*length,gap,i};
    arc+=length;
  }
  return best;
}

inline BodyRoute transitLookahead(const ExecutionGrid& grid,const std::vector<TopologyPoint>& guide,
                                  double x,double y,double yaw){
  BodyRoute result;
  std::vector<TopologyPoint> candidates;
  double arc=0.;
  TopologyPoint previous{x,y};
  for(const auto& point:guide){
    arc+=std::hypot(point.first-previous.first,point.second-previous.second);
    if(arc>3.8)break;
    if(std::hypot(point.first-x,point.second-y)>=.85)candidates.push_back(point);
    previous=point;
  }
  // Coarse topology uses staircase paths. A distant point on the assigned
  // route can be approached directly when this robot verifies the whole
  // body sweep, without repeatedly turning at each coarse cell.
  for(double margin:{.22,.15}){
    if(grid.footprint(x,y,yaw,margin)!=0)continue;
    for(auto it=candidates.rbegin();it!=candidates.rend();++it){
      const double dx=it->first-x,dy=it->second-y;
      const double length=std::hypot(dx,dy);
      const double turn=std::remainder(std::atan2(dy,dx)-yaw,2*M_PI);
      if(std::abs(turn)>.75)continue;
      const int rotations=std::max(1,int(std::ceil(std::abs(turn)/.05)));
      bool safe=true;
      for(int i=1;i<=rotations&&safe;++i)
        safe=grid.footprint(x,y,yaw+turn*i/rotations,margin)==0;
      const int steps=std::max(1,int(std::ceil(length/.05)));
      for(int i=1;i<=steps&&safe;++i)
        safe=grid.footprint(x+dx*i/steps,y+dy*i/steps,yaw+turn,margin)==0;
      if(!safe)continue;
      result.poses={{x,y,yaw}};
      if(std::abs(turn)>1e-6)result.poses.push_back({x,y,yaw+turn});
      result.poses.push_back({it->first,it->second,yaw+turn});
      result.method="DIRECTED_LOOKAHEAD";result.status="BODY_APPROACH";result.arc=length;
      return result;
    }
  }
  return result;
}

inline BodyRoute directedTransit(const ExecutionGrid& grid,const std::vector<TopologyPoint>& path,
                                 double x,double y,double yaw){
  const TopologyPoint pose{x,y};
  auto start=projectTransit(path,pose,1.6);
  std::vector<TopologyPoint> guide;
  // Attach to the already travelled prefix only in a short neighbourhood.
  // A nearby later branch or a crossing must never teleport route progress.
  if(start.after&&start.gap<=.40)
    guide.assign(path.begin()+start.after,path.end());
  else
    guide=path;
  auto route=transitLookahead(grid,guide,x,y,yaw);
  if(route.poses.empty())route=bodyRoute(grid,guide,x,y,yaw);
  if(route.poses.empty()||route.status=="BODY_RECENTER"||path.size()<2)return route;
  const auto& endpoint=route.poses.back();
  const auto projected=projectTransit(path,{endpoint.x,endpoint.y},5.);
  const double goal_gain=std::hypot(path.back().first-x,path.back().second-y)
      -std::hypot(path.back().first-endpoint.x,path.back().second-endpoint.y);
  // Full own-map footprint certification already ran. Require the certified
  // translation to advance along the assigned graph route or toward its goal.
  if((projected.gap<=.70&&projected.arc-start.arc>=.38)||goal_gain>=.50)return route;
  route.poses.clear();
  route.status="BODY_NO_ROUTE_PROGRESS";
  return route;
}
}
