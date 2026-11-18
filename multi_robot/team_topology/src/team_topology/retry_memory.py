"""Robot-local failed ingress memory, independent of changing task IDs.

This rejects temporary execution attempts, never marks unknown space observed.
Other robots may still bid; old-owner STOP proof is enforced elsewhere.
"""
import math

def ingress(path):
    if not path:return None
    origin=tuple(path[0][:2]);distance=0.;previous=origin;target=origin
    for p in path[1:]:
        p=tuple(p[:2]);step=math.dist(previous,p)
        if distance+step>=1.5:
            t=(1.5-distance)/max(step,1e-9);target=tuple(a+t*(b-a) for a,b in zip(previous,p));break
        distance+=step;previous=target=p
    d=math.dist(origin,target)
    return origin,None if d<.1 else tuple((b-a)/d for a,b in zip(origin,target))

class RetryMemory:
    def __init__(self):self.entries={}

    def fail(self,robot,command,now,unsafe_start=False,before_execution=False):
        route=ingress(command.get('path',[]))
        if route is None:return
        origin,direction=route;items=self.entries.setdefault(robot,[])
        # Modest drift or a newly named remote frontier cannot evade this gate.
        match=next((e for e in items if math.dist(e['origin'],origin)<.75 and
            (unsafe_start or e['unsafe_start'] or e['direction'] is None or direction is None or sum(a*b for a,b in zip(e['direction'],direction))>.7)),None)
        attempts=(match['attempts']+1) if match and now-match['last']<120 else 1
        # A dispatch without an executor certificate has not tested physical
        # ingress. Keep bounded alias-shared retry, preserving recent physical
        # failures and their conservative cooldown.
        recent_physical=match is not None and not match.get('before_execution') and now-match['last']<120.
        prestart=before_execution and not unsafe_start and not recent_physical
        if before_execution and not unsafe_start and recent_physical and now<match['until']:
            return
        delay=(4.,8.,16.,30.)[min(attempts,4)-1] if prestart else min(60.,15.*attempts)
        value=dict(origin=origin,direction=direction,unsafe_start=unsafe_start,attempts=attempts,
                   before_execution=prestart,last=now,until=now+delay)
        if match:items.remove(match)
        items.append(value);self.entries[robot]=items[-16:]

    def blocked(self,robot,path,now):
        route=ingress(path)
        if route is None:return False
        origin,direction=route
        return any(now<e['until'] and math.dist(e['origin'],origin)<.75 and
            (e['unsafe_start'] or e['direction'] is None or direction is None or sum(a*b for a,b in zip(e['direction'],direction))>.7)
            for e in self.entries.get(robot,[]))
