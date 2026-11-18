"""Wall-clock execution fencing and stop barriers, independent of ROS.

A planner ACCEPTED event is never a stop ACK. Only the final velocity gate can
prove a bounded stationary interval using fresh, post-request odometry and its
own successful zero publications. Clock, publisher and sensor faults fail closed.
"""
import copy
import math
from .scope import claims_conflict, work_claim


def token(command):
    return "%s/%s/%s/%s" % (command["allocation_session"], command["robot"],
                            command["version"], command["dispatch_id"])


def stop_proof(message):
    return (message.get("source") == "velocity_gate"
            and message.get("status") == "STOPPED"
            and int(message.get("fresh_samples", 0)) >= 3
            and float(message.get("stationary_s", 0)) >= .5
            and float(message.get("zero_s", 0)) >= .5)


def no_dispatch_progress(state,position):
    """A fresh rolling route must not reset the dispatch's measured origin."""
    origin=state.get('dispatch_origin')
    return bool(origin is not None and position is not None
                and math.dist(origin[:2],position[:2])<.1)


class ExecutionSupervisor:
    """One authority issues stable STOP nonces and new dispatch generations."""
    def __init__(self, robots, session, stop_timeout=6.0, stop_retries=0):
        self.robots, self.session, self.stop_timeout = tuple(robots), session, stop_timeout
        self.counter, self.sequence = 0, 0
        self.stop_retries=max(0,int(stop_retries))
        self.states = {r: {"phase": "initial", "active": None, "requests": []} for r in robots}
        self.released = []

    def request_stop(self, robot, request_id, now, reason="external"):
        state = self.states[robot]
        # A transport retry is the same operation. Do not turn a completed idle
        # STOP into another nonce/deadline. A NEW request ID still needs a fresh
        # post-request proof; a retry after intervening motion is stopped again.
        if (request_id and state['phase']=='stopped' and state['active'] is None
                and request_id in state.get('ack_requests',[])):
            return
        if not request_id and state['phase'] in ('stopped','stopping','fault'):
            return
        if request_id and request_id not in state["requests"]:
            state["requests"].append(request_id)
            # A new request needs a new post-request proof, not a cached ACK.
            state["phase"] = "request"
        elif state["phase"] not in ("stopping", "fault"):
            state["phase"] = "request"
        state["reason"] = reason

    @staticmethod
    def work_conflict(a,b):
        """Only related work waits for an old owner's physical stop barrier.

        Preserve exact task/member identity and overlapping common-world task
        support. Traffic reservations separately protect physical path crossings.
        A robot stopping unrelated work must not starve a ready recipient.
        """
        return claims_conflict(work_claim(a), work_claim(b))

    def feedback(self, value, now):
        robot = int(value["robot"])
        if value.get("allocation_session") != self.session or robot not in self.states:
            return False
        state = self.states[robot]
        if value.get("status") in ("STOP_REQUIRED", "STOP_REQUEST"):
            if value.get("source") not in ("velocity_gate", "executor", "pci"):
                return False
            if value["status"] == "STOP_REQUIRED" and value.get("token") != state.get("token"):
                return False
            self.request_stop(robot, value.get("request_id"), now, value.get("reason", "execution"))
            return True
        if (state["phase"] != "stopping" or now > state["deadline"]
            or value.get("stop_id") != state["stop_id"] or not stop_proof(value)):
            return False
        if set(value.get("request_ids", [])) != set(state["requests"]):
            return False
        if state["active"] is not None:
            self.released.append((robot, state["active"]))
        state.update(phase="stopped", active=None, token=None, ack_requests=list(state["requests"]),requests=[])
        return True

    def commands(self, desired, now, ros_now):
        self.sequence += 1
        result = {}
        # Inspect all transitions before arming any recipient. Robot iteration
        # order must not let a new owner start while the previous owner is stopping.
        for robot,state in self.states.items():
            wish=desired[robot]
            if state["phase"]=="running" and (wish["mode"]!="ROUTE" or
                    (wish.get("task"),wish.get("version"))!=(state["active"].get("task"),state["active"].get("version"))):
                state["phase"]="request"
                state["reason"]="assignment_changed"
        for robot in self.robots:
            state, wish = self.states[robot], desired[robot]
            state['blocked_by']=[]
            identity = (wish.get("task"), wish.get("version"))
            active_identity = (state["active"].get("task"), state["active"].get("version")) if state["active"] else None
            if state["phase"] == "running" and (wish["mode"] != "ROUTE" or identity != active_identity):
                state["phase"] = "request"
                state["reason"] = "assignment_changed"
            if state["phase"] in ("initial", "request"):
                self.counter += 1
                state.update(phase="stopping", stop_id="%s/stop/%d/%d" % (self.session, robot, self.counter),
                             deadline=now+self.stop_timeout,stop_retry_count=0)
            if state["phase"] == "stopping" and now > state["deadline"]:
                # A lost one-shot ACK must not wedge the team forever. Retry a
                # bounded number of times with a NEW nonce and new stationary
                # interval. A late proof for the expired nonce remains invalid.
                if state['stop_retry_count']<self.stop_retries:
                    self.counter+=1
                    state.update(stop_retry_count=state['stop_retry_count']+1,
                        stop_id='%s/stop/%d/%d'%(self.session,robot,self.counter),
                        deadline=now+self.stop_timeout)
                else:state['phase']='fault'
            if state["phase"] == "stopped" and wish["mode"] == "ROUTE":
                # Inspect every still-active owner, including a failed/stopping
                # one. New starts are included immediately, so two recipients
                # cannot simultaneously acquire the same aliased task.
                blockers=[r for r,s in self.states.items() if r!=robot and s['active'] is not None and self.work_conflict(wish,s['active'])]
                state['blocked_by']=blockers
                if not blockers:
                    self.counter += 1
                    state.update(phase="running", active=copy.deepcopy(wish), dispatch_id=self.counter,
                                 executor_confirmed=False,
                                 dispatch_origin=wish.get('path',[None])[0] if wish.get('path') else None)
            if state["phase"] == "running":
                command = dict(wish, schema=2, allocation_session=self.session,
                               dispatch_id=state["dispatch_id"])
                # A dispatch is a contract for a FIXED observation support.
                # Map updates may refresh its approach path, but cannot expand
                # 8 unknown cells into 52 under the same version/generation and
                # make completion chase a moving frontier forever. New support
                # is allocated after completion/physical STOP in a new dispatch.
                for key in ('scopes','scope_digest','scope_cells','task_members'):
                    if key in state['active']:command[key]=copy.deepcopy(state['active'][key])
                    else:command.pop(key,None)
                state["active"] = copy.deepcopy(command)
                state["token"] = token(command)
            else:
                # Repeated STOP keeps its nonce; retries do not reset the deadline.
                command = {"schema": 2, "mode": "STOP", "frame": "world", "robot": robot,
                    "allocation_session": self.session, "stop_id": state["stop_id"],
                    "request_ids": list(state.get("ack_requests",[])) if state["phase"]=="stopped" else list(state["requests"]), "reason": state.get("reason", "bootstrap"),
                    "fault": state["phase"] == "fault", "path": []}
            command.update(command_seq=self.sequence, stamp=ros_now, frame="world")
            result[robot] = command
        return result


