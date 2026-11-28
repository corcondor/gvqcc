"""Exact normalized component certificates; not a full DQI verifier."""
import base64, zlib, hashlib, json, random, sys
from pathlib import Path
D=Path(__file__).parent
raw=zlib.decompress(base64.b64decode((D/'terms.b64').read_text()))
assert len(raw)==3564
nums=[int.from_bytes(raw[i:i+3],'little') for i in range(0,len(raw),3)]
T=[list(zip(nums[i:i+297:3],nums[i+1:i+297:3],nums[i+2:i+297:3])) for i in range(0,len(nums),297)]
hashes=['abb443275eef1e59b22de8787495162175dddd7c1b9a2c376d21201532bd5b54','400d0914f7ff7417f923764a15e1fdc9e8e73c5a0902f114b16d0d99e0fef766','8fac98e024f308bf0860f1c17696372fcc7303fe62d9196ed8f7732150e1afa2','d39820360649b8a77d2fcbae0fd79de56622650d36fe625212b0b167ee16071e']
def mul(ts,x,y):
    z=0
    for a,b,c in ts:
        if ((a&x).bit_count()&1) and ((b&y).bit_count()&1):z^=c
    return z
for ts,h in zip(T,hashes):
    assert len(ts)==99 and all(0<x<2**24 for t in ts for x in t)
    assert hashlib.sha256(''.join(f'{a} {b} {c}\n' for a,b,c in ts).encode()).hexdigest()==h
for typ in (0,1):
    assert all(mul(T[2*typ],1<<i,1<<j)==mul(T[2*typ+1],1<<i,1<<j) for i in range(24) for j in range(24))
print('BASIS 1152/1152 exact; 99 terms each')
def lean():
    s=['import Std','set_option maxRecDepth 100000','set_option maxHeartbeats 0','namespace GVQCC.Rank99CRT',
       'def coeff (ts : List (Nat × Nat × Nat)) (i j : Nat) : Nat := ts.foldl (fun acc t => if t.1.testBit i && t.2.1.testBit j then Nat.xor acc t.2.2 else acc) 0',
       'def row (ts : List (Nat × Nat × Nat)) (i : Nat) : List Nat := (List.range 24).map (coeff ts i)']
    for k,ts in enumerate(T):
        s.append('def t%d : List (Nat × Nat × Nat) := [%s]'%(k,','.join(f'({a},{b},{c})' for a,b,c in ts)))
    for t in (0,1):
        for i in range(24):
            n=f'basis_{t}_{i}'
            s.extend([f'theorem {n} : row t{2*t} {i} = row t{2*t+1} {i} := by decide',f'#print axioms {n}'])
    s.extend(['theorem dirty_echo (x y t : Bool) : xor (xor t (x && y)) (x && y) = t := by cases x <;> cases y <;> cases t <;> decide','#print axioms dirty_echo','end GVQCC.Rank99CRT'])
    Path('Rank99Concrete.lean').write_text('\n'.join(s)+'\n')
def native():
    import kickmix as km
    import numpy as np
    def bits(x):return [i for i in range(24) if x>>i&1]
    def build(ts):
        cb=km.CircuitBuilder();cb.set_max_qubits(72);q=list(cb.create_quantum_register(72,'W'))
        for a,b,c in ts:
            A=bits(a);B=[x+24 for x in bits(b)];C=[x+48 for x in bits(c)]
            for S in (A,B):
                for i in S[1:]:cb.cx(q[i],q[S[0]])
            for i in C[1:]:cb.cx(q[C[0]],q[i])
            cb.ccx(q[A[0]],q[B[0]],q[C[0]])
            for i in reversed(C[1:]):cb.cx(q[C[0]],q[i])
            for S in (B,A):
                for i in reversed(S[1:]):cb.cx(q[i],q[S[0]])
        return cb.finish_circuit()
    def bitarray(rows):return ((np.array(rows,np.uint32)[:,:,None]>>np.arange(24,dtype=np.uint32))&1).reshape(len(rows),72).T.astype(bool)
    rng=random.Random(30920261128);receipt=[]
    for k,ts in enumerate(T):
        c=build(ts);p=f'rank99_{k}.kmb';c.to_file(p,format='kmb');c=km.Circuit.from_file(p)
        assert c.num_qubits==72 and int(c.operation_statistics().num_toffoli_like)==99
        ins=[(1<<i,1<<j,rng.randrange(1<<24)) for i in range(24) for j in range(24)]
        ins += [tuple(rng.randrange(1<<24) for _ in range(3)) for _ in range(1024)]
        outs=[(x,y,z^mul(T[k//2*2],x,y)) for x,y,z in ins]
        A=bitarray(ins);B=bitarray(outs);q=km.array([km.q(i) for i in range(72)])
        for seed in (11,97):
            for i in range(0,len(ins),64):
                n=min(64,len(ins)-i);s=km.Simulator(batch_size=n,seed=seed+i,debug_print=False,counting_operations=True);s.use_same_registers_as(c);s.write_across_shots(q,A[:,i:i+n]);s.do(c)
                assert np.array_equal(s.read_across_shots(q),B[:,i:i+n]);assert not np.any(s.read_phase_flipped_across_shots())
                s.do(c);assert np.array_equal(s.read_across_shots(q),A[:,i:i+n]);assert not np.any(s.read_phase_flipped_across_shots())
        r=dict(type=k//2,variant=k%2,Q=c.num_qubits,CCX=99,ops=len(c),shots_forward=2*len(ins),shots_inverse=2*len(ins),errors=0,sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest());print(json.dumps(r),flush=True);receipt.append(r)
    Path('native_receipt.json').write_text(json.dumps(receipt,indent=2))
if '--lean' in sys.argv:lean()
if '--native' in sys.argv:native()
