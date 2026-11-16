"""Versioned topology exchange and routing, without an exchanged occupancy map.

Inspired by MGGPlanner graph exchange and GVP-MREP MR-DTG. Implemented here
independently: no paper implementation is copied. Point coincidences only join
observed path samples on the SAME world lattice; proximity alone never adds an
edge through a wall. Persistent records remain source-owned, not Boost labels.
"""
import copy
import hashlib
import heapq
import json
import math


def wire(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def point(value):
    if len(value) != 2 or not all(math.isfinite(float(v)) for v in value):
        raise ValueError("non-finite 2D point")
    return tuple(round(float(v), 6) for v in value)


def length(path):
    return sum(math.dist(a, b) for a, b in zip(path, path[1:]))


class DeltaBuilder:
    """Own-author record revisions plus explicit tombstones; full repair on demand."""
    def __init__(self, robot, session):
        if int(robot) < 1 or not session or "/" in session:
            raise ValueError("invalid source identity")
        self.author = str(int(robot)) + "/" + session
        self.robot = int(robot)
        self.seq = 0
        self.previous = {}

    def key(self, kind, local):
        return self.author + "/" + kind + "/" + str(local)

    def build(self, records, state, full=False):
        self.seq += 1
        result = {}
        for key, value in records.items():
            if not key.startswith(self.author + "/"):
                raise ValueError("foreign authored record")
            old = self.previous.get(key)
            if old is not None and old["value"] == value:
                result[key] = old
            else:
                result[key] = {"rev": self.seq, "deleted": False, "value": copy.deepcopy(value)}
        # Keep deletion revisions indefinitely in this first-stage implementation.
        for key, old in self.previous.items():
            if key not in result:
                result[key] = old if old["deleted"] else {
                    "rev": self.seq, "deleted": True, "value": None}
        changed = {k: v for k, v in result.items()
                   if full or v != self.previous.get(k)}
        self.previous = result
        return {"schema": 1, "frame": "world", "author": self.author,
                "robot": self.robot, "seq": self.seq, "full": full or self.seq == 1,
                "records": changed, "state": copy.deepcopy(state)}


class GraphStore:
    """Atomic, idempotent receive; sequence gaps require an explicit full repair.

    Perfect communication is assumed, not guaranteed by dictionary order. A
    partial out-of-order delta is rejected rather than silently losing deletes.
    Full repair contains tombstones and can safely bridge a sequence gap.
    """
    def __init__(self):
        self.records, self.sequences, self.states, self.robot_authors = {}, {}, {}, {}
        self.received_bytes = 0
        self.last_packets = {}

    def apply(self, delta):
        if delta.get("schema") != 1 or delta.get("frame") != "world":
            raise ValueError("unsupported schema/frame")
        author, robot, seq = delta["author"], int(delta["robot"]), int(delta["seq"])
        if not author.startswith(str(robot) + "/") or len(author.split("/")) != 2 or not author.split("/")[1]:
            raise ValueError("author/robot mismatch")
        # Session replacement needs an explicit restart protocol; fail closed now.
        if robot in self.robot_authors and self.robot_authors[robot] != author:
            raise ValueError("robot session replacement requires reset")
        last = self.sequences.get(author, 0)
        packet = wire(delta)
        if seq == last and self.last_packets.get(author) != packet:
            raise ValueError("same-sequence conflict")
        if seq <= last:
            return False
        if seq != last + 1 and not delta.get("full"):
            raise ValueError("delta sequence gap: request full repair")
        if delta.get("full") and any(k.startswith(author + "/") and k not in delta["records"] for k in self.records):
            raise ValueError("full repair omitted an existing record/tombstone")
        candidate = copy.deepcopy(self.records)
        for key, record in delta["records"].items():
            if not key.startswith(author + "/") or record["rev"] > seq or record["rev"] < 1:
                raise ValueError("foreign ID or invalid revision")
            old = candidate.get(key)
            if old and old["rev"] == record["rev"] and old != record:
                raise ValueError("same-revision conflict")
            if old is None or old["rev"] < record["rev"]:
                candidate[key] = copy.deepcopy(record)
        # Geometry is checked before publishing any part of the transaction.
        live = {k: r["value"] for k, r in candidate.items() if not r["deleted"]}
        for key, obj in live.items():
            if obj["kind"] == "node":
                point(obj["p"])
            elif obj["kind"] == "edge":
                if obj.get("evidence") != "known_free":
                    raise ValueError("unknown-space edge is not navigable")
                path = [point(p) for p in obj["path"]]
                if len(path) < 2:
                    raise ValueError("empty edge")
                if not obj["a"].startswith(key.split("/edge/")[0] + "/") or not obj["b"].startswith(key.split("/edge/")[0] + "/"):
                    raise ValueError("edge endpoints must retain author provenance")
                if obj["a"] in live and obj["b"] in live:
                    if point(live[obj["a"]]["p"]) != path[0] or point(live[obj["b"]]["p"]) != path[-1]:
                        raise ValueError("edge endpoint mismatch")
                resolution = float(obj["resolution"])
                if not math.isfinite(resolution) or resolution <= 0:
                    raise ValueError("bad edge resolution")
                if any(math.dist(a, b) > resolution * 1.001 for a, b in zip(path, path[1:])):
                    raise ValueError("unsampled jump in edge")
            elif obj["kind"] != "task":
                raise ValueError("unknown record kind")
        point(delta["state"]["pose"])
        if not math.isfinite(float(delta["state"]["stamp"])):
            raise ValueError("non-finite source timestamp")
        if delta["state"]["root"] not in live:
            raise ValueError("missing robot attachment")
        self.records = candidate
        self.sequences[author] = seq
        self.states[robot] = dict(delta["state"], author=author, seq=seq)
        self.robot_authors[robot] = author
        self.last_packets[author] = packet
        self.received_bytes += len(packet.encode("utf-8")) + 4  # ROS String length prefix
        return True

    def live(self, kind):
        return {k: r["value"] for k, r in self.records.items()
                if not r["deleted"] and r["value"]["kind"] == kind}

    def digest(self):
        return hashlib.sha256(wire(self.records).encode()).hexdigest()


class Navigation:
    """Sparse exchanged graph; expanded path-sample index only for local search.

    A shared sample is an exact common-world position on known-free paths.
    This conservative first-stage association cannot estimate inter-robot pose
    or perform SLAM loop closure. Near parallel paths do NOT connect.
    """
    def __init__(self, store):
        self.nodes = store.live("node")
        self.adj, self.samples = {}, {}
        self.edges = store.live("edge")
        resolutions = {round(e["resolution"], 6) for e in self.edges.values()}
        if len(resolutions) > 1:
            raise ValueError("phase 1 requires the same world lattice resolution")
        for edge_id, edge in sorted(self.edges.items()):
            if edge["a"] not in self.nodes or edge["b"] not in self.nodes:
                continue  # A node tombstone also disables dependent edges.
            path = [point(p) for p in edge["path"]]
            for a, b in zip(path, path[1:]):
                if a == b:
                    continue
                cost = math.dist(a, b)
                self.adj.setdefault(a, []).append((b, cost, edge_id))
                self.adj.setdefault(b, []).append((a, cost, edge_id))
        for node in self.nodes.values():
            self.adj.setdefault(point(node["p"]), [])

    def search(self, start_key):
        start = point(self.nodes[start_key]["p"])
        dist, previous, queue = {start: 0.0}, {}, [(0.0, start)]
        while queue:
            cost, cur = heapq.heappop(queue)
            if cost != dist[cur]:
                continue
            for nxt, step, edge in sorted(self.adj[cur]):
                value = cost + step
                if value + 1e-9 < dist.get(nxt, math.inf):
                    dist[nxt], previous[nxt] = value, (cur, edge)
                    heapq.heappush(queue, (value, nxt))
        return dist, previous

    def route(self, start_key, end_key):
        dist, prev = self.search(start_key)
        end, start = point(self.nodes[end_key]["p"]), point(self.nodes[start_key]["p"])
        if end not in dist:
            return None
        points, edges = [end], []
        while points[-1] != start:
            parent, edge = prev[points[-1]]
            edges.append(edge)
            points.append(parent)
        return {"cost": dist[end], "path": list(reversed(points)),
                "edges": list(reversed(edges))}
