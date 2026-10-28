"""Private branch verification and an independent restore; never persist credentials."""
import argparse
import datetime
import json
import os
import subprocess
import urllib.request
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--inspect',action='store_true')
parser.add_argument('--preflight-name',default='backup_preflight.json',choices=['backup_preflight.json','backup_pre_push.json'])
parser.add_argument('--restore',type=Path)
parser.add_argument('--receipt-name',default='GBP2_OPTIMIZATION_BACKUP_VERIFIED.json',choices=['GBP2_OPTIMIZATION_BACKUP_VERIFIED.json','GBP2_OPTIMIZATION_FINAL_HEAD_VERIFIED.json'])
args=parser.parse_args()
root=Path('D:/STGPlanner');repo=root/'catkin_ws/src/STGPlanner'
out=root/'codex/outputs/gbp2_optimization_20261028'
env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
git=['git','-c','core.longpaths=true','-c','http.proxy=','-c','https.proxy=']
credential=subprocess.run(git+['-C',str(repo),'credential','fill'],
    input='protocol=https\nhost=github.com\nusername=y-ii-ii\n\n',capture_output=True,text=True,env=env,check=True)
fields=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
assert fields.get('password')
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def api(path):
    request=urllib.request.Request('https://api.github.com/repos/y-ii-ii/STGPlanner-reproduction'+path,
        headers={'Authorization':'Bearer '+fields['password'],'Accept':'application/vnd.github+json',
                 'X-GitHub-Api-Version':'2022-11-28','User-Agent':'STGPlanner-GBP2-optimization-verification'})
    with opener.open(request,timeout=40) as response:return json.load(response)
metadata=api('');assert metadata['private'] and metadata['full_name']=='y-ii-ii/STGPlanner-reproduction'
protected={}
for name,expected in {'heads/main':'dfc712982891f29c266083d7efad72ad48e730a2',
    'heads/benchmark/scene4-baselines':'9dec3c45184259a0d68e3dfe066040966d807aed',
    'tags/repro-baseline-2026-10-26':'dfc712982891f29c266083d7efad72ad48e730a2',
    'tags/scene4-baselines-2026-10-27':'9dec3c45184259a0d68e3dfe066040966d807aed'}.items():
    reference=api('/git/ref/'+name)['object']
    if reference['type']=='tag':reference=api('/git/tags/'+reference['sha'])['object']
    assert reference['sha']==expected,name
    protected[name]=expected
remote=api('/git/ref/heads/fix/fael-gbp2-progress')['object']['sha']
head=subprocess.check_output(git+['-C',str(repo),'rev-parse','HEAD'],text=True).strip()
value={'verified_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
       'repository':metadata['full_name'],'private':True,'branch':'fix/fael-gbp2-progress',
       'remote_commit':remote,'local_commit':head,'protected_refs_unchanged':protected}
assert remote==head,'Remote moved; reconcile without force pushing'
if args.inspect:
    target=out/args.preflight_name;assert not target.exists()
else:
    destination=args.restore;assert destination is not None
    destination.resolve().relative_to((root/'codex/work/restores').resolve())
    assert not json.loads((root/'codex/SIMULATION_LOCK.json').read_text(encoding='utf-8'))['runtime_active']
    assert not subprocess.check_output(git+['-C',str(repo),'status','--porcelain']).strip()
    destination.parent.mkdir(parents=True,exist_ok=True)
    with (out/'backup_restore.log').open('a',encoding='utf-8') as log:
        if destination.exists():
            assert not subprocess.check_output(git+['-C',str(destination),'status','--porcelain']).strip()
            subprocess.run(git+['-C',str(destination),'pull','--ff-only'],stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
        else:
            subprocess.run(git+['clone','--branch','fix/fael-gbp2-progress',
                'https://github.com/y-ii-ii/STGPlanner-reproduction.git',str(destination)],stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
    assert subprocess.check_output(git+['-C',str(destination),'rev-parse','HEAD'],text=True).strip()==head
    assert not subprocess.check_output(git+['-C',str(destination),'status','--porcelain']).strip()
    verify=out/'remote_restore_validation.json'
    subprocess.run(['python',str(repo/'benchmarks/gbp2_optimization_20261028/verify_delivery.py'),
                    '--repo',str(destination),'--output',str(verify)],check=True,stdout=subprocess.DEVNULL)
    value.update(remote_head_matches_local=True,restored_checkout=str(destination),restored_checkout_clean=True,
                 verification=json.loads(verify.read_text(encoding='utf-8')))
    target=out/args.receipt_name
target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
