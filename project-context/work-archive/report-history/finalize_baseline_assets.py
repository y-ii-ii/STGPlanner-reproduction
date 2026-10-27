from pathlib import Path
import hashlib,json
repo=Path('D:/STGPlanner/catkin_ws/src/STGPlanner')
attributes=repo/'.gitattributes'
text=attributes.read_text(encoding='utf-8')
rules='''/deployment/** text=auto eol=lf
/docs/** text=auto eol=lf
/evidence/** text=auto eol=lf
/baseline_manifest.json text eol=lf
/deployment/windows/*.cmd text eol=crlf
/deployment/windows/*.ps1 text eol=crlf
'''
if rules not in text:attributes.write_bytes((text.rstrip()+'\n'+rules).encode())
manifest_path=repo/'baseline_manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
for relative in manifest['assets']:
    path=repo/relative
    data=path.read_bytes()
    try:
        decoded=data.decode('utf-8')
    except UnicodeDecodeError:
        continue
    if b'\0' in data[:8192] or path.suffix.lower() in ('.png','.jpg','.jpeg'):continue
    decoded=decoded.replace('\r\n','\n').replace('\r','\n')
    if path.suffix.lower() in ('.ps1','.cmd'):decoded=decoded.replace('\n','\r\n')
    path.write_bytes(decoded.encode())
manifest['assets']={relative:hashlib.sha256((repo/relative).read_bytes()).hexdigest() for relative in manifest['assets']}
manifest_path.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())
for rel,digest in manifest['assets'].items():
    assert hashlib.sha256((repo/rel).read_bytes()).hexdigest()==digest
for image in ('01_gazebo_scene4.jpg','02_rviz_mapping.jpg','03_exploration_metrics.jpg','04_rviz_diagnostics_fixed.png'):
    assert (repo/'docs/screenshots'/image).is_file()
print('Portable text line endings and {} asset SHA256 values verified.'.format(len(manifest['assets'])))
