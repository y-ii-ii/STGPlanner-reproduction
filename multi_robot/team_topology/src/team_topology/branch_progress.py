"""Robot-local evidence that a viewpoint or a route needs another attempt."""
from collections import defaultdict
import math

from .scope import unknown_support


class BranchProgress:
    def __init__(self):
        self.active = {}
        self.failed = defaultdict(list)
        self.no_progress_stops = 0
        self.excluded_viewpoints = 0

    def blocked(self, robot, portal, support, now):
        return any(now < until and math.dist(portal, old_portal) <= 1.4
                   and support and len(support & old_support) >= .4*min(len(support), len(old_support))
                   for old_portal, old_support, until in self.failed[robot])

    def defer_viewpoint(self, robot, command, now):
        support = unknown_support(command.get('scopes', ()))
        if not support or not command.get('path'):
            return
        # Use geometry as well as observation support so renaming the same
        # frontier cannot immediately send the same robot back to it.
        entries = [entry for entry in self.failed[robot] if entry[2]>now]
        entries.append((tuple(command['path'][-1]), support, now+90.))
        self.failed[robot] = entries[-32:]

    def update(self, robot, command, pose, now, observation_count=0):
        if not command.get('path'):
            return False
        key = command.get('dispatch_id')
        distance = math.dist(pose, command['path'][-1])
        graph_cost=command.get('cost_m',math.inf)
        state = self.active.get(robot)
        if state is None or state['dispatch']!=key or state['portal']!=command.get('portal'):
            self.active[robot] = dict(dispatch=key, portal=command.get('portal'), pose=tuple(pose),
                best=distance,best_cost=graph_cost,observed=observation_count,at=now,travelled=0.)
            return False
        state['travelled'] += math.dist(pose,state['pose'])
        state['pose'] = tuple(pose)
        # Evidence of new observations or a sustained reduction in goal error
        # resets the check. Rolling lease renewals and a loop do not.
        graph_progress=math.isfinite(graph_cost) and graph_cost+.8<state['best_cost']
        if observation_count>state['observed'] or distance+.45<state['best'] or graph_progress:
            state.update(observed=max(observation_count,state['observed']),
                         best=min(distance,state['best']),best_cost=min(graph_cost,state['best_cost']),
                         at=now,travelled=0.)
        near=distance<=3.
        # A detour around an obstacle can increase Euclidean distance while
        # still using up its graph route. Only stop a far loop when the graph
        # cost is available and has failed to improve as well.
        return ((near or math.isfinite(graph_cost))
                and state['travelled']>=(2.4 if near else 5.)
                and now-state['at']>=(12. if near else 18.))
