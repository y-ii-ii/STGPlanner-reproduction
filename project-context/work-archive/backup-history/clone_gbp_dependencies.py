from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess,json
root=Path('D:/STGPlanner/benchmarks/sources/gbp_dependencies')
root.mkdir(exist_ok=True)
deps=[
 ('catkin_simple','https://github.com/catkin/catkin_simple.git','0e62848b12da76c8cc58a1add42b4f894d1ac21e'),
 ('eigen_catkin','https://github.com/ethz-asl/eigen_catkin.git','00b5eb254bad8de9cd68d238aa994e443062cf30'),
 ('eigen_checks','https://github.com/ethz-asl/eigen_checks.git','22a6247a3df11bc285d43d1a030f4e874a413997'),
 ('gflags_catkin','https://github.com/ethz-asl/gflags_catkin.git','5324e74119996a6e2da12d20e5388c17480ebd79'),
 ('glog_catkin','https://github.com/ethz-asl/glog_catkin.git','dcb4559be6b9f9248c543df6789d46271c13efcf'),
 ('minkindr','https://github.com/ethz-asl/minkindr.git','bc4503c34970a13b7ef06f62505e3333395ce02c'),
 ('minkindr_ros','https://github.com/ethz-asl/minkindr_ros.git','88e0bd476f82027453f04fdf7c40c7c9a358aa1b'),
 ('mav_comm','https://github.com/ethz-asl/mav_comm.git','master'),
 ('yaml_cpp_catkin','https://github.com/ethz-asl/yaml_cpp_catkin.git','master'),
 ('protobuf_catkin','https://github.com/ethz-asl/protobuf_catkin.git','master'),
 ('voxblox','https://github.com/ntnu-arl/voxblox.git','dev/noetic'),
 ('adaptive_obb_ros','https://github.com/ntnu-arl/adaptive_obb_ros.git','master'),
]
def clone(dep):
    name,url,ref=dep;path=root/name
    if not (path/'.git').is_dir():
        args=['git','-c','http.proxy=','-c','https.proxy=','-c','http.version=HTTP/1.1','-c','core.autocrlf=false','clone']
        if len(ref)!=40:args+=['--depth','1','--branch',ref]
        r=subprocess.run(args+[url,str(path)],capture_output=True,text=True,timeout=180)
        if r.returncode:raise RuntimeError(name+': '+r.stderr)
    r=subprocess.run(['git','-C',str(path),'checkout',ref],capture_output=True,text=True)
    if r.returncode and ref=='master':
        subprocess.run(['git','-C',str(path),'checkout','main'],check=True,capture_output=True)
    elif r.returncode:raise RuntimeError(name+': '+r.stderr)
    sha=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
    print(name+' '+sha,flush=True)
    return {'name':name,'url':url,'ref':ref,'commit':sha}
with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(clone,deps))
(root/'sources.lock.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
