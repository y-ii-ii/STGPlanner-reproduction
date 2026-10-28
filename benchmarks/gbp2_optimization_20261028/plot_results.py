"""Plot completed trials only, including censored/native-ended observations."""
import csv
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

root=Path('/mnt/d/STGPlanner');out=root/'codex/outputs/gbp2_optimization_20261028'
catalog=json.loads(Path(__file__).with_name('trial_catalog.json').read_text())
names=['repair_formal_gbp2_09']+[r['trial'] for r in catalog]
labels=['09: frontier1%, h0.456m']+[
    r['trial'].rsplit('_',1)[1]+(': repeat ' if 'repeat' in r['trial'] else ': ')+
    'frontier'+format(r['threshold']*100,'g')+'%, h'+format(r['height'],'g')+'m' for r in catalog]
colors=['#596579','#D26A29','#167D9A','#2B8355','#6D579A','#B44375','#807021','#9B4E22','#43847F']
completed=[]
for name,label,color in zip(names,labels,colors):
    folder=root/'benchmarks/results'/name
    if not (folder/'result.json').exists():continue
    result=json.loads((folder/'result.json').read_text())
    rows=[json.loads(line) for line in (folder/'metrics.jsonl').read_text().splitlines() if line.strip()]
    completed.append((name,label,color,folder,result,rows))
assert completed
fig,axes=plt.subplots(1,2,figsize=(12,4.4),dpi=150)
for name,label,color,folder,result,rows in completed:
    t=[r['sim_s'] for r in rows]
    axes[0].plot(t,[r['coverage_fraction']*100 for r in rows],label=label,color=color,lw=1.8)
    axes[1].plot(t,[r['distance_m'] for r in rows],label=label,color=color,lw=1.8)
    end=result.get('native_finish_sim_s')
    if end is not None:
        hit=next(r for r in rows if r['sim_s']>=end)
        axes[0].scatter([end],[hit['coverage_fraction']*100],color=color,marker='X',s=55,zorder=5)
axes[0].axhline(95,color='#a83b3b',ls='--',lw=1.2,label='Public 95% goal')
axes[0].set(ylim=(0,100),ylabel='Public planar coverage (%)')
axes[1].set(ylabel='Travel distance (m)')
for ax in axes:
    ax.set(xlabel='Simulation time (s)',xlim=(0,2400));ax.grid(alpha=.2);ax.legend(fontsize=8,loc='best')
fig.suptitle('Scene4 GBP2 follow-up: all completed trials; X = native homing ended',fontsize=11)
fig.tight_layout();fig.savefig(out/'gbp2_frontier_curves.png');plt.close(fig)

def cells(name):
    with (root/'benchmarks/results'/name/'known_plane_cells.csv').open() as handle:
        return {(math.floor(float(r['x'])/.4+1e-7),math.floor(float(r['y'])/.4+1e-7)):int(r['occupied']) for r in csv.DictReader(handle)}
union=set()
for name in ['formal_stgp_01','formal_tare_01','repair_formal_fael_01']:union.update(cells(name))
ncols=2 if len(completed)==4 else min(3,len(completed));nrows=math.ceil(len(completed)/ncols)
fig,axes=plt.subplots(nrows,ncols,figsize=(5*ncols,5.5*nrows),dpi=150,squeeze=False)
for ax in axes.flat[len(completed):]:ax.set_visible(False)
for ax,(name,label,color,folder,result,rows) in zip(axes.flat,completed):
    own=cells(name)
    all_xy=union|set(own)
    xmin,xmax=min(x for x,y in all_xy),max(x for x,y in all_xy)
    ymin,ymax=min(y for x,y in all_xy),max(y for x,y in all_xy)
    img=np.full((ymax-ymin+1,xmax-xmin+1),np.nan)
    for x,y in union:img[y-ymin,x-xmin]=0
    for (x,y),occupied in own.items():img[y-ymin,x-xmin]=2 if occupied else 1
    from matplotlib.colors import ListedColormap
    ax.imshow(img,origin='lower',extent=(xmin*.4,(xmax+1)*.4,ymin*.4,(ymax+1)*.4),
              cmap=ListedColormap(['#e5e7eb','#9dcad8','#34495e']),vmin=0,vmax=2,interpolation='nearest')
    ax.plot([r['x'] for r in rows],[r['y'] for r in rows],color='#b94532',lw=.65,alpha=.85)
    ax.set(title=label+'\n'+format(result['coverage_fraction']*100,'.2f')+'% public coverage',xlabel='x (m)',ylabel='y (m)',aspect='equal')
fig.suptitle('Known plane and trajectory; gray = successful-run union (offline context, not ground truth)',fontsize=11)
fig.tight_layout(rect=(0,0,1,.94));fig.savefig(out/'gbp2_frontier_maps.png');plt.close(fig)
print(json.dumps({'plotted_completed_trials':[r[0] for r in completed],'outputs':['gbp2_frontier_curves.png','gbp2_frontier_maps.png']}))
