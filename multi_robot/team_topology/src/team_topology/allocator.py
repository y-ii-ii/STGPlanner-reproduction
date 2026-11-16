"""Graph-distance allocation on common-world topology (GVP-MREP-inspired).

This is a ground-robot adaptation, not a reproduction of the UAV EROI/MINCO
system. A single perfect-communication authority commits ownership. The input
contains topology and task summaries only; no fused occupancy or ground truth.
"""
import hashlib
import math
from .graph import Navigation, point, wire


class TaskLedger:
    def __init__(self):
        self.items, self.version = {}, 0

    def assign(self, key, owner):
        if key not in self.items:
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
        if version != item["version"] or robot != expected or item["state"] not in ("assigned", "offered", "active"):
            return False
        item.update(owner=robot, state="active")
        item.pop("receiver", None)
        return True

    def release(self, key, robot, version):
        item = self.items[key]
        if item["owner"] != robot or item["version"] != version:
            return False
        item["state"] = "assigned"
        return True


class Coordinator:
    def __init__(self, robots=(1, 2), max_age=3.0):
        self.robots, self.max_age = tuple(sorted(robots)), max_age
        self.ledger, self.command_seq, self.commands = TaskLedger(), 0, {}

    def groups(self, store, nav):
        groups = []
        for key, task in sorted(store.live("task").items()):
            if task["state"] != "pending":
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

    def plan(self, store, now):
        self.command_seq += 1
        waits = {r: {"schema": 1, "frame": "world", "robot": r, "mode": "WAIT",
                    "stamp": now, "command_seq": self.command_seq, "path": []}
                 for r in self.robots}
        if any(r not in store.states or not 0 <= now-store.states[r]["stamp"] <= self.max_age
               for r in self.robots):
            self.commands = waits
            return waits
        nav = Navigation(store)
        groups = self.groups(store, nav)
        searches = {r: nav.search(store.states[r]["root"])[0] for r in self.robots}
        costs, portal_for = {}, {}
        for group in groups:
            gid = group["id"]
            for r in self.robots:
                attachment = math.dist(point(store.states[r]["pose"]),
                                       point(nav.nodes[store.states[r]["root"]]["p"]))
                options = [(searches[r].get(point(nav.nodes[p]["p"]), math.inf) + attachment, p)
                           for p in group["portals"]]
                costs[r, gid], portal_for[r, gid] = min(options)
            reachable = [r for r in self.robots if math.isfinite(costs[r, gid])]
            if reachable:
                self.ledger.assign(gid, min(reachable, key=lambda r: (costs[r, gid], r)))
        # An observation-completed/disappeared task stops being dispatched, but is
        # not relabelled completed just because this filtered group list is empty.
        valid = {g["id"] for g in groups}
        candidates = {r: [] for r in self.robots}
        for gid in sorted(valid):
            item = self.ledger.items.get(gid)
            if not item:
                continue
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
            if not available:
                continue
            # Keep an already active task; otherwise choose closest within responsibility.
            gid = min(available, key=lambda k: (self.ledger.items[k]["state"] != "active",
                                                costs[r, k], k))
            item = self.ledger.items[gid]
            route = nav.route(store.states[r]["root"], portal_for[r, gid])
            if route is None:
                continue
            path = route["path"]
            pose = point(store.states[r]["pose"])
            if pose != point(path[0]):
                path = [pose] + path
            waits[r] = {"schema": 1, "frame": "world", "robot": r, "mode": "ROUTE",
                "stamp": now, "command_seq": self.command_seq,
                "task": gid, "version": item["version"], "path": path,
                "cost_m": costs[r, gid], "edge_ids": route["edges"],
                "peer_edges": sorted({e for e in route["edges"] if not e.startswith(store.states[r]["author"] + "/")}),
                "graph_digest": store.digest()}
        self.commands = waits
        return waits

    def feedback(self, feedback):
        r = int(feedback["robot"])
        command = self.commands.get(r, {})
        if (command.get("mode") != "ROUTE" or feedback.get("command_seq") != command["command_seq"]
            or feedback.get("task") != command["task"] or feedback.get("version") != command["version"]):
            return False
        key, version = command["task"], command["version"]
        if feedback["status"] == "ACCEPTED":
            return self.ledger.acknowledge(key, r, version)
        if feedback["status"] in ("BLOCKED", "STOPPED"):
            # Failures release responsibility for retry, never mark observed.
            return self.ledger.release(key, r, version)
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

