import json,sys
sys.path.insert(0,'/tmp/seam')
from core_unitzero import Pipeline
from central_schedule import schedule
S=Pipeline.P.Synthesis;M=__import__(S.accumulate_product.__module__,fromlist=['multiplication_tensor'])
terms=tuple(M.multiplication_tensor());tape=schedule(terms,12)
# Lane i*12+j tests input pair (2^i,2^j); remaining 12 lanes test arbitrary target basis.
a=[sum(1<<(i*12+j) for j in range(12)) for i in range(12)]
b=[sum(1<<(i*12+j) for i in range(12)) for j in range(12)]
z=[1<<(144+i) for i in range(12)]
def gf(x,y):
 r=0
 for i in range(12):
  if y>>i&1:r^=x
  x<<=1
  if x&4096:x^=0x1053
 return r
expected=[z[k]^sum(1<<(i*12+j) for i in range(12) for j in range(12) if gf(1<<i,1<<j)>>k&1) for k in range(12)]
for i in range(12):
 for j in range(12):assert M.tensor_value(terms,1<<i,1<<j)==gf(1<<i,1<<j)
with open('/tmp/seam/schedule_certificate.json','w') as f:json.dump(dict(terms=terms,tape=tape),f)
ops=[]
for op,k,i,j in tape:
 if op==0:ops.append(f'(false,{12*k+i},{12*k+j},0)')
 else:ops.append(f'(true,{k},{12+i},{24+j})')
# Split into chunks to reduce elaborator recursion; use a single 156-lane symbolic execution.
src='''import Init
import Std
namespace GVQCC.CentralTensor
abbrev Lane := BitVec 156
abbrev Gate := Bool Ã Nat Ã Nat Ã Nat
def step (s : Array Lane) (g : Gate) : Array Lane :=
  let (cc,a,b,t) := g
  if cc then s.set! t (s[t]! ^^^ (s[a]! &&& s[b]!))
  else s.set! b (s[b]! ^^^ s[a]!)
'''
for n in range(0,len(ops),50):src+=f'def tape{n//50} : List Gate := [\n  '+',\n  '.join(ops[n:n+50])+'\n]\n'
src+='def tape : List Gate := '+ ' ++ '.join('tape'+str(n//50) for n in range(0,len(ops),50))+'\n'
for name,arr in [('initial',a+b+z),('expected',a+b+expected)]:
 src+=f'def {name} : Array Lane := #['+', '.join(f'({x} : Lane)' for x in arr)+']\n'
src+='''set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
theorem exact_basis : tape.foldl step initial = expected := by decide
theorem exact_count : tape.length = '''+str(len(ops))+''' := by decide
#print axioms exact_basis
#print axioms exact_count
end GVQCC.CentralTensor
'''
open('/tmp/seam/CentralTensor.lean','w').write(src)

