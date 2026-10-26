#!/usr/bin/env python3
"""Read actual RViz display status properties while rendering the same ROS data."""
import json
import sys
import time
import ctypes
import sip
from pathlib import Path
from python_qt_binding.QtWidgets import QApplication
from python_qt_binding.QtCore import QTimer
from rviz import bindings as rviz

output = Path(sys.argv[1])
output.parent.mkdir(parents=True, exist_ok=True)
app = QApplication(sys.argv)
frame = rviz.VisualizationFrame()
frame.setSplashPath('')
frame.initialize()
config = rviz.Config()
rviz.YamlConfigReader().readFile(config, '/mnt/d/STGPlanner/catkin_ws/src/STGPlanner/stgp_planner/planner/resource/topo_planner.rviz')
frame.load(config)
frame.setWindowTitle('STGPlanner RViz Diagnostic Monitor')
frame.show()
root = frame.getManager().getRootDisplayGroup()
last_capture=0.0
capture_library=ctypes.CDLL('/opt/stgplanner/librviz_native_capture.so')
capture_library.capture_rviz.argtypes=[ctypes.c_void_p,ctypes.c_char_p]
capture_library.capture_rviz.restype=ctypes.c_int

def property_data(prop, depth=0):
    value = prop.getValue()
    result = {'name':prop.getName(), 'value':str(value)}
    if depth < 5:
        result['children'] = [property_data(prop.childAt(i),depth+1) for i in range(prop.numChildren())]
    return result

def dump():
    global last_capture
    result = {'unix_time':time.time(), 'displays':{}}
    for i in range(root.numDisplays()):
        display = root.getDisplayAt(i)
        if display.getName() not in ('RobotModel','topo_map','grid_map'):
            continue
        statuses=[]
        for j in range(display.numChildren()):
            prop=display.childAt(j)
            if prop.getName().startswith('Status'):
                statuses.append(property_data(prop))
        result['displays'][display.getName()]={'enabled':bool(display.getValue()),'status':statuses}
    output.write_text(json.dumps(result,indent=2))
    with output.with_suffix('.history.jsonl').open('a') as stream:
        stream.write(json.dumps(result)+'\n')
    if output.name=='status_after.json' and time.monotonic()-last_capture>10:
        ready=len(result['displays'])==3 and all(d['enabled'] and d['status'] and all(s['name']=='Status: Ok' for s in d['status']) for d in result['displays'].values())
        if ready:
            path=output.parent/'rviz_native_capture.png'
            code=capture_library.capture_rviz(int(sip.unwrapinstance(frame)),str(path).encode())
            if code:
                print('Native capture failed',code,flush=True)
                return
            (output.parent/'qt_capture_metadata.json').write_text(json.dumps({'unix_time':time.time(),'window_title':frame.windowTitle(),'width':frame.width(),'height':frame.height(),'method':'Live RViz Qt controls plus OGRE framebuffer captured in the same application callback; no generated content','status':result['displays']},indent=2))
            last_capture=time.monotonic()

timer=QTimer()
timer.timeout.connect(dump)
timer.start(2000)
sys.exit(app.exec_())
