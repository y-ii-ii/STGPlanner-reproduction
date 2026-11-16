#pragma once
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <cmath>
#include <chrono>
#include <sstream>
#include <stdexcept>
#include <string>

namespace interface {
inline double executionMonotonicNow(){
  return std::chrono::duration<double>(std::chrono::steady_clock::now().time_since_epoch()).count();
}
struct ExecutionLease {
  std::string session,task;unsigned long robot=0,version=0,dispatch=0,sequence=0;
  double stamp=0;
  std::string token()const{return session+"/"+std::to_string(robot)+"/"+std::to_string(version)+"/"+std::to_string(dispatch);}
};
inline boost::property_tree::ptree jsonTree(const std::string& text){
  boost::property_tree::ptree out;std::istringstream in(text);boost::property_tree::read_json(in,out);return out;
}
inline ExecutionLease readExecutionLease(const std::string& text){
  auto t=jsonTree(text);ExecutionLease x;
  if(t.get<int>("schema")!=2)throw std::runtime_error("execution ABI requires schema 2");
  x.session=t.get<std::string>("allocation_session");x.task=t.get<std::string>("task");
  x.robot=t.get<unsigned long>("robot");x.version=t.get<unsigned long>("version");
  x.dispatch=t.get<unsigned long>("dispatch_id");x.sequence=t.get<unsigned long>("command_seq");x.stamp=t.get<double>("stamp");
  if(x.session.empty()||x.task.empty()||!x.robot||!x.version||!x.dispatch||!std::isfinite(x.stamp))
    throw std::runtime_error("invalid execution lease");
  return x;
}
inline bool executionLeaseMatches(const ExecutionLease&goal,const ExecutionLease&current,double now){
  return goal.token()==current.token()&&goal.task==current.task&&goal.sequence<=current.sequence
    &&std::isfinite(now)&&now>=goal.stamp&&now-goal.stamp<=2.;
}
inline bool stoppedProofMatches(const std::string& text,const std::string& request,
                                int robot,const std::string& session){
  try{
    auto p=jsonTree(text);
    if(p.get<std::string>("source")!="velocity_gate"||p.get<std::string>("status")!="STOPPED"
      ||p.get<int>("robot")!=robot||p.get<std::string>("allocation_session").empty()
      ||(!session.empty()&&p.get<std::string>("allocation_session")!=session)
      ||p.get<std::string>("stop_id").empty()||p.get<int>("fresh_samples")<3
      ||p.get<double>("stationary_s")<.5||p.get<double>("zero_s")<.5)return false;
    if(!std::isfinite(p.get<double>("stationary_s"))||!std::isfinite(p.get<double>("zero_s")))return false;
    for(const auto&id:p.get_child("request_ids"))if(id.second.get_value<std::string>()==request)return true;
  }catch(const std::exception&){}
  return false;
}
}
