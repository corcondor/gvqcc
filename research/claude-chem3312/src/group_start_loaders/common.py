import sys, os
from pathlib import Path
import numpy as np
ROOT = Path(r'<ROOT>')
K8M = ROOT/'w_push11/k8/model'
FAM = ROOT/'w_push12/dc3356/family_merged'
os.environ.setdefault('K8_NPZ', str(FAM/'submission.npz'))
sys.path.insert(0, str(K8M))
import k8lib as K
HEADS = [1,5,7,11,0]
def load_spec(k, kmb=None, words=None):
    kmb = kmb or FAM/f'angle_k_{k}.kmb'
    bk = K.Bank(k, words)
    return K.extract_spec(kmb, k, bk), bk

P0 = K.P0 if hasattr(K,'P0') else 47
NV = 1219
ADDR = np.arange(NV)
def bits(f):
    return np.unpackbits(np.frombuffer(int(f).to_bytes((NV+7)//8,'little'),np.uint8),bitorder='little')[:NV].astype(np.uint8)
def pack(a):
    return int.from_bytes(np.packbits(np.asarray(a,np.uint8),bitorder='little').tobytes(),'little')
def products(sp,bk):
    fn,viol = K.symbol_functions(sp,bk)
    assert not viol
    out=[]
    for i,e in enumerate(sp.events):
        if e.kind in 'SOC':
            out.append(dict(ev=i, kind=e.kind, L=e.a, M=e.b, fL=K.func_of(e.a,fn), fM=K.func_of(e.b,fn)))
    for p in out: p['f']=p['fL']&p['fM']
    return out, fn
