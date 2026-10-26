"""Fetch exactly the recorded baseline versions; does not contain credentials."""
from pathlib import Path
import argparse,json,subprocess
p=argparse.ArgumentParser();p.add_argument('--root',default='D:/STGPlanner/benchmarks');a=p.parse_args()
root=Path(a.root);lock=json.loads((root/'sources.lock.json').read_text(encoding='utf-8'))
items=[(root/'sources'/name,v['url'],v['commit']) for name,v in lock.items() if name!='gbp_dependencies']
items.extend((root/'sources/gbp_dependencies'/v['name'],v['url'],v['commit']) for v in lock['gbp_dependencies'])
for path,url,commit in items:
    path.parent.mkdir(parents=True,exist_ok=True)
    prefix=['git','-c','http.proxy=','-c','https.proxy=','-c','http.version=HTTP/1.1','-c','core.autocrlf=false']
    if not (path/'.git').exists():subprocess.run(prefix+['clone',url,str(path)],check=True)
    existing=subprocess.run(prefix+['-C',str(path),'cat-file','-e',commit+'^{commit}'],capture_output=True)
    if existing.returncode:subprocess.run(prefix+['-C',str(path),'fetch','origin',commit],check=True)
    subprocess.run(prefix+['-C',str(path),'checkout','--detach',commit],check=True)
    actual=subprocess.check_output(prefix+['-C',str(path),'rev-parse','HEAD'],text=True).strip()
    assert actual==commit
    print(path.name,actual,flush=True)
