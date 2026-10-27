"""Verify private remote and restore the Scene4 stage archive using existing Git auth."""
import argparse
import datetime
import json
import os
import subprocess
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--inspect', action='store_true')
parser.add_argument('--restore', type=Path)
args = parser.parse_args()
root = Path('D:/STGPlanner')
repo = root / 'catkin_ws/src/STGPlanner'
out = root / 'codex/outputs'
env = os.environ.copy()
env.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
git = ['git', '-c', 'core.longpaths=true', '-c', 'http.proxy=', '-c', 'https.proxy=']
credential = subprocess.run(git + ['-C', str(repo), 'credential', 'fill'],
    input='protocol=https\nhost=github.com\nusername=y-ii-ii\n\n', capture_output=True, text=True, env=env, check=True)
fields = dict(line.split('=', 1) for line in credential.stdout.splitlines() if '=' in line)
assert fields.get('password'), 'Existing Git credential unavailable'
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def api(path):
    request = urllib.request.Request('https://api.github.com/repos/y-ii-ii/STGPlanner-reproduction' + path,
        headers={'Authorization': 'Bearer ' + fields['password'], 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'STGPlanner-stage-archive-verification'})
    with opener.open(request, timeout=40) as response:
        return json.load(response)

metadata = api('')
assert metadata['private'] and metadata['full_name'] == 'y-ii-ii/STGPlanner-reproduction'
protected = {}
for name, sha in {'heads/main': 'dfc712982891f29c266083d7efad72ad48e730a2',
                  'heads/benchmark/scene4-baselines': '9dec3c45184259a0d68e3dfe066040966d807aed',
                  'tags/repro-baseline-2026-10-26': 'dfc712982891f29c266083d7efad72ad48e730a2',
                  'tags/scene4-baselines-2026-10-27': '9dec3c45184259a0d68e3dfe066040966d807aed'}.items():
    reference = api('/git/ref/' + name)['object']
    if reference['type'] == 'tag':
        reference = api('/git/tags/' + reference['sha'])['object']
    assert reference['sha'] == sha, name
    protected[name] = sha
remote = api('/git/ref/heads/fix/fael-gbp2-progress')['object']['sha']
value = {'verified_at': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
         'repository': metadata['full_name'], 'private': True, 'branch': 'fix/fael-gbp2-progress',
         'remote_commit': remote, 'protected_refs_unchanged': protected,
         'stage_status': 'stage_complete', 'GBP2_followup': 'paused_by_user'}
if args.inspect:
    (out / 'Scene4阶段备份前核对.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
else:
    head = subprocess.check_output(git + ['-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    assert remote == head, 'Remote HEAD mismatch'
    destination = args.restore
    assert destination is not None
    assert destination.resolve().is_relative_to((root / 'codex/work/restores').resolve())
    destination.parent.mkdir(parents=True, exist_ok=True)
    log = out / 'Scene4阶段备份恢复.log'
    with log.open('w', encoding='utf-8') as handle:
        if destination.exists():
            assert not subprocess.check_output(git + ['-C', str(destination), 'status', '--porcelain'], env=env).strip()
            subprocess.run(git + ['-C', str(destination), 'pull', '--ff-only'], stdout=handle, stderr=subprocess.STDOUT, env=env, check=True)
        else:
            subprocess.run(git + ['clone', '--branch', 'fix/fael-gbp2-progress',
                            'https://github.com/y-ii-ii/STGPlanner-reproduction.git', str(destination)],
                            stdout=handle, stderr=subprocess.STDOUT, env=env, check=True)
    assert subprocess.check_output(git + ['-C', str(destination), 'rev-parse', 'HEAD'], text=True).strip() == head
    assert not subprocess.check_output(git + ['-C', str(destination), 'status', '--porcelain']).strip()
    check_output = out / 'Scene4阶段远端恢复核验.json'
    subprocess.run(['python', str(repo / 'benchmarks/maintenance/verify_scene4_stage.py'), '--repo', str(destination),
                    '--output', str(check_output)], check=True, stdout=subprocess.DEVNULL)
    verification = json.loads(check_output.read_text(encoding='utf-8'))
    value.update(remote_head_matches_local=True, restored_checkout=str(destination),
                 restored_checkout_clean=True, restored_manifest_files=verification['manifest_file_count'],
                 restored_raw_evidence_files=verification['preserved_raw_evidence_file_count'],
                 all_restore_checks_passed=verification['all_checks_passed'], new_simulation_started=False)
    (out / 'SCENE4_STAGE_BACKUP_VERIFIED.json').write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(value, ensure_ascii=False, indent=2))
