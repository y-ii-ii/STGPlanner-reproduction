"""Graph-distance allocation on common-world topology (GVP-MREP-inspired).

This is a ground-robot adaptation, not a reproduction of the UAV EROI/MINCO
system. A single perfect-communication authority commits ownership. The input
contains topology and task summaries only; no fused occupancy or ground truth.
"""
import hashlib
import math
from .graph import Navigation, point, wire
from .scope import claims_conflict, completion_signature, unknown_support, work_claim
from .retry_memory import RetryMemory
from .observations import TeamObservations


class TaskLedger:
    def __init__(self):
        self.items, self.version = {}, 0

    def assign(self, key, owner):
        if key not in self.items or self.items[key]["state"] == "completed":
            self.version += 1
            self.items[key] = {"owner": owner, "version": self.version, "state": "assigned"}
        return self.items[key]

    def offer(self, key, receiver):
        item = self.items[key]
        if item["state"] != "assigned" or item["owner"] == receiver:
            raise ValueError("only an unexecuted task can be offered without a stop ACK")
        self.version += 1
        item.update(receiver=receiver, version=self.version, state="offered")
        return dict(item)

    def acknowledge(self, key, robot, version):
        item = self.items[key]
        expected = item.get("receiver", item["owner"])
        if version != item["version"] or robot != expected or item["state"] not in ("assigned", "offered", "dispatched", "active"):
            return False
        item.update(owner=robot, state="active")
        item.pop("receiver", None)
        return True

    def release(self, key, robot, version):
        item = self.items[key]
        if (item["state"] == "offered" and item.get("receiver") == robot
                and item["version"] == version):
            item.pop("receiver")
            item["state"] = "assigned"
            return True
        if item["owner"] != robot or item["version"] != version:
            return False
        item["state"] = "completed" if item.get("observed_completed") else "assigned"
        return True