class VelocityFence:
    """Sole final-command publisher's pure state; times are monotonic seconds."""
    def __init__(self, robot, lease_s=1.5, permit_s=.3, sensor_s=.3, stall_s=8., run_s=60.):
        self.robot, self.lease_s, self.permit_s = robot, lease_s, permit_s
        self.sensor_s, self.stall_s, self.run_s = sensor_s, stall_s, run_s
        self.session, self.seq, self.phase = None, 0, "initial"
        self.command, self.active_token, self.stop_id = {}, None, None
        self.command_at, self.permit_at, self.raw_at = -math.inf, -math.inf, -math.inf
        self.raw, self.odom = (0., 0.), None
        self.zero_since, self.zero_last, self.stationary_since = None, -math.inf, None
        self.samples, self.stop_started, self.proof_sent = 0, -math.inf, False
        self.permit_seq, self.issuer, self.events = 0, None, []
        self.executor_paused, self.certified_goal_seq = False, None
        self.armed_at, self.progress_at, self.progress_pose = 0., 0., None

    def receive_command(self, command, now, ros_now):
        if (command.get("schema") != 2 or command.get("frame") != "world"
            or int(command.get("robot", 0)) != self.robot):
            return False
        seq, session = int(command["command_seq"]), command["allocation_session"]
        stamp = float(command["stamp"])
        if (not session or not math.isfinite(stamp) or ros_now<stamp
            or command.get("mode")=="ROUTE" and ros_now-stamp>2.
            or seq <= self.seq or self.session not in (None, session)):
            return False
        if command["mode"] not in ("ROUTE", "STOP"):
            return False
        if command["mode"] == "ROUTE":
            new_token = token(command)
            if not (self.phase == "stopped" or self.phase in ("armed", "running") and self.active_token == new_token):
                return False
        elif not command.get("stop_id"):
            return False
        elif command["stop_id"] == self.stop_id and command.get("request_ids", []) != self.command.get("request_ids", []):
            return False
        self.session, self.seq, self.command_at = session, seq, now
        self.command = copy.deepcopy(command)
        if command["mode"] == "STOP":
            identifier = command["stop_id"]
            if identifier != self.stop_id:
                self.phase, self.stop_id = "stopping", identifier
                self.stop_started, self.proof_sent = now, False
                self.proof_at=-math.inf
                self.stop_ros = ros_now
                self.zero_since, self.zero_last, self.stationary_since = None, -math.inf, None
                self.samples, self.active_token, self.issuer = 0, None, None
                self.permit_seq, self.permit_at = 0, -math.inf
                self.executor_paused, self.certified_goal_seq = False, None
            return True
        new_token = token(command)
        if self.phase == "stopped":
            self.phase, self.active_token = "armed", new_token
            self.armed_at, self.progress_at = now, now
            self.progress_pose = None if self.odom is None else self.odom["pose"]
            self.permit_seq, self.permit_at, self.issuer = 0, -math.inf, None
            self.executor_paused, self.certified_goal_seq = False, None
            self.raw_at = -math.inf
        elif self.active_token != new_token or self.phase not in ("armed", "running"):
            return False
        return True

    def receive_permit(self, permit, now):
        if (self.phase not in ("armed", "running") or permit.get("token") != self.active_token
            or int(permit.get("permit_seq", 0)) <= self.permit_seq or not permit.get("issuer")):
            return False
        if self.issuer not in (None, permit["issuer"]):
            return False
        goal_seq = int(permit["goal_seq"]) if "goal_seq" in permit else None
        if goal_seq is not None and (goal_seq < 0 or self.certified_goal_seq is not None
                                     and goal_seq < self.certified_goal_seq):
            return False
        self.issuer, self.permit_seq = permit["issuer"], int(permit["permit_seq"])
        # property_tree emits JSON booleans as strings; "false" is truthy in
        # Python and must never accidentally grant motion permission.
        allowed = permit.get("allow") is True or permit.get("allow") == "true"
        if not allowed:
            self._trip("EXECUTOR_STOP")
            return True
        if self.phase=="armed":self.raw_at=-math.inf  # No cached pre-goal follower command.
        paused = permit.get("paused") is True or permit.get("paused") == "true"
        if paused or self.executor_paused:
            # Resume must use a new local proposal, never the previous
            # finished prefix's stale Twist. Neither deadline is reset.
            self.raw_at=-math.inf
        self.executor_paused, self.certified_goal_seq = paused, goal_seq
        self.permit_at, self.phase = now, "running"
        return True

    def receive_raw(self, vx, wz, now):
        if not math.isfinite(vx) or not math.isfinite(wz):
            return False
        self.raw, self.raw_at = (vx, wz), now
        return True

    def receive_odom(self, stamp, pose, twist, now, ros_now):
        if (not all(math.isfinite(v) for v in [stamp, *pose, *twist])
            or not 0 <= ros_now-stamp <= self.sensor_s
            or self.odom is not None and stamp <= self.odom["stamp"]):
            return False
        previous = self.odom
        self.odom = {"stamp": stamp, "pose": tuple(pose), "at": now}
        stationary = abs(twist[0]) <= .05 and abs(twist[1]) <= .09
        if previous is not None:
            dt = stamp-previous["stamp"]
            delta_yaw = math.atan2(math.sin(pose[2]-previous["pose"][2]), math.cos(pose[2]-previous["pose"][2]))
            stationary = stationary and math.dist(pose[:2], previous["pose"][:2])/dt <= .05 and abs(delta_yaw)/dt <= .09
        if self.phase in ("stopping","stopped") and now >= self.stop_started and stamp > self.stop_ros:
            if previous is None or now-previous["at"] > self.sensor_s or not stationary:
                self.stationary_since, self.samples = None, 0
            else:
                if self.stationary_since is None:
                    self.stationary_since = now
                self.samples += 1
        if self.phase == "running" and (self.progress_pose is None or
                math.dist(pose[:2], self.progress_pose[:2]) >= .1):
            self.progress_at, self.progress_pose = now, tuple(pose)
        return True

    def _trip(self, reason):
        if self.phase in ("armed", "running"):
            self.phase = "tripped"
            self.events.append({"schema": 2, "source": "velocity_gate",
                "status": "STOP_REQUIRED", "robot": self.robot,
                "allocation_session": self.session, "token": self.active_token, "reason": reason})

    def tick(self, now):
        if self.phase in ("armed", "running") and now-self.command_at > self.lease_s:
            self._trip("COORDINATOR_TIMEOUT")
        if self.phase == "running":
            if now-self.permit_at > self.permit_s:
                self._trip("EXECUTOR_TIMEOUT")
            elif self.odom is None or now-self.odom["at"] > self.sensor_s:
                self._trip("ODOMETRY_TIMEOUT")
            elif now-self.progress_at > self.stall_s:
                self._trip("EXECUTION_STALL")
            elif now-self.armed_at > self.run_s:
                self._trip("EXECUTION_DEADLINE")
            elif now-self.raw_at > .3 and now-self.armed_at > .5:
                self._trip("FOLLOWER_TIMEOUT")
        if self.phase == "armed" and now-self.armed_at > self.lease_s:
            self._trip("GOAL_NOT_STARTED")
        if (self.phase in ("stopping","stopped") and self.command.get('mode')=='STOP'
            and now-self.command_at<=self.lease_s
            and (not self.proof_sent or now-self.proof_at>=.75) and self.odom is not None
            and now-self.odom["at"] <= self.sensor_s and self.stationary_since is not None
            and now-self.stationary_since >= .5 and self.samples >= 3
            and self.zero_since is not None and now-self.zero_since >= .5
            and now-self.zero_last <= .1):
            self.events.append({"schema": 2, "source": "velocity_gate", "status": "STOPPED",
                "robot": self.robot, "allocation_session": self.session, "stop_id": self.stop_id,
                "request_ids": list(self.command.get("request_ids", [])),
                "fresh_samples": self.samples, "stationary_s": now-self.stationary_since,
                "zero_s": now-self.zero_since})
            self.phase, self.proof_sent = "stopped", True
            self.proof_at=now
        velocity = self.raw if (self.phase == "running" and not self.executor_paused
                                and now-self.raw_at <= .3) else (0., 0.)
        events, self.events = self.events, []
        return velocity, events

    def output_published(self, velocity, now):
        # Call only after the ROS publisher successfully accepted this output.
        if velocity == (0., 0.):
            if self.zero_since is None or now-self.zero_last > .1:
                self.zero_since = now
            self.zero_last = now
        else:
            self.zero_since = None
