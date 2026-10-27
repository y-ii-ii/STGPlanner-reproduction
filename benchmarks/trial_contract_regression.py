"""Exercise actual GBP2 adapter with memory transport; assert shared scope unchanged."""
from pathlib import Path
import ast,copy,json,subprocess,threading,time,types,yaml
root=Path('/mnt/d/STGPlanner/benchmarks');archive=root/'trial_repairs'
before=ast.parse((archive/'benchmark_trial.py.before').read_text());after=ast.parse((root/'benchmark_trial.py').read_text())
def shared_ast(tree):
    tree=copy.deepcopy(tree)
    for node in ast.walk(tree):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='d' and node.func.attr=='update':
            node.keywords=[k for k in node.keywords if k.arg!='adapter_revision']
        if isinstance(node,ast.FunctionDef) and node.name=='driver':
            # Preserve STGPlanner/FAEL and TARE branches, omit only GBP2 else.
            outer=node.body[0].body[0];tare=outer.orelse[0];tare.orelse=[ast.Pass()]
    return ast.dump(tree,include_attributes=False)
checks={'shared_protocol_ast_unchanged_outside_gbp_branch':shared_ast(before)==shared_ast(after)}
function=next(n for n in after.body if isinstance(n,ast.FunctionDef) and n.name=='driver')
def exercise(statuses,empty=False,motion_state=3):
    finished=threading.Event();calls=[];paths=[];events=[];paused=[];failures=[]
    data={'request_wall_s':[],'planner_states':{},'motion_states':{},'empty_plans':0,'native_finished':False}
    def service(request):
        if len(calls)>=len(statuses):raise RuntimeError('Extra native request after end')
        status=statuses[len(calls)];calls.append(status)
        return types.SimpleNamespace(status=status,path=[] if empty and status==2 else [object()])
    def request():return types.SimpleNamespace(header=types.SimpleNamespace(stamp=None,frame_id=None),root_pose=types.SimpleNamespace(orientation=types.SimpleNamespace(w=0)))
    def finish(reason):failures.append(reason);finished.set()
    fake_ros=types.SimpleNamespace(wait_for_service=lambda *a,**k:None,ServiceProxy=lambda *a:service,ServiceException=RuntimeError,Time=types.SimpleNamespace(now=lambda:0),get_time=lambda:110.)
    namespace={'a':types.SimpleNamespace(method='gbp2'),'rospy':fake_ros,'planner_srv':object(),'planner_srvRequest':request,'finished':finished,'time':time,'d':data,'start_sim':100.,'ground_path':lambda x:x,'send_paths':lambda x:paths.append(x),'motion':types.SimpleNamespace(get_state=lambda:motion_state,cancel_all_goals=lambda:None),'event':lambda *a,**k:events.append((a,k)),'finish':finish,'pause_pub':types.SimpleNamespace(publish=lambda x:paused.append(x)),'Bool':lambda x:x,'traceback':types.SimpleNamespace(format_exc=lambda:'fixture')}
    exec(compile(ast.Module(body=[function],type_ignores=[]),'actual_driver','exec'),namespace)
    thread=threading.Thread(target=namespace['driver'],daemon=True);thread.start();deadline=time.monotonic()+3
    while not data['native_finished'] and not finished.is_set() and time.monotonic()<deadline:time.sleep(.005)
    time.sleep(.12);finished.set();thread.join(1)
    return {'calls':calls,'native_finished':data['native_finished'],'finish_sim_s':data.get('native_finish_sim_s'),'path_empty':data.get('native_homing_path_empty'),'paused':paused,'failures':failures,'thread_stopped':not thread.is_alive()}
cases={
 'home_once':exercise([2]),
 'reposition_then_home':exercise([3,2]),
 'empty_home':exercise([2],empty=True),
 'failed_home_execution':exercise([2],motion_state=4),
}
checks['home_path_once_then_no_new_exploration']=cases['home_once']['calls']==[2] and cases['home_once']['native_finished'] and cases['home_once']['paused']==[True] and not cases['home_once']['failures']
checks['reposition_does_not_mean_finished']=cases['reposition_then_home']['calls']==[3,2] and not cases['reposition_then_home']['failures']
checks['empty_home_end_is_observed']=cases['empty_home']['native_finished'] and cases['empty_home']['path_empty'] and not cases['empty_home']['failures']
checks['failed_return_is_not_reported_as_success']=cases['failed_home_execution']['failures']==['native_homing_motion_failure']
checks['native_finish_time_separate_from_common_stop']=cases['home_once']['finish_sim_s']==10. and all(c['thread_stopped'] for c in cases.values())
native=Path('/opt/stgplanner/benchmarks/gbp2_ws/src/gbplanner/src/gbplanner.cpp').read_text()
helper=native.split('// BEGIN_NATIVE_GLOBAL_STATUS\n')[1].split('// END_NATIVE_GLOBAL_STATUS')[0]
program='''namespace planner_msgs{struct planner_srv{struct Response{static constexpr int kHoming=2,kRepositioning=3;};};}
'''+helper+'''int main(){return nativeGlobalResponseStatus(true)==2 && nativeGlobalResponseStatus(false)==3?0:1;}'''
source=Path('/opt/stgplanner/benchmarks/native_status_regression.cpp');source.write_text(program);binary=source.with_suffix('')
subprocess.run(['g++','-std=c++17',str(source),'-o',str(binary)],check=True)
checks['actual_native_status_helper_preserves_idl']=subprocess.run([str(binary)]).returncode==0
checks['native_global_and_sticky_homing_use_correct_status']=native.count('res.status = nativeGlobalResponseStatus')==2
old=yaml.safe_load((archive/'config__gbp2.yaml.before').read_text());new=yaml.safe_load((root/'config/gbp2.yaml').read_text())
def flatten(d,p=''):
    out={}
    for k,v in d.items():
        key=p+'/'+k
        if isinstance(v,dict):out.update(flatten(v,key))
        else:out[key]=v
    return out
a,b=flatten(old),flatten(new);changed={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
expected={'/PlanningParams/'+k for k in ['num_vertices_max','num_edges_max','num_loops_cutoff','num_loops_max','v_max','v_homing_max']}
expected.add('/SensorParams/VLP16/frontier_percentage_threshold')
checks['native_config_changes_are_explicit_and_limited']=changed==expected
old_sensor=copy.deepcopy(old['SensorParams']);new_sensor=copy.deepcopy(new['SensorParams'])
old_sensor['VLP16'].pop('frontier_percentage_threshold');new_sensor['VLP16'].pop('frontier_percentage_threshold')
checks['sensor_model_and_bounds_unchanged_except_declared_frontier_calibration']=new_sensor==old_sensor and new['BoundedSpaceParams']==old['BoundedSpaceParams']
value={'passed':all(checks.values()),'checks':checks,'cases':cases,'changed_native_config_keys':sorted(changed),'note':'Actual driver AST with memory-only ROS/action transport. Real sensor, controller and common measurement code are not changed; complete robot runs remain separate evidence.'}
(root/'trial_contract_regression.json').write_text(json.dumps(value,indent=2));print(json.dumps(value,indent=2))
if not value['passed']:raise SystemExit(1)
