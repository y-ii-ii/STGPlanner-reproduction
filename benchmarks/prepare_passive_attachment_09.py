"""Prepare a passive observer that preserves existing frozen runtime evidence."""
from pathlib import Path
root=Path('D:/STGPlanner')
source=(root/'codex/outputs/preflight_repair_formal_gbp2_09/audit_live.py').read_text()
start=source.index('rosparam.dump_params(')
end=source.index("stats = {'cmd_samples'")
source=source[:start]+"if not (out / 'live_runtime_audit.json').exists():\n"+''.join('    '+line+'\n' for line in source[start:end].splitlines())+source[end:]
source=source.replace("stats = {'cmd_samples'", "while rospy.get_time()==0:\n    time.sleep(.05)\nstats = {'cmd_samples'")
source=source.replace("'vehicle_action_requests': 0}","'vehicle_action_requests': 0, 'audit_start_absolute_sim': rospy.get_time(), 'audit_scope': 'Attached after initial observer import failure; pre-attachment command/action samples unavailable. No control changes.'}")
source=source.replace("(out / 'passive_global_action_audit.jsonl').open('w')","(out / 'passive_global_action_audit.jsonl').open('x')")
source=source.replace('while not rospy.is_shutdown():',"while not rospy.is_shutdown() and not (out / 'result.json').exists():")
(root/'codex/work/audit_passive_09_attached.py').write_text(source)
print('Prepared passive-only observer; existing runtime manifest and parameter capture preserved.')
