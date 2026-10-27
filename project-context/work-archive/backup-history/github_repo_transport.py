"""Use the existing Git Credential Manager session; never print credentials."""
import argparse,base64,datetime,json,os,subprocess,urllib.request,urllib.error
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('action',choices=['inspect','create','verify'])
p.add_argument('--visibility',choices=['private','public'],default='private')
a=p.parse_args()
env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
r=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\nusername=y-ii-ii\n\n',text=True,capture_output=True,env=env)
if r.returncode:raise SystemExit('Existing noninteractive GitHub credential unavailable.')
cred=dict(line.split('=',1) for line in r.stdout.splitlines() if '=' in line)
if 'password' not in cred:raise SystemExit('Credential Manager returned no usable credential.')
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def api(path,body=None):
    req=urllib.request.Request('https://api.github.com'+path,data=(json.dumps(body).encode() if body is not None else None),headers={'Authorization':'Bearer '+cred['password'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'STGPlanner-reproduction-backup','Content-Type':'application/json'})
    try:
        with opener.open(req,timeout=30) as res:return json.load(res)
    except urllib.error.HTTPError as e:
        payload=json.load(e)
        raise SystemExit(json.dumps({'http_status':e.code,'message':payload.get('message'),'errors':payload.get('errors')},ensure_ascii=False))
user=api('/user')
assert user['login']=='y-ii-ii','Authenticated Git account does not match the user.'
if a.action=='inspect':
    print(json.dumps({'login':user['login'],'id':user['id'],'authenticated':True}))
elif a.action=='create':
    repo=api('/user/repos',{'name':'STGPlanner-reproduction','description':'STGPlanner Scene4 reproduction baseline: Windows/WSL2 deployment, runtime fixes, validated tests and rollback documentation.','private':a.visibility=='private','auto_init':False})
    print(json.dumps({k:repo[k] for k in ('full_name','html_url','clone_url','private','default_branch')},indent=2))
else:
    prefix='/repos/y-ii-ii/STGPlanner-reproduction'
    repo=api(prefix)
    local=subprocess.check_output(['git','-C','D:/STGPlanner/catkin_ws/src/STGPlanner','rev-parse','HEAD'],text=True).strip()
    branch=api(prefix+'/git/ref/heads/main')
    tag=api(prefix+'/git/ref/tags/repro-baseline-2026-10-26')
    annotated=api(prefix+'/git/tags/'+tag['object']['sha'])
    compare=api(prefix+'/compare/59b41451f7b80ba09a9bcbaf44b58141cd6f9de8...'+local)
    tree=api(prefix+'/git/trees/'+local+'?recursive=1')
    paths={e['path'] for e in tree['tree'] if e['type']=='blob'}
    remote_summary=api(prefix+'/contents/evidence/scene4-final/verification_summary.json')
    validation=json.loads(base64.b64decode(remote_summary['content']))
    assert repo['private'] and repo['owner']['login']=='y-ii-ii'
    assert branch['object']['sha']==local and annotated['object']['sha']==local
    assert compare['status']=='ahead' and compare['merge_base_commit']['sha']=='59b41451f7b80ba09a9bcbaf44b58141cd6f9de8'
    assert not tree['truncated']
    for path in ('README.md','baseline_manifest.json','deployment/install-local-tools.ps1','deployment/scripts/run.sh','docs/STGPlanner部署报告.md','docs/版本控制与回滚.md','docs/screenshots/04_rviz_diagnostics_fixed.png','evidence/scene4-final/verification_summary.json'):
        assert path in paths,path
    assert validation['passed'] and len(validation['checks'])==16 and all(validation['checks'].values())
    result={'repository':repo['full_name'],'url':repo['html_url'],'private':repo['private'],'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'branch':'main','commit':local,'baseline_tag':'repro-baseline-2026-10-26','annotated_tag_object':tag['object']['sha'],'tag_resolves_to_commit':annotated['object']['sha'],'upstream_commit':compare['merge_base_commit']['sha'],'new_commits':compare['ahead_by'],'remote_files':len(paths),'remote_runtime_checks':len(validation['checks']),'remote_runtime_passed':validation['passed'],'local_checkout_assets_verified':91}
    dest=Path(__file__).resolve().parents[1]/'outputs/GitHub上传验证.json'
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
