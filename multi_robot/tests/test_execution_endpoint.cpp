#include "path_execution/execution_endpoint.h"
#include <cassert>
#include <iostream>
using path_execution::topologyEndpointReached;
int main(){
 for(double error=.8;error>.02;error-=.025)assert(!topologyEndpointReached(0,error,true));
 assert(topologyEndpointReached(0,.015,true));
 assert(!topologyEndpointReached(.1,.04,true)&&topologyEndpointReached(.1,.04,false));
 assert(!topologyEndpointReached(0,NAN,false)&&!topologyEndpointReached(INFINITY,0,true));
 assert(topologyEndpointReached(0,2*M_PI+.015,true));
 std::cout<<"5 execution-endpoint regressions passed (zero-distance turn cannot complete early)\n";
}
