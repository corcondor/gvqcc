import numpy as np, sys, subprocess, json
from pathlib import Path
import source72 as s
p=Path(sys.argv[1]); lines=p.read_text().splitlines(); c=np.fromstring(lines[-1],sep=' ',dtype=np.int32);assert len(c)==4025
r=np.random.default_rng(20261129072).integers(0,4096,(64,4025),dtype=np.int32);r[:,-1]=0
for k in range(8):
    l=int(k+1);u=int(k+23);ids=np.arange(10+8*k,10+8*k+75);r[k,ids]=l^s.mul(c[ids],u)
best=np.zeros(64,dtype=np.int32);lam=best.copy();mu=best.copy();initial=None;score64=None
for k,a in enumerate(s.A72):
    ids=np.delete(np.arange(4025),a); slopes=s.mul(r[:,ids]^r[:,a,None],s.inv(c[ids]^c[a])[None,:]);full=np.stack([np.bincount(row,minlength=4096) for row in slopes]);full[:,0]=0
    if k<8:
        v=np.argmax(full,axis=1);sc=full[np.arange(64),v];accept=sc>best;best=np.where(accept,sc,best);lam=np.where(accept,r[:,a]^s.mul(c[a],v),lam);mu=np.where(accept,v,mu)
    else:
        h=np.stack([np.bincount(row,minlength=4096) for row in slopes[:,np.arange(1024)*4024//1024]]);h[:,0]=0
        key=np.minimum(h,15)*4096-s.F2D[None,:];key[:,0]=-4096;top=np.argsort(-key,axis=1)[:,:4]
        for v in top.T:
            sc=full[np.arange(64),v];accept=(sc>best)&(h[np.arange(64),v]>0);best=np.where(accept,sc,best);lam=np.where(accept,r[:,a]^s.mul(c[a],v),lam);mu=np.where(accept,v,mu)
    if k==7:initial=np.column_stack([best,s.F2D[lam],s.F2D[mu],s.F2D[r[:,:4024]]]);initial_best=best.copy()
    if k==63:score64=best.copy()
    assert np.array_equal(best,np.count_nonzero((r^lam[:,None]^s.mul(c[None,:],mu[:,None]))==0,axis=1)-1)
assert initial is not None
with open('native_inputs.txt','w') as f:
    print(64,file=f);np.savetxt(f,initial,fmt='%d')
subprocess.run(['./selector_native',str(p),'native_inputs.txt','native_out.txt'],check=True,stdout=subprocess.DEVNULL,stderr=open('native.log','w'))
got=np.loadtxt('native_out.txt',dtype=np.int32);want=np.column_stack([best,s.F2D[lam],s.F2D[mu]])
assert np.array_equal(got,want),(np.where(got!=want),got[got[:,0]!=want[:,0]],want[got[:,0]!=want[:,0]])
rec={'cases':64,'structured':8,'exact_gauge_triples':int(got.size),'old_support':int(initial_best.sum()),'gray64_support':int(score64.sum()),'gray72_support':int(best.sum()),'worsened':int(np.count_nonzero(best<score64)),'emitter':Path('native.log').read_text().splitlines()[-1]}; print(json.dumps(rec));Path('out/native_receipt.json').write_text(json.dumps(rec,indent=2)+'\n')
