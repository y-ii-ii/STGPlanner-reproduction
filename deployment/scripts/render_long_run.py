#!/usr/bin/env python3
"""Plot only recorded real ROS messages and project statistics from this run."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

base=Path('/mnt/d/STGPlanner/logs/planner_completion')
d=json.loads((base/'long_runtime.json').read_text())
assert d['passed']
rows=d['metrics']
t=[r['project_elapsed'] for r in rows]
metric=[r['metric'] for r in rows]
dist=[r['reported_distance'] for r in rows]
stats=base/'long_run_statistics'
trajectory=np.loadtxt(str(stats/'trajectory.txt'),skiprows=1)
iterations=np.loadtxt(str(stats/'iteration_time.txt'),skiprows=1)
fig,axes=plt.subplots(2,2,figsize=(13,8.4),constrained_layout=True)
fig.suptitle('STGPlanner Scene4: recorded full exploration lifecycle',fontsize=17)
ax=axes[0,0]
ax.plot(t,metric,color='#168075',linewidth=2,label='Project known-area metric')
ax.axhline(.95*d['map_area'],color='#bd571b',linestyle='--',label='Configured 95% stop threshold')
ax.scatter(t[-1],metric[-1],color='#bd571b',zorder=4)
ax.set(xlabel='Elapsed exploration time (wall seconds)',ylabel='Project metric (nominal m²)',title='Configured stop condition')
ax.legend(fontsize=8,loc='lower right')
ax=axes[0,1]
ax.plot(t,dist,color='#3564ad',linewidth=2)
ax.set(xlabel='Elapsed exploration time (wall seconds)',ylabel='Reported travel distance (m)',title='Continuous movement before completion')
ax=axes[1,0]
ax.plot(iterations[:,0],iterations[:,1],'.',markersize=2,color='#8861a6',alpha=.6)
ax.set(xlabel='Elapsed exploration time (wall seconds)',ylabel='Planning iteration time (s)',title='Recorded planner computation time')
ax=axes[1,1]
points=ax.scatter(trajectory[:,1],trajectory[:,2],c=trajectory[:,0],s=3,cmap='viridis')
ax.plot(trajectory[0,1],trajectory[0,2],'o',color='#267647',label='Start')
ax.plot(trajectory[-1,1],trajectory[-1,2],'X',color='#b94737',label='Finish')
ax.set(xlabel='World X (m)',ylabel='World Y (m)',title='Actual odometry trajectory')
ax.set_aspect('equal',adjustable='datalim');ax.legend(fontsize=8)
fig.colorbar(points,ax=ax,label='Elapsed wall seconds',shrink=.7)
for ax in axes.flat:ax.grid(True,alpha=.18)
fig.savefig(str(base/'long_run_metrics.png'),dpi=160)
print(base/'long_run_metrics.png')
