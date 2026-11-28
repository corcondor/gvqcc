#!/usr/bin/env python3
"""Native full raw-S research build: #274 shell + #237 rank15 + #241 guard4
+ #308/#310 public-mask adjoint. No syndrome-dependent host dispatch.
The existing raw-key shell has known errors; fail closed on all tests.
"""
import argparse, hashlib, inspect, json, sys
from pathlib import Path
from functools import lru_cache
import kickmix as km
sys.path.insert(0, '/tmp/seam')
sys.path.insert(0, '/tmp/public266/generators/dqi/src/team')
import core_direct_unit as B
import crt882 as C, joint_phase as J, general_scan as G
import joint_rank15 as R, guard4 as H

ANCHORS = frozenset(range(70))
C.Compact = R.Rank15
H.check_truth()
TRACE = tuple(C.xor_word(C.gf_pow(x, 1 << i, 12, C.MOD)
                         for i in range(12)) for x in range(4096))
assert set(TRACE) == {0, 1}
raw = [sum(TRACE[C.m(x, 1 << i)] << i for i in range(12))
       for x in range(4096)]
assert len(set(raw)) == 4096
dual = [raw.index(1 << i) for i in range(12)]

@lru_cache(None)
def phase_columns(z, half):
    weight = C.xor_word(C.BASIS12[6*half+i] for i in C.bits(z))
    return tuple(C.m(1<<i, weight) for i in range(12))

def phase_half(b,a,y,p,mask,half,w):
    """Pull the linear functional of p through the GF64 rank-15 tensor.
    Only 1 borrowed clean qubit, no 6- or 12-bit inverse output.
    Every classical coefficient depends on public mask alone.
    """
    cb=b.alloc_bits(1)[0]
    for l,s,z in R.terms:
        x=G.parity_pivot(b,a,l); v=G.parity_pivot(b,y,s)
        columns=phase_columns(z,half)
        def contract():
            for i,col in enumerate(columns):
                b.bit_store(cb,False)
                for j in C.bits(col): b.cx(mask[j],cb)
                b.ccx(p[i],cb,w)
        contract()
        b.ccz(x[0],v[0],w)
        contract()
        G.unpivot(b,v);G.unpivot(b,x)
    b.bit_store(cb,False);b.free(cb)

def kernel(b,f,d,p,work,mask):
    assert len(work)==33 and len(set(f+d+p+work))==69
    chain,n,nn,gw,y=work[:11],work[11:17],work[17:20],work[20:26],work[26:32]
    w=work[32]
    G.root(b,f,chain); r=chain[-1]
    J.frame(b,d,C.BASIS12,True); a,c=d[:6],d[6:]
    J.norm_compute(b,a,c,n,6,C.K6,C.F6MOD)
    J.frame(b,n,C.BASIS6,True); u,v=n[:3],n[3:]
    J.norm_compute(b,u,v,nn,3,C.K3,C.F3MOD)
    hg=H.guard4(b,nn,r,gw)
    J.xor(b,v,u);J.arith(b,'prod',u,hg,y[:3],3,C.F3MOD);J.xor(b,v,u)
    J.arith(b,'prod',v,hg,y[3:],3,C.F3MOD)
    J.frame(b,y,C.BASIS6)
    J.xor(b,c,a);phase_half(b,a,y,p,mask,0,w);J.xor(b,c,a)
    phase_half(b,c,y,p,mask,1,w)
    J.frame(b,y,C.BASIS6,True)
    J.xor(b,v,u);J.product_clear(b,u,hg,y[:3],3,C.F3MOD);J.xor(b,v,u)
    J.product_clear(b,v,hg,y[3:],3,C.F3MOD)
    H.unguard4(b,nn,r,gw)
    J.norm_clear(b,u,v,nn,3,C.K3,C.F3MOD)
    J.frame(b,n,C.BASIS6)
    J.norm_clear(b,a,c,n,6,C.K6,C.F6MOD)
    J.frame(b,d,C.BASIS12)
    G.unroot(b,f,chain)

