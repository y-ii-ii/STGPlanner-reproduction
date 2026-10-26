#!/usr/bin/env python3
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

base = Path('/mnt/d/STGPlanner/logs')
data = json.loads((base/'runtime_headless.json').read_text())
with (base/'runtime_headless.trajectory.csv').open() as stream:
    rows = list(csv.DictReader(stream))
x = [float(r['x']) for r in rows]
y = [float(r['y']) for r in rows]
t = [float(r['wall_seconds']) for r in rows]
fig, ax = plt.subplots(figsize=(8.5, 6.5))
ax.plot(x, y, color='#b5c4d3', linewidth=1.0)
points = ax.scatter(x, y, c=t, cmap='viridis', s=12)
ax.scatter(x[0], y[0], marker='o', c='#ef6c00', s=75, label='Start', zorder=5)
ax.scatter(x[-1], y[-1], marker='*', c='#d81b60', s=120, label='End', zorder=5)
ax.set_aspect('equal', adjustable='datalim')
ax.set_xlabel('World X (m)')
ax.set_ylabel('World Y (m)')
ax.grid(alpha=0.2)
ax.legend(loc='best')
fig.colorbar(points, ax=ax, label='Elapsed wall time (s)')
ax.set_title('STGPlanner / Scene4 - measured robot trajectory\n'
             '{:.1f} m traveled | {} nonempty plans | {:.0f} s test'.format(
                 data['odometry_distance_m'], data['successful_nonempty_plans'], data['wall_seconds']))
fig.tight_layout()
fig.savefig(str(base/'runtime_trajectory.png'), dpi=170)
print(base/'runtime_trajectory.png')
