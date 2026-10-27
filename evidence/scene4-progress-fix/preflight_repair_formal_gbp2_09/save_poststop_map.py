"""Wait on disk; only request an observational map save after exploration finishes."""
import hashlib
import json
import time
from pathlib import Path

out = Path('/mnt/d/STGPlanner/benchmarks/results/repair_formal_gbp2_09')
deadline = time.monotonic() + 11000
finish = None
while time.monotonic() < deadline:
    try:
        lines = (out / 'events.jsonl').read_text().splitlines()
        events = []
        for line in lines:
            try: events.append(json.loads(line))
            except json.JSONDecodeError: pass
        finish = next((event for event in events if event['kind']=='finish'), None)
    except OSError: pass
    if finish or (out/'result.json').exists(): break
    time.sleep(.2)
record = {'after_finish_only': True, 'finish_event': finish, 'changes_planning_or_motion': False}
if finish:
    try:
        import rospy
        from voxblox_msgs.srv import FilePath
        rospy.init_node('save_native_map_after_finish_07', anonymous=True, disable_signals=True)
        rospy.wait_for_service('/gbplanner_node/save_map', timeout=3)
        path = out / 'poststop_native_map.vxblx'
        response = rospy.ServiceProxy('/gbplanner_node/save_map',FilePath)(str(path))
        record.update(response=str(response), exists=path.exists())
        if path.exists(): record.update(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    except Exception as error: record['error'] = str(error)
else: record['error'] = 'No finish event observed'
(out/'poststop_map_capture.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record, indent=2))
