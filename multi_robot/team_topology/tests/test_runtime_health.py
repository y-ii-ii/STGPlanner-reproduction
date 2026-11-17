import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'bench'))
from runtime_health import incarnation,ended

class RuntimeHealthTests(unittest.TestCase):
 def fixture(self,root,state='S',start='123'):
  p=root/'17';p.mkdir(exist_ok=True);(p/'stat').write_text('17 (native planner (worker)) '+state+' '+' '.join(['0']*18+[start]))

 def test_live_process_incarnation(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p);self.assertEqual(incarnation(17,p),'123');self.assertEqual(ended({17:'123'},p),[])

 def test_zombie_is_an_exit_even_while_roslaunch_lives(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p,'Z');self.assertEqual(ended({17:'123'},p),[17])

 def test_reused_pid_is_not_the_original_native_node(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);self.fixture(p,start='456');self.assertEqual(ended({17:'123'},p),[17])

 def test_missing_process_fails_closed(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(ended({17:'123'},Path(d)),[17])

if __name__=='__main__':unittest.main()
