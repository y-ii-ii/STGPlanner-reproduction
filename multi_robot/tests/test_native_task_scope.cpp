#include "rapid_cover_planner/native_task_scope.h"
#include <cassert>
#include <map>
#include <set>
#include <stdexcept>
#include <iostream>
struct Pending {std::set<int> frontiers;int distance=0;std::vector<int> path;};
int main(){
 using namespace rapid_cover_planner;
 NativeTaskScope scope;scope.active=true;TaskPatch a;a.resolution=1.;
 a.unknown={{0,1,2}};a.portals={{0,0,0}};scope.patches.push_back(a);
 assert(scope.allows(1.5,.5));assert(scope.allows(.5,.5));
 assert(!scope.allows(1.5,2.5));assert(!scope.allows(4.5,.5));
 assert(!scope.allows(INFINITY,.5));
 using Labels=std::vector<int>;using History=std::vector<std::map<int,Pending>>;
 Labels labels{1,2,3},suppressed;History history{{{10,{{1,2},7,{4,5}}},{20,{{3},9,{6}}}}};
 auto valid=[](int x){return x>=1&&x<=4;};auto owned=[](int x){return x==1;};
 {
   ScopedPending<Labels,History> view(labels,history,suppressed,valid,owned);
   assert(labels==Labels{1});assert(history.size()==1);
   assert(history[0][10].frontiers==std::set<int>{1});
   assert(history[0][10].distance==7&&history[0][10].path==Labels({4,5}));
   history.clear();suppressed.push_back(4);
 }
 assert(labels==Labels({1,2,3,4}));
 std::set<int> restored;for(auto&f:history)for(auto&e:f)restored.insert(e.second.frontiers.begin(),e.second.frontiers.end());
 assert(restored==std::set<int>({2,3}));
 assert(history[0][10].distance==7&&history[0][10].path==Labels({4,5}));
 try{ScopedPending<Labels,History> view(labels,history,suppressed,valid,owned);throw std::runtime_error("abort");}
 catch(const std::runtime_error&){}
 assert(labels==Labels({1,2,3,4}));assert(!history.empty());
 std::cout<<"14 native task-scope/history invariants passed\n";
}
