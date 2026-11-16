#pragma once
#include "rapid_cover_planner/execution_grid.h"
#include <string>
#include <utility>
#include <vector>

namespace rapid_cover_planner {
using TopologyPoint = std::pair<double, double>;
struct TopologyPrefix {
  std::vector<TopologyPoint> points;
  std::string status = "BLOCKED";
};
// A remote known-free edge is global routing evidence, not current local safety.
// This independent gate accepts only a sampled, observed-free BODY prefix.
// No unknown-space exception from the historical endpoint repair is reused.
inline TopologyPrefix topologyPrefix(const ExecutionGrid& grid,
    const std::vector<TopologyPoint>& route, double x, double y, double yaw,
    double now, double stamp, double max_distance = 4.0) {
  TopologyPrefix out;
  if (!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(yaw) ||
      !std::isfinite(max_distance) || max_distance<=0 || !std::isfinite(grid.resolution)) return out;
  if (!std::isfinite(now) || !std::isfinite(stamp) || now < stamp || now-stamp > 2.0) {
    out.status = "STALE"; return out;
  }
  if (grid.resolution <= 0 || route.empty()) return out;
  for (const auto& p : route)
    if (!std::isfinite(p.first) || !std::isfinite(p.second)) return out;
  if (std::hypot(route.front().first-x, route.front().second-y) > .8) return out;
  if (grid.footprint(x,y,yaw) != 0) return out;
  out.points.push_back({x,y});
  double travelled = 0, heading = yaw;
  const double step = std::min(.05, grid.resolution/2.);
  auto turn_free = [&](double nx, double ny, double target) {
    double delta = std::atan2(std::sin(target-heading),std::cos(target-heading));
    int n = std::max(1, int(std::ceil(std::abs(delta)/.05)));
    for (int k=1;k<=n;++k)
      if (grid.footprint(nx,ny,heading+delta*k/n)!=0) return false;
    return true;
  };
  for (const auto& goal : route) {
    auto from = out.points.back();
    double distance = std::hypot(goal.first-from.first, goal.second-from.second);
    if (distance < 1e-8) continue;
    double direction = std::atan2(goal.second-from.second,goal.first-from.first);
    if (!turn_free(from.first,from.second,direction)) break;
    heading = direction;
    int n = std::max(1,int(std::ceil(distance/step)));
    bool stop = false;
    for (int k=1;k<=n;++k) {
      TopologyPoint p{from.first+(goal.first-from.first)*k/n,
                      from.second+(goal.second-from.second)*k/n};
      double move = std::hypot(p.first-out.points.back().first,p.second-out.points.back().second);
      if (travelled+move > max_distance || grid.footprint(p.first,p.second,heading)!=0) {
        stop=true; break;
      }
      travelled+=move;out.points.push_back(p);
    }
    if (stop) break;
  }
  if (travelled < .25) {out.points.clear();return out;}
  out.status = std::hypot(out.points.back().first-route.back().first,
                          out.points.back().second-route.back().second)<.05 ? "CLEAR" : "PREFIX";
  return out;
}
}
