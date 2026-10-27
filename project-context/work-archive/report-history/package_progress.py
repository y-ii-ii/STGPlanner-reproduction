"""Final user archive; preserve every earlier baseline deliverable."""
from pathlib import Path
import datetime,hashlib,json,zipfile
task=Path(__file__).resolve().parents[1];out=task/'outputs';root=Path('D:/STGPlanner/benchmarks');repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner')
archive=out/'Scene4探索修复材料.zip'
selection=json.loads((root/'progress_trials.json').read_text())
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in ['formal_fael_01','formal_gbp2_01']+selection['pilot_runs']+selection['intermediate_runs']+list(selection['final_runs'].values()):
        for p in sorted((root/'results'/name).rglob('*')):
            if p.is_file():z.write(p,'benchmark/'+p.relative_to(root).as_posix())
    for name in ['gbp_gain_snapshot.vxblx','gbp_gain_positions.txt','gbp_gain_probe.json','gbp_gain_probe_calibrated.json','gbp_ground_snapshot.vxblx','gbp_ground_positions.txt','gbp_ground_context.json']:
        z.write(root/name,'benchmark/'+name)
    for folder in ['benchmarks','evidence/scene4-progress-fix']:
        for p in sorted((repo/folder).rglob('*')):
            if p.is_file():z.write(p,'repository/'+p.relative_to(repo).as_posix())
    for name in ['Scene4探索停滞修复报告.md','Scene4探索停滞修复报告.html','Scene4修复长测结果.json','scene4_progress_curves.png','scene4_progress_maps.png','Scene4修复证据校验清单.json','Scene4修复GitHub上传验证.json','Scene4修复远程克隆校验.json','STGPlanner-scene4-progress-fix.bundle']:
        z.write(out/name,'delivery/'+name)
files={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [archive,out/'STGPlanner-scene4-progress-fix.bundle',out/'Scene4探索停滞修复报告.md',out/'Scene4探索停滞修复报告.html',out/'Scene4修复长测结果.json',out/'Scene4修复GitHub上传验证.json',out/'Scene4修复远程克隆校验.json']}
(out/'Scene4修复交付校验.json').write_text(json.dumps({'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files},indent=2),encoding='utf-8',newline='\n')
print(json.dumps(files,indent=2))
