"""Derive nominal sensor-to-ground height from the captured runtime URDF."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import yaml
root=Path('/mnt/d/STGPlanner')
folder=root/'benchmarks/results/gbp2_default_frontier_20261028_10'
params=yaml.safe_load((folder/'live_rosparams.yaml').read_text())
robot=ET.fromstring(params['robot_description'])
joints={j.find('child').attrib['link']:j for j in robot.findall('joint')}
links={link.attrib['name']:link for link in robot.findall('link')}
def height(link):
    z=0.;chain=[]
    while link!='base_link':
        j=joints[link];origin=j.find('origin')
        xyz=[float(x) for x in origin.attrib.get('xyz','0 0 0').split()] if origin is not None else [0.,0.,0.]
        rpy=[float(x) for x in origin.attrib.get('rpy','0 0 0').split()] if origin is not None else [0.,0.,0.]
        assert all(abs(x)<1e-8 for x in rpy),'This simple chain audit expects zero joint rotation'
        z+=xyz[2];chain.append({'joint':j.attrib['name'],'xyz':xyz,'parent':j.find('parent').attrib['link']})
        link=j.find('parent').attrib['link']
    return z,chain
sensor_z,sensor_chain=height('jackal/velodyne/VLP_16')
wheels=[]
for name,link in links.items():
    if name.endswith('_wheel_link'):
        center,chain=height(name)
        cylinder=link.find('collision/geometry/cylinder');assert cylinder is not None
        radius=float(cylinder.attrib['radius'])
        wheels.append({'link':name,'center_z':center,'radius':radius,'bottom_z':center-radius,'chain':chain})
assert len(wheels)==4
ground_z=sum(w['bottom_z'] for w in wheels)/4
assert max(w['bottom_z'] for w in wheels)-min(w['bottom_z'] for w in wheels)<1e-8
sensor_height=sensor_z-ground_z
snapshot=json.loads((folder/'sensor_frame_snapshot.json').read_text())
raw_sensor_z=snapshot['odometry']['/jackal/velodyne/gazebo_gt/odometry']['position'][2]
assert abs(sensor_height-raw_sensor_z)<.001
value={'source':'Captured runtime robot_description in10/live_rosparams.yaml',
       'sensor_z_above_base_link_m':sensor_z,'wheel_contact_z_in_base_link_m':ground_z,
       'nominal_sensor_z_above_wheel_contact_m':sensor_height,'old_native_robot_height_m':.456,
       'geometry_difference_m':sensor_height-.456,'raw_gazebo_sensor_z_on_flat_floor_m':raw_sensor_z,
       'geometry_agrees_with_flat_snapshot':True,'sensor_chain':sensor_chain,'wheels':wheels,
       'scope':'Robot geometry calibration only. Actual GBP2 odometry input is the sensor frame, so its nominal height above ground differs from sensor-to-base offset. No exploration targets or common coverage input. TSDF projection quantization and slopes remain separate errors.'}
out=root/'codex/outputs/gbp2_optimization_20261028'
(out/'sensor_ground_geometry.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k not in ['sensor_chain','wheels']},indent=2))
