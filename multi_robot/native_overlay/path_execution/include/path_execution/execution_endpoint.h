#pragma once
#include <cmath>
namespace path_execution {
// A zero-distance clearance turn is not complete until its yaw was executed.
// Keep this geometry-only predicate usable by offline safety regression tests.
inline bool topologyEndpointReached(double distance,double yaw_error,bool recovery){
  if(!std::isfinite(distance)||!std::isfinite(yaw_error)||distance<0)return false;
  double angle=std::abs(std::atan2(std::sin(yaw_error),std::cos(yaw_error)));
  return distance<(recovery?.008:.18)&&angle<(recovery?.02:.12);
}
}
