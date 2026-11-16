#pragma once
#include <algorithm>
#include <cmath>
#include <functional>
#include <set>
#include <stdexcept>
#include <vector>

namespace rapid_cover_planner {
struct TaskRun {int y, first, last;};
struct TaskPatch {
  double x0=0,y0=0,resolution=0;
  std::vector<TaskRun> unknown,portals;
  bool contains(double x,double y) const {
    if(!std::isfinite(x)||!std::isfinite(y)||resolution<=0)return false;
    double gx=std::floor((x-x0)/resolution),gy=std::floor((y-y0)/resolution);
    if(std::abs(gx)>1e7||std::abs(gy)>1e7)return false;
    auto in=[&](const std::vector<TaskRun>& rows){
      for(const auto&r:rows)if(r.y==int(gy)&&r.first<=gx&&gx<=r.last)return true;
      return false;
    };
    return in(unknown)||in(portals);
  }
};
struct NativeTaskScope {
  bool active=false;
  std::vector<TaskPatch> patches;
  bool allows(double x,double y) const {
    if(!active)return true;
    for(const auto& patch:patches)if(patch.contains(x,y))return true;
    return false;
  }
};

// Borrow the native local frontier/history containers for ONE task-constrained
// planning call. Unassigned labels are restored even on exceptions. Ownership
// filtering never marks a vertex confirmed or removes a pending branch.
template<class Labels,class History>
class ScopedPending {
  Labels& local_;History& history_;Labels& suppressed_;
  Labels original_;History excluded_;
  std::function<bool(int)> valid_;
public:
  ScopedPending(Labels& local,History& history,Labels& suppressed,
                std::function<bool(int)> valid,std::function<bool(int)> allowed)
      :local_(local),history_(history),suppressed_(suppressed),original_(local),valid_(valid) {
    Labels filtered;
    for(auto label:local)if(valid(label)&&allowed(label))filtered.push_back(label);
    local=filtered;
    History owned;
    for(const auto& frame:history){
      typename History::value_type a,b;
      for(const auto& entry:frame){
        auto own=entry.second,other=entry.second;own.frontiers.clear();other.frontiers.clear();
        for(auto label:entry.second.frontiers){
          if(!valid(label))continue;
          (allowed(label)?own:other).frontiers.insert(label);
        }
        if(!own.frontiers.empty())a[entry.first]=own;
        if(!other.frontiers.empty())b[entry.first]=other;
      }
      if(!a.empty())owned.push_back(a);
      if(!b.empty())excluded_.push_back(b);
    }
    history=owned;
  }
  ~ScopedPending(){
    History owned=history_;history_=excluded_;
    for(const auto& frame:owned){
      typename History::value_type clean;
      for(const auto& entry:frame){
        auto value=entry.second;value.frontiers.clear();
        for(auto label:entry.second.frontiers)if(valid_(label))value.frontiers.insert(label);
        if(!value.frontiers.empty())clean[entry.first]=value;
      }
      if(!clean.empty())history_.push_back(clean);
    }
    std::set<int> seen;Labels restored;
    auto append=[&](const Labels& items){for(auto label:items)
      if(valid_(label)&&seen.insert(label).second)restored.push_back(label);};
    append(original_);append(local_);append(suppressed_);
    local_=restored;suppressed_.clear();
  }
};
}
