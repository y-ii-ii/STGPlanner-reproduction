"""Read saved TARE observations; report speed, direction changes and coverage stages."""
import argparse
import json
import math
import statistics
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('trial')
args = parser.parse_args()
root = Path('D:/STGPlanner')
trial = root / 'benchmarks/results' / args.trial
events = [json.loads(line) for line in (trial / 'events.jsonl').read_text(encoding='utf-8').splitlines()]
starts = [row['sim'] for row in events if row['kind'] == 'exploration_start']
start = starts[0] if starts else None
ends = [row['sim'] for row in events if row['kind'] == 'finish']
end = ends[-1] if ends else float('inf')
metrics = [json.loads(line) for line in (trial / 'metrics.jsonl').read_text(encoding='utf-8').splitlines()]
data = []
path = trial / 'tare_diagnostics.jsonl'
if path.exists():
    for line in path.read_text(encoding='utf-8').splitlines():
        try:
            row = json.loads(line)
            if start is not None and start <= row['sim'] <= end:
                data.append(row)
        except json.JSONDecodeError:
            pass
commands = [r for r in data if r['kind'] == 'command']
waypoints = [r for r in data if r['kind'] == 'waypoint']
value = {'trial': args.trial, 'last_metric': metrics[-1] if metrics else None,
         'commands': len(commands), 'waypoints': len(waypoints),
         'path_counts': {kind: sum(r['kind'] == kind for r in data) for kind in ['local_path', 'global_path', 'exploration_path']}}
if commands:
    value['command_summary'] = {
        'mean_abs_linear': statistics.mean(abs(r['linear']) for r in commands),
        'slow_fraction_under_0_2': statistics.mean(abs(r['linear']) < .2 for r in commands),
        'fast_fraction_over_1_8': statistics.mean(abs(r['linear']) > 1.8 for r in commands),
        'turning_fraction_over_0_5_rad_s': statistics.mean(abs(r['angular']) > .5 for r in commands),
        'max_abs_linear': max(abs(r['linear']) for r in commands)}
if waypoints:
    value['waypoint_summary'] = {
        'target_distance_mean_m': statistics.mean(r['target_distance_m'] for r in waypoints),
        'reversals_over_120_degrees': sum(abs(r['direction_change_rad'] or 0) > math.radians(120) for r in waypoints),
        'targets_behind_robot': sum(abs(r['yaw_error_rad']) > math.pi/2 for r in waypoints)}
value['stages'] = []
step_speeds = []
direction_changes = []
last_heading = None
heading_anchor = metrics[0] if metrics else None
for first, last in zip(metrics, metrics[1:]):
    delta = last['sim_s'] - first['sim_s']
    if delta > 0:
        step_speeds.append((last['distance_m'] - first['distance_m']) / delta)
    dx, dy = last['x'] - heading_anchor['x'], last['y'] - heading_anchor['y']
    if math.hypot(dx, dy) >= 1.0:
        heading = math.atan2(dy, dx)
        if last_heading is not None:
            direction_changes.append(abs(math.atan2(math.sin(heading-last_heading), math.cos(heading-last_heading))))
        last_heading = heading
        heading_anchor = last
if step_speeds:
    value['trajectory_summary'] = {
        'one_second_speed_mean': statistics.mean(step_speeds),
        'slow_samples_fraction_under_0_2_m_s': statistics.mean(speed < .2 for speed in step_speeds),
        'measured_heading_changes_over_90_degrees': sum(angle > math.pi/2 for angle in direction_changes),
        'measured_heading_changes_over_120_degrees': sum(angle > math.radians(120) for angle in direction_changes),
        'heading_method': 'XY displacement headings sampled after >=1m chord, diagnostic only, not planner BFM ground truth'}
previous = {'sim_s': 0, 'distance_m': 0, 'area_m2': 0}
for limit in range(200, 1800, 200):
    eligible = [r for r in metrics if r['sim_s'] <= limit]
    if not eligible:
        continue
    last = eligible[-1]
    if last['sim_s'] <= previous['sim_s']:
        break
    value['stages'].append({'end_sim_s': last['sim_s'], 'coverage_percent': last['coverage_fraction'] * 100,
                            'distance_m': last['distance_m'], 'stage_speed_m_s': (last['distance_m']-previous['distance_m'])/(last['sim_s']-previous['sim_s']),
                            'stage_new_area_m2': last['area_m2']-previous['area_m2']})
    previous = last
out = root / 'codex/outputs/tare_optimization_20261028'
out.mkdir(exist_ok=True)
(out / (args.trial + '_diagnostics.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(value, ensure_ascii=False, indent=2))
