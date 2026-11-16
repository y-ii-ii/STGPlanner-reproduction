"""Own-map utilities. Grid data is local-only and never enters GraphDelta."""
import heapq
import math
from .graph import point


class Grid:
    def __init__(self, width, height, resolution, origin, data):
        self.width, self.height = int(width), int(height)
        self.resolution, self.origin = float(resolution), point(origin)
        if self.width <= 0 or self.height <= 0 or self.resolution <= 0 or not math.isfinite(self.resolution):
            raise ValueError("bad grid geometry")
        self.data = tuple(int(v) for v in data)
        if len(self.data) != self.width * self.height:
            raise ValueError("grid size mismatch")
        if any(v not in (-1, 0, 100) for v in self.data):
            raise ValueError("grid states must be -1/0/100")

    def contains(self, u):
        return 0 <= u[0] < self.width and 0 <= u[1] < self.height

    def state(self, u):
        return self.data[u[1] * self.width + u[0]] if self.contains(u) else None

    def xy(self, u):
        return point((self.origin[0] + (u[0] + .5) * self.resolution,
                      self.origin[1] + (u[1] + .5) * self.resolution))

    def cell(self, p):
        return (math.floor((p[0] - self.origin[0]) / self.resolution),
                math.floor((p[1] - self.origin[1]) / self.resolution))

    def neighbors(self, u):
        return [(u[0] + dx, u[1] + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                if self.contains((u[0] + dx, u[1] + dy))]

    def path(self, start, goal):
        # Four-connected known-free A*: no diagonal corner-cutting or unknown jump.
        if self.state(start) != 0 or self.state(goal) != 0:
            return None
        costs, prev, queue = {start: 0}, {}, [(0, 0, start)]
        while queue:
            _, cost, cur = heapq.heappop(queue)
            if cost != costs[cur]:
                continue
            if cur == goal:
                result = [goal]
                while result[-1] != start:
                    result.append(prev[result[-1]])
                return list(reversed(result))
            for nxt in self.neighbors(cur):
                if self.state(nxt) != 0 or cost + 1 >= costs.get(nxt, math.inf):
                    continue
                costs[nxt], prev[nxt] = cost + 1, cur
                heuristic = abs(nxt[0] - goal[0]) + abs(nxt[1] - goal[1])
                heapq.heappush(queue, (cost + 1 + heuristic, cost + 1, nxt))
        return None

    def components(self, cells):
        pending, result = set(cells), []
        while pending:
            seed = min(pending)
            pending.remove(seed)
            component, todo = {seed}, [seed]
            while todo:
                for nxt in self.neighbors(todo.pop()):
                    if nxt in pending:
                        pending.remove(nxt)
                        component.add(nxt)
                        todo.append(nxt)
            result.append(component)
        return result
