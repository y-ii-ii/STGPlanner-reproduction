"""Verify the pushed repair by a new remote checkout and all evidence hashes."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess
task=Path(__file__).resolve().parents[1];repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner')
dest=task/'work'/('progress-remote-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
subprocess.run(['git','-c','http.proxy=','-c','https.proxy=','clone','--branch','fix/fael-gbp2-progress','https://github.com/y-ii-ii/STGPlanner-reproduction.git',str(dest)],check=True,env=env)
def git(*args):return subprocess.check_output(['git','-C',str(dest),*args],text=True).strip()
local=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
assert git('rev-parse','HEAD')==git('rev-parse','scene4-progress-fix-2026-10-27^{}')==local
assert git('rev-parse','origin/main')==git('rev-parse','repro-baseline-2026-10-26^{}')=='dfc712982891f29c266083d7efad72ad48e730a2'
assert git('rev-parse','origin/benchmark/scene4-baselines')==git('rev-parse','scene4-baselines-2026-10-27^{}')=='9dec3c45184259a0d68e3dfe066040966d807aed'
assert not git('status','--porcelain')
manifest=json.loads((dest/'evidence/scene4-progress-fix/evidence_manifest.json').read_text(encoding='utf-8'))
bad=[name for name,expected in manifest['files'].items() if hashlib.sha256((dest/name).read_bytes()).hexdigest()!=expected]
assert not bad,bad
v=json.loads((dest/'evidence/scene4-progress-fix/validation.json').read_text(encoding='utf-8'));assert v['protocol_checks_passed']
value={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commit':local,'fresh_remote_checkout':str(dest),'all_recorded_file_hashes_passed':True,'file_count':len(manifest['files']),'protected_refs_preserved':True,'protocol_checks_passed':v['protocol_checks_passed'],'exploration_goals_passed':v['exploration_goals_passed'],'clean_checkout':True}
(task/'outputs/Scene4修复远程克隆校验.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