def anchor_gauge(b,S,E):
    """R(alpha^j)=traceDual(E_j)/alpha^j for 70 fixed public anchors.
    Add Tr(sum_j R_j S_j) BEFORE modifying the raw syndrome.
    """
    xs=[C.exp[j] for j in sorted(ANCHORS)]
    rw=[list(b.alloc_bits(12)) for _ in xs]
    for word in rw:
        for bit in word:b.bit_store(bit,False)
    for i,x in enumerate(xs):
        poly=[1]
        for j,y in enumerate(xs):
            if i!=j:poly=C.mul(poly,[y,1])
        scale=C.inv(C.m(x,C.evalp(poly,x)))
        for j,coef in enumerate(poly):
            coef=C.m(coef,scale)
            for t in range(12):
                for k in C.bits(C.m(coef,dual[t])):b.cx(E[i][t],rw[j][k])
    for s,word in zip(S,rw):
        for i,q in enumerate(s):
            for j,bit in enumerate(word):
                if TRACE[C.m(1<<i,1<<j)]:b.cz(q,bit)
    return rw

def residue_mask(b,rx,x,c,mask):
    # rx carries R(x) in the same FFT frame, no syndrome-derived classical input.
    for i in range(12):
        weight=C.m(x,C.m(c,C.m(1<<i,1<<i)))
        for j,bit in enumerate(rx):
            if TRACE[C.m(weight,1<<j)]:b.cx(bit,mask[i])

def configure_fft():
    # Patch only the exact old #266 source at asserted unique boundaries.
    # Its existing additive FFT also evaluates the classical 70-coefficient R
    # in place, rather than constructing a separate large residual table.
    s=inspect.getsource(B.fft)
    changes=[
      ('def fft(b,D,N,E):','def fft(b,D,N,E,R):'),
      (' L=[0,1];S=[];NB=[[1]]',' words.append(R)\n L=[0,1];S=[];NB=[[1]]'),
      ('range(1,18):','range(1,70):'),
      ('b.alloc_qubits(35)','b.alloc_qubits(33)'),
      ('if not x:return','if not x or C.log[x] in ANCHORS:return'),
      ('  kernel(b,A,B,P,work,mask)','  residue_mask(b,R[0],x,c,mask)\n  kernel(b,A,B,P,work,mask)'),
      ('dfs(12,0,17);assert count==4095','dfs(12,0,69);assert count==4025'),
      (' for a in words:basis(a,True)',' for a in words:basis(a,True)\n words.pop()'),
    ]
    for old,new in changes:
        assert s.count(old)==1,(old,s.count(old))
        s=s.replace(old,new)
    B.__dict__.update(ANCHORS=ANCHORS,residue_mask=residue_mask,kernel=kernel)
    exec(compile(s,'<pinned-fft-adjoint>','exec'),B.__dict__)

def check_leaf():
    """Independent exact coefficient check, full 4096 denominators and both guards.
    All 12x12 phase coefficients; no probability-based inference.
    """
    def parity(x):return x.bit_count()&1
    tw={C.xor_word(v for i,v in enumerate(C.BASIS12) if a>>i&1):a
        for a in range(4096)}
    t6={C.xor_word(v for i,v in enumerate(C.BASIS6) if a>>i&1):a
        for a in range(64)}
    mul6=lambda a,b:C.gf_mul(a,b,6,C.F6MOD)
    mul3=lambda a,b:C.gf_mul(a,b,3,C.F3MOD)
    for i in range(6):
        for j in range(6):
            assert C.xor_word(z for l,s,z in R.terms if l>>i&1 and s>>j&1)==mul6(1<<i,1<<j)
    for d in range(4096):
        a,c=tw[d]&63,tw[d]>>6
        n=mul6(a,a)^mul6(a,c)^mul6(C.K6,mul6(c,c))
        u,v=t6[n]&7,t6[n]>>3
        nn=mul3(u,u)^mul3(u,v)^mul3(C.K3,mul3(v,v))
        for g in (0,1):
            h=C.gf_pow(nn,6,3,C.F3MOD) if g else 0
            yp=mul3(u^v,h)|(mul3(v,h)<<3)
            y=C.xor_word(z for j,z in enumerate(C.BASIS6) if yp>>j&1)
            target=C.gf_pow(d,4094,12,C.MOD) if g else 0
            for i in range(12):
                v0=C.xor_word(phase_columns(z,0)[i] for l,s,z in R.terms
                              if parity((a^c)&l) and parity(y&s))
                v1=C.xor_word(phase_columns(z,1)[i] for l,s,z in R.terms
                              if parity(c&l) and parity(y&s))
                assert v0^v1==C.m(1<<i,target),(d,g,i)
    print(json.dumps(dict(denominator_guard_cases=8192,
        phase_binary_coefficients=1179648,rank15_basis_checks=36,
        guard4_cases=16,phase_word_mismatches=0,
        predicted_leaf_paid=78,leaf_scratch=33)),flush=True)

