from pathlib import Path
p=Path('/opt/stgplanner/benchmarks/gbp2_ws/src/gbplanner/src/gbplanner.cpp')
s=p.read_text()
if 'BenchmarkRuntimeScope' not in s:
    s=s.replace('#include <nav_msgs/Path.h>','#include <nav_msgs/Path.h>\n#include <std_msgs/Float64.h>\n#include <chrono>\n')
    needle='planner_msgs::planner_srv::Response& res) {\n'
    replacement=needle+'''  // Measurement only: includes build, gain evaluation and returned path.
  struct BenchmarkRuntimeScope {
    ros::Publisher publisher;
    std::chrono::steady_clock::time_point start;
    BenchmarkRuntimeScope(ros::NodeHandle& nh) : start(std::chrono::steady_clock::now()) {
      static ros::Publisher pub = nh.advertise<std_msgs::Float64>("/benchmark/native_runtime", 100);
      publisher = pub;
    }
    ~BenchmarkRuntimeScope() {
      std_msgs::Float64 value;
      value.data = std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
      publisher.publish(value);
    }
  } runtime_scope(nh_);
'''
    assert s.count(needle)==1
    s=s.replace(needle,replacement)
    p.write_text(s)
print('GBP2 callback measurement installed')
