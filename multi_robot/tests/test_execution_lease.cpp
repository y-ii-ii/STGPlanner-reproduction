#include "control_planner_interface/execution_lease.h"
#include <cassert>
#include <iostream>
int main(){
 using namespace interface;
 const std::string value=R"({"schema":2,"allocation_session":"s","robot":1,"task":"t","version":3,"dispatch_id":4,"command_seq":5,"stamp":1})";
 auto a=readExecutionLease(value),b=a;
 assert(executionLeaseMatches(a,b,1.5));
 b.dispatch=5;assert(!executionLeaseMatches(a,b,1.5));
 b=a;b.task="other";assert(!executionLeaseMatches(a,b,1.5));
 assert(!executionLeaseMatches(a,a,4.));
 assert(!executionLeaseMatches(a,a,0.));
 const std::string proof=R"({"source":"velocity_gate","status":"STOPPED","robot":1,"allocation_session":"s","stop_id":"nonce","request_ids":["req"],"fresh_samples":5,"stationary_s":0.6,"zero_s":0.7})";
 assert(stoppedProofMatches(proof,"req",1,"s"));
 assert(stoppedProofMatches(proof,"req",1,""));
 assert(!stoppedProofMatches(proof,"old",1,"s"));
 assert(!stoppedProofMatches(proof,"req",2,"s"));
 assert(!stoppedProofMatches(proof,"req",1,"oldsession"));
 assert(!stoppedProofMatches(value,"req",1,"s"));
 bool rejected=false;try{readExecutionLease("{}");}catch(const std::exception&){rejected=true;}assert(rejected);
 std::cout<<"12 execution-lease/stop-proof invariants passed\n";
}
