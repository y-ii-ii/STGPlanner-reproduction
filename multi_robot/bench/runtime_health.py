"""Watch original process incarnations even when roslaunch itself stays alive."""
from pathlib import Path

def incarnation(pid,proc=Path('/proc')):
    try:
        text=(proc/str(pid)/'stat').read_text();fields=text[text.rfind(')')+2:].split()
        return None if fields[0] in ('Z','X') else fields[19] # field 22: starttime
    except (OSError,IndexError):return None

def ended(expected,proc=Path('/proc')):
    return [pid for pid,born in expected.items() if born is None or incarnation(pid,proc)!=born]


def stop_action_snapshot(clients):
    """SUCCEEDED may arrive on /status before the result message."""
    snapshots={}
    pending=False
    for robot,client in clients.items():
        state=client.get_state()
        message=client.get_result() if state==3 else None
        pending |= state in (0,1,6,7) or state==3 and message is None
        snapshots[robot]=(state,message)
    return pending,snapshots
