"""Source-owned observation certificates, separate from motion ownership.

Static common-world phase: an observation retires information demand only. It
never inserts free/occupied cells or edges into another robot's local map.
"""
import math
from .graph import wire
from .scope import completion_signature,unknown_support


class TeamObservations:
    def __init__(self,support):
        self.support=support;self.geometry={};self.seen=set()
        self.accepted=0;self.rejected=0;self.new_cells=0

    def accept(self,key,task,state):
        try:
            proof=task.get('observation_proof')
            if task.get('state')!='completed' or task.get('observation')!='all_previous_unknown_observed' or not proof:return False
            author=key.split('/task/')[0]
            if (proof.get('schema')!=1 or proof.get('frame')!='world' or proof.get('author')!=author
                    or state.get('author')!=author or proof.get('evidence')!='own_observed_support'):
                raise ValueError('unbound source observation')
            if any(type(proof.get(k)) is not int for k in ('map_rev','required_cells','observed_cells')):
                raise ValueError('nonintegral observation counts')
            stamp=float(proof['stamp']);revision=proof['map_rev'];scope=task['scope']
            if (not math.isfinite(stamp) or stamp<0 or stamp>float(state['stamp'])+1e-6
                    or not 1<=revision<=int(task['map_rev'])<=int(state['map_rev'])):
                raise ValueError('invalid observation epoch')
            # Cache stable geometry, not map_rev/heartbeat metadata. Validate the
            # actual support before trusting a claimed digest or a duplicate ID.
            geometry=wire([scope['origin'],scope['resolution'],scope['unknown_runs']])
            if geometry not in self.geometry:
                digest,count=completion_signature([scope]);cells=unknown_support([scope])
                if not count:raise ValueError('empty observation support')
                self.geometry[geometry]=(digest,cells)
            digest,cells=self.geometry[geometry]
            if (proof['scope_digest']!=digest or int(proof['required_cells'])!=len(cells)
                    or int(proof['observed_cells'])!=len(cells)):
                raise ValueError('partial or mismatched observation support')
            identity=(key,digest)
            if identity in self.seen:return False
            self.seen.add(identity);self.accepted+=1
            before=len(self.support);self.support.update(cells);self.new_cells+=len(self.support)-before
            return True
        except (ValueError,KeyError,TypeError,OverflowError):
            self.rejected+=1;return False

    def stats(self):
        return dict(accepted_certificates=self.accepted,rejected_certificates=self.rejected,
                    novel_author_cells=self.new_cells,world_observed_cells=len(self.support))
