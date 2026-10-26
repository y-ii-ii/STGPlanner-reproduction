import time, xmlrpc.client
deadline=time.monotonic()+240
while time.monotonic()<deadline:
    try:
        response=xmlrpc.client.ServerProxy('http://localhost:11311').getSystemState('/long_test_readiness')
        if response[0]==1 and any(name=='/topo_planner_node/topo_planner/result' for name,_ in response[2][0]):
            print('Exploration action server advertised.',flush=True)
            raise SystemExit(0)
    except (OSError,xmlrpc.client.Error):pass
    time.sleep(.5)
raise SystemExit('Exploration action server not ready within 240 seconds.')
