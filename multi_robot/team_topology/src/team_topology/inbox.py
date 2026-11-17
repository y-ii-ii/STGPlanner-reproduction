"""Callbacks enqueue; one owner mutates graph, task ledger and execution state.

Priority STOP events cannot lose an unfair Python mutex race against continuously
arriving topology updates. No packet is discarded or treated as a stop proof by
this transport queue. Semantic validation remains in GraphStore/Supervisor.
"""
import threading
from collections import deque

class AuthorityInbox:
    CRITICAL=frozenset(('STOPPED','STOP_REQUEST','STOP_REQUIRED','EXECUTOR_REJECTED'))
    def __init__(self):
        self.lock=threading.Lock();self.critical=deque();self.normal=deque();self.topology=deque()
        self.bytes={'feedback_received_bytes':0,'topology_received_bytes':0}
        self.max_depth=0

    def put(self,kind,value,serialized_bytes,now):
        with self.lock:
            self.bytes[kind+'_received_bytes']+=serialized_bytes
            if kind=='topology':self.topology.append((now,value))
            elif value.get('status') in self.CRITICAL:self.critical.append((now,value))
            elif value.get('status')!='TRAFFIC_CAPABILITY':self.normal.append((now,value))
            # Capabilities are consumed by the traffic authority, not this
            # mission authority. Count received bytes, avoid useless state work.
            self.max_depth=max(self.max_depth,len(self.critical)+len(self.normal)+len(self.topology))

    def feedback(self,normal_limit=64):
        with self.lock:
            result=list(self.critical);self.critical.clear()
            for _ in range(min(normal_limit,len(self.normal))):result.append(self.normal.popleft())
            return result

    def packet(self):
        with self.lock:return self.topology.popleft() if self.topology else None

    def stats(self):
        with self.lock:return dict(self.bytes,critical_pending=len(self.critical),normal_pending=len(self.normal),topology_pending=len(self.topology),max_depth=self.max_depth)
