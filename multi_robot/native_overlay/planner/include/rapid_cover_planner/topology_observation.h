#pragma once
namespace rapid_cover_planner {
// Skeleton morphology is a planning aid, never an observation. In particular,
// a painted UNKNOWN pixel must remain unknown in connected-task evidence.
inline int topologyObservedCell(bool observed_free, bool observed_blocked, bool morphology_free) {
  if (observed_blocked) return 100;
  if (observed_free) return morphology_free ? 0 : 100;
  return -1;
}
}
