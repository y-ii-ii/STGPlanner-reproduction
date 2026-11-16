#include "rapid_cover_planner/own_observation_union.h"
#include "rapid_cover_planner/topology_route_gate.h"
#include <cassert>
#include <iostream>
int main(){
 using namespace rapid_cover_planner;
 ExecutionGrid g;g.resolution=.1;g.x0=-3;g.y0=-3;g.width=60;g.height=60;g.data.assign(3600,-1);
 assert(g.footprint(0,0,0)==2);
 auto all=g;auto n=combineOwnObservations(all,[](double,double){return 0;});
 assert(n==3600);assert(all.footprint(0,0,0)==0);
 assert(!topologyPrefix(all,{{0,0},{2,0}},0,0,0,1,1).points.empty());
 auto unknown=g;combineOwnObservations(unknown,[](double,double){return 2;});assert(unknown.footprint(0,0,0)==2);
 auto obstacle=g;obstacle.data[30*60+30]=100;combineOwnObservations(obstacle,[](double,double){return 0;});assert(obstacle.footprint(0,0,0)==1);
 auto projected=all;combineOwnObservations(projected,[](double x,double y){return x>-.1&&x<.2&&y>-.1&&y<.2?1:0;});assert(projected.footprint(0,0,0)==1);
 auto partial=g;combineOwnObservations(partial,[](double x,double){return x<0?0:2;});assert(partial.footprint(0,0,0)==2);
 std::cout<<"8 own-observation blind-spot/obstacle/unknown checks passed\n";
}
