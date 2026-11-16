"""C²-inspired connected task units, independently adapted for ground robots.

Coarse tiles are indexes, not exclusive tasks. Unknown and free components in
each tile determine portal-connected tasks. Unknown connectivity is an estimate,
never an executable route. Local membership stays local; only a compact digest,
portal node references, counts and lifecycle metadata are exchanged.
"""
import hashlib
import math
from .graph import wire


class TaskTracker:
    def __init__(self, tile_size=4.0, min_unknown=1):
        self.tile_size, self.min_unknown = tile_size, min_unknown
        self.counter, self.items, self.map_rev = 0, {}, 0
        self.lattice = None
        self.last_observation = None

    def update(self, grid):
        lattice = (grid.resolution, grid.origin)
        if self.lattice is not None and self.lattice != lattice:
            raise ValueError("task tracking requires a fixed world lattice")
        self.lattice = lattice
        observation = (grid.width, grid.height, grid.data)
        if observation == self.last_observation:
            return self.items
        self.map_rev += 1
        self.last_observation = observation
        # A pending task must have an actually observed free/unknown boundary.
        # Select those tiles first; do not flood-fill every untouched world tile.
        frontier_tiles = set()
        for index, value in enumerate(grid.data):
            if value != 0:
                continue
            u = (index % grid.width, index // grid.width)
            for v in grid.neighbors(u):
                if grid.state(v) == -1:
                    p = grid.xy(v)
                    frontier_tiles.add((math.floor(p[0]/self.tile_size), math.floor(p[1]/self.tile_size)))
        tiles = {}
        for tile in frontier_tiles:
            states = {-1:set(), 0:set()}
            # A small conservative index halo avoids floating-point boundary
            # errors; the exact original world-cell tile test decides membership.
            ax=max(0,math.floor((tile[0]*self.tile_size-grid.origin[0])/grid.resolution)-1)
            bx=min(grid.width,math.ceil(((tile[0]+1)*self.tile_size-grid.origin[0])/grid.resolution)+1)
            ay=max(0,math.floor((tile[1]*self.tile_size-grid.origin[1])/grid.resolution)-1)
            by=min(grid.height,math.ceil(((tile[1]+1)*self.tile_size-grid.origin[1])/grid.resolution)+1)
            for y in range(ay,by):
                for x in range(ax,bx):
                    u=(x,y);value=grid.state(u)
                    if value not in (-1,0):
                        continue
                    p=grid.xy(u)
                    if (math.floor(p[0]/self.tile_size),math.floor(p[1]/self.tile_size))==tile:
                        states[value].add(u)
            tiles[tile]=states
        candidates = []
        for tile, states in sorted(tiles.items()):
            # A tile border is not a physical wall: an unknown component may
            # be approached from an observed-free cell in its neighboring tile.
            halo = {v for u in states[-1] for v in grid.neighbors(u) if grid.state(v) == 0}
            free_components = grid.components(states[0] | halo)
            for unknown in grid.components(states[-1]):
                if len(unknown) < self.min_unknown:
                    continue
                boundary = {v for u in unknown for v in grid.neighbors(u) if grid.state(v) == 0}
                for free in free_components:
                    portals = boundary & free
                    if not portals:
                        continue
                    # Separate portal patches preserve entrances, not their unsafe centroid.
                    representatives = [min(c) for c in grid.components(portals)]
                    signature = hashlib.sha256(wire(sorted(grid.xy(u) for u in unknown)).encode()).hexdigest()
                    candidates.append({"tile": tile, "cells": unknown,
                        "portal_cells": representatives, "portal_members": portals,
                        "signature": signature})
        old_live = {k: v for k, v in self.items.items() if v["state"] != "completed"}
        used, current = set(), {}
        for candidate in sorted(candidates, key=lambda c: (c["tile"], min(c["cells"]), c["portal_cells"])):
            # Same unknown CC can touch disconnected free CCs: require portal overlap.
            overlaps = [(len(v["cells"] & candidate["cells"]), key)
                        for key, v in old_live.items() if v["tile"] == candidate["tile"]
                        and v["portal_members"] & candidate["portal_members"]
                        and v["cells"] & candidate["cells"]]
            available = sorted((n, k) for n, k in overlaps if k not in used)
            if available:
                key = max(available)[1]
            else:
                self.counter += 1
                key = str(self.counter)
            used.add(key)
            lineage = {k for _, k in overlaps if k != key}
            for _, previous_key in overlaps:
                lineage.update(self.items[previous_key].get("parents", []))
            # Reopened observed space is a new task with explicit ancestry,
            # rather than silently resurrecting a completed task revision.
            lineage.update(k for k, v in self.items.items() if v["state"] == "completed"
                           and v["tile"] == candidate["tile"] and v["cells"] & candidate["cells"])
            parents = sorted(lineage - {key})
            current[key] = dict(candidate, state="pending", map_rev=self.map_rev,
                                parents=parents, observation="frontier_present")
        for key, old in self.items.items():
            if key in current:
                continue
            # Missing candidates or out-of-window data do NOT prove completion.
            observed = all(grid.state(u) in (0, 100) for u in old["cells"])
            done = old["state"] == "completed" or observed
            current[key] = dict(old, state="completed" if done else "deferred",
                map_rev=self.map_rev, observation="all_previous_unknown_observed" if observed else old["observation"])
        self.items = current
        return current
