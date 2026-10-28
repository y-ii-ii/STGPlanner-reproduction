"""Plot saved completed TARE trials only; supports the existing WSL matplotlib."""
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root = Path('/mnt/d/STGPlanner') if sys.platform != 'win32' else Path('D:/STGPlanner')
out = root / 'codex/outputs/tare_optimization_20261028'
specs = [('formal_tare_01', 'Historical stock', '#969fa9', '--'),
         ('tare_audit_control_20261028_01', 'Fresh stock control', '#4477aa', '-'),
         ('tare_sensor_model_20261028_01', 'Aligned sensor 01', '#228833', '-'),
         ('tare_sensor_model_20261028_02', 'Aligned sensor 02', '#ee7733', '-')]
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 160})
fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), constrained_layout=True)
count = 0
for trial, label, color, style in specs:
    folder = root / 'benchmarks/results' / trial
    if not (folder / 'result.json').exists():
        continue
    result = json.loads((folder / 'result.json').read_text())
    if 'sim_time_s' not in result:
        continue
    rows = [json.loads(line) for line in (folder / 'metrics.jsonl').read_text().splitlines()]
    rows.append({'sim_s': result['sim_time_s'], 'coverage_fraction': result['coverage_fraction'], 'distance_m': result['distance_m']})
    for ax, key, multiplier in [(axes[0], 'coverage_fraction', 100), (axes[1], 'distance_m', 1)]:
        ax.plot([r['sim_s'] for r in rows], [r[key]*multiplier for r in rows], label=label, color=color, linestyle=style, linewidth=1.8)
        ax.scatter(result['sim_time_s'], result[key]*multiplier, color=color, s=20, zorder=4)
    count += 1
axes[0].axhline(95, color='#333333', linestyle=':', linewidth=1, label='Common 95% threshold')
axes[0].set(ylabel='Known plane area / 7790 m2 (%)', xlabel='Exploration simulation time (s)', ylim=(0, 102))
axes[1].set(ylabel='Measured XY travel distance (m)', xlabel='Exploration simulation time (s)')
for ax in axes:
    ax.grid(alpha=.22)
    ax.legend(loc='lower right', frameon=False, fontsize=9)
fig.suptitle('Scene4 TARE follow-up: complete recorded trials; unchanged public observer / 2 m/s cap', fontsize=12)
fig.savefig(out / 'tare_optimization_curves.png')
plt.close(fig)
print('Plotted ' + str(count) + ' completed trials')
