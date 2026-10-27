from pathlib import Path
import json, re, zipfile, hashlib
root=Path(__file__).resolve().parents[1]/'outputs'
md=(root/'STGPlanner部署报告.md').read_text(encoding='utf-8')
html=(root/'STGPlanner部署报告.html').read_text(encoding='utf-8')
for rel in re.findall(r'!\[[^\]]*\]\(([^)]+)\)',md):
    assert (root/rel).is_file(),rel
assert html.count('src="data:image/')==6
assert '{{' not in md
assert '更新进行中' not in md
manifest=json.loads((root/'screenshots/capture_manifest.json').read_text())
latest=manifest[-1]
assert hashlib.sha256((root/'screenshots'/latest['file']).read_bytes()).hexdigest()==latest['sha256']
assert all(d['enabled'] and all(s['name']=='Status: Ok' for s in d['status']) for d in latest['status'].values())
assert json.loads((root/'RViz修复验证结果.json').read_text())['passed']
assert json.loads((root/'长时间运行验证结果.json').read_text())['passed']
strict=json.loads((root/'长时间运行验证结果.json').read_text())
assert len(strict['checks'])==16 and all(strict['checks'].values())
assert strict['max_post_finish_command']==0 and strict['stop_action_status']==3
with zipfile.ZipFile(root/'STGPlanner部署材料.zip') as z:
    names=z.namelist()
    for item in ('screenshots/04_rviz_diagnostics_fixed.png','RViz修复验证结果.json','scripts/repair_rviz_sources.py','scripts/rviz_native_capture.cpp','logs/rviz_repair/verification_summary.json'):
        assert item in names,item
    patch=z.read('logs/deploy-fixes.patch').decode('utf-8')
    for source in ('VLP_16.urdf.xacro','global_topo_manager.cpp','grid_map_2d.cpp','control_planner_interface.cpp','explorer.cpp','exploration_data.cpp','path_execution.cpp','pathFollower.cpp'):
        assert source in patch,source
    assert z.testzip() is None
for filename in ('STGPlanner部署报告.md','STGPlanner部署报告.html','STGPlanner部署材料.zip'):
    assert (root/filename).read_bytes()==(Path('D:/STGPlanner')/filename.replace('STGPlanner','')).read_bytes()
print('PASS: six embedded images, enabled/Ok status evidence, long lifecycle result, source patches, archive CRC, D-drive copies.')
