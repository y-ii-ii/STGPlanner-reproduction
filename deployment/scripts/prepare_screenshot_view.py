from pathlib import Path
import yaml
root = Path('/mnt/d/STGPlanner/catkin_ws/src/STGPlanner')
path = root/'stgp_planner/planner/resource/topo_planner.rviz'
backup = Path('/mnt/d/STGPlanner/logs/screenshot_demo')
backup.mkdir(exist_ok=True)
if not (backup/'topo_planner.original.rviz').exists():
    (backup/'topo_planner.original.rviz').write_bytes(path.read_bytes())
config = yaml.safe_load(path.read_text())
config['Panels'] = [p for p in config['Panels'] if p.get('Class') == 'rviz/Displays']
config['Window Geometry'] = {'Height': 900, 'Width': 1600, 'X': 30, 'Y': 30,
                             'Hide Left Dock': False, 'Hide Right Dock': True,
                             'Displays': {'collapsed': False}}
view = config['Visualization Manager']['Views']['Current']
view.update({'Distance': 190.0, 'Pitch': 1.45, 'Yaw': -1.57, 'Target Frame': 'world',
             'Focal Point': {'X': 15.0, 'Y': 40.0, 'Z': 0.0}})
for panel in config['Panels']:
    if panel.get('Class') == 'rviz/Displays':
        panel['Help Height'] = 0
        panel['Tree Height'] = 700
        panel['Property Tree Widget']['Expanded'] = ['/RobotModel1', '/topo_map1', '/grid_map1']
        panel['Property Tree Widget']['Splitter Ratio'] = 0.6
path.write_text(yaml.safe_dump(config, sort_keys=False))
print('RViz window geometry and fixed world view prepared for this monitor.')
