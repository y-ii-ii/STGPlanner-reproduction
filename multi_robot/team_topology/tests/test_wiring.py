import unittest
import xml.etree.ElementTree as ET
from team_topology.prepare_stack import transform,validate


class WiringTests(unittest.TestCase):
    def source(self):
        r=ET.Element('launch')
        for i in (1,2):
            g=ET.SubElement(r,'group',ns='robot_%d'%i)
            ET.SubElement(g,'remap',{'from':'/cmd_vel','to':'/robot_%d/cmd_vel'%i})
            for name in ('topo_planner_node','path_execution_node','localPlanner','pathFollower'):
                n=ET.SubElement(g,'node',name=name,pkg='fixture',type='fixture')
                ET.SubElement(n,'env',name='ROS_HOME',value='/historical/ros_home')
        return r

    def test_all_follower_outputs_are_fenced_and_old_log_paths_removed(self):
        r=transform(self.source(),'/new/runtime','/new/ws')
        validate(r)
        self.assertEqual(len(r.findall('include')),1)
        self.assertFalse(any('/historical/' in x.get('value','') for x in r.iter('env')))

    def test_bypass_or_mixed_mode_is_rejected(self):
        r=transform(self.source(),'/new/runtime','/new/ws')
        node=r.find("group/node[@name='pathFollower']")
        node.find("remap[@from='/cmd_vel']").set('to','/robot_1/cmd_vel')
        with self.assertRaisesRegex(ValueError,'bypasses'):validate(r)


if __name__=='__main__':unittest.main()
