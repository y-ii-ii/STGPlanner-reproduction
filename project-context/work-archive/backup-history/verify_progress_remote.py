"""Verify private remote, new repair and immutable old baselines; no credential output."""
from pathlib import Path
import base64,datetime,json,os,subprocess,urllib.request
repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner');out=Path(__file__).resolve().parents[1]/'outputs'
env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
r=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\nusername=y-ii-ii\n\n',capture_output=True,text=True,env=env,check=True)
credentials=dict(x.split('=',1) for x in r.stdout.splitlines() if '=' in x)
opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def api(path):
    req=urllib.request.Request('https://api.github.com'+path,headers={'Authorization':'Bearer '+credentials['password'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'Scene4-progress-verification'})
    with opener.open(req,timeout=30) as response:return json.load(response)
prefix='/repos/y-ii-ii/STGPlanner-reproduction';account=api('/user');remote=api(prefix)
def ref(name):return api(prefix+'/git/ref/'+name)['object']['sha']
def tag(name):return api(prefix+'/git/tags/'+ref('tags/'+name))['object']['sha']
head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
assert account['login']=='y-ii-ii' and remote['private']
assert ref('heads/fix/fael-gbp2-progress')==tag('scene4-progress-fix-2026-10-27')==head
assert ref('heads/main')==tag('repro-baseline-2026-10-26')=='dfc712982891f29c266083d7efad72ad48e730a2'
assert ref('heads/benchmark/scene4-baselines')==tag('scene4-baselines-2026-10-27')=='9dec3c45184259a0d68e3dfe066040966d807aed'
payload=api(prefix+'/contents/evidence/scene4-progress-fix/validation.json?ref=fix%2Ffael-gbp2-progress')
validation=json.loads(base64.b64decode(payload['content']))
assert validation['protocol_checks_passed']
value={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository':remote['full_name'],'private':remote['private'],'branch':'fix/fael-gbp2-progress','commit':head,'tag':'scene4-progress-fix-2026-10-27','old_main_and_baseline_refs_preserved':True,'remote_protocol_checks_passed':validation['protocol_checks_passed'],'remote_exploration_goals_passed':validation['exploration_goals_passed'],'check_count':len(validation['checks'])}
(out/'Scene4修复GitHub上传验证.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps(value,ensure_ascii=False,indent=2))