def native_leaf_test():
    b=km.CircuitBuilder();b.set_max_qubits(69)
    f=list(b.create_quantum_register(12,'f'));d=list(b.create_quantum_register(12,'d'))
    p=list(b.create_quantum_register(12,'p'));m=list(b.create_classical_register(12,'m'))
    work=list(b.alloc_qubits(33));kernel(b,f,d,p,work,m);b.free(km.array(work))
    circ=b.finish_circuit()
    import numpy as np
    rng=np.random.default_rng(310312)
    q=km.array(f+d+p);bitsm=km.array(m);anc=km.array([km.q(i) for i in range(36,circ.num_qubits)])
    errors=np.zeros(4,dtype=np.int64);shots=0;paid=0
    def bits(z):return (((z[:,:,None]>>np.arange(12))&1).reshape(len(z),-1).T).astype(bool)
    for g in (0,1):
      for st in range(0,4096,256):
        den=np.arange(st,st+256,dtype=np.int64)
        f0=np.zeros(256,dtype=np.int64) if g else rng.integers(1,4096,256)
        pp=rng.integers(0,4096,256);mm=rng.integers(0,4096,256)
        A=bits(np.stack((f0,den,pp),axis=1));M=bits(mm[:,None])
        truth=np.array([bool((C.m(int(a),C.gf_pow(int(d0),4094,12,C.MOD))&int(m0)).bit_count()&1) if g else False for a,d0,m0 in zip(pp,den,mm)])
        for seed in (11,97):
          s=km.Simulator(batch_size=256,seed=seed+st,debug_print=False,counting_operations=True);s.use_same_registers_as(circ)
          s.write_across_shots(q,A);s.write_across_shots(bitsm,M);s.do(circ)
          errors+=np.array([(s.read_across_shots(q)!=A).any(0),(s.read_across_shots(bitsm)!=M).any(0),s.read_across_shots(anc).any(0),s.read_phase_flipped_across_shots()!=truth]).sum(1)
          shots+=256;paid+=int(s.operation_statistics().num_toffoli_like)
    result=dict(shots=shots,errors=errors.tolist(),q=circ.num_qubits,static_paid=int(circ.operation_statistics().num_toffoli_like),mean_paid=paid/shots)
    print('NATIVE_LEAF',json.dumps(result),flush=True)
    assert not errors.any() and result['static_paid']==78 and result['q']<=69

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--shell',action='store_true');ap.add_argument('--guarded-synthesis',action='store_true')
    args=ap.parse_args()
    check_leaf();native_leaf_test()
    if args.guarded_synthesis:
        # Diagnostic only: this does NOT fix a nonzero old target when source is zero.
        syn=B.Pipeline.P.Synthesis
        old=syn.emit_prefix
        def guarded(*a,**k):
            k['guarded']=True
            return old(*a,**k)
        syn.emit_prefix=guarded
    configure_fft()
    b=km.CircuitBuilder();b.set_max_qubits(900)
    S=[b.create_quantum_register(12,f'S{i}') for i in range(70)]
    E=[b.create_classical_register(12,f'E{i}') for i in range(4095)]
    gauge=None if args.shell else anchor_gauge(b,S,E)
    key=B.Pipeline.emit_key_prefix(b,S,j_min=0,stage=lambda x:None)
    D,N=[list(x) for x in key['D']],[list(x) for x in key['N']]
    assert len(D)==36 and len(N)==35
    if not args.shell:
        B.fft(b,D,N,E,gauge)
        for word in gauge:J.cclear(b,word)
    B.Pipeline.emit_key_closing(b,key,stage=lambda x:None)
    assert b.num_allocated_qubits==840
    circ=b.finish_circuit();args.output.parent.mkdir(parents=True,exist_ok=True);circ.to_file(str(args.output),format='kmb')
    receipt=dict(scope='full raw-S circuit, not certified submission',shell=args.shell,guarded_synthesis=args.guarded_synthesis,q=circ.num_qubits,ops=len(circ),static_paid=int(circ.operation_statistics().num_toffoli_like),sha256=hashlib.file_digest(args.output.open('rb'),'sha256').hexdigest())
    assert receipt['q']<=900
    args.output.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('BUILT',json.dumps(receipt),flush=True)
if __name__=='__main__':main()
