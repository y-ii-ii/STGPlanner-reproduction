from rviz import bindings as r
for cls in ('VisualizationFrame','RenderPanel','VisualizationManager'):
    print(cls, [x for x in dir(getattr(r,cls)) if any(t in x.lower() for t in ('render','capture','screen','manager','window'))])
