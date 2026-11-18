#pragma once
#include <mutex>
#include <utility>
#include <optional>
namespace utils {
// Timer updates clear/replace unordered frontier sets. Planning runs in a
// separate action thread: copying under the SAME writer lock is required;
// merely copying an iterator/reference still leaves dangling Code objects.
template<class Codes>
std::pair<Codes,Codes> frontierSnapshot(std::mutex&mutex,const Codes&local,const Codes&global){
 std::lock_guard<std::mutex> guard(mutex);return {local,global};
}
template<class Map,class Code>
auto frontierCoordinate(const Map&map,const Code&code)
 ->std::optional<decltype(map.toCoord(code.toKey()))>{
 // A bad depth would index UFOMap's fixed nodes_half_sizes_ array unchecked.
 if(code.getDepth()>map.getTreeDepthLevels())return std::nullopt;
 return map.toCoord(code.toKey());
}
}
