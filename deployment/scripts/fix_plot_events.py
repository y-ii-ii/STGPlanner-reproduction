from pathlib import Path
path = Path('/mnt/d/STGPlanner/catkin_ws/src/STGPlanner/stgp_planner/visualization_tools/scripts/realTimePlot.py')
text = path.read_text()
old = '            fig.canvas.draw()'
new = '            fig.canvas.draw()\n            plt.pause(0.001)  # Process Tk events so the window stays responsive.'
if new not in text:
    if old not in text:
        raise RuntimeError('Unexpected plotting script contents')
    text = text.replace(old, new)
init = "    rospy.init_node('realTimePlot')"
idle = init + "\n    if rospy.get_param('~suppress_window', False):\n        rospy.loginfo('Figure 1 closed for this ROS session; plotting is idle.')\n        rospy.spin()\n        return"
if idle not in text:
    if init not in text:
        raise RuntimeError('Unexpected plotting node initialization')
    text = text.replace(init,idle)
path.write_text(text)
print('Matplotlib/Tk event loop and optional session window suppression applied.')
