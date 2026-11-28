"""Pinned #246 native D,H seam vs saved syndrome fixtures; not a whole oracle."""
import collections, json, struct, zipfile
from pathlib import Path
import numpy as np
import kickmix as km
import verify_half as v
import packed_cf as cf
import pivot_codec as pc

def batches(archive,panel):
    with archive.open(f'joint_work/audit/{panel}.bin') as f:
        for _ in range(struct.unpack('<I',f.read(4))[0]):
            n=struct.unpack('<I',f.read(4))[0]
            def unpack(l):return np.unpackbits(np.frombuffer(f.read(l*8),np.uint8).reshape(l,8),axis=1,bitorder='little')[:,:n].astype(bool)
            x=unpack(840);p=unpack(49140);z=unpack(1)[0]
            yield (x.T.reshape(n,70,12)@ (1<<np.arange(12))).tolist(),p,z

def witness():
    w=json.loads(Path('GVQCC_DQI_w33_423bit_witness.json').read_text())
    e=dict(zip(w['error_indices'],w['error_values']))
    s=v.moments(e);assert s==w['native_rows'][0]['input']
    masks=np.zeros((49140,1+12*len(e)),bool)
    for i,j in enumerate(e):
        for b in range(12):masks[12*j+b,1+12*i+b]=1
    phase=np.array([0,*[(c>>b)&1 for c in e.values() for b in range(12)]],bool)
    for i in range(0,len(phase),32):
        a=masks[:,i:i+32];yield [s]*a.shape[1],a,phase[i:i+32]

def moments_from_rational(D,N):
    # N = polynomial part of D(x) * sum S_j*x^(-j-1).
    # Then the same recurrence reconstructs later moments including padding.
    out=[];n=len(D)-1
    for i in range(70):
        a=N[n-1-i] if 0<=n-1-i<len(N) else 0
        for j in range(1,min(i,n)+1):a^=v.m(D[n-j],out[i-j])
        out.append(a)
    return out

def main():
    pin={'forward.kmb':'532aee1f775a084d63005fd4135d327896ed45a19540cb40305cd361ebc2962c','half.kmb':'5718d30c253e1b29b01f2bab597d81994345fbe16ca5f58145cd3e8c77a7931b'}
    assert {p:v.sha(p) for p in pin}==pin
    circuits={p:km.Circuit.from_file(p) for p in pin}
    q=km.array([km.q(i) for i in range(840)])
    a=km.array([km.q(i) for i in range(840,851)])
    b=km.array([km.b(i) for i in range(49140)])
    archive=zipfile.ZipFile('GVQCC_316K_RANK15_FULL_SPLICE_SOURCE_RECEIPTS.zip')
    receipt={}
    for panel in ('w33_zero_and_true_support_onehot','cross_inverse_frob4','saved','cross','fresh'):
        records=witness() if panel.startswith('w33') else batches(archive,panel)
        r=dict(cases=0,weight_hist={},bm_cf_mismatch=0,cf_reverse_mismatch=0,half_inverse_mismatch=0,rational_reverse_mismatch=0,native={})
        hist=collections.Counter()
        for batch,(rows,masks,phase) in enumerate(records):
            ss=[]; vv=[]
            # The classical oracle re-encodes once per distinct syndrome per batch.
            memo={}
            for s in rows:
                t=tuple(s)
                if t not in memo:
                    D,N,w=v.decode(s);D,N=v.make_squarefree(D,N,w)
                    dn,h,_=cf.forward(s)
                    dn_p,h_p,used=pc.forward(s);assert (dn,h)==(dn_p,h_p) and pc.reverse(dn_p,h_p)==s
                    H,V=v.half(D,N)
                    n2=cf.inverse_half(D,H)
                    memo[t]=(w,D[:-1]+H,D[:-1]+V,
                        (dn[:35]+[1]!=D or v.trim(dn[35:])!=N),
                        (cf.reverse(D[:-1]+v.pad(n2,35),h)!=s),
                        n2!=N,moments_from_rational(D,n2)!=s)
                w,x,y,*checks=memo[t]
                for k,c in zip(('bm_cf_mismatch','cf_reverse_mismatch','half_inverse_mismatch','rational_reverse_mismatch'),checks):r[k]+=int(c)
                ss.append(x);vv.append(y);hist[w]+=1;r['cases']+=1
            x=v.bits(ss); y=v.bits(vv)
            for p,c in circuits.items():
                full=(p=='half.kmb')
                for seed in (64571,64572):
                    s=km.Simulator(batch_size=len(rows),seed=seed+batch,counting_operations=True,debug_print=False)
                    s.use_same_registers_as(c);s.write_across_shots(q,x);s.write_across_shots(b,masks);s.do(c)
                    er=[(s.read_across_shots(q)!=(x if full else y)).any(0),
                        (s.read_across_shots(b)!=masks).any(0),
                        (s.read_phase_flipped_across_shots()!=(phase if full else False)),
                        s.read_across_shots(a).any(0) if full else np.zeros(len(rows),bool)]
                    z=r['native'].setdefault(p,dict(shots=0,word=0,mask=0,phase=0,scratch=0,paid_total=0))
                    z['shots']+=len(rows);z['paid_total']+=int(s.operation_statistics().num_toffoli_like)
                    for k,t in zip(('word','mask','phase','scratch'),er):z[k]+=int(t.sum())
        r['weight_hist']=dict(sorted(hist.items()))
        for z in r['native'].values():z['mean_paid']=z['paid_total']/z['shots']
        receipt[panel]=r; print(json.dumps({panel:r}),flush=True)
        Path('stress_receipt.json').write_text(json.dumps(dict(scope='classical S -> D,H, native optimized #246-ABI stage only; no native syndrome bridge',hashes=pin,pivot_comparison=pc.costs(),panels=receipt),indent=2)+'\n')
if __name__=='__main__':main()
