"""Test exact physical-wire KMB, including dirty target, controls and free wires."""
import hashlib,json
from pathlib import Path
import numpy as np
import kickmix as km

def mul(a,b):
    z=0
    while b:
        if b&1:z^=a
        a<<=1
        if a&4096:a^=0x1053
        b>>=1
    return z
def prod(a,b):
    z=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):z[i+j]^=mul(int(x),int(y))
    return z
def words(state,reg):
    return (state[reg]*np.uint16(1<<np.arange(12))[None,:,None]).sum(axis=1)
def cases(kind,k):
    l=json.loads(Path('raw_audit.json').read_text())['layout']
    a=np.array(l['D'][0 if kind!='red' else 1:34:2])
    assert a.shape==(17,12)
    n=18-k if kind in ('low','high') else 17-k
    b=np.array(l['N'][k::2][:n])
    size=17-k if kind in ('high','revq') else 17
    t=np.array(l['N'][1-k::2][:size])
    c=km.Circuit.from_file(f'{kind}{k}.kmb')
    stats=dict(c.operation_statistics())
    q=km.array([km.q(i) for i in range(900)])
    rng=np.random.default_rng(3171); count=paid=errors=0
    for j in range(8):
        initial=rng.integers(0,2,(900,64),dtype=bool)
        u,v=words(initial,a),words(initial,b)
        if kind=='revq':u=u[:17-k][::-1];v=v[::-1]
        h=17 if kind=='high' else 0
        ans=np.array([prod(s,r)[h:h+size] for s,r in zip(u.T,v.T)],dtype=np.uint16).T
        want=initial.copy()
        want[t]^=(ans[:,None,:]>>np.arange(12)[None,:,None])&1!=0
        z=km.Simulator(batch_size=64,seed=110+j,debug_print=False,counting_operations=True)
        z.use_same_registers_as(c); z.write_across_shots(q,initial); z.do(c)
        errors+=int(((z.read_across_shots(q)!=want).any(0)|z.read_phase_flipped_across_shots()).sum())
        paid+=int(z.operation_statistics().num_toffoli_like); count+=64
    p=Path(f'{kind}{k}.kmb')
    return dict(kind=kind,sector=k,tests=count,errors=errors,declared_Q=c.num_qubits,operations=len(c),CCX=stats.get('CCX',0),static_paid=int(c.operation_statistics().num_toffoli_like),executed_paid_mean=paid/count,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
    r=[cases(kind,k) for kind in ('low','high','revq','red') for k in range(2)]
    print(json.dumps(r,indent=2))
    assert not any(x['errors'] or x['CCX']!=x['static_paid'] or x['CCX']!=x['executed_paid_mean'] for x in r)
if __name__=='__main__':main()
