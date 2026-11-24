#!/usr/bin/env python3
"""Joint reachable-state macro synthesis for public 211T bank8.
Mode A: 1 NEW nonlinear AND + 2 removed CCX + arbitrary free affine repair.
Mode B: 2 NONCOMMUTING new ANDs + 3 removed CCX + affine repair.
The repair transforms ALL 128 wires before the first HMR, so the original
measurement-dependent suffix remains exactly unchanged, including phase.
No score claim unless an actual KMB is emitted and officially verified.
"""
import argparse,base64,hashlib,json,random,zlib,time
from pathlib import Path
import numpy as np
from native_kmb import NativeKMB,Op
N=1219; Q=128; FULL=(1<<(2*N))-1
PIN='227472385bffce8eb08c31ee93d635755901b29107bb32177885e1b7e212f898'
WORDPIN='e17119791be643d66a992bfc7469223546146a86223f1b7e9a9a345b2878d870'
def pack(v,bit):
    return int.from_bytes(np.packbits(((v.astype(np.int64)>>bit)&1).astype(np.uint8),
        bitorder='little').tobytes(),'little')
def input_states(words):
    q=[0]*Q;addr=np.arange(N,dtype=np.int64)
    for i in range(11):
        b=pack(addr,i);q[i]=b|(b<<N)
    for j in range(5):
        for i in range(7):
            old=pack(words[:,35+j],i)
            now=pack(words[:,40+j],i)
            q[11+7*j+i]=old|(now<<N)
    return q
def step(q,o):
    if o.raw==17:q[o.wires[0]]^=FULL
    elif o.raw==33:
        a,t=o.wires;q[t]^=q[a]
    elif o.raw==49:
        a,b,t=o.wires;q[t]^=q[a]&q[b]
    else:raise ValueError('unhandled pre-HMR opcode '+str(o.raw))
def basis(vals):
    rows={}
    for v in vals:
        while v:
            hi=v.bit_length()-1
            if hi not in rows:rows[hi]=v;break
            v^=rows[hi]
    return rows
def mod(v,bs):
    # Full XOR-linear projection: partial reduction is mathematically unsound.
    for k in sorted(bs,reverse=True):
        if (v>>k)&1:v^=bs[k]
    return v
def sim(q,ops,cut,hm,record):
    q=q[:];prods={}
    for idx in range(cut,hm):
        op=ops[idx]
        if idx in record:
            a,b,t=op.wires;prods[idx]=q[a]&q[b]
        step(q,op)
    return q,prods
def influence(ops,hm,tail):
    # Delete effects are linear when no changed wire reaches a later CCX control.
    out=[]
    for idx in tail:
        mask=1<<ops[idx].wires[2];ok=True
        for op in ops[idx+1:hm]:
            if op.raw==33:
                a,t=op.wires
                if mask>>a&1:mask^=1<<t
            elif op.raw==49:
                a,b,t=op.wires
                if (mask>>a&1) or (mask>>b&1):ok=False;break
            elif op.raw!=17:raise ValueError('pre-HMR opcode')
        if ok:out.append((idx,mask))
    return out
def coefficients(vals):
    bs={}
    for i,v in enumerate(vals):
        m=1<<i
        while v:
            k=v.bit_length()-1
            if k not in bs:bs[k]=(v,m);break
            v^=bs[k][0];m^=bs[k][1]
        if not v:return None
    return bs
def represent(v,bs):
    m=0
    while v:
        k=v.bit_length()-1
        if k not in bs:return None
        vv,mm=bs[k];v^=vv;m^=mm
    return m
def repair(src,dest):
    bs=coefficients(src+[FULL])
    if bs is None:return None
    co=[represent(x,bs) for x in dest]
    if any(x is None for x in co):return None
    rows=[x&((1<<Q)-1) for x in co];rev=[]
    for i in range(Q):
        p=next((j for j in range(i,Q) if (rows[j]>>i)&1),None)
        if p is None:return None
        if p!=i:
            rows[i],rows[p]=rows[p],rows[i]
            rev.append(('swap',i,p))
        for j in range(Q):
            if i!=j and (rows[j]>>i)&1:
                rows[j]^=rows[i];rev.append(('cx',i,j))
    seq=[]
    for kind,a,b in reversed(rev):
        if kind=='cx':seq.append(Op(33,(a,b)))
        else:seq.extend([Op(33,(a,b)),Op(33,(b,a)),Op(33,(a,b))])
    seq.extend(Op(17,(j,)) for j,x in enumerate(co) if (x>>Q)&1)
    s=src[:]
    for o in seq:step(s,o)
    assert s==dest
    return seq
