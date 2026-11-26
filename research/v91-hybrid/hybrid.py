"""V91: Exact temporal output synthesis using PR175 KMB and pinned V20 charts.
No submission, no score claim. A cheaper native family must pass replay.
"""
import argparse, collections, hashlib, itertools, json, pathlib, struct, zipfile
import numpy as np
import native_donor as nd
N=nd.NV; FULL=nd.FULL
def bits(x):
    while x:
        b=x&-x; yield b.bit_length()-1; x^=b
def xor(xs):
    r=0
    for x in xs:r^=int(x)
    return r
def add(B,v,m):
    while v:
        i=v.bit_length()-1
        if i not in B:B[i]=(v,m);return None
        a,b=B[i];v^=a;m^=b
    return m
def solve(B,v):
    m=0
    while v:
        i=v.bit_length()-1
        if i not in B:return None
        a,b=B[i];v^=a;m^=b
    return m
def care_masks(W,E):
    a=[FULL]+[0]*75;out=[];seen={0}
    for j,(p,c) in enumerate(E):
        p,c=int(p),int(c)
        assert p in seen and c not in seen;seen.add(c)
        out.append(a[p]);a[c]=a[p]&nd.pack(W[:,j]%64!=0);a[p]&=nd.pack(W[:,j]%64!=32)
    return out
def parse(path):
    d=path.read_bytes();h=struct.unpack_from("<4I9Q",d,16);pos=104;sec={};regs={}
    while pos<len(d):
        k,n=struct.unpack_from("<QQ",d,pos);pos+=16;s=d[pos:pos+n];pos+=n
        assert len(s)==n
        if k==0:
            l,w=struct.unpack_from("<II",s);regs[s[8:8+l].decode()]=[x&0x7fffffff for x in struct.unpack_from("<"+"I"*w,s,8+l)]
        else:sec[k]=s
    assert h[0]==2 and h[1]<=128
    it={k:iter(x[0] for x in struct.iter_unpack("<I",sec[k])) for k in range(2,10)}
    ops=[]
    for op in sec[1]:
        assert op in (17,33,49,80,0,16,32,48,128,144,160,176),op
        r=[next(it[k]) for k in {0:[],1:[7],2:[5,6],3:[2,3,4]}[(op>>4)&3]]
        b=next(it[8]) if op&64 else next(it[9]) if op&128 else None
        ops.append((op,r,b))
    assert len(ops)==h[4]
    assert all(next(v,None) is None for v in it.values())
    return h[1],regs,ops
def replay(C,words):
    qn,regs,ops=C
    sel=regs["selection"];wq=sum([regs[f"word_{j}"] for j in range(5)],[])
    assert len(sel)==11 and len(wq)==35
    q=[0]*qn
    for i,z in enumerate(sel):q[z]=nd.A[i]
    for z,v in zip(wq,words):q[z]=v
    debts=[];bitvar={};phase=0
    for op,r,b in ops:
        if op==17:q[r[0]]^=FULL
        elif op==33:q[r[1]]^=q[r[0]]
        elif op==49:q[r[2]]^=q[r[0]]&q[r[1]]
        elif op==80:
            bitvar[b]=len(debts);debts.append(q[r[0]]);q[r[0]]=0
        else:
            m=FULL
            for z in r:m&=q[z]
            if op&128:debts[bitvar[b]]^=m
            else:phase^=m
    assert all(q[z]==nd.A[i] for i,z in enumerate(sel))
    assert not any(q[z] for z in range(qn) if z not in sel and z not in wq)
    assert not any(debts) and phase==0,"measurement phase"
    return [q[z] for z in wq]
def count(C):return sum((op&127) in (48,49) for op,r,b in C[2])
def word_rows(w,k):
    return nd.words(w,k)
def verify_group(C,W,ks):
    for k in ks:
        prev=word_rows(W,k-1);cur=word_rows(W,k)
        assert replay(C[k],prev)==cur,("forward",k)
        assert replay(C[k],cur)==prev,("reverse",k)
