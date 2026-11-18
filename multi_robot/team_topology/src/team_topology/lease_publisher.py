"""Bounded renewal of an already committed contract, not a second allocator.

One mutex orders owner commits and heartbeat publication. A heartbeat cannot
change task/version/dispatch/scope/STOP nonce. It stops renewing motion if the
single authority is unresponsive, mission disabled, or validated sources stale;
the unchanged executor/sensor/permit deadlines still fail closed.
"""
import copy,math,threading
from .graph import wire


class LeasePublisher:
    def __init__(self,publish,owner_timeout=1.2,source_timeout=3.,clocks=None):
        self.publish=publish;self.owner_timeout=owner_timeout;self.source_timeout=source_timeout
        self.clocks=clocks
        self.lock=threading.RLock();self.plans={};self.sources={};self.owner_at=-math.inf;self.enabled=False
        self.sequence=0;self.sent=0;self.bytes=0;self.suppressed=0;self.last_at=None;self.max_gap=0.

    def health(self,sources,now,enabled=True):
        with self.lock:self.sources=dict(sources);self.owner_at=now;self.enabled=enabled

    def commit(self,plans,sources,now,ros_now,enabled=True):
        with self.lock:
            if self.clocks is not None:now,ros_now=self.clocks()
            self.plans=copy.deepcopy(plans);self.health(sources,now,enabled)
            return self._emit(now,ros_now)

    def tick(self,now,ros_now,enabled=True):
        with self.lock:
            # Runtime clocks are sampled AFTER taking the publication lock;
            # a delayed caller cannot renew using its obsolete pre-lock time.
            if self.clocks is not None:now,ros_now=self.clocks()
            if not enabled:self.enabled=False
            return self._emit(now,ros_now)

    def _emit(self,now,ros_now):
        healthy=(self.enabled and now-self.owner_at<=self.owner_timeout
                 and math.isfinite(ros_now) and bool(self.sources)
                 and all(0<=ros_now-stamp<=self.source_timeout for stamp in self.sources.values()))
        commands={r:copy.deepcopy(p) for r,p in self.plans.items() if p.get('mode')=='STOP' or healthy}
        self.suppressed+=sum(p.get('mode')=='ROUTE' for r,p in self.plans.items() if r not in commands)
        if not commands:return commands
        self.sequence+=1
        for r,p in commands.items():
            p.update(command_seq=self.sequence,stamp=ros_now)
            encoded=wire(p);self.publish(r,encoded);self.sent+=1;self.bytes+=len(encoded.encode())+4
        if self.last_at is not None:self.max_gap=max(self.max_gap,now-self.last_at)
        self.last_at=now
        return commands

    def stats(self):
        with self.lock:return dict(commands=self.sent,application_bytes=self.bytes,
                                  suppressed_motion_renewals=self.suppressed,max_publish_gap_s=self.max_gap)
