#pragma once
#include <chrono>
#include <thread>
namespace path_execution {
// ROS command and action goal travel over independent connections. Wait a
// bounded wall interval for a newer referenced command; this grants NO motion.
// Caller must still check session/token, STOP state, sequence and freshness.
template<class Pending> bool waitWhileCommandPending(Pending pending,double seconds=.25){
 const auto end=std::chrono::steady_clock::now()+std::chrono::duration<double>(seconds);
 while(pending()){
  if(std::chrono::steady_clock::now()>=end)return false;
  std::this_thread::sleep_for(std::chrono::milliseconds(2));
 }
 return true;
}
}
