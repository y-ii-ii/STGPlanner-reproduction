from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

root=Path('/mnt/d/STGPlanner/benchmarks');out=root/'report';out.mkdir(exist_ok=True)
methods=['gbp2','tare','fael','stgp'];labels={'gbp2':'GBP2','tare':'TARE','fael':'FAEL','stgp':'STGPlanner'}
colors={'gbp2':'#9558a4','tare':'#d48728','fael':'#2878b5','stgp':'#239b76'}
results={m:json.loads((root/'results'/('formal_'+m+'_01')/'result.json').read_text()) for m in methods}
series={m:[json.loads(line) for line in (root/'results'/('formal_'+m+'_01')/'metrics.jsonl').read_text().splitlines()] for m in methods}
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
fig,axes=plt.subplots(1,2,figsize=(13,4.8),constrained_layout=True)
for m in methods:
    d=results[m];s=series[m];time=[r['sim_s'] for r in s]+[d['sim_time_s']];area=[r['coverage_fraction']*100 for r in s]+[d['coverage_fraction']*100];distance=[r['distance_m'] for r in s]+[d['distance_m']]
    axes[0].plot(time,area,color=colors[m],label=labels[m]);axes[1].plot(time,distance,color=colors[m],label=labels[m])
    marker='o' if d['finish_reason']=='coverage_threshold' else 'x'
    axes[0].plot(time[-1],area[-1],marker,color=colors[m],ms=7);axes[1].plot(time[-1],distance[-1],marker,color=colors[m],ms=7)
axes[0].axhline(95,color='#555555',ls='--',lw=1,label='Common 95% threshold');axes[0].set(ylabel='Known-plane area / 7790 (%)',xlabel='Exploration simulation time (s)',ylim=(0,101),title='Common exploration metric')
axes[1].set(ylabel='Odometry XY distance (m)',xlabel='Exploration simulation time (s)',title='Actual travelled distance')
for ax in axes:ax.grid(alpha=.18);ax.legend(loc='best',fontsize=9)
fig.suptitle('Scene4 | one formal run per method | o: threshold reached, x: censored at time limit',fontsize=12)
fig.savefig(out/'scene4_curves.png');plt.close(fig)

fig,axes=plt.subplots(2,2,figsize=(12,11),constrained_layout=True)
for ax,m in zip(axes.flat,methods):
    folder=root/'results'/('formal_'+m+'_01');d=results[m];rows=list(csv.DictReader((folder/'known_plane_cells.csv').open()))
    p=np.array([[float(r['x']),float(r['y']),int(r['occupied'])] for r in rows]);res=.4
    if len(p):
        xmin,xmax=-51,81;ymin,ymax=-21,101;grid=np.full((int((ymax-ymin)/res)+1,int((xmax-xmin)/res)+1),np.nan)
        # Centres lie on a 0.4m lattice. Round instead of truncating floating
        # values, which would duplicate rows and leave false white stripes.
        ix=np.rint((p[:,0]-xmin)/res).astype(int);iy=np.rint((p[:,1]-ymin)/res).astype(int);valid=(ix>=0)&(ix<grid.shape[1])&(iy>=0)&(iy<grid.shape[0]);grid[iy[valid],ix[valid]]=p[valid,2]
        ax.imshow(grid,origin='lower',extent=[xmin-res/2,xmax+res/2,ymin-res/2,ymax+res/2],cmap=ListedColormap(['#dde3e8','#2d3641']),vmin=0,vmax=1,interpolation='nearest')
    s=series[m];ax.plot([r['x'] for r in s],[r['y'] for r in s],color=colors[m],lw=.8)
    if s:ax.plot(s[0]['x'],s[0]['y'],'o',mfc='white',mec=colors[m],ms=6);ax.plot(s[-1]['x'],s[-1]['y'],'x',color=colors[m],ms=7)
    state='completed' if d['finish_reason']=='coverage_threshold' else 'time limit'
    ax.set(title=f"{labels[m]} | {d['sim_time_s']:.1f}s | {d['distance_m']:.1f}m | {100*d['coverage_fraction']:.2f}% | {state}",xlabel='World X (m)',ylabel='World Y (m)',xlim=(-51,81),ylim=(-21,101));ax.set_aspect('equal');ax.grid(alpha=.12)
fig.suptitle('Recorded final known-plane cells and robot trajectories\nLight grey: known free, dark: occupied, white: unknown; nominal ratio is not reachable-area coverage',fontsize=12)
fig.savefig(out/'scene4_maps.png');plt.close(fig)

paper={'gbp2':(1600,1560,.465,.97),'tare':(1018.6,1640,.338,1.61),'fael':(1033.9,1420.3,.119,1.37),'stgp':(779.8,1194,.015,1.53)}
fig,axes=plt.subplots(1,2,figsize=(13,4.7),constrained_layout=True);x=np.arange(4)
for ax,index,title,unit in [(axes[0],0,'Exploration time','seconds'),(axes[1],1,'Travelled distance','metres')]:
    pv=[paper[m][index] for m in methods];rv=[results[m]['sim_time_s' if index==0 else 'distance_m'] for m in methods]
    left=ax.bar(x-.2,pv,.36,color='#b5bec8',label='Paper (5-run summary)');right=ax.bar(x+.2,rv,.36,color=[colors[m] for m in methods],label='This PC (one run)')
    for i,(b,m) in enumerate(zip(left,methods)):
        text=('>' if m=='gbp2' else '')+f'{pv[i]:.1f}';ax.text(b.get_x()+b.get_width()/2,b.get_height()+(65 if m=='gbp2' else 25),text,ha='center',fontsize=9)
    for b,m,value in zip(right,methods,rv):
        failed=results[m]['finish_reason']!='coverage_threshold'
        if failed:b.set_hatch('//');b.set_alpha(.65)
        ax.text(b.get_x()+b.get_width()/2,b.get_height()+25,f'{value:.1f}'+('*' if failed else ''),ha='center',fontsize=9)
    ax.set_xticks(x);ax.set_xticklabels([labels[m] for m in methods]);ax.set(ylabel=unit,title=title,ylim=(0,max(pv+rv)*1.22));ax.grid(axis='y',alpha=.18);ax.legend(fontsize=9)
fig.suptitle('Paper comparison | * hatched local result: time-limit observation, not a completed exploration',fontsize=11)
fig.savefig(out/'scene4_paper_comparison.png');plt.close(fig)
print(out)
