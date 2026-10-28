"""Extract the actual simulated LiDAR model from the captured runtime URDF."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import yaml
root=Path('/mnt/d/STGPlanner');folder=root/'benchmarks/results/gbp2_default_frontier_20261028_10'
params=yaml.safe_load((folder/'live_rosparams.yaml').read_text())
tree=ET.fromstring(params['robot_description']);records=[]
for sensor in tree.findall('.//sensor'):
    if sensor.attrib.get('type') not in ['ray','gpu_ray']:continue
    records.append({'name':sensor.attrib.get('name'),'type':sensor.attrib.get('type'),
       'xml':ET.tostring(sensor,encoding='unicode')})
value={'source':'10/live_rosparams.yaml robot_description','captured_lidar_sensors':records,
       'scope':'Read-only source audit. Planning range, native integration cutoff and public observer cutoff are separate from the physical simulator maximum range.'}
out=root/'codex/outputs/gbp2_optimization_20261028/sensor_model_audit.json'
out.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(value,indent=2))
