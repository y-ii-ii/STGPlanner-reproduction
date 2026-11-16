#!/usr/bin/env python3
"""Own-map adapter. Raw grid is read only from this robot's private local topic."""
import json
import threading
import uuid

from team_topology.exporter import LocalExporter
from team_topology.graph import wire


def main():
    import rospy
    from std_msgs.msg import String
    rospy.init_node("topology_agent")
    robot = int(rospy.get_param("~robot_id"))
    exporter = LocalExporter(robot, uuid.uuid4().hex)
    lock = threading.Lock()
    publisher = rospy.Publisher("/team/topology_delta", String, queue_size=20)
    metrics = rospy.Publisher("~communication", String, queue_size=1)
    sent = [0]

    def receive(msg):
        with lock:
            try:
                snapshot = json.loads(msg.data)
                # Periodic tombstone-inclusive repair also supports late subscribers.
                packet = exporter.snapshot(snapshot, full=(exporter.delta.seq % 10 == 0))
                encoded = wire(packet)
                count = len(encoded.encode("utf-8")) + 4
                sent[0] += count
                publisher.publish(String(data=encoded))
                metrics.publish(String(data=wire({"robot": robot,
                    "category": "topology_task_state", "serialized_bytes": count,
                    "cumulative_published_bytes": sent[0],
                    "accounting": "one ROS String publication; excludes transport overhead and fanout"})))
            except (ValueError, KeyError, TypeError) as exc:
                rospy.logwarn_throttle(2., "Topology export refused: %s", exc)

    rospy.Subscriber(rospy.get_param("~snapshot_topic"), String, receive, queue_size=1)
    rospy.spin()


if __name__ == "__main__":
    main()
