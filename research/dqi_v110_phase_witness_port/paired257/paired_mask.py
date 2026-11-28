"""Fixed-syndrome mask counterfactuals with an independent algebra oracle."""
import argparse, collections, hashlib, json, struct, zipfile
from pathlib import Path
import numpy as np
import kickmix as km
import verify_submission_dqi as V

SPEC=V.ProblemSpecDQI.benchmark_instance(num_shots=102400)
TABLE=V.FieldTables(km.GF2Field(12))
EXP=np.array(TABLE.antilog,dtype=np.int32)
LOG=np.array(TABLE.log,dtype=np.int32)
PAR=np.array([v.bit_count()%2 for v in range(4096)],dtype=np.uint8)
PIN='81081a88c27b708322f0724a09197814a18646a4a9969984ab9cf76a6e6cd7fa'

def mul(a,b):
    if not a or not b:return 0
    return int(EXP[(LOG[a]+LOG[b])%4095])

def inv(a):
    assert a
    return int(EXP[-LOG[a]%4095])

def vm(a,b):
    return np.where((a!=0)&(b!=0),EXP[(LOG[a]+LOG[b])%4095],0)

def bm(s):
    c,b=[1],[1]
    l,k,e=0,1,1
    for i,u in enumerate(map(int,s)):
        d=u
        for j in range(1,min(len(c),l+1)):
            d^=mul(c[j],int(s[i-j]))
        if not d:k+=1;continue
        old=c[:]
        z=mul(d,inv(e))
        c.extend([0]*max(0,k+len(b)-len(c)))
        for j,v in enumerate(b):c[k+j]^=mul(z,v)
        if 2*l<=i:l,b,k,e=i+1-l,old,1,d
        else:k+=1
    assert l<=35
    return (c+[0]*(l+1-len(c)))[:l+1][::-1]

def eval_poly(a,x):
    v=0
    for u in reversed(a):v=mul(v,x)^u
    return v

def recover(s):
    d=bm(s); w=len(d)-1
    v=np.zeros(4095,np.int32)
    for t in d[::-1]:v=vm(v,EXP[:4095])^t
    loc=np.flatnonzero(v==0)
    assert len(loc)==w
    n=[0]*w
    for k in range(w):
        for i in range(k+1,w+1):n[k]^=mul(d[i],int(s[i-k-1]))
    deriv=[d[i] if i%2 else 0 for i in range(1,w+1)]
    a=[int(EXP[j]) for j in loc]
    e=[mul(eval_poly(n,x),inv(mul(x,eval_poly(deriv,x)))) for x in a]
    check=moments(loc,np.array(e,np.int32))
    assert all(e) and np.array_equal(s,check)
    return loc,np.array(e,np.int32)

def moments(pos,e):
    return np.bitwise_xor.reduce(EXP[(LOG[e][None,:]+np.arange(1,71)[:,None]*pos[None,:])%4095],axis=1)

def load_archive(path):
    with zipfile.ZipFile(path) as z,z.open('joint_work/audit/saved.bin') as f:
        n=struct.unpack('<I',f.read(4))[0]
        def words(k,lanes):
            x=np.unpackbits(np.frombuffer(f.read(8*k),np.uint8).reshape(k,8),axis=1,bitorder='little')[:,:lanes]
            return x
        for i in range(n):
            m=struct.unpack('<I',f.read(4))[0]
            a=words(840,m).T.reshape(m,70,12)@(1<<np.arange(12))
            mask=words(49140,m).T.reshape(m,4095,12)@(1<<np.arange(12))
            p=words(1,m)[0]
            yield a.astype(np.int32),mask.astype(np.int32),p.astype(bool)

def generated():
    r=np.random.default_rng(416257)
    out=[]
    for w in range(36):
        for k in range(8):
            i=np.sort(r.choice(4095,size=w,replace=False))
            v=r.integers(1,4096,w,dtype=np.int32) if k%2 else np.ones(w,np.int32)
            out.append(moments(i,v))
    rows=np.array(out,np.int32)
    return [(s,None,None) for s in np.array_split(rows,6)]

