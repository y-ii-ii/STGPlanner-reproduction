#pragma once
#include <map>
#include <deque>
#include <string>
#include <cstdint>
#include <cmath>
#include <limits>
namespace path_execution {
// Caller holds the executor mutex. Delivery of an in-flight STOP result must
// survive the next ROUTE, but an old proof must never certify a NEW stop after
// motion. Bind retry eligibility to the STOP nonce's motion epoch, not to the
// (possibly delayed) proof callback's arrival time.
class StopProofCache {
 struct Entry {std::string proof;std::uint64_t epoch;double stamp;};
 std::map<std::string,Entry> proofs_;
 std::map<std::string,std::uint64_t> stop_epochs_;
 std::deque<std::string> proof_order_,stop_order_;
 std::uint64_t motion_epoch_=0;size_t limit_;
public:
 explicit StopProofCache(size_t limit=128):limit_(limit?limit:1){}
 void beginMotion(){++motion_epoch_;}
 void beginStop(const std::string& id){
  if(id.empty()||stop_epochs_.count(id))return;
  stop_epochs_[id]=motion_epoch_;stop_order_.push_back(id);
  while(stop_order_.size()>4*limit_){stop_epochs_.erase(stop_order_.front());stop_order_.pop_front();}
 }
 void record(const std::string& request,const std::string& stop_id,const std::string& proof,double stamp){
  if(!std::isfinite(stamp)||request.empty())return;
  auto previous=proofs_.find(request);if(previous!=proofs_.end()&&previous->second.stamp>stamp)return;
  if(previous==proofs_.end())proof_order_.push_back(request);
  auto e=stop_epochs_.find(stop_id);
  proofs_[request]={proof,e==stop_epochs_.end()?std::numeric_limits<std::uint64_t>::max():e->second,stamp};
  while(proofs_.size()>limit_){proofs_.erase(proof_order_.front());proof_order_.pop_front();}
 }
 std::string retryProof(const std::string& request,bool uninterrupted_stopped)const{
  auto p=proofs_.find(request);return uninterrupted_stopped&&p!=proofs_.end()&&p->second.epoch==motion_epoch_?p->second.proof:"";
 }
 std::string waitingProof(const std::string& request,double requested_stamp)const{
  auto p=proofs_.find(request);return p!=proofs_.end()&&p->second.stamp>=requested_stamp?p->second.proof:"";
 }
 void erase(const std::string& request){proofs_.erase(request);for(auto i=proof_order_.begin();i!=proof_order_.end();++i)if(*i==request){proof_order_.erase(i);break;}}
 size_t size()const{return proofs_.size();}
};
}
