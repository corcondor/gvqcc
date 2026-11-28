"""Native prefix comparison for the exact #267 144 distinct structured inputs."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import kickmix as km
import core_rebase_hmr as R
import crt882 as C
from verify_submission_dqi import FieldTables

# Use the exact published generator without its replay main routine.
data=Path('verify_structured267.py').read_text()
case_defs={}
exec(compile(data[:data.index('\nrows=[]')], 'verify_structured267.py:cases', 'exec'),case_defs)
rows=list(case_defs['cases']())
assert len(rows)==144
F=FieldTables(km.GF2Field(12))
def bits(a):
    return ((a[:,:,None]>>np.arange(12))&1).reshape(len(a),-1).T.astype(bool)
SYN=[np.bitwise_xor.reduce(np.asarray(F.antilog)[(np.asarray(F.log)[v][None,:]+np.arange(1,71)[:,None]*i[None,:])%4095],axis=1)
     if w else np.zeros(70,np.uint16) for _,w,i,v in rows]

def trace(prefix):
    b=km.CircuitBuilder();b.set_max_qubits(900)
    S=[b.create_quantum_register(12,f'S{i}') for i in range(70)]
    E=[b.create_classical_register(12,f'E{i}') for i in range(4095)]
    key=R.Pipeline.emit_key_prefix(b,S,j_min=0,stage=lambda _:None)
    d,n=[list(x) for x in key['D']],[list(x) for x in key['N']]
    if prefix!='raw':R.replace_pad(b,d,n)
    if prefix=='phase_input':
        dd,nn=[km.array(x) for x in d],[km.array(x) for x in n]
        R.Pipeline.NewOuter.emit_prefix(b,dd,nn,gauge_flag=key['gauge'].flag,
            gauge_other=key['carry'][12:],fused=False,stage=lambda _:None)
        R.Pipeline.P.Finish.emit_prefix(b,dd,nn)
    M=list(R.Pipeline.P.Finish.geometry()['M']) if prefix=='phase_input' else None
    p=b.finish_circuit()
    def words(sim,words,n):
        return (sim.read_across_shots(km.array(sum(words,[]))).T.reshape(n,len(words),12)@(1<<np.arange(12))).tolist()
    sx=km.array(sum([list(x) for x in S],[]))
    fail=[]
    h={}; ph=0; max_gap_by_case={}
    for k in range(0,len(rows),64):
        local=rows[k:k+64]
        sim=km.Simulator(batch_size=len(local),seed=268267+k,debug_print=False)
        sim.use_same_registers_as(p);sim.write_across_shots(sx,bits(np.array(SYN[k:k+len(local)])));sim.do(p)
        DD,NN=words(sim,d,len(local)),words(sim,n,len(local))
        ph+=int(sim.read_phase_flipped_across_shots().sum())
        for z,((tag,w,i,v),dd,nn) in enumerate(zip(local,DD,NN,strict=True)):
            dx=[dd[j] if j%2 else 0 for j in range(1,len(dd))]
            if prefix=='after_pad':
                def sqrt(v):return C.gf_pow(v,2048,12,C.MOD)
                aa,bb=[C.trim([sqrt(v) for v in dd[k::2]]) for k in (0,1)]
                a,b=bb,C.div(aa,bb)[1]
                degrees=[len(a)-1]
                while b:a,b=b,C.div(a,b)[1];degrees.append(len(a)-1)
                max_gap_by_case[k+z]=max((u-v for u,v in zip(degrees,degrees[1:])),default=0)
            want=dict(zip(map(int,i),map(int,v),strict=True))
            seen={};singular=0
            for j,x in enumerate(C.exp[:4095]):
                if C.evalp(dd,x):continue
                den=C.m(C.m(x,C.evalp(M if M is not None else dx,x)),C.evalp(R.U,x))
                v=C.evalp(nn,x)
                if not den:
                    singular+=1;continue
                val=C.m(v,C.inv(den))
                if val:seen[j]=val
            bad=seen!=want or singular
            h[w]=h.get(w,0)+bool(bad)
            if bad:fail.append(dict(case=k+z,weight=w,tag=tag,want_n=len(want),seen_n=len(seen),singular=singular))
    return dict(tape_operations=len(p),qubits=p.num_qubits,
       failures_by_weight=h,failures=fail,raw_phase_diagnostic_only=ph,max_gap_by_case=max_gap_by_case)

out={}
for where in (sys.argv[1:] or ('raw','after_pad','phase_input')):
    out[where]=trace(where)
    Path('p266_prefix_receipt.json').write_text(json.dumps(out,indent=2)+'\n')
    print(where,len(out[where]['failures']),out[where]['failures_by_weight'],flush=True)

if set(out)=={'raw','after_pad','phase_input'}:
    assert not out['raw']['failures'] and not out['after_pad']['failures']
    wrong={x['case'] for x in out['phase_input']['failures']}
    predicted={k for k,v in out['after_pad']['max_gap_by_case'].items() if v>2}
    assert wrong==predicted and len(wrong)==48
