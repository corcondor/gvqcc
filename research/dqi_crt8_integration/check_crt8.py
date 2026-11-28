"""Generate a Lean certificate for both GF(8)-CRT decompositions against PR #311."""
import base64,zlib
from pathlib import Path
D=Path(__file__).parent
def decode(p,n):
    raw=zlib.decompress(base64.b64decode(p.read_text()))
    assert len(raw)==891*n
    nums=[int.from_bytes(raw[i:i+3],'little') for i in range(0,len(raw),3)]
    return [list(zip(nums[i:i+297:3],nums[i+1:i+297:3],nums[i+2:i+297:3])) for i in range(0,len(nums),297)]
O=decode(D.parent/'dqi_rank99_crt'/'terms.b64',4)
N=decode(D/'terms8.b64',2)
T=[O[0],N[0],O[2],N[1]]
def coeff(ts,i,j):
    c=0
    for a,b,d in ts:
        if (a>>i)&(b>>j)&1:c^=d
    return c
assert all(len(t)==99 and all(0<x<2**24 for term in t for x in term) for t in T)
for k in (0,2):
    assert all(coeff(T[k],i,j)==coeff(T[k+1],i,j) for i in range(24) for j in range(24))
s=['import Std','set_option maxRecDepth 100000','set_option maxHeartbeats 0','namespace GVQCC.CRT8Concrete',
'def coeff (ts : List (Nat × Nat × Nat)) (i j : Nat) : Nat := ts.foldl (fun acc t => if t.1.testBit i && t.2.1.testBit j then Nat.xor acc t.2.2 else acc) 0',
'def row (ts : List (Nat × Nat × Nat)) (i : Nat) : List Nat := (List.range 24).map (coeff ts i)']
for k,t in enumerate(T):
    s.append('def t%d : List (Nat × Nat × Nat) := [%s]'%(k,','.join(f'({a},{b},{c})' for a,b,c in t)))
for k in (0,2):
    for i in range(24):
        name=f'crt8_{k}_{i}'
        s.extend([f'theorem {name} : row t{k} {i} = row t{k+1} {i} := by decide',f'#print axioms {name}'])
s.extend([
'theorem product_shear (a b : Bool) : (xor a b && b) = xor (a && b) b := by cases a <;> cases b <;> decide',
'#print axioms product_shear',
'theorem affine_delta (x y p a b : Bool) : xor (xor x (p && a)) (xor y (p && b)) = xor (xor x y) (p && xor a b) := by cases x <;> cases y <;> cases p <;> cases a <;> cases b <;> decide',
'#print axioms affine_delta',
'theorem two_observer_debt (p a b m n : Bool) : xor (m && xor a p) (n && xor b p) = xor (xor (m && a) (n && b)) (p && xor m n) := by cases p <;> cases a <;> cases b <;> cases m <;> cases n <;> decide',
'#print axioms two_observer_debt',
'theorem guarded_debt (g p m n : Bool) : xor (g && p && m) (g && p && n) = (g && p && xor m n) := by cases g <;> cases p <;> cases m <;> cases n <;> decide',
'#print axioms guarded_debt',
'theorem dirty_echo (x y t : Bool) : xor (xor t (x && y)) (x && y) = t := by cases x <;> cases y <;> cases t <;> decide',
'#print axioms dirty_echo','end GVQCC.CRT8Concrete'])
Path('CRT8Concrete.lean').write_text('\n'.join(s)+'\n')
print('1152 basis coefficient checks; generate 53 declarations')
