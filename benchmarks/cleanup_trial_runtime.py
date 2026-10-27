"""Terminate only processes whose command/env identifies this exact result directory."""
import json
import os
import signal
import socket
import time
from pathlib import Path

def cleanup_owned_runtime(out):
    owned=[]
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit() or int(directory.name)==os.getpid(): continue
        try:
            command=directory.joinpath('cmdline').read_bytes()
            environment=directory.joinpath('environ').read_bytes().split(b'\0')
            if str(out).encode() not in command and ('ROS_LOG_DIR='+str(out/'ros')).encode() not in environment: continue
            owned.append({'pid':int(directory.name),'command':command.replace(b'\0',b' ').decode(errors='replace'),
                'start_ticks':directory.joinpath('stat').read_text().split()[21]})
        except (OSError,IndexError): continue
    def still_same(process):
        try:return Path('/proc',str(process['pid']),'stat').read_text().split()[21]==process['start_ticks']
        except (OSError,IndexError):return False
    for signum in (signal.SIGINT,signal.SIGTERM,signal.SIGKILL):
        for process in owned:
            if still_same(process):
                try:os.kill(process['pid'],signum)
                except ProcessLookupError:pass
        deadline=time.monotonic()+3
        while time.monotonic()<deadline and any(still_same(p) for p in owned):time.sleep(.1)
        if not any(still_same(p) for p in owned):break
    ports={}
    for port in (11311,11345):
        with socket.socket() as connection:ports[str(port)]=connection.connect_ex(('127.0.0.1',port))!=0
    record={'owned_processes':owned,'remaining_owned_pids':[p['pid'] for p in owned if still_same(p)],'ports_free':ports}
    (out/'runtime_cleanup.json').write_text(json.dumps(record,indent=2)+'\n')
    return all(ports.values())
