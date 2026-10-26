from pathlib import Path
import json, subprocess, re
root=Path('/mnt/d/STGPlanner/benchmarks'); src=root/'sources'; cfg=root/'config';cfg.mkdir(exist_ok=True)
base=Path('/mnt/d/STGPlanner/catkin_ws/src/STGPlanner/stgp_planner')
(cfg/'coverage.yaml').write_text((base/'planner/resource/topo_planner_Scene4.yaml').read_text())
(cfg/'fael.yaml').write_text((src/'FAEL/fael_planner/planner/resource/topo_planner_1.yaml').read_text())
s=(src/'tare_planner/src/tare_planner/config/indoor.yaml').read_text()
for key,value in {'sub_state_estimation_topic_':'/sensor_to_world/odometry','sub_registered_scan_topic_':'/benchmark/registered_cloud','sub_terrain_map_topic_':'/benchmark/terrain_map','sub_terrain_map_ext_topic_':'/benchmark/terrain_map','kAutoStart':'false','kSensorRange':'12.0'}.items():
    s=re.sub(r'^'+re.escape(key)+r'\s*:.*$',key+' : '+value,s,flags=re.M)
(cfg/'tare.yaml').write_text(s)
s=(src/'gbplanner_ros/gbplanner/config/smb/gbplanner_config.yaml').read_text()
s=s.replace('size:               [0.8, 0.8, 0.2]','size:               [0.8, 0.6, 0.4]').replace('center_offset:      [0.0, 0.0, 0.0]','center_offset:      [0.0, 0.0, -0.2]')
s=s.replace('max_range:      20.0','max_range:      12.0').replace('min_val:        [-1000.0, -1000.0, -30.0]','min_val:        [-50.0, -20.0, -2.0]').replace('max_val:        [1000.0, 1000.0, 30.0]','max_val:        [80.0, 100.0, 3.0]')
s=s.replace('no_gain_zones_list: ["g1"]','no_gain_zones_list: []').replace('robot_height: 0.6','robot_height: 0.456').replace('geofence_checking_enable: true','geofence_checking_enable: false').replace('AreaList: ["GLeft", "GBack", "GRight"]','AreaList: []')
(cfg/'gbp2.yaml').write_text(s)
s=(src/'gbplanner_ros/gbplanner/config/smb/voxblox_sim_config.yaml').read_text().replace('max_ray_length_m: 50.0','max_ray_length_m: 12.0')
# Visualization publishers run only when requested by native code; no RViz subscribers.
(cfg/'voxblox.yaml').write_text(s)
terrain=(base/'robot_move/cmu_planner/terrain_analysis/launch/terrain_analysis.launch').read_text()
assert '<param name="clearDyObs" type="bool" value="true" />' in terrain
(cfg/'terrain_static.launch').write_text(terrain.replace('<param name="clearDyObs" type="bool" value="true" />','<param name="clearDyObs" type="bool" value="false" />'))
movement=(base/'exploration_manager/launch/robot_move.launch').read_text()
(cfg/'movement.launch').write_text(movement.replace('$(find terrain_analysis)/launch/terrain_analysis.launch',str(cfg/'terrain_static.launch')))
common='''<remap from="/odometry" to="/base_link/odometry"/>
<remap from="/explorer_inited" to="/explorer_node/explorer_inited"/>
<remap from="point_cloud" to="/jackal/velodyne/velodyne_points"/>
<remap from="sensor_odometry" to="/sensor_to_world/odometry"/>
<remap from="/base_odometry" to="/base_link/odometry"/>
<remap from="/terrain_map" to="/traversability_analysis_node/terrain_map"/>'''
for method in ['stgp','fael']:
    config=str(cfg/'fael.yaml') if method=='fael' else str(base/'planner/resource/topo_planner_Scene4.yaml')
    (cfg/(method+'.launch')).write_text('<launch><node pkg="planner" type="topo_planner_node" name="topo_planner_node" output="screen">'+common+'<rosparam command="load" file="'+config+'"/></node></launch>')
(cfg/'tare.launch').write_text('<launch><node pkg="tare_planner" type="tare_planner_node" name="tare_planner_node" ns="sensor_coverage_planner" output="screen"><rosparam command="load" file="'+str(cfg/'tare.yaml')+'"/></node></launch>')
(cfg/'gbp2.launch').write_text('<launch><node pkg="gbplanner" type="gbplanner_node" name="gbplanner_node" output="screen"><remap from="odometry" to="/sensor_to_world/odometry"/><remap from="/pointcloud" to="/jackal/velodyne/velodyne_points"/><rosparam command="load" file="'+str(cfg/'gbp2.yaml')+'"/><rosparam command="load" file="'+str(cfg/'voxblox.yaml')+'"/></node></launch>')
for path in cfg.iterdir():
    if path.is_file():path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines()).rstrip()+'\n')
locks={}
for name in ['tare_planner','FAEL','gbplanner_ros']:
    def git(*args):return subprocess.check_output(['git','-C',str(src/name),*args],text=True).strip()
    locks[name]={'url':git('remote','get-url','origin'),'commit':git('rev-parse','HEAD'),'branch':git('branch','--show-current')}
locks['gbp_dependencies']=json.loads((src/'gbp_dependencies/sources.lock.json').read_text())
(root/'sources.lock.json').write_text(json.dumps(locks,indent=2))
print(json.dumps(locks,indent=2))
