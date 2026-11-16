"""Convert one native STG snapshot into owned topology plus connected tasks."""
from .graph import DeltaBuilder, point
from .grid import Grid
from .tasks import TaskTracker
from .scope import task_scope


class LocalExporter:
    def __init__(self, robot, session):
        self.delta = DeltaBuilder(robot, session)
        self.tasks = TaskTracker()

    def snapshot(self, snapshot, full=False):
        if snapshot["frame"] != "world":
            raise ValueError("common world required")
        g = snapshot["grid"]
        grid = Grid(g["width"], g["height"], g["resolution"], g["origin"], g["data"])
        pose = point(snapshot["pose"])
        root_cell = grid.cell(pose)
        if grid.state(root_cell) != 0:
            raise ValueError("robot is not in observed free space")
        records, anchors = {}, {}

        def node(local, cell, role):
            key = self.delta.key("node", local)
            records[key] = {"kind": "node", "p": grid.xy(cell), "role": role}
            anchors[key] = cell
            return key

        def edge(a, b, cells):
            if not cells or len(cells) < 2:
                return
            name = min(a, b).split("/node/")[1] + "~" + max(a, b).split("/node/")[1]
            key = self.delta.key("edge", name)
            records[key] = {"kind": "edge", "a": a, "b": b,
                "path": [grid.xy(u) for u in cells], "resolution": grid.resolution,
                "evidence": "known_free"}

        root = node("root", root_cell, "robot")
        native = {}
        for item in snapshot.get("nodes", []):
            cell = grid.cell(item["p"])
            if grid.state(cell) == 0:
                native[str(item["id"])] = node("stg_" + str(item["id"]), cell, "stg")
        for a, b in snapshot.get("edges", []):
            a, b = native.get(str(a)), native.get(str(b))
            if a and b:
                edge(a, b, grid.path(anchors[a], anchors[b]))
        # Attach the moving robot through a validated own-map path, not a straight snap.
        for key in sorted(native.values(), key=lambda k: (sum(abs(a-b) for a,b in zip(anchors[k], root_cell)), k)):
            cells = grid.path(root_cell, anchors[key])
            if cells:
                edge(root, key, cells)
                break
        for local, task in self.tasks.update(grid).items():
            portal_keys = []
            if task["state"] == "pending":
                for cell in task["portal_cells"]:
                    key = node("portal_%d_%d" % cell, cell, "portal")
                    portal_keys.append(key)
                    # Preserve native topology; connect the portal to a reachable anchor.
                    for anchor in sorted([root] + list(native.values()),
                                         key=lambda k: (sum(abs(a-b) for a,b in zip(anchors[k], cell)), k)):
                        cells = grid.path(anchors[anchor], cell)
                        if cells:
                            edge(anchor, key, cells)
                            break
            records[self.delta.key("task", local)] = {"kind": "task", "tile": task["tile"],
                "signature": task["signature"], "unknown_count": len(task["cells"]),
                "portals": portal_keys, "state": task["state"], "map_rev": task["map_rev"],
                "observation": task["observation"],
                "parents": [self.delta.key("task", x) for x in task["parents"]]}
            records[self.delta.key("task", local)]["scope"] = task_scope(grid, task)
        # The real pose-to-cell-center attachment cost is retained in bidding.
        state = {"root": root, "pose": pose, "stamp": float(snapshot["stamp"]),
                 "map_rev": self.tasks.map_rev, "resolution": grid.resolution}
        return self.delta.build(records, state, full=full)
