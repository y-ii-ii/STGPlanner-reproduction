#include "path_execution/stop_proof_cache.h"
#include <cassert>
#include <iostream>
using path_execution::StopProofCache;
int main(){
 StopProofCache c;c.beginStop("one");c.record("A","one","proof-one",1.);
 assert(c.retryProof("A",true)=="proof-one");assert(c.retryProof("A",false).empty());
 assert(c.waitingProof("A",.8)=="proof-one"&&c.waitingProof("A",1.1).empty());
 c.beginMotion();assert(c.retryProof("A",true).empty());assert(c.waitingProof("A",.8)=="proof-one");
 c.record("delayed","one","arrived-after-route",1.1);assert(c.retryProof("delayed",true).empty());
 c.beginStop("two");c.record("A","two","proof-two",2.);c.record("A","one","late-old",1.);
 assert(c.retryProof("A",true)=="proof-two");
 c.record("unknown","missing-stop","valid-inflight-only",3.);
 assert(c.retryProof("unknown",true).empty()&&c.waitingProof("unknown",2.9)=="valid-inflight-only");
 StopProofCache bound(2);bound.beginStop("s");for(auto id:{"A","B","C"})bound.record(id,"s",id,1.);
 assert(bound.size()==2&&bound.retryProof("A",true).empty());
 std::cout<<"7 stop-proof cache regressions passed (inflight delivery, delayed ACK, no reuse after motion)\n";
}
