import numpy as np, kickmix as km, json,hashlib,sys,time
from pathlib import Path
import verify_submission_dqi as V
# Explicit, paired 1024 distribution + saved 622 + stratified 144 dense tests.
sp=V.ProblemSpecDQI.benchmark_instance(num_shots=1024);t=V.FieldTables(km.GF2Field(12));rng=np.random.default_rng(202611280834);S,M,P=V.sample_shots(sp,t,rng,1024)
import struct
panels=[]
for i in range(0,1024,64):panels.append(('distribution', V.to_bits(S[i:i+64],12),V.to_bits(M[i:i+64],12),P[i:i+64],202611280834+i))
fpath='saved.bin'
with open(fpath,'rb') as f:
 nb,=struct.unpack('<I',f.read(4))
 for st in range(nb):
  n,=struct.unpack('<I',f.read(4));ar=[]
  for l in (840,49140):ar.append(np.unpackbits(np.frombuffer(f.read(l*8),np.uint8).reshape(l,8),axis=1,bitorder='little')[:,:n].astype(bool))
  x,y=ar;z=np.unpackbits(np.frombuffer(f.read(8),np.uint8),bitorder='little')[:n].astype(bool)
  panels.append(('saved622',x,y,z,64571+st))
import direct_codec as D
rng=np.random.default_rng(202611281527);ss=[];mm=[];pp=[]
for w in range(36):
 for j in range(4):
  e={int(x):int(v) for x,v in zip(rng.choice(np.arange(1,4096),w,replace=False),rng.integers(1,4096,w))};mask=rng.integers(0,4096,4095,dtype=np.uint16)
  ss.append(D.moments(e));mm.append(mask);pp.append(sum((int(v)&int(mask[D.LOG[x]])).bit_count() for x,v in e.items())%2)
ss=np.array(ss);mm=np.array(mm);pp=np.array(pp,bool)
for i in range(0,len(ss),64):panels.append(('dense_weights',V.to_bits(ss[i:i+64],12),V.to_bits(mm[i:i+64],12),pp[i:i+64],801+i))
# Re-batch the exact same input panels; same independent measurement seed per batch
# for parent/candidate. The shot input selection is not changed.
old=panels;panels=[]
for kind in ('distribution','saved622','dense_weights'):
 p=[a for a in old if a[0]==kind]; xx=np.concatenate([a[1] for a in p],axis=1); yy=np.concatenate([a[2] for a in p],axis=1); zz=np.concatenate([a[3] for a in p]);
 for i in range(0,len(zz),256):panels.append((kind,xx[:,i:i+256],yy[:,i:i+256],zz[i:i+256],20261129+i))
from collections import Counter
def bm(xs):
    C=[1]+[0]*len(xs);B=C[:];L=0;m=1;b=1
    for i,a in enumerate(xs):
        d=a
        for j in range(1,L+1):d^=D.mul(C[j],xs[i-j])
        if not d:m+=1;continue
        T=C[:];t=D.div(d,b)
        for j in range(len(xs)+1-m):C[j+m]^=D.mul(t,B[j])
        if 2*L<=i:L=i+1-L;B=T;b=d;m=1
        else:m+=1
    assert all(not np.bitwise_xor.reduce([D.mul(C[j],xs[i-j]) for j in range(L+1)]) for i in range(L,len(xs)))
    return L,C[:L+1]
def gcd(a,b):
    while b:a,b=b,D.divrem(a,b)[1]
    return len(a)-1
def der(a):return D.trim([a[i+1] if i%2==0 else 0 for i in range(len(a)-1)])
def words(x):return x.T.reshape(x.shape[1],70,12)@np.left_shift(1,np.arange(12))
assert len(sys.argv)==2
path=sys.argv[1]; c=km.Circuit.from_file(path); qr,br,ar=map(km.array,V.validate_registers(c,sp)); allout={}
for i,(kind,x,y,z,seed) in enumerate(panels):
 n=x.shape[1];sim=km.Simulator(batch_size=n,seed=seed,debug_print=False,counting_operations=True);sim.use_same_registers_as(c);sim.write_across_shots(qr,x);sim.write_across_shots(br,y);sim.do(c)
 out=np.asarray(sim.read_across_shots(qr)); phase=np.asarray(sim.read_phase_flipped_across_shots())
 g=allout.setdefault(kind,dict(result=Counter(),clusters=Counter(),cases=0))
 for j,(a,b) in enumerate(zip(words(x).tolist(),words(out).tolist())):
    w,_=bm(a);d=[u^v for u,v in zip(a,b)]
    if any(d):
        r,pol=bm(d); repeat=gcd(D.trim(pol),der(pol))
        o,_=bm(b)
        code=f'w={w},res={r},repeated={repeat},out={o}'
        g['result'][code]+=1
        if r<=12:g['clusters'][str(pol)]+=1
        if pol==[1,0,1,0,2890] or pol==[1,0,2890,0,2890]:print('old recurrence candidate',kind,i,j,pol,flush=True)
    else:g['result'][f'w={w},phaseonly' if (phase[j]!=z[j]) else f'w={w},pass']+=1
    g['cases']+=1
Path('stress_signatures.json').write_text(json.dumps(allout,indent=2)+'\n')
