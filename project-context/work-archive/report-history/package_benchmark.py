from pathlib import Path
import gzip,hashlib,json,shutil,zipfile,datetime
task=Path(__file__).resolve().parents[1];out=task/'outputs';root=Path('D:/STGPlanner/benchmarks');repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner')
evidence=repo/'evidence/scene4-baselines';evidence.mkdir(parents=True,exist_ok=True)
def gz(source,dest):
    with source.open('rb') as f,dest.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as g:shutil.copyfileobj(f,g)
for directory in sorted((root/'results').iterdir()):
    if not directory.is_dir():continue
    target=evidence/directory.name;target.mkdir(exist_ok=True)
    for name in ['result.json','interruption.json','events.jsonl','metrics.jsonl','trajectory.csv']:
        source=directory/name
        if source.exists():shutil.copy2(source,target/name)
    if directory.name.startswith('formal_'):
        for name in ['known_plane_cells.csv','native_planner.log','movement.log','simulation.log','coverage.log','cloud_bridge.log','fael_traversability.log']:
            source=directory/name
            if source.exists():gz(source,target/(name+'.gz'))
        if (directory/'coverage.ufo').exists():shutil.copy2(directory/'coverage.ufo',target/'coverage.ufo')
for name in ['validation.json','environment.json','runtime_linkage.txt','sources.lock.json','protocol_manifest.json','protocol2_manifest.json','path_contract_regression.json']:
    shutil.copy2(root/name,evidence/name)
for name in ['fael_stall_probe.json','fael_obstacles_probe.json']:
    shutil.copy2(root/'logs'/name,evidence/name)
for source in (root/'logs').glob('*.log'):
    if source.name.startswith(('build_','suite','gbp_runtime_build','path_progress_build')):gz(source,evidence/(source.name+'.gz'))
for source in (root/'logs').glob('*.err'):
    if source.name.startswith('formal_'):gz(source,evidence/(source.name+'.gz'))
for name in ['validate_benchmark.py','plot_benchmark.py','make_benchmark_report.py','record_linkage.py']:
    shutil.copy2(root/name,repo/'benchmarks'/name)
for name in ['Scene4基线算法对比报告.md','Scene4基线算法对比报告.html','Scene4对比结果.json','Scene4测试协议.md','scene4_curves.png','scene4_maps.png','scene4_paper_comparison.png']:
    shutil.copy2(out/name,repo/'docs'/name)
shutil.copy2(out/'STGPlanner部署报告.md',repo/'docs/STGPlanner部署报告.md');shutil.copy2(out/'STGPlanner部署报告.html',repo/'docs/STGPlanner部署报告.html')
manifest={str(p.relative_to(repo)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in evidence.rglob('*') if p.is_file() and p.name!='evidence_manifest.json'}
(out/'Scene4证据校验清单.json').write_text(json.dumps({'generated':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':manifest},indent=2),encoding='utf-8',newline='\n')
shutil.copy2(out/'Scene4证据校验清单.json',evidence/'evidence_manifest.json')
# Bundle is created after the final Git commit, then added separately below.
with zipfile.ZipFile(out/'Scene4基线对比材料.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for folder in ['results','config','patches','logs']:
        for source in sorted((root/folder).rglob('*')):
            if source.is_file():archive.write(source,'benchmark/'+source.relative_to(root).as_posix())
    for source in sorted((repo/'benchmarks').rglob('*')):
        if source.is_file():archive.write(source,'code/'+source.relative_to(repo).as_posix())
    for name in ['Scene4基线算法对比报告.md','Scene4基线算法对比报告.html','Scene4对比结果.json','Scene4测试协议.md','scene4_curves.png','scene4_maps.png','scene4_paper_comparison.png','Scene4证据校验清单.json']:
        archive.write(out/name,'report/'+name)
print('Prepared evidence files:',len(manifest),'archive bytes:',(out/'Scene4基线对比材料.zip').stat().st_size)
