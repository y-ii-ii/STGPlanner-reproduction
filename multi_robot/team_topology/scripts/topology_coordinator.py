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
from team_topology.execution import ExecutionSupervisor,no_dispatch_progress
from team_topology.inbox import AuthorityInbox
from team_topology.lease_publisher import LeasePublisher


def main():
    import rospy
    from std_msgs.msg import String
    rospy.init_node("topology_coordinator")
    robots = tuple(int(r) for r in rospy.get_param("~robots", [1, 2]))
    if len(set(robots)) != len(robots) or not robots:
        raise ValueError("robot identities must be unique")
    store, coordinator, inbox = GraphStore(), Coordinator(robots), AuthorityInbox()
    ack_audit={"accepted":0,"rejected":0,"last_rejection":None}
    service={"max_feedback_queue_wait_s":0.,"max_plan_wall_s":0.,"max_graph_apply_wall_s":0.,"graph_packets_applied":0}
    session = uuid.uuid4().hex
    # One transport recovery only: use a fresh nonce, never accept a late proof
    # from the expired round or retry forever when the gate/odometry is dead.
    supervisor=ExecutionSupervisor(robots,session,stop_retries=1)
    publishers = {r: rospy.Publisher("/robot_%d/topo_planner_node/topology_command" % r,
                                   String, queue_size=1) for r in robots}
    lease=LeasePublisher(lambda r,encoded:publishers[r].publish(String(data=encoded)),
                         clocks=lambda:(time.monotonic(),rospy.Time.now().to_sec()))
    metrics = rospy.Publisher("~status", String, queue_size=1)
    traffic={"topology_received_bytes":0,"feedback_received_bytes":0,"commands_published_bytes":0}
    armed=[not rospy.get_param('~require_mission_start',False)]
    from std_msgs.msg import Bool
    rospy.Subscriber('/team/mission_start',Bool,lambda m:armed.__setitem__(0,m.data),queue_size=1)

    def publish_plans_unlocked():
        for r,state in supervisor.states.items():
            if state.get('active') is not None and coordinator.team_completed(state['active']):
                # Any valid own-map observer may retire information demand.
                # The current owner is still released only after physical ACK.
                supervisor.request_stop(r,None,time.monotonic(),'team_observation_completed')
        committed={r:state['active'] for r,state in supervisor.states.items() if state['phase']=='running'}
        desired=coordinator.plan(store,rospy.Time.now().to_sec(),time.monotonic(),committed) if armed[0] else {r:dict(mode='WAIT',path=[]) for r in robots}
        now,ros_now=time.monotonic(),rospy.Time.now().to_sec()
        sources={r:store.states[r]['stamp'] for r in robots if r in store.states}
        if len(sources)!=len(robots) or any(not 0<=ros_now-s<=coordinator.max_age for s in sources.values()):
            desired={r:dict(mode='WAIT',path=[]) for r in robots}
        plans=supervisor.commands(desired,now,ros_now)
        emitted=lease.commit(plans,sources,now,ros_now,armed[0])
        coordinator.commit_dispatches(emitted) # Commit actual publication, not a held intention.
        traffic['commands_published_bytes']=lease.stats()['application_bytes']
        return emitted

    def apply_packet(value):
        try:
            began=time.monotonic();applied=store.apply(value)
            service['max_graph_apply_wall_s']=max(service['max_graph_apply_wall_s'],time.monotonic()-began)
            service['graph_packets_applied']+=int(applied)
            if applied:
                coordinator.ingest_author_observations(store,value['records'])
        except (ValueError,KeyError,TypeError) as exc:
            rospy.logwarn_throttle(2.,"Topology receive refused: %s",exc)

    def process_feedback(value):
        try:
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
                        coordinator.fail_execution(r,active,time.monotonic(),value.get('local_gate')=='BODY_START_BLOCKED')
                        supervisor.request_stop(r,None,time.monotonic(),"planner_blocked")
                    elif matches and value.get("status")=="OBSERVATION_COMPLETED":
                        if coordinator.observe_completed(value,active,rospy.Time.now().to_sec()):
                            supervisor.request_stop(r,None,time.monotonic(),"observation_completed")
                else:
                    state=supervisor.states.get(r,{})
                    active=state.get("active")
                    executor_matches=(value.get('source')=='executor' and active is not None
                        and value.get('task')==active.get('task')
                        and int(value.get('version',0))==active.get('version')
                        and int(value.get('dispatch_id',0))==active.get('dispatch_id'))
                    if executor_matches and state.get('phase')=='running' and value.get('status')=='EXECUTOR_REJECTED':
                        coordinator.fail_execution(r,active,time.monotonic())
                        supervisor.request_stop(r,None,time.monotonic(),'executor_rejected')
                    if (value.get("source")=="executor" and value.get("status")=="EXECUTOR_ACCEPTED"
                        and state.get("phase")=="running" and active is not None and value.get("task")==active.get("task")
                        and int(value.get("version",0))==active.get("version")
                        and int(value.get("dispatch_id",0))==active.get("dispatch_id")):
                        coordinator.ledger.acknowledge(active["task"],r,active["version"])
                    if value.get("status")=="STOP_REQUIRED" and value.get("token")==state.get("token") and state.get("active") is not None and value.get("reason") in ("EXECUTION_STALL","EXECUTION_DEADLINE","TRAFFIC_WAIT_REPLAN"):
                        coordinator.fail_execution(r,active,time.monotonic())
                    if (value.get('status')=='STOP_REQUIRED' and value.get('token')==state.get('token')
                            and active is not None and value.get('reason')=='EXECUTOR_STOP'
                            and r in store.states and no_dispatch_progress(state,store.states[r]['pose'])):
                        # A completed/rejected short goal before 10cm motion
                        # must not earn a new dispatch and another fresh 8s
                        # stall budget indefinitely. Defer work, not complete it.
                        coordinator.fail_execution(r,active,time.monotonic())
                    accepted=supervisor.feedback(value,time.monotonic())
                    if value.get('status')=='STOPPED':
                        ack_audit['accepted' if accepted else 'rejected']+=1
                        if not accepted:ack_audit['last_rejection']=dict(robot=r,phase=state['phase'],expected_stop_id=state.get('stop_id'),received_stop_id=value.get('stop_id'),deadline_remaining_s=state.get('deadline',0)-time.monotonic())
                while supervisor.released:
                    robot,old=supervisor.released.pop(0)
                    if old["task"] in coordinator.ledger.items:
                        coordinator.ledger.release(old["task"],robot,old["version"])
        except (ValueError, KeyError, TypeError) as exc:
            rospy.logwarn_throttle(2., "Topology feedback refused: %s", exc)

    def tick():
        try:
            began=time.monotonic()
            plans = publish_plans_unlocked()
            service["max_plan_wall_s"]=max(service["max_plan_wall_s"],time.monotonic()-began)
        except (ValueError, KeyError) as exc:
            rospy.logwarn_throttle(2., "Topology planning refused: %s", exc)
            return
        counts=inbox.stats();traffic.update({k:counts[k] for k in ('feedback_received_bytes','topology_received_bytes')})
        metrics.publish(String(data=wire({"graph_digest": store.digest(),
            "nodes": len(store.live("node")), "edges": len(store.live("edge")),
            "tasks": len(store.live("task")), "accepted_received_bytes": store.received_bytes,
            "communication_one_delivery_application_bytes":dict(traffic),
            "execution_phases":{str(r):s["phase"] for r,s in supervisor.states.items()},
            "execution_blocked_by":{str(r):s.get('blocked_by',[]) for r,s in supervisor.states.items()},
            "stop_retry_counts":{str(r):s.get('stop_retry_count',0) for r,s in supervisor.states.items()},
            "allocation_diagnostics":coordinator.diagnostics,
            "execution_retry_memory":coordinator.retry_memory.entries,
            "observed_completion_cells":len(coordinator.observed_support),
            "team_observation_certificates":coordinator.team_observations.stats(),
            "command_lease_publisher":lease.stats(),
            "ledger_state_counts":{k:sum(i['state']==k for i in coordinator.ledger.items.values()) for k in ('assigned','offered','dispatched','active','completed')},
            "feedback_ack_audit":dict(ack_audit),"authority_service":dict(service),"authority_inbox":counts,
            "command_serialized_bytes": sum(len(wire(dict(p, allocation_session=session)).encode("utf-8"))+4 for p in plans.values()),
            "robot_distance_m": math.dist(store.states[robots[0]]["pose"],store.states[robots[1]]["pose"])
                if len(robots)==2 and all(r in store.states for r in robots) else None,
            "phase": "world_perfect_no_loop_closure"})))

    def enqueue(kind,msg):
        try:inbox.put(kind,json.loads(msg.data),len(msg.data.encode('utf-8'))+4,time.monotonic())
        except (ValueError,TypeError):rospy.logwarn_throttle(2.,'Invalid topology authority JSON')

    rospy.Subscriber('/team/topology_delta',String,lambda m:enqueue('topology',m),queue_size=100,buff_size=8*1024*1024)
    for r in robots:
        rospy.Subscriber('/robot_%d/topo_planner_node/topology_feedback'%r,String,lambda m:enqueue('feedback',m),queue_size=100)
        rospy.Subscriber('/robot_%d/topology/execution_feedback'%r,String,lambda m:enqueue('feedback',m),queue_size=100)
    # Single authority owner, wall-clock scheduling. ROS subscriber threads only
    # enqueue and cannot starve ACK handling by repeatedly reacquiring a mutex.
    wait=threading.Event();next_plan=0.
    def drain_feedback(normal_limit=64):
        for received,value in inbox.feedback(normal_limit):
            service['max_feedback_queue_wait_s']=max(service['max_feedback_queue_wait_s'],time.monotonic()-received)
            process_feedback(value)
    shutdown=threading.Event()
    def renew_contract():
        while not shutdown.wait(.1) and not rospy.is_shutdown():
            # No graph/ledger/supervisor mutation in this thread. The pulse can
            # renew only a committed contract while its authority and validated
            # source stamps remain bounded; unchanged local watchdogs stay on.
            lease.tick(time.monotonic(),rospy.Time.now().to_sec(),armed[0])
    heartbeat=threading.Thread(target=renew_contract,daemon=True);heartbeat.start()
    try:
        while not rospy.is_shutdown():
            lease.health({r:s['stamp'] for r,s in store.states.items()},time.monotonic(),armed[0])
            drain_feedback()
            graph_began=time.monotonic()
            for _ in range(8):
                packet=inbox.packet()
                if packet is None:break
                apply_packet(packet[1]);drain_feedback(0)
                if time.monotonic()-graph_began>.12:break
            drain_feedback()
            lease.health({r:s['stamp'] for r,s in store.states.items()},time.monotonic(),armed[0])
            if time.monotonic()>=next_plan:
                tick();next_plan=time.monotonic()+.25
            wait.wait(.02)
    finally:shutdown.set();heartbeat.join(1.)


if __name__ == "__main__":
    main()
