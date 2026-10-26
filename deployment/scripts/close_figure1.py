from pathlib import Path
import time, xmlrpc.client
path=Path('/mnt/d/STGPlanner/catkin_ws/src/STGPlanner/stgp_planner/visualization_tools/scripts/realTimePlot.py')
text=path.read_text()
old="    rospy.init_node('realTimePlot')"
new=old+"\n    if rospy.get_param('~suppress_window', False):\n        rospy.loginfo('Figure 1 closed for this ROS session; plotting is idle.')\n        rospy.spin()\n        return"
if new not in text:
    assert old in text
    path.write_text(text.replace(old,new))
master=xmlrpc.client.ServerProxy('http://localhost:11311')
master.setParam('/codex_close_figure','/realTimePlot/suppress_window',True)
reply=master.lookupNode('/codex_close_figure','/realTimePlot')
assert reply[0]==1,reply
uri=reply[2]
print(xmlrpc.client.ServerProxy(uri).shutdown('/codex_close_figure','User requested closing Figure 1.'),flush=True)
deadline=time.monotonic()+20
while time.monotonic()<deadline:
    reply=master.lookupNode('/codex_close_figure','/realTimePlot')
    if reply[0]==1 and reply[2]!=uri:
        print('Plot node respawned in idle mode; the figure will stay closed for this ROS master session.',flush=True)
        break
    time.sleep(.5)
else:print('Shutdown sent; no active plot window was requested by this script.',flush=True)
