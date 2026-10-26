#!/usr/bin/env python3
"""Small, repeatable launch and packaging repairs for upstream 59b4145."""
from pathlib import Path
import xml.etree.ElementTree as ET
import re

root = Path('/mnt/d/STGPlanner/catkin_ws/src/STGPlanner')
for subtree in ('3rdparty', 'stgp_planner'):
    for path in (root / subtree).rglob('*'):
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if raw.startswith(b'#!') or path.suffix in ('.sh', '.py') or 'configs' in path.parts:
            if b'\r\n' in raw:
                path.write_bytes(raw.replace(b'\r\n', b'\n'))
            if raw.startswith(b'#!'):
                path.chmod(path.stat().st_mode | 0o111)
(root / '.gitattributes').write_text('*.sh text eol=lf\n*.py text eol=lf\n3rdparty/jackal/jackal_description/scripts/* text eol=lf\n3rdparty/jackal/jackal_description/urdf/configs/* text eol=lf\n')

def replace(relative, old, new):
    path = root / relative
    text = path.read_text()
    if new in text:
        return
    if old not in text:
        raise RuntimeError('Unexpected upstream contents: ' + relative)
    path.write_text(text.replace(old, new))

replace('README.md', 'source devel/setup.zsh', 'source devel/setup.bash')
replace('README.md', 'roslaunch sim_env.launch', 'roslaunch exploration_manager sim_env.launch')
replace('stgp_planner/exploration_manager/launch/sim_env.launch', 'default="scene_2"', 'default="Scene4"')
replace('stgp_planner/exploration_manager/launch/sim_env.launch',
        '${GAZEBO_MODEL_PATH}:$(find exploration_manager)/mesh:$(find exploration_manager)/models',
        '$(optenv GAZEBO_MODEL_PATH)')
replace('stgp_planner/exploration_manager/launch/explorer.launch',
        '<arg name="world" default="default"/>',
        '<arg name="world" default="Scene4"/>\n    <arg name="rviz" default="true"/>\n    <arg name="plot" default="true"/>')
replace('stgp_planner/exploration_manager/launch/explorer.launch',
        '<arg name="topo_planner_params" value="topo_planner_$(arg world).yaml"/>',
        '<arg name="topo_planner_params" value="topo_planner_$(arg world).yaml"/>\n        <arg name="rviz" value="$(arg rviz)"/>')
replace('stgp_planner/exploration_manager/launch/explorer.launch',
        '<arg name="world" value="$(arg world)"/>',
        '<arg name="world" value="$(arg world)"/>\n        <arg name="plot" value="$(arg plot)"/>')
replace('stgp_planner/planner/launch/planner.launch',
        '<arg name="topo_planner_params" default="topo_planner_1.yaml"/>',
        '<arg name="topo_planner_params" default="topo_planner_Scene4.yaml"/>\n    <arg name="rviz" default="true"/>')
replace('stgp_planner/planner/launch/planner.launch',
        '<node name="planner_rviz"', '<node if="$(arg rviz)" name="planner_rviz"')
replace('stgp_planner/visualization_tools/launch/visualization_tools.launch',
        '<arg name="world" default="default"/>',
        '<arg name="world" default="Scene4"/>\n    <arg name="plot" default="true"/>')
replace('stgp_planner/visualization_tools/launch/visualization_tools.launch',
        '<node pkg="visualization_tools" type="realTimePlot.py"',
        '<node if="$(arg plot)" pkg="visualization_tools" type="realTimePlot.py"')
cmake = root / 'stgp_planner/visualization_tools/CMakeLists.txt'
if 'catkin_install_python(PROGRAMS scripts/realTimePlot.py' not in cmake.read_text():
    cmake.write_text(cmake.read_text() + '\ncatkin_install_python(PROGRAMS scripts/realTimePlot.py\n  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}\n)\n')
(root / 'files/exploration_data').mkdir(parents=True, exist_ok=True)
replace('stgp_planner/sensor_conversion/package.xml', '>tf_ros<', '>tf2_ros<')
manifest = root / 'stgp_planner/sensor_conversion/package.xml'
if '<depend>tf2_sensor_msgs</depend>' not in manifest.read_text():
    manifest.write_text(manifest.read_text().replace('</package>', '  <depend>tf2_sensor_msgs</depend>\n</package>'))
replace('stgp_planner/sensor_conversion/CMakeLists.txt',
        '        tf2_ros\n', '        tf2_ros\n        tf2_sensor_msgs\n')
replace('stgp_planner/sensor_conversion/CMakeLists.txt',
        'LIBRARIES simulation', 'LIBRARIES slam_output')
replace('stgp_planner/sensor_conversion/CMakeLists.txt',
        'CATKIN_DEPENDS message_filters geometry_msgs  nav_msgs pcl_ros roscpp sensor_msgs std_msgs tf\n',
        'CATKIN_DEPENDS message_filters geometry_msgs  nav_msgs pcl_ros roscpp sensor_msgs std_msgs tf tf2_ros tf2_sensor_msgs\n')
scene = root / 'stgp_planner/exploration_manager/worlds/Scene4.world'
original = scene.read_text()
before_models = sorted(e.get('name') for e in ET.fromstring(original).iter('model') if e.get('name') != 'jackal')
portable, removed = re.subn(r'(?m)^[ \t]*<model name=([\x27\x22])jackal\1>.*?^[ \t]*</model>\n?', '', original, flags=re.S)
if removed:
    after_models = sorted(e.get('name') for e in ET.fromstring(portable).iter('model'))
    if before_models != after_models:
        raise RuntimeError('Scene repair unexpectedly changed environment models')
    scene.write_text(portable)
    print('Removed {} saved Jackal model(s); environment models preserved.'.format(removed))
for path in root.rglob('*.launch'):
    ET.parse(path)
replace('stgp_planner/visualization_tools/scripts/realTimePlot.py',
        '            fig.canvas.draw()',
        '            fig.canvas.draw()\n            plt.pause(0.001)  # Process Tk events so the window stays responsive.')
import runpy
runpy.run_path('/mnt/d/STGPlanner/scripts/prepare_screenshot_view.py')
runpy.run_path('/mnt/d/STGPlanner/scripts/repair_rviz_sources.py')
runpy.run_path('/mnt/d/STGPlanner/scripts/repair_planner_completion.py')
runpy.run_path('/mnt/d/STGPlanner/scripts/fix_plot_events.py')
print('Deployment repairs applied; all launch XML files parse successfully.')
