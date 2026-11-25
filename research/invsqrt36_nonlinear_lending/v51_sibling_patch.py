"""Generate V51 optimized emitter from pinned PR116 archive source.
Run: python v51_sibling_patch.py /path/to/PR116/v49_phase_adjoint.py /path/to/PR116/v51_phase_adjoint.py
Then run generated source with v49_joint_spectral_plan.json (60 blocks).
The archived verifier re-reads the serialized circuit and checks every control mask.
"""
from pathlib import Path
import sys
def transform(s):
    changes=[
    ("""   cur=1<<pivot
   for s,a in sorted(group,key=lambda z:gray_index(z[0]^(1<<pivot))):""",
     """   cur=1<<pivot
   if flag is not None:op(33,flag,pivot)
   for s,a in sorted(group,key=lambda z:gray_index(z[0]^(1<<pivot))):"""),
    ("""    if flag is not None:op(33,flag,pivot)
    rot(pivot,a,[b,s])
    if flag is not None:op(33,flag,pivot)
   d=cur^(1<<pivot)
   while d:q=(d&-d).bit_length()-1;op(33,q,pivot);d&=d-1""",
     """    rot(pivot,a,[b,s])
   d=cur^(1<<pivot)
   while d:q=(d&-d).bit_length()-1;op(33,q,pivot);d&=d-1
   if flag is not None:op(33,flag,pivot)"""),
    ("""  for bit in (0,1):
   if bit not in node:continue
   q=21-depth;t=22+depth;s=len(ops)
   if not bit:op(17,q)
   if depth:op(49,21+depth,q,t)
   else:op(33,q,t)
   if not bit:op(17,q)
   pre=ops[s:];visit(node[bit],depth+1);ops.extend(pre[::-1])""",
     """  children=[bit for bit in (0,1)if bit in node]
  if not children:return
  q=21-depth;t=22+depth
  def toggle(bit):
   if not bit:op(17,q)
   if depth:op(49,21+depth,q,t)
   else:op(33,q,t)
   if not bit:op(17,q)
  first=children[0];toggle(first);visit(node[first],depth+1)
  if len(children)==2:
   if depth:op(33,21+depth,t)
   else:op(17,t)
   visit(node[children[1]],depth+1);toggle(children[1])
  else:toggle(first)"""),
    ("""   for bit in (0,1):
    if bit not in nd:continue
    q=10-d;t=23+d;beg=len(ops)
    if not bit:op(17,q)
    op(49,22+d,q,t)
    if not bit:op(17,q)
    pre=ops[beg:];deep_visit(nd[bit],d+1);ops.extend(pre[::-1])""",
     """   children=[bit for bit in (0,1)if bit in nd]
   if not children:return
   q=10-d;t=23+d
   def toggle(bit):
    if not bit:op(17,q)
    op(49,22+d,q,t)
    if not bit:op(17,q)
   first=children[0];toggle(first);deep_visit(nd[first],d+1)
   if len(children)==2:
    op(33,22+d,t);deep_visit(nd[children[1]],d+1);toggle(children[1])
   else:toggle(first)""")]
    for old,new in changes:
        assert s.count(old)==1, "incompatible source"
        s=s.replace(old,new)
    return s

if __name__=="__main__":
    Path(sys.argv[2]).write_text(transform(Path(sys.argv[1]).read_text()))
