#!/usr/bin/env python3
import argparse,json,math,time
from pathlib import Path
import rospy
from visualization_msgs.msg import MarkerArray,Marker
parser=argparse.ArgumentParser()
parser.add_argument('--seconds',type=int,default=60)
parser.add_argument('--output',required=True)
args=parser.parse_args()
stats={name:{'messages':0,'markers':0,'empty_add':0,'delete':0,'invalid_floats':0,'odd_line_lists':0,'nonempty_add':0,'examples':[]} for name in ('topo_map','grid_map')}
def callback(msg,name):
    s=stats[name];s['messages']+=1
    for m in msg.markers:
        s['markers']+=1
        if m.action==Marker.DELETE:
            s['delete']+=1;continue
        if m.action!=Marker.ADD:continue
        if not m.points:
            s['empty_add']+=1
            example={'namespace':m.ns,'id':m.id,'type':m.type,'issue':'empty ADD points'}
            if example not in s['examples']:s['examples'].append(example)
        else:s['nonempty_add']+=1
        if any(not math.isfinite(v) for p in m.points for v in (p.x,p.y,p.z)):
            s['invalid_floats']+=1
        if m.type==Marker.LINE_LIST and len(m.points)%2:s['odd_line_lists']+=1
rospy.init_node('stgplanner_marker_audit',anonymous=True)
subs=[rospy.Subscriber('/topo_planner_node/my_topo_markers',MarkerArray,lambda m:callback(m,'topo_map'),queue_size=10),
      rospy.Subscriber('/topo_planner_node/global_topo_grid',MarkerArray,lambda m:callback(m,'grid_map'),queue_size=10)]
start=time.monotonic()
while time.monotonic()-start<args.seconds and not rospy.is_shutdown():time.sleep(.1)
result={'wall_seconds':time.monotonic()-start,'topics':stats}
Path(args.output).write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
