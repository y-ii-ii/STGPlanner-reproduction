#include <ufo/map/occupancy_map.h>
#include "utils/frontier_snapshot.h"
#include <unordered_set>
#include <thread>
#include <cassert>
#include <cmath>
#include <iostream>
int main(){
 using Codes=std::unordered_set<ufo::map::Code,ufo::map::Code::Hash>;
 ufo::map::OccupancyMap map(.1);std::mutex mutex;Codes local,global;
 local.insert(map.toCode(ufo::map::Point3(1.,2.,0.)));global=local;
#ifdef UNSAFE
 // Same lifetime defect as the action reader racing frontierSearch.clear().
 const auto& held=*local.begin();local.clear();auto p=map.toCoord(held.toKey());
 std::cout<<p.x()<<"\n";return 0;
#else
 auto saved=utils::frontierSnapshot(mutex,local,global);local.clear();global.clear();
 auto coordinate=utils::frontierCoordinate(map,*saved.first.begin());
 assert(coordinate&&std::isfinite(coordinate->x())); // value snapshot survives live erasure
 std::thread writer([&](){for(int i=0;i<3000;++i){
  std::lock_guard<std::mutex> guard(mutex);local.clear();global.clear();
  for(int k=0;k<8;++k)local.insert(map.toCode(ufo::map::Point3(i*.01,k*.2,0.)));
  global=local;
 }});
 for(int i=0;i<1000;++i){auto snapshot=utils::frontierSnapshot(mutex,local,global);
  assert(snapshot.first==snapshot.second);
  for(const auto&code:snapshot.first)assert(utils::frontierCoordinate(map,code));
 }
 writer.join(); // concurrent mutation and snapshots remain coherent
 assert(!utils::frontierCoordinate(map,ufo::map::Code(0,255))); // unchecked UFO depth used to index out of range
 {std::lock_guard<std::mutex> guard(mutex);local.clear();global.clear();}
 auto empty=utils::frontierSnapshot(mutex,local,global);assert(empty.first.empty()&&empty.second.empty());
 std::cout<<"4 actual-UFO frontier snapshot cases passed (erasure, concurrency, bad depth, empty)\n";
#endif
}
