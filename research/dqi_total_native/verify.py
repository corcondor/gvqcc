"""Native end-to-end regression. Inputs are only raw 70 syndromes and 4095 masks."""
import hashlib,json,random,sys,time
from pathlib import Path
import numpy as np,kickmix as km
from crt882 import m,inv,exp,log,mul,evalp,ks,moment
def derv(D):return [D[i] if i%2 else 0 for i in range(1,len(D))]
def force(xs,N):
    D=[1]
    for x in xs:D=mul(D,[x,1])
    dp=derv(D)
    return {x:m(evalp(N,x),inv(m(x,evalp(dp,x)))) for x in xs}
def fixture():
    rng=random.Random(202611280821);out=[]
    for w in range(36):
        for i in range(8):
            e={x:rng.randrange(1,4096) for x in rng.sample(range(1,4096),w)}
            out.append(("weight",w,e,("zero","onehot","random","random")[i%4]))
        if w:
            for i in range(2):
                e=force(rng.sample(range(1,4096),w),[rng.randrange(1,4096)])
                out.append(("constant_numerator",w,e,"random"))
        if w>=3:
            for i in range(2):
                e=force(rng.sample(range(1,4096),w),[ks[(w+i)%len(ks)],1,1])
                out.append(("forced_quadratic",w,e,"random"))
    G=[1]
    for k in ks:G=mul(G,[k,1,1])
    for i in range(32):
        e=force(rng.sample(range(1,4096),35),G)
        out.append(("allpole",35,e,("zero","onehot","random","random")[i%4]))
    return out
def bits(a):
    a=np.asarray(a,np.uint16)
    return ((a[:,:,None]>>np.arange(12))&1).reshape(len(a),-1).T.astype(bool)
def main():
    path=Path(sys.argv[1]);batch=int(sys.argv[2]) if len(sys.argv)>2 else 64
    c=km.Circuit.from_file(str(path));assert c.num_qubits==900
    assert set(c.register_data)=={f'S{i}' for i in range(70)}|{f'E{i}' for i in range(4095)}
    q=km.array([km.q(i) for i in range(840)]);a=km.array([km.q(i) for i in range(840,900)]);b=km.array([km.b(i) for i in range(49140)])
    fs=fixture();cases=[];rng=np.random.default_rng(19316)
    for g,w,e,kind in fs:
        S=moment(list(e),list(e.values()))
        if kind=="zero":M=np.zeros(4095,np.uint16)
        elif kind=="onehot":
            M=np.zeros(4095,np.uint16);x=next(iter(e),1);M[log[x]]=1<<int(rng.integers(12))
        else:M=rng.integers(0,4096,4095,dtype=np.uint16)
        expected=sum((int(M[log[x]])&v).bit_count() for x,v in e.items())&1
        cases.append((g,w,S,M,expected,kind))
    if len(sys.argv)>3 and sys.argv[3]=="smoke":
        cases=[next(x for x in cases if x[0]=="weight" and x[1]==w and x[5]=="random") for w in range(36)]+[x for x in cases if x[0]=="allpole"][:4]
        seeds=[611]
    else:seeds=[611,977]
    if len(sys.argv)>3 and sys.argv[3].endswith(".npz"):
        z=np.load(sys.argv[3]);cases += [("saved",-1,s,m,p,"saved") for s,m,p in zip(z['S'],z['M'],z['expected'])]
    out=dict(scope="complete native raw S -> decoder -> 4095-point rational phase -> inverse; no HMR, no host selection",sha256=hashlib.file_digest(path.open('rb'),'sha256').hexdigest(),Q=c.num_qubits,ops=len(c),static_paid=int(c.operation_statistics().num_toffoli_like),errors_order=["value","mask","dirty","phase"],checks=[],groups={},weights={},shots=0,errors=[0]*4,union=0)
    start=time.time();paid=0
    for seed in seeds:
        for i in range(0,len(cases),batch):
            rows=cases[i:i+batch];S=bits([z[2] for z in rows]);M=bits([z[3] for z in rows]);expected=np.asarray([z[4] for z in rows],bool)
            sim=km.Simulator(batch_size=len(rows),seed=seed+i,debug_print=False,counting_operations=True);sim.use_same_registers_as(c);sim.write_across_shots(q,S);sim.write_across_shots(b,M);sim.do(c)
            E=np.array([(sim.read_across_shots(q)!=S).any(0),(sim.read_across_shots(b)!=M).any(0),sim.read_across_shots(a).any(0),np.asarray(sim.read_phase_flipped_across_shots(),bool)^expected])
            errs=E.sum(1).tolist();union=int(E.any(0).sum());paid+=int(sim.operation_statistics().num_toffoli_like)
            out['checks'].append(dict(seed=seed,start=i,shots=len(rows),errors=errs,union=union));out['shots']+=len(rows);out['errors']=[u+v for u,v in zip(out['errors'],errs)];out['union']+=union
            for j,row in enumerate(rows):
                for key,label in [('groups',row[0]),('weights',str(row[1]))]:
                    g=out[key].setdefault(label,dict(shots=0,errors=[0]*4,union=0));g['shots']+=1;g['errors']=[u+int(v) for u,v in zip(g['errors'],E[:,j])];g['union']+=int(E[:,j].any())
            out['mean_paid']=paid/out['shots'];out['seconds']=time.time()-start
            print(json.dumps(out['checks'][-1]),flush=True);Path("native_receipt.json").write_text(json.dumps(out,indent=2)+"\n")
            if union:
                print("FAILING CASES",[(row[0],row[1],row[5],E[:,j].tolist()) for j,row in enumerate(rows) if E[:,j].any()],flush=True)
                np.savez_compressed("failing.npz",S=np.asarray([row[2] for j,row in enumerate(rows) if E[:,j].any()]),M=np.asarray([row[3] for j,row in enumerate(rows) if E[:,j].any()]),expected=np.asarray([row[4] for j,row in enumerate(rows) if E[:,j].any()]))
                raise RuntimeError("native full-oracle mismatch")
    print(json.dumps({k:v for k,v in out.items() if k not in ['weights','checks']}),flush=True)
if __name__=="__main__":main()
