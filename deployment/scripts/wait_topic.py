#!/usr/bin/env python3
import sys
import rospy
rospy.init_node('stgplanner_wait_topic', anonymous=True)
rospy.wait_for_message(sys.argv[1], rospy.AnyMsg, timeout=20)