def dual_encode(r):
    p=0
    for t in r[::-1]:p=vm(p,EXP[:4095])^t
    p=vm(p,EXP[:4095])
    return TRACE[vm(p[:,None],(1<<np.arange(12))[None,:])]@(1<<np.arange(12))

def traces():
    x=np.arange(4096,dtype=np.int32)
    t=x.copy()
    for k in range(11):
        x=vm(x,x);t^=x
    assert set(t)=={0,1}
    return t
TRACE=traces()

def execute(tape,group,raw,tag):
    q,m,a=map(km.array,V.validate_registers(tape,SPEC))
    rng=np.random.default_rng(257108)
    rows=[]
    for batch,(S,arch_mask,arch_phase) in enumerate(raw):
        n=len(S);X=V.to_bits(S,12); supports=[recover(s) for s in S]
        if arch_mask is not None:
            check=[bool(PAR[am[i]&v].sum()%2) for am,(i,v) in zip(arch_mask,supports,strict=True)]
            assert np.array_equal(check,arch_phase)
        C=rng.integers(0,4096,70,dtype=np.int32)
        D=dual_encode(C).astype(np.int32)
        M=arch_mask if arch_mask is not None else rng.integers(0,4096,(n,4095),dtype=np.int32)
        masks=(np.zeros_like(M),np.broadcast_to(D,M.shape),M,M^D)
        expect=[np.array([bool(PAR[am[i]&v].sum()%2) for am,(i,v) in zip(mm,supports,strict=True)])
                for mm in masks]
        shift=(TRACE[vm(S,C[None,:])].sum(1)%2).astype(bool)
        assert np.array_equal(shift,expect[1]) and np.array_equal(expect[3]^expect[2],shift)
        for base in (102362,418356):
            errs=[];phases=[]; residual=[];paid=[]
            for j,mm in enumerate(masks):
                sim=km.Simulator(batch_size=n,seed=base+batch,counting_operations=True,debug_print=False)
                sim.use_same_registers_as(tape)
                Y=V.to_bits(mm,12)
                sim.write_across_shots(q,X);sim.write_across_shots(m,Y);sim.do(tape)
                delta=sim.read_across_shots(q)^X
                h=[hashlib.sha256(np.packbits(z,bitorder='little').tobytes()).hexdigest() for z in delta.T]
                p=sim.read_phase_flipped_across_shots()
                errs.append(np.array([delta.any(0),p^expect[j],
                    sim.read_across_shots(a).any(0),(sim.read_across_shots(m)!=Y).any(0)]))
                residual.append(h);phases.append(p);paid.append(sim.operation_statistics().num_toffoli_like)
            delta=(phases[2]^phases[3])!=shift
            for k,(i,v) in enumerate(supports):
                rows.append(dict(batch=batch,lane=k,seed=base+batch,weight=len(i),
                    arms=[e[:,k].astype(int).tolist() for e in errs],trace_bit=int(shift[k]),m_is_zero=bool(not M[k].any()),
                    delta_wrong=int(delta[k]),same_dense_return=residual[2][k]==residual[3][k],
                    residual_dense=residual[2][k] if errs[2][0,k] else None,
                    residual_translated=residual[3][k] if errs[3][0,k] else None))
            print(tag,batch,base,[e.sum(1).tolist() for e in errs],int(delta.sum()),paid,flush=True)
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('circuit',type=Path)
    ap.add_argument('archive',type=Path)
    ap.add_argument('out',type=Path)
    a=ap.parse_args()
    sha=hashlib.file_digest(a.circuit.open('rb'),'sha256').hexdigest()
    assert sha==PIN
    tape=km.Circuit.from_file(str(a.circuit))
    assert (tape.num_qubits,len(tape),tape.operation_statistics().num_toffoli_like)==(900,69534364,318333)
    for tag,raw in [('saved',load_archive(a.archive)),('synthetic',generated())]:
        rows=execute(tape,tag,raw,tag)
        out=dict(sha=sha,arms=['zero','dual','dense-original','dense-xor-dual'],error_order=['value','phase','dirty','mask'],rows=rows)
        a.out.mkdir(parents=True,exist_ok=True)
        (a.out/f'{tag}.json').write_text(json.dumps(out,separators=(',',':'))+'\n')

if __name__=='__main__':main()
