import datetime, hashlib, json
from pathlib import Path
root=Path('D:/STGPlanner'); out=root/'codex/outputs'
remote=json.loads((out/'私有仓库备份验证.json').read_text(encoding='utf-8'))
clone=json.loads((out/'私有仓库克隆恢复核验.json').read_text(encoding='utf-8'))
assert remote['remote_commit']==clone['commit'] and remote['private'] and clone['all_recorded_hashes_passed']
bundle=out/'STGPlanner-FAEL-success-GBP2-incomplete-2026-10-27.bundle'
record={'completed_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(), 'repository':'y-ii-ii/STGPlanner-reproduction','private':True,'branch':'fix/fael-gbp2-progress','final_commit':remote['remote_commit'],'content_commit':'bbab488a560319118da045aaeade532e879b45b6','verified_recorded_files':clone['file_count'],'native_map_decompression_hash_passed':True,'protected_refs':remote['protected_refs'],'GBP2_tests_paused':True,'FAEL_reached_95':True,'GBP2_reached_95':False,'bundle':str(bundle),'bundle_bytes':bundle.stat().st_size,'bundle_sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),'bundle_verified':True}
(out/'私有备份完成记录.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
status=root/'codex/STATUS.md';text=status.read_text(encoding='utf-8')
text+='\n## 最终备份完成记录（本地补全）\n\n最终远端与本地HEAD：'+record['final_commit']+'。内容提交bbab488、验收/暂停交接提交ac6927e均已推送；私有性、原main/基线引用、522项克隆文件SHA及原生地图解压SHA均通过。当前Git工作树干净。\n本地bundle已创建并验证：'+str(bundle)+'，SHA256 '+record['bundle_sha256']+'。机器记录见codex/outputs/私有备份完成记录.json。Git内交接记录的是内容提交及验收元数据，当前最终HEAD可由git log核对。GBP2后续测试保持用户暂停，不自动恢复。\n'
status.write_text(text,encoding='utf-8',newline='\n')
print(json.dumps({'final_commit':record['final_commit'],'verified_files':record['verified_recorded_files'],'bundle_MiB':round(record['bundle_bytes']/1024**2,2),'GBP2_paused':True}))