import subprocess,threading,re
class ContactMonitor:
 def __init__(self,out):
  self.pairs=0;self.ground=0;self.non_ground=[]
  self.proc=subprocess.Popen(['gz','topic','-e','/gazebo/default/physics/contacts'],stdout=subprocess.PIPE,stderr=(out/'contacts.stderr').open('w'),text=True,bufsize=1,start_new_session=True)
  threading.Thread(target=self.read,daemon=True).start()
 def read(self):
  first=None
  for line in self.proc.stdout:
   m=re.search(r'collision1:\s*"([^"]+)"',line)
   if m:first=m.group(1)
   m=re.search(r'collision2:\s*"([^"]+)"',line)
   if m and first:
    pair=[first,m.group(1)];self.pairs+=1
    if any('robot_' in v for v in pair):
     if any('ground_plane' in v for v in pair):self.ground+=1
     elif len(self.non_ground)<100:self.non_ground.append(pair)
    first=None
 def result(self):return dict(contact_pairs=self.pairs,robot_ground_pairs=self.ground,robot_non_ground_pairs=self.non_ground,transport_alive=self.proc.poll() is None)
