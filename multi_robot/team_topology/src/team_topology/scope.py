"""Sparse per-task geometry, not an exchanged occupancy map.

Unknown/portal membership is needed for exact STG candidate filtering. RLE is
bounded to one task component; it does not insert any remote observations into
UFOMap and does not make unknown cells executable.
"""
import math
import hashlib
from .graph import wire


def unknown_support(scopes):
    """Common-world support, independent of heartbeat/map revision or aliases."""
    cells = set()
    for scope in scopes:
        r = float(scope["resolution"])
        x0, y0 = scope["origin"]
        if not all(math.isfinite(v) for v in (r, x0, y0)) or r <= 0:
            raise ValueError("invalid task geometry")
        for y, lo, hi in scope["unknown_runs"]:
            if lo > hi or hi-lo > 100000:
                raise ValueError("invalid task support run")
            for x in range(lo, hi+1):
                cells.add((round((x0+(x+.5)*r)*1e6), round((y0+(y+.5)*r)*1e6)))
                if len(cells) > 100000:
                    raise ValueError("task observation support too large")
    return frozenset(cells)


def completion_signature(scopes):
    support = unknown_support(scopes)
    return hashlib.sha256(wire(sorted(support)).encode()).hexdigest(), len(support)


def runs(cells):
    rows = {}
    for x, y in cells:
        rows.setdefault(y, []).append(x)
    result = []
    for y, xs in sorted(rows.items()):
        start = end = sorted(xs)[0]
        for x in sorted(xs)[1:]:
            if x == end + 1:
                end = x
            else:
                result.append([y, start, end])
                start = end = x
        result.append([y, start, end])
    return result


def task_scope(grid, task):
    return {"origin": list(grid.origin), "resolution": grid.resolution,
            "unknown_runs": runs(task["cells"]),
            "portal_runs": runs(task["portal_members"]),
            "map_rev": task["map_rev"]}


def contains(scope, x, y):
    r = scope["resolution"]
    ix, iy = (math.floor((x-scope["origin"][0])/r),
              math.floor((y-scope["origin"][1])/r))
    return any(y0 == iy and lo <= ix <= hi for y0, lo, hi in
               scope["unknown_runs"] + scope["portal_runs"])
