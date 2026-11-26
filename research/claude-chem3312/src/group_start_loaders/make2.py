# usage: make2.py k cover.pkl nrel e seed [p1limit]
import sys, os, pickle, time
from common import *
from frame import *
from solve import check_function
from solve2 import solve_all
from build2 import Builder2
from gf2 import Ech
k=int(sys.argv[1]); cover_file=sys.argv[2]; nrel=int(sys.argv[3]); e=int(sys.argv[4]); seed=int(sys.argv[5])
limit=float(sys.argv[6]) if len(sys.argv)>6 else 0
t0=time.time()
F=Frame(k)
cov=pickle.load(open(cover_file,'rb'))
ncov=len(cov)
tag='' if ncov==96 else f'_n{ncov}'
solf=f'sol2_k{k}{tag}_r{nrel}.pkl'
if os.path.exists(solf): sol=pickle.load(open(solf,'rb'))
else:
    sol=solve_all(F,cov,nrel); pickle.dump(sol,open(solf,'wb'))
B=Builder2(k,F,cov,sol,seed=seed)
B.p1seed=seed
# optional retries after a cached window search (same .in, different later choices)
if os.environ.get('NANCH'): B.nanchors=int(os.environ['NANCH'])
if os.environ.get('POST'): B.post_seed=int(os.environ['POST'])
if os.environ.get('EAGER'): B.eager_tail=True
from order_util import early_order
order=early_order(F, cov, e, B.rng)
orig=B.phase1
B.phase1=lambda o,ee: orig(o,ee,p1seed=seed,limit=limit)
B.run(e=e,order=order)
bad,_=check_function(F,cov,B.sol); assert bad==0
sp=B.spec()
nlow=4
print('spec built; toffoli',sp.toffoli,'cache',sp.toffoli-len(cov),'chips',len(cov),f'({time.time()-t0:.0f}s)',flush=True)
bk=K.Bank(k)
res=K.evaluate(sp,bk)
print('evaluate ok',res.ok,'toffoli',res.toffoli,'peak width',res.peak_width,res.violations[:5],f'({time.time()-t0:.0f}s)',flush=True)
if res.ok:
    sp.save(f'spec2_k{k}{tag}_r{nrel}_s{seed}.json')
    kmb=K.emit(sp,bk,template=FAM/f'angle_k_{k}.kmb',check=False)
    out=f'angle_k_{k}{tag}_f{nrel}_s{seed}.kmb'
    sha=K.write_kmb(kmb,out)
    print('emitted',out,'sha',sha[:16],'ops',len(kmb.ops),f'({time.time()-t0:.0f}s)',flush=True)
    v=K.verify_kmb(out,k,direction='forward' if k==0 else 'both')
    print('verify:',v,f'({time.time()-t0:.0f}s)')
