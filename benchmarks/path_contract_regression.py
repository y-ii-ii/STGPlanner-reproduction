"""Replay captured disconnected FAEL output with in-memory transport doubles.

No action or stop command is sent to the running simulation. This is separate
from all performance trials and checks a recorded integration failure.
"""
from pathlib import Path
import ast,copy,csv,json,math,re,time
import rospy
from geometry_msgs.msg import Pose
from std_msgs.msg import Bool
from control_planner_interface.msg import VehicleExecuteGoal,Path as PlannerPath
root=Path('/mnt/d/STGPlanner/benchmarks');probe=json.loads((root/'logs/fael_stall_probe.json').read_text())
class Motion:
    def __init__(self):self.goals=[];self.cancels=0
    def send_goal(self,g):self.goals.append(g)
    def cancel_all_goals(self):self.cancels+=1
class Publisher:
    def __init__(self):self.messages=[]
    def publish(self,m):self.messages.append(m.data)
class Finish:
    def is_set(self):return False
rospy.init_node('path_contract_regression',anonymous=True)
tree=ast.parse((root/'benchmark_trial.py').read_text());node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='send_paths')
module=ast.Module(body=[node],type_ignores=[]);ast.fix_missing_locations(module)
body=probe['/base_link/odometry']['pose'];xyz=[float(x) for x in re.findall(r'\b[xyz]:\s*([-+0-9.eE]+)',body)[:3]]
pose=Pose();pose.position.x,pose.position.y,pose.position.z=xyz
motion=Motion();publisher=Publisher();events=[]
env=dict(finished=Finish(),pose=pose,copy=copy,math=math,time=time,rospy=rospy,start_sim=rospy.get_time(),motion=motion,pause_pub=publisher,path_paused=False,last_rejection_log=0.,Bool=Bool,VehicleExecuteGoal=VehicleExecuteGoal,event=lambda *args,**kw:events.append((args,kw)),d={'rejected_disconnected_paths':0,'disconnected_path_examples':[],'nonempty_plans':0})
exec(compile(module,'captured_send_paths','exec'),env)
paths=[]
for segment in probe['/topo_planner_node/topo_planner/result']['segments']:
    p=PlannerPath()
    for x,y,z in segment:
        q=Pose();q.position.x=x;q.position.y=y;q.position.z=z;q.orientation.w=1;p.path.append(q)
    paths.append(p)
env['send_paths'](paths)
checks={'recorded_bad_plan_rejected':env['d']['rejected_disconnected_paths']==1,'no_bad_motion_goal_sent':not motion.goals,'previous_motion_cancelled':motion.cancels==1,'controller_pause_published':publisher.messages==[True]}
# Replay two consecutive real trajectory positions from the initial free run.
rows=list(csv.DictReader((root/'results/formal_fael_01/trajectory.csv').open()))
p=PlannerPath()
for row in rows[:2]:
    q=Pose();q.position.x=float(row['x']);q.position.y=float(row['y']);q.position.z=float(row['z']);q.orientation.w=1;p.path.append(q)
env['pose']=copy.deepcopy(p.path[0]);env['send_paths']([p])
checks.update(valid_recorded_geometry_accepted=len(motion.goals)==1,pause_released_for_valid_geometry=publisher.messages==[True,False])
result={'passed':all(checks.values()),'checks':checks,'source':'actual fael_stall_probe.json and formal FAEL trajectory','sent_to_real_vehicle':False}
(root/'path_contract_regression.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if not result['passed']:raise SystemExit(1)
