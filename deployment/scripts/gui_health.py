#!/usr/bin/env python3
import json
from pathlib import Path
import rosnode
names = ['/gazebo_gui', '/planner_rviz', '/realTimePlot']
data = {name: rosnode.rosnode_ping(name, max_count=1, verbose=False) for name in names}
Path('/mnt/d/STGPlanner/logs/gui_node_health.json').write_text(json.dumps(data, indent=2))
print(json.dumps(data, indent=2))
raise SystemExit(0 if all(data.values()) else 1)
