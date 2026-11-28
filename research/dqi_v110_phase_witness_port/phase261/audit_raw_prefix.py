"""Audit #261 in-place seams, with frozen #238 and V110 input panels."""
import argparse, collections, hashlib, json, struct, zipfile
from pathlib import Path
import numpy as np
import kickmix as km
from core_direct import Pipeline,C,U

def read_panels(root):
    archive=zipfile.ZipFile(root/'GVQCC_316K_RANK15_FULL_SPLICE_SOURCE_RECEIPTS.zip')
    for name in ('saved','cross','fresh','cross_inverse_frob4'):
        with archive.open(f'joint_work/audit/{name}.bin') as f:
            for batch in range(struct.unpack('<I',f.read(4))[0]):
                n=struct.unpack('<I',f.read(4))[0]
                def unpack(l):return np.unpackbits(np.frombuffer(f.read(l*8),np.uint8).reshape(l,8),axis=1,bitorder='little')[:,:n].astype(bool)
                yield name,batch,unpack(840),unpack(49140),unpack(1)[0]
    w=json.loads((root/'GVQCC_DQI_w33_423bit_witness.json').read_text())
    x=np.array([w['native_rows'][0]['input']],np.uint16)
    y=np.zeros((1,4095),np.uint16)
    for j in w['error_indices']:y[0,j]=1
    def b(a):return ((a[:,:,None]>>np.arange(12))&1).reshape(len(a),-1).T.astype(bool)
    yield 'w33',0,b(x),b(y),None

def readwords(s,W,n):
    q=km.array([b for a in W for b in a]); x=s.read_across_shots(q).T.reshape(n,len(W),12)
    return (x @ (1<<np.arange(12))).tolist()

def gcd(a,b):
    a=C.trim(a[:]);b=C.trim(b[:])
    while b:a,b=b,C.div(a,b)[1]
    if a:a=[C.m(v,C.inv(a[-1])) for v in a]
    return a

