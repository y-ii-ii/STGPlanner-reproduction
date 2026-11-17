#include "path_execution/execution_clock.h"
#include <cassert>
#include <iostream>
#include <limits>
int main(){
 using path_execution::executionGoalTimeValid;
 assert(executionGoalTimeValid(15304.723,15304.722));
 assert(executionGoalTimeValid(10.019,10.));
 assert(!executionGoalTimeValid(10.021,10.));
 assert(!executionGoalTimeValid(7.99,10.));
 assert(!executionGoalTimeValid(std::numeric_limits<double>::quiet_NaN(),10.));
 assert(!executionGoalTimeValid(10.,std::numeric_limits<double>::infinity()));
 std::cout<<"6 execution timestamp regressions passed (recorded 1ms skew, stale/future/nonfinite rejection)\n";
}
