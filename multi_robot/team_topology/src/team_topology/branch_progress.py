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
        state = self.active.get(robot)
        if state is None or state['dispatch']!=key or state['portal']!=command.get('portal'):
            self.active[robot] = dict(dispatch=key, portal=command.get('portal'), pose=tuple(pose),
                best=distance, observed=observation_count, at=now, travelled=0.)
            return False
        state['travelled'] += math.dist(pose,state['pose'])
        state['pose'] = tuple(pose)
        # Evidence of new observations or a sustained reduction in goal error
        # resets the check. Rolling lease renewals and a loop do not.
        if observation_count>state['observed'] or distance+.45<state['best']:
            state.update(observed=max(observation_count,state['observed']),
                         best=min(distance,state['best']),at=now,travelled=0.)
        return distance<=3.0 and state['travelled']>=2.4 and now-state['at']>=12.