def solve_group(W,care,ks,selected,P):
    # Fixed bank contributions are the exact matched original deltas.
    # Retained circuits must ALSO replay on the modified incoming word table.
    fs=[];desc=[]
    for k in selected:
        p=P[k];f=nd.features(p)
        products=[nd.linear(u,f)&nd.linear(v,f) for u,v in zip(p["U"],p["V"])]
        fs.append(f+products)
        desc.extend((k,j,x) for j,x in enumerate(f+products))
    paid=[i for i,(k,j,x) in enumerate(desc) if j>=99]
    active=set(range(len(desc)))
    matrices=[];ys=[]
    for s in range(5):
        masks=[care[5*k+s] if k!=ks[-1] or k==14 else FULL for k in ks]
        columns=[xor((x&masks[h])<<(N*h) for h in range(ks.index(k),len(ks))) for k,j,x in desc]
        targets=[]
        for b in range(6):
            o=7*s+b;fixed=word_rows(W,ks[0]-1)[o];seq=[]
            for k,m in zip(ks,masks):
                if k not in selected:fixed^=word_rows(W,k-1)[o]^word_rows(W,k)[o]
                seq.append((fixed^word_rows(W,k)[o])&m)
            targets.append(xor(x<<(N*h) for h,x in enumerate(seq)))
        matrices.append(columns);ys.append(targets)
    def fit(s):
        B={};ker=0
        for i in sorted(active):
            d=add(B,matrices[s][i],1<<i)
            if d is not None:ker|=d
        ss=[solve(B,y) for y in ys[s]]
        if None in ss:return None
        use=0
        for m in ss:use|=m
        return ss,ker,use
    fits=[fit(s) for s in range(5)]
    if any(f is None for f in fits):return None
    while True:
        i=next((i for i in paid if i in active and all(not ((u&~k)>>i&1) for ss,k,u in fits)),None)
        if i is None:break
        active.remove(i);fits=[fit(s) for s in range(5)];assert all(f is not None for f in fits)
    co={k:np.zeros((len(f),30),np.uint8) for k,f in zip(selected,fs)}
    for s,(ss,ker,use) in enumerate(fits):
        for b,sol in enumerate(ss):
            for i in bits(sol):
                k,j,x=desc[i];co[k][j,6*s+b]=1
    new={};ww=W.copy();running=word_rows(W,ks[0]-1)
    for k in ks:
        if k in selected:
            p=P[k];c=co[k];f=fs[selected.index(k)];keep=np.flatnonzero(c[99:].any(axis=1))
            new[k]=dict(p,U=p["U"][keep],V=p["V"][keep],M=c[99:][keep],R=c[:99].T.copy())
            for s in range(5):
                for b in range(6):running[7*s+b]^=xor(f[j] for j in np.flatnonzero(c[:,6*s+b]))
                # Tags of the incoming and target words must agree; preserve the source tag.
                running[7*s+6]=running[7*s+5]^word_rows(W,k)[7*s+5]^word_rows(W,k)[7*s+6]
        else:
            running=[a^b^c for a,b,c in zip(running,word_rows(W,k-1),word_rows(W,k))]
        for s in range(5):
            for b in range(7):assert not ((running[7*s+b]^word_rows(W,k)[7*s+b])&care[5*k+s])
        nd.store(ww,k,running)
    return new,ww
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",type=pathlib.Path,required=True);a=ap.parse_args()
    out=a.out;out.mkdir(exist_ok=True,parents=True)
    root=pathlib.Path(__file__).resolve().parents[2]/"research/claude-chem3312"
    receipts=json.loads((root/"verification/official_receipts.json").read_text())
    ref=out/"reference";ref.mkdir(exist_ok=True)
    # No zip path traversal. Preserve exact official member hashes.
    with zipfile.ZipFile(root/"family_3312.zip") as z:
        names={pathlib.Path(n).name:n for n in z.namelist()}
        for n,h in receipts["member_sha256"].items():
            d=z.read(names[n]);assert hashlib.sha256(d).hexdigest()==h,n;(ref/n).write_bytes(d)
    C={k:parse(ref/f"angle_k_{k}.kmb") for k in range(15)}
    arrays=dict(np.load(ref/"submission.npz",allow_pickle=False));W=arrays["angle_words"];E=arrays["tree_edges"]
    care=care_masks(W,E);verify_group(C,W,list(range(15)))
    before=sum(map(count,C.values()));assert before==3312,before
    P,build,_=nd.donor(out)
    target=out/"candidate";target.mkdir(exist_ok=True)
    files={k:ref/f"angle_k_{k}.kmb" for k in C};record=[]
    for ks in ([2,3,4],[6],[8,9,10],[12,13,14]):
        base=sum(count(C[k]) for k in ks);best=base
        chosen=None
        for n in range(1,len(ks)+1):
            for sub in itertools.combinations(ks,n):
                sub=list(sub);r={"group":ks,"selected":sub}
                try:
                    sol=solve_group(W,care,ks,sub,P)
                    if sol is None:r["status"]="inconsistent";record.append(r);continue
                    plans,ww=sol;D=C.copy();fpaths={}
                    for k,plan in plans.items():
                        ops=build(plan,nd.SEL,nd.WQ);fp=out/("trial_"+"_".join(map(str,sub))+f"_{k}.kmb")
                        nd.write_kmb(fp,ops);D[k]=parse(fp);fpaths[k]=fp
                    verify_group(D,ww,ks)
                    r["actual_count"]=sum(count(D[k]) for k in ks);r["status"]="native replay pass"
                    if r["actual_count"]<best:best=r["actual_count"];chosen=(D,ww,fpaths)
                except (AssertionError,ValueError,KeyError) as ex:r["status"]="rejected";r["reason"]=str(ex)
                record.append(r);print(json.dumps(r),flush=True)
        if chosen:
            C,W,newfiles=chosen;files.update(newfiles)
        print("group",ks,base,best,flush=True)
    # Stronger global gate: all legal addresses, both transitions, phase and workspace.
    verify_group(C,W,list(range(15)))
    orig=arrays["angle_words"]
    for j,m in enumerate(care):
        assert not (nd.pack(W[:,j]!=orig[:,j])&m)
    arrays["angle_words"]=W
    for k,f in files.items():(target/f"angle_k_{k}.kmb").write_bytes(f.read_bytes())
    np.savez_compressed(target/"submission.npz",**arrays)
    C={k:parse(target/f"angle_k_{k}.kmb") for k in range(15)}
    verify_group(C,W,list(range(15)))
    total=sum(map(count,C.values()))
    receipt={"reference":before,"actual_candidate":total,"below_3300":total<3300,"counts":[count(C[k]) for k in range(15)],"changed_words":int(np.count_nonzero(W!=orig)),"all_36570_transitions":True,"official_verifier":"not_run","cases":record}
    (out/"receipt.json").write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True)
if __name__=="__main__":main()
