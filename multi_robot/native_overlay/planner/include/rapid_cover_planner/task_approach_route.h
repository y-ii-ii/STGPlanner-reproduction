#pragma once
#include "rapid_cover_planner/body_route.h"
#include "rapid_cover_planner/native_task_scope.h"

namespace rapid_cover_planner {
inline bool seesBoundary(const ExecutionGrid& grid,TopologyPoint pose,TopologyPoint target) {
  const double distance=std::hypot(target.first-pose.first,target.second-pose.second);
  if(distance>3.2||distance<.15)return false;
  const int steps=std::max(1,int(std::ceil(distance/(grid.resolution*.7))));
  for(int i=0;i<steps;++i){
    const double t=double(i)/steps;
    const int x=std::floor((pose.first+t*(target.first-pose.first)-grid.x0)/grid.resolution);
    const int y=std::floor((pose.second+t*(target.second-pose.second)-grid.y0)/grid.resolution);
    if(x<0||x>=grid.width||y<0||y>=grid.height)return false;
    int state=grid.data[y*grid.width+x];
    // Allow the unknown target cell itself. A known wall immediately
    // before it or unobserved space along the approach occludes the ray.
    if(state>=50||(state<0&&(1.-t)*distance>grid.resolution))return false;
  }
  return true;
}
// A saturated or deferred graph endpoint can still have a reachable viewpoint
// in its assigned approach band. Try simple turn-then-straight primitives with
// the normal body margin and a bounded search. This uses only own-map evidence.
template<class Deferred>
BodyRoute taskApproachRoute(const ExecutionGrid& grid, const NativeTaskScope& scope,
                           double x, double y, double yaw, Deferred deferred,
                           const std::vector<TopologyPoint>& remaining={}) {
  BodyRoute best;
  if (!scope.active || grid.footprint(x,y,yaw,.15)!=0) return best;
  struct Candidate {BodyPose pose;double distance,turn;int gain=0;};
  std::vector<Candidate> candidates;
  for (const auto& patch : scope.patches) {
    for (const auto& run : patch.approach) {
      for (int ix=run.first;ix<=run.last;++ix) {
        const double px=patch.x0+(ix+.5)*patch.resolution;
        const double py=patch.y0+(run.y+.5)*patch.resolution;
        const double distance=std::hypot(px-x,py-y);
        if (distance<.65 || distance>2.6 || deferred(px,py)) continue;
        const double heading=std::atan2(py-y,px-x);
        const double turn=std::remainder(heading-yaw,2*M_PI);
        if (std::abs(turn)>(remaining.empty()?.65:1.2)) continue;
        candidates.push_back({{px,py,heading},distance,turn});
      }
    }
  }
  std::stable_sort(candidates.begin(),candidates.end(),[](const Candidate& a,const Candidate& b) {
    return a.distance-.8*std::abs(a.turn)>b.distance-.8*std::abs(b.turn);
  });
  if (candidates.size()>24) candidates.resize(24);
  if(!remaining.empty()){
    // Candidate view gain estimates new information only. It is not a score
    // or a declaration that this task has been observed.
    std::vector<TopologyPoint> hidden;
    const size_t stride=std::max(size_t(1),(remaining.size()+63)/64);
    for(size_t i=0;i<remaining.size();i+=stride)
      if(!seesBoundary(grid,{x,y},remaining[i]))hidden.push_back(remaining[i]);
    auto gain=[&](const Candidate& c){
      return std::count_if(hidden.begin(),hidden.end(),[&](TopologyPoint p){
        return seesBoundary(grid,{c.pose.x,c.pose.y},p);
      });
    };
    for(auto& c:candidates)c.gain=gain(c);
    std::stable_sort(candidates.begin(),candidates.end(),[](const Candidate& a,const Candidate& b){return a.gain>b.gain;});
    candidates.erase(std::remove_if(candidates.begin(),candidates.end(),[](const Candidate& c){return c.gain==0;}),candidates.end());
  }
  if (candidates.size()>12) candidates.resize(12);
  for (double margin : {.22,.15}) {
    if (grid.footprint(x,y,yaw,margin)!=0) continue;
    for (const auto& c : candidates) {
      bool safe=true;
      const int turns=std::max(1,int(std::ceil(std::abs(c.turn)/.05)));
      for (int k=1;k<=turns&&safe;++k)
        safe=grid.footprint(x,y,yaw+c.turn*k/turns,margin)==0;
      const int steps=std::max(1,int(std::ceil(c.distance/.05)));
      for (int k=1;k<=steps&&safe;++k)
        safe=grid.footprint(x+(c.pose.x-x)*k/steps,y+(c.pose.y-y)*k/steps,c.pose.yaw,margin)==0;
      if (!safe) continue;
      best.poses={{x,y,yaw}};
      if (std::abs(c.turn)>.001) best.poses.push_back({x,y,c.pose.yaw});
      best.poses.push_back(c.pose);
      best.status="BODY_APPROACH";
      best.method="TASK_APPROACH_FALLBACK";
      best.arc=c.distance;
      return best;
    }
  }
  return best;
}
}