def raw_to_errors(d,n,shift):
    out={}
    dd=[d[i] if i%2 else 0 for i in range(1,len(d))]
    for j,x in enumerate(C.exp[:4095]):
        if C.evalp(d,x):continue
        den=C.m(C.m(x,C.evalp(U,x)),C.evalp(dd,x))
        assert den
        e=C.m(C.evalp(n,x),C.inv(den))
        assert e
        out[j]=e
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--prefix',default='raw_prefix.kmb');ap.add_argument('--roundtrip',default='raw_roundtrip.kmb');a=ap.parse_args()
    b=km.CircuitBuilder();b.set_max_qubits(900)
    S=[b.create_quantum_register(12,f'S{i}') for i in range(70)]
    E=[b.create_classical_register(12,f'E{i}') for i in range(4095)]
    key=Pipeline.emit_key_prefix(b,S,j_min=0,stage=lambda x:print('KEY',x,b.num_allocated_qubits,flush=True) if isinstance(x,str) else None)
    D,N=key['D'],key['N']
    p=b.finish_circuit()
    ids=lambda words:[[int(str(x)[1:]) for x in word] for word in words]
    di,ni,si=ids(D),ids(N),ids(S)
    pq={x for w in di+ni for x in w};assert len(pq)==852
    print('PREFIX',len(p),p.num_qubits,p.operation_statistics(),b.num_allocated_qubits,flush=True)
    p.to_file(a.prefix,format='kmb')
    # Rebuild in a fresh builder; do not assume finish_circuit is nondestructive.
    b=km.CircuitBuilder();b.set_max_qubits(900)
    S2=[b.create_quantum_register(12,f'S{i}') for i in range(70)]
    E2=[b.create_classical_register(12,f'E{i}') for i in range(4095)]
    key2=Pipeline.emit_key_prefix(b,S2,j_min=0)
    assert (ids(key2['D']),ids(key2['N']),ids(S2))==(di,ni,si)
    Pipeline.emit_key_closing(b,key2)
    assert b.num_allocated_qubits==840
    rt=b.finish_circuit();rt.to_file(a.roundtrip,format='kmb');del b,key,key2
    print('ROUNDTRIP',len(rt),rt.num_qubits,rt.operation_statistics(),flush=True)
    q=km.array([km.q(i) for w in si for i in w]);m=km.array([km.b(i) for w in E2 for i in [int(str(x)[1:]) for x in w]])
    dwords=[[km.q(i) for i in w] for w in di];nwords=[[km.q(i) for i in w] for w in ni]
    qa=km.array([km.q(i) for i in range(rt.num_qubits) if i not in set(sum(si,[]))]); ra=km.array([km.q(i) for i in range(p.num_qubits) if i not in pq])
    out={}
    with (a.root/'raw_words.jsonl').open('w') as f:
        for panel,st,x,y,wantphase in read_panels(a.root):
            n=x.shape[1]
            sp=km.Simulator(batch_size=n,seed=64571+st,counting_operations=True,debug_print=False);sp.use_same_registers_as(p);sp.write_across_shots(q,x);sp.do(p)
            DD,NN=readwords(sp,dwords,n),readwords(sp,nwords,n)
            live=sp.read_across_shots(ra).T
            r=out.setdefault(panel,dict(cases=0,gcd_degree={},gcd_N_degree={},degrees={},nonmonic=0,lead_min=4096,lead_max=0,rational_errors=0,phase_mask_errors=0,roundtrip_errors=0,paid_total=0,extra_live_max=0))
            tr=km.Simulator(batch_size=n,seed=64571+st,counting_operations=True,debug_print=False);tr.use_same_registers_as(rt);tr.write_across_shots(q,x);tr.write_across_shots(m,y);tr.do(rt)
            err=(tr.read_across_shots(q)!=x).any(0)|(tr.read_across_shots(m)!=y).any(0)|tr.read_across_shots(qa).any(0)|tr.read_phase_flipped_across_shots()
            r['roundtrip_errors']+=int(err.sum());r['paid_total']+=int(tr.operation_statistics().num_toffoli_like)
            SYN=(x.T.reshape(n,70,12)@(1<<np.arange(12))).tolist()
            masks=(y.T.reshape(n,4095,12)@(1<<np.arange(12))).tolist()
            for i,(d,v,s,mask) in enumerate(zip(DD,NN,SYN,masks)):
                dd=[d[j] if j%2 else 0 for j in range(1,len(d))]
                g=gcd(d,dd);h=gcd(d,v)
                deg=len(C.trim(d[:]))-1
                lead=d[-1]
                e=raw_to_errors(d,v,C.MOD)
                bad=C.moment([C.exp[j] for j in e],list(e.values()))!=s
                phase=sum((z & mask[j]).bit_count() for j,z in e.items())%2
                r['rational_errors']+=int(bad)
                r['phase_mask_errors']+=int(wantphase is not None and phase!=wantphase[i])
                r['nonmonic']+=int(lead!=1);r['lead_min']=min(r['lead_min'],lead);r['lead_max']=max(r['lead_max'],lead)
                r['extra_live_max']=max(r['extra_live_max'],int(live[i].sum()))
                for k,j in [('gcd_degree',len(g)-1),('gcd_N_degree',len(h)-1),('degrees',deg)]:
                    r[k][j]=r[k].get(j,0)+1
                r['cases']+=1
                f.write(json.dumps([panel,st,i,len(e),lead,g,h,d,v,np.flatnonzero(live[i]).tolist()])+'\n')
            print(panel,st,{k:v for k,v in r.items() if k not in ('gcd_degree','gcd_N_degree','degrees')},flush=True)
    for p0,r0 in out.items():r0['roundtrip_mean_paid']=r0['paid_total']/r0['cases']
    def fileinfo(p0,c):return dict(Q=c.num_qubits,ops=len(c),paid=int(c.operation_statistics().num_toffoli_like),sha=hashlib.file_digest(open(p0,'rb'),'sha256').hexdigest())
    (a.root/'raw_audit.json').write_text(json.dumps(dict(layout=dict(D=di,N=ni,other_at_seam=[int(str(x)[1:]) for x in ra]),prefix=fileinfo(a.prefix,p),roundtrip=fileinfo(a.roundtrip,rt),panels=out),indent=2)+'\n')
if __name__=='__main__':main()
