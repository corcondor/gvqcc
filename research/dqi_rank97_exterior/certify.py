"""Exact certificate and native compiler for quadratic mixed-control planes.

No claim that the current 99-term witnesses meet the 97 threshold. All
same-side quadratic terms must vanish and the diagonal correction is emitted.
Only a verified <=97 term candidate can be marked for whole-tape promotion.
"""
import argparse,base64,hashlib,json,random,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def read_original():
    raw=zlib.decompress(base64.b64decode((ROOT/'terms.b64').read_text()))
    assert len(raw)==3564
    n=[int.from_bytes(raw[i:i+3],'little') for i in range(0,len(raw),3)]
    return [[(n[j],n[j+1]<<24,n[j+2]) for j in range(i,i+297,3)] for i in range(0,len(n),297)]
def bits(x):
    while x:
        y=x&-x;yield y.bit_length()-1;x^=y
def anf(terms):
    q={};l=[0]*48
    for a,b,w in terms:
        assert 0<a<1<<48 and 0<b<1<<48 and a!=b and 0<w<1<<24
        for i in bits(a):
            for j in bits(b):
                if i==j:l[i]^=w
                else:
                    k=min(i,j),max(i,j);q[k]=q.get(k,0)^w
    return [q.get((i,j),0) for i in range(48) for j in range(i+1,48)],l
def evaluate(ts,x):
    z=0
    for a,b,w in ts:
        if (a&x).bit_count()%2 and (b&x).bit_count()%2:z^=w
    return z
def verify():
    R=json.loads((ROOT/'mixed_native_terms.json').read_text())
    ans=[]
    for i,(orig,r) in enumerate(zip(read_original(),R,strict=True)):
        new=[(int(a,16),int(b,16),w) for a,b,w in r['bestTerms']]
        q0,l0=anf(orig);q1,l1=anf(new)
        assert len(new)==r['best'] and q0==q1
        fix=[a^b for a,b in zip(l0,l1)]
        assert fix==r['linearCorrection']
        ans.append((orig,new,fix))
        print(json.dumps(dict(variant=i,terms=len(new),mixed=r['mixedBest'],
             quadratic_word_checks=1128,linear_word_checks=48,
             linear_correction_words=sum(bool(x) for x in fix),
             eligible97=len(new)<=97)),flush=True)
    return ans
def linear_frame(a,b):
    # Pick a nonsingular two-column minor. Rows p,q become a,b exactly.
    p,q=next((i,j) for i in range(48) for j in range(48) if i!=j
             and (((a>>i)&1)*((b>>j)&1)^((a>>j)&1)*((b>>i)&1)))
    goal=[1<<i for i in range(48)];goal[p]=a;goal[q]=b
    rows=goal.copy();rev=[]
    def cx(s,t):
        assert s!=t
        rows[t]^=rows[s];rev.append((s,t))
    for i in range(48):
        j=next(j for j in range(i,48) if rows[j]>>i&1)
        if i!=j:cx(i,j);cx(j,i);cx(i,j)
        for j in range(48):
            if j!=i and rows[j]>>i&1:cx(i,j)
    assert rows==[1<<i for i in range(48)]
    ops=rev[::-1];check=[1<<i for i in range(48)]
    for x,y in ops:check[y]^=check[x]
    assert check==goal
    return p,q,ops
def emit(ts,fix):
    import kickmix as km
    cb=km.CircuitBuilder();cb.set_max_qubits(72);q=list(cb.create_quantum_register(72,'W'))
    for a,b,w in ts:
        p,r,frame=linear_frame(a,b)
        for x,y in frame:cb.cx(q[x],q[y])
        z=list(bits(w));t=48+z[0]
        for j in z[1:]:cb.cx(q[t],q[48+j])
        cb.ccx(q[p],q[r],q[t])
        for j in reversed(z[1:]):cb.cx(q[t],q[48+j])
        for x,y in reversed(frame):cb.cx(q[x],q[y])
    for i,w in enumerate(fix):
        for j in bits(w):cb.cx(q[i],q[48+j])
    return cb.finish_circuit()
def native(rows,out):
    import kickmix as km,numpy as np
    rng=random.Random(9720261128);out.mkdir(parents=True,exist_ok=True);receipt=[]
    vals=[0]+[1<<i for i in range(48)]+[(1<<i)|(1<<j) for i in range(48) for j in range(i+1,48)]
    vals += [rng.randrange(1<<48) for _ in range(1024)]
    for i,(orig,ts,fix) in enumerate(rows):
        circ=emit(ts,fix);path=out/f'mixed_{i}.kmb';circ.to_file(str(path),format='kmb')
        c=km.Circuit.from_file(str(path))
        assert c.num_qubits==72 and int(c.operation_statistics().num_toffoli_like)==len(ts)
        q=km.array([km.q(j) for j in range(72)])
        ins=[x|(rng.randrange(1<<24)<<48) for x in vals]
        outs=[v^(evaluate(orig,x)<<48) for v,x in zip(ins,vals)]
        def array(a):return np.array([[(x>>j)&1 for j in range(72)] for x in a],dtype=bool).T.copy()
        A,B=array(ins),array(outs);n=len(ins)
        for seed in (11,97):
            for st in range(0,n,128):
                en=min(n,st+128);s=km.Simulator(batch_size=en-st,seed=seed+st,debug_print=False,counting_operations=True)
                s.use_same_registers_as(c);s.write_across_shots(q,A[:,st:en]);s.do(c)
                assert np.array_equal(s.read_across_shots(q),B[:,st:en])
                assert not np.any(s.read_phase_flipped_across_shots())
                s.do(c)
                assert np.array_equal(s.read_across_shots(q),A[:,st:en])
                assert not np.any(s.read_phase_flipped_across_shots())
        row=dict(variant=i,Q=72,CCX=len(ts),ops=len(c),forward=2*n,inverse=2*n,errors=0,
                 sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        receipt.append(row);print('NATIVE',json.dumps(row),flush=True)
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native',type=Path);p.add_argument('--require97',action='store_true');a=p.parse_args()
    rows=verify()
    if a.require97:
        if any(len(new)>97 for _,new,_ in rows):
            raise SystemExit('REJECT: no <=97 certificate for both algebras; do not splice.')
    if a.native:native(rows,a.native)