def fingerprint(v,quotient,probe):
    r=mod(v,quotient)
    return sum((1<<j) for j,x in enumerate(probe) if (r&x).bit_count()&1)
def signature_difference(src,dst,quotient,probe):
    v=[0]*len(probe)
    for i,(a,b) in enumerate(zip(src,dst)):
        bits=fingerprint(a^b,quotient,probe)
        for j in range(len(probe)):
            if (bits>>j)&1:v[j]^=1<<i
    return tuple(v)
def solve_one(qcut,qref,ops,cut,hm,tail,source_basis,out_basis,probe,
              proposals,seed,outdir,mode,limit_seconds=600):
    rng=random.Random(seed)
    options=[]
    for a in range(Q):
        for b in range(a+1,Q):
            if a<46 and b<46:continue
            f=qcut[a]&qcut[b]
            if f and mod(f,source_basis):options.append((a,b,f))
    rng.shuffle(options)
    safe=influence(ops,hm,tail)
    assert len(safe)>0
    ctl=[17,31,45,12,21,30,35,22,23,34,36,13]
    work=[x for x in range(46,Q)]
    rng.shuffle(work)
    n=0;hits=0;exact=0;trials=0;best=None
    started=time.time()
    for a,b,f in options:
        if n>=proposals or time.time()-started>limit_seconds or best:break
        if mode==1:
            tlist=ctl[:5]+[ctl[(a*7+b)%len(ctl)]]
        else:
            tlist=[ctl[(a*7+b)%len(ctl)]]
        for t in dict.fromkeys(tlist):
            if n>=proposals or best:break
            if t in (a,b):continue
            q1=qcut[:];q1[t]^=f
            if mode==1:family=[(q1,[(a,b,t)])]
            else:
                family=[]
                for u in work[:4]:
                    for dst in ctl[:3]:
                        if len(family)>=12:break
                        if dst in (a,b,t,u):continue
                        g=q1[t]&q1[u]
                        if not g or not mod(g,source_basis):continue
                        q2=q1[:];q2[dst]^=g
                        family.append((q2,[(a,b,t),(t,u,dst)]))
                    if len(family)>=12:break
            for changed,added in family:
                if n>=proposals or best:break
                n+=1
                qnew,prods=sim(changed,ops,cut,hm,set(tail))
                wanted=signature_difference(qref,qnew,out_basis,probe)
                sigs=[]
                for idx,inf in safe:
                    f=fingerprint(prods[idx],out_basis,probe)
                    sigs.append((idx,inf,tuple(inf if (f>>j)&1 else 0
                        for j in range(len(probe)))))
                if mode==1:
                    m={};poss=[]
                    for idx,inf,si in sigs:
                        key=tuple(x^y for x,y in zip(wanted,si))
                        poss.extend([(jj,mi,idx,inf) for jj,mi in m.get(key,[]) if jj<idx])
                        m.setdefault(si,[]).append((idx,inf))
                    trials+=len(sigs)*(len(sigs)-1)//2
                    combos=[[(i,im),(j,jm)] for i,im,j,jm in poss]
                else:
                    m={}
                    for x in range(len(sigs)):
                        i,im,si=sigs[x]
                        for y in range(x+1,len(sigs)):
                            j,jm,sj=sigs[y]
                            key=tuple(v^w for v,w in zip(si,sj))
                            m.setdefault(key,[]).append((i,im,j,jm))
                    combos=[]
                    for k,km,sk in sigs:
                        target=tuple(v^w for v,w in zip(wanted,sk))
                        combos.extend([[(i,im),(j,jm),(k,km)] for i,im,j,jm
                          in m.get(target,[]) if j<k])
                    trials+=len(sigs)*(len(sigs)-1)*(len(sigs)-2)//6
                hits+=len(combos)
                for deletions in combos:
                    qc=qnew[:]
                    for k,inf in deletions:
                        f=prods[k]
                        for j in range(Q):
                            if (inf>>j)&1:qc[j]^=f
                    if any(mod(x,out_basis) for x in qc):continue
                    exact+=1
                    affine=repair(qc,qref)
                    if affine is None:continue
                    qcheck=changed[:];dels=set(k for k,_ in deletions)
                    for j in range(cut,hm):
                        if j not in dels:step(qcheck,ops[j])
                    for op in affine:step(qcheck,op)
                    assert qcheck==qref
                    baseline_circuit=NativeKMB.parse(SOURCE_KMB)
                    prefix=ops[:cut];tail_ops=[op for j,op in enumerate(ops[cut:hm],cut) if j not in dels]
                    baseline_circuit.ops=prefix+[Op(49,x) for x in added]+tail_ops+affine+ops[hm:]
                    raw=baseline_circuit.to_bytes()
                    assert NativeKMB.parse(raw).stats()['T']==210
                    path=outdir/f'bank8_210T_macro{mode}_{seed}.kmb';path.write_bytes(raw)
                    best={'new_gates':added,'removed_ops':sorted(dels),'repair_ops':len(affine),
                          'candidate_sha256':hashlib.sha256(raw).hexdigest(),
                          'full_128_state_equal_before_first_HMR':True,
                          'native_official_verified':False,'path':str(path)}
                    break
                if n%250==0:
                    print('mode',mode,'proposals',n,'combination_trials',trials,
                          'fingerprint_hits',hits,'elapsed',round(time.time()-started,1),flush=True)
    return {'mode':mode,'source_candidate_products':len(options),'tested':n,
      'safe_ccx_deletions':len(safe),'deleted_combinations_screened':trials,
      'fingerprint_hits':hits,'exact_quotient_hits':exact,'best':best,
      'seconds':round(time.time()-started,3)}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--kmb',type=Path,required=True)
    ap.add_argument('--fixture',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--one',type=int,default=3000)
    ap.add_argument('--two',type=int,default=400)
    ap.add_argument('--seed',type=int,default=20261124)
    z=ap.parse_args();z.out.mkdir(parents=True,exist_ok=True)
    global SOURCE_KMB
    SOURCE_KMB=z.kmb.read_bytes()
    assert hashlib.sha256(SOURCE_KMB).hexdigest()==PIN
    j=json.loads(z.fixture.read_text())
    raw=zlib.decompress(base64.b85decode(j['payload']))
    assert hashlib.sha256(raw).hexdigest()==WORDPIN
    words=np.frombuffer(raw[:N*75],dtype=np.uint8).reshape(N,75).astype(np.int64)
    assert words.max()<128
    c=NativeKMB.parse(SOURCE_KMB)
    assert c.stats()['T']==211 and c.stats()['Q']==128
    ops=c.ops
    ccx=[i for i,o in enumerate(ops) if o.raw==49]
    cache=[i for i in ccx if ops[i].wires[2]>=46]
    tail=[i for i in ccx if ops[i].wires[2]<46]
    cut=cache[-1]+1;hm=next(i for i,o in enumerate(ops) if o.raw==80)
    assert len(cache)==82 and len(tail)==129 and tail[-1]<hm
    qcut=input_states(words)
    for o in ops[:cut]:step(qcut,o)
    qend,_=sim(qcut,ops,cut,hm,set(tail))
    b0=basis(qcut+[FULL]);b1=basis(qend+[FULL])
    assert len(b0)==len(b1)==129
    rng=random.Random(z.seed);probes=[rng.getrandbits(2*N) for _ in range(16)]
    out=[]
    for mode,num in [(1,z.one),(2,z.two)]:
        out.append(solve_one(qcut,qend,ops,cut,hm,tail,b0,b1,probes,
                             num,z.seed+mode*29,z.out,mode))
    receipt={'source_kmb_sha256':PIN,'fixture_raw_sha256':WORDPIN,
      'baseline_T':211,'baseline_Q':128,'cache_T':82,'tail_T':129,
      'first_HMR_op_index':hm,'searches':out,
      'achieved_210T':any(x['best'] for x in out),
      'scope':'exhaustive 1219 forward+1219 backward reachable input states before first HMR; all 128 wires exact; original measurement suffix unchanged',
      'scope_warning':'No native KickMix or official contest verifier run; bounds apply only to fixed insert-at-cut and affine-final-repair architectures'}
    (z.out/'receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    print('FINAL',json.dumps(receipt,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
