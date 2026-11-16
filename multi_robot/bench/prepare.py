"""Prepare fresh frozen Scene4 configuration. Does not launch a ROS process."""
import argparse,copy,json,shutil,os,xml.etree.ElementTree as E
from common import *
from team_topology.prepare_stack import transform,set_param,set_remap

def sandbox(folder):
    (folder/'diagnostics/exploration_data').mkdir(parents=True)
    (folder/'diagnostics/vis2').mkdir()
    (folder/'ros_home').mkdir()
    pkg=folder/'sandbox/stgp_planner/planner';pkg.mkdir(parents=True)
    shutil.copy2(NATIVE/'src/planner/package.xml',pkg/'package.xml')
    (folder/'sandbox/files').symlink_to(folder/'diagnostics',target_is_directory=True)
    return str(pkg.parent)+':'+os.environ['ROS_PACKAGE_PATH']

def prepare(index):
    idle();out=result_path(index);out.mkdir(exist_ok=False);f=out/'frozen';f.mkdir()
    for p in (REF/'frozen').iterdir():
        if p.suffix in ('.world','.yaml','.urdf'):shutil.copy2(p,f/p.name)
    sim=E.fromstring((REF/'frozen/simulation.launch').read_text().replace(str(REF),str(out)))
    root=transform(E.fromstring((REF/'frozen/stack.launch').read_text().replace(str(REF),str(out))),str(out/'runtime'),str(NATIVE))
    # Sensors/local maps survive initialization. Only the legacy initialization
    # executor is replaced after a verified stop; exploration uses the new ABI.
    execution=E.Element('launch');exploration=E.Element('launch')
    for g in root.findall('group'):
        r=g.get('ns');prefix='/'+r
        planner=g.find("node[@name='topo_planner_node']")
        set_remap(planner,'point_cloud',prefix+'/team/cloud');set_remap(planner,'sensor_odometry',prefix+'/team/odom')
        env=planner.find("env[@name='ROS_PACKAGE_PATH']");env.set('value',sandbox(out/r/'planner/private'))
        planner.find("env[@name='LD_LIBRARY_PATH']").set('value',str(PLANNER/'devel/lib')+':'+str(NATIVE/'devel/lib')+':$(optenv LD_LIBRARY_PATH)')
        explorer=g.find("node[@name='explorer_node']");g.remove(explorer)
        ge=E.SubElement(exploration,'group',ns=r);ge.append(explorer)
        set_param(explorer,'run_mode','kReal')  # Simulation is already owned/unpaused.
        node=g.find("node[@name='path_execution_node']")
        ge=E.SubElement(execution,'group',ns=r);ge.append(copy.deepcopy(node))
        set_param(node,'team/topology_enabled',False);node.set('required','false')
    inc=root.find('include');root.remove(inc);exploration.append(inc)
    mapping=E.fromstring((REF/'frozen/mapping.launch').read_text().replace(str(REF),str(out)))
    for g in mapping.findall('group'):
        r=g.get('ns');node=g.find('node');folder=out/r/'score';folder.mkdir(parents=True)
        node.find("env[@name='ROS_PACKAGE_PATH']").set('value',sandbox(folder/'private'))
        node.find("env[@name='ROS_HOME']").set('value',str(folder/'private/ros_home'))
    for name,xml in [('simulation',sim),('stack',root),('mapping',mapping),('execution',execution),('exploration',exploration)]:
        E.ElementTree(xml).write(f/(name+'.launch'),encoding='utf-8',xml_declaration=True)
    reference=json.loads((REF/'manifest.json').read_text())
    checks={'same_world':sha(f/'Scene4.world')==reference['world_sha256'],
            'same_physical_configs':all(sha(f/p)==sha(REF/'frozen'/p) for p in ('robot_1.urdf','robot_2.urdf','robot_1_controllers.yaml','robot_2_controllers.yaml')),
            'same_scoring_configs':all(sha(f/(r+'_planner.yaml'))==sha(REF/'frozen'/(r+'_planner.yaml')) for r in ('robot_1','robot_2'))}
    assert all(checks.values()),checks
    executables={str(p):sha(p) for p in [PLANNER/'devel/lib/planner/topo_planner_node',PLANNER/'devel/lib/libtopo_planner.so',NATIVE/'devel/lib/path_execution/path_execution_node',NATIVE/'devel/lib/libpath_execution.so',NATIVE/'devel/lib/libcontrol_planner_interface.so',SCORE_CODE/'bin/team_score',Path('/opt/stgplanner/catkin_ws/devel/lib/libtopo_planner.so')]}
    implementation={p.relative_to(CODE).as_posix():sha(p) for sub in ('bench','team_topology') for p in (CODE/sub).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    dump(out/'manifest.json',dict(index=index,robot_count=2,checks=checks,executables=executables,implementation_sha256=implementation,
         frozen_sha256={p.name:sha(p) for p in f.iterdir() if p.is_file()},speed_m_s=2.,score_resolution_m=.4,range_m=12.,denominator_m2=7790.,threshold_m2=7400.5,
         world_clock_origin_s=15228.482,initialization_targets={'robot_1':[3.5,0.],'robot_2':[1.2,0.]},initialization_speed_m_s=.6,max_wall_s=2400,max_sim_s=2400,
         communication='perfect topology/task/path/traffic state; no peer cloud insertion',native_workspace=str(NATIVE),planner_workspace=str(PLANNER),python_overlay=str(OVERLAY)))
    dump(out/'offline_preflight.json',dict(all_passed=True,checks=checks))
    print(out)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--index',type=int,required=True);prepare(p.parse_args().index)
