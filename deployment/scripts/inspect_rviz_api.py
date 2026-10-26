from rviz import bindings as rviz
for name in ('VisualizationFrame','VisualizationManager','Display','DisplayGroup','Property','StatusProperty','StatusList'):
    obj=getattr(rviz,name,None)
    print(name, [x for x in dir(obj) if any(key in x.lower() for key in ('prop','status','value','child','display','level','manager','initial','error'))])
