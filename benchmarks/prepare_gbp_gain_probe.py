from pathlib import Path
import json,rospy
from voxblox_msgs.srv import FilePath
root=Path('/mnt/d/STGPlanner/benchmarks');rospy.init_node('prepare_gbp_gain_probe',anonymous=True)
rospy.set_param('/gbp_gain_probe',rospy.get_param('/gbplanner_node'))
rospy.wait_for_service('/gbplanner_node/save_map',timeout=10)
rospy.ServiceProxy('/gbplanner_node/save_map',FilePath)(str(root/'gbp_gain_snapshot.vxblx'))
rows=[json.loads(x) for x in (root/'results/repair_formal_gbp2_01/metrics.jsonl').read_text().splitlines()]
sample=rows[::30]+rows[-1:]
(root/'gbp_gain_positions.txt').write_text(''.join(str(x['x'])+' '+str(x['y'])+'\n' for x in sample))
print('Saved live native map and',len(sample),'actual visited positions for independent replay.')
