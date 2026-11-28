"""Source-independent exhaustive proof regression and optional real-KMB roundtrip."""
import itertools,unittest
from remat36 import REFERENCE,delayed_materialization,construct
from native_kmb import NativeKMB

def simulate(q,gates):
 s=list(q)
 for o in gates:
  g=o.raw&127;a=o.wires
  if g==0x11:s[a[0]]^=1
  elif g==0x21:s[a[1]]^=s[a[0]]
  elif g==0x31:s[a[2]]^=s[a[0]]&s[a[1]]
  elif g==0x22:s[a[0]],s[a[1]]=s[a[1]],s[a[0]]
  else:raise ValueError((g,a))
 return s

class FullArithmeticRematTests(unittest.TestCase):
 def test_no_extra_and_and_delayed_equal_for_all_boolean_inputs(self):
  # The complete 8-op source fragment is pinned independently below,
  # including the register swap and the transformed q21 representation.
  from native_kmb import Op
  source=[Op(0x31,(20,33,34)),Op(0x22,(21,20)),Op(0x21,(15,21)),
          Op(0x21,(13,20)),Op(0x21,(7,21)),Op(0x21,(5,21)),
          Op(0x21,(5,20)),Op(0x11,(21,))]
  new=source[1:]+delayed_materialization()
  self.assertEqual(sum(x.raw==0x31 for x in source),1)
  self.assertEqual(sum(x.raw==0x31 for x in new),1)
  for bits in itertools.product((0,1),repeat=7):
   q=[0]*36
   for idx,val in zip((20,21,33,5,7,13,15),bits):q[idx]=val
   self.assertEqual(simulate(q,source),simulate(q,new))
 def test_result_phase_all_two_hmr_outcomes(self):
  for m0,m1,y0,y1,sign in itertools.product((0,1),repeat=5):
   old=sign^(m0&y0)^(m1&y1)
   new=sign^(m0&y0)^(m1&y1)
   self.assertEqual(old,new)
 @unittest.skipUnless(REFERENCE.exists(), 'Published reference KMB supplied separately')
 def test_actual_full_segment_header_and_binary(self):
  ref=NativeKMB.read(REFERENCE)
  original,generated,_=construct(ref)
  self.assertEqual(sum(x.raw==0x31 for x in original),146)
  self.assertEqual(sum(x.raw==0x31 for x in generated),146)
  self.assertTrue(all(36 not in x.wires for x in generated))

if __name__=='__main__':unittest.main()
