"""Verify private backup with Credential Manager; never print credentials."""
from pathlib import Path
import base64,datetime,json,os,subprocess,urllib.request
repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner');out=Path(__file__).resolve().parents[1]/'outputs'
env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
r=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\nusername=y-ii-ii\n\n',capture_output=True,text=True,env=env,check=True)
credentials=dict(x.split('=',1) for x in r.stdout.splitlines() if '=' in x)
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def api(path):
    request=urllib.request.Request('https://api.github.com'+path,headers={'Authorization':'Bearer '+credentials['password'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'Scene4-backup-verification'})
    with opener.open(request,timeout=30) as response:return json.load(response)
prefix='/repos/y-ii-ii/STGPlanner-reproduction';account=api('/user');remote=api(prefix)
head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
branch=api(prefix+'/git/ref/heads/benchmark/scene4-baselines');main=api(prefix+'/git/ref/heads/main')
tag=api(prefix+'/git/ref/tags/scene4-baselines-2026-10-27');tag_object=api(prefix+'/git/tags/'+tag['object']['sha'])
oldtag=api(prefix+'/git/ref/tags/repro-baseline-2026-10-26');old_object=api(prefix+'/git/tags/'+oldtag['object']['sha'])
payload=api(prefix+'/contents/evidence/scene4-baselines/validation.json?ref=benchmark%2Fscene4-baselines')
validation=json.loads(base64.b64decode(payload['content']))
assert account['login']=='y-ii-ii' and remote['private']
assert branch['object']['sha']==head and tag_object['object']['sha']==head
assert main['object']['sha']==old_object['object']['sha']=='dfc712982891f29c266083d7efad72ad48e730a2'
assert validation['passed'] and all(validation['checks'].values())
result={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository':remote['full_name'],'private':remote['private'],'branch':'benchmark/scene4-baselines','commit':head,'tag':'scene4-baselines-2026-10-27','tag_commit':tag_object['object']['sha'],'original_main_and_tag_preserved':True,'original_main_commit':main['object']['sha'],'remote_validation_passed':validation['passed'],'remote_check_count':len(validation['checks']),'results':validation['results']}
(out/'Scene4GitHub上传验证.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))
