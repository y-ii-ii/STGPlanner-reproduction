#include "path_execution/command_wait.h"
#include <atomic>
#include <cassert>
#include <iostream>
int main(){
 using namespace path_execution;std::atomic<unsigned> received{178};
 std::thread delivery([&](){std::this_thread::sleep_for(std::chrono::milliseconds(20));received=179;});
 assert(waitWhileCommandPending([&](){return 179>received.load();}));delivery.join();assert(received==179);
 // Lost command / frozen ROS clock cannot wait forever (steady wall deadline).
 auto began=std::chrono::steady_clock::now();assert(!waitWhileCommandPending([](){return true;},.02));
 assert(std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count()<.5);
 // A newer STOP sequence is not considered a pending old ROUTE. The caller's
 // original STOP check remains authoritative and must reject that old goal.
 received=180;assert(waitWhileCommandPending([&](){return 179>received.load();}));
 std::cout<<"5 command delivery wait checks passed (reorder, lost command, wall bound, newer STOP)\n";
}
