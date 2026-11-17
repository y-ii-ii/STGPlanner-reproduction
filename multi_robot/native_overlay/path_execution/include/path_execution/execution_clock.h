#pragma once
#include <cmath>
namespace path_execution {
// ROS /clock is delivered independently to processes. A goal made 1ms "in
// the future" relative to this process must not poison a valid task lease.
// This is only timestamp transport tolerance, never a lease/token bypass.
inline bool executionGoalTimeValid(double stamp,double now){
 return std::isfinite(stamp)&&std::isfinite(now)&&now-stamp>=-.02&&now-stamp<=2.;
}
}