class Coordinator:
    def __init__(self, robots=(1, 2), max_age=3.0):
        self.robots, self.max_age = tuple(sorted(robots)), max_age
        self.ledger, self.command_seq, self.commands = TaskLedger(), 0, {}
        self.deferred = {}
        self.completed_support = {}  # Authority overlay; never rewrite peer-owned maps/tasks.
        # Static common-world phase only: validated observation evidence follows
        # geometry across renamed/source-alias tasks, not transient task IDs.
        # This is a completion mask, never free-space/navigation evidence.
        self.observed_support = set()
        self.team_observations=TeamObservations(self.observed_support)
        self.diagnostics={}
        self.retry_memory=RetryMemory()
        self.missing_since={}

    def ingest_author_observations(self,store,keys):
        for key in keys:
            record=store.records.get(key)
            if not record or record['deleted'] or record['value'].get('kind')!='task':continue
            robot=int(key.split('/')[0]);state=store.states.get(robot,{})
            self.team_observations.accept(key,record['value'],state)

    def team_completed(self,active):
        """Information may be complete; execution ownership still needs STOP."""
        support=unknown_support(active.get('scopes',[]));item=self.ledger.items.get(active.get('task'))
        if (not support or not support<=self.observed_support or item is None
                or item['version']!=active.get('version')
                or item.get('receiver',item['owner'])!=int(active.get('robot',0))):return False
        if item['state']=='offered':
            item.update(owner=int(active['robot']),state='dispatched');item.pop('receiver',None)
        item['observed_completed']=True
        return True

    def commit_dispatches(self,plans):
        """Reserve delivered ROUTEs, not intentions still blocked by STOP/ACK.

        Ledger ownership is exclusive even while assigned; only a real ROUTE
        enters dispatched state and requires a physical release barrier.
        """
        for r,p in plans.items():
            if p.get('mode')!='ROUTE':continue
            item=self.ledger.items.get(p['task'])
            if item and item['version']==p['version'] and item.get('receiver',item['owner'])==r and item['state'] in ('assigned','offered'):
                item.update(owner=r,state='dispatched');item.pop('receiver',None)

    def fail_execution(self,robot,active,now,unsafe_start=False):
        self.defer(robot,active['task'],now,15.)
        self.retry_memory.fail(robot,active,now,unsafe_start)

    def defer(self, robot, task, wall_now, seconds=8.):
        self.deferred[robot,task] = max(self.deferred.get((robot,task),0.),wall_now+seconds)

    def groups(self, store, nav):
        groups = []
        for key, task in sorted(store.live("task").items()):
            if task["state"] != "pending":
                continue
            support = unknown_support([task["scope"]]) if "scope" in task else frozenset()
            if support and (support <= self.observed_support or support <= self.completed_support.get(key, frozenset())):
                continue
            portals = [p for p in task["portals"] if p in nav.nodes]
            positions = {point(nav.nodes[p]["p"]) for p in portals}
            if not portals:
                continue
            # Conservative cross-source association: same unknown digest/tile AND
            # an exact common free portal. Bounds overlap alone is never enough.
            match = next((g for g in groups if g["signature"] == task["signature"]
                          and g["tile"] == task["tile"] and g["positions"] & positions), None)
            if match:
                match["members"].append(key)
                match["portals"].update(portals)
                match["positions"].update(positions)
            else:
                groups.append(dict(id=key, members=[key], portals=set(portals),
                    positions=positions, tile=task["tile"], signature=task["signature"]))
        return groups

    def plan(self, store, now, wall_now=None, committed=None, reserved=None):
        wall_now = now if wall_now is None else wall_now
        self.command_seq += 1
        waits = {r: {"schema": 1, "frame": "world", "robot": r, "mode": "WAIT",
                    "stamp": now, "command_seq": self.command_seq, "path": []}
                 for r in self.robots}
        if any(r not in store.states or not 0 <= now-store.states[r]["stamp"] <= self.max_age
               for r in self.robots):
            self.diagnostics={'reason':'stale_source_state','state_age_s':{str(r):now-store.states[r]['stamp'] if r in store.states else None for r in self.robots}}
            self.commands = waits
            return waits
        nav = Navigation(store)
        # An offer never emitted as a ROUTE carries no physical ownership. Rebid
        # it freely; actual dispatched/active work remains protected until ACK.
        for item in self.ledger.items.values():
            if item['state']=='offered':item.pop('receiver',None);item['state']='assigned'
        groups = self.groups(store, nav)
        tasks = store.live("task")
        contracts = {g["id"]: dict(task=g["id"], task_members=g["members"],
            scopes=[tasks[k]["scope"] for k in g["members"] if "scope" in tasks[k]])
            for g in groups}
        claims = {gid:work_claim(contract) for gid,contract in contracts.items()}
        occupied = {r:work_claim(active) for r,active in (reserved or committed or {}).items()}
        excluded = {r:0 for r in self.robots}
        trees = {r: nav.search(store.states[r]["root"]) for r in self.robots}
        searches = {r:tree[0] for r,tree in trees.items()}
        costs, portal_for = {}, {}
        routes = {}
        for group in groups:
            gid = group["id"]
            for r in self.robots:
                attachment = math.dist(point(store.states[r]["pose"]),
                                       point(nav.nodes[store.states[r]["root"]]["p"]))
                options = [(searches[r].get(point(nav.nodes[p]["p"]), math.inf) + attachment, p)
                           for p in group["portals"]]
                costs[r, gid] = math.inf
                if self.deferred.get((r,gid),-math.inf)>wall_now:
                    continue # Execution feedback is temporary; preserve pending work.
                if any(peer!=r and claims_conflict(claims[gid],claim) for peer,claim in occupied.items()):
                    # The supervisor's STOP barrier would hold this intention.
                    # Leave the group pending and bid on disjoint work instead.
                    excluded[r] += 1
                    continue
                # A failed nearest portal must not hide a different reachable
                # entrance of this same connected task.
                for cost,portal in sorted(options):
                    if not math.isfinite(cost):break
                    route=nav.route(store.states[r]['root'],portal,trees[r])
                    pose=point(store.states[r]['pose'])
                    if route is None or self.retry_memory.blocked(r,[pose]+route['path'],wall_now):
                        continue
                    costs[r,gid],portal_for[r,gid],routes[r,gid]=cost,portal,route
                    break
            reachable = [r for r in self.robots if math.isfinite(costs[r, gid])]
            if reachable:
                best = min(reachable, key=lambda r: (costs[r, gid], r))
                item = self.ledger.assign(gid, best)
                if item["state"] == "assigned" and item["owner"] != best:
                    # Only never-executing work can be offered automatically.
                    # Active/dispatched work waits for explicit release feedback.
                    self.ledger.offer(gid, best)
        # An observation-completed/disappeared task stops being dispatched, but is
        # not relabelled completed just because this filtered group list is empty.
        valid = {g["id"] for g in groups}
        candidates = {r: [] for r in self.robots}
        for gid in sorted(valid):
            item = self.ledger.items.get(gid)
            if not item:
                continue
            if item.get("observed_completed"):
                continue  # New/grown scope waits for the old generation's stop proof.
            r = item.get("receiver", item["owner"])
            if math.isfinite(costs.get((r, gid), math.inf)):
                candidates[r].append(gid)
        # Idle assistance is allowed only for work not currently executing.
        # Active work needs an explicit old-owner release/stop ACK first.
        for r in self.robots:
            if candidates[r]:
                continue
            options = [gid for gid in valid if gid in self.ledger.items
                and self.ledger.items[gid]["state"] == "assigned"
                and len(candidates[self.ledger.items[gid]["owner"]]) > 1
                and math.isfinite(costs.get((r, gid), math.inf))]
            if options:
                gid = min(options, key=lambda k: (costs[r, k], k))
                old_owner = self.ledger.items[gid]["owner"]
                self.ledger.offer(gid, r)
                candidates[old_owner].remove(gid)
                candidates[r].append(gid)
        for r, available in candidates.items():
            available = [gid for gid in available if not any(
                peer!=r and claims_conflict(claims[gid],claim)
                for peer,claim in occupied.items())]
            if not available:
                continue
            # Keep an already active task; otherwise choose closest within responsibility.
            gid = min(available, key=lambda k: (self.ledger.items[k]["state"] not in ("active", "dispatched"),
                                                costs[r, k], k))
            item = self.ledger.items[gid]
            route = routes[r,gid]
            if route is None:
                continue
            path = route["path"]
            pose = point(store.states[r]["pose"])
            if pose != point(path[0]):
                path = [pose] + path
            waits[r] = {**contracts[gid], "schema": 1, "frame": "world", "robot": r, "mode": "ROUTE",
                "stamp": now, "command_seq": self.command_seq,
                "version": item["version"], "path": path,
                "cost_m": costs[r, gid], "edge_ids": route["edges"],
                "portal":portal_for[r,gid],
                "peer_edges": sorted({e for e in route["edges"] if not e.startswith(store.states[r]["author"] + "/")}),
                "graph_digest": store.digest()}
            # The supervisor may still withhold this intention behind a STOP
            # barrier. commit_dispatches() runs on the actual published ROUTEs.
            waits[r]["scope_digest"], waits[r]["scope_cells"] = completion_signature(waits[r]["scopes"])
            # Also keep simultaneous fresh requests disjoint. A still-active
            # claim persists unchanged until its stop proof in the supervisor.
            occupied.setdefault(r, claims[gid])
        retained=[]
        for r in self.robots:
            active=(committed or {}).get(r)
            identity=(active['task'],active['version'],active.get('dispatch_id')) if active else None
            if not active or (waits[r].get('task'),waits[r].get('version'))==identity[:2]:
                self.missing_since.pop(r,None)
                continue
            deadline_key,began=self.missing_since.get(r,(identity,wall_now))
            if deadline_key!=identity:began=wall_now
            self.missing_since[r]=(identity,began)
            if wall_now-began>=2.0 or self.deferred.get((r,active['task']),-math.inf)>wall_now:
                continue
            portal=active.get('portal')
            if portal not in nav.nodes or self.team_completed(active):
                continue
            route=nav.route(store.states[r]['root'],portal,trees[r])
            if route is None or route['cost']<.65:continue
            path=[point(store.states[r]['pose'])]+route['path']
            if self.retry_memory.blocked(r,path,wall_now):continue
            # Debounce a disappearing frontier only while the old portal still
            # has a current route. Use the same task scope and owner. Genuine
            # completion and execution failures still enter the STOP barrier.
            waits[r]=dict(active,path=path,stamp=now,command_seq=self.command_seq,
                          edge_ids=route['edges'],graph_digest=store.digest(),cost_m=route['cost'])
            retained.append(r)
        self.commands = waits
        self.diagnostics={'reason':'allocated','groups':len(groups),'pending_tasks':sum(t['state']=='pending' for t in store.live('task').values()),
            'completed_support_keys':len(self.completed_support),'reachable_groups':{str(r):sum(math.isfinite(costs.get((r,g['id']),math.inf)) for g in groups) for r in self.robots},
            'candidates':{str(r):len(v) for r,v in candidates.items()},'desired':{str(r):c['mode'] for r,c in waits.items()},
            'retained_transient_contracts':retained,'excluded_peer_contract_candidates':excluded}
        return waits

    def observe_completed(self, feedback, active, ros_now):
        """Accept only current assignee observation evidence, then wait for STOP.

        A task discovered by A can be observed by B without fusing B's occupancy
        into A's map. Empty candidate lists, failures and timeouts are not evidence.
        """
        if (active.get("mode") != "ROUTE" or feedback.get("source") != "planner"
                or feedback.get("status") != "OBSERVATION_COMPLETED"
                or any(str(feedback.get(k)) != str(active.get(k)) for k in
                       ("robot", "task", "version", "dispatch_id", "allocation_session"))):
            return False
        digest, count = completion_signature(active.get("scopes", []))
        stamp = float(feedback.get("map_stamp", -math.inf))
        if (not count or feedback.get("scope_digest") != digest
                or int(feedback.get("required_cells", 0)) != count
                or int(feedback.get("observed_cells", 0)) != count
                or not math.isfinite(stamp) or not 0 <= ros_now-stamp <= 1.):
            return False
        item = self.ledger.items.get(active["task"])
        if (item is None or item.get("receiver", item["owner"]) != int(active["robot"])
                or item["version"] != int(active["version"])):
            return False
        support = unknown_support(active["scopes"])
        self.observed_support.update(support)
        for key in active["task_members"]:
            self.completed_support[key] = self.completed_support.get(key, frozenset()) | support
        if item["state"] == "offered":
            item.update(owner=int(active["robot"]), state="dispatched")
            item.pop("receiver", None)
        item["observed_completed"] = True
        return True

    def feedback(self, feedback):
        r = int(feedback["robot"])
        command = self.commands.get(r, {})
        # Boost property_tree's JSON writer emits scalars as strings. Normalize
        # the native wire values, while still checking the exact dispatch/version.
        sequence = int(feedback.get("command_seq", -1))
        version = int(feedback.get("version", -1))
        if (command.get("mode") != "ROUTE" or sequence != command["command_seq"]
            or feedback.get("task") != command["task"] or version != command["version"]):
            return False
        key, version = command["task"], command["version"]
        if feedback["status"] == "EXECUTOR_ACCEPTED" and feedback.get("source")=="executor":
            return self.ledger.acknowledge(key, r, version)
        # A planner failure or an unverified "STOPPED" string cannot release
        # dispatched work. The execution supervisor alone applies a nonce-bound
        # final velocity-gate stop proof, then calls ledger.release explicitly.
        return False

    def partition(self, store):
        """Nearest-robot ownership of navigation samples, independent of commitments."""
        nav = Navigation(store)
        searches = {r: nav.search(store.states[r]["root"])[0] for r in self.robots}
        result = {}
        for p in nav.adj:
            values = [(d.get(p, math.inf) + math.dist(point(store.states[r]["pose"]),
                       point(nav.nodes[store.states[r]["root"]]["p"])), r) for r, d in searches.items()]
            cost, robot = min(values)
            result[p] = robot if math.isfinite(cost) else None
        return result
