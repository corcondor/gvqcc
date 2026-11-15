#!/usr/bin/env python3
"""Independent exhaustive checks of symbolic simplification certificates."""
from itertools import product
import json
from pathlib import Path
import subprocess
import tempfile
from test_scratch_audit import write_small_kmb

HERE=Path(__file__).resolve().parent
EXE=Path('/workspace/scratch/3815fb5fae06/score_ancilla_semantic')
def op(code,*qs,bit=None,condition=None):return code,list(qs),bit,condition
cases={
 'linear_uncompute':[op(0x21,0,2),op(0x21,1,2),op(0x21,0,2),op(0x21,1,2),op(0x31,2,0,3)],
 'nonlinear_uncompute':[op(0x31,0,1,2),op(0x31,0,1,2),op(0x31,2,0,3)],
 'restored_controls':[op(0x31,0,1,2),op(0x21,0,1),op(0x21,0,1),op(0x31,0,1,2),op(0x31,2,0,3)],
 'conditional_uncompute':[op(0xa1,0,2,condition=0),op(0xa1,0,2,condition=0),op(0x31,2,0,3)],
 'unknown_conditional_reset':[op(0x21,0,2),op(0x92,2,condition=0),op(0x31,2,1,3)],
 'known_one':[op(0x11,2),op(0x31,2,0,3),op(0x30,2,0,1),op(0x32,2,0,1)],
 'copied_equal_swap':[op(0x21,0,2),op(0x21,0,3),op(0x32,1,2,3)],
 'measurement_mask':[op(0x21,0,2),op(0x50,2,bit=0),op(0x91,3,condition=0),op(0x91,3,condition=0),op(0x31,3,0,2)],
 'nested_condition':[op(0x81,condition=0),op(0x81,condition=1),op(0x21,0,2),op(0x21,0,2),op(0x31,2,0,3),op(0x01),op(0x01)],
}

def check(ops,changes):
 count=0
 measurements=sum((c&127)==0x50 for c,_,_,_ in ops)
 for inputs in product((0,1),repeat=2+2+measurements):
  q=list(inputs[:2])+[0]*2;b=list(inputs[2:4]);outcomes=iter(inputs[4:]);stack=[];effective=1
  for index,(code,qs,bit,condition) in enumerate(ops):
   base=code&127;enabled=effective & (b[condition] if code&128 else 1)
   if code==0x81:stack.append(effective);effective=enabled;continue
   if code==0x01:effective=stack.pop();continue
   if index in changes:
    replacement,reason,*arguments=changes[index]
    if not enabled:pass
    elif replacement==0:
     if base==0x31:assert not(q[qs[0]]&q[qs[1]])
     elif base==0x30:assert not(q[qs[0]]&q[qs[1]]&q[qs[2]])
     elif base==0x32:assert not q[qs[0]] or q[qs[1]]==q[qs[2]]
     else:raise AssertionError(base)
    elif base==0x31:
     control,target=arguments;assert q[qs[0]]&q[qs[1]]==q[control] and target==qs[2]
    elif base==0x30:
     assert q[qs[0]]&q[qs[1]]&q[qs[2]]==q[arguments[0]]&q[arguments[1]]
    elif base==0x32:assert q[qs[0]]==1 and arguments==qs[1:]
    count+=1
   outcome=next(outcomes) if base==0x50 else None
   if not enabled:continue
   if base==0x11:q[qs[0]]^=1
   elif base==0x21:q[qs[1]]^=q[qs[0]]
   elif base==0x31:q[qs[2]]^=q[qs[0]]&q[qs[1]]
   elif base==0x32:
    if q[qs[0]]:q[qs[1]],q[qs[2]]=q[qs[2]],q[qs[1]]
   elif base==0x50:q[qs[0]]=0;b[bit]=outcome
   elif base==0x12:q[qs[0]]=0
   elif base in (0x10,0x20,0x30):pass
   else:raise AssertionError(base)
 return count

def main():
 receipts=[]
 with tempfile.TemporaryDirectory() as tmp:
  tmp=Path(tmp)
  for name,ops in cases.items():
   tape=tmp/(name+'.kmb');changes=tmp/(name+'.tsv')
   write_small_kmb(tape,ops)
   r=subprocess.run([str(EXE),str(tape),'2',str(changes)],capture_output=True,text=True,check=True)
   parsed={}
   for line in changes.read_text().splitlines():
    index,replacement,reason,*args=line.split('\t');parsed[int(index)]=[int(replacement),reason,*map(int,args)]
   assert parsed or name=='unknown_conditional_reset',name
   if name=='unknown_conditional_reset':assert not parsed
   receipts.append(dict(name=name,changes=len(parsed),exhaustive_checks=check(ops,parsed),analysis=json.loads(r.stdout)))
 report=dict(status='PASS',cases=receipts)
 (HERE/'score_ancilla_semantic_check_result.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))

if __name__=='__main__':main()
