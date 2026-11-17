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
import time

from team_topology.graph import GraphStore, wire
from team_topology.allocator import Coordinator
from team_topology.execution import ExecutionSupervisor


def main():
    import rospy
    from std_msgs.msg import String
    rospy.init_node("topology_coordinator")
    robots = tuple(int(r) for r in rospy.get_param("~robots", [1, 2]))
    if len(set(robots)) != len(robots) or not robots:
        raise ValueError("robot identities must be unique")
    store, coordinator, lock = GraphStore(), Coordinator(robots), threading.Lock()
    session = uuid.uuid4().hex
    supervisor=ExecutionSupervisor(robots,session)
    publishers = {r: rospy.Publisher("/robot_%d/topo_planner_node/topology_command" % r,
                                   String, queue_size=1) for r in robots}
    metrics = rospy.Publisher("~status", String, queue_size=1)
    traffic={"topology_received_bytes":0,"feedback_received_bytes":0,"commands_published_bytes":0}
    armed=[not rospy.get_param('~require_mission_start',False)]
    from std_msgs.msg import Bool
    rospy.Subscriber('/team/mission_start',Bool,lambda m:armed.__setitem__(0,m.data),queue_size=1)

    def publish_plans_unlocked():
        desired=coordinator.plan(store,rospy.Time.now().to_sec(),time.monotonic()) if armed[0] else {r:dict(mode='WAIT',path=[]) for r in robots}
        plans=supervisor.commands(desired,time.monotonic(),rospy.Time.now().to_sec())
        for r,plan in plans.items():
            encoded=wire(plan);publishers[r].publish(String(data=encoded))
            traffic['commands_published_bytes']+=len(encoded.encode())+4
        return plans

    def receive(msg):
        with lock:
            traffic["topology_received_bytes"]+=len(msg.data.encode("utf-8"))+4
            try:
                store.apply(json.loads(msg.data))
            except (ValueError, KeyError, TypeError) as exc:
                # A gap is repaired by the agent's periodic full packet; no old
                # delta is partially applied and no hidden map channel is used.
                rospy.logwarn_throttle(2., "Topology receive refused: %s", exc)

    def feedback(msg):
        with lock:
            traffic["feedback_received_bytes"]+=len(msg.data.encode("utf-8"))+4
            try:
                value = json.loads(msg.data)
                if value.get("allocation_session") == session:
                    r=int(value["robot"])
                    if value.get("source")=="planner":
                        active=supervisor.states[r].get("active")
                        matches=supervisor.states[r]["phase"]=="running" and active is not None and value.get("task")==active.get("task") and int(value.get("dispatch_id",0))==active.get("dispatch_id") and int(value.get("version",0))==active.get("version")
                        if matches and value.get("status")=="ACCEPTED":
                            # Planning acceptance is not execution acceptance.
                            item=coordinator.ledger.items.get(active["task"])
                            if item is not None:item["planner_accepted"]=True
                        elif matches and value.get("status")=="BLOCKED":
                            # A geometric planning failure needs a useful cooling
                            # interval; a 2s retry previously reset the execution
                            # stall timer without ever moving the robot.
                            coordinator.defer(r,active["task"],time.monotonic(),15.)
                            supervisor.request_stop(r,None,time.monotonic(),"planner_blocked")
                        elif matches and value.get("status")=="OBSERVATION_COMPLETED":
                            if coordinator.observe_completed(value,active,rospy.Time.now().to_sec()):
                                supervisor.request_stop(r,None,time.monotonic(),"observation_completed")
                    else:
                        state=supervisor.states.get(r,{})
                        active=state.get("active")
                        if (value.get("source")=="executor" and value.get("status")=="EXECUTOR_ACCEPTED"
                            and state.get("phase")=="running" and active is not None and value.get("task")==active.get("task")
                            and int(value.get("version",0))==active.get("version")
                            and int(value.get("dispatch_id",0))==active.get("dispatch_id")):
                            coordinator.ledger.acknowledge(active["task"],r,active["version"])
                        if value.get("status")=="STOP_REQUIRED" and value.get("token")==state.get("token") and state.get("active") is not None and value.get("reason") in ("EXECUTION_STALL","EXECUTION_DEADLINE","TRAFFIC_WAIT_REPLAN"):
                            coordinator.defer(r,state["active"]["task"],time.monotonic())
                        stopped=supervisor.feedback(value,time.monotonic()) and value.get('status')=='STOPPED'
                    while supervisor.released:
                        robot,old=supervisor.released.pop(0)
                        if old["task"] in coordinator.ledger.items:
                            coordinator.ledger.release(old["task"],robot,old["version"])
                    if value.get('status')=='STOPPED' and supervisor.states[r]['phase']=='stopped':
                        # Publish a ready assignment in the same verified-stop
                        # event. Idle empty-path retries must not repeatedly win
                        # the race against the 0.5s allocation timer.
                        publish_plans_unlocked()
            except (ValueError, KeyError, TypeError) as exc:
                rospy.logwarn_throttle(2., "Topology feedback refused: %s", exc)

    def tick(_):
        with lock:
            try:
                plans = publish_plans_unlocked()
            except (ValueError, KeyError) as exc:
                rospy.logwarn_throttle(2., "Topology planning refused: %s", exc)
                return
            metrics.publish(String(data=wire({"graph_digest": store.digest(),
                "nodes": len(store.live("node")), "edges": len(store.live("edge")),
                "tasks": len(store.live("task")), "accepted_received_bytes": store.received_bytes,
                "communication_one_delivery_application_bytes":dict(traffic),
                "execution_phases":{str(r):s["phase"] for r,s in supervisor.states.items()},
                "command_serialized_bytes": sum(len(wire(dict(p, allocation_session=session)).encode("utf-8"))+4 for p in plans.values()),
                "robot_distance_m": math.dist(store.states[robots[0]]["pose"],store.states[robots[1]]["pose"])
                    if len(robots)==2 and all(r in store.states for r in robots) else None,
                "phase": "world_perfect_no_loop_closure"})))

    rospy.Subscriber("/team/topology_delta", String, receive, queue_size=100)
    for r in robots:
        rospy.Subscriber("/robot_%d/topo_planner_node/topology_feedback" % r, String, feedback, queue_size=10)
        rospy.Subscriber("/robot_%d/topology/execution_feedback" % r, String, feedback, queue_size=20)
    rospy.Timer(rospy.Duration(.5), tick)
    rospy.spin()


if __name__ == "__main__":
    main()
