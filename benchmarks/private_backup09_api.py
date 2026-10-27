"""Use existing Git authentication without printing credentials; verify private backup."""
import argparse
import base64
import datetime
import json
import os
import subprocess
import urllib.request
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');args=parser.parse_args()
repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner');out=Path('D:/STGPlanner/codex/outputs')
git=['git','-c','safe.directory='+str(repo),'-C',str(repo)]
env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
credential=subprocess.run(git+['credential','fill'],input='protocol=https\nhost=github.com\nusername=y-ii-ii\n\n',capture_output=True,text=True,env=env,check=True)
fields=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
assert fields.get('password'),'Existing Git credential unavailable'
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def api(path):
    request=urllib.request.Request('https://api.github.com/repos/y-ii-ii/STGPlanner-reproduction'+path,
        headers={'Authorization':'Bearer '+fields['password'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'STGPlanner-private-backup-verification'})
    with opener.open(request,timeout=45) as response:return json.load(response)
metadata=api('');assert metadata['private'] and metadata['full_name']=='y-ii-ii/STGPlanner-reproduction'
expected={'heads/main':'dfc712982891f29c266083d7efad72ad48e730a2','heads/benchmark/scene4-baselines':'9dec3c45184259a0d68e3dfe066040966d807aed','tags/repro-baseline-2026-10-26':'dfc712982891f29c266083d7efad72ad48e730a2','tags/scene4-baselines-2026-10-27':'9dec3c45184259a0d68e3dfe066040966d807aed'}
protected={}
for name,sha in expected.items():
    ref=api('/git/ref/'+name)['object']
    if ref['type']=='tag':ref=api('/git/tags/'+ref['sha'])['object']
    assert ref['sha']==sha,(name,ref['sha']);protected[name]=ref['sha']
branch=api('/git/ref/heads/fix/fael-gbp2-progress')['object']['sha']
value={'verified_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'repository':metadata['full_name'],'private':True,'branch':'fix/fael-gbp2-progress','remote_commit':branch,'protected_refs':protected,'mode':'after_push' if args.verify else 'pre_push'}
if args.verify:
    head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip();assert branch==head
    payload=api('/contents/evidence/scene4-progress-fix/validation.json?ref='+head)
    validation=json.loads(base64.b64decode(payload['content']))
    assert validation['protocol_checks_passed'] and not validation['exploration_goals_passed']
    assert validation['results']['fael']['after']['finish_reason']=='coverage_threshold'
    assert validation['results']['gbp2']['after']['finish_reason']=='sim_time_limit'
    value.update(remote_head_matches_local=True,protocol_checks_passed=True,exploration_goals_passed=False,
        fael_coverage=validation['results']['fael']['after']['coverage_fraction'],gbp2_coverage=validation['results']['gbp2']['after']['coverage_fraction'],check_count=len(validation['checks']))
(out/('私有仓库备份验证.json' if args.verify else '私有仓库备份前核对.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
