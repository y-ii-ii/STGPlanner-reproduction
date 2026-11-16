#!/usr/bin/env python3
"""One allocation authority for phase-1 perfect communication.

Only compact graph/task/state deltas cross into this process. No occupancy,
point cloud or Gazebo truth subscriber exists here. This is centralized
ownership commit, not a claim of distributed consensus under packet loss.
"""
import json
import threading
import uuid
import math

from team_topology.graph import GraphStore, wire
from team_topology.allocator import Coordinator


def main():
    import rospy
    from std_msgs.msg import String
    rospy.init_node("topology_coordinator")
    robots = tuple(int(r) for r in rospy.get_param("~robots", [1, 2]))
    if len(set(robots)) != len(robots) or not robots:
        raise ValueError("robot identities must be unique")
    store, coordinator, lock = GraphStore(), Coordinator(robots), threading.Lock()
    session = uuid.uuid4().hex
    publishers = {r: rospy.Publisher("/robot_%d/topo_planner_node/topology_command" % r,
                                   String, queue_size=1) for r in robots}
    metrics = rospy.Publisher("~status", String, queue_size=1)

    def receive(msg):
        with lock:
            try:
                store.apply(json.loads(msg.data))
            except (ValueError, KeyError, TypeError) as exc:
                # A gap is repaired by the agent's periodic full packet; no old
                # delta is partially applied and no hidden map channel is used.
                rospy.logwarn_throttle(2., "Topology receive refused: %s", exc)

    def feedback(msg):
        with lock:
            try:
                value = json.loads(msg.data)
                if value.get("allocation_session") == session:
                    coordinator.feedback(value)
            except (ValueError, KeyError, TypeError) as exc:
                rospy.logwarn_throttle(2., "Topology feedback refused: %s", exc)

    def tick(_):
        with lock:
            try:
                plans = coordinator.plan(store, rospy.Time.now().to_sec())
            except (ValueError, KeyError) as exc:
                rospy.logwarn_throttle(2., "Topology planning refused: %s", exc)
                return
            for r, plan in plans.items():
                plan["allocation_session"] = session
                publishers[r].publish(String(data=wire(plan)))
            metrics.publish(String(data=wire({"graph_digest": store.digest(),
                "nodes": len(store.live("node")), "edges": len(store.live("edge")),
                "tasks": len(store.live("task")), "accepted_received_bytes": store.received_bytes,
                "command_serialized_bytes": sum(len(wire(dict(p, allocation_session=session)).encode("utf-8"))+4 for p in plans.values()),
                "robot_distance_m": math.dist(store.states[robots[0]]["pose"],store.states[robots[1]]["pose"])
                    if len(robots)==2 and all(r in store.states for r in robots) else None,
                "phase": "world_perfect_no_loop_closure"})))

    rospy.Subscriber("/team/topology_delta", String, receive, queue_size=100)
    for r in robots:
        rospy.Subscriber("/robot_%d/topo_planner_node/topology_feedback" % r, String, feedback, queue_size=10)
    rospy.Timer(rospy.Duration(.5), tick)
    rospy.spin()


if __name__ == "__main__":
    main()
