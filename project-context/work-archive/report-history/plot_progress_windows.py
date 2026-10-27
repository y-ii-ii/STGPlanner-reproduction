from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
root=Path('D:/STGPlanner/benchmarks');out=root/'progress_report';out.mkdir(exist_ok=True)
selection=json.loads((root/'progress_trials.json').read_text())
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
fig,axes=plt.subplots(1,2,figsize=(13,4.8),constrained_layout=True)
for ax,method in zip(axes,['fael','gbp2']):
    curves=[('formal_'+method+'_01','Before','#a7afb9','--')]
    if method=='gbp2':
        names=selection.get('plot_intermediate_runs',selection['intermediate_runs']);labels=dict(zip(selection['intermediate_runs'],selection['intermediate_labels']))
        curves.extend((trial,labels[trial],color,':') for trial,color in zip(names,['#d18b2d','#698879','#c36b73']))
    curves.append((selection['final_runs'][method],'Selected repair '+selection['final_runs'][method].rsplit('_',1)[-1],'#2878b5' if method=='fael' else '#8c56a2','-'))
    for trial,label,color,style in curves:
        folder=root/'results'/trial;d=json.loads((folder/'result.json').read_text())
        s=[json.loads(x) for x in (folder/'metrics.jsonl').read_text().splitlines()]
        t=[x['sim_s'] for x in s]+[d['sim_time_s']];v=[x['coverage_fraction']*100 for x in s]+[d['coverage_fraction']*100]
        ax.plot(t,v,label=label,color=color,ls=style,lw=1.8)
        ax.plot(t[-1],v[-1],'o' if d['finish_reason']=='coverage_threshold' else 'x',color=color,ms=7)
        offset=-20 if label.startswith('Frontier calibration') else 18 if label.startswith('Geometry repair') else -16 if label.startswith('Cluster type') else 9
        ax.annotate(f"{v[-1]:.2f}% / {t[-1]:.1f}s",(t[-1],v[-1]),xytext=(-10,offset),textcoords='offset points',ha='right',fontsize=9,color=color)
    ax.axhline(95,color='#555555',ls=':',lw=1);ax.axvline(1600,color='#555555',ls=':',lw=.8)
    ax.set(title=method.upper(),xlabel='Exploration simulation time (s)',ylabel='Known-plane area / 7790 (%)',ylim=(0,103));ax.grid(alpha=.15);ax.legend(fontsize=8.5)
fig.suptitle('Scene4: actual before / after runs | protocol 3 | o: 95% threshold, x: limit / diagnostic stop',fontsize=12)
fig.savefig(out/'scene4_progress_curves.png');plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(12,11),constrained_layout=True)
for i,method in enumerate(['fael','gbp2']):
    for j,(prefix,label) in enumerate([('formal_','Before'),('repair_formal_','Repaired')]):
        ax=axes[i,j];folder=root/'results'/(selection['final_runs'][method] if prefix=='repair_formal_' else 'formal_'+method+'_01');d=json.loads((folder/'result.json').read_text())
        rows=list(csv.DictReader((folder/'known_plane_cells.csv').open()))
        p=np.array([[float(x['x']),float(x['y']),int(x['occupied'])] for x in rows])
        xmin,xmax,ymin,ymax,res=-51,81,-21,101,.4
        grid=np.full((int((ymax-ymin)/res)+1,int((xmax-xmin)/res)+1),np.nan)
        ix=np.rint((p[:,0]-xmin)/res).astype(int);iy=np.rint((p[:,1]-ymin)/res).astype(int)
        valid=(ix>=0)&(ix<grid.shape[1])&(iy>=0)&(iy<grid.shape[0]);grid[iy[valid],ix[valid]]=p[valid,2]
        ax.imshow(grid,origin='lower',extent=[xmin-res/2,xmax+res/2,ymin-res/2,ymax+res/2],cmap=ListedColormap(['#dde3e8','#2d3641']),vmin=0,vmax=1,interpolation='nearest')
        s=[json.loads(x) for x in (folder/'metrics.jsonl').read_text().splitlines()]
        color='#2878b5' if method=='fael' else '#8c56a2'
        ax.plot([x['x'] for x in s],[x['y'] for x in s],color=color,lw=.7)
        ax.plot(s[0]['x'],s[0]['y'],'o',mfc='white',mec=color,ms=5);ax.plot(s[-1]['x'],s[-1]['y'],'x',color=color,ms=6)
        display_label=('Selected '+selection['final_runs'][method].rsplit('_',1)[-1]) if prefix=='repair_formal_' else label
        ax.set(title=f"{method.upper()} {display_label} | {d['sim_time_s']:.1f}s | {d['coverage_fraction']*100:.2f}%",xlabel='World X (m)',ylabel='World Y (m)',xlim=(xmin,xmax),ylim=(ymin,ymax));ax.set_aspect('equal')
fig.suptitle('Recorded final maps and trajectories | grey: known free, dark: occupied, white: unknown\nNominal known-plane ratio does not mean 100% reachable-area coverage',fontsize=12)
fig.savefig(out/'scene4_progress_maps.png');plt.close(fig)
print(out)
