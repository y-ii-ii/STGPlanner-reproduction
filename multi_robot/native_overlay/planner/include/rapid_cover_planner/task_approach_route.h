#pragma once
#include "rapid_cover_planner/body_route.h"
#include "rapid_cover_planner/native_task_scope.h"

namespace rapid_cover_planner {
// A saturated or deferred graph endpoint can still have a reachable viewpoint
// in its assigned approach band. Try simple turn-then-straight primitives with
// the normal body margin and a bounded search. This uses only own-map evidence.
template<class Deferred>
BodyRoute taskApproachRoute(const ExecutionGrid& grid, const NativeTaskScope& scope,
                           double x, double y, double yaw, Deferred deferred) {
  BodyRoute best;
  if (!scope.active || grid.footprint(x,y,yaw,.15)!=0) return best;
  struct Candidate {BodyPose pose;double distance,turn;};
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
        if (std::abs(turn)>.65) continue;
        candidates.push_back({{px,py,heading},distance,turn});
      }
    }
  }
  std::stable_sort(candidates.begin(),candidates.end(),[](const Candidate& a,const Candidate& b) {
    return a.distance-.8*std::abs(a.turn)>b.distance-.8*std::abs(b.turn);
  });
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
