"""Convert one native STG snapshot into owned topology plus connected tasks."""
from .graph import DeltaBuilder, point, wire
from .grid import Grid
from .tasks import TaskTracker
from .scope import task_scope,completion_signature
from .navigation_history import NavigationHistory


class LocalExporter:
    def __init__(self, robot, session):
        self.delta = DeltaBuilder(robot, session)
        self.tasks = TaskTracker()
        self.last_snapshot_key = None
        self.history=NavigationHistory()
        self.completion_proofs={}

    def snapshot(self, snapshot, full=False):
        if snapshot["frame"] != "world":
            raise ValueError("common world required")
        g = snapshot["grid"]
        grid = Grid(g["width"], g["height"], g["resolution"], g["origin"], g["data"])
        pose = point(snapshot["pose"])
        root_cell = grid.cell(pose)
        if grid.state(root_cell) != 0:
            raise ValueError("robot is not in observed free space")
        snapshot_key=(grid.width,grid.height,grid.origin,grid.resolution,grid.data,root_cell,
             wire(snapshot.get("nodes",[])),wire(snapshot.get("edges",[])))
        if snapshot_key==self.last_snapshot_key:
            # Pose/time can advance without changing any navigation/task record.
            records={k:r["value"] for k,r in self.delta.previous.items() if not r["deleted"]}
            state={"root":self.delta.key("node","root"),"pose":pose,"stamp":float(snapshot["stamp"]),
                   "map_rev":self.tasks.map_rev,"resolution":grid.resolution}
            return self.delta.build(records,state,full=full)
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
        root_tree=grid.path_tree(root_cell)
        def from_root(cell):
            if cell not in root_tree:
                return None
            path=[]
            while cell is not None:
                path.append(cell)
                cell=root_tree[cell]
            return list(reversed(path))
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
            cells = from_root(anchors[key])
            if cells:
                edge(root, key, cells)
                break
        for local, task in self.tasks.update(grid).items():
            portal_keys = []
            if task["state"] == "pending":
                viewpoints=set(task['portal_cells'])
                viewpoints.update(grid.stand_off(cell,root_tree) for cell in task['portal_cells'] if cell in root_tree)
                for cell in sorted(viewpoints):
                    key = node("portal_%d_%d" % cell, cell, "portal")
                    portal_keys.append(key)
                    # A nearby native anchor may itself be disconnected from
                    # the robot after observed-free edge validation. An actual
                    # own-free root route is the admission evidence, not merely
                    # reachability from an isolated nearest anchor.
                    cells=from_root(cell)
                    if cells:edge(root,key,cells)
            records[self.delta.key("task", local)] = {"kind": "task", "tile": task["tile"],
                "signature": task["signature"], "unknown_count": len(task["cells"]),
                "portals": portal_keys, "state": task["state"], "map_rev": task["map_rev"],
                "observation": task["observation"],
                "parents": [self.delta.key("task", x) for x in task["parents"]]}
            scope=task_scope(grid,task)
            record=records[self.delta.key("task",local)];record['scope']=scope
            if task['state']=='completed' and task['observation']=='all_previous_unknown_observed':
                digest,count=completion_signature([scope]);old=self.completion_proofs.get(local)
                if old is None or old['scope_digest']!=digest:
                    # Certify actual own-map observations, never mere absence
                    # of candidates. Preserve this historical static-world
                    # evidence when a later local window no longer includes it.
                    if count and all(grid.state(u) in (0,100) for u in task['cells']):
                        old=dict(schema=1,frame='world',author=self.delta.author,
                            evidence='own_observed_support',scope_digest=digest,
                            required_cells=count,observed_cells=count,map_rev=task['map_rev'],stamp=float(snapshot['stamp']))
                        self.completion_proofs[local]=old
                if old is not None and old['scope_digest']==digest:record['observation_proof']=dict(old)
        # The real pose-to-cell-center attachment cost is retained in bidding.
        state = {"root": root, "pose": pose, "stamp": float(snapshot["stamp"]),
                 "map_rev": self.tasks.map_rev, "resolution": grid.resolution}
        self.history.update(grid,records,self.delta)
        result=self.delta.build(records, state, full=full)
        self.last_snapshot_key=snapshot_key
        return result
